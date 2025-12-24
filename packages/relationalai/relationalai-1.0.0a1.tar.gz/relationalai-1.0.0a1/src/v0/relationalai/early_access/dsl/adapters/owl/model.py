from dataclasses import dataclass
from typing import Optional


@dataclass
class OWLClass:
    name: str
    parents: Optional[set[str]] = None
    children: Optional[set[str]] = None
    partition: Optional[set[str]] = None
    disjoint: Optional[set[str]] = None
    mandatory_properties: Optional[set[str]] = None
    inverse_mandatory_properties: Optional[set[str]] = None


@dataclass
class OWLObjectProperty:
    name: str
    domain: list[str]
    range: list[str]
    inverse_property: Optional[str] = None
    functional: Optional[bool] = False
    inverse_functional: Optional[bool] = False


@dataclass
class OWLDatatypeProperty:
    name: str
    domain: list[str]
    range: list[type]
    functional: Optional[bool] = False
