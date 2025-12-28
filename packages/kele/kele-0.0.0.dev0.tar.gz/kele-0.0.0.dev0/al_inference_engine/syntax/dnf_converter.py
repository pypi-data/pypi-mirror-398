from functools import reduce
import warnings
from sympy import Symbol
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent, simplify_logic
from bidict import bidict

from .base_classes import Assertion, Formula, Rule, Intro
from uuid import uuid1
from typing import TYPE_CHECKING, ClassVar, Any, cast


class _AssertionSymbol:
    assertion_to_id: ClassVar[bidict[Assertion, Symbol]] = bidict()

    @classmethod
    def get_symbol(cls, assertion: Assertion) -> Symbol:
        if assertion not in cls.assertion_to_id:
            cls.assertion_to_id[assertion] = Symbol(str(uuid1()))
        return cls.assertion_to_id[assertion]

    @classmethod
    def get_assertion(cls, assertion_id: Symbol) -> Assertion:
        return cls.assertion_to_id.inverse[assertion_id]


def convert_to_dnf(formula: Formula | Assertion) -> Formula | Assertion:
    """
    将一个公式转化为dnf格式

    :param formula: _description_
    :type formula: Formula | Assertion
    :return: _description_
    :rtype: Formula | Assertion
    """
    sympy_expr = _convert_to_sympy_expr(formula)
    dnf_sympy_expr = simplify_logic(sympy_expr, form='dnf')
    return _rebuild_formula(dnf_sympy_expr)


def _rebuild_formula(sympy_expr: Any) -> Formula | Assertion:  # noqa: ANN401
    if isinstance(sympy_expr, Symbol):
        return _AssertionSymbol.get_assertion(sympy_expr)
    if isinstance(sympy_expr, Not):
        return Formula(connective='NOT', formula_left=_rebuild_formula(sympy_expr.args[0]))
    if isinstance(sympy_expr, And):
        return reduce(lambda x, y: Formula(connective='AND', formula_left=x, formula_right=y),
                        map(_rebuild_formula, sympy_expr.args))
    if isinstance(sympy_expr, Or):
        return reduce(lambda x, y: Formula(connective='OR', formula_left=x, formula_right=y),
                        map(_rebuild_formula, sympy_expr.args))

    raise ValueError(f"Unknown sympy expression type {type(sympy_expr)}")


def _convert_to_sympy_expr(cur_formula: Formula | Assertion) -> Any:  # noqa: ANN401
    if isinstance(cur_formula, Assertion):
        return _AssertionSymbol.get_symbol(cur_formula)
    if cur_formula.connective == 'NOT':
        return Not(_convert_to_sympy_expr(cur_formula.formula_left))
    if TYPE_CHECKING:
        cur_formula.formula_right = cast("Formula | Assertion", cur_formula.formula_right)
    if cur_formula.connective == 'AND':
        return And(_convert_to_sympy_expr(cur_formula.formula_left), _convert_to_sympy_expr(cur_formula.formula_right))
    if cur_formula.connective == 'OR':
        return Or(_convert_to_sympy_expr(cur_formula.formula_left), _convert_to_sympy_expr(cur_formula.formula_right))
    if cur_formula.connective == 'IMPLIES':
        return Implies(_convert_to_sympy_expr(cur_formula.formula_left), _convert_to_sympy_expr(cur_formula.formula_right))
    if cur_formula.connective == 'EQUAL':
        return Equivalent(_convert_to_sympy_expr(cur_formula.formula_left), _convert_to_sympy_expr(cur_formula.formula_right))
    raise ValueError(f"Unknown connective {cur_formula.connective}")


class RuleSafetyProcesser:
    """
    将规则拆分成一系列规则，且body部分是DNF
    """
    def _split_into_dnf_formulas(self, formula: Formula | Assertion) -> list[Assertion | Formula]:
        """
        将公式拆分成DNF规则

        :param formula: 待拆分的公式
        :type formula: Formula | Assertion
        :return: 拆分后的DNF规则
        :rtype: list[Assertion | Formula]
        """
        if isinstance(formula, Assertion) or formula.connective != "OR":
            return [formula]
        if TYPE_CHECKING:
            formula.formula_right = cast("Formula | Assertion", formula.formula_right)
        return self._split_into_dnf_formulas(formula.formula_left) + self._split_into_dnf_formulas(formula.formula_right)

    def split_rule_and_process_safety[T1: Rule](self, rule: T1) -> list[T1]:
        """
        将公式拆分成DNF规则，并且将unsafe_variables以intro的形式加入规则

        :param formula: 待拆分的公式
        :type formula: Formula | Assertion
        :return: 拆分后的DNF规则
        :rtype: list[Assertion | Formula]
        """
        # 1、转化规则并拆分
        new_rules: list[T1] = []
        dnf_body = convert_to_dnf(rule.body)
        body_formulas = self._split_into_dnf_formulas(dnf_body)
        new_rules.extend(rule.replace(body=single_body_formula) for single_body_formula in body_formulas)

        # 2、将unsafe_variables以intro的形式加入新规则
        processed_new_rules: list[T1] = []

        for r in new_rules:
            unsafe_variables = r.unsafe_variables
            new_rule_body = r.body
            if unsafe_variables:
                warnings.warn(f"""规则 {r!s} 中包含不安全变量 {[str(u) for u in unsafe_variables]}，已自动处理\n
                          一个规则是安全的，如果它的action term中出现的variable和否定字面出现的variable都被包含在非action且肯定的assertion中\n
                          详细的内容请参阅引擎教程：#TODO
                          """, stacklevel=4)  # TODO: 需要具体的网址
            for single_variable in unsafe_variables:
                new_rule_body = Formula(new_rule_body, "AND", Intro(single_variable))

            new_rule = r.replace(body=new_rule_body)
            processed_new_rules.append(new_rule)

        return processed_new_rules
