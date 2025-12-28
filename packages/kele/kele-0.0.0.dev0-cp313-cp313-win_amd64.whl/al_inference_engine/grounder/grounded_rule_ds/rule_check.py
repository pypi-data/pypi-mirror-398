from __future__ import annotations

from collections import defaultdict, deque
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, cast, Any
from graphviz import Digraph

from ._nodes import _OperatorNode, _AssertionNode, _ConnectiveNode, _BuildTerm, _RuleNode, _AtomCompoundTermNode, _RootNode, _QuestionRuleNode
from al_inference_engine.syntax import _QuestionRule
from al_inference_engine.syntax import Assertion, Formula, Variable, AtomCompoundTerm
import operator


if TYPE_CHECKING:
    from al_inference_engine.config import Config
    from al_inference_engine.syntax import FACT_TYPE, TERM_TYPE
    from .grounded_class import GroundedRule


class RuleCheckGraph:
    """将Assertion/Formula级别的规则处理为易于处理的图结构"""

    def __init__(self, cur_rule: GroundedRule, args: Config) -> None:
        self.cur_rule = cur_rule
        self.args = args

        self.antecedent = cur_rule.rule.body
        self.abstract_rule = cur_rule.rule
        self.execute_nodes: list[_AssertionNode] = []  # 记录所有的AssertionNode，这将是execute开始的地方
        if isinstance(self.abstract_rule, _QuestionRule):
            self.rule_node: _RuleNode = _QuestionRuleNode(self.abstract_rule, self.cur_rule, self.args)
        else:
            self.rule_node = _RuleNode(self.abstract_rule, self.cur_rule, self.args)
            # 记录RuleNode的位置，这将是execute结束的地方

        self.grounding_nodes: list[_AssertionNode] = []  # HACK: 记录所有参与grounding过程的AssertionNode。以后total table下沉到TermNode
        # 后，这里的类型标注似乎应当转为list[TermNode]
        self.substitution_nodes: list[_AssertionNode] = []  # HACK: 记录所有不参与grounding过程、只执行substitution的AssertionNode。
        # 以后total table下沉到TermNode后，这里的类型标注似乎应当转为list[TermNode]
        # 在DNF的情况下，不应该存在某个Assertion既可以取True又可以取False

        self.graph_root = self._convert_formula_into_graph(self.antecedent)

        sat_result = self.cur_rule.rule.get_models
        for assertion_node in self.execute_nodes:
            if sat_result[assertion_node.content][0] and sat_result[assertion_node.content][1]:
                assertion_node.keep_table = None
            elif sat_result[assertion_node.content][0]:
                assertion_node.keep_table = True
            elif sat_result[assertion_node.content][1]:
                assertion_node.keep_table = False

    def _build_assertion_structure(self, cur_assertion: Assertion, root_node: _RootNode) -> _AssertionNode:
        """
        构造 AssertionNode 及其对应的 term 子图结构。
        """
        # TODO: 这里的工程封装还有待商榷。比如可能这些Assertion不在图上出现或者不在query_children等处出现
        # 被not影响也是AssertionNode不进入join流程的可能性之一
        cur_rule = self.cur_rule

        term_node_builder = _BuildTerm(cur_rule, root_node, self.args)

        assertion_node = _AssertionNode(content=cur_assertion,
                                        grounded_rule=cur_rule, negated_assertion=self._influenced_by_not(cur_assertion))

        drop_left, drop_right = self._drop_assertion_term(assertion_node)

        term_l = term_node_builder.build_term_structure(cur_term=cur_assertion.lhs, root_node=root_node, only_substitution=drop_left)
        term_r = term_node_builder.build_term_structure(cur_term=cur_assertion.rhs, root_node=root_node, only_substitution=drop_right)

        term_l.add_child(assertion_node)
        term_r.add_child(assertion_node)

        self.execute_nodes.append(assertion_node)
        return assertion_node

    def _drop_assertion_term(self, assertion_node: _AssertionNode) -> tuple[bool, bool]:
        """
        判断 AssertionNode 左右 term 是否仅做 substitution。
        """
        assertion = assertion_node.content
        term_l = assertion.lhs
        term_r = assertion.rhs

        if assertion_node.negated_assertion:
            # 否定的Assertion，左右都要被丢弃
            return True, True

        # 默认情况：如果term_l或term_r有free_variable，那么就不被丢弃
        drop_left = not bool(term_l.free_variables)
        drop_right = not bool(term_r.free_variables)
        if drop_left and drop_right:
            # 如果左右都被丢弃，那么就没有必要继续判断了
            return drop_left, drop_right

        # action_term需要被丢弃
        if assertion_node.content.is_action_assertion:
            if term_l.is_action_term:
                drop_left = True
            if term_r.is_action_term:
                drop_right = True
            # 如果存在action_term，那么就不应该进入下面的优化流程，所以直接return
            return drop_left, drop_right

        # 优化：当前term是Variable，且被包含在另一侧的时候，可以被丢弃
        if self._variable_included(term_l, term_r):
            # 如果term_l是Variable，被包含于term_r的free_variables中，则丢弃term_l
            drop_left = True
        elif self._variable_included(term_r, term_l):
            # 这里使用elif，保证了x=x这种互相包含的情况下不会把两边一起丢弃掉
            # 这里无需再判断drop_left = False，因为能走到这一步意味着不是negated_assertion也不是action_assertion
            # 而且term_l一定有free_variable，所以drop_left一定是False
            drop_right = True

        return drop_left, drop_right

    def _build_formula_structure(self, cur_formula: Formula, root_node: _RootNode) -> _ConnectiveNode:
        """
        拆解 Formula 并构造 ConnectiveNode。
        """
        r_formula = cur_formula.formula_right

        connective_node = _ConnectiveNode(formula=cur_formula)
        # 当前节点是否被not影响，取决于其父节点是否被not影响，以及当前节点的算子
        # 传递的not_influenced如果是True，意味着它的某个字节是NOT，如果此时它自身还是NOT，最后的结果是它的父节点不被NOT影响
        father_node = self._call_assertion_or_formula_builder(cur_formula.formula_left, root_node)
        father_node.add_child(connective_node)

        if r_formula is not None:
            father_node = self._call_assertion_or_formula_builder(r_formula, root_node)
            father_node.add_child(connective_node)  # 这里就是添加ConnectiveNode的地方，左右两侧的最末Node都需要_ConnectiveNode作为子节点

        return connective_node  # 这里返回的是ConnectiveNode

    def _call_assertion_or_formula_builder(self, input_formula: FACT_TYPE, root_node: _RootNode) ->\
        _AssertionNode | _ConnectiveNode:
        if isinstance(input_formula, Assertion):
            return self._build_assertion_structure(input_formula, root_node)
        return self._build_formula_structure(input_formula, root_node)

    def _convert_formula_into_graph(self, formula: FACT_TYPE) -> _RootNode:
        """
        将规则前提转换为图结构，具体说明见 grounder/README.md。
        """
        root_node = _RootNode()

        if isinstance(formula, Assertion):
            # 只有Assertion，此时的任何AssertionNode自然都不会被NOT影响
            a_node = self._build_assertion_structure(formula, root_node)
            a_node.add_child(self.rule_node)

        elif isinstance(formula, Formula):
            # 此时还没有拆分到基础单元，我们应当继续拆分，如何拆分呢？递归地拆分即可
            # 我们除了应当建立两个TermNode和一个join节点，还应当建立一个ConnectiveNode，将两个TermNode和一个join节点连接到ConnectiveNode上。
            # 最底层节点没有子connective节点，自然也不认为是被NOT影响
            f_node = self._build_formula_structure(formula, root_node)
            # 最底层的节点，连接到RuleNode
            f_node.add_child(self.rule_node)

        # 一些初始变量声明
        grounding_nodes = []
        substitution_nodes = []

        for node in self.execute_nodes:
            if node.only_substitution:
                substitution_nodes.append(node)
            else:
                grounding_nodes.append(node)

        self.grounding_nodes = self._grounding_nodes_merge_optimization(grounding_nodes)
        self.substitution_nodes = self._sort_substitution_nodes(substitution_nodes)

        return root_node

    @staticmethod
    def _grounding_nodes_merge_optimization(assertion_list: list[_AssertionNode]) -> list[_AssertionNode]:
        """
        贪心地优化AssertionNode的合并顺序
        具体地，从列数最多的开始，每次选择与当前合并表重合度最高的表进行合并。
        """
        if not assertion_list:
            return assertion_list

        variable_count: defaultdict[Variable, int] = defaultdict(int)
        for node in assertion_list:
            for var in node.content.free_variables:
                variable_count[var] += 1

        result_merge_order: list[_AssertionNode] = [max(assertion_list, key=lambda node: (
            len(variable_count) - sum((variable_count[var] == 1) for var in node.content.free_variables)
        ))]

        # 从与其他表重合度最高的开始
        remaining_tables: list[_AssertionNode] = assertion_list.copy()  # 移除第一个表
        remaining_tables.remove(result_merge_order[0])
        cur_table_columns: set[Variable] = set(result_merge_order[0].content.free_variables)

        while remaining_tables:
            cur_table = result_merge_order[-1]
            cur_table_columns |= set(cur_table.content.free_variables)

            # 使用max和key函数找到最佳匹配的AssertionNode
            # 原则是：重合度高的优先，重合度相同的话，列数多的优先
            best_node = max(remaining_tables,
                            key=lambda node: (
                                len(set(node.content.free_variables) & cur_table_columns),
                                len(node.content.free_variables)  # 列数多的优先
                            ))
            remaining_tables.remove(best_node)
            result_merge_order.append(best_node)

        return result_merge_order

    def _influenced_by_not(self, assertion: Assertion) -> bool:
        """
        判断某个 assertion 是否被 NOT 影响。

        :param assertion_node: 待判断的断言节点
        :type assertion_node: _AssertionNode
        :return: 是否被NOT影响
        :rtype: bool
        """
        sat_result = self.cur_rule.rule.get_models
        # 如果当前Assertion取False，那么意味着它被NOT影响，并进行记录
        # TODO: 目前来看这个记录和drop_true_table/drop_false_table有重合，可能可以简化
        return sat_result[assertion][1]

    @staticmethod
    def _variable_included(left: TERM_TYPE, right: TERM_TYPE) -> bool:
        """
        如果左侧是Variable并且被严格包含在右侧的Variables中，那么返回True，否则返回False
        """
        if isinstance(left, Variable):
            return set(left.free_variables) <= set(right.free_variables)
        return False

    def _sort_substitution_nodes(self, substitution_nodes: list[_AssertionNode]) -> list[_AssertionNode]:
        """按依赖关系排序 substitution nodes。"""
        # 邻接表：arg -> [var]，表示先处理 arg，再处理 var
        self._substitution_graph: dict[Variable, list[Variable]] = defaultdict(list)

        substitution_nodes_var: list[tuple[_AssertionNode, Variable]] = []

        for node in substitution_nodes:
            lhs = node.content.lhs
            rhs = node.content.rhs

            if TYPE_CHECKING:
                lhs, rhs = cast("tuple[Variable, AtomCompoundTerm] | tuple[AtomCompoundTerm, Variable]", (lhs, rhs))

            if isinstance(lhs, Variable):  # 写成一行的时候mypy过不去
                var = lhs
                term = rhs
            else:
                if TYPE_CHECKING:  # 一定有一边是Variable，是对action op写法的限制。 TODO：以后期望从类型上强制引入这个限制，现在只是
                    # 对原代码的最小改动
                    rhs = cast("Variable", rhs)

                term = lhs
                var = rhs

            # 建边：_term.arguments 中的每个变量 -> _var
            # 并确保 _var 也作为节点出现（即便没有出边）
            self._substitution_graph.setdefault(var, [])
            for arg in getattr(term, "arguments", ()):
                self._substitution_graph[arg].append(var)

            substitution_nodes_var.append((node, var))

        # 计算拓扑序，并建立节点到其位置的映射
        topo_order = list(TopologicalSorter(self._substitution_graph).static_order())
        pos = {v: i for i, v in enumerate(topo_order)}

        # 根据拓扑位置从小到大排序（越靠前越应先执行）
        substitution_nodes_order = sorted(
            ((node, pos.get(var, float("inf"))) for node, var in substitution_nodes_var),
            key=operator.itemgetter(1),
            reverse=True,
        )

        return [n for n, _ in substitution_nodes_order]

    def reset(self) -> None:
        """重置RuleCheckGraph的状态，用于新一轮（iteration）的推理。仅仅clear是权宜之计，影响效率"""
        node_queue: deque[_RootNode | _OperatorNode | _AssertionNode |
                         _ConnectiveNode | _RuleNode | _AtomCompoundTermNode] = deque([self.graph_root])
        while node_queue:  # TODO: 这里似乎应该封个遍历用的函数
            node = node_queue.popleft()
            node.reset()
            node_queue.extend([u for u in node.get_all_children() if u is not None])

    def generate_graphviz(self, show_mode: str = "default", filename: str = 'rule_graph') -> None:  # noqa: C901
        """
        生成Graphviz格式的图结构可视化
        :param show_mode: 显示模式，可选值为"default"、"free_var"，如果选择free_var将会显示free_variables的信息
        :param filename: 输出文件名（不含扩展名）
        """

        dot = Digraph(comment='Rule Check Graph')
        visited: set[str] = set()

        def _add_nodes(node: _RootNode | _OperatorNode | _AssertionNode |  # noqa: C901
                      _ConnectiveNode | _RuleNode | _AtomCompoundTermNode | None) -> None:
            if node is None:
                return

            node_id = str(id(node))
            if node_id in visited:
                return
            visited.add(node_id)

            # 根据节点类型设置样式
            if isinstance(node, _RootNode):
                dot.node(node_id, 'Root', shape='ellipse', color='green')
            elif isinstance(node, _OperatorNode):
                dot.node(node_id, f'Operator:\n{node.operator.name}', shape='box', color='blue')
            elif isinstance(node, _AssertionNode):
                dot.node(node_id, 'Assertion', shape='diamond', color='orange')
            elif isinstance(node, _ConnectiveNode):
                dot.node(node_id, f'Connective:\n{node.content.connective}', shape='hexagon', color='purple')
            elif isinstance(node, _RuleNode):
                dot.node(node_id, 'Rule Endpoint', shape='doubleoctagon', color='red')
            elif isinstance(node, _AtomCompoundTermNode):
                if show_mode == "free_var":
                    dot.node(node_id,
                             f'AtomCompoundTerm:\n{node.node_representative}\nfree_vars:\n{node.get_free_var_name()}',
                             shape='ellipse')
                elif show_mode == "default":
                    dot.node(node_id, f'AtomCompoundTerm:\n {node.node_representative!s}', shape='ellipse')

            # 递归处理子节点
            for child in node.get_all_children():
                child_id = str(id(child))
                dot.edge(node_id, child_id)
                _add_nodes(child)

        # 从根节点开始遍历
        _add_nodes(self.graph_root)
        dot.render(filename, view=True)

    def generate_graph_represent(self) -> dict[str, list[Any]]:
        """
        用于生产代表图结构的一个字典，在pytest中使用

        :return: 代表图结构的字典
        :rtype: dict[str, tuple[list[str], list[dict[Any, Any]]]]
        """
        graph_represent = {}
        node_queue: deque[_RootNode | _OperatorNode | _AssertionNode |
                      _ConnectiveNode | _RuleNode | _AtomCompoundTermNode] = deque([self.graph_root])
        while node_queue:
            node = node_queue.popleft()
            key = str(node)
            if isinstance(node, _RuleNode):
                key = key[key.count(':'):].strip()  # hack: Rule.__str__加入了不确定的name，故此移除。也许以后把str(node)用一个专为图
                # 的str代替最好。但此时感觉引入了价值不大的复杂度

            if key not in graph_represent:
                if isinstance(node, (_AtomCompoundTermNode)):
                    str_freevar_table = node.freevar_table.table_represent
                    graph_represent[key] = [[str(u) for u in node.get_all_children()], str_freevar_table]
                else:
                    graph_represent[key] = [[str(u) for u in node.get_all_children()], [{}]]
            node_queue.extend([u for u in node.get_all_children() if u is not None])
        return graph_represent
