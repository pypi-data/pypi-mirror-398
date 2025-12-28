from collections.abc import Generator
from ._op import _OperatorNode
from al_inference_engine.syntax import CompoundTerm, Operator, TERM_TYPE
from ._term import _AtomCompoundTermNode, _VariableNode, _ConstantNode, _TermNode


class _RootNode:
    """
    这是图的入口
    """
    def __init__(self) -> None:
        self._variable_nodes: list[_AtomCompoundTermNode] = []  # 用于添加待匹配值为变量的AtomCompoundTermNode
        self._mapping_to_node: dict[Operator, _OperatorNode] = {}  # 用于添加某些CompoundTerm所对应的operator所形成的Node
        self._no_variable_nodes: list[_AtomCompoundTermNode] = []  # 用于添加待匹配值不含变量的AtomCompoundTermNode

    def __str__(self) -> str:
        return 'RootNode'

    def add_child(self, node: _OperatorNode | _AtomCompoundTermNode) -> None:
        """
        建立RootNode和OperatorNode | _AtomCompoundTermNode 的连边

        :param node: 待添加的节点
        """
        if isinstance(node, _OperatorNode):
            # 实际上这里一个Operator一定只对应一个OperatorNode，所以这么写应该是没问题的
            self._mapping_to_node[node.operator] = node
        elif isinstance(node, _VariableNode):
            self._variable_nodes.append(node)
        elif isinstance(node, (_ConstantNode, _TermNode)):
            self._no_variable_nodes.append(node)

    def query_for_children(self, term_or_const: TERM_TYPE | None = None) -> \
            tuple[_OperatorNode | _AtomCompoundTermNode, ...]:
        """
        对于Operator，我们查询它对应的_OperatorNode
        对于Constant，我们找到通配的VariableNode

        无任何传入参数，返回所有的OperatorNode和VariableNode

        :yield: 一个生成器，生成器里面是_OperatorNode或_AtomCompoundTermNode。如果没有任何可能的结果，那么返回None
        """
        if term_or_const is None:  # XXX: 用于洪泛地向下执行整张图，希望有机会移除
            return_list = list(self._mapping_to_node.values()) + self._variable_nodes
            return tuple(return_list)

        return_list = [*self._variable_nodes]
        if isinstance(term_or_const, CompoundTerm) and term_or_const.operator in self._mapping_to_node:
            return_list.append(self._mapping_to_node[term_or_const.operator])

        return tuple(return_list)

    def operator_exist(self, operator: Operator) -> _OperatorNode | None:  # HACK: 后续继续保留此函数还是选择别的方式记录有待商榷
        # HACK: 以及返回值是直接取出OperatorNode还是单纯返回是否存在也需要考虑  # noqa: ERA001
        """
        检查operator是否存在于图中

        :param operator: 待检查的operator
        :return: 如果存在，返回对应的_OperatorNode，否则返回None
        """
        if operator in self._mapping_to_node:
            return self._mapping_to_node[operator]
        return None

    def get_all_children(self) -> Generator[_OperatorNode | _AtomCompoundTermNode]:
        yield from self._mapping_to_node.values()
        yield from self._variable_nodes
        yield from self._no_variable_nodes

    def reset(self) -> None:
        pass
