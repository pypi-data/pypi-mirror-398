"""用于判断几何关系中的等价性"""
from ._checker import Checker


class GeoChecker(Checker):
    """用于判断几何中的等价关系，比如△ABC = △ACB"""
    def __init__(self) -> None:
        pass

    def is_equal(self, elem1: object, elem2: object) -> bool:
        raise NotImplementedError
