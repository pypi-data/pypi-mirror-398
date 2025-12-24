from abc import ABC, abstractmethod
from enum import Enum
from typing import Sequence, Optional, TypeVar, Generic, Union
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid
from v0.relationalai.early_access.dsl.orm.relationships import Role
from v0.relationalai.early_access.dsl.orm.types import Concept


class Constraint(ABC):
    @abstractmethod
    def _validate(self, ontology) -> bool:
        """Validate the constraint against the ontology."""

    @abstractmethod
    def _unique_name(self) -> str:
        """Validate the constraint against the ontology."""

    @abstractmethod
    def _desugar(self):
        """Declare QB constraints"""

    def _guid(self):
        return generate_stable_uuid(self._unique_name())

    def __eq__(self, other):
        if isinstance(other, Constraint):
            return self._guid() == other._guid()
        return False

    def __hash__(self):
        return hash(self._guid())

class ConceptConstraint(Constraint):

    def concept(self) -> Concept:
        return self._concept

    def __init__(self, concept: Concept):
        self._concept = concept
        self._name = f'{type(self).__name__}{concept._guid()}'

    def _unique_name(self) -> str:
        return self._name

class RoleConstraint(Constraint):

    def roles(self) -> list[Role]:
        return self._roles

    def __init__(self, roles: list[Role]):
        self._roles = roles
        self._name = f'{type(self).__name__}{"".join(role._guid() for role in self._roles)}'

    def _unique_name(self) -> str:
        return self._name

    def _discharged(self) -> bool:
        return False

class RoleSequenceConstraint(Constraint):
    def role_sequences(self):
        return self._role_sequences

    def __init__(self, role_sequences):
        if all(isinstance(item, list) for item in role_sequences):
            self._role_sequences = role_sequences
        elif all(not isinstance(item, list) for item in role_sequences):
            self._role_sequences = [[item] for item in role_sequences]
        else:
            raise TypeError("All items in role_sequences must be either all lists or all non-lists")

        self._name = f'{type(self).__name__}{"".join(role._guid() for role_list in self._role_sequences for role in role_list)}'

    def _unique_name(self) -> str:
        return self._name

class Unique(RoleConstraint):
    def __init__(self, *roles: Role, is_preferred_identifier=False):
        super().__init__(list(roles))
        self.is_preferred_identifier = is_preferred_identifier

    def _validate(self, ontology) -> bool:
        # Implement uniqueness validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def _is_internal(self) -> bool:
        # only when there is a single role
        return len(self._roles) == 1

    def __repr__(self):
        return f'Unique(({", ".join(role._guid() for role in self._roles)}), preferred_identifier={self.is_preferred_identifier})'


class Mandatory(RoleConstraint):
    def __init__(self, role: Role):
        super().__init__([role])

    def _validate(self, ontology) -> bool:
        # Implement mandatory validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'Mandatory({self._roles[0]._guid()})'


class InclusiveRoleConstraint(RoleConstraint):
    def __init__(self, *roles: Role):
        super().__init__(list(roles))

    def _validate(self, ontology) -> bool:
        # Implement inclusive validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'InclusiveRoles(({", ".join(role._guid() for role in self._roles)})'


class ExclusiveRoleConstraint(RoleSequenceConstraint):
    def __init__(self, *role_sequences):
        super().__init__(list(role_sequences))

    def _validate(self, ontology) -> bool:
        # Implement exclusive validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'ExclusiveRoles([{"], [".join(", ".join(ro._guid()) for ro_list in self.role_sequences() for ro in ro_list)}])'


class RingType(Enum):
    IRREFLEXIVE = 1
    ANTISYMMETRIC = 2
    ASYMMETRIC = 3
    STRONGLY_INTRANSITIVE = 4
    INTRANSITIVE = 5
    ACYCLIC = 6
    PURELY_REFLEXIVE = 7
    REFLEXIVE = 8
    SYMMETRIC = 9
    TRANSITIVE = 10


class RingConstraint(RoleConstraint):
    def __init__(self, constraint_types: list[RingType], *roles: Role):
        super().__init__(list(roles))
        self.types = constraint_types

    def _validate(self, ontology) -> bool:
        # Implement ring constraint logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'Ring(({", ".join(str(type) for type in self.types)}), ({", ".join(role._guid() for role in self._roles)}))'


class ValueComparisonType(Enum):
    GREATER_THAN_OR_EQUAL = 1
    LESS_THAN_OR_EQUAL = 2
    GREATER_THAN = 3
    LESS_THAN = 4
    NOT_EQUAL = 5
    EQUAL = 6


class ValueComparisonConstraint(RoleConstraint):
    def __init__(self, constraint_type: ValueComparisonType, *roles: Role):
        super().__init__(list(roles))
        self.type = constraint_type

    def _validate(self, ontology) -> bool:
        # Implement value comparison constraint logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'ValueComparison({self.type}, ({", ".join(role._guid() for role in self._roles)}))'


class RoleSubsetConstraint(RoleSequenceConstraint):
    def __init__(self, *role_sequences):
        super().__init__(list(role_sequences))

    def _validate(self, ontology) -> bool:
        # Implement role subset validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'RoleSubsets([{"], [".join(", ".join(ro._guid()) for ro_list in self.role_sequences() for ro in ro_list)}])'


class EqualityConstraint(RoleSequenceConstraint):
    def __init__(self, *role_sequences):
        super().__init__(list(role_sequences))

    def _validate(self, ontology) -> bool:
        # Implement equality validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'Equality([{"], [".join(", ".join(ro._guid()) for ro_list in self.role_sequences() for ro in ro_list)}])'


class FrequencyConstraint(RoleConstraint):
    def __init__(self, constraint_frequency: tuple, *roles: Role):
        super().__init__(list(roles))
        self.frequency = constraint_frequency

    def _validate(self, ontology) -> bool:
        # Implement frequency constraint logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'Frequency(({", ".join(str(freq) for freq in self.frequency)}), ({", ".join(role._guid() for role in self._roles)}))'


# Role value constraint
T = TypeVar('T', int, float, str)


class Range(Generic[T]):

    def __init__(self, start: Optional[T], end: Optional[T]):
        if start is None and end is None:
            raise ValueError("'start' and 'end' cannot be None")
        if start is not None and end is not None:
            if type(start) is not type(end):
                raise TypeError("'start' and 'end' must be of same type")
            if start > end:  # type: ignore[reportOperatorIssue]
                raise ValueError("'start' must be less than 'end'")
        self._start = start
        self._end = end

    def _matches(self, value: T) -> bool:
        if self._start is not None and value < self._start:
            return False
        if self._end is not None and value > self._end:
            return False
        return True

    def _type(self):
        if self._start is not None:
            return type(self._start)
        else:
            return type(self._end)

    def __repr__(self):
        return f"Range({self._start}, {self._end})"

    @staticmethod
    def between(start: T, end: T):
        return Range(start, end)

    @staticmethod
    def to_value(value: T):
        return Range(None, value)

    @staticmethod
    def from_value(value: T):
        return Range(value, None)


class RoleValueConstraint(RoleConstraint, Generic[T]):
    def __init__(self, role: Role, values: Sequence[Union[T, Range[T]]]):
        super().__init__([role])
        self._values = values

    def values(self):
        return self._values

    def _validate(self, ontology) -> bool:
        # Implement role value validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'RoleValueConstraint({self._roles[0]._guid()}, values={self._values})'

    def _discharged(self) -> bool:
        # TODO: Implement logic to determine if the constraint is discharged when a unified reasoner is available
        # See RAI-40577
        return False


class RoleCardinalityConstraint(RoleConstraint):
    def __init__(self, role: Role, values: Sequence[Union[int, Range[int]]]):
        if len(role._relationship._fields) > 1:
            raise ValueError("Role cardinality constraints can only be applied to unary relationships roles.")
        super().__init__([role])
        self._values = values

    def values(self):
        return self._values

    def _validate(self, ontology) -> bool:
        # Implement role cardinality validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'RoleCardinalityConstraint({self._roles[0]._guid()}, values={self._values})'

class CardinalityConstraint(ConceptConstraint, Generic[T]):
    def __init__(self, concept: Concept, values: Sequence[Union[int, Range[int]]]):
        super().__init__(concept)
        self._values = values

    def values(self):
        return self._values

    def _validate(self, ontology) -> bool:
        # TODO
        # Implement concept cardinality validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'CardinalityConstraint({self._concept._name}, values={self._values})'


class ValueConstraint(ConceptConstraint, Generic[T]):
    def __init__(self, concept: Concept, values: Sequence[Union[T, Range[T]]]):
        super().__init__(concept)
        self._values = values

    def values(self):
        return self._values

    def _validate(self, ontology) -> bool:
        # TODO
        # Implement value type constraint validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass

    def __repr__(self):
        return f'ValueConstraint({self._concept._name}, values={self._values})'

class SubtypeConstraint(Constraint):
    _concepts: dict[str, Concept]

    def __init__(self, *concepts: Concept):
        self._concepts = {}
        for concept in concepts:
            self._concepts[concept._name] = concept
        if len(concepts) < 2:
            raise ValueError("Invalid subtype constraint. A constraint should hold at least 2 concepts")
        first = next(iter(self._concepts.values()))
        first_super_types = [super_type._id for super_type in first._extends]
        for c in self._concepts.values():
            if len(c._extends) == 0:
                raise ValueError(f"Invalid subtype constraint. '{c}' is not a subtype")
            c_super_types = [super_type._id for super_type in c._extends]
            if first_super_types != c_super_types:
                raise ValueError(f"Invalid subtype constraint. '{first}' and '{c}' must have the same parents")
        self._name = f'{type(self).__name__}({", ".join(str(c) for c in sorted(self._concepts.values(), key=lambda c: str(c)))})'

    def _unique_name(self) -> str:
        return self._name

    def concepts(self) -> dict[str, Concept]:
        return self._concepts

    def __repr__(self):
        return self._name


class ExclusiveSubtypeConstraint(SubtypeConstraint):

    def __init__(self, *concepts: Concept):
        super().__init__(*concepts)

    def _validate(self, ontology) -> bool:
        # Implement validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass


class InclusiveSubtypeConstraint(SubtypeConstraint):

    def __init__(self, *concepts: Concept):
        super().__init__(*concepts)

    def _validate(self, ontology) -> bool:
        # Implement validation logic here
        return True

    def _desugar(self):
        # todo: Implement QB representation
        pass
