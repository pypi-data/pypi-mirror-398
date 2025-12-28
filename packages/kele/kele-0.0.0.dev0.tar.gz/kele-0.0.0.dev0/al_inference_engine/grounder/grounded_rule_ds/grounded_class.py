from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, ClassVar
import warnings


from .rule_check import RuleCheckGraph
from al_inference_engine.grounder.grounded_rule_ds.grounded_ds_utils import unify_all_terms
from ._nodes import _AtomCompoundTermNode, _OperatorNode, _RootNode, _AssertionNode, _ConnectiveNode, _RuleNode, _QuestionRuleNode
from ._nodes._tupletable import _TupleTable
from collections import deque
from al_inference_engine.syntax import Formula, Assertion

if TYPE_CHECKING:
    from al_inference_engine.config import Config
    from al_inference_engine.control import InferencePath
    from al_inference_engine.knowledge_bases.fact_base import FactBase
    from al_inference_engine.syntax import GROUNDED_TYPE_FOR_UNIFICATION
    from al_inference_engine.syntax import Constant, Rule, FACT_TYPE, SankuManagementSystem, CompoundTerm
    from al_inference_engine.syntax.base_classes import _QuestionRule
    from collections.abc import Sequence, Mapping
    from al_inference_engine.equality import Equivalence
    from al_inference_engine.syntax import Variable


class GroundedRule:
    """
    管理单条规则的实例化状态，负责 term-level unify、合并变量候选表与 check 阶段的执行。

    GroundedRule 不保存完整展开后的 grounded rules，而是维护变量候选表与执行状态，
    在 check 时再按需展开并生成新的事实。
    """

    def __init__(self, rule: Rule, equivalence: Equivalence, sk_system_handler: SankuManagementSystem, args: Config) -> None:
        if rule.unsafe_variables:
            raise TypeError(f"""规则 {rule!s} 不安全，因为它包含了不安全的变量 {[str(u) for u in rule.unsafe_variables]}。\n
                            这个错误之所以出现很可能是因为规则没有加入RuleBase，也没有经过相应的预处理
                            """)
        if not self._is_conjunctive_body(rule):
            warnings.warn(f"""
                          规则{rule!s}的Body部分只允许为positive assertion和negative assertion的conjunction，此规则不符合要求\n
                          这个警告出现很可能是因为规则没有加入RuleBase，也没有经过相应的预处理。\n
                          其他相关信息请查阅：#TODO
                          """, stacklevel=5)  # TODO: 需要引擎教程网址
        if not self._is_conjunctive_head(rule):
            warnings.warn(f"规则{rule!s}的head部分包含除了and以外的其他连接词，可能会导致无法正确生成事实", stacklevel=5)

        self.args = args
        self.rule = rule
        self.rule_checker = RuleCheckGraph(self, self.args)  # risk: 如果fact里面里面是forall的很难处理，实操时候需要先实例化fact再推。
        self.is_concept_compatible_binding = partial(self.rule.is_concept_compatible_binding,
                                              fuzzy_match=self.args.grounder.conceptual_fuzzy_unification)

        self.equivalence = equivalence
        self.sk_system_handler = sk_system_handler

        self.fact_base: FactBase
        self.inference_path: InferencePath

        self.all_freevar_table: list[_TupleTable] = []
        self._action_new_fact_list: list[FACT_TYPE] = []
        self._past_all_freevar_table: list[_TupleTable] = []
        self._past_df_prefix_sum: list[_TupleTable] = []  # 前缀和会有较大的浪费，即第二个df包含第一个df，以此类推

        columns = set()
        # 引擎只使用部分nodes进入grounding过程，部分node只做substitution。此外，substitution nodes中的action op相关nodes也会影响grounded rule的生成
        # 但其不增加已通过semi-naive策略生成的grounded rule的数量，也不需要进行unification，因此不记录与之相关的past_df
        for assertion_node in self.rule_checker.grounding_nodes:
            columns |= assertion_node.grounding_arguments
            self._past_df_prefix_sum.append(_TupleTable(column_name=tuple(columns)))

        self.total_table: _TupleTable
        self._back_up_total_table: _TupleTable
        self._back_up_true_table: _TupleTable

    def unify(self, terms: list[CompoundTerm[Constant | CompoundTerm] | Constant]) -> None:
        """
        对传入的 term 进行 unify，仅生成实例化候选值，不检查事实的正确性。

        - AtomCompoundTermNode 会先将常量替换为等价类代表元；
        - unify 仅走 term-level，后续由 AssertionNode 进行 join 与 check。

        :params terms: 用于实例化的事实 term 列表
        """
        node_queue: deque[_RootNode | _OperatorNode | _AtomCompoundTermNode] = deque()
        root: _RootNode = self.rule_checker.graph_root
        node_queue.append(root)

        while node_queue:
            cur_node = node_queue.popleft()
            if isinstance(cur_node, _AtomCompoundTermNode):
                cur_node.process_equiv_represent_elem()
            elif isinstance(cur_node, (_OperatorNode, _RootNode)):
                node_queue.extend(cur_node.query_for_children())

        for t in terms:
            self._unify_single(t)
        self._start_passing_process()

    def check_grounding(self) -> list[FACT_TYPE]:
        """
        执行 check 阶段并返回新事实。

        AssertionNode 会执行 action assertion 的计算并生成额外事实，最终由 RuleNode 汇总。

        :returns list[FACT_TYPE]: check得到的新事实
        """
        execute_queue: deque[_AssertionNode | _ConnectiveNode | _RuleNode] = deque(self.rule_checker.execute_nodes)
        new_facts: list[FACT_TYPE] = []

        self._start_join_process()

        # 同时由于execute_queue的创建时直接加入AssertionNode，我们保证了AssertionNode总是最先被执行，而是否可以执行ConnectiveNode，由
        # ConnectiveNode的ready_for_execute属性控制。注意可以执行即要求它的父节点都向它传递了TfIndexs。
        while execute_queue:
            cur_node = execute_queue.popleft()
            if isinstance(cur_node, _AssertionNode) and cur_node.ready_to_execute:
                # 这AssertionNode将首先获得向下传递的true/false index，然后向所有子节点传递true/false index
                cur_node.exec_check()
                cur_node.pass_tf_index()
                execute_queue.extend(cur_node.query_for_children())
                if cur_node.action_assertion:
                    self._action_new_fact_list.extend(cur_node.get_action_result())
            elif isinstance(cur_node, _ConnectiveNode) and cur_node.ready_to_execute:
                cur_node.exec_check()
                cur_node.pass_tf_index()
                execute_queue.extend(cur_node.query_for_children())
            elif isinstance(cur_node, _RuleNode):
                # 一般来说对于单个rule，RuleNode只有一个，所以直接赋值即可  # FIXME: 会多的以后，先留着
                new_facts = cur_node.exec_check()
        if self._action_new_fact_list:
            new_facts.extend(set(self._action_new_fact_list))
            self._action_new_fact_list.clear()
        return new_facts

    def _unify_single(self, term: CompoundTerm[Constant | CompoundTerm] | Constant) -> None:
        node_queue: deque[_RootNode | _OperatorNode | _AtomCompoundTermNode] = deque()
        root: _RootNode = self.rule_checker.graph_root
        node_queue.append(root)

        while node_queue:
            cur_node = node_queue.popleft()
            if isinstance(cur_node, _AtomCompoundTermNode) and not cur_node.only_substitution:  # FIXME: 带着一个term往下走，似乎要多判断很多次这个
                # 另外这个only的判断可能也有待优化
                cur_node.exec_unify(term, allow_unify_with_nested_term=self.args.grounder.allow_unify_with_nested_term)
                # 对_AtomCompoundTermNode进行unification操作
            elif isinstance(cur_node, (_OperatorNode, _RootNode)):
                node_queue.extend(cur_node.query_for_children(term))

    def receive_true_table(self, true_table: _TupleTable) -> None:
        """
        接收从AssertionNode传递来的true indexs
        """
        if not hasattr(self, '_back_up_true_table') or self._back_up_true_table.height == 0:
            self._back_up_true_table = true_table.copy()
        else:
            self._back_up_true_table = self._back_up_true_table.concat_table(true_table)

    def _start_passing_process(self) -> None:
        """
        启动传递过程，将 freevar_table 传递到 _AssertionNode。
        """
        node_queue: list[_RootNode | _OperatorNode | _AtomCompoundTermNode | _AssertionNode] = []
        root: _RootNode = self.rule_checker.graph_root
        node_queue.append(root)

        while node_queue:
            cur_node = node_queue.pop()
            if isinstance(cur_node, _AtomCompoundTermNode):
                cur_node.pass_freevar_to_child()
                node_queue.extend(cur_node.query_for_child())
            elif isinstance(cur_node, (_OperatorNode, _RootNode)):
                node_queue.extend(cur_node.query_for_children())

    def _start_join_process(self) -> None:
        """
        将各 AssertionNode 的表合并为规则级别总表，并广播给执行节点。
        """
        for assertion_node in self.rule_checker.grounding_nodes:
            self._past_all_freevar_table.append(assertion_node.past_freevar_table)
            self.all_freevar_table.append(assertion_node.exec_join())

        if self.rule_checker.grounding_nodes:
            total_table = self._calc_total_table()

            if self.args.executor.anti_join_used_facts and hasattr(self, "_back_up_true_table"):
                # 在config中开启anti_join_used_facts、且已经有备份的情况下，执行anti join操作
                total_table = total_table.anti_join(self._back_up_true_table)

            self.total_table = total_table
        else:  # 规则前提不含 free vars 时，total table 为空列。  TODO：考虑是否将这种特殊规则单独出来，不走unify的流程
            self.total_table = _TupleTable(column_name=())

        self._broadcast_total_table(self.total_table)
        self._back_up_total_table = self.__dict__.pop('total_table')

    def _calc_total_table(self) -> _TupleTable:
        """对齐等价类代表元并执行 semi-naive 合并。"""
        # 将过往的所有table对齐
        self._past_all_freevar_table = [table.update_equiv_element(self.equivalence) for table in self._past_all_freevar_table]
        self._past_df_prefix_sum = [table.update_equiv_element(self.equivalence) for table in self._past_df_prefix_sum]
        # 将当前table对齐
        self.all_freevar_table = [table.update_equiv_element(self.equivalence) for table in self.all_freevar_table]
        # FIXME: 注意这里new_table实质上进行了两遍对齐：在unify过程一次对齐，在这里另外一次对齐。可能需要考虑并移除一次对齐
        return self._semi_naive()  # FIXME: 这里需要拆分变量绑定一致性检查、exec_check和最后的semi。第一个考虑到内存，改换Yannakakis

    def _semi_naive(self) -> _TupleTable:
        """TODO: 目前版本是(A1+A1')(A2+A2')...的，还没加入设计的其他公式"""
        t1_last = self._past_df_prefix_sum[0]  # 对应前j-1个的总last，此时是第0个
        t1_new = self.all_freevar_table[0]  # 对应前j-1个总new，此时是第0个

        self._past_df_prefix_sum[0] = self._past_df_prefix_sum[0].concat_table(t1_new)  # 更新为第T轮的prefix sum

        for i in range(1, len(self.all_freevar_table)):
            # 对于任意两项，其可以拆解为A1A2 + A1A2' + A1'A2 + A1'A2'。t1_last对应A1，t1new对应A1'。t2同理

            t2_last = self._past_all_freevar_table[i]
            t2_new = self.all_freevar_table[i]

            new_tables = []
            if t1_new.height > 0 and t2_last.height > 0:
                new_tables.append(t1_new.union_table(t2_last))  # A1'A2

            if t1_last.height > 0 and t2_new.height > 0:
                new_tables.append(t1_last.union_table(t2_new))  # A1A2'

            if t1_new.height > 0 and t2_new.height > 0:
                new_tables.append(t1_new.union_table(t2_new))  # A1'A2'

            nxt_prefix_sum = self._past_df_prefix_sum[i]

            if len(new_tables) > 0:
                new_table = new_tables[0].concat_table(*new_tables[1:])
                self._past_df_prefix_sum[i] = self._past_df_prefix_sum[i].concat_table(new_table)  # 更新prefix sum，用于下次
            else:
                new_table = _TupleTable(self._past_df_prefix_sum[i].raw_column_name)

            t1_last = nxt_prefix_sum  # 继续为i+1项做准备而迭代
            t1_new = new_table

        return t1_new

    @staticmethod
    def _is_conjunctive_body(rule: Rule) -> bool:
        """判断当前规则的body的连接词只出现and, not，且not只能作用在Assertion上（换言之就是没有OR的DNF格式）"""
        is_standard = True
        cur_term_queue: deque[Formula | Assertion | None] = deque([rule.body])
        while cur_term_queue:
            cur_term = cur_term_queue.popleft()
            if isinstance(cur_term, Formula):
                if cur_term.connective not in {'AND', 'NOT'}:
                    is_standard = False
                    break
                if cur_term.connective == 'NOT' and not isinstance(cur_term.formula_left, Assertion):
                    # NOT必须作用在Assertion上，不能作用在其他公式上
                    is_standard = False
                    break
                cur_term_queue.append(cur_term.formula_left)
                cur_term_queue.append(cur_term.formula_right)
        return is_standard

    @staticmethod
    def _is_conjunctive_head(rule: Rule) -> bool:
        """判断当前规则的head的连接词只出现and"""
        is_standard = True
        cur_term_queue: deque[Formula | Assertion | None] = deque([rule.head])
        while cur_term_queue:
            cur_term = cur_term_queue.popleft()
            if isinstance(cur_term, Formula):
                if cur_term.connective != 'AND':
                    is_standard = False
                    break
                cur_term_queue.append(cur_term.formula_left)
                cur_term_queue.append(cur_term.formula_right)
        return is_standard

    def _broadcast_total_table(self, total_table: _TupleTable) -> None:
        """
        将规则级别总表广播到 AssertionNode / RuleNode。

        :params: total_table (_TupleTable): 等待储存的总表
        """
        for cur_assertion in self.rule_checker.execute_nodes:
            cur_assertion.broadcast_total_table(total_table)

    def print_all_grounded_rules(self) -> list[str]:
        """为了调试方便，打印所有实例化后的规则（注意控制内存开销）"""
        grounded_rule_text = []
        for combination in self._back_up_total_table.iter_rows():
            rule_text = self.rule.replace_variable(combination)
            grounded_rule_text.append(str(rule_text))

        return grounded_rule_text

    def get_question_solutions(self) -> tuple[list[Mapping[Variable, Constant | CompoundTerm]], _QuestionRule | None]:
        """获取问题规则节点（如果存在）"""
        if isinstance(self.rule_checker.rule_node, _QuestionRuleNode):
            question_node = self.rule_checker.rule_node
            return question_node.solutions, question_node.question_rule
        return [], None

    def reset(self) -> None:  # fixme: 此函数实现仅起过渡作用，令当前commit与之前的代码表现一致。后续会逐渐用更多的reset替代这个reset
        """重置GroundedRule的状态，用于新一轮（iteration）的推理。_past_prefix_sum变量和_backup变量不应删除"""
        self.rule_checker.reset()
        self._past_all_freevar_table.clear()
        self.all_freevar_table.clear()
        self._action_new_fact_list.clear()
        if hasattr(self, 'total_table'):
            del self.total_table


class GroundedRuleDS:
    """
    维护全局 GroundedRule 的生命周期与当前轮次的实例化输入。

    GroundedRuleDS 不追求存储“最终 grounded rule”，而是提供实例化、合并与复用的管理入口。
    """

    grounded_rule_pool: ClassVar[dict[Rule, GroundedRule]] = {}

    def __init__(self, equivalence: Equivalence, sk_system_handler: SankuManagementSystem, args: Config) -> None:
        # FIXME：这里虽然因为对齐需要传入equivalence，但具体到底是否应该在init传入，以及是否应该换用其他方式调用都有待进一步讨论  # noqa: TD004
        self.equivalence = equivalence
        self.sk_system_handler = sk_system_handler
        self.args = args
        self.current_grounded_rule_terms: Sequence[tuple[GroundedRule, Sequence[GROUNDED_TYPE_FOR_UNIFICATION]]] | None = None

    def _add_rule(self, rule: Rule) -> GroundedRule:
        """
        将一条规则纳入 GroundedRuleDS 管理，并返回对应 GroundedRule。
        """
        if rule not in self.grounded_rule_pool:
            grounded_rule = GroundedRule(rule, self.equivalence, self.sk_system_handler, self.args)
            self.grounded_rule_pool[rule] = grounded_rule

        return self.grounded_rule_pool[rule]
        # 这里转化为GroundedRule的时候，就已经将rule的图结构生成好了。暂时没有明确的处理范畴约束，先置空，仅
        # 转一下GroundedRule。但是以后可能会留存历史以来所有选中的Rule，并进行恰当的事实选取以进行额外的实例化

    def start(self, cur_rules_facts: Sequence[tuple[Rule, Sequence[GROUNDED_TYPE_FOR_UNIFICATION]]]) -> None:
        """
        设置本轮需要执行的cur_rules和facts，及一些可能需要的初始化操作

        :raises RuntimeError: grounding过程还未结束时，再次调用start
        """  # noqa: DOC501
        if self.current_grounded_rule_terms is not None:
            raise RuntimeError("Grounding process is not ended")

        self.current_grounded_rule_terms = []
        for rule, facts in cur_rules_facts:
            cur_rule = self._add_rule(rule)
            cur_rule.reset()
            self.current_grounded_rule_terms.append((cur_rule, facts))

    def end(self) -> None:
        """grounding过程结束，移除cur_rules和facts。"""
        self.current_grounded_rule_terms = None

    @staticmethod
    def _unify(cur_rule: GroundedRule, facts: Sequence[GROUNDED_TYPE_FOR_UNIFICATION]) -> None:
        """对单条规则使用对应事实进行实例化。"""
        useful_terms: list[CompoundTerm[Constant | CompoundTerm] | Constant] = []
        for single_fact in facts:
            useful_terms.extend(unify_all_terms(single_fact))

        cur_rule.unify(useful_terms)

    def _grounding_term_level(self) -> None:
        """遍历当前轮次规则并完成 term-level 实例化。"""
        if self.current_grounded_rule_terms is not None:
            for rule_tuple in self.current_grounded_rule_terms:
                single_rule, single_facts = rule_tuple
                self._unify(single_rule, single_facts)

    def exec_grounding(self) -> None:
        """TODO: 这个函数还可以优化。可能是对self.current_grounded_rule_terms做一些调整，如加入过往选择的rule？"""
        self._grounding_term_level()

    def get_corresponding_grounded_rules(self, abstract_rules: list[Rule]) -> list[GroundedRule]:
        """
        取出给定rule的GroundedRule，用于下一步executor的执行
        1. 如果grounding信息的存储方式是现在逐条的check graph的话，记录好二者的映射关系即可；
        2. 如果存储方式是一张大图的话，直接return规则末端的节点。
        此外，如果某条rule在本阶段没有得到实际的实例化，那是可以不return的。  risk: 这里有个权衡，是本阶段没有 or 至今没有
        TODO: executor.check时，要注意避免check已check的部分（这个和used还不完全一样，有可能没过全局的check所有没有use）。一个可能的策略
        是所有check过的都丢到下一个节点存储，当前节点移除。但还是会存在，比如op(x)=y中，x=1是used，不需要二次实例化。但x=1曾经被check过后，
        不代表日后不能被check（因为可能y变了）。但另一方面，如果等价类够快的话，检查是否已check可能开销check一下差不多。

        risk: 从上面的分析来看，这个函数的返回值约束不会出现太大的问题，因为无论是GroundedRule还是末端代表规则的节点，它们都能够索引到
        规则本身的信息 + 实例化信息，这样后续executor进行check时总是有办法快速适配的。但总之还是多加小心一些
        """
        return [self.grounded_rule_pool[r] for r in abstract_rules]

    @classmethod
    def reset(cls) -> None:
        """
        清空grounded_rule_pool，这是为了防止重复创建Inference_engine带来的错误
        """
        cls.grounded_rule_pool.clear()


class GroundedProcess:
    """执行 grounding 的上下文管理器。"""
    def __init__(self, grounded_structure: GroundedRuleDS, cur_rules_terms: Sequence[tuple[Rule, Sequence[GROUNDED_TYPE_FOR_UNIFICATION]]]):
        self.grounded_structure = grounded_structure
        self.cur_terms_facts = cur_rules_terms

    def __enter__(self) -> GroundedRuleDS:
        self.grounded_structure.start(cur_rules_facts=self.cur_terms_facts)
        return self.grounded_structure

    def __exit__(self, exc_type, exc_value, traceback) -> bool | None:  # type: ignore[no-untyped-def]  # noqa: ANN001
        if exc_type:  # XXX: 暂时没有对异常做特殊处理，且强制返回了True。以后使用时根据实际出现的异常逐步优化
            raise exc_value

        self.grounded_structure.end()
        return True
