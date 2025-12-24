from typing import Union

from v0.relationalai.early_access.dsl.bindings.common import Binding, IdentifierConceptBinding, RoleBinding, \
    SubtypeConceptBinding, BindableTable, BindableAttribute, ReferentConceptBinding
from v0.relationalai.early_access.dsl.codegen.common import BoundIdentifierConstraint, BoundRelationship
from v0.relationalai.early_access.dsl.orm.relationships import Role, Relationship
from v0.relationalai.semantics.metamodel.util import OrderedSet

import v0.relationalai.semantics as qb

class Binder:
    def __init__(self, model):
        self._model = model
        self._reasoner = self._model.reasoner()

        # bindings classification
        self._identifier_bindings: OrderedSet[IdentifierConceptBinding] = OrderedSet()
        self._subtype_bindings: OrderedSet[Union[IdentifierConceptBinding, ReferentConceptBinding]] = OrderedSet()
        self._subtype_concept_bindings: OrderedSet[SubtypeConceptBinding] = OrderedSet()
        self._referent_concept_bindings: OrderedSet[ReferentConceptBinding] = OrderedSet()
        self._value_type_bindings: OrderedSet[Binding] = OrderedSet()
        self._entity_type_bindings: OrderedSet[Binding] = OrderedSet()
        self._role_bindings: dict[Role, OrderedSet[Binding]] = {}
        self._bound_identifier_constraints = OrderedSet[BoundIdentifierConstraint]()
        self._bound_relationships = OrderedSet[BoundRelationship]()

        self._analyze()

    def value_type_bindings(self) -> OrderedSet[Binding]:
        """
        Returns the value type bindings.
        """
        return self._value_type_bindings

    def is_value_type_binding(self, binding: Binding) -> bool:
        """
        Returns True if the binding is a value type binding.
        """
        return binding in self._value_type_bindings

    def constructor_bindings(self) -> OrderedSet[IdentifierConceptBinding]:
        """
        Returns the identifier bindings that construct entity types.
        """
        return self._identifier_bindings

    def is_constructor_binding(self, binding: Binding) -> bool:
        """
        Returns True if the binding is an IdentifierBinding.
        """
        return isinstance(binding, IdentifierConceptBinding) and binding in self._identifier_bindings

    @staticmethod
    def is_filtering_binding(binding: Binding) -> bool:
        """
        Returns True if the binding is a SubtypeConceptBinding or has filter_by.
        """
        return isinstance(binding, SubtypeConceptBinding) or binding.filter_by is not None

    def subtype_ctor_bindings(self) -> OrderedSet[Union[IdentifierConceptBinding, ReferentConceptBinding]]:
        """
        Returns the identifier or referent subtype bindings. Those are only possible for subtypes that define
        their own reference scheme.

        They are different from SubtypeConceptBinding, which is a subtype binding with a filter.
        """
        return self._subtype_bindings

    def subtype_filtering_bindings(self) -> OrderedSet[SubtypeConceptBinding]:
        """
        Returns the subtype concept bindings. These are bindings that are used to derive subtypes from a parent type,
        and they are different from IdentifierConceptBinding or ReferentConceptBinding, which are used to construct
        entities or refer to them.
        """
        return self._subtype_concept_bindings

    def referent_concept_bindings(self) -> OrderedSet[ReferentConceptBinding]:
        """
        Returns the referent concept bindings.
        """
        return self._referent_concept_bindings

    def lookup_binding_role(self, binding: Binding):
        if isinstance(binding, RoleBinding):
            # simple case: use the Role from the binding
            role = binding.role
        elif isinstance(binding, (IdentifierConceptBinding, SubtypeConceptBinding, ReferentConceptBinding)):
            # either an IdentifierBinding or a SubtypeBinding, look up the role in the IdentifierRelationship
            concept = binding.entity_type
            if self._reasoner.has_own_ref_scheme(concept):
                role = self._reasoner.own_ref_scheme_role(concept)
            else:
                # this is a subtype binding...
                role = self._reasoner.subtype_unique_ref_scheme_role(concept)
        else:
            raise ValueError(f"Unknown binding type: {type(binding)}")
        return role

    def lookup_role_bindings(self, role: Role, source: BindableTable) -> OrderedSet[Binding]:
        """
        Look up bindings for the given Role and source table.
        Returns an OrderedSet of bindings.
        """
        if role not in self._role_bindings:
            raise ValueError(f"No bindings found for role {role} in table {source}")
        bindings = [binding for binding in self._role_bindings[role] if binding.column.table == source]
        return OrderedSet().update(bindings)

    def is_role_bound(self, role: Role, source: BindableTable) -> bool:
        """
        Check if the given Role is bound in the source table.
        """
        return role in self._role_bindings and bool(self.lookup_role_bindings(role, source))

    def lookup_constructor_binding(self, concept: qb.Concept, column: BindableAttribute):
        """
        Look up a constructor binding for the given Concept and source table.
        """
        if concept._is_primitive():
            raise ValueError(f"Cannot look up entity constructor binding for a value type: {concept}")
        candidates = list(self._identifier_bindings) + list(self._referent_concept_bindings)
        for binding in candidates:
            candidate_role = self.lookup_binding_role(binding)
            sibling = candidate_role.sibling()
            assert sibling is not None
            if binding.column is column and sibling.player() is concept:
                return binding
        raise ValueError(f"Cannot look up entity constructor binding for {concept} from {column}")

    def lookup_constructor_binding_by_source(self, concept: qb.Concept, source: BindableTable):
        """
        Look up a constructor binding for the given Concept and source table.
        """
        if concept._is_primitive():
            raise ValueError(f"Cannot look up entity constructor binding for a value type: {concept}")
        for binding in self._identifier_bindings:
            sibling_role = self.lookup_binding_role(binding).sibling()
            assert sibling_role is not None
            if binding.column.table == source and sibling_role.player() is concept:
                return binding
        raise ValueError(f"Cannot look up entity constructor binding for {concept} from {source}")

    def lookup_subtype_reference_binding(self, binding: Union[IdentifierConceptBinding, SubtypeConceptBinding]):
        """
        Look up a constructor binding referenced by the subtype binding.
        """
        ctor_role = self._reasoner.subtype_unique_ref_scheme_role(binding.entity_type)
        sibling_role = ctor_role.sibling()
        assert sibling_role is not None
        parent_type = sibling_role.player()
        return self.lookup_constructor_binding(parent_type, binding.column)

    def lookup_subtype_reference_binding_by_source(self, binding: Union[IdentifierConceptBinding, SubtypeConceptBinding]):
        """
        Look up a constructor binding referenced by the subtype binding.
        """
        ctor_role = self._reasoner.subtype_unique_ref_scheme_role(binding.entity_type)
        sibling_role = ctor_role.sibling()
        assert sibling_role is not None
        parent_type = sibling_role.player()
        return self.lookup_constructor_binding_by_source(parent_type, binding.column.table)

    def lookup_bound_identifier_constraint_by_source(self, concept: qb.Concept, source: BindableTable):
        """
        Look up a bound identifier constraint for the given Concept and source table.
        """
        identifier_constraints = self._reasoner.ref_schemes_of(concept)
        bound_constraints = OrderedSet()
        for bound_constraint in self._bound_identifier_constraints:
            if bound_constraint.constraint in identifier_constraints and bound_constraint.table == source:
                bound_constraints.add(bound_constraint)
        #=
        # Note: this is a bit naive right now, it should take into account whether the concept is being:
        #  * constructed (we need ALL) or;
        #  * referenced (we need exactly one).
        #
        # To be addressed in https://relationalai.atlassian.net/browse/RAI-39757.
        #=
        if not (bound_constraints and all(b.constraint in identifier_constraints for b in bound_constraints)):
            raise ValueError(
                f"Cannot look up bound identifier constraints for {concept} from {source}, "
                f"no bound constraints found"
            )
        return bound_constraints

    def bound_identifier_constraints(self):
        """
        Returns the bound identifier constraints.
        """
        return self._bound_identifier_constraints

    def lookup_bound_identifier_constraint_by_column(self, concept: qb.Concept, column: BindableAttribute):
        """
        Look up a bound identifier constraint for the given column and concept.
        """
        for constraint in self._bound_identifier_constraints:
            if constraint.concept is concept and constraint.table == column.table:
                for _, binding in constraint.role_bindings.items():
                    if binding.column is column:
                        return constraint
        raise ValueError(f"Cannot look up bound identifier constraint for {concept} from {column.table}")

    def bound_relationships(self) -> OrderedSet[BoundRelationship]:
        """
        Returns the bound relationships.
        """
        return self._bound_relationships

    #=
    # Analysis based on the bindings in the model.
    #=

    def _analyze(self):
        self._classify_bindings()
        self._classify_constraints()
        self._classify_relationships()

    #=
    # Look through the bindings and classify them.
    #=

    def _classify_bindings(self):
        """
        Analyze the bindings in the model and update the reasoner.
        """
        for binding in self._model._bindings:
            self._classify_binding(binding)

    def _classify_binding(self, binding: Binding):
        if isinstance(binding, Union[IdentifierConceptBinding, ReferentConceptBinding]):
            self._process_concept_binding(binding)
        elif isinstance(binding, RoleBinding):
            self._process_role_binding(binding)
        elif isinstance(binding, SubtypeConceptBinding):
            self._process_subtype_concept_binding(binding)
        else:
            raise ValueError(f"Unknown binding type: {type(binding)}")

    def _process_concept_binding(self, binding: Union[IdentifierConceptBinding, ReferentConceptBinding]):
        """
        ConceptBinding could either be an IdentifierBinding or a SubtypeBinding.
        It depends on whether the entity type has a reference scheme or not, if so
        it is an IdentifierBinding, otherwise it is a SubtypeBinding.
        """
        concept = binding.entity_type
        is_referent_binding = isinstance(binding, ReferentConceptBinding)
        if self._reasoner.has_own_ref_scheme(concept):
            # If the concept has its own reference scheme, it is an IdentifierBinding,
            # which could be a referent (if there's a FK to another table) or constructor binding.
            # ReferentConceptBinding is a special case of ConceptBinding, where users tell explicitly
            # that the binding is a referent.
            if not is_referent_binding:
                self._identifier_bindings.add(binding)
            constructing_role = self._reasoner.own_ref_scheme_role(concept)
        else:
            self._subtype_bindings.add(binding)
            constructing_role = self._reasoner.subtype_unique_ref_scheme_role(concept)
        if is_referent_binding:
            self._referent_concept_bindings.add(binding)
        self._role_bindings.setdefault(constructing_role, OrderedSet()).add(binding)
        ref_mode_concept = constructing_role.player()
        self._classify_binding_by_type(binding, ref_mode_concept)

    def _process_role_binding(self, binding: RoleBinding):
        """
        RoleBinding is a simple binding to a Role in a Relationship. The player of the role could
        be either a ValueType or an EntityType.
        """
        self._classify_binding_by_type(binding, binding.role.player())
        self._role_bindings.setdefault(binding.role, OrderedSet()).add(binding)

    def _process_subtype_concept_binding(self, binding: SubtypeConceptBinding):
        """
        FilteringSubtypeBinding is a subtype binding with a filter.

        It is neither an entity nor a value type binding. The filter may be a literal or a value from a
        RoleValueConstraint.
        """
        self._subtype_concept_bindings.add(binding)

    def _classify_binding_by_type(self, binding: Binding, player: qb.Concept):
        if isinstance(binding, SubtypeConceptBinding):
            # SubtypeConceptBinding is neither an entity nor a value type binding.
            return
        if player._is_primitive():
            self._value_type_bindings.add(binding)
        else:
            self._entity_type_bindings.add(binding)

    def _classify_constraints(self):
        for concept, identifier_constraints in self._reasoner.concept_identifiers().items():
            for constraint in identifier_constraints:
                roles = constraint.roles()
                role_bindings_by_table = self._collect_table_role_bindings(roles)
                for table, bindings in role_bindings_by_table.items():
                    if len(bindings) < len(roles):
                        raise ValueError(f"Not all roles are bound in {table.physical_name()}: {bindings} for {roles}")
                    bound_constraint = BoundIdentifierConstraint(constraint, table, bindings)
                    self._bound_identifier_constraints.add(bound_constraint)

    def _collect_table_role_bindings(self, roles):
        role_bindings_by_table = {}
        for role in roles:
            bindings = self._role_bindings.get(role)
            if not bindings:
                continue
            for binding in bindings:
                table = binding.column.table
                role_bindings_by_table.setdefault(table, {}).setdefault(role, []).append(binding)
        return role_bindings_by_table

    def _classify_relationships(self):
        bound_relationship_bindings = {}
        for role, bindings in self._role_bindings.items():
            relationship = role._part_of()
            assert isinstance(relationship, Relationship)
            for binding in bindings:
                table = binding.column.table
                bound_relationship = BoundRelationship(relationship, table)
                bound_relationship_bindings.setdefault(bound_relationship, []).append(binding)

        for bound_relationship, bindings in bound_relationship_bindings.items():
            bound_relationship.bindings.extend(bindings)
            self._validate_bound_relationship(bound_relationship)

    def _validate_bound_relationship(self, bound_relationship: BoundRelationship):
        relationship = bound_relationship.relationship
        arity = relationship._arity()

        if arity == 1 and bound_relationship.bindings:
            self._bound_relationships.add(bound_relationship)
        elif arity == 2:
            self._validate_binary_bound_relationship(bound_relationship)
        elif arity > 2:
            self._validate_nary_bound_relationship(bound_relationship)

    def _validate_binary_bound_relationship(self, bound_relationship: BoundRelationship):
        relationship = bound_relationship.relationship
        if self._reasoner.is_identifier_relationship(relationship):
            # ignore as this is handled by constructor entity maps
            return
        #=
        # Typically, at least one of the roles in a binary relationship must be bound.
        # In such cases, we attempt to infer the entity map for the unbound role, but
        # any value type role must be bound. If unable to infer the entity map, an error
        # is raised.
        #=
        key_role, value_role = self._identify_binary_relationship_roles(relationship)
        # the value role may infer if it's an entity type and the key role is bound
        value_role_may_infer =\
            not value_role.player()._is_primitive() and self.is_role_bound(key_role, bound_relationship.table)
        self._assert_role_is_bound(value_role, bound_relationship.table, may_infer=value_role_may_infer)
        self._assert_role_is_bound(key_role, bound_relationship.table, may_infer=True)
        self._bound_relationships.add(bound_relationship)

    def _identify_binary_relationship_roles(self, relationship: Relationship) -> tuple[Role, Role]:
        roles = relationship._roles()
        key_role, value_role = None, None
        for role in roles:
            if role.player()._is_primitive():
                if value_role is not None:
                    raise ValueError(f"Binary relationship {relationship} has multiple value type roles: "
                                     f"{value_role} and {role}")
                value_role = role
            elif key_role is None and not self._reasoner.is_constructing_role(role):
                key_role = role
            else:
                value_role = role
        if not isinstance(key_role, Role) and not isinstance(value_role, Role):
            raise ValueError(f'Cannot identify roles in a binary relationship {relationship}')
        return key_role, value_role  # pyright: ignore[reportReturnType]

    def _assert_role_is_bound(self, role: Role, source: BindableTable, may_infer=False):
        """
        Asserts that the role is bound in the context of a tabular source.
        If may_infer is True, it allows for inferring the entity map, only for roles played by
        an entity type.
        """
        if not self._role_bindings.get(role):
            # value type roles must be bound, entity type roles may infer
            may_infer = False if role.player()._is_primitive() else may_infer
            if may_infer and self.lookup_bound_identifier_constraint_by_source(role.player(), source):
                # infer the binding from the relationship
                return
            raise ValueError(f"Role {role} in relationship {role._part_of()} is not bound")

    def _validate_nary_bound_relationship(self, bound_relationship: BoundRelationship):
        relationship = bound_relationship.relationship
        roles = relationship._roles()
        bound_roles = OrderedSet()
        for binding in bound_relationship.bindings:
            if not isinstance(binding, RoleBinding):
                raise ValueError(f"Only RoleBindings allowed in N-ary relationships, got: {type(binding)}")
            bound_roles.add(binding.role)

        has_entity_type_player, is_bound = False, True
        for role in roles:
            if not (role in bound_roles or
                    self.lookup_bound_identifier_constraint_by_source(role.player(), bound_relationship.table)):
                is_bound = False
                break
            if not role.player()._is_primitive():
                has_entity_type_player = True

        if is_bound and has_entity_type_player:
            self._bound_relationships.add(bound_relationship)
        elif not is_bound:
            raise ValueError(f"N-ary relationship {relationship} is not fully bound: {bound_roles} vs {roles}")
        else:
            raise ValueError(f"N-ary relationship {relationship} must have at least one entity type player, "
                             f"but all players are value types: {roles}")
