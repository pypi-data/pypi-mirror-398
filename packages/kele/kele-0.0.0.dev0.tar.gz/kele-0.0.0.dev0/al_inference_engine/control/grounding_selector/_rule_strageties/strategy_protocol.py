from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from al_inference_engine.syntax import Rule
    from collections.abc import Callable


@runtime_checkable
class RuleSelectionStrategy(Protocol):
    """
    选取策略的统一接口。允许根据需求返回任意规则。
    """
    def __init__(self) -> None: ...
    def set_rules(self, rules: Sequence[Rule]) -> None: ...
    def reset(self) -> None: ...
    def select_next(self) -> Sequence[Rule]: ...
    def on_feedback(self, feedback: Feedback) -> None: ...    # 给策略回传一次选择后的反馈


@dataclass
class Feedback:
    """一次选择后的可选反馈信息；字段都可缺省，策略按需使用。"""
    rule: Rule | None = None  # 这次反馈关联到的规则；hack: 后面增加其他的相关信息，可能有facts等等


rule_strategy_registry: dict[str, type[RuleSelectionStrategy]] = {}


def register_strategy(name: str) -> Callable[[type[RuleSelectionStrategy]], type[RuleSelectionStrategy]]:
    """装饰器：将策略类注册到全局表中"""
    def decorator(cls: type[RuleSelectionStrategy]) -> type[RuleSelectionStrategy]:
        rule_strategy_registry[name] = cls
        return cls
    return decorator


def get_strategy_class(name: str) -> type[RuleSelectionStrategy]:
    try:
        return rule_strategy_registry[name]
    except KeyError as err:
        raise KeyError(f"Rule选取策略 '{name}' 未注册，可用策略: {list(rule_strategy_registry.keys())}") from err


def _available_strategies() -> list[str]:
    return list(rule_strategy_registry.keys())
