from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from al_inference_engine.syntax import (TERM_TYPE, AtomCompoundTerm, Constant, CompoundTerm, Operator,
                                        Variable, ATOMTERM_TYPE, ATOM_TYPE)

from collections import OrderedDict
from ._tupletable import _TupleTable
from ._op import _OperatorNode

from al_inference_engine.grounder.grounded_rule_ds.grounded_ds_utils import atomize_arguments, FREEANY
# HACK: 一会儿想想如何调整逻辑，按说有一个地方用就够了
# 替代方案是，在构造节点的时候（composite_node = _AtomCompoundTermNode(self.grounded_rule, term_or_constant=cur_term)），
# 生成一个额外的、执行过_atomize_arguments的term作为入参，虽然比在_AtomCompoundTermNode里面直接对atom_arguments赋值时候
# 进行_atomize_arguments操作要花费更多的时间空间，但利于代码组织。
# 不过另一方面，AtomCompoundTermNode.term_or_constant的类型是TERM_TYPE，如果用这个替代方案就意味着类型应该是Constant, Varibale和变更为FREEANY
# 的CompoundTerm，就会有点不匹配。解决方案是当完全以效率优先是，用于绘图、展示等需求的term_or_constant应当被直接替换为arguments，
# 从而类型就变成了Constant | Va....，就不存在这个问题了。因此既然替代方案最终会被丢弃，暂时就先注释掉这个报错且从FIXME修改为hack。

if TYPE_CHECKING:
    from al_inference_engine.config import Config
    from ._assertion import _AssertionNode
    from ._root import _RootNode
    from collections.abc import Generator
    from al_inference_engine.grounder import GroundedRule


class _AtomCompoundTermNode(ABC):
    """
    这是原子 CompoundTermNode，其参数中不再含嵌套 CompoundTerm。

    AtomCompoundTermNode 可以连接到 AssertionNode，也可以继续连接到更外层的 term 节点。
    """
    composite_or_assertion_child: list[_AtomCompoundTermNode | _AssertionNode]
    raw_atom_arguments: tuple[ATOM_TYPE, ...]  # FIXME: 原始的atom_arguments，似乎没有其他需要调用它的地方
    represent_arguments: tuple[TERM_TYPE, ...]
    grounding_arguments: tuple[Variable, ...]  # 当前AtomTerm的所有（去重后的）Variable，例如op(x, $F)的grounding_arguments为(x,)
    _term_or_constant: TERM_TYPE
    only_substitution: bool

    grounded_rule: GroundedRule

    freevar_table: _TupleTable
    all_freevar_table: list[_TupleTable]

    operator: Operator
    able_to_pass_freevar: bool  # 只有当此层级的AtomTerm存在Variable的时候，也就是grounding_arguments不为空/表列数不为0的时候，
    # 才会向GroundedRule传递table（但按图结构的向下pass是不影响的，向GroundedRule传递实则代表是否被用于total table的生成）
    # 例如op(x, $F)会向GroundedRule传递，但是op($F, $F)不会传递

    def add_child(self, node: _AtomCompoundTermNode | _AssertionNode) -> None:
        self.composite_or_assertion_child.append(node)

    def __str__(self) -> str:
        return str(self._term_or_constant)

    @abstractmethod
    def exec_unify(self,
                   term: CompoundTerm[Constant | CompoundTerm] | Constant,
                   *,
                   allow_unify_with_nested_term: bool = True
                ) -> None:
        """
        执行unify操作
        在useful_terms的控制下，传入的一定是AtomCompoundTerm

        :param term (CompoundTerm | Constant): 待实例化的Term，某种意义上只有可能是AtomCompoundTerm，但是为了避免外层的类型检查，
            我们还是采纳这种写法
        :param allow_unify_with_nested_term: 是否允许与嵌套的Term进行unify

        FIXME: 此外应考虑机器剩余核数并考虑如何并行处理。不过这个可能是在executor的check中处理
        """

    @abstractmethod
    def process_equiv_represent_elem(self) -> None:
        """
        将常量替换为等价类代表元，用于统一匹配与表合并。
        """

    def pass_freevar_to_child(self) -> None:
        """
        将 freevar_table 传递给子节点，并在需要时加入 GroundedRule 的合并列表。
        """
        if self.able_to_pass_freevar and not self.only_substitution:
            self.all_freevar_table.append(self.freevar_table)
        for child in self.composite_or_assertion_child:
            child.all_freevar_table.extend(self.all_freevar_table)

    def query_for_child(self, term: ATOMTERM_TYPE | None = None) -> tuple[_AssertionNode | _AtomCompoundTermNode, ...]:
        """
        获得所有子节点，参数term为可选参数，照理来说没啥用，仅用于统一格式
        """
        return tuple(self.composite_or_assertion_child)

    def get_all_children(self) -> Generator[_AtomCompoundTermNode | _AssertionNode]:
        """
        仅用于绘图使用
        """  # noqa: DOC402
        yield from self.composite_or_assertion_child

    def get_free_var_name(self) -> str:
        """
        仅用于绘图使用
        """
        variable_name = self.freevar_table.raw_column_name
        print_dict = _TupleTable(variable_name)
        print_dict.set_base_df(self.freevar_table.base_df)

        variables_str: list[str] = print_dict.raw_columns_name_str
        result_str = ','.join(variables_str) + '\n'

        values_str = []
        for var_value in print_dict.iter_rows():
            var_value_str = [str(v) for v in var_value.values()]
            single_str = ','.join(var_value_str)
            values_str.append(single_str)

        return result_str + '\n'.join(values_str)

    def _add_uncheck_results(self) -> None:
        """将实例化的匹配信息传递回grounded rule"""
        raise NotImplementedError

    @property
    def node_representative(self) -> str:  # 注意其他节点如果需要打印信息时，也可以采用相似的同名函数
        """用于绘图中，代表当前node的简短信息"""
        return str(self._term_or_constant)

    def reset(self) -> None:
        self.all_freevar_table.clear()
        self.freevar_table.clear()  # 不应该在join操作之前将all_freevar_table给清空，否则由于传递的是指针会导致错误
        # 其他tf index和joint类同


class _VariableNode(_AtomCompoundTermNode):
    def __init__(self,
                 rule: GroundedRule,
                 term_or_constant: Variable,
                 *,
                 only_substitution: bool = False) -> None:
        self.grounded_rule = rule
        self.composite_or_assertion_child: list[_AtomCompoundTermNode | _AssertionNode] = []

        self.raw_atom_arguments = (term_or_constant,)
        self.grounding_arguments = self.raw_atom_arguments

        self.only_substitution = only_substitution

        self.freevar_table: _TupleTable = _TupleTable(self.grounding_arguments)
        self.all_freevar_table: list[_TupleTable] = []

        self._term_or_constant: Variable = term_or_constant
        self.able_to_pass_freevar: bool = True

    def process_equiv_represent_elem(self) -> None:
        pass

    def exec_unify(self,
                   term: CompoundTerm[Constant | CompoundTerm] | Constant,
                   *,
                   allow_unify_with_nested_term: bool = True) -> None:
        # 这种情况是直接连接RootNode的Variable，此时传入的任何东西都会作为可能的候选值
        if ((isinstance(term, Constant) or
                (isinstance(term, CompoundTerm) and allow_unify_with_nested_term)) and
            self.grounded_rule.is_concept_compatible_binding(self._term_or_constant, term)
        ):
            self.freevar_table.add_row({self._term_or_constant: term})
    # 当节点类型为Constant时，由_RootNode的query_for_children函数来保证可以匹配，而不必执行unify操作 fixme: Constant可能更名const


class _TermNode(_AtomCompoundTermNode):
    def __init__(self,
                 rule: GroundedRule,
                 term_or_constant: CompoundTerm,
                 *,
                 only_substitution: bool = False) -> None:
        self.grounded_rule = rule
        self.composite_or_assertion_child: list[_AtomCompoundTermNode | _AssertionNode] = []

        self.atom_arguments: tuple[TERM_TYPE, ...] = atomize_arguments(term_or_constant.arguments)
        self.represent_arguments = self.atom_arguments  # 初始化代表元组和原本的一致
        self.grounding_arguments = tuple(u for u in self.atom_arguments if isinstance(u, Variable))
        self.grounding_arguments = tuple(OrderedDict.fromkeys(self.grounding_arguments))
        self.operator = term_or_constant.operator

        self.only_substitution = only_substitution

        self.freevar_table: _TupleTable = _TupleTable(self.grounding_arguments)
        self.all_freevar_table: list[_TupleTable] = []

        self._term_or_constant: CompoundTerm = term_or_constant
        self.able_to_pass_freevar: bool = self.grounding_arguments != ()  # grounding_arguments非空才能向下传递

    def process_equiv_represent_elem(self) -> None:
        """
        将所有的Constant替换为等价类代表元
        """
        processed_represent_arguments: list[TERM_TYPE] = []
        for arg in self.represent_arguments:
            if arg is not FREEANY and isinstance(arg, Constant):
                processed_represent_arguments.append(self.grounded_rule.equivalence.get_represent_elem(arg))
            else:
                processed_represent_arguments.append(arg)
        self.represent_arguments = tuple(processed_represent_arguments)

    def _unify_the_term(self,
                        term_fact: CompoundTerm[Constant | CompoundTerm],
                        *,
                        allow_unify_with_nested_term: bool = True) -> None:
        """
        将TermNode的unify过程单独放在这里，减少for循环的次数
        以下情况，我们认为term_fact可以用来实例化atom_term：
        1、对应位置上，atom_term是Variable，此时term_fact随便是什么都可以
        2、对应位置上，atom_term是FREEANY，此时term_fact随便是什么都可以（存疑，也许应当要求term_fact这时候也是FREEANY）
        3、对应位置都是Constant，而且他们一致
        注意：这里使用的是 self.represent_arguments，它已完成等价类代表元替换。
        """
        # 例如op(x,y,1)，现在记录的应该就是(x,y,1):[(1,2,1), (1,3,1),(2,3,1),....]这样的
        temp_arguments: dict[Variable, Constant | CompoundTerm] = {}

        for _i, (s_rule, s_fact) in enumerate(zip(self.represent_arguments, term_fact.arguments, strict=True)):
            if TYPE_CHECKING:
                s_fact = cast("Constant | CompoundTerm", s_fact)

            s_fact_represent = self.grounded_rule.equivalence.get_represent_elem(s_fact)

            # risk：如果规则中为op1(x,y,op2(z))，出现了事实op1(1,2,3)，照理来说也许不应当实例化，但是此处我们仍然会将(1,2)作为(x,y)的候选值

            if isinstance(s_rule, Variable):
                if ((s_rule in temp_arguments and temp_arguments[s_rule] != s_fact_represent) or
                    # 同名变量多次出现时必须绑定到同一个值（例如 add(x, x) 不能与 add(1, 2) 匹配）
                    not self.grounded_rule.is_concept_compatible_binding(s_rule, s_fact_represent)):
                    # Rule-level variable concept constraints check (e.g., constraints propagated via x=y)
                    return

                if (isinstance(s_fact_represent, Constant) and
                        self.grounded_rule.is_concept_compatible_binding(s_rule, s_fact_represent)):
                    # s_fact_represent为constant的情况
                    temp_arguments[s_rule] = s_fact_represent

                elif ((allow_unify_with_nested_term and isinstance(s_fact_represent, CompoundTerm))
                      and self.grounded_rule.is_concept_compatible_binding(s_rule, s_fact_represent)):
                    # s_fact_represent为CompoundTerm的情况
                    temp_arguments[s_rule] = s_fact_represent
                else:
                    return

            elif isinstance(s_rule, Constant) and s_rule != s_fact and s_rule is not FREEANY:
                if s_rule is FREEANY:
                    continue
                if s_rule == s_fact_represent:
                    # s_fact 与 s_rule 已替换为等价类代表元，因此直接比较即可
                    continue
                # 当Rule在此处取值为Constant时，如果rule和fact对应位置不一致，应该视为匹配失败
                # FREEANY虽然是特殊的Constant，但是此处不受到限制（因为它是占位符）
                return

        self.freevar_table.add_row(temp_arguments)

    def exec_unify(self,
                   term: CompoundTerm[Constant | CompoundTerm] | Constant,
                   *,
                   allow_unify_with_nested_term: bool = True) -> None:
        if isinstance(term, CompoundTerm):
            # 针对term的情况，只有传入的是CompoundTerm才会开始Unify操作
            self._unify_the_term(term, allow_unify_with_nested_term=allow_unify_with_nested_term)


class _ConstantNode(_AtomCompoundTermNode):
    def __init__(self, rule: GroundedRule, term_or_constant: Constant) -> None:
        self.grounded_rule = rule
        self.composite_or_assertion_child: list[_AtomCompoundTermNode | _AssertionNode] = []

        self.raw_atom_arguments = (term_or_constant,)
        self.represent_arguments = (term_or_constant,)
        self.grounding_arguments = ()  # fixme: 常量这里会不会为空就行？

        self.freevar_table: _TupleTable = _TupleTable(())
        self.all_freevar_table: list[_TupleTable] = []

        self._term_or_constant: Constant = term_or_constant
        self.able_to_pass_freevar: bool = False

        self.only_substitution = False

    def process_equiv_represent_elem(self) -> None:
        """
        将常量替换为等价类代表元。
        """
        self.represent_arguments = (self.grounded_rule.equivalence.get_represent_elem(self._term_or_constant), )

    def exec_unify(self,
                   term: CompoundTerm[Constant | CompoundTerm] | Constant,
                   *,
                   allow_unify_with_nested_term: bool = True,
                   fuzzy_match: bool = True) -> None:
        pass


def build_termnode(rule: GroundedRule, term_or_constant: TERM_TYPE) -> _AtomCompoundTermNode:
    """
    工厂函数，用于创建合适的AtomCompoundTerm
    :param rule: 用于创建Node的groundedRule
    :param term_or_constant: 用于创建Node的term
    :return: 合适的AtomCompoundTerm

    :raises ValueError: 如果term_or_constant不是CompoundTerm、Constant或Variable

    """  # noqa: DOC501
    if isinstance(term_or_constant, CompoundTerm):
        return _TermNode(rule, term_or_constant)
    if isinstance(term_or_constant, Constant):
        return _ConstantNode(rule, term_or_constant)
    if isinstance(term_or_constant, Variable):
        return _VariableNode(rule, term_or_constant)
    raise ValueError("term_or_constant must be CompoundTerm, Constant or Variable")


class _BuildTerm:
    """
    进行实例化的单位，将题目拆解为一个个Term分别匹配和存储可能的实例化。对Term中变量的实例化候选值，将存储到GroundedRule的free_variables中。
    目前这个类作为一个过渡类，在创建的时候会将Term拆分为AtomCompoundTermNode和TermConstantNode，创建内部的图结构。
    以后将以AtomCompoundTermNode | TermConstantNode作为基本单位进行操作
    """

    def __init__(self, grounded_rule: GroundedRule, root_node: _RootNode, args: Config) -> None:
        self.grounded_rule = grounded_rule  # 用于传回free_variables里面
        self.root_node = root_node
        self.args = args  # TODO: 需要这么去传args，说明可能有优化余地

    def build_term_structure(self, cur_term: TERM_TYPE, root_node: _RootNode, *, only_substitution: bool = False) -> _AtomCompoundTermNode:
        """
        对于当前的term，创建对应的AtomCompoundTermNode，如果有复合结构，那么拆开复合结构而构建图结构

        :param cur_term: 当前的term
        :param root_node: 根节点
        :return: 对应的AtomCompoundTermNode
        """
        if isinstance(cur_term, (Constant, Variable)):  # 只有Constant|Variable|AtomTerm的情况会在这里处理
            # 直接返回即可，拆解到此为止
            atom_node = build_termnode(self.grounded_rule, cur_term)
            # 本来被标记为only_substitution的不会再改变其状态
            # 严格来说此构图代码只会被触发一次，此处写法是保险起见
            atom_node.only_substitution = True if atom_node.only_substitution else only_substitution
            root_node.add_child(atom_node)
            return atom_node

        # 此后，cur_term一定是CompoundTerm，进而term_node一定是_TermNode
        term_node = build_termnode(self.grounded_rule, cur_term)
        term_node.only_substitution = True if term_node.only_substitution else only_substitution

        if term_node.able_to_pass_freevar:
            # 只有当需要传递free_var（也即grounding_arguments非空）才需要创建operatorNode
            op_node = self._build_operator_node(cur_term, root_node)
            op_node.add_child(term_node)
        elif isinstance(cur_term, (AtomCompoundTerm, Constant)):
            # 这是完全没有Variable的AtomCompundTerm，无需连接到OperatorNode，但是需要连接到RootNode
            root_node.add_child(term_node)

        for single_term in cur_term.arguments:
            if isinstance(single_term, CompoundTerm):
                father_node = self.build_term_structure(cur_term=single_term, root_node=root_node)
                father_node.add_child(term_node)

        return term_node

    def _build_operator_node(self, single_term: CompoundTerm, root_node: _RootNode) -> _OperatorNode:
        re_operator_node = root_node.operator_exist(single_term.operator)
        if re_operator_node:
            # 之前创建过这个Operator的_OperatorNode，直接返回这个OperatorNode就好
            return re_operator_node
        # 这是全新的_AtomCompoundTermNode，现在的AtomCompoundTermNode是由buildterm的入口传来的，而它作为入口意味着一定
        # 有创建_OperatorNode的必要.如果_AtomCompoundTermNode全是由复合的Term组成的，那他就没有必要连接OperatorNode，这里也不会传入
        operator_node = _OperatorNode(single_term.operator)
        self.root_node.add_child(operator_node)
        return operator_node
