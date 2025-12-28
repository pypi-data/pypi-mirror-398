from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING

from ._tftable import TfTables

if TYPE_CHECKING:
    from al_inference_engine.syntax import TERM_TYPE, CompoundTerm, Formula
    from collections.abc import Generator
    from ._rule import _RuleNode


class _ConnectiveNode:
    """表达p^q等formula，换句话是若干（正常是1-2个）Assertion及逻辑连接词形成了一个Formula。主要是bool值判断和候选值的join、传递"""
    def __init__(self, formula: Formula) -> None:
        self.rule_or_connective_children: list[_ConnectiveNode | _RuleNode] = []
        self.content = formula

        self.tf_table: TfTables
        self.left_table: TfTables
        self.right_table: TfTables

        self.left_or_right: int  # 记录其为左父节点还是右父节点，0为左父节点，1为右父节点

    def __str__(self) -> str:
        return str(self.content)

    def add_child(self, node: _ConnectiveNode | _RuleNode) -> None:
        self.rule_or_connective_children.append(node)

    def exec_check(self) -> None:  # HACK: 当前计算图方案有大量冗余难以优化，后续可能考虑修改
        """
        对单一ConnectiveNode进行处理：
        对于AND节点而言，一者为假即为假，所以false_table进行并集。需要左右两侧都为真才能为真，所以会将传来的true_table做交集。
        对于OR节点而言，两者为假才能为假，所以false_table进行交集。需要左右一者为真就能为真，所以会将传来的true_table做并集。
        NOT节点只需要反转true_table和false_table就好

        :raises TypeError: 未知的connective名称，在真正的图中只会处理AND, OR, NOT三种节点
        """  # noqa: DOC501
        # 首先应该基于left_token和right_token获得token组。组合方式自由组合原则，即左侧可以自由地和右侧的一个token组合

        if self.content.connective == 'NOT':
            # NOT节点导致True,False的table反转，即原本为True的一组取值，在经过NOT节点之后反转为False。我们只需要交换true,false table即可
            # 同时，注意NOT节点只会有一个父节点，于是true_table和false_table都只有0
            false_table = self.left_table.true
            true_table = self.left_table.false
        elif self.content.connective == 'AND':
            # AND节点，只有同时为真的情况才为真，所以将两个true_table union之后就是此节点的true_table
            # 左右一侧为假即为假，所以剩下情况一一对应union得到三个false table。最后直接concat拼接起来，就是此节点的false_table
            all_false_table = [self.left_table.false.union_table(self.right_table.false), self.left_table.false.union_table(self.right_table.true),
                               self.left_table.true.union_table(self.right_table.false)]
            false_table = reduce(lambda x, y: x.concat_table(y), all_false_table)
            true_table = self.left_table.true.union_table(self.right_table.true)
        elif self.content.connective == 'OR':
            # OR节点，类似前面
            all_true_table = [self.left_table.true.union_table(self.right_table.true), self.left_table.false.union_table(self.right_table.true),
                               self.left_table.true.union_table(self.right_table.false)]
            true_table = reduce(lambda x, y: x.concat_table(y), all_true_table)
            false_table = self.left_table.false.union_table(self.right_table.false)
        else:
            raise TypeError("Unknown connective node")
        self.tf_table = TfTables(true=true_table, false=false_table)
        self._remove_parent_tables()
        # 执行完成之后就能移除父节点传来的tftables了，这样可以保证ready_for_execute属性控制不会执行第二次exec_execute

    def pass_tf_index(self) -> None:
        """
        传递自身节点的tf_index到子节点。
        """
        # 在一次传递之后，立即移除本身的tf_indexs，防止反复执行时重复传递
        for child in self.query_for_children():
            if not hasattr(child, "left_table"):
                child.left_table = self.tf_table
            elif isinstance(child, _ConnectiveNode):
                child.right_table = self.tf_table

        del self.tf_table

    def get_all_children(self) -> Generator[_ConnectiveNode | _RuleNode]:
        """
        Yields:
            ConnectiveNode | RuleNode: 跳转到下一级节点，对应嵌套的ConnectiveNode或最终的RuleNode
        """
        yield from self.rule_or_connective_children

    def query_for_children(self, term: TERM_TYPE | CompoundTerm | None = None) -> Generator[_ConnectiveNode | _RuleNode]:
        """
        Yields:
            ConnectiveNode | RuleNode: 跳转到下一级节点，对应嵌套的ConnectiveNode或最终的RuleNode
        """
        yield from self.rule_or_connective_children

    def _remove_parent_tables(self) -> None:
        if hasattr(self, "left_table"):
            del self.left_table
        if hasattr(self, "right_table"):
            del self.right_table

    @property
    def ready_to_execute(self) -> bool:
        """
        这个属性作为判断是否适合执行exec_check的依据
        当它返回false时，表明仅有一个父节点提供了它的tfIndexs信息，仍需要等待第二个父节点提供，外层需要在此时忽此节点
        由于每次父节点执行完成后，都一定会通过query_for_children把此节点加入队列，所以一定会有某次加入时节点ready_to_execute为真
        """
        if self.content.connective == 'NOT':
            # NOT节点只有一个父节点
            return hasattr(self, "left_table")
        # AND, OR节点都有两个父节点，所以这里要求tf_indexs_list>=2来保证父节点都已经执行。注意：每个父节点只执行一次，这由外层控制
        return hasattr(self, "left_table") and hasattr(self, "right_table")

    def reset(self) -> None:
        self._remove_parent_tables()
        if hasattr(self, "tf_table"):
            del self.tf_table
