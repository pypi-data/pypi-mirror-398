from abc import ABC, abstractmethod
from typing import List

from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid
from v0.relationalai.early_access.dsl.ontologies.roles import AbstractRole


class Constraint(ABC):
    @abstractmethod
    def validate(self, ontology) -> bool:
        """Validate the constraint against the ontology."""

    @abstractmethod
    def _unique_name(self) -> str:
        """Validate the constraint against the ontology."""

    @abstractmethod
    def roles(self) -> list[AbstractRole]:
        """Return the roles of the constraint."""

    def guid(self):
        return generate_stable_uuid(self._unique_name())

    def __eq__(self, other):
        if isinstance(other, Constraint):
            return self.guid() == other.guid()
        return False

    def __hash__(self):
        return hash(self.guid())


class Unique(Constraint):
    def __init__(self, *roles, is_preferred_identifier=False):
        self._roles = list(roles)
        self.is_preferred_identifier = is_preferred_identifier

    def roles(self):
        return self._roles

    def validate(self, ontology) -> bool:
        # Implement uniqueness validation logic here
        return True

    def _unique_name(self) -> str:
        return f'Unique{"".join(role.guid() for role in self._roles)}'

    def __repr__(self):
        return f'Unique(({", ".join(role.ref_name() for role in self._roles)}), preferred_identifier={self.is_preferred_identifier})'

class Mandatory(Constraint):
    def __init__(self, role: AbstractRole):
        self.role = role

    def roles(self):
        return [self.role]

    def validate(self, ontology) -> bool:
        return True

    def _unique_name(self) -> str:
        return f'Mandatory{self.role.guid()}'

    def __repr__(self):
        return f'Mandatory({self.role.ref_name()})'

class RoleValueConstraint(Constraint):
    def __init__(self, role: AbstractRole, values: List[str]):
        self._role = role
        self._values = values

    def roles(self):
        return [self._role]

    def values(self):
        return self._values

    def validate(self, ontology) -> bool:
        return True

    def _unique_name(self) -> str:
        return f'RoleValueConstraint{self._role.guid()}'

    def role(self):
        return self._role

    def __repr__(self):
        return f'RoleValueConstraint({self._role.ref_name()}, values={self._values})'
