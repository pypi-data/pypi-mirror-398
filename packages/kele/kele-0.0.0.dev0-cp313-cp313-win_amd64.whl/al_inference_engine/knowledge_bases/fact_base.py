from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from al_inference_engine.config import KBConfig
    from al_inference_engine.syntax.base_classes import FACT_TYPE, Question
    from collections.abc import Sequence
    from al_inference_engine.equality import Equivalence
    from al_inference_engine.syntax.external import SankuManagementSystem
    from al_inference_engine.control.grounding_selector import GroundingAtomTermWithWildCardSelector


# FIXME: 存入事实库和规则库的信息应当满足safe的条件，我们将在 #132 中对CompoundTerm加入generic且引入safe的约束，以完成更精细的类型标注
class FactBase:
    """存储所有fact的总结构"""

    def __init__(self,
                 initial_facts_or_dir_or_path: Sequence[FACT_TYPE] | str,
                 equivalence_handler: Equivalence,
                 term_selector: GroundingAtomTermWithWildCardSelector,
                 sk_system_handler: SankuManagementSystem,
                 args: KBConfig,
                 ):
        if isinstance(initial_facts_or_dir_or_path, str):
            self.facts: set[FACT_TYPE] = self._read_facts(initial_facts_or_dir_or_path)
        else:
            self.facts = set(initial_facts_or_dir_or_path)

        for fact in self.facts:
            if fact.free_variables:
                raise ValueError(f"Fact {fact} contains free variables, which is not allowed.")

        self.equivalence_handler = equivalence_handler
        self.term_selector = term_selector
        self.sk_system_handler = sk_system_handler  # HACK: 三库系统在解题前，会执行一次initial_by_question更新事实库。考虑到
        # 事实库的初始化是一个独立环节，此函数的调用被放置到FactBase内，而非最外层的InferenceEngine内。虽然从模块拆分的角度上FactBase和
        # 三库系统是两个系统，可能会建议在main函数内完成二者的交互。
        self._args = args
        self.max_facts = self._args.fact_cache_size

        self.initial_sign = False  # 引擎希望先挑选FactBase中的部分事实进行初始化。因此在__init__阶段我们认为初始化未完成，为False。
        # 当初始化完成后、当前值为True时才应当进行后续其他操作
        self.cur_facts: set[FACT_TYPE] = set()

    def _read_facts(self, path: str) -> set[FACT_TYPE]:
        """传入一个dir或文件，读取整个文件夹下面所有的文件或单个文件。TODO: 需要约定字符串书写格式（此刻还没有字符串的parser，先不实现）"""
        raise NotImplementedError

    def _add_or_not(self, fact: FACT_TYPE) -> bool:
        """判断某条事实是否应当被加入事实库。"""

        # 1. 判断事实是否已存在
        if fact in self.facts:
            return False  # 已存在的事实不再加入

        # 2. 判断是否超过事实库大小上限
        if self.max_facts != -1 and len(self.facts) >= self.max_facts:  # noqa: SIM103  # 函数还可以继续扩充，
            # 不应当直接简化为return (self.max_facts is not None...)，因此注释掉SIM103
            return False  # TODO: 如果事实库已满，最好是根据启发式决定是否丢弃现有事实或丢弃库内事实但保留当前事实

        # 3. 不合需求没必要保留（依赖启发式/NN判断）

        return True

    def add_facts(self, facts: Sequence[FACT_TYPE], *, force_add: bool = False) -> list[FACT_TYPE]:
        """
        通过add加入的fact也会同步更新等价类。TODO: 为了效率可以拆分add_facts和add_fact，转C的时候留意下即可

        :param facts: 要加入的事实序列
        :param force_add: 是否强制加入，默认为False
        :return: 实际加入的事实序列
        :raise ValueError: 当事实包含自由变量时抛出
        """  # noqa: DOC501
        added_facts = []
        for fact in facts:
            if fact.free_variables:
                raise ValueError(f"Fact {fact} contains free variables, which is not allowed.")

        if force_add:  # 冗余一点避免多次判断force_add
            for fact in facts:
                self.facts.add(fact)
                added_facts.append(fact)
        else:
            for fact in facts:
                if self._add_or_not(fact):
                    self.facts.add(fact)
                    added_facts.append(fact)

        self.cur_facts |= set(added_facts)
        self.equivalence_handler.update_equiv_class(added_facts)
        if added_facts:
            self.term_selector.update_terms(facts=added_facts)

        return added_facts

    def _select_initial_facts(self, question: Question, topn: int | None = None) -> list[FACT_TYPE]:
        """根据问题选择最有可能有用的topn条事实，当没有num时将不对最终结果的数量做限制"""
        all_facts = list(self.facts)

        if topn is None or topn == -1 or topn >= len(all_facts):
            return all_facts

        return all_facts[:topn]  # TODO: 默认按插入顺序（或原始顺序）截取，是优化点

    def initial_fact_base(self, question: Question, topn: int | None = None) -> None:
        """作为整个解题流程开始前的一次筛选，需要选择充足的事实以免无法成功。此外也包括向三库获取一部分事实、初始化等价类等"""
        selected_facts = self._select_initial_facts(question, topn)
        self.equivalence_handler.update_equiv_class(selected_facts)
        self.cur_facts |= set(selected_facts)

        sk_facts = self.sk_system_handler.initial_by_question(question, topn)
        self.add_facts(sk_facts)

        self.cur_facts |= set(sk_facts)
        self.initial_sign = True

    def reset_fact_base(self) -> None:
        """将事实库置回初始状态，sign为False，尚不确定等价类和sanku信息是否有必要移除"""
        self.initial_sign = False
        self.cur_facts.clear()
        self.equivalence_handler.clear()  # 理论上如果这个函数仅有main调用，这一行是不应当有的。但我担心由于函数是外部的，如果被
        # 凑巧谁的代码调用过时，一步clear的冗余可以减少风险

    def get_facts(self) -> list[FACT_TYPE]:
        """待定，取出正在使用的所有facts，可能用于一些日志追踪等，尤其是求解完毕后打印所有的facts"""
        if self.initial_sign:
            return list(self.cur_facts)

        warnings.warn("Fact base has not been initialized yet.", stacklevel=2)
        return list(self.facts)

    def __str__(self) -> str:
        fact_count = len(self.facts)
        show_topn = 5

        fact_summary = ', '.join(str(fact) for fact in list(self.facts)[:show_topn])  # 只展示前五条事实

        # 如果事实数目大于5，提示用户后续还有更多
        if fact_count > show_topn:
            fact_summary += "..."

        return f"FactBase with {fact_count} facts. First 5 facts: [{fact_summary}]"
