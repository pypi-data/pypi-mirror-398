# ruff: noqa: PLC0415

from __future__ import annotations
import warnings
from contextlib import contextmanager
import re
from collections.abc import Generator
from collections.abc import Sequence, Mapping
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from al_inference_engine.syntax import Concept


# Concept从属关系录入
def register_concept_relations(relations: str | Mapping[Concept | str, Sequence[Concept | str]] | Sequence[tuple[Concept | str, Concept | str]]) \
        -> None:
    """
    批量注册从属关系列表 [(child, parent), ...]，每条对应一个概念从属关系 child ⊆ parent。
    支持三种录入形式：字符串DSL / 映射(子->[父...]) / 列表[(子,父),...]
    """
    if isinstance(relations, str):
        register_concept_from_string(relations)
    elif isinstance(relations, Mapping):
        register_concept_from_mapping(relations)
    else:
        register_concept_subsumptions(relations)


def register_concept_subsumptions(pairs: Sequence[tuple[Concept | str, Concept | str]]) -> None:
    """批量注册从属关系列表 [(child, parent), ...]"""
    from al_inference_engine.syntax import Concept
    for ch, pa in pairs:
        Concept.add_subsumption(ch, pa)


def register_concept_from_mapping(mapping: Mapping[Concept | str, Sequence[Concept | str]]) -> None:
    """从映射(子->[父...])注册"""
    from al_inference_engine.syntax import Concept
    for ch, parents in mapping.items():
        for pa in parents:
            Concept.add_subsumption(ch, pa)


def register_concept_from_string(spec: str) -> None:
    """
    从字符串录入多条从属关系。支持分隔符：逗号/分号/换行；关系符：'⊆'、'<='。
    :raise ValueError: 分隔符需要用'⊆'、'<='
    """  # noqa: DOC501
    from al_inference_engine.syntax import Concept
    items = re.split(r"[;,]+", spec)
    for item in items:
        s = item.strip()
        if not s:
            continue
        m = re.match(r"^(.+?)(?:⊆|<=)(.+)$", s)
        if not m:
            raise ValueError(f"无法解析的从属语句: {s!r}. 期望形如 'A ⊆ B' 或 'A <= B'.")
        left, right = m.group(1).strip(), m.group(2).strip()
        Concept.add_subsumption(left, right)


def with_concept_relations(relations: str | Mapping[Concept | str, Sequence[Concept | str]] | Sequence[tuple[Concept | str, Concept | str]]) \
        -> object:
    """装饰器：在被装饰对象定义时注册关系。

    用法：
        @with_concept_relations("int ⊆ real; positive_int <= int")
        def build_ops(): ...
    """
    def _decorator(obj: object) -> object:
        register_concept_relations(relations)
        return obj
    return _decorator


@contextmanager
def concept_relation_scope(relations: str | Mapping[Concept | str, Sequence[Concept | str]] | Sequence[tuple[Concept | str, Concept | str]]) \
        -> Generator:  # type: ignore[type-arg]
    """上下文管理器：进入时注册给定关系，注意退出时不做回滚，因为我们暂时认为子集关系是不变的。"""
    register_concept_relations(relations)
    try:
        yield
    finally:
        warnings.warn("进入时注册给定关系，注意退出时不做回滚，因为我们暂时认为子集关系是不变的", stacklevel=2)
