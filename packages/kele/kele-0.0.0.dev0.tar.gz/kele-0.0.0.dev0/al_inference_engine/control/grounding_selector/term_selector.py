from __future__ import annotations

import itertools
from typing import TYPE_CHECKING
from ._term_strageties import get_strategy_class
from al_inference_engine.control.grounding_selector._selector_utils import _unify_into_terms

if TYPE_CHECKING:
    from al_inference_engine.config import Config
    from al_inference_engine.syntax import GROUNDED_TYPE_FOR_UNIFICATION, Rule
    from al_inference_engine.equality import Equivalence
    from ._term_strageties.strategy_protocol import Feedback
    from collections.abc import Sequence
    from al_inference_engine.syntax import FACT_TYPE


class GroundingAtomTermWithWildCardSelector:  # 此时是AtomTerm-level grounding，所以进strategy不止是Term。但是strategy本身是Term和
    # AtomTerm均合适的，所以strategy自己的标准仍然得是TERM_TYPE。
    # 此外，目前通配符和atom term无法分割，所以命名强调了wild card
    """
    对外统一入口，内部委托给策略实现。
    """
    def __init__(self,
                 equivalence: Equivalence,
                 args: Config) -> None:

        strategy_cls = get_strategy_class(args.strategy.grounding_term_strategy)
        self._strategy = strategy_cls()
        self._equivalence = equivalence
        self._args = args

    def next_terms(self, rule: Rule) -> list[GROUNDED_TYPE_FOR_UNIFICATION]:
        """为给定规则选择候选事实/term 用于 grounding。"""
        init_terms = list(self._strategy.select_next(rule))

        if self._args.run.semi_eval_with_equality:
            selected_terms: set[GROUNDED_TYPE_FOR_UNIFICATION] = set()

            for t in init_terms:
                if t not in selected_terms:
                    equiv_terms = self._equivalence.get_related_item(t)
                    selected_terms |= set(equiv_terms)  # TODO: 这里后面考虑是否把_unify_into_atom_terms挪到term selector

                    # 在semi-evaluation中纳入等价类其余terms，这是由
                    # 断言逻辑带来的内嵌、强制等词公理，和term-level grounding二者共同决定的算法，因为不放置于具体的Strategy中，而是作为
                    # Selector自身的行为。
            return list(selected_terms)

        return list(set(init_terms))

    def reset(self) -> None:
        """重置选择器"""
        self._strategy.reset()

    def update_terms(self,
                     terms: Sequence[GROUNDED_TYPE_FOR_UNIFICATION] | None = None,
                     facts: Sequence[FACT_TYPE] | None = None) -> None:
        """
        更新事实集合，并同步给当前策略。
        :raise: ValueError: 没有可选terms_or_facts时报错
        """  # noqa: DOC501

        if terms:
            fact_terms = terms
        elif facts:
            fact_terms = list(itertools.chain.from_iterable(_unify_into_terms(f) for f in facts))  # FIXME: 更进一步地，其实只有Assertion
            # 能触发等式公理
        else:
            raise ValueError("terms or facts 不能为空")

        # 不应有action operator的term。fact_terms = [f for f in fact_terms if f.operator.implement_func is not None]
        self._strategy.add_terms(fact_terms)

    def send_feedback(self, feedback: Feedback) -> None:
        """把一次选择后的反馈转发给当前策略"""
        self._strategy.on_feedback(feedback)
