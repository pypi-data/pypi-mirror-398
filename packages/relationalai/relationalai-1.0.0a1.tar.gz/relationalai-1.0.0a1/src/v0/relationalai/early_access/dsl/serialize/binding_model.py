# type: ignore
import dataclasses
from typing import Optional

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class BoundRole:
    relationship: str
    player: str
    entityMapRef: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class BoundAttribute:
    name: str
    source: str
    hasValue: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class DataTransformerApplication:
    transformer: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class BindingObject:
    id: str
    attribute: Optional[BoundAttribute]
    role: BoundRole
    transformations: list[DataTransformerApplication] = dataclasses.field(default_factory=list)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class DataTransformer:
    name: str
    sourceType: str
    targetType: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class Pattern:
    conceptName: str
    pattern: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class EntityMapRef:
    name: str
    source: str
    entityType: str
    relation: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclasses.dataclass
class BindingModelObject:
    bindings: list[BindingObject] = dataclasses.field(default_factory=list)
    patterns: list[Pattern] = dataclasses.field(default_factory=list)
    dataTransformers: list[DataTransformer] = dataclasses.field(default_factory=list)
    entityMaps: list[EntityMapRef] = dataclasses.field(default_factory=list)
