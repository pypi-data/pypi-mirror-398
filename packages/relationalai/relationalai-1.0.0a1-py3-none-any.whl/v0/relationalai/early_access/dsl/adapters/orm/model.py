from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

@dataclass
class ORMEntityType:
    id: str
    name: str
    ref_mode: Optional[str]


@dataclass
class ORMValueType:
    id: str
    name: str
    data_type: str


@dataclass
class ORMRole:
    id: str
    name: str
    relationship_name: str
    player: str


@dataclass
class ORMSubtypeFact:
    subtype_role_id: Optional[str]
    subtype: Optional[str]
    supertype_role_id: Optional[str]
    supertype: Optional[str]


@dataclass
class SubtypeFact:
    subtype_name: str
    supertype_name: str


@dataclass
class ExclusiveSubtypeFact(SubtypeFact):
    pass

@dataclass
class InclusiveSubtypeFact(SubtypeFact):
    pass

@dataclass
class ExclusiveInclusiveSubtypeFact(SubtypeFact):
    pass


@dataclass
class ORMUniquenessConstraint:
    id: str
    roles: list[str]
    identifies: Optional[str]


@dataclass
class ORMMandatoryConstraint:
    id: str
    roles: list[str]


class ORMValueComparisonOperator(Enum):
    GREATER_THAN_OR_EQUAL = 'GreaterThanOrEqual'
    LESS_THAN_OR_EQUAL = 'LessThanOrEqual'
    GREATER_THAN = 'GreaterThan'
    LESS_THAN = 'LessThan'
    NOT_EQUAL = 'NotEqual'
    EQUAL = 'Equal'


@dataclass
class ORMValueComparisonConstraint:
    id: str
    operator: ORMValueComparisonOperator
    roles: list[str]


@dataclass
class ORMRoleSubsetConstraint:
    id: str
    roles: list[list[str]]


@dataclass
class ORMRingConstraint:
    id: str
    roles: list[str]
    ring_types: list[ORMRingType]


class ORMRingType(Enum):
    IRREFLEXIVE = 'Irreflexive'
    ANTISYMMETRIC = 'Antisymmetric'
    ASYMMETRIC = 'Asymmetric'
    STRONGLY_INTRANSITIVE = 'StronglyIntransitive'
    INTRANSITIVE = 'Intransitive'
    ACYCLIC = 'Acyclic'
    PURELY_REFLEXIVE = 'PurelyReflexive'
    REFLEXIVE = 'Reflexive'
    SYMMETRIC = 'Symmetric'
    TRANSITIVE = 'Transitive'


@dataclass
class ORMExclusionConstraint:
    id: str
    roles: list[list[str]]
    inclusive: bool


@dataclass
class ORMInclusionConstraint:
    id: str
    roles: list[str]
    exclusive: bool


@dataclass
class ORMReading:
    front_text: Optional[str]
    roles: list[ORMReadingRole]


@dataclass
class ORMReadingRole:
    index: int
    prefix: Optional[str]
    postfix: Optional[str]
    text: Optional[str]
    role: Optional[ORMRole]


@dataclass
class ORMRoleValueConstraint:
    role: ORMRole
    values: list[Union[str, ORMRange]]


@dataclass
class ORMInclusiveRoleConstraint:
    id: str
    roles: list[str]


@dataclass
class ORMExclusiveRoleConstraint:
    id: str
    roles: list[list[str]]


@dataclass
class ORMEqualityConstraint:
    id: str
    roles: list[list[str]]


@dataclass
class ORMFrequencyConstraint:
    id: str
    min_frequency: int
    max_frequency: int
    roles: list[str]


@dataclass
class ORMRange:
    range_from: str
    range_to: str


@dataclass
class ORMCardinalityConstraint:
    id: str
    object_type: str
    ranges: list[ORMRange]


@dataclass
class ORMRoleCardinalityConstraint:
    id: str
    role: str
    ranges: list[ORMRange]

@dataclass
class ORMValueTypeValueConstraint:
    id: str
    value_type: str
    ranges: list[ORMRange]
