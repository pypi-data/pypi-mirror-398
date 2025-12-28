from typing import NamedTuple
from ._tupletable import _TupleTable


class TfTables(NamedTuple):
    """
    类TfIndexs，记录了经过一个节点之后的true_index和false_index
    """
    true: _TupleTable
    false: _TupleTable

    def clear(self) -> None:
        """本函数应当谨慎使用。由于效率缘故，exec阶段会以指针形式传递tfindex相关字段，应在确定某字段使用完毕后，再执行"""
        self.true.clear()
        self.false.clear()
