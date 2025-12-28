from __future__ import annotations

import warnings
from typing import TYPE_CHECKING
from ._rule_strageties import get_strategy_class

if TYPE_CHECKING:
    from ._rule_strageties.strategy_protocol import RuleSelectionStrategy, Feedback
    from collections.abc import Sequence
    from al_inference_engine.syntax import Rule, _QuestionRule


class GroundingRuleSelector:
    """
    对外统一入口，内部委托给策略实现。
    - 允许切换策略（接口不限制“连续取中”）
    - 允许更新规则集合
    """
    def __init__(self, strategy: str = "sequential_cyclic", question_rule_interval: int = -1) -> None:
        strategy_cls = get_strategy_class(strategy)
        self._strategy = strategy_cls()
        self._normal_rules: list[Rule] | None = None

        self.question_rule_interval = question_rule_interval
        self.used_rule_cnt: int = 0
        self._question_rules: list[Rule] = []
        self._at_fixpoint: bool = False

    def set_at_fixpoint(self, *, at_fixpoint: bool) -> None:
        """设置是否已经达到不动点状态"""
        self._at_fixpoint = at_fixpoint

    def next_rules(self) -> Sequence[Rule]:
        """选择一定数量的规则用于grounding，在一定轮次后会查看一次question是否被解决
        :raises ValueError: 当 question_rule_interval 小于1且不为-1时抛出。
        """  # noqa: DOC501
        if self._at_fixpoint:
            if self._question_rules:
                self.used_rule_cnt = 0
                return self._question_rules
            return []

        # 确定实际的检查间隔
        if self.question_rule_interval < 1 and self.question_rule_interval != -1:
            raise ValueError("question_rule_interval 必须大于等于1，或为-1表示用普通规则总数作为间隔")

        interval = self.question_rule_interval
        if interval == -1:
            normal_count = len(self._normal_rules) if self._normal_rules is not None else 0
            interval = normal_count or 1

        if self.used_rule_cnt >= interval and self._question_rules:
            self.used_rule_cnt = 0  # 重置计数器
            return self._question_rules

        rules = self._strategy.select_next()
        self.used_rule_cnt += len(rules)

        return rules

    def reset(self) -> None:
        """重置选择器"""
        self._strategy.reset()
        self._normal_rules = None
        self._question_rules = []
        self.used_rule_cnt = 0
        self._at_fixpoint = False

    def set_strategy(self, strategy: RuleSelectionStrategy) -> None:
        """切换策略实现（不重置调用方传入策略的内部状态，由策略自行决定）。"""
        self._strategy = strategy

        if self._normal_rules is not None:
            self._strategy.set_rules(self._normal_rules)
        else:
            warnings.warn("No given rules, please call set_rules after calling set_strategy.", stacklevel=2)

    def set_rules(self, normal_rules: Sequence[Rule], question_rules: Sequence[_QuestionRule]) -> None:
        """
        更新规则集合，并同步给当前策略
        :raise: ValueError: 没有可选rules时报错
        """  # noqa: DOC501
        if not normal_rules:
            raise ValueError("rules 不能为空")

        self._normal_rules = list(normal_rules)
        self._question_rules = list(question_rules)

        self._strategy.set_rules(self._normal_rules)

        # 重置计数器
        self.used_rule_cnt = 0

    def send_feedback(self, feedback: Feedback) -> None:
        """把一次选择后的反馈转发给当前策略"""
        self._strategy.on_feedback(feedback)
