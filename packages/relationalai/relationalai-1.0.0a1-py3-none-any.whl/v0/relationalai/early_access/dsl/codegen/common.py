from v0.relationalai.early_access.dsl.bindings.common import Binding, BindableTable
from v0.relationalai.early_access.dsl.orm.constraints import Unique
from v0.relationalai.early_access.dsl.orm.relationships import Relationship, Role
from v0.relationalai.early_access.dsl.orm.types import Concept


class BoundRelationship:
    _relationship: Relationship
    _table: BindableTable
    _bindings: list[Binding]

    def __init__(self, relationship: Relationship, table: BindableTable):
        self._relationship = relationship
        self._table = table
        self._bindings = []

    def __hash__(self):
        # hash based on the relationship and the table
        return hash((self._relationship, self._table))

    def __eq__(self, other):
        if not isinstance(other, BoundRelationship):
            return False
        return self._relationship == other._relationship and self._table == other._table

    @property
    def relationship(self):
        return self._relationship

    @property
    def table(self):
        return self._table

    @property
    def bindings(self):
        return self._bindings

class BoundIdentifierConstraint:
    _constraint: Unique
    _table: BindableTable
    _role_bindings: dict[Role, Binding]
    _concept: Concept

    def __init__(self, constraint: Unique, table: BindableTable, role_bindings: dict[Role, Binding]):
        self._constraint = constraint
        self._table = table
        self._role_bindings = role_bindings
        self._lookup_value_concept(constraint)

    def _lookup_value_concept(self, constraint):
        # concept if the sibling player of an arbitrary role (all should have the same) in the constraint
        first_role = constraint.roles()[0]
        sibling_role = first_role.sibling()
        if sibling_role is None:
            raise ValueError('Roles in external UCs must be part of binary relationships')
        self._concept = sibling_role.player()

    def __hash__(self):
        # hash based on the constraint and the table
        return hash((self._constraint, self._table))

    @property
    def constraint(self):
        return self._constraint

    @property
    def table(self):
        return self._table

    @property
    def role_bindings(self):
        return self._role_bindings

    @property
    def concept(self):
        return self._concept

    def is_external(self):
        return len(self._role_bindings) > 1
