from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Any
from bidict import bidict
import numpy as np
import polars as pl
from polars.type_aliases import PolarsDataType

if TYPE_CHECKING:
    from al_inference_engine.equality import Equivalence
    from polars.type_aliases import PolarsDataType
    from al_inference_engine.syntax.base_classes import Constant, CompoundTerm, Variable
    from collections.abc import Generator
    from numpy.typing import NDArray


class NameToObject:
    """
    记录了Variable到其uuid（或term、constant到其uuid）的双向映射
    """
    _item_to_name: ClassVar[bidict[Any, int]] = bidict()
    _item_counter: ClassVar[int] = 0

    @classmethod
    def register_item(cls, var: Constant | CompoundTerm) -> None:
        if var not in cls._item_to_name:
            var_id = cls._item_counter
            cls._item_to_name[var] = var_id
            cls._item_counter += 1

    @classmethod
    def get_item_by_name(cls, name: int | str) -> Any:  # noqa: ANN401 # HACK: 列名必须str，值必须int。为了后续改动不容易出bug
        # 的角度，这里最好拆开两个get_item，分值和列名。或者列名直接从variable的name去生成，这个没必要单独用item
        return cls._item_to_name.inverse[int(name)]

    @classmethod
    def get_item_name(cls, item: Any) -> int:  # noqa: ANN401
        cls.register_item(item)
        return cls._item_to_name[item]

    @classmethod
    def len(cls) -> int: return cls._item_counter

    @classmethod
    def reset(cls) -> None:
        cls._item_to_name.clear()
        cls._item_counter = 0


class _TupleTable:  # HACK: 此结构储存非常容易导致爆内存，后续应当考虑是否修改
    """
    这是用于记录实例化结果的一个类。
    它本质上是一个dict[Variable, list[Constant]]，但是特别之处在于，index相同的元素可以视作一个元组，
    也就是说，删除list中某个index的元素，那么所有的list都要删除这个index的元素。
    同时还实现了合并功能，合并的时候，按照：相同元素取交集，全新元素基于乘法法则生成新的组来合并
    """
    def __init__(self, column_name: tuple[Variable, ...]) -> None:
        self.column_name = [str(NameToObject.get_item_name(var)) for var in column_name]
        self._raw_column_name: tuple[Variable, ...] = column_name
        self._add_row_cache: dict[str, list[int]] = {}
        self._base_df: pl.DataFrame

    def __len__(self) -> int:
        """
        返回行数。
        """
        return self.height

    def __getitem__(self, index: int) -> dict[Variable, Constant | CompoundTerm]:
        """
        按行索引返回一条记录，格式与 iter_rows一致。仅支持 int 索引（正/负），不支持切片。
        raise: TypeError: 暂时只允许通过数字访问行
        raise: IndexError：数字只允许[-n~n-1]的范围
        """  # noqa: DOC501
        self.make_table_ready()

        n = self.height
        if not isinstance(index, int):
            raise TypeError("Index must be an int.")
        if n == 0:
            raise IndexError("The table is empty.")
        # 负索引处理
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError("Row index out of range.")

        row_np = self.base_df.row(index)  # 使用缓存的 numpy 数组以获得更快的随机访问
        # 将字符串名恢复成原对象；键用原始 Variable 对象
        result = {}

        for name, val in zip(self.raw_column_name, row_np, strict=True):
            val_obj = NameToObject.get_item_by_name(val)
            result[name] = val_obj

        return result

    def __iter__(self) -> Generator[dict[Variable, Constant | CompoundTerm]]:
        yield from self.iter_rows()

    def set_base_df(self, df: pl.DataFrame) -> None:

        """
        从外界的一个lazyframe初始化此TupleTable，这主要是用于join过程

        :param df: 初始化数据
        :type df: pl.DataFrame
        """
        self._base_df = df.unique()
        self.column_name = df.columns

    def get_small_table(self, column_name: tuple[Any, ...]) -> _TupleTable:
        """
        获取一个子表，只包含column_name中的列

        :param column_name: 子表的列名
        :type column_name: tuple[Any, ...]
        :return: 子表
        :rtype: _TupleTable
        """
        self.make_table_ready()  # 使用的一定是准备好后的table

        column_name = tuple(set(column_name))
        small_column_name = [str(NameToObject.get_item_name(var)) for var in column_name]
        small_table = _TupleTable(column_name)
        small_table.set_base_df(self.base_df.select(pl.col(small_column_name)))
        return small_table

    def get_true_false_table(self, data: list[bool], *, keep_table: bool | None = None) -> tuple[_TupleTable, _TupleTable]:
        """
        基于真值列获取新表true_table/false_table
        :param column_name: 列名
        :type column_name: Assertion
        :param data: 真值列
        :type data: list[str]
        :return: 真值表/假值表
        :rtype: tuple[_TupleTable, _TupleTable]
        """
        self.make_table_ready()

        mask_series = pl.Series(data, dtype=pl.Boolean)
        true_table = _TupleTable(self.raw_column_name)
        false_table = _TupleTable(self.raw_column_name)
        if keep_table is None or keep_table:
            df_true_lazy = self.base_df.filter(mask_series)
            true_table.set_base_df(df_true_lazy)
        if keep_table is None or not keep_table:
            df_false_lazy = self.base_df.filter(~mask_series)
            false_table.set_base_df(df_false_lazy)

        return true_table, false_table

    def concat_table(self, *tables: _TupleTable) -> _TupleTable:
        """
        合并此表与多个表，返回合并后的 table

        :param tables: 需要合并的其他表
        :type tables: _TupleTable
        :return: 合并后的表
        :rtype: _TupleTable
        """
        # 确保所有表的cache都被合并为df了
        for table in (self, *tables):
            table.make_table_ready()

        valid_tables = [t for t in tables if t.height > 0]

        # 新建表，列名取 self 的
        new_table = _TupleTable(self.raw_column_name)

        # 拼接所有表
        all_lfs = []
        columns = self.base_df.columns
        for t in valid_tables:
            df = t.base_df.select(columns)
            all_lfs.append(df)

        new_df = pl.concat([self.base_df, *all_lfs])
        new_table.set_base_df(new_df)

        return new_table

    def update_equiv_element(self, equivalence: Equivalence) -> _TupleTable:
        """
        将当前table的所有元素更新为他们的等价类代表元

        :param equivalence: 等价类
        :type equivalence: Equivalence
        :return: 新的table
        :rtype: _TupleTable
        """
        # 1) 取所有列的唯一值
        unique_values = (
            self.base_df.select(pl.concat_list(pl.all()).explode().unique())
            .to_series()
            .to_list()
        )

        # 2) 计算代表元映射
        mapping = {}
        for old in unique_values:
            old_elem = NameToObject.get_item_by_name(old)
            rep_elem = equivalence.get_represent_elem(old_elem)
            mapping[old] = NameToObject.get_item_name(rep_elem)

        new_df = self.base_df.with_columns(
            pl.all().map_elements(lambda a: mapping.get(a, a))
        )
        new_table = _TupleTable(self.raw_column_name)
        new_table.set_base_df(new_df)
        return new_table

    def union_table(self, another_table: _TupleTable) -> _TupleTable:
        """
        将此表与另外一个表按照inner方式合并，返回合并后的table

        :param another_table: 另外一个表
        :type another_table: _TupleTable
        :return: 合并后的表
        :rtype: _TupleTable
        """
        for table in (self, another_table):
            table.make_table_ready()

        common_columns: set[str] = set(self.column_name) & set(another_table.column_name)
        if common_columns == set():
            result_df = self.base_df.join(another_table.base_df, how='cross')
            # 没有任何公共列，二者按照乘法原则合并
        else:
            result_df = self.base_df.join(another_table.base_df, on=list(common_columns), how='inner')
            # 有公共列：二者按照"inner"方式合并

        new_column_name = tuple(NameToObject.get_item_by_name(name) for name in result_df.columns)
        new_table = _TupleTable(new_column_name)
        new_table.set_base_df(result_df)
        return new_table

    def anti_join(self, another_table: _TupleTable) -> _TupleTable:
        """
        移除掉此table中与another_table中相同的行，返回一个新的table
        """
        same_column_name = set(another_table.column_name) & set(self.column_name)
        result_df = self.base_df.join(another_table.base_df, on=list(same_column_name), how='anti')
        new_table = _TupleTable(self.raw_column_name)
        new_table.set_base_df(result_df)
        return new_table

    def copy(self) -> _TupleTable:
        """
        复制此表
        """
        new_table = _TupleTable(self.raw_column_name)
        new_table.set_base_df(self.base_df)
        return new_table

    def iter_rows(self) -> Generator[dict[Variable, Constant | CompoundTerm]]:
        """
        获取所有行
        :yield: 所有行
        :rtype: Generator[tuple[Any, ...]]
        """  # noqa: DOC402
        for i in self.base_df.iter_rows():
            temp_dict: dict[Variable, Constant | CompoundTerm] = {}
            for j in range(len(i)):
                temp_dict[self.raw_column_name[j]] = NameToObject.get_item_by_name(i[j])
            yield temp_dict

    def make_table_ready(self) -> None:
        """
        确保表已经准备好，实质就是调用内部的_merge_to_lazy_block方法
        """
        if not hasattr(self, "_base_df"):
            self._base_df = pl.DataFrame(data=self._add_row_cache, schema=self._column_schema())

    def clear(self) -> None:
        """
        清空dataframe
        """
        self._add_row_cache = {}
        self._laze_base_df = pl.DataFrame([], schema=self._column_schema())
        self.__dict__.pop('_base_df', None)
        self.__dict__.pop('_np_list_store', None)
        self.__dict__.pop('table_represent', None)
        self.__dict__.pop('raw_columns_name_str', None)

    def add_row(self, row: dict[Variable, Constant | CompoundTerm]) -> None:
        """
        添加一行
        :param row: 一行数据
        :type row: dict[Variable, Constant | CompoundTerm]
        """
        for k, v in row.items():
            key_name = str(NameToObject.get_item_name(k))
            var_name = NameToObject.get_item_name(v)
            if key_name in self._add_row_cache:
                self._add_row_cache[key_name].append(var_name)
            else:
                self._add_row_cache[key_name] = [var_name]

    def add_column(self, new_columns: dict[Variable, list[Constant | CompoundTerm]]) -> _TupleTable:
        """添加一列。TODO: 暂时还没有加入列对应的cache以实现lazy"""
        self.make_table_ready()

        base_df = self.base_df

        series_to_add: list[pl.Series] = []
        for var, values in new_columns.items():
            col_name = NameToObject.get_item_name(var)
            str_values = [NameToObject.get_item_name(v) for v in values]
            series_to_add.append(pl.Series(name=col_name, values=str_values, dtype=self._smallest_unsigned_int_dtype()))

        new_base_df = base_df.hstack(series_to_add)

        new_raw_column_name = (*new_columns.keys(), *self.raw_column_name)

        new_table = _TupleTable(new_raw_column_name)
        new_table.set_base_df(new_base_df)
        return new_table

    @classmethod
    def create_empty_table_with_emptyset(cls) -> _TupleTable:
        df = pl.DataFrame([[]], orient="row")
        table = _TupleTable(())
        table.set_base_df(df)
        return table

    @property
    def height(self) -> int:
        """
        获取表的高度

        :return: 表的高度
        :rtype: int
        """
        return self.base_df.height

    @property
    def base_df(self) -> pl.DataFrame:
        if not hasattr(self, '_base_df'):
            self.make_table_ready()
            if self._base_df.width == 0:  # 没有任何列的空表直接to_numpy会报错，通过强行判断来避免这件事
                # 这种没有任何列的空表来源于ConstantNode，一般grounding不会涉及到它们，但是pytest有可能涉及，因此这里再
                # 强行判断一下
                self._np_list_store = np.empty((0, 0))
            else:
                self._np_list_store = self._base_df.to_numpy()
        return self._base_df

    @property
    def _np_list(self) -> NDArray[np.float64]:
        """
        转换为numpy数组，主要用于取单列
        """
        if not hasattr(self, '_np_list_store'):
            _ = self.base_df  # 如果在触发base_df之前触发_np_list，则先触发一次base_bf来计算_np_list_store
        return self._np_list_store

    @property
    def table_represent(self) -> list[dict[str, str]]:
        """
        用于pytest，相当于将table转化为list[dict]，同时将变量名和常量名转化为字符串

        :return: 转化后的table
        :rtype: list[dict[str, str]]
        """
        list_dict = self.base_df.unique(maintain_order=True).to_dicts()
        return [{str(NameToObject.get_item_by_name(u)): str(NameToObject.get_item_by_name(v)) for u, v in s_dict.items()} for s_dict in list_dict]

    @property
    def raw_column_name(self) -> tuple[Any, ...]:
        """
        获取原始列名（对象）

        :return: 原始列名（对象）
        :rtype: list[Any]
        """
        if not hasattr(self, "_raw_column_name"):
            self._raw_column_name = tuple(NameToObject.get_item_by_name(u) for u in self.column_name)
        return self._raw_column_name

    @property
    def raw_columns_name_str(self) -> list[str]:
        """
        获取原始列名（字符串），用于绘图

        :return: 原始列名（字符串）
        :rtype: list[str]
        """
        return [str(NameToObject.get_item_by_name(u)) for u in self.column_name]

    @staticmethod
    def _smallest_unsigned_int_dtype() -> PolarsDataType:
        max_val = NameToObject.len()

        if max_val <= ((1 << 8) - 1):
            return pl.UInt8
        if max_val <= ((1 << 16) - 1):
            return pl.UInt16
        if max_val <= ((1 << 32) - 1):
            return pl.UInt32
        return pl.UInt64

    def _column_schema(self) -> dict[str, PolarsDataType]:
        return dict.fromkeys(self.column_name, self._smallest_unsigned_int_dtype())
