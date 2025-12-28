from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from al_inference_engine.syntax import GROUNDED_TYPE_FOR_UNIFICATION, Rule, TERM_TYPE
    from collections.abc import Callable


@runtime_checkable
class TermSelectionStrategy(Protocol):
    """
    选取策略的统一接口。允许根据需求返回任意规则。
    """
    def __init__(self) -> None: ...
    def add_terms(self, terms: Sequence[TERM_TYPE]) -> None: ...
    def reset(self) -> None: ...
    def select_next(self, rule: Rule) -> Sequence[GROUNDED_TYPE_FOR_UNIFICATION]: ...
    def on_feedback(self, feedback: Feedback) -> None: ...    # 给策略回传一次选择后的反馈


@dataclass
class Feedback:
    """一次选择后的可选反馈信息；字段都可缺省，策略按需使用。"""


term_strategy_registry: dict[str, type[TermSelectionStrategy]] = {}


def register_strategy(name: str) -> Callable[[type[TermSelectionStrategy]], type[TermSelectionStrategy]]:
    """装饰器：将策略类注册到全局表中"""
    def decorator(cls: type[TermSelectionStrategy]) -> type[TermSelectionStrategy]:
        term_strategy_registry[name] = cls
        return cls
    return decorator


def get_strategy_class(name: str) -> type[TermSelectionStrategy]:
    try:
        return term_strategy_registry[name]
    except KeyError as err:
        raise KeyError(f"Term选取策略 '{name}' 未注册，可用策略: {list(term_strategy_registry.keys())}") from err


def _available_strategies() -> list[str]:
    return list(term_strategy_registry.keys())
