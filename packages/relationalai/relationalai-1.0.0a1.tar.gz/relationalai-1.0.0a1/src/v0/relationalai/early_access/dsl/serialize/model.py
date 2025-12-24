# type: ignore
import dataclasses
from typing import Optional

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class ValueType:
    id: str
    name: str
    data_type: str
    data_type_name: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class EntityType:
    id: str
    name: str
    domain: list[str] = dataclasses.field(default_factory=list)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class UniqueConstraint:
    id: str
    roles: list[str]
    is_preferred_identifier: bool


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class MandatoryConstraint:
    id: str
    roles: list[str]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Role:
    id: str
    role_player: str
    role_player_name: str
    name: Optional[str] = None
    pre_bound_text: Optional[str] = None
    post_bound_text: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Reading:
    id: str
    text: str
    roles: list[str]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class DataType:
    id: str
    name: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Constraints:
    uniqueness: list[UniqueConstraint]
    mandatory: list[MandatoryConstraint]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Relationship:
    id: str
    name: str
    roles: list[Role]
    readings: list[Reading] = dataclasses.field(default_factory=list)
    is_subtype: bool = False


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Concepts:
    value_types: list[ValueType]
    entity_types: list[EntityType]

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class SubtypeArrow:
    id: str
    start: str
    start_name: str
    end: str
    end_name: str

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Model:
    id: str
    name: str
    is_primary: bool
    concepts: Concepts
    relationships: list[Relationship]
    constraints: Constraints
    data_types: list[DataType]
    subtype_arrows: list[SubtypeArrow]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class ModelObject:
    model: Model
