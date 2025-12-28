from __future__ import annotations

import logging
from typing import TYPE_CHECKING


from al_inference_engine.syntax import Rule, Variable, Constant, CompoundTerm

if TYPE_CHECKING:
    from al_inference_engine.config import Config
    from al_inference_engine.grounder import GroundedRule
    from ._tftable import TfTables
    from collections.abc import Generator
    from al_inference_engine.syntax import FACT_TYPE
    from al_inference_engine.syntax.base_classes import _QuestionRule
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class _RuleNode:
    """进入一个RuleNode节点表明当前规则已被满足，需要进行新事实的生成"""

    def __init__(self, content: Rule, grounded_rule: GroundedRule, args: Config) -> None:
        self.content: Rule = content
        self.grounded_rule: GroundedRule = grounded_rule
        self._args = args

        self.left_table: TfTables  # RuleNode的父节点只会有一个，我们默认为left_table来统一名称

    def __str__(self) -> str:
        return str(self.content)

    def exec_check(self) -> list[FACT_TYPE]:
        """
        返回所有的新事实，用于判断终止条件和更新事实库
        :returns list[FACT_TYPE]: 新事实
        """
        return self._gen_new_facts()

    def _gen_new_facts(self) -> list[FACT_TYPE]:
        """FIXME: 这里要避免重复，可能是在grounding阶段就尽量移除掉重复的取值？不过此时的合并方式影响中途的去重"""
        new_facts: list[FACT_TYPE] = []
        if not self.left_table.true:
            return new_facts

        total_true_table = self.left_table.true

        for combination in total_true_table.iter_rows():
            new_fact = self.content.head.replace_variable(combination)
            new_facts.append(new_fact)

            if self._args.run.trace:
                self._trace(new_fact, combination)

        if self._args.executor.anti_join_used_facts:
            self.grounded_rule.receive_true_table(total_true_table)

        return new_facts

    @staticmethod
    def get_all_children() -> Generator[None]:
        """
        Yields:
            None: 因为RuleNode没有子节点，所以返回None
        """
        yield None

    def reset(self) -> None:
        if hasattr(self, 'left_table'):
            del self.left_table

    def _trace(self, new_fact: FACT_TYPE, combination: Mapping[Variable, Constant | CompoundTerm]) -> None:
        new_rule = Rule.from_parts(
            head=new_fact,
            body=self.content.body.replace_variable(combination),
            priority=self.content.priority,
        )

        for head in new_rule.head_units:
            self.grounded_rule.inference_path.add_infer_edge(consequent=head,
                                                             antecedents=new_rule.body_units,
                                                             grounded_rule=self.content.replace_variable(combination))  # FIXME: 这里
            # 存一整个grounded rule的instance，是不是有点太重了。而如果只是存一个实例化的Rule instance，那好像又不需要传


class _QuestionRuleNode(_RuleNode):
    """问题规则节点：额外负责收集查询解"""

    def __init__(self, content: _QuestionRule, grounded_rule: GroundedRule, args: Config) -> None:
        super().__init__(content, grounded_rule, args)
        self.question_rule = content
        self.solutions: list[Mapping[Variable, Constant | CompoundTerm]] = []

    def _gen_new_facts(self) -> list[FACT_TYPE]:  # TODO: 考虑与rule_node中的_gen_new_facts合并
        """生成新事实的同时收集查询解"""
        new_facts: list[FACT_TYPE] = []
        if not self.left_table.true:
            return new_facts

        total_true_table = self.left_table.true
        new_fact = self.content.head
        new_facts.append(new_fact)

        for combination in total_true_table.iter_rows():
            self.solutions.append(combination)

            if self._args.run.trace:
                self._trace(new_fact, combination)

        if self._args.executor.anti_join_used_facts:
            self.grounded_rule.receive_true_table(total_true_table)

        return new_facts

    def reset(self) -> None:
        """重写 reset：额外清空 solutions"""
        super().reset()
        self.solutions.clear()
