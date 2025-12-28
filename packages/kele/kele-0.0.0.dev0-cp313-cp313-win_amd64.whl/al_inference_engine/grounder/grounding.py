from __future__ import annotations

import logging
import time

from .grounded_rule_ds import GroundedRuleDS, GroundedProcess, GroundedRule

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al_inference_engine.syntax import Rule, Question, GROUNDED_TYPE_FOR_UNIFICATION
    from al_inference_engine.knowledge_bases import FactBase, RuleBase
    from collections.abc import Sequence
    from al_inference_engine.control.grounding_selector import GroundingRuleSelector, GroundingAtomTermWithWildCardSelector

logger = logging.getLogger(__name__)


class Grounder:
    """Grounding过程最外层的数据结构，执行完整的grounding过程并与Executor对接"""
    def __init__(self,  # noqa: PLR0913
                 *,
                 fact_base: FactBase,
                 rule_base: RuleBase,
                 rule_selector: GroundingRuleSelector,
                 term_selector: GroundingAtomTermWithWildCardSelector,
                 grounded_structure: GroundedRuleDS,
                 rules_num_every_step: int = 5,
                 facts_num_for_each_rule: int = 10):  # 这些参数是不是也进selector即可
        """
        :param fact_base: 事实库指针，供 selector 与 grounding 使用
        :param rule_base: 规则库指针（后续将由 selector 直接接管）
        :param rules_num_every_step: 每轮 grounding 可选中的规则数量上限
        :param facts_num_for_each_rule: 每条规则在当前轮次可使用的事实数量上限
        """
        self.grounded_structure = grounded_structure

        self.facts_base = fact_base
        self.rule_base = rule_base  # TODO: 两个 base 将逐步移除，被 rule/term selector 代替
        self.m = rules_num_every_step
        self.n = facts_num_for_each_rule  # TODO: 由 selector 控制上限

        self._rule_selector = rule_selector
        self._term_selector = term_selector

    def __select_abstract_rule(self, question: Question, m: int = 5) -> Sequence[Rule]:
        """选择进入 grounding 的抽象规则集合。"""
        abstract_rules: Sequence[Rule] = self._rule_selector.next_rules()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Selected %s abstract rules from facts_base with %s active facts.",
                 len(abstract_rules),
                 len(self.facts_base.get_facts()))
        return abstract_rules

    def __select_facts_for_abstract_rules(self, question: Question, abstract_rules: Sequence[Rule]) \
            -> Sequence[tuple[Rule, list[GROUNDED_TYPE_FOR_UNIFICATION]]]:
        """为抽象规则选择用于实例化的事实/term 列表。"""
        rule_terms_pairs: list[tuple[Rule, list[GROUNDED_TYPE_FOR_UNIFICATION]]] = [(r, self._term_selector.next_terms(r)) for r in abstract_rules]
        # 变量名字我先不改，类型先写成ATOM_GROUNDED_TYPE
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Selected %s rule-fact pairs from rule base with %s active rules",
                 len(rule_terms_pairs),
                 len(self.rule_base.get_rules()))
        return rule_terms_pairs

    def _select_rule_terms_pair(self, question: Question) -> Sequence[tuple[Rule, list[GROUNDED_TYPE_FOR_UNIFICATION]]]:
        """选择规则并为每条规则准备可见的事实集合。"""
        return self.__select_facts_for_abstract_rules(question=question, abstract_rules=self.__select_abstract_rule(question))

    def select_facts_rules_pair(self, question: Question) -> list[tuple[Rule, list[GROUNDED_TYPE_FOR_UNIFICATION]]]:
        """先选 facts 后选 rules 的对称实现，当前未启用。"""
        raise NotImplementedError

    def _select_grounded_rule(self, grounded_rules: Sequence[GroundedRule]) -> Sequence[GroundedRule]:
        """用于过滤无候选值的 grounded rule（未来可接入更细粒度筛选）。"""
        self.max_grounded_series: int  # 如果注释中的TODO完成，那以后会有一个参数用于控制筛选算法或数量
        return list(grounded_rules)

    def grounding_process(self, question: Question) -> Sequence[GroundedRule]:
        """
        执行一次完整的 grounding 流程并返回 GroundedRule 集合。

        :param question: 查询的问题及其前提
        :returns: GroundedRule 列表
        """
        logger.info("Starting grounding process for question: %s", question.description)
        start_time = time.time()

        selected_rule_terms_pair = self._select_rule_terms_pair(question)
        with GroundedProcess(grounded_structure=self.grounded_structure, cur_rules_terms=selected_rule_terms_pair) as grounded_structure:
            grounded_structure.exec_grounding()

        grounded_rules = self.grounded_structure.get_corresponding_grounded_rules(
            abstract_rules=[r[0] for r in selected_rule_terms_pair])

        elapsed = time.time() - start_time
        logger.info("Grounding completed in %.2f seconds. Grounded rules: %s", elapsed, len(grounded_rules))

        return self._select_grounded_rule(grounded_rules)

    def reset(self) -> None:
        """在面向新问题推理时重置 Grounder 状态。"""
        self.grounded_structure.reset()  # 现在的RuleCheckGraph是每条GroundedRule自己维护的，所以清空Pool就相当于删除了Graph
        # 如果后期Graph合并时，这里应当进行额外的reset过程
        self._rule_selector.reset()  # 不会清空规则，只是重置到初始状态
        # 1. 由更换问题导致的rule base整个变更，应当重新声明InferenceEngine类
        # 2. 由rule base或其他地方选择推理所用规则导致的变更，由各处自行通过set rules进行变更
        self._term_selector.reset()  # 会清空term候选表，因为事实是从初始阶段逐步推理而得的
