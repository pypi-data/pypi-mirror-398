"""最合理的方案是调用有名的包，不过我没看什么合适的，就先作罢，手搓一个。这个也不是关键瓶颈"""
from __future__ import annotations

from typing import cast, TYPE_CHECKING

# FIXME: 另外请注意这里只是一个简单的CNF，无法获得最小的CNF（每个clause的元素尽可能少）。而且现在的单测检查规则也不够智能，不是用永真式验证的
# 而是严格要求一致

from .base_classes import FACT_TYPE, Formula, Assertion


def _eliminate_implications(f: FACT_TYPE) -> FACT_TYPE:
    """
    1. 先递归处理左右子公式
    2. 如果当前节点是EQUAL，就把 A ↔ B 转换为 (A → B) ∧ (B → A)
    3. 如果当前节点是 IMPLIES，就把 A → B 转换为 (¬A) ∨ B
    """
    if isinstance(f, Assertion):
        return f

    # 递归下放
    left = _eliminate_implications(f.formula_left)
    right = None
    if f.formula_right is not None:
        right = _eliminate_implications(f.formula_right)

    if f.connective == 'EQUAL':
        if TYPE_CHECKING:
            right = cast('FACT_TYPE', right)  # 当connective为EQUAL的时候formula_right一定不为None

        # 构造两个单向蕴含
        impl1 = Formula(left, 'IMPLIES', right)
        impl2 = Formula(right, 'IMPLIES', left)
        # 递归消除里面的蕴含
        return Formula(
            _eliminate_implications(impl1),
            'AND',
            _eliminate_implications(impl2)
        )

    # 处理蕴含
    if f.connective == 'IMPLIES':
        # A → B  ⇒  (¬A) ∨ B
        neg_left = Formula(left, 'NOT', None)
        return Formula(neg_left, 'OR', right)

    return Formula(left, f.connective, right)


def _move_negations_inward(f: FACT_TYPE) -> FACT_TYPE:
    """
    使用德摩根律，把所有 ¬ 向内推进到原子断言层面。
    """
    if isinstance(f, Assertion):
        return f

    if f.connective != 'NOT':
        left = _move_negations_inward(f.formula_left)
        right = None
        if f.formula_right is not None:
            right = _move_negations_inward(f.formula_right)
        return Formula(left, f.connective, right)

    # 对应f.connective为 'NOT'
    inner = f.formula_left
    # 如果 ¬ 后面又是一个 Formula，就应用德摩根
    if isinstance(inner, Formula):
        if inner.connective == 'AND':
            # ¬(A ∧ B) => (¬A) ∨ (¬B)
            left = _move_negations_inward(Formula(inner.formula_left, 'NOT', None))
            right = _move_negations_inward(Formula(inner.formula_right, 'NOT', None)) if inner.formula_right is not None else None
            return Formula(left, 'OR', right)
        if inner.connective == 'OR':
            # ¬(A ∨ B) => (¬A) ∧ (¬B)
            left = _move_negations_inward(Formula(inner.formula_left, 'NOT', None))
            right = _move_negations_inward(Formula(inner.formula_right, 'NOT', None)) if inner.formula_right is not None else None
            return Formula(left, 'AND', right)
        if inner.connective == 'NOT':
            # ¬¬A => A
            return _move_negations_inward(inner.formula_left)

    # 如果formula_left是Assertion，不需要处理
    return f


def _distribute_or_over_and(f: FACT_TYPE) -> FACT_TYPE:
    """
    应用分配律，把 ∨ 分布到 ∧ 上，生成 CNF 形式。
    只处理当前节点是 OR 的情况，其它先递归。
    """
    if isinstance(f, Assertion):
        return f

    # 先递归下放
    left = _distribute_or_over_and(f.formula_left)
    right = None
    if f.formula_right is not None:
        right = _distribute_or_over_and(f.formula_right) if isinstance(f.formula_right, FACT_TYPE) else f.formula_right

    # 只关心 OR 节点
    if f.connective == 'OR':
        # 如果左子公式是 AND，(A ∧ B) ∨ C => (A ∨ C) ∧ (B ∨ C)
        if isinstance(left, Formula) and left.connective == 'AND':
            formula_left = left.formula_left
            formula_right = left.formula_right

            if TYPE_CHECKING:  # 当connective为AND的时候formula_right一定不为None
                # HACK: 理想情况下这个通过Formula内部保障，不过这个AND可能还是难以被mypy理解，可能也是工厂模式提供5个子类
                formula_right = cast('FACT_TYPE', formula_right)

            a = _distribute_or_over_and(Formula(formula_left, 'OR', right))
            b = _distribute_or_over_and(Formula(formula_right, 'OR', right))
            return Formula(a, 'AND', b)
        # 如果右子公式是 AND，A ∨ (B ∧ C) => (A ∨ B) ∧ (A ∨ C)
        if isinstance(right, Formula) and right.connective == 'AND':
            a = _distribute_or_over_and(Formula(left, 'OR', right.formula_left))
            b = _distribute_or_over_and(Formula(left, 'OR', right.formula_right))
            return Formula(a, 'AND', b)

    # 其它情况不变
    return Formula(left, f.connective, right)


def to_cnf(formula: FACT_TYPE) -> FACT_TYPE:
    """
    将任意公式转换为合取范式（CNF）。
    步骤：
      1. 消除蕴含
      2. 消除部分否定
      3. 分配率替换OR为AND
    """
    step1 = _eliminate_implications(formula)
    step2 = _move_negations_inward(step1)
    return _distribute_or_over_and(step2)  # 暂且认为不动点算法是非必要的，因为德摩根律不引入蕴含、分配率也不引入否定和蕴含。


def _split_and(f: FACT_TYPE) -> list[FACT_TYPE]:
    """
    如果当前公式是 AND 连接符，则递归拆分左右子公式，否则返回当前公式本身。
    """
    # 如果公式是一个原子断言，直接返回
    if isinstance(f, Assertion):
        return [f]

    # 如果当前公式的连接符是 AND，递归拆分左右子公式
    if f.connective == 'AND':
        left_facts = _split_and(f.formula_left)
        right_facts = _split_and(f.formula_right) if f.formula_right is not None else []
        return left_facts + right_facts

    # 如果当前公式的连接符不是 AND，直接返回当前公式
    return [f]


def to_cnf_clauses(formula: FACT_TYPE) -> list[FACT_TYPE]:
    """
    先将公式转为 CNF，然后分拆为多个子句
    """
    cnf_formula = to_cnf(formula)
    return _split_and(cnf_formula)
