from al_inference_engine.syntax.base_classes import Assertion
from ._equiv_elem import EquivElem
import warnings
from functools import singledispatch


@singledispatch
def fact_validator(item: Assertion | tuple[EquivElem, EquivElem]) -> bool:
    """
    用于验证fact的合法性，分别对Assertion和tuple两种更新方式验证是否包含非法元素
    有其他的验证条件，也应当在这个函数实现

    :param item: 一个fact，可能是Assertion或者tuple
    :return: 如果fact合法，返回True；否则，返回False
    """
    warnings.warn(f"不应当采用{type(item)}来更新事实！", stacklevel=5)
    return False


@fact_validator.register(Assertion)
def _(item: Assertion) -> bool:
    # 实际上这用来判断非法情形：断言中出现True/False这样的非法形式
    # 这里将在后续解决：实际上Assertion左右放入False/True是非法的，True/False将以Constant/Concept的方式出现，需要单独的判断方法
    return True


@fact_validator.register(tuple)
def _(item: tuple[EquivElem, EquivElem]) -> bool:
    length_of_legal_assertion = 2
    if not isinstance(item, tuple) or len(item) != length_of_legal_assertion:
        warnings.warn(f"无效的等价关系格式: {item}，应为二元组", stacklevel=2)
        return False
    # 后续还将有一个if
    # 实际上这用来判断非法情形：断言中出现True/False这样的非法形式
    # 这里将在后续解决：实际上Assertion左右放入False/True是非法的，True/False将以Constant/Concept的方式出现，需要单独的判断方法
    return True
