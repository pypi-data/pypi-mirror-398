from __future__ import annotations

from typing import TYPE_CHECKING
from al_inference_engine.syntax import CompoundTerm

if TYPE_CHECKING:
    from al_inference_engine.syntax import Operator, Constant
    from ._term import _AtomCompoundTermNode
    from collections.abc import Generator


class _OperatorNode:
    """用于维护从fact → list[_AtomCompoundTermNode]的索引，每当一个fact传入时将会进入一个OperatorNode，然后去对其连接的TermNode进行实例化"""
    def __init__(self, operator: Operator) -> None:
        self.term_children: list[_AtomCompoundTermNode] = []
        self.operator = operator

    def __str__(self) -> str:
        return str(self.operator)

    def add_child(self, term: _AtomCompoundTermNode) -> None:
        """建立OperatorNode和CompoundTermNode的连边"""
        self.term_children.append(term)

    def exec_unify(self,
                   term: CompoundTerm[Constant | CompoundTerm] | Constant,
                   *,
                   allow_unify_with_nested_term: bool = True) -> None:
        """
        _OperatorNode会对自己的所有child执行unify，而child的代码保证了这个Unify操作是可控的：
        即它只局限在直接和这个_OperatorNode相连的child
        后续的传递过程也不再会是exec_unnify

        :param term (CompoundTerm | Constant): 待实例化的Term，某种意义上只有可能是AtomCompoundTerm，但是为了避免外层的类型检查，
            我们还是采纳这种写法
        :param allow_unify_with_nested_term: 是否允许与嵌套的Term进行unify
        """
        if isinstance(term, CompoundTerm):
            for child in self.term_children:
                child.exec_unify(term, allow_unify_with_nested_term=allow_unify_with_nested_term)

    def query_for_children(self, term: CompoundTerm | Constant | None = None) -> Generator[_AtomCompoundTermNode]:
        """
        直接返回所有子节点，暂时没有其他额外操作
        term参数纯粹为了格式统一
        """  # noqa: DOC402
        yield from self.term_children

    def get_all_children(self) -> Generator[_AtomCompoundTermNode]:
        """
        Yields:
            TermNode: 用于汇总同Operator的多个TermNode，所以跳转到下一级为TermNode
        """
        yield from self.term_children

    def reset(self) -> None:
        pass
