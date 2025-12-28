from al_inference_engine.syntax.base_classes import Constant, CompoundTerm, Concept, Operator, TERM_TYPE, Variable
from functools import singledispatch


class EquivElem:
    """等价类中的一个元素"""

    def __init__(self, content: TERM_TYPE) -> None:
        self.content = content
        self._hash = get_hash(self.content)  # 缓存hash值，避免重复计算

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EquivElem):
            return self.content == other.content
        return False


@singledispatch
def get_hash(content: Constant | CompoundTerm | Concept | Operator | Variable) -> int:
    """
    使用singledispatchmethod是为了在后续添加新的类型的时候，能更加便捷地修改
    """
    return hash(content)


@get_hash.register(Constant)
def _(content: Constant) -> int:
    """
    取得hash值的时候，要考虑到Constant的value, name三个属性
    value的类型是string，因此直接返回hash值，无需递归
    """
    return hash((content.name, content.belong_concept))


@get_hash.register(CompoundTerm)
def _(content: CompoundTerm) -> int:
    """
    CompoundTerm的hash值应当考虑到Term的operator和所有的variable
    """
    return hash((content.operator, content.arguments))


@get_hash.register(Concept)
def _(content: Concept) -> int:
    """
    Concept的hash值应当考虑到Concept的name，name的类型为string，应当直接返回hash值
    """
    return hash(content.name)


@get_hash.register(Operator)
def _(content: Operator) -> int:
    """
    Operator的hash值暂时只需要考虑name，类型为string。我们暂时不允许name相同但Operator不同的情况
    """
    return hash(content.name)


@get_hash.register(Variable)
def _(content: Variable) -> int:
    """
    Operator的hash值暂时只需要考虑name，类型为string。我们暂时不允许name相同但Operator不同的情况
    """
    return hash(content.name)
