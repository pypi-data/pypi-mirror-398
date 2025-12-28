from collections.abc import Sequence

from .strategy_protocol import Feedback, register_strategy, RuleSelectionStrategy
from al_inference_engine.syntax import Rule


@register_strategy('SequentialCyclic')
class SequentialCyclicStrategy(RuleSelectionStrategy):
    """
    按顺序循环遍历策略：
    r0, r1, ..., rN-1, r0, r1, ...
    """
    def __init__(self) -> None:
        self._idx: int = 0

    def set_rules(self, rules: Sequence[Rule]) -> None:
        self._rules = list(rules)
        if not self._rules:
            raise ValueError("rules 不能为空")
        self._idx = 0

    def reset(self) -> None:
        self._idx = 0

    def select_next(self) -> Sequence[Rule]:
        # 循环顺序取下一条
        r = self._rules[self._idx]
        self._idx = (self._idx + 1) % len(self._rules)
        return [r]

    def on_feedback(self, feedback: Feedback) -> None:  # noqa: PLR6301  # 尚未实现，不需要转static
        # 顺序循环策略不依赖反馈，空实现即可
        return


@register_strategy("SequentialCyclicWithPriority")
class SequentialCyclicWithPriorityStrategy(SequentialCyclicStrategy):
    """将规则按优先级排序，优先级高的先取"""

    def set_rules(self, rules: Sequence[Rule]) -> None:
        rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        super().set_rules(rules)
