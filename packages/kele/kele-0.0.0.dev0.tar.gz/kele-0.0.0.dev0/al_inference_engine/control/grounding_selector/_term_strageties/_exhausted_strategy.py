from collections import defaultdict
from collections.abc import Sequence

from .strategy_protocol import Feedback, register_strategy, TermSelectionStrategy
from al_inference_engine.syntax import GROUNDED_TYPE_FOR_UNIFICATION, Rule, TERM_TYPE


@register_strategy('Exhausted')
class ExhuastedStrategy(TermSelectionStrategy):
    """
    每次选择剩余的所有terms
    """
    def __init__(self) -> None:
        self._terms: list[GROUNDED_TYPE_FOR_UNIFICATION] = []  # _terms应当对所有的rule都成立，只是有的被用掉了。需要有去重的方案
        self._rules_used_id: dict[Rule, int] = defaultdict(lambda: 0)

    def add_terms(self, terms: Sequence[TERM_TYPE]) -> None:
        self._terms.extend(terms)

    def reset(self) -> None:  # HACK: 这个还没用
        self._terms.clear()
        self._rules_used_id = defaultdict(lambda: 0)

    def select_next(self, rule: Rule) -> Sequence[GROUNDED_TYPE_FOR_UNIFICATION]:
        # 循环顺序取下一条
        start_id = self._rules_used_id[rule]
        selected_terms = list(self._terms[start_id:])
        self._rules_used_id[rule] = len(self._terms)

        return selected_terms

    def on_feedback(self, feedback: Feedback) -> None:  # noqa: PLR6301  # 尚未实现，不需要转static
        # 顺序循环策略不依赖反馈，空实现即可
        return
