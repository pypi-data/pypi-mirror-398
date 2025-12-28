from __future__ import annotations
import warnings
from typing import cast, overload, TYPE_CHECKING


from al_inference_engine.egg_equiv import EggEquivalence
from al_inference_engine.equality._utils import fact_validator  # FIXME: 内部函数
from al_inference_engine.syntax import Formula, Assertion, CompoundTerm, FACT_TYPE, Constant
from al_inference_engine.grounder.grounded_rule_ds.grounded_ds_utils import split_all_terms

if TYPE_CHECKING:
    from al_inference_engine.config import Config
    from al_inference_engine.syntax.base_classes import TERM_TYPE, Variable, HashableAndStringable
    from collections.abc import Sequence


class Equivalence:
    """
    这个类是等价类的主要代码，用于实现维护等价类
    这个类主要的属性是father和length
    """
    def __init__(self, args: Config) -> None:
        self._args = args
        self.engine: EggEquivalence = EggEquivalence(trace=False)  # HACK: 暂时不通过egraph获取等价关系解释
        self._fact_validator = fact_validator

    def get_related_item(self, input_item: TERM_TYPE) -> list[TERM_TYPE]:
        # HACK: 此功能实际上应该由term_selector实现，或者调用egraph的相关函数来获取所有可能的等价形式
        """
        获取与item相关的所有节点
        相关节点定义为：与item等价的所有节点，与term的某个复合子结构等价的所有节点，以及item本身

        :param item: 要获取相关元素的元素
        :returns: 返回与item相关的所有元素
        """
        if isinstance(input_item, CompoundTerm):
            if TYPE_CHECKING:
                input_item = cast("CompoundTerm[Constant | CompoundTerm[Constant | Variable | HashableAndStringable]]", input_item)
            atomized_term = split_all_terms(input_item)
            result_set = set()
            for term in atomized_term:
                result_set.update(self.engine.get_equiv_elem(term))
            return list(result_set)
        return self.get_equiv_item(input_item)

    def get_equiv_item(self, input_item: TERM_TYPE) -> list[TERM_TYPE]:
        """
        获取与item等价的所有节点
        如果item是与某个BOOL_CONCEPT等价，或者其本身是BOOL_CONCEPT，那么将*不会返回*和该BOOL_CONCEPT等价的元素

        :param item: 要获取等价元素的元素
        :returns: 返回与item等价的所有元素
        """
        return self.engine.get_equiv_elem(input_item)

    def update_equiv_class(
        self,
        facts_or_equiv_rels: Sequence[FACT_TYPE],
    ) -> None:
        """更新等价类的对外接口"""
        for item in facts_or_equiv_rels:
            self._update_by_facts(item)

    def get_represent_elem(self, input_item: Constant | CompoundTerm) -> Constant | CompoundTerm[Constant | CompoundTerm]:
        """
        获取与item等价的代表元素

        :param item: 要获取等价元素的元素
        :returns: 返回与item等价的代表元素
        """
        return self.engine.get_represent_elem(input_item)

    @overload
    def query_equivalence(self, facts: Assertion) -> bool: ...

    @overload
    def query_equivalence(self, facts: Sequence[Assertion]) -> list[bool]: ...

    def query_equivalence(
        self,
        facts: Sequence[Assertion] | Assertion,
    ) -> bool | list[bool]:
        """
        查询某个Assertion是否成立，即检查左右式是否匹配。包括如下几种情况：
        1. 检查是否为a == a；
        2. 如果被某个checker返回True，则成立 (./checkers/__init__.py)；
        3. 如果Equivalence本身返回True，则成立 (_is_same_equiv_class)；
        2-3步需要结合莱布尼茨法则多次执行，即a = b → operator(a) = operator(b)。注意此时执行时可能会多次更新Equivalence（可能会发现多个等价关系）

        :param facts: 传入单个事实或者一组事实
        :returns: 为每一个Assertion查询返回一个bool，对单个事实返回一个bool，对多个事实返回list[bool]

        risk: 不确定设计是否合适，毕竟如果用并查集实现的话，本身也很难支持a=?的查询（先不考虑耗费O(n)时间能查询）
        risk: 需要考虑是否区分unknown和false，此刻的方案不区分。
        """
        if isinstance(facts, Assertion):
            return self._query_equivalence(facts)
        result_list: list[bool] = []  # 这是用于储存匹配结果的，每个元素是一个bool，代表一个匹配结果
        for assert_item in facts:
            if self._query_equivalence(assert_item):  # 调用函数执行查询，成功则加入True，失败则加入False
                result_list.append(True)
            else:
                result_list.append(False)
        return result_list

    def clear(self) -> None:
        """清空等价类"""
        self._id_counter = 0
        self.engine.clear()

    def _update_by_facts(self, facts: FACT_TYPE | None) -> None:
        """
        用于新事实对等价类模块的更新，一般出现在初始化KB、引擎

        :param facts: 断言内的等号指示了等价关系。注意到Formula中，仅有and是可以直接拆分更新等价类的、or无法确定等价关系、not会删除等价类（暂不允许)、
        imply先不管、equivalent也可以不管、forall现在的模式难以支持、exists无法确定等价关系
        :returns: None
        """
        if isinstance(facts, Assertion) and self._fact_validator(facts):
            if TYPE_CHECKING:
                # Assertion中不可能含有Variable
                facts.lhs = cast("CompoundTerm | Constant", facts.lhs)
                facts.rhs = cast("CompoundTerm | Constant", facts.rhs)
            self.engine.add_to_equiv(facts.lhs, facts.rhs)
        elif isinstance(facts, Formula):
            if facts.connective == 'AND':
                self._update_by_facts(facts.formula_left)
                self._update_by_facts(facts.formula_right)
            else:
                warnings.warn(f"连接词 '{facts.connective}' 无法更新等价类", stacklevel=2)
        else:
            warnings.warn(f"无效的事实类型：{facts}的类型为{type(facts)}，无法更新等价类", stacklevel=1)

    def _query_equivalence(
        self,
        fact: Assertion,
    ) -> bool:
        if TYPE_CHECKING:
            # Assertion中不可能含有Variable
            fact.lhs = cast("CompoundTerm | Constant", fact.lhs)
            fact.rhs = cast("CompoundTerm | Constant", fact.rhs)
        return self.engine.query_equivalence(fact.lhs, fact.rhs)
