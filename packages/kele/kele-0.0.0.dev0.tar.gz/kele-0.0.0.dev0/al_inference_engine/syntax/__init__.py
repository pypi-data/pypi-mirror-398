"""断言逻辑和推理引擎所需要的语法结构"""

# 导入 base_classes.py 中的核心类型
from .base_classes import (
    Constant,
    Variable,
    Concept,
    Operator,
    CompoundTerm,
    TERM_TYPE,
    Assertion,
    Formula,
    FACT_TYPE,
    Rule,
    Intro,
    Question,
    _QuestionRule,
    AtomCompoundTerm,
    ATOMTERM_TYPE,
    ATOM_TYPE,
    GROUNDED_TYPE_FOR_UNIFICATION,
    vf
)

# 导入 external.py 中的外部系统结构
from .external import (
    SankuManagementSystem,
)

__all__ = [  # noqa: RUF022
    # base_classes
    "Constant", "Variable", "Concept", "Operator", "CompoundTerm", "TERM_TYPE",
    "Assertion", "Formula", "FACT_TYPE", "Rule", "Question", "_QuestionRule",
    "AtomCompoundTerm", "ATOMTERM_TYPE", "ATOM_TYPE", "GROUNDED_TYPE_FOR_UNIFICATION",
    "vf", "Intro",

    # external
    "SankuManagementSystem",
]
