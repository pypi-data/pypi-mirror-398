from collections.abc import Callable
from pydantic import BaseModel, ConfigDict

from .base_classes import FACT_TYPE, Question, Assertion


class SankuManagementSystem(BaseModel):
    """三库系统的抽象，主要用于类型检查和说明数据结构"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    knowledge: list[FACT_TYPE] = []
    initial_by_question: Callable[[Question, int | None], list[FACT_TYPE]] = lambda x, y: []
    # TODO(lbq): 需与泳融沟通，使用一个question和一个取出的上限值，由三库系统决定返回哪些有用的信息协助初始化。
    # 另外 HACK: 实则应该用memcached语言传入，而且这是一个http链接，不是函数
    query_assertion: Callable[[Assertion | list[Assertion]], list[Assertion]] = lambda x: []
    update_facts: Callable[[FACT_TYPE | list[FACT_TYPE]], None] = lambda x: None
