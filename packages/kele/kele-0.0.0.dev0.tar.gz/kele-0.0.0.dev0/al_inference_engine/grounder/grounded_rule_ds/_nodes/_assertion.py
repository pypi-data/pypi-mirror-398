from __future__ import annotations

from typing import TYPE_CHECKING, cast
from functools import reduce
from itertools import product

from ._tftable import TfTables
from ._conn import _ConnectiveNode
from ._tupletable import _TupleTable

from al_inference_engine.syntax import Variable, Assertion, CompoundTerm, Constant, AtomCompoundTerm

if TYPE_CHECKING:
    from al_inference_engine.syntax import TERM_TYPE
    from ._rule import _RuleNode
    from collections.abc import Generator
    from al_inference_engine.grounder import GroundedRule


class _AssertionNode:
    """
    负责断言节点的 join 与 check 执行。

    - join：合并来自 term 节点的变量候选表；
    - check：基于 total_table 执行真假判断；
    - action assertion：计算 action term 并将结果写回事实。
    """

    def __init__(self, content: Assertion,
                 grounded_rule: GroundedRule,
                 *,
                 negated_assertion: bool) -> None:

        self.content: Assertion = content
        self.rule_or_connective_children: list[_ConnectiveNode | _RuleNode] = []  # 亦或者应该统一叫children，然后不要next_node函数。  # 我们此刻的图
        # 这里不是list，就是一个ConnectiveNode，但考虑到共享不妨留一下。另外init里估计要传这个参数
        # 还需要一个标记是否有匹配结果的标记符
        self.grounded_rule = grounded_rule

        self.tf_table: TfTables
        self.all_freevar_table: list[_TupleTable] = []
        self.freevar_table: _TupleTable
        self.grounding_arguments: set[Variable]
        self._action_result: list[Assertion] = []  # FIXME: 这里返回的是含有action_op的Assertion，后续有待进一步讨论这里的格式

        if negated_assertion:
            # 否定assertion的初始化
            self.grounding_arguments = set()
            self.action_assertion = self.content.is_action_assertion
        elif self.content.is_action_assertion:
            # 非否定但是action_assertion的初始化
            self.action_assertion = True
            self.grounding_arguments = set()
            for term in (content.lhs, content.rhs):
                if not term.is_action_term:
                    self.grounding_arguments.update(term.free_variables)
        else:
            # 其他情况的初始化
            self.action_assertion = False
            self.grounding_arguments = set(self.content.free_variables)
        self.past_freevar_table: _TupleTable = _TupleTable(column_name=tuple(self.grounding_arguments))
        # 过往freevar_table，每次都会通过concat将当前freevar_table加入记忆中

        self.keep_table: bool | None = None  # 基于SAT solver的结果，确定需要保留的table
        # true 保留true table, false保留false table，None表示均保留
        self.negated_assertion: bool = negated_assertion  # 记录了当前assertion是否被not算子影响。
        # 受到not算子影响的Assertion不会进入grounding, join流程，也不会建立CompoundTerm节点
        # 记录了最后合并得到的大表
        self.total_table: _TupleTable

    def __str__(self) -> str:
        return str(self.content)

    def add_child(self, node: _ConnectiveNode | _RuleNode) -> None:
        self.rule_or_connective_children.append(node)

    def exec_join(self) -> _TupleTable:
        """
        执行join操作，将所有子节点的结果合并起来。

        :return: 合并后的freevar_table
        :rtype: _TupleTable
        """
        self.freevar_table = reduce(lambda x, y: x.union_table(y), self.all_freevar_table)
        return self.freevar_table

    def exec_check(self) -> None:
        """
        检查每个可能的赋值，并传递 true/false 索引表。
        """
        empty_table = _TupleTable(column_name=tuple(self.content.free_variables))  # check操作是验证assertion实例化正确性的，
        # 需要和assertion本身相关的变量。而grounding_arguments则用于判断参与unify过程的判断

        small_table = self.total_table.get_small_table(tuple(self.content.free_variables))

        # 对于无变量的assertion而言，只需要判断和传递自身的True/False
        if not small_table.column_name:
            check_result = self._check_self()  # 判断当前assertion是否为真
            if check_result and (self.keep_table is None or self.keep_table):  # 如果为真，且当前Assertion也有为真的解释，则保留
                self.tf_table = TfTables(true=_TupleTable.create_empty_table_with_emptyset(), false=empty_table)
                # 保留用空列的table表示，即不参与table的运算。
                # 因此空列table与其他table做cross时，将直接返回另一个table。不保留则用空行table表示，因为空行意味着某个变量组合没有合法替换方案。
            elif not check_result and (self.keep_table is None or not self.keep_table):
                self.tf_table = TfTables(true=empty_table, false=_TupleTable.create_empty_table_with_emptyset())
            else:
                # 如果keep_table与自身检查结果不匹配（例如自身为True，但是keep_table为False），那么两个表都是空
                self.tf_table = TfTables(true=empty_table, false=empty_table)
            return

        tf_list = []

        for combination in small_table.iter_rows():
            if self.action_assertion:
                tf_list.append(self._check_single_action_assertion(combination))
            else:
                tf_list.append(self._check_single(combination))

        true_table, false_table = small_table.get_true_false_table(tf_list, keep_table=self.keep_table)

        self.tf_table = TfTables(true=true_table, false=false_table)

        if not self.only_substitution:
            self.past_freevar_table = self.past_freevar_table.concat_table(self.freevar_table)

    def _check_self(self) -> bool:
        """
        检查自身是否为真。

        :raise ValueError: grounding_arguments不为空时，combination不能为None
        """  # noqa: DOC501
        if self.grounding_arguments:
            raise ValueError("Assertion with pure arguments must be checked with combination")
        return self._ask_equivalence(self.content) or self._ask_sk_system(self.content)

    def _exec_implement_func(self, term: CompoundTerm) -> CompoundTerm | Constant | None:
        """
        给定 action_term 计算结果并返回。
        """
        implement_func = term.operator.implement_func
        if implement_func is None:
            return None

        equivalence = self.grounded_rule.equivalence

        candidate_arguments: list[list[TERM_TYPE]] = []
        for arg in term.arguments:
            if TYPE_CHECKING:
                arg = cast("CompoundTerm | Constant", arg)
            equiv_items = list(equivalence.get_equiv_item(arg))
            candidate_arguments.append(equiv_items)  # 这里get_equiv_item已经把元素自身加入进去了，同时去重操作也已经进行过了
        # 获得符合条件的所有参数的组合（写成list[list[TERM_TYPE]]，每个list对应每个参数的的equiv_items）

        for arguments in product(*candidate_arguments):
            candidate_term = AtomCompoundTerm.from_parts(term.operator, arguments)
            try:
                result = implement_func(candidate_term)
                if TYPE_CHECKING:
                    result = cast("CompoundTerm | Constant", result)
            except TypeError:  # HACK: 这里except TypeError的实质是处理无法计算的情况，将在进一步确定implement_func的格式之后修改这里的代码
                continue  # 如果计算失败，尝试下一个参数组合，否则将会直接返回结果
            else:
                return result

        return None

    def _check_single_action_assertion(self, combination: dict[Variable, Constant | CompoundTerm]) -> bool:
        """执行 action assertion：先计算 action term，再进行真假判断。"""
        assertion = self.content.replace_variable(combination)
        if isinstance(assertion.lhs, CompoundTerm) and assertion.lhs.is_action_term:
            value = self._exec_implement_func(assertion.lhs)
            if value is not None:
                self._action_result.append(Assertion.from_parts(assertion.lhs, value))  # 记录计算出来的值，这个值将在后续加入事实库中
                # 必须在assertion将action_term替换为计算结果前记录生成结果，否则无法正确把包含action_term的表示计算结果的fact加入事实库中

                assertion = Assertion.from_parts(value, assertion.rhs)
            # value为None时，意味着implement_func无法计算，此时不再替换assertion.lhs

        if isinstance(assertion.rhs, CompoundTerm) and assertion.rhs.is_action_term:
            value = self._exec_implement_func(assertion.rhs)
            if value is not None:
                self._action_result.append(Assertion.from_parts(assertion.rhs, value))
                assertion = Assertion.from_parts(assertion.lhs, value)

        return self._ask_equivalence(assertion) or self._ask_sk_system(assertion)

    def _check_single(self, combination: dict[Variable, Constant | CompoundTerm]) -> bool:
        """
        对实例化候选进行检查，并返回真假结果。TODO: 暂且没有和GroundedRule交互用到一些缓存，以后可以优化

        :param combination: 变量替换表
        """
        assertion = self.content.replace_variable(combination)
        # 变量表，每个Variable只用唯一一个指针的话，这里的时空开销会更低，不过并行难度会加大。但暂时这个级别的优化似乎意义不大
        if self._ask_equivalence(assertion):
            return True
        if self._ask_sk_system(assertion):  # noqa: SIM103
            return True

        return False

    def _ask_equivalence(self, assertion: Assertion) -> bool:
        """查询等价关系是否能证明该断言成立。"""
        return (self.grounded_rule.equivalence is not None and
                self.grounded_rule.equivalence.query_equivalence(assertion))

    def _ask_sk_system(self, assertion: Assertion) -> bool:
        return (self.grounded_rule.sk_system_handler is not None and
                len(self.grounded_rule.sk_system_handler.query_assertion(assertion)) > 0)

    def broadcast_total_table(self, total_table: _TupleTable) -> None:
        """
        广播 total_table，为规则级别的变量候选总表。

        :params: total_freevar (_TupleTable)
        """
        self.total_table = total_table

    def query_for_children(self, term: TERM_TYPE | CompoundTerm | None = None) -> Generator[_ConnectiveNode | _RuleNode]:
        """
        Yields:
            ConnectiveNode | RuleNode: 跳转到下一级节点，对应嵌套的ConnectiveNode或最终的RuleNode
        """
        yield from self.rule_or_connective_children

    def pass_tf_index(self) -> None:
        """
        传递自身节点的 true/false table 到子节点。
        """
        # 在一次传递之后，立即移除本身的tf_indexs，防止反复执行时重复传递
        for child in self.query_for_children():
            if not hasattr(child, "left_table"):
                child.left_table = self.tf_table
            elif isinstance(child, _ConnectiveNode):
                child.right_table = self.tf_table
        del self.tf_table

    def get_action_result(self) -> Generator[Assertion]:
        """
        获取 action assertion 计算得到的结果。

        :yield: 执行的结果
        :rtype: Assertion
        """  # noqa: DOC402
        yield from self._action_result
        self._action_result.clear()

    @property
    def ready_to_execute(self) -> bool:
        """
        AssertionNode 总是执行队列中的起点，因此始终处于 ready 状态。
        """
        return True

    @property
    def only_substitution(self) -> bool:
        """
        TODO：safety稳定后更新注释
        """
        return self.negated_assertion or not self.grounding_arguments

    def get_all_children(self) -> Generator[_ConnectiveNode | _RuleNode]:
        yield from self.rule_or_connective_children

    def reset(self) -> None:
        if hasattr(self, 'total_table'):
            del self.total_table
        if hasattr(self, 'tf_table'):
            del self.tf_table
