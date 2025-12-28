"""用于代数表达式的等价判断"""
from al_inference_engine.syntax.base_classes import TERM_TYPE
from ._checker import Checker


class AlgExprChecker(Checker):
    """用于判断代数表达式的等价关系，比如x^2 + 2 == 2 + x^2"""
    def __init__(self) -> None:
        pass

    def is_equal(self, elem1: TERM_TYPE, elem2: TERM_TYPE) -> bool:
        """
        判断两个代数表达式是否等价
        """
        raise NotImplementedError
