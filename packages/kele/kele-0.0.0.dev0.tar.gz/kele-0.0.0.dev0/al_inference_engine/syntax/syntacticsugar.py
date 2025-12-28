# ruff: noqa: PLR6301

"""
这个模块提供四则运算的语法糖，使用 Lark 语法解析器。
请注意每个CompoundTerm都必须用括号括起来，包括但不限于嵌套、原子的CompoundTerm等
支持的符号包括：
- 数字（整数或浮点数）
- 变量名（[A-Za-z_]\\w*）
- 括号（支持嵌套）
- 二元操作符：+、-、*、/
- 一元操作符：+、-
- 方程式：e_term "=" e_term
解析后会将语法树转换为推理引擎的syntax：CompoundTerm、Constant、Variable等
支持的op和concept置于builtin_base文件夹，例如 arithmetic_plus_op、arithmetic_minus_op 等。
"""

from __future__ import annotations

from typing import Final

from lark import Lark, Transformer, Token

from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import (
    COMPLEX_NUMBER_CONCEPT,
)
from al_inference_engine.knowledge_bases.builtin_base.builtin_operators import (
    arithmetic_divide_op,
    get_arithmetic_equation_op,
    arithmetic_minus_op,
    arithmetic_negate_op,
    arithmetic_plus_op,
    arithmetic_times_op,
)
from al_inference_engine.syntax import CompoundTerm, Constant, Variable, TERM_TYPE, Assertion, Formula


GRAMMAR: Final[str] = r"""
// 顶层：（方程中的）等式 | 带括号表达式 | 裸数字
start: equation
     | pexpr                 -> top_paren_expr
     | number

// （方程中的）等式：两侧允许 带括号表达式 或 裸数字
equation: e_term "=" e_term   -> equation
e_term: pexpr | number

// 带括号表达式：目前是四则运算 + 一元正负，允许嵌套
pexpr: "(" expr ")"          -> paren
     | "(" pexpr ")"         -> nested_paren

// 四则运算
?expr: expr "+" term         -> add
     | expr "-" term         -> sub
     | expr "*" term         -> mul
     | expr "/" term         -> div
     | "-" expr              -> neg
     | "+" expr              -> pos
     | term

?term: number
       | name
       | pexpr               // 支持嵌套括号

number: NUMBER
name: NAME

NAME: /[A-Za-z_]\w*/
%import common.NUMBER
%ignore /[ \t]+/
"""


class ToSyntax(Transformer):  # type: ignore[type-arg]
    """Transform Lark parse trees into AL inference engine terms."""

    # --- Entrypoints & helpers -------------------------------------------------

    def start(self, items: list[TERM_TYPE | Assertion | Formula]) -> TERM_TYPE | Assertion | Formula:
        """Return the single top-level term."""
        return items[0]

    def e_term(self, items: list[TERM_TYPE]) -> TERM_TYPE:
        """Return an equation-side term unchanged."""
        return items[0]

    # --- Parentheses handling --------------------------------------------------

    def top_paren_expr(self, items: list[TERM_TYPE]) -> TERM_TYPE:
        """Alias for a top-level parenthesized expression."""
        return items[0]

    def paren(self, items: list[TERM_TYPE]) -> TERM_TYPE:
        """Elide a single layer of parentheses."""
        return items[0]

    def nested_paren(self, items: list[TERM_TYPE]) -> TERM_TYPE:
        """Elide nested parentheses."""
        return items[0]

    # --- Atoms -----------------------------------------------------------------

    def number(self, items: list[Token]) -> Constant:
        """Convert a numeric token into a :class:`Constant`."""
        s = str(items[0])
        v = float(s) if ("." in s or "e" in s or "E" in s) else int(s)
        return Constant(v, COMPLEX_NUMBER_CONCEPT)

    def name(self, items: list[Token]) -> Variable:
        """Convert an identifier token into a :class:`Variable`."""
        return Variable(str(items[0]))

    # --- Unary ops -------------------------------------------------------------

    def neg(self, items: list[CompoundTerm]) -> CompoundTerm:
        """Build a unary negation term."""
        return CompoundTerm.from_parts(arithmetic_negate_op, [items[0]])

    def pos(self, items: list[CompoundTerm]) -> TERM_TYPE:
        """Return the inner term for unary plus (no-op)."""
        return items[0]

    # --- Binary ops ------------------------------------------------------------

    def add(self, items: list[CompoundTerm]) -> CompoundTerm:
        """Build an addition term."""
        left, right = items
        return CompoundTerm.from_parts(arithmetic_plus_op, [left, right])

    def sub(self, items: list[CompoundTerm]) -> CompoundTerm:
        """Build a subtraction term."""
        left, right = items
        return CompoundTerm.from_parts(arithmetic_minus_op, [left, right])

    def mul(self, items: list[CompoundTerm]) -> CompoundTerm:
        """Build a multiplication term."""
        left, right = items
        return CompoundTerm.from_parts(arithmetic_times_op, [left, right])

    def div(self, items: list[CompoundTerm]) -> CompoundTerm:
        """Build a division term."""
        left, right = items
        return CompoundTerm.from_parts(arithmetic_divide_op, [left, right])

    # --- Equation --------------------------------------------------------------

    def equation(self, items: list[CompoundTerm]) -> CompoundTerm:
        """Build an equality term for the left/right sides."""
        left, right = items
        return CompoundTerm.from_parts(get_arithmetic_equation_op, [left, right])


_parser: Lark = Lark(GRAMMAR, parser="lalr", maybe_placeholders=False)
_to_syntax: ToSyntax = ToSyntax()


class SyntacticSugar:
    """Callable facade that delegates to :func:`parse_term`."""

    def __call__(self, input_str: str) -> TERM_TYPE | Assertion | Formula:
        """Parse ``input_str`` and return a transformed term.

        Parameters
        ----------
        input_str
            The input string to parse.

        Returns
        -------
        Term
            The transformed term produced by :func:`parse_term`.

        Raises
        ------
        SyntaxError
            If parsing fails for any reason.
        """
        try:
            return _to_syntax.transform(_parser.parse(s))  # type: ignore[no-any-return]
        except Exception as e:
            raise SyntaxError(f"解析失败：{e}\n") from e


syntactic_sugar: Final[SyntacticSugar] = SyntacticSugar()


if __name__ == "__main__":
    cases: list[str] = [
        "(1+2)=3",
        "(x*2+3)",
        "1",
        "((1)+(2))=((3))",  # 多余括号仍可
        "((1)+(2))=3",
        "((1+2))=3",
        "(1+(2*3))=7",
        "(-(1+2))",  # 顶层表达式需括号
        "(1+x)",  # 所有的term都要求有括号
        "(1+(-x))",
        "(((1+x)))",
    ]
    for s in cases:
        print(s, "=>", syntactic_sugar(s))  # noqa: T201
