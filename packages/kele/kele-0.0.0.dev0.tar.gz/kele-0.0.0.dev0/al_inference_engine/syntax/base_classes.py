from __future__ import annotations

import functools
import itertools
import warnings
from collections import defaultdict
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, Literal, cast, Self
from collections.abc import Sequence, Mapping
import inspect

import os

# When enabled, `from_parts` will run full `__init__` validation instead of bypassing checks.
# Use this in tests/CI to catch invalid internal object construction early.
_RUN_INIT_VALIDATION_IN_FROM_PARTS = os.getenv("RUN_INIT_VALIDATION_IN_FROM_PARTS", "").strip().lower() not in {"", "0", "false", "no"}

if TYPE_CHECKING:
    from collections.abc import Callable


class HashableAndStringable(Protocol):
    """An object that can be converted to a string."""

    def __str__(self) -> str:
        """Return the string representation of the object."""
        ...

    def __hash__(self) -> int:
        """Return the hash value of the object."""
        ...

    def __eq__(self, other: object, /) -> bool:
        """Return whether this object equals another object."""
        ...


class Constant:
    """object"""

    def __init__(self,
                 name: HashableAndStringable,
                 belong_concept: Concept | str | Sequence[Concept | str],  # FIXME: Rename to belong_concepts.
                 comments: str = '',
                 ) -> None:
        """
        :param name: Constant value.
        :param belong_concept: Each Constant must belong to at least one Concept.
        :param comments: Optional annotations.
        """
        self.name = name  # Allow any value with __str__ and __hash__ for flexibility.

        self.belong_concept = self._normalize_concepts(belong_concept)
        self.belong_concept_hash_key = tuple(sorted(self.belong_concept))  # Lists are unhashable; sort concept names into a tuple.

        self.comments = comments

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Constant):
            return False
        return self.name == other.name and bool(self.belong_concept & other.belong_concept)  # Sets have no duplicates; any overlap is enough.

    def __hash__(self) -> int:
        return hash((self.name, self.belong_concept_hash_key))

    def __str__(self) -> str:
        return str(self.name)

    @functools.cached_property
    def free_variables(self) -> tuple[Variable, ...]:  # Tuple (not set) to allow same-name variables at different addresses.
        """Return free variables contained within."""
        return ()

    @functools.cached_property
    def is_action_term(self) -> bool:
        """Return whether this is an action term."""
        return False

    def replace_variable(self, var_map: Mapping[Variable, Constant | CompoundTerm]) -> Constant:
        """Return a grounded instance for the current object."""
        # Constant is returned directly; no replacement needed.
        return self

    @property
    def belong_concept_str(self) -> str:
        """
        Return a human-readable string representation of the concepts this object belongs to.
        """
        return "∩".join([str(c) for c in list(self.belong_concept)])

    @staticmethod
    def _normalize_concepts(belong_concept: Concept | str | Sequence[Concept | str]) -> set[Concept]:
        """
        Normalize the given concept(s).

        If a concept or a sequence of concepts is provided, this method attempts to
        retrieve or create them from the declared concepts.

        :param concepts: A single Concept, a concept name (str), or a sequence of Concepts or names.
        :type concepts: Concept | str | Sequence[Concept | str]
        :return: A non-empty tuple of normalized Concept objects.
        :rtype: tuple[Concept, ...]

        :raises TypeError: If ``concepts`` is not a Concept, str, or a valid sequence of them.
        :raises ValueError: If ``concepts`` is empty after normalization.
        """  # noqa: DOC501
        if not isinstance(belong_concept, (Concept, str, Sequence)) or isinstance(belong_concept, (bytes, bytearray)):  # type: ignore[unreachable]
            # Skip details like Sequence[xx] checks here.
            raise TypeError(
                f"belong_concept must be Concept, str or Sequence[Concept | str]; got {type(belong_concept)!s}."
            )

        concepts = Concept.normalize_to_set(belong_concept)
        if not concepts:
            raise ValueError("belong_concept must be nonempty; a Constant must belong to at least one Concept.")

        return concepts


class Variable:
    """
    Variable.

    - The external display (str) always uses the original user-provided name.
    - When the engine accesses `name`, if RuleBase renamed it, return the unique name; otherwise return the user name.
    """
    def __init__(self, name: HashableAndStringable, *, _original_name: str | None = None) -> None:
        self.name = str(name)
        self._original_name = _original_name  # Keep the original user-provided name internally.

    def create_renamed_variable(self, new_name: str) -> Variable:
        """Create a renamed variable while preserving the original display name."""
        return Variable(new_name, _original_name=self._original_name or self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variable):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    @property
    def display_name(self) -> str:
        """Display name for external use, usually the user input, distinct from internal unique IDs."""
        return self._original_name if self._original_name is not None else self.name

    def __str__(self) -> str:
        return self.display_name

    def __lt__(self, other: Variable) -> bool:
        return self.display_name < other.display_name  # Prefer original names for display-centric sorting.

    @functools.cached_property
    def free_variables(self) -> tuple[Variable, ...]:
        """Return free variables contained within."""
        return (self, )

    @functools.cached_property
    def is_action_term(self) -> bool:
        """Return whether this is an action term."""
        return False

    def replace_variable(self, var_map: Mapping[Variable, Constant | CompoundTerm]) -> TERM_TYPE:
        """Return a grounded instance for the current object."""
        return var_map[self]


class Concept:
    """A collection of Constants that share the something in common.
    """

    # Store declared Concepts to avoid duplicate declarations.
    declared_concepts: ClassVar[dict[str, Concept]] = {}

    # --- Transitive closure structures for fast subsumption checks ---
    _parents: ClassVar[dict[Concept, set[Concept]]] = {}
    _children: ClassVar[dict[Concept, set[Concept]]] = {}
    _ancestors_inclusive: ClassVar[dict[Concept, set[Concept]]] = {}
    _descendants_inclusive: ClassVar[dict[Concept, set[Concept]]] = {}

    def __init__(self, name: HashableAndStringable, comments: str = '', parents: Sequence[Concept | str] | None = None) -> None:
        self.name = str(name)
        self.comments = comments

        Concept._initial_subsumption_structure(self)
        if parents:
            for par in parents:
                Concept.add_subsumption(self, par)

    def __new__(cls, name: HashableAndStringable, comments: str = '', parents: Sequence[Concept | str] | None = None) -> Concept:  # noqa: PYI034
        """Ensure Concept uniqueness."""
        key = str(name)
        if key in cls.declared_concepts:
            return cls.declared_concepts[key]
        obj = super().__new__(cls)
        cls.declared_concepts[key] = obj
        return obj

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Concept):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

    # ---- Concept subsumption maintenance and queries ----
    @classmethod
    def _initial_subsumption_structure(cls, c: Concept) -> None:
        if c not in cls._parents:
            cls._parents[c] = set()
        if c not in cls._children:
            cls._children[c] = set()
        if c not in cls._ancestors_inclusive:
            cls._ancestors_inclusive[c] = {c}
        else:
            cls._ancestors_inclusive[c].add(c)
        if c not in cls._descendants_inclusive:
            cls._descendants_inclusive[c] = {c}
        else:
            cls._descendants_inclusive[c].add(c)

    @classmethod
    def add_subsumption(cls, child: Concept | str, parent: Concept | str) -> None:
        """
        Declare a subsumption (subset) relation: child ⊆ parent.
        :raise ValueError: Disallow A ⊊ b and b ⊊ a at the same time.
        """  # noqa: DOC501
        child_c = cls._convert_concept(child)
        parent_c = cls._convert_concept(parent)

        cls._initial_subsumption_structure(child_c)
        cls._initial_subsumption_structure(parent_c)

        # Ignore reflexive relationships.
        if child_c is parent_c:
            return

        # Disallow mutual subsets: if parent ⊆ child already exists, reject child ⊆ parent.
        anc_parent = cls._ancestors_inclusive.get(parent_c, {parent_c})
        if child_c in anc_parent:
            raise ValueError(
                f"Mutual subsumption is not allowed: {parent_c} ⊆ {child_c} already exists, cannot add {child_c} ⊆ {parent_c}."
            )

        # Skip if already exists (including transitive).
        if parent_c in cls._ancestors_inclusive[child_c]:
            return

        # Direct edge.
        cls._parents[child_c].add(parent_c)
        cls._children[parent_c].add(child_c)

        # Incremental closure update.
        child_descs = set(cls._descendants_inclusive[child_c])
        parent_ancs = set(cls._ancestors_inclusive[parent_c])

        # Merge parent's ancestors into all descendants' ancestors.
        for d in child_descs:
            anc = cls._ancestors_inclusive[d]
            plus = parent_ancs - anc
            if plus:
                anc |= plus

        # Merge child's descendants into all ancestors' descendants.
        for a in parent_ancs:
            des = cls._descendants_inclusive[a]
            plus = child_descs - des
            if plus:
                des |= plus

    def set_parents(self, parents: Sequence[Concept | str]) -> Concept:
        """Directly register parents for the current concept."""
        for p in parents:
            Concept.add_subsumption(self, p)
        return self

    @classmethod
    def _convert_concept(cls, c: Concept | str) -> Concept:
        if isinstance(c, str):
            warnings.warn(f"Concept '{c!s}' not found; created automatically.", stacklevel=2)
            return Concept(c)

        return c

    def __le__(self, other: Concept) -> bool:
        return self.is_subconcept_of(other)

    def __lt__(self, other: Concept) -> bool:
        return self is not other and self <= other

    @staticmethod
    def is_subconcept_rel(c1: Concept, c2: Concept) -> bool:
        """Return whether c1 is a subconcept of c2 (or the same concept)."""
        # 1. Same concept.
        if c1 is c2:
            return True

        # FREEVARANY wildcard.
        from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import FREEVARANY_CONCEPT  # noqa: PLC0415
        if c1 is FREEVARANY_CONCEPT or c2 is FREEVARANY_CONCEPT:
            return True

        # Subsumption: check if c2 is in c1's ancestors; parent sets are usually smaller.
        anc = Concept._ancestors_inclusive.get(c1)
        return bool(anc and c2 in anc)

    def is_subconcept_of(self, c: Concept) -> bool:
        """Return whether the current concept is a subconcept of c (or equal)."""
        return self.is_subconcept_rel(self, c)

    @classmethod
    def normalize(cls, spec: Concept | str | Sequence[Concept | str]) -> tuple[Concept, ...]:
        """
        If a concept or a sequence of concepts is provided, this method attempts to
            retrieve from the declared concepts or create them, and then return a tuple of them.
        """
        if isinstance(spec, (Concept, str)):
            return (cls._convert_concept(spec),)
        return tuple(cls._convert_concept(x) for x in spec)

    @classmethod
    def normalize_to_set(cls, spec: Concept | str | Sequence[Concept | str]) -> set[Concept]:
        """
        If a concept or a sequence of concepts is provided, this method attempts to
            retrieve from the declared concepts or create them, and then return a set of them.
        """
        if isinstance(spec, (Concept, str)):
            return {cls._convert_concept(spec)}
        return {cls._convert_concept(x) for x in spec}

    @classmethod
    def _upward_closure(cls, cons: set[Concept]) -> set[Concept]:
        """Upward closure: each concept + all its ancestors (including itself)."""
        out: set[Concept] = set()
        for c in cons:
            out |= cls._ancestors_inclusive.get(c, {c})
        return out

    @classmethod
    def _downward_closure(cls, cons: set[Concept]) -> set[Concept]:
        """Downward closure: each concept + all its descendants (including itself)."""
        out: set[Concept] = set()
        for c in cons:
            out |= cls._descendants_inclusive.get(c, {c})
        return out

    @classmethod
    def belong_intersection_match(cls, con_candidate: set[Concept], con_constraint: set[Concept]) -> bool:
        """
        Check whether con_candidate satisfies con_constraint.
        For each constraint concept c, there exists a candidate x such that x ⊆ c (more specific is acceptable).
        """
        if not con_constraint:
            return True

            # FREEVARANY wildcard (following is_subconcept_rel semantics).
        from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import \
            FREEVARANY_CONCEPT  # noqa: PLC0415
        if FREEVARANY_CONCEPT in con_candidate:
            return True

        upward = cls._upward_closure(con_candidate)

        return con_constraint.issubset(upward)

    @classmethod
    def union_match(cls, con_s1: set[Concept], con_s2: set[Concept]) -> bool:
        """Loose matching: treat subsumption as "intersection" matching, no input/constraint distinction.
        Returns whether there is a non-empty common concept set aligned by the hierarchy.
        """
        if not con_s1 or not con_s2:  # Empty means universal set.
            return True

        from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import \
            FREEVARANY_CONCEPT  # noqa: PLC0415    # TODO: Replace FREEVARANY_CONCEPT with wildcard for consistency.

        # Wildcard: any FREEVARANY passes.
        if FREEVARANY_CONCEPT in con_s1:
            return True

        upward_input = cls._downward_closure(con_s1)  # FIXME: Consider fixed point / upward closure carefully.
        upward_constraint = cls._downward_closure(con_s2)

        return bool(upward_input & upward_constraint)

    @classmethod
    def is_compatible(  # TODO: Consider recording mismatch details later.
        cls,
        con_candidate: Concept | str | Sequence[Concept | str] | set[Concept],
        con_constraint: Concept | str | Sequence[Concept | str] | set[Concept],
        *,
        fuzzy_match: bool = True
    ) -> bool:
        """
        determine whether x and y are compatible.

        con_candidate defaults to the intersection of concepts.

        con_constraint depends on fuzzy_match:

        fuzzy_match = False:
        - Strict: require con_s1 to be a subset of con_s2 (correct type inference).
        fuzzy_match = True:
        - Loose: require con_s1 to intersect con_s2. This allows users to omit complete concept annotations by
          using a union for constraints instead of the default intersection.

        When the type is set, it is viewed as an internal call; accept Concepts only (no Concept | str).
        """
        if not isinstance(con_candidate, set):
            con_candidate = cls.normalize_to_set(con_candidate)
        if not isinstance(con_constraint, set):
            con_constraint = cls.normalize_to_set(con_constraint)

        if fuzzy_match:
            return Concept.union_match(con_candidate, con_constraint)

        return Concept.belong_intersection_match(con_candidate, con_constraint)


class Operator:
    """Syntax element for assertion logic expressing relations among individuals and concepts."""

    # Store declared Operators to avoid duplicate declarations.
    declared_operators: ClassVar[dict[str, Operator]] = {}

    def __init__(
        self,
        name: HashableAndStringable,
        input_concepts: Sequence[Concept | str],
        output_concept: Concept | str,
        implement_func: Callable[[AtomCompoundTerm], TERM_TYPE] | None = None,  # If action_op always targets
        # AtomCompoundTerm, consider passing arity const values to implement_func for convenience.
        comments: str = '',
    ) -> None:
        """
        :param name: Operator name, used to uniquely identify the operation.
        :param input_concepts: Input concept list describing accepted parameter types.
        :param output_concept: Output concept describing the return type.
        :param implement_func: Optional function defining operator semantics, reducing fact input.
        :param comments: Optional annotation describing usage or notes.

        :raises TypeError: Raised when `input_concepts` is not a Concept list, `output_concept` is not a Concept,
                           or `implement_func` is not callable (non-None and non-callable).
        """  # noqa: DOC501

        # Validation and defaults: auto-declare missing concepts with warnings.
        # Process input concepts.
        input_concept_instances = self._normalize_concepts(input_concepts)

        if not isinstance(output_concept, (str, Concept)):
            raise TypeError(f"output_concept must be a Concept or its name, got {type(output_concept)}")
        output_concept_instance = self._normalize_concepts(output_concept)[0]  # Output has only one concept.

        if implement_func is not None and not callable(implement_func):
            raise TypeError('implement_func must be Callable or None')

        self.name = str(name)
        self.input_concepts = input_concept_instances
        self.output_concept = output_concept_instance
        self.implement_func = implement_func
        self.comments = comments

    def __new__(  # noqa: PYI034 This conflicts with mypy.
        cls,
        name: HashableAndStringable,
        input_concepts: Sequence[Concept],
        output_concept: Concept,
        implement_func: Callable[..., TERM_TYPE] | None = None,
        comments: str = '',
    ) -> Operator:
        """
        Use __new__ to control instantiation and avoid duplicate instances.
        """
        key = str(name)
        if key in cls.declared_operators:
            return cls.declared_operators[key]
        obj = super().__new__(cls)
        cls.declared_operators[key] = obj
        return obj

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:  # Operators are equal if their names match.
        if not isinstance(other, Operator):
            return False
        return self.name == other.name

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def _normalize_concepts(concepts: Concept | str | Sequence[Concept | str]) -> tuple[Concept, ...]:
        """
        Normalize the given concept(s).

        If a concept or a sequence of concepts is provided, this method attempts to
        retrieve or create them from the declared concepts.

        :param concepts: A single Concept, a concept name (str), or a sequence of Concepts or names.
        :type concepts: Concept | str | Sequence[Concept | str]
        :return: A non-empty tuple of normalized Concept objects.
        :rtype: tuple[Concept, ...]

        :raises TypeError: If ``concepts`` is not a Concept, str, or a valid sequence of them.
        :raises ValueError: If ``concepts`` is empty after normalization.
        """  # noqa: DOC501
        if not isinstance(concepts, (Concept, str, Sequence)):
            raise TypeError(
                f"input_concepts/output_concepts must be Concept, str or Sequence[Concept | str]; got {type(concepts)!s}."
            )

        concepts = Concept.normalize(concepts)
        if not concepts:
            raise ValueError("input_concepts/output_concepts must be nonempty.")

        return concepts


class CompoundTerm[T1: Constant | Variable | HashableAndStringable = Constant | Variable | HashableAndStringable]:
    # hack: This generic is tricky; T1 is theoretically TERM_TYPE | HashableAndStringable, but CompoundTerm is removed
    # to avoid circular references. Type checkers rely on CompoundTerm also satisfying HashableAndStringable, which
    # is not the intended design. All syntax layers have str/hash, so it passes; rely on developer caution and review.
    """Structure like op(xxx). In theory Constant, concept, operator, and op(term) are all terms, but we only handle the last."""
    def __init__(self, operator: Operator | str, arguments: Sequence[T1 | CompoundTerm]) -> None:
        """
        :param operator: Operator of the term.
        :param arguments: Term expression op(t1, ... , tn). Arguments must be TERM_TYPE.
        Non-conforming inputs (e.g., HashableAndStringable) default to Constant.
        risk: The first version does not accept concept | operator as parameters.
        """  # noqa: DOC501
        # Process operator.
        declared = Operator.declared_operators
        if isinstance(operator, str):
            if operator in declared:
                operator_instance = declared[operator]
            else:
                # Cannot auto-create operator without input/output concepts; Concept args don't define output.
                raise ValueError(f"Operator '{operator}' not found in declared_operators")
        elif isinstance(operator, Operator):
            operator_instance = operator
        else:
            raise TypeError(f"operator must be a Operator object or its name，got {type(operator)}")

        if not isinstance(arguments, Sequence):
            raise TypeError("arguments must be a sequence")

        if len(arguments) != len(operator_instance.input_concepts):
            raise ValueError(
                f"Input arguments {[str(a) for a in arguments]} (count {len(arguments)}); \n"
                f"do not match operator {operator_instance} input count {len(operator_instance.input_concepts)}, "
                f"expected {[str(c) for c in operator_instance.input_concepts]}")

        self.operator = operator_instance  # Assign early to satisfy mypy.

        # Validate argument types based on input concepts.
        argument_instances: list[TERM_TYPE] = []
        for i, (expected_concept, arg) in enumerate(zip(operator_instance.input_concepts, arguments)):  # noqa: B905
            if not isinstance(arg, TERM_TYPE):
                argument_instances.append(Constant(arg, expected_concept))
                warnings.warn("non-term input will be transformed into Constant", stacklevel=2)
                continue

            # TODO: No need to check concept and operator for now.
            # Constants may belong to multiple Concepts; any matching concept is acceptable.
            if isinstance(arg, Constant) and not Concept.is_compatible(arg.belong_concept, expected_concept, fuzzy_match=False):
                raise ValueError(
                    f"Argument {i} has concept intersection {arg.belong_concept_str}, but expected {expected_concept!s}"
                )

            if isinstance(arg, CompoundTerm) and not Concept.is_compatible(arg.operator.output_concept, expected_concept, fuzzy_match=False):
                raise ValueError(
                    f"Argument {i} has concept {arg.operator.output_concept!s}, but expected {expected_concept!s}"
                )

            argument_instances.append(arg)

        self.arguments = tuple(argument_instances)

    def __new__(cls, operator: Operator, arguments: Sequence[TERM_TYPE]) -> CompoundTerm:  # noqa: PYI034 Conflicts with mypy.
        """
        Use __new__ to control term creation and instantiate AtomCompoundTerm when eligible.
        """
        if all(not isinstance(argument, CompoundTerm) for argument in arguments):
            return super().__new__(AtomCompoundTerm)
        return super().__new__(cls)

    def __eq__(self, other: object) -> bool:  # Terms are equal if operator and arguments match.
        if not isinstance(other, CompoundTerm):
            return False
        return self.operator == other.operator and self.arguments == other.arguments

    def __hash__(self) -> int:  # Hash terms by operator and arguments.
        return hash((self.operator, self.arguments))

    def __str__(self) -> str:  # Print terms using operator and arguments only.
        return f'{self.operator.name}({", ".join(str(u) for u in self.arguments)})'

    @functools.cached_property
    def free_variables(self) -> tuple[Variable, ...]:
        """Return free variables contained within."""
        return tuple(itertools.chain.from_iterable([v.free_variables for v in self.arguments]))

    @classmethod
    def from_parts(cls, operator: Operator, arguments: Sequence[TERM_TYPE]) -> CompoundTerm:
        """Lightweight construction: skip __init__ checks for trusted internal use (e.g., replace_variable)."""
        if TYPE_CHECKING:
            if _RUN_INIT_VALIDATION_IN_FROM_PARTS:
                return cls(operator, cast("Sequence[T1 | CompoundTerm[Constant | Variable | HashableAndStringable]]", arguments))
            # TODO: Investigate this unexpected mypy check failure.
        elif _RUN_INIT_VALIDATION_IN_FROM_PARTS:
            return cls(operator, arguments)

        target_cls = AtomCompoundTerm if all(not isinstance(argument, CompoundTerm) for argument in arguments) else CompoundTerm
        obj = object.__new__(target_cls)
        # Set fields directly to avoid __init__ validation.
        obj.operator = operator
        obj.arguments = tuple(arguments)
        return obj

    @functools.cached_property
    def is_action_term(self) -> bool:
        """
        Determine whether the current term is an action term.

        :return: Whether this is an action term.
        :rtype: bool
        :raises ValueError: If operator implements implement_func but is not AtomCompoundTerm.
        """  # noqa: DOC501
        if self.operator.implement_func is not None and (not isinstance(self, AtomCompoundTerm)):
            raise ValueError(f"operator {self.operator} implements implement_func but is not AtomCompoundTerm")
        return self.operator.implement_func is not None

    def replace_variable(self, var_map: Mapping[Variable, Constant | CompoundTerm]) -> CompoundTerm:
        """Return a grounded instance for the current object."""
        # For CompoundTerm, recursively process arguments.
        if not self.free_variables:
            return self

        new_arguments: list[TERM_TYPE] = []
        for arg in self.arguments:
            if type(arg) is Variable:
                new_arguments.append(var_map[arg])
            elif type(arg) is Constant:  # hack: If TERM_TYPE changes, this else may add overhead.
                # Similar checks appear elsewhere.
                new_arguments.append(arg)
            else:
                new_arguments.append(arg.replace_variable(var_map))

        return self.from_parts(self.operator, new_arguments)


TERM_TYPE = Constant | CompoundTerm | Variable  # risk: concept | operator are terms too, but not handled yet.


def _term_possible_concepts(term: TERM_TYPE) -> set[Concept]:  # FIXME: Consider moving.
    """Return possible/declared Concepts for a term.

    - Constant: return its belong_concept (can be multiple).
    - CompoundTerm: return operator.output_concept.
    - Variable: has no direct concept binding in syntax; return empty (constraints inferred from Rule/Assertion).
    """
    if isinstance(term, Constant):
        return term.belong_concept
    if isinstance(term, CompoundTerm):
        return {term.operator.output_concept}
    return set()  # FIXME: Consider whether Variables should be inferred here.


class Assertion:  # TODO: Consider a dedicated action op class requiring left-to-right, like "is".
    # This would avoid repeated only_substitution checks on both sides.
    """Basic unit representing facts/knowledges in assertion logic."""

    def __init__(self, lhs: TERM_TYPE | HashableAndStringable, rhs: TERM_TYPE | HashableAndStringable | None = None) -> None:
        """
        An assertion is an expression of the form a = b, representing a piece of knowledge.
        :param lhs: Must be TERM_TYPE. Non-conforming inputs (e.g., HashableAndStringable) default to Constant.
        :param rhs: Must be TERM_TYPE. Non-conforming inputs (e.g., HashableAndStringable) default to Constant.
        :raises TypeError: a and b must be terms in the theoretical sense, not necessarily the Term class (which only treats op(...) as Term).
        """  # noqa: DOC501
        if not isinstance(lhs, TERM_TYPE):
            from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import BOOL_CONCEPT  # noqa: PLC0415
            from al_inference_engine.knowledge_bases.builtin_base.builtin_facts import true_const  # noqa: PLC0415
            # Avoid circular imports by importing at runtime; only when needed.

            if not isinstance(rhs, CompoundTerm):
                raise TypeError('one of lhs and rhs must be TERM_TYPE at least')

            if rhs.operator.output_concept is BOOL_CONCEPT and 'true' in str(rhs).strip().lower():
                # Normalize true representation when lhs was set to TrueConst earlier.
                warnings.warn(f'replace {rhs} with builtin TrueConst', stacklevel=2)
                lhs = true_const
            else:
                warnings.warn('non-term input will be transformed into Constant', stacklevel=2)
                lhs = Constant(rhs, rhs.operator.output_concept)

        if rhs is None:
            from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import BOOL_CONCEPT  # noqa: PLC0415
            from al_inference_engine.knowledge_bases.builtin_base.builtin_facts import true_const  # noqa: PLC0415

            if isinstance(lhs, CompoundTerm) and lhs.operator.output_concept is BOOL_CONCEPT:  # If RHS is True, it can be omitted.
                rhs = true_const
            else:
                raise ValueError("only the boolean value True can be omitted.")

        if not isinstance(rhs, TERM_TYPE):
            from al_inference_engine.knowledge_bases.builtin_base.builtin_concepts import BOOL_CONCEPT  # noqa: PLC0415
            from al_inference_engine.knowledge_bases.builtin_base.builtin_facts import true_const  # noqa: PLC0415

            if not isinstance(lhs, CompoundTerm):
                raise TypeError('one of lhs and rhs must be TERM_TYPE at least')

            if lhs.operator.output_concept is BOOL_CONCEPT and 'true' in str(rhs).strip().lower():
                # Normalize true representation when rhs was set to TrueConst earlier.
                warnings.warn(f'replace {rhs} with builtin TrueConst', stacklevel=2)
                rhs = true_const
            else:
                warnings.warn('non-term input will be transformed into Constant', stacklevel=2)
                rhs = Constant(rhs, lhs.operator.output_concept)

        self.lhs = lhs
        self.rhs = rhs

        # -------- Concept consistency checks --------
        # Only validate when both sides have inferable concepts.
        lhs_concepts = _term_possible_concepts(self.lhs)
        rhs_concepts = _term_possible_concepts(self.rhs)

        if not Concept.union_match(lhs_concepts, rhs_concepts):  # TODO: Replace with inferred lhs | rhs concepts.
            raise ValueError(
                f"Assertion concept mismatch: {self.lhs!s} has concepts { [str(c) for c in list(lhs_concepts)] } "
                f"and {self.rhs!s} has concepts { [str(c) for c in list(rhs_concepts)] } with no intersection"
            )

    @classmethod
    def from_parts(cls, lhs: TERM_TYPE, rhs: TERM_TYPE) -> Self:
        """Trusted internal construction: skip __init__ conversions and Concept validation."""
        if _RUN_INIT_VALIDATION_IN_FROM_PARTS:
            return cls(lhs, rhs)
        obj = object.__new__(cls)
        obj.lhs = lhs
        obj.rhs = rhs
        return obj

    def __eq__(self, other: object) -> bool:  # Assertions are equal if lhs and rhs match.
        if not isinstance(other, Assertion):
            return False
        return self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self) -> int:  # Hash assertions by lhs and rhs.
        return hash((self.lhs, self.rhs))

    def __str__(self) -> str:
        return f'{self.lhs} = {self.rhs}'

    @functools.cached_property
    def free_variables(self) -> tuple[Variable, ...]:
        """Return free variables contained within."""
        return self.lhs.free_variables + self.rhs.free_variables

    @functools.cached_property
    def is_action_assertion(self) -> bool:
        """
        Determine whether this assertion is an action assertion.
        """
        return self.lhs.is_action_term or self.rhs.is_action_term

    def replace_variable(self, var_map: Mapping[Variable, Constant | CompoundTerm]) -> Assertion:
        """
        Return a grounded instance by replacing all Variables in the Assertion.

        :param var_map: Mapping[Variable, Constant | CompoundTerm] mapping Variables to Constants.
        :return: Grounded Assertion object.
        """
        if not self.free_variables:
            return self

        new_lhs: TERM_TYPE

        lhs = self.lhs
        if isinstance(lhs, Variable):
            new_lhs = var_map[lhs]
        elif type(lhs) is Constant:
            new_lhs = lhs
        else:
            new_lhs = lhs.replace_variable(var_map)

        new_rhs: TERM_TYPE

        rhs = self.rhs
        if isinstance(rhs, Variable):
            new_rhs = var_map[rhs]
        elif type(rhs) is Constant:
            new_rhs = rhs
        else:
            new_rhs = rhs.replace_variable(var_map)

        return type(self).from_parts(new_lhs, new_rhs)


class Intro(Assertion):
    """
    Syntactic sugar for X=X. In an unsafe rule, this assertion can indicate X is a free variable to match,
    making the rule safe. When generating facts, use Intro(term) to include a term in the fact base.
    """
    def __init__(self, term: TERM_TYPE) -> None:
        super().__init__(term, term)


class Formula:
    """Combination of multiple Assertions."""

    def __init__(self,
                 formula_left: FACT_TYPE,
                 connective: HashableAndStringable | Literal['AND', 'OR', 'NOT', 'IMPLIES', 'EQUAL'],
                 # XXX: HashableAndStringable corresponds to unsupported forall/exists for now.
                 formula_right: FACT_TYPE | None = None) -> None:
        """
        Logical formula composed of left/right sub-formulas or assertions and a connective.

        :param formula_left: Left term, Formula or Assertion.
        :param connective: Logical connective, e.g., "AND", "OR", "IMPLIES".
        :param formula_right: Right term, Formula, Assertion, or None for unary structure.

        :raises TypeError: Raised when formula_left is not Formula/Assertion,
                           or formula_right is not Formula/Assertion/None.

        """  # noqa: DOC501
        if not isinstance(formula_left, (Formula, Assertion)):
            raise TypeError('formula_left must be a Formula or Assertion')
        if not isinstance(formula_right, (Formula, Assertion)) and formula_right is not None:
            raise TypeError('formula_right must be a Formula or Assertion or None')

        self.formula_left = formula_left
        self.connective = str(connective)
        self.formula_right = formula_right

    @classmethod
    def from_parts(
        cls,
        formula_left: FACT_TYPE,
        connective: HashableAndStringable | Literal['AND', 'OR', 'NOT', 'IMPLIES', 'EQUAL'],
        formula_right: FACT_TYPE | None = None,
    ) -> Formula:
        """Trusted internal construction: skip __init__ type checks."""
        if _RUN_INIT_VALIDATION_IN_FROM_PARTS:
            return cls(formula_left, connective, formula_right)
        obj = object.__new__(cls)
        obj.formula_left = formula_left
        obj.connective = str(connective)
        obj.formula_right = formula_right
        return obj

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Formula):
            return False
        return (self.connective == other.connective and self.formula_left == other.formula_left
                and self.formula_right == other.formula_right)

    def __hash__(self) -> int:
        return hash((self.formula_left, self.connective, self.formula_right))

    def __str__(self) -> str:
        if self.connective == 'NOT':
            return f'NOT({self.formula_left})'
        return f'({self.formula_left}) {self.connective} ({self.formula_right})'

    @functools.cached_property
    def free_variables(self) -> tuple[Variable, ...]:
        """Return free variables contained within."""
        return (self.formula_left.free_variables + self.formula_right.free_variables) if self.formula_right is not None \
            else self.formula_left.free_variables

    def replace_variable(self, var_map: Mapping[Variable, Constant | CompoundTerm]) -> Formula:
        """Return a grounded instance for the current object."""
        if not self.free_variables:
            return self

        formula_left = self.formula_left
        new_formula_left = formula_left.replace_variable(var_map) if formula_left.free_variables else formula_left

        formula_right = self.formula_right
        new_formula_right = formula_right.replace_variable(var_map) if formula_right is not None and formula_right.free_variables else formula_right

        return type(self).from_parts(new_formula_left, connective=self.connective, formula_right=new_formula_right)


FACT_TYPE = Formula | Assertion


class Rule:
    """Logical rule a → b, where head is the conclusion and body is the premise, with priority and extensions."""

    def __init__(self,
                 head: FACT_TYPE | Sequence[FACT_TYPE],
                 body: FACT_TYPE | Sequence[FACT_TYPE],
                 priority: float = 0.0,
                 name: str = "",
                ) -> None:
        """
        Construct a Rule object expressing conclusions derived from premises.

        :param head: Rule conclusion, type FACT_TYPE.
        :param body: Rule premise, type FACT_TYPE.
        :param priority: Rule priority (float) for conflict resolution.

        :raises TypeError: Raised when:
                - head is not a FACT_TYPE instance
                - body is not a FACT_TYPE instance
                - priority is not a float or int
        :raises ValueError:
            - body is empty (rules must have at least one premise)
            - head is empty (rules must have at least one conclusion)
        """  # noqa: DOC501
        if not body:
            raise ValueError(
                "Rule body cannot be empty: a rule must have at least one premise. "
                "If you want to express a fact, simply add an Assertion instead of creating a Rule with an empty body."
            )
        if not head:
            raise ValueError(
                "Rule head cannot be empty: a rule must have at least one conclusion. "
                "KELE does not support constraint rules."
            )
        merged_head = self._standardize(head)
        merged_body = self._standardize(body)

        if not isinstance(priority, float) or not (0 <= float(priority) <= 1.0):
            raise TypeError('priority must be a float between 0 and 1')

        self.head = merged_head  # Splitting to smallest disjuncts may be better for fact storage and chaining, but
        # FACT_TYPE is more expressive than list[FACT_TYPE], so keep to_cnf_clauses as a property instead.
        self.body = merged_body  # body may include multiple facts but represents f1 AND f2; it should be a Formula.
        self.priority = priority
        self.name = name

        from ._cnf_converter import to_cnf_clauses  # noqa: PLC0415  # No better approach yet.
        from ._sat_solver import get_models_for_rule  # noqa: PLC0415
        self.to_cnf_clauses = to_cnf_clauses
        self._get_models_for_rule = get_models_for_rule

    @classmethod
    def from_parts(
        cls,
        head: FACT_TYPE | Sequence[FACT_TYPE],
        body: FACT_TYPE | Sequence[FACT_TYPE],
        *,
        priority: float = 0.0,
        name: str = "",
    ) -> Self:
        """Trusted internal construction: skip __init__ non-empty/standardize/priority checks."""
        if _RUN_INIT_VALIDATION_IN_FROM_PARTS:
            return cls(head, body, priority=priority, name=name)  # FIXME: Consider signature + __dict__ for extensibility.
        # Similar approaches elsewhere.
        obj = object.__new__(cls)
        obj.head = obj._standardize(head)  # noqa: SLF001
        obj.body = obj._standardize(body)  # noqa: SLF001
        obj.priority = priority
        obj.name = name

        # Dependency injection consistent with __init__ (avoid circular imports).
        from ._cnf_converter import to_cnf_clauses  # noqa: PLC0415
        from ._sat_solver import get_models_for_rule  # noqa: PLC0415
        obj.to_cnf_clauses = to_cnf_clauses
        obj._get_models_for_rule = get_models_for_rule  # noqa: SLF001
        return obj

    @functools.cached_property
    def free_variables(self) -> tuple[Variable, ...]:
        """Return free variables contained within."""
        return self.head.free_variables + self.body.free_variables  # TODO: If rules must be safe, add a helper.

    def replace_variable(self, var_map: Mapping[Variable, Constant | CompoundTerm]) -> Rule:
        """Return a grounded instance for the current object."""
        head = self.head
        new_head = head.replace_variable(var_map) if head.free_variables else head

        body = self.body
        new_body = body.replace_variable(var_map) if body.free_variables else body

        return type(self).from_parts(
            new_head,
            new_body,
            priority=self.priority,
            name=self.name,
        )

    def replace(self, **changes: Any) -> Self:  # noqa: ANN401
        # HACK: Once converted to a dataclass, replace can be used directly.
        """
        Create a new rule based on the current rule type, with partial attribute updates.

        :param changes: Attributes to update and their new values.
        :type changes: dict[str, Any]
        :raises ValueError: If changes contain attributes not present in the original rule.
        :return: New rule instance.
        :rtype: Rule | _QuestionRule
        """  # noqa: DOC501
        cls = self.__class__
        params = [
            n for n in inspect.signature(cls.__init__).parameters
            if n != "self"
        ]
        unknown = set(changes) - set(params)
        if unknown:
            raise ValueError(f"{cls.__name__}.__init__ does not accept: {sorted(unknown)}")

        data = {n: changes.get(n, getattr(self, n)) for n in params}

        return cls.from_parts(**data)

    def is_concept_compatible_binding(
        self,
        var: Variable | str,
        value: Constant | CompoundTerm[Constant | CompoundTerm],
        *,
        fuzzy_match: bool = True,
    ) -> bool:
        """Check Rule-level variable Concept constraints while binding var -> value in unify."""
        constraints = self._get_variable_concept_constraints(var)
        if not constraints:
            return True

        value_concepts = value.belong_concept if isinstance(value, Constant) else {value.operator.output_concept}

        return Concept.is_compatible(value_concepts, constraints, fuzzy_match=fuzzy_match)

    def __eq__(self, other: object) -> bool:  # We do not forbid duplicate rules; comparison isn't always syntactic.
        # e.g., p(x)=1→q(x)=1 and p(y)=1→q(y)=1. Leave equality to the user.
        if not isinstance(other, Rule):
            return False
        return self.head == other.head and self.body == other.body

    def __hash__(self) -> int:
        return hash((self.head, self.body, self.priority))

    def __str__(self) -> str:
        return f"{self.name}: {self.body} → {self.head} (priority: {self.priority})"

    def _get_unsafe_variables(self) -> set[Variable]:
        """
        Return unsafe variables in the rule.

        :param rule: Rule to inspect.
        :type rule: Rule
        :return: Unsafe variables in the rule.
        :rtype: set[Variable]
        """
        positive_non_action_assertion_vars: set[Variable] = set()
        action_assertion_vars: set[Variable] = set()
        negated_assertion_vars: set[Variable] = set()

        for assertion, sat_result in self.get_models.items():
            if sat_result[0] and not assertion.is_action_assertion:
                # Only positive literals from non-action assertions contribute to real_grounding_variables.
                # IMPORTANT: positive_non_action_assertion_vars does not include all grounding variables.
                # Variables in action assertions (not in action terms) also ground, but are not included here.
                positive_non_action_assertion_vars.update(assertion.free_variables)

        for assertion, sat_result in self.get_models.items():
            if sat_result[0]:
                for term in (assertion.lhs, assertion.rhs):
                    if term.is_action_term:
                        action_assertion_vars.update(set(term.free_variables))
            elif sat_result[1]:
                # Free variables in negated literals must appear in real_grounding_variables.
                negated_assertion_vars.update(set(assertion.free_variables))

        return (set(self.head.free_variables) | negated_assertion_vars | action_assertion_vars) - positive_non_action_assertion_vars

    @functools.cached_property
    def head_units(self) -> list[FACT_TYPE]:
        """Return minimal disjunctive units of head. XXX: Not guaranteed minimal yet."""
        return self.to_cnf_clauses(self.head)

    @functools.cached_property
    def body_units(self) -> list[FACT_TYPE]:
        """Return minimal disjunctive units of body. XXX: Not guaranteed minimal yet."""
        return self.to_cnf_clauses(self.body)

    @functools.cached_property
    def unsafe_variables(self) -> set[Variable]:
        """Return unsafe variables in the rule."""
        return self._get_unsafe_variables()

    @staticmethod
    def _standardize(body_or_head: FACT_TYPE | Sequence[FACT_TYPE]) -> FACT_TYPE:
        if isinstance(body_or_head, FACT_TYPE):
            merged = body_or_head
        elif isinstance(body_or_head, Sequence) and all(isinstance(f, FACT_TYPE) for f in body_or_head):
            merged = functools.reduce(lambda x, y: Formula(x, 'AND', y), body_or_head)
        else:
            raise TypeError('body_or_head must be FACT_TYPE (Formula | Assertion)')

        return merged

    @functools.cached_property
    def get_models(self) -> dict[Assertion, list[bool]]:
        """
        For a Rule, find all possible models from a Boolean logic perspective,
        and analyze assignments to determine whether each assertion can be True or False.
        :return: Dict indicating whether each assertion can be T/F.
        """
        return self._get_models_for_rule(self)

    # ----------------------- Concept constraint collection and validation -----------------------

    @functools.cached_property
    def _variable_concept_constraints(self) -> dict[str, set[Concept]]:
        """Collect and validate Concept constraints for same-named variables in the Rule."""
        return self._validate_concepts_in_rule()

    @staticmethod
    def _iter_assertions(fact: FACT_TYPE) -> list[Assertion]:
        """Recursively expand Formula and collect all Assertions."""
        if isinstance(fact, Assertion):
            return [fact]
        # Formula
        left = Rule._iter_assertions(fact.formula_left)
        if fact.formula_right is None:
            return left
        return left + Rule._iter_assertions(fact.formula_right)

    @staticmethod
    def _collect_var_constraints_from_term(
            term: TERM_TYPE,
            expected_concept: Concept | None,
            out: dict[str, set[Concept]],
    ) -> None:
        """Recursively collect variable Concept constraints from a term.

        - When Variable appears in operator argument i, that argument's Concept constrains the Variable.
        - expected_concept is None when the context has no direct Concept constraint.
        """
        if isinstance(term, Variable):
            if expected_concept is not None:
                out[term.name].add(expected_concept)
            return
        if isinstance(term, Constant):
            return
        # CompoundTerm
        for arg, exp_c in zip(term.arguments, term.operator.input_concepts, strict=False):
            Rule._collect_var_constraints_from_term(arg, exp_c, out)

    @staticmethod
    def _union_find_build(links: list[tuple[str, str]]) -> dict[str, str]:
        """Build a union-find parent map from equality constraints of the form (a, b)."""
        parent: dict[str, str] = {}

        def find(x: str) -> str:
            parent.setdefault(x, x)
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for a, b in links:
            union(a, b)

        # Path compression.
        for k in list(parent.keys()):
            parent[k] = find(k)
        return parent

    def _validate_concepts_in_rule(self) -> dict[str, set[Concept]]:
        """Compute Rule-level Concept constraints.

        1) Record Concept constraints for same-named variables from different positions (list indicates multiple constraints).
        2) TODO: Validate satisfiability of constraints based on mode (strict/loose).
        """
        assertions = self._iter_assertions(self.body) + self._iter_assertions(self.head)
        # TODO: Potential optimization: compute head/body separately. If head constraints are absent in body,
        # warn about potential conflicts. For now, just record combined constraints.

        # 1) Collect: constraints from operator argument positions; and variable/term constraints in a=b.
        var_constraints: dict[str, set[Concept]] = defaultdict(set)  # Variables may have multiple same-name instances.
        equal_links: list[tuple[str, str]] = []

        for a in assertions:
            # Same-name variables are equivalent in a = b (var1 = var2).
            if isinstance(a.lhs, Variable) and isinstance(a.rhs, Variable):
                equal_links.append((a.lhs.name, a.rhs.name))

            # Collect operator-level concept constraints.
            self._collect_var_constraints_from_term(a.lhs, expected_concept=None, out=var_constraints)
            self._collect_var_constraints_from_term(a.rhs, expected_concept=None, out=var_constraints)

            # Equality constraints: Variable vs. output concepts on the opposite term.
            if isinstance(a.lhs, Variable):
                var_constraints[a.lhs.name] |= _term_possible_concepts(a.rhs)
            if isinstance(a.rhs, Variable):
                var_constraints[a.rhs.name] |= _term_possible_concepts(a.lhs)

        # 2) Merge: union constraints for var1=var2 equivalence classes.
        parent = self._union_find_build(equal_links)

        merged: dict[str, set[Concept]] = defaultdict(set)
        for var_name, concepts in var_constraints.items():
            root = parent.get(var_name, var_name)
            merged[root] |= concepts

        # NOTE:
        # - `merged` uses only the root variable name as key, so non-root vars cannot query constraints in unify.
        # - Grounder/Unify uses Variable.name (renamed to unique _vK in RuleBase), so use Variable.name as key,
        #   not display_name.
        merged_by_root = merged

        # Expand merged constraints to each variable name (including non-root names) for faster lookup.
        expanded: dict[str, set[Concept]] = defaultdict(set)
        all_var_names = set(var_constraints.keys()) | set(parent.keys())
        for var_name in all_var_names:
            root = parent.get(var_name, var_name)
            expanded[var_name] |= merged_by_root.get(root, set())

        # TODO: Add a more detailed third validation step.
        # For example, if X is constrained by A∩B, require a declared concept C that belongs to both (strict),
        # or allow the engine to create one (loose).

        return expanded

    # ----------------------- Concept constraint access and checks -----------------------

    def _get_variable_concept_constraints(self, var: Variable | str) -> set[Concept]:
        """Get Concept constraints for a variable name (Variable.name).

        IMPORTANT:
        - Always use Variable.name as the key inside the engine (RuleBase renames to `_vK`); do not use `str(var)` (display_name).
        - Return empty set if the variable has no constraints.
        """
        key = var.name if isinstance(var, Variable) else str(var)
        return self._variable_concept_constraints.get(key, set())


class Question:
    """Problem to solve, including premises and variable-containing queries related to the problem description."""

    def __init__(self, premises: Sequence[FACT_TYPE] | FACT_TYPE, question: Sequence[FACT_TYPE]) -> None:
        """
        Construct a Question object with relevant premises and target formulas containing variables.

        :param premises: Premises related to the question. FACT_TYPE or list of FACT_TYPE.
                         If a single Assertion or Formula is provided, it is wrapped into a list.
        :param question: Query items to solve, as FACT_TYPE or list of FACT_TYPE.

        :raises TypeError:
                - Raised when premises is not a list or valid Assertion/Formula.
                - Raised when question is not a list or valid Assertion/Formula.
        """  # noqa: DOC501
        if not isinstance(premises, Sequence):
            if isinstance(premises, (Assertion, Formula)):
                premises = [premises]
            else:
                raise TypeError('premises must be a list of FACT_TYPE')

        if not isinstance(question, Sequence) or not all(isinstance(q, FACT_TYPE) for q in question):
            raise TypeError('question must be a list of FACT_TYPE')

        self.premises = premises
        self.question = question

    @property
    def description(self) -> str:
        """Build a natural-language description combining premises and question."""
        question_str = ','.join(str(q) for q in self.question)
        return (f'Question : {question_str},\nincluding {len(self.premises)} premises '
                f'and {len(self.question)} target facts.')

    def __str__(self) -> str:
        return (f'Premises: {self.premises}\n'
                f'Question: {','.join(str(q) for q in self.question)}')

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Question):
            return False
        return self.question == other.question and self.premises == other.premises

    def __hash__(self) -> int:
        return hash((tuple(self.premises), tuple(self.question)))


class AtomCompoundTerm(CompoundTerm):
    """recursively defined to be a constant, or a variable, or an n-ary operator whose arguments are atom terms."""
    # atomize/atom keywords are scoped to this class. Also note: Variables are treated as free variables,
    # but introducing predicates adds complications, so isinstance(xxx, Variable) is not sufficient.

    def __init__(self, operator: Operator, arguments: Sequence[Constant | Variable]) -> None:
        super().__init__(operator, arguments)
        self.arguments: tuple[Constant | Variable, ...]

    def __str__(self) -> str:
        return f'{self.operator.name}({", ".join(str(u) for u in self.arguments)})'

    @classmethod
    def from_parts(cls, operator: Operator, arguments: Sequence[TERM_TYPE]) -> AtomCompoundTerm:
        """Lightweight construction: skip __init__ checks for trusted internal use (e.g., replace_variable)."""
        if TYPE_CHECKING:
            arguments = cast("Sequence[Constant | Variable]",
                             arguments)  # AtomCompoundTerm arguments are Constant | Variable.
        # But the types are still hard to annotate precisely.

        if _RUN_INIT_VALIDATION_IN_FROM_PARTS:
            return cls(operator, arguments)

        obj = object.__new__(cls)
        obj.operator = operator
        obj.arguments = tuple(arguments)
        return obj


ATOMTERM_TYPE = Constant | AtomCompoundTerm | Variable  # risk: concept | operator are terms too, but not handled yet.
ATOM_TYPE = Constant | Variable
ATOM_GROUNDED_TYPE = Constant | AtomCompoundTerm  # HACK: Strictly, AtomCompoundTerm should be variable-free.
GROUNDED_TYPE_FOR_UNIFICATION = TERM_TYPE  # risk: Consider whether term selector uses TERM_TYPE or ATOM_GROUNDED_TYPE.


# This alias may change; we use a special alias for now. We still prefer TERM_TYPE for two reasons:
# 1) Equality axioms operate on assertions or their related terms, not on nested terms (atom-level).
# 2) Equivalence classes do not yet support FREEANY; op(1, op2(2)) records itself, not op(1, FREE).
# Restricting to atoms would impact equivalence class extraction.

# ============= Gradually provide factory/helper functions to simplify writing and move toward frozen =============

# Variable entry
class VariableFactory:
    """Factory for Variable instances. Use vf.x or vf['x'] to create instances (same name still creates new instances)."""
    def __getattr__(self, name: HashableAndStringable) -> Variable:
        return Variable(name)

    def __getitem__(self, item: HashableAndStringable) -> Variable:
        return Variable(item)


vf = VariableFactory()


# ===========================Internal Class=====================================

class _QuestionRule(Rule):
    """
    Internal Rule subclass used to carry Question variable mapping information.
    """
    QUESTION_SOLVED_FLAG = Constant('QUESTION_SOLVED_FLAG', Concept("Bool"))  # Marks whether the question is solved.
    QUESTIONRULE_NAME = "QUESTION_RULE"

    def __init__(self, head: FACT_TYPE | Sequence[FACT_TYPE], body: FACT_TYPE | Sequence[FACT_TYPE],
                 priority: float = 0.0, name: str | None = None):
        self.name = name if name is not None else self.QUESTIONRULE_NAME
        super().__init__(head, body, priority=priority, name=self.name)
