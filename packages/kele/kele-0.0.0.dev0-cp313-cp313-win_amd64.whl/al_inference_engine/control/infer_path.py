from __future__ import annotations

import warnings
from pyvis.network import Network
from collections import deque

from typing import TYPE_CHECKING, Literal
from al_inference_engine.syntax import Assertion, Formula
import logging
from al_inference_engine.syntax import FACT_TYPE

if TYPE_CHECKING:
    from al_inference_engine.config import RunControlConfig
    from collections.abc import Sequence
    from al_inference_engine.syntax import Rule
    from al_inference_engine.equality import Equivalence

logger = logging.getLogger(__name__)


# 单个推理步：记录一个事实由哪条规则得到，以及它与前后事实的连接
class FactStep:
    """与上游/下游的事实联系的封装，记录事实来源用的"""
    def __init__(self, content: FACT_TYPE, infer_step: Rule | tuple[Assertion, ...] | None,
                fact_type: Literal['premise', 'equivalence', 'rule_infer']) -> None:
        # 当前仅记录等价类推导的“存在性”，不追溯具体等价链路
        # TODO: 可扩展记录推理深度或来源解释
        self.fact_type: Literal['premise', 'equivalence', 'rule_infer'] = fact_type  # 事实的类型
        self.content: FACT_TYPE = content        # 实例化后的事实
        self.infer_step: Rule | tuple[Assertion, ...] | None = infer_step  # 派生该事实的规则，若由等价关系/同余闭包推导则为tuple，
        # 若为前提事实则为 None
        self._next_facts: list[FactStep] = []   # 由当前事实推演出的下游事实
        self._prev_facts: list[FactStep] = []   # 支撑当前事实的上游事实

    def add_next(self, fact: FactStep) -> None:
        """将事实与它帮助推导的下游事实联系起来"""
        self._next_facts.append(fact)

    def add_prev(self, fact: FactStep) -> None:
        """将事实连接到支持它的上游事实"""
        self._prev_facts.append(fact)

    @property
    def next(self) -> tuple[FactStep, ...]:
        """下游事实"""
        return tuple(self._next_facts)

    @property
    def prev(self) -> tuple[FactStep, ...]:
        """上游事实"""
        return tuple(self._prev_facts)

    @property
    def step_name(self) -> str:
        """
        FactStep的名称，用于打印
        """
        if self.fact_type == 'premise':
            return f"无前提事实：{self.content !s}"
        if self.fact_type == 'equivalence':
            return f"等价推出事实：{self.content !s}"
        return f"规则推导：{self.infer_step !s} 新事实({self.content !s})"

    def __repr__(self) -> str:  # pragma: no cover
        rule_name = getattr(self.infer_step, "name", None)
        return f"FactStep({self.content}, rule={rule_name})"

    def __hash__(self) -> int:
        return hash((self.content, self.infer_step))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FactStep) and self.content == other.content and self.infer_step == other.infer_step


class InferencePath:
    """
        存储推理图：
            1. forward  : (antecedent_fact, rule)  -> [consequent_facts]
            2. reverse  : (consequent_fact, rule)  -> [antecedent_facts]
    """
    def __init__(self, args: RunControlConfig) -> None:
        self._args = args

        self.fact_factstep_pool: dict[FACT_TYPE, FactStep] = {}
        self.terminal_step: FactStep | None = None  # 记录最后的终点fact，通常是question对应的fact
        self.equivalence: Equivalence | None = None
        self.initial_facts: set[FACT_TYPE] = set()

        self._fact_counter = 1
        self._step_counter = 1
        self.fact_factid_map: dict[FACT_TYPE, str] = {}
        self.step_stepid_map: dict[str, str] = {}

    def set_equivalence(self, equivalence: Equivalence) -> None:
        """
        设置等价关系处理器
        """
        self.equivalence = equivalence

    def _add_initial_facts(self, facts: Sequence[FACT_TYPE] | FACT_TYPE) -> None:
        """
        添加初始事实
        """
        if isinstance(facts, FACT_TYPE):
            facts = [facts]

        for fact in facts:
            if isinstance(fact, Assertion):
                self.initial_facts.add(fact)
                self.initial_facts.add(self._reverse_fact(fact))
            else:
                self.initial_facts.add(fact)

    def _is_validate_none_premise_assertion(self, fact: Assertion) -> bool:
        """
        检查一个fact是否是一个合法的前提为None的Assertion
        以下两种情况前提为None
        1、fact出现在initial_fact里面
        2、左右显然相等
        """
        return fact in self.initial_facts or fact.lhs == fact.rhs or fact.is_action_assertion

    def _query_equiv_step(self, fact: FACT_TYPE) -> FactStep:
        """
        获取一个fact的推理路径，总共由三个可能：
        1. 它是由等价关系推出来的
        2. 它是由规则推出来的
        3. 它是一个前提事实
        最后都会返回一个FactStep

        :param fact: 待检查的事实
        :type fact: FACT_TYPE
        :raises RuntimeError: 若等价关系处理器未设置
        :return: 若fact是由等价关系推出来的，则返回等价关系的FactStep，否则返回None
        :rtype: FactStep
        """  # noqa: DOC501
        if fact in self.fact_factstep_pool:
            # fact 已记录过推理路径，直接复用
            return self.fact_factstep_pool[fact]
        if isinstance(fact, Assertion) and self._is_validate_none_premise_assertion(fact):
            # fact是一个前提事实
            return FactStep(fact, None, 'premise')
        # Assertion的factstep需要考虑是否是等价关系推导出来的，但是Formula类型的（实质只可能为NOT Assertion）则不需要
        if isinstance(fact, Formula) and isinstance(fact.formula_left, Assertion) and fact.connective == 'NOT':
            # NOT Assertion类型的Fact不需要考虑等价关系
            # 在正常情况下，它自然是成立的前提事实，否则是不可能推理出结果的
            return FactStep(fact, None, 'premise')
        if isinstance(fact, Formula):
            raise TypeError("Rule的前提不能包含除了AND和NOT的其他连接词。这个错误可能来源于CNF_convert的错误")
        if self.equivalence is None:
            raise RuntimeError("等价关系处理器未设置，无法正确记录等价类事实的推理路径")
        if self.equivalence.query_equivalence(fact):
            fact_step = FactStep(fact, None, 'equivalence')  # HACK：暂时不详细处理等价关系推出的事实，
            # 后续需要获取等价关系的解释
            self.fact_factstep_pool[fact] = fact_step
            self.fact_factstep_pool[self._reverse_fact(fact)] = fact_step  # 对称事实也要记录进去
            return fact_step

        raise ValueError(f"fact {fact!s} 不成立，无法记录推理路径")

    @staticmethod
    def _reverse_fact(fact: FACT_TYPE) -> FACT_TYPE:
        if isinstance(fact, Assertion):
            return Assertion.from_parts(fact.rhs, fact.lhs)
        return fact

    def add_infer_edge(self,
                       consequent: FACT_TYPE,  # FIXME: 这里得缩减为Assertion
                       antecedents: list[FACT_TYPE] | None = None,
                       grounded_rule: Rule | None = None,
                    ) -> None:
        """
        录入一条推理边：多前提 → 单结论
        :param antecedents: 对应某条rule的前提，不过已经实例化过了
        :param consequent: 对应规则后件的实例化结果
        :param grounded_rule: 触发推理的规则
        :return: None
        """
        if antecedents is None:
            return self._add_initial_facts(consequent)

        if consequent in self.fact_factstep_pool:
            # 事实已经存在，推理路径默认保留一条即可
            # TODO: 可选保留多条推理路径
            return None
        # 记录结论的推理路径
        conse_step = FactStep(consequent, grounded_rule, 'rule_infer')

        self.fact_factstep_pool[consequent] = conse_step
        self.fact_factstep_pool[self._reverse_fact(consequent)] = conse_step  # 对称事实也要记录进去
        for fact in antecedents:
            factstep = self._query_equiv_step(fact)
            self.fact_factstep_pool[fact] = factstep
            self.fact_factstep_pool[self._reverse_fact(fact)] = factstep  # 对称事实也要记录进去

            factstep.add_next(conse_step)
            conse_step.add_prev(factstep)
        return None

    def add_terminal_status(self, termnial_fact: FACT_TYPE) -> None:
        """记录终点事实"""
        try:
            self.terminal_step = self._query_equiv_step(termnial_fact)  # termnimal_step也要考虑由等价关系推出的可能
        except ValueError:
            warnings.warn(f"终点事实 {termnial_fact!s} 显然成立", stacklevel=1)
            self.terminal_step = None

    @staticmethod
    def _print_log_info(prev_fact_steps: list[FactStep], infer_path: deque[FactStep], terminal_fact: FACT_TYPE) -> None:
        logger.info("================无前提事实:=================")
        for prev_fact_counter, fact_step in enumerate(prev_fact_steps):
            logger.info("%d. %s", prev_fact_counter + 1, fact_step.step_name)  # FIXME: 这里的注释有点奇怪，一个数字
            # 一个name。博洋改到这里的时候留意一下，反正你的infer最近要动，我就不细究了
        logger.info("================推理路径:=================")
        for infer_fact_counter, fact_step in enumerate(infer_path):
            logger.info("step %d: %s", infer_fact_counter + 1, fact_step.step_name)
        logger.info("================终点事实:=================")
        logger.info("终点事实：%s", terminal_fact)

    def get_infer_graph(self, terminal_fact: FACT_TYPE | None = None) -> tuple[list[FactStep], FACT_TYPE | None]:
        """
        获得推理路径
        :param terminal_fact: 推理的终点事实，默认是question对应的fact
        :return: 推理路径，终点事实
        """
        if not self._args.trace:
            warnings.warn("未开启推理路径跟踪，无法打印推理路径", stacklevel=5)
            return [], None
        terminal_step = self.terminal_step if terminal_fact is None else self._query_equiv_step(terminal_fact)

        infered: set[FactStep] = set()
        if terminal_step is not None:
            infer_path: deque[FactStep] = deque()
            prev_fact_steps: list[FactStep] = []
            cur_fact_queue = deque([terminal_step])
            while cur_fact_queue:
                cur_fact_step = cur_fact_queue.popleft()
                if cur_fact_step in infered:  # 推出的事实不再重复推导
                    continue
                infered.add(cur_fact_step)

                if cur_fact_step.fact_type != 'premise':
                    infer_path.appendleft(cur_fact_step)
                else:
                    # 前提事实全部在第一步展示
                    # 这里的前提事实指的是原始Premises中真正被用于推理的那些前提事实
                    prev_fact_steps.append(cur_fact_step)
                if cur_fact_step.infer_step is not None:
                    cur_fact_queue.extend(cur_fact_step.prev)

            self._print_log_info(prev_fact_steps, infer_path, terminal_step.content)
            prev_fact_steps.extend(infer_path)  # 将分开的两个集合合并起来返回，此时顺序已经被确定下来
            return prev_fact_steps, terminal_step.content
        warnings.warn("推理引擎没能推理出结果，或者终点事实显然成立", stacklevel=1)
        return [], None

    def _get_fact_id(self, fact: FACT_TYPE, net: Network) -> str:
        if fact not in self.fact_factid_map:
            self.fact_factid_map[fact] = f"fact{self._fact_counter}"
            self._fact_counter += 1
            net.add_node(self.fact_factid_map[fact], label=self.fact_factid_map[fact], title=str(fact))
        return self.fact_factid_map[fact]

    def _get_step_id(self, step_name: str, net: Network) -> str:
        if step_name not in self.step_stepid_map:
            self.step_stepid_map[step_name] = f"step{self._step_counter}"
            self._step_counter += 1
            net.add_node(self.step_stepid_map[step_name], label=self.step_stepid_map[step_name], title=str(step_name), shape="square", color="red")
        return self.step_stepid_map[step_name]

    def gennerate_infer_path_graph(self, infer_path: list[FactStep], terminal_fact: FACT_TYPE | None = None) -> None:
        """
        生成推理路径的图
        :param infer_path: 推理路径
        :param terminal_fact: 推理的终点事实，默认是question对应的fact
        :return: None
        """
        net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
        self._fact_counter = 1
        self._step_counter = 1
        self.fact_factid_map.clear()
        self.step_stepid_map.clear()
        if terminal_fact is not None:
            self.fact_factid_map[terminal_fact] = "terminal_fact"
            net.add_node("terminal_fact", label="终点事实", shape="star", color="red")

        for fact_step in infer_path:
            cur_fact_id = self._get_fact_id(fact_step.content, net)
            cur_step_id = self._get_step_id(fact_step.step_name, net) if fact_step.infer_step is not None else None
            if cur_step_id is not None:
                for fact in fact_step.prev:
                    prev_fact_id = self._get_fact_id(fact.content, net)
                    net.add_edge(prev_fact_id, cur_step_id, label="前提", color="blue")
                net.add_edge(cur_step_id, cur_fact_id, label="结论", color="red", arrows="to")
            else:
                for nodes in net.nodes:
                    if nodes["id"] == cur_fact_id:
                        nodes["label"] = "无前提事实"
                        nodes["shape"] = "triangle"
                        nodes["color"] = "green"
        net.save_graph("infer_path.html")

    def reset(self) -> None:
        """重置推理路径"""
        self.fact_factstep_pool.clear()
        self.terminal_step = None
        self.initial_facts.clear()
