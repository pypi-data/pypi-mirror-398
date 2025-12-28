from al_inference_engine.syntax import Constant, Variable, CompoundTerm, AtomCompoundTerm, Assertion, Formula
from .builtin_concepts import BOOL_CONCEPT, example_concept_1, example_concept_2, example_concept_4
# 不同于builtin_operators.py中的注释，本文件模拟正常的builtin base的导入，由于引擎内部是直接导入py文件的，我们可以自然地使用相对导入。
# 同时两个文件也用于说明本体名可以用变量或字符串任一来调用
from .builtin_operators import example_operator_1, example_operator_2

true_const = Constant("TrueConst", BOOL_CONCEPT)
false_const = Constant('FalseConst', BOOL_CONCEPT)

# Example Constants
example_constant_1 = Constant("Alice", example_concept_1)
example_constant_2 = Constant("Bob", example_concept_1)
example_constant_3 = Constant("Red", example_concept_2)
example_constant_4 = Constant("desk", example_concept_4)


# Example Variables
example_variable_1 = Variable("x")
example_variable_2 = Variable("y")

# Example Terms
example_term_1 = CompoundTerm(
    example_operator_1,
    [example_constant_1, example_variable_1],
)
example_term_2 = CompoundTerm(
    example_operator_2,
    [example_constant_4],
)

# Example Atom CompoundTerm
example_atom_compound_term_1 = AtomCompoundTerm(
    example_operator_1,
    [example_constant_2, example_constant_1],
)

# Example Assertions
example_assertion_1 = Assertion(example_term_1, example_constant_1)
example_assertion_2 = Assertion(example_atom_compound_term_1, example_constant_1)

# Example Formulas
example_formula_1 = Formula(example_assertion_1, "AND", example_assertion_2)
example_formula_2 = Formula(example_assertion_2, "NOT", None)
