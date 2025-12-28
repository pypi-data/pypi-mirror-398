"""checker的抽象类，用于快速导入所有checker"""
from abc import abstractmethod, ABC

from al_inference_engine.syntax.base_classes import TERM_TYPE


class Checker(ABC):
    @abstractmethod
    def is_equal(self, elem1: TERM_TYPE, elem2: TERM_TYPE) -> bool:
        """用于判断给定的两个元素是否等价"""

    def scope_check(self) -> bool:
        """TODO: 当checker太多后，预留一个跳过某些checker的函数，尚不清楚如何实现"""
        raise NotImplementedError
