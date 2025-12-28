import warnings
from collections.abc import Sequence

from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import FREEVARANY_CONCEPT
from al_inference_engine.syntax import (FACT_TYPE, TERM_TYPE, Assertion, Formula, CompoundTerm,
                                        Constant, Variable, ATOM_TYPE)
from functools import singledispatch


@singledispatch
def _unify_all_terms(fact: FACT_TYPE | TERM_TYPE) -> tuple[CompoundTerm | Constant, ...]:
    """
    主要是将作为formula的fact拆开成Assertion用的，对于单个的Assertion，我们拆成TERMTYPE，传入其他函数处理
    这里直接拆到AtomCompoundTerm方便一些
    """
    return ()


@_unify_all_terms.register(Assertion)
def _(fact: Assertion) -> tuple[CompoundTerm | Constant, ...]:
    return _unify_all_terms(fact.lhs) + _unify_all_terms(fact.rhs)


@_unify_all_terms.register(Formula)
def _(fact: Formula) -> tuple[CompoundTerm | Constant, ...]:
    tuple_left = _unify_all_terms(fact.formula_left)
    tuple_right = _unify_all_terms(fact.formula_right) if fact.formula_right is not None else ()
    return tuple_right + tuple_left


@_unify_all_terms.register(CompoundTerm)
def _(fact: CompoundTerm) -> tuple[CompoundTerm | Constant, ...]:
    return tuple(_split_all_terms(fact))


@_unify_all_terms.register(Constant)
def _(fact: Constant) -> tuple[CompoundTerm | Constant, ...]:
    return (fact, )


@_unify_all_terms.register(Variable)
def _(fact: Variable) -> tuple[CompoundTerm | Constant, ...]:
    warnings.warn("Variable should not exist in fact", stacklevel=2)
    return ()


class FREEVARANY(Constant):
    """
    ANY标签，在free_variables用于占位，暂定为一种特殊的Constant。
    本引擎在atom term的level上进行grounding操作，即规则、事实中的fact都会被拆解到atom term层级进行匹配。因此nested term需要被拆解为多个
    atom term完成，并且nested term的arguments里的Term类型的值，需要被替换为通配符，即FREEVARANY类
    """

    def __init__(self, value: str) -> None:
        concept = FREEVARANY_CONCEPT
        super().__init__(value, concept)


FREEANY = FREEVARANY('FREEVARANY')


def _split_all_terms(term: CompoundTerm) -> list[CompoundTerm]:
    """
    这个函能将CompoundTerm拆分成AtomCompoundTerm，并且返回一个list
    返回的过程中，除非所有的arguments都是Term，否则都会标记之后生成AtomCompoundTerm
    这个函数只应当用在Fact当中，因为它不处理含有Variable的情况
    """
    # NOTE: 常量在 _unify_all_terms 层面单独处理，这里仅拆分 CompoundTerm
    split_terms: list[CompoundTerm] = []
    split_terms.append(term)  # 将一个复合的term中的复合子结构取出来

    for var in term.arguments:
        if isinstance(var, CompoundTerm):
            split_terms.extend(_split_all_terms(var))
    return split_terms


def atomize_arguments(arguments: Sequence[TERM_TYPE]) -> tuple[ATOM_TYPE, ...]:  # 暂时先作为对外函数，
    # 另外这一页的singledispatch按说可以改成正常的if，以获得更清晰的阅读体验（比如把class丢最上面）
    """
    给定一个term，这个函数会将term的arguments中的所有Term替换为$F
    无论在fact还是rule中这个函数都是可用的，因为是否存在variable并不影响这个函数的工作
    """
    return tuple(
        FREEANY if isinstance(var, CompoundTerm) else var
        for var in arguments
    )


@singledispatch
def _unify_into_terms(fact: FACT_TYPE | TERM_TYPE) -> tuple[TERM_TYPE, ...]:
    """
    主要是将作为formula的fact拆开成Assertion用的，对于单个的Assertion，我们拆成TERMTYPE，传入其他函数处理
    这里直接拆到AtomCompoundTerm方便一些
    """
    return ()


@_unify_into_terms.register(Assertion)
def _(fact: Assertion) -> tuple[TERM_TYPE, ...]:
    return (fact.lhs, fact.rhs)


@_unify_into_terms.register(Formula)
def _(fact: Formula) -> tuple[TERM_TYPE, ...]:
    tuple_left = _unify_all_terms(fact.formula_left)
    tuple_right = _unify_all_terms(fact.formula_right) if fact.formula_right is not None else ()
    return tuple_right + tuple_left


@_unify_into_terms.register(TERM_TYPE)
def _(fact: TERM_TYPE) -> tuple[TERM_TYPE, ...]:
    return (fact, )
