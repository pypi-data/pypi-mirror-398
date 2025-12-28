import warnings
from collections.abc import Sequence
from typing import cast, TYPE_CHECKING

from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import FREEVARANY_CONCEPT
from al_inference_engine.syntax import (FACT_TYPE, TERM_TYPE, Assertion, Formula, CompoundTerm,
                                        Constant, Variable, ATOM_TYPE)
from functools import singledispatch


@singledispatch
def unify_all_terms(fact: FACT_TYPE | TERM_TYPE) -> tuple[CompoundTerm[Constant | CompoundTerm] | Constant, ...]:
    # hack: 注意这里和split等函数，回头可以再细分一下。比如有的可以支持带Variable的（这种回头也得改泛型）
    """
    主要是将作为formula的fact拆开成Assertion用的，对于单个的Assertion，我们拆成TERMTYPE，传入其他函数处理
    这里直接拆到AtomCompoundTerm方便一些
    """
    return ()


@unify_all_terms.register(Assertion)
def _(fact: Assertion) -> tuple[CompoundTerm[Constant | CompoundTerm] | Constant, ...]:
    return unify_all_terms(fact.lhs) + unify_all_terms(fact.rhs)


@unify_all_terms.register(Formula)
def _(fact: Formula) -> tuple[CompoundTerm[Constant | CompoundTerm] | Constant, ...]:
    tuple_left = unify_all_terms(fact.formula_left)
    tuple_right = unify_all_terms(fact.formula_right) if fact.formula_right is not None else ()
    return tuple_right + tuple_left


@unify_all_terms.register(CompoundTerm)
def _(fact: CompoundTerm[Constant | CompoundTerm]) -> tuple[CompoundTerm[Constant | CompoundTerm] | Constant, ...]:
    return tuple(split_all_terms(fact))


@unify_all_terms.register(Constant)
def _(fact: Constant) -> tuple[CompoundTerm[Constant | CompoundTerm] | Constant, ...]:
    return (fact, )


@unify_all_terms.register(Variable)
def _(fact: Variable) -> tuple[CompoundTerm[Constant | CompoundTerm] | Constant, ...]:
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


def split_all_terms(term: CompoundTerm[Constant | CompoundTerm]) -> list[CompoundTerm[Constant | CompoundTerm]]:
    """
    这个函能将一个Term的所有复合子结构取出来，返回一个list。
    """
    # 倒是Constant可能也算atom term，如果对类型标注比较麻烦就算了，可以区分为俩倒是，就注释时候仔细一点即可
    split_terms: list[CompoundTerm[Constant | CompoundTerm]] = []
    split_terms.append(term)  # 将一个复合的term中的复合子结构取出来

    if TYPE_CHECKING:
        term.arguments = cast("tuple[Constant | CompoundTerm[Constant | CompoundTerm], ...]", term.arguments)

    for var in term.arguments:
        if isinstance(var, CompoundTerm):
            split_terms.extend(split_all_terms(var))

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
