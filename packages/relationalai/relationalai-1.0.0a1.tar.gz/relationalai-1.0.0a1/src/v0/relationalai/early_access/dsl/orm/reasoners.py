from enum import Enum
from typing import Optional, Union

import v0.relationalai.semantics as qb
from v0.relationalai.early_access.dsl.orm.constraints import Constraint, Unique, Mandatory, RoleValueConstraint, \
    InclusiveSubtypeConstraint, ExclusiveSubtypeConstraint, InclusiveRoleConstraint, ExclusiveRoleConstraint, \
    RingConstraint, RoleCardinalityConstraint, ValueConstraint, CardinalityConstraint, FrequencyConstraint, \
    ValueComparisonConstraint, RoleSubsetConstraint, EqualityConstraint
from v0.relationalai.early_access.dsl.orm.relationships import Role, Relationship
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set


class Multiplicity(Enum):
    AT_MOST_ONE = 0
    EXACTLY_ONE = 1
    ZERO_OR_MORE = 2

    def many(self) -> bool:
        return self == Multiplicity.ZERO_OR_MORE

    def qualifier(self) -> str:
        if self == Multiplicity.AT_MOST_ONE:
            return "at most one"
        elif self == Multiplicity.EXACTLY_ONE:
            return "exactly one"
        else:
            return "more than one"

class OntologyReasoner:
    def __init__(self):

        # TODO : populate and use
        self._value_types: OrderedSet[qb.Concept] = OrderedSet()
        self._entity_types: OrderedSet[qb.Concept] = OrderedSet()
        self._exclusive_entity_types: OrderedSet[qb.Concept] = OrderedSet()

        self._concept_identifiers: dict[qb.Concept, OrderedSet[Unique]] = {}
        self._subtype_identifiers: dict[qb.Concept, OrderedSet[Unique]] = {}
        self._supertype_identifiers: dict[qb.Concept, OrderedSet[Unique]] = {}
        self._constraint_identifies: dict[Unique, qb.Concept] = {}
        self._constructor_roles: OrderedSet[Role] = OrderedSet()
        self._mandatory_roles: OrderedSet[Role] = OrderedSet()
        self._role_unique_constraints: dict[Role, OrderedSet[Unique]] = {}

        self._internal_unique_constraints: OrderedSet[Unique] = OrderedSet()
        self._role_value_constraints: OrderedSet[RoleValueConstraint] = OrderedSet()
        self._inclusive_subtype_constraints: OrderedSet[InclusiveSubtypeConstraint] = OrderedSet()
        self._exclusive_subtype_constraints: OrderedSet[ExclusiveSubtypeConstraint] = OrderedSet()
        self._inclusive_role_constraints: OrderedSet[InclusiveRoleConstraint] = OrderedSet()
        self._exclusive_role_constraints: OrderedSet[ExclusiveRoleConstraint] = OrderedSet()
        self._ring_constraints: OrderedSet[RingConstraint] = OrderedSet()
        self._value_comparison_constraints: OrderedSet[ValueComparisonConstraint] = OrderedSet()
        self._role_subset_constraints: OrderedSet[RoleSubsetConstraint] = OrderedSet()
        self._equality_constraints: OrderedSet[EqualityConstraint] = OrderedSet()
        self._frequency_constraints: OrderedSet[FrequencyConstraint] = OrderedSet()
        self._cardinality_constraints: OrderedSet[CardinalityConstraint] = OrderedSet()
        self._role_cardinality_constraints: OrderedSet[RoleCardinalityConstraint] = OrderedSet()
        self._value_constraints: OrderedSet[ValueConstraint] = OrderedSet()

        self._subtype_map: dict[qb.Concept, OrderedSet[qb.Concept]] = {}
        self._supertype_map: dict[qb.Concept, OrderedSet[qb.Concept]] = {}
        self._subtype_closure: dict[qb.Concept, OrderedSet[qb.Concept]] = {}
        self._supertype_closure: dict[qb.Concept, OrderedSet[qb.Concept]] = {}
        self._type_closure: dict[qb.Concept, OrderedSet[qb.Concept]] = {}

        # TODO: populate to check in weaver
        self._errors: OrderedSet[Exception] = OrderedSet()

    
    #=
    # When concepts are added, update the type hierarchy and capture the preferred IDs (inferring as necessary).
    #=

    def new_concept(self, concept: qb.Concept):
        if concept._is_primitive():
            self._value_types.add(concept)
        else:
            self._entity_types.add(concept)
            self._update_type_hierarchy(concept)
            self._update_type_closures(concept)
            self._inherit_parent_identifiers(concept)

    #=
    # When constraints are added, capture the ones that are reference schemes.
    #=

    def new_constraint(self, constraint: Constraint):
        if isinstance(constraint, Unique):
            self._process_uniqueness_constraint(constraint)
        elif isinstance(constraint, Mandatory):
            self._process_mandatory_constraint(constraint)
        elif isinstance(constraint, RoleValueConstraint):
            self._role_value_constraints.add(constraint)
        elif isinstance(constraint, InclusiveSubtypeConstraint):
            self._inclusive_subtype_constraints.add(constraint)
        elif isinstance(constraint, ExclusiveSubtypeConstraint):
            self._exclusive_subtype_constraints.add(constraint)
        elif isinstance(constraint, InclusiveRoleConstraint):
            self._inclusive_role_constraints.add(constraint)
        elif isinstance(constraint, ExclusiveRoleConstraint):
            self._exclusive_role_constraints.add(constraint)
        elif isinstance(constraint, RingConstraint):
            self._ring_constraints.add(constraint)
        elif isinstance(constraint, ValueComparisonConstraint):
            self._value_comparison_constraints.add(constraint)
        elif isinstance(constraint, RoleSubsetConstraint):
            self._role_subset_constraints.add(constraint)
        elif isinstance(constraint, EqualityConstraint):
            self._equality_constraints.add(constraint)
        elif isinstance(constraint, FrequencyConstraint):
            self._frequency_constraints.add(constraint)
        elif isinstance(constraint, CardinalityConstraint):
            self._cardinality_constraints.add(constraint)
        elif isinstance(constraint, RoleCardinalityConstraint):
            self._role_cardinality_constraints.add(constraint)
        elif isinstance(constraint, ValueConstraint):
            self._value_constraints.add(constraint)

    #=
    # Constraints: uniqueness and reference schemes.
    #=

    def ref_schemes_of(self, entity_type: qb.Concept, shallow=False) -> OrderedSet[Unique]:
        """
        Returns the reference schemes that are defined for the entity type (plus those inferred from sub- or supertypes).
        """
        own_reference_schemes = self._concept_identifiers.get(entity_type) or OrderedSet()
        if shallow or self.is_exclusive_entity_type(entity_type):
            supertype_reference_schemes = self._supertype_identifiers.get(entity_type) or OrderedSet()
            subtype_reference_schemes = self._subtype_identifiers.get(entity_type) or OrderedSet()
        else:
            supertype_reference_schemes = self.subtype_ref_schemes_of(entity_type)
            subtype_reference_schemes = OrderedSet()
        return supertype_reference_schemes | own_reference_schemes | subtype_reference_schemes

    def subtype_unique_ref_scheme_role(self, entity_type: qb.Concept) -> Role:
        """
        Returns the role used to construct the entity type.

        Only valid for simple reference schemes inferred by a subtype.
        """
        ref_schemes = self.ref_schemes_of(entity_type)
        if len(ref_schemes) != 1:
            raise ValueError(f"No unique reference scheme found for {entity_type}")
        ref_scheme = ref_schemes[0]
        return self._extract_unique_role_from_uc(ref_scheme)

    def subtype_ref_schemes_of(self, entity_type: qb.Concept) -> OrderedSet[Unique]:
        """
        Returns the reference schemes that are defined for the entity type and any of its parent types.
        """
        ref_schemes = entity_type._ref_scheme()
        if ref_schemes is None:
            raise ValueError(f"No reference scheme found for {entity_type}")
        identifier_constraints = OrderedSet()
        for relationship in ref_schemes:
            if not isinstance(relationship, Relationship):
                raise ValueError(f"Expected a Relationship, but got {type(relationship)}")
            identifier_constraints.add(self.lookup_identifier_constraint(relationship))
        return identifier_constraints

    def own_ref_scheme_of(self, entity_type: qb.Concept) -> Unique:
        """
        Returns the reference schemes that are defined for the entity type (but not inferred).
        """
        own_ref_schemes = self._concept_identifiers[entity_type]
        if len(own_ref_schemes) != 1:
            raise ValueError(f"Expected exactly one reference scheme for {entity_type}, but got {len(own_ref_schemes)}")
        return own_ref_schemes[0]

    def own_ref_scheme_role(self, entity_type: qb.Concept) -> Role:
        """
        Returns the role used to construct the entity type. Only valid for simple reference schemes.
        """
        ref_scheme = self.own_ref_scheme_of(entity_type)
        return self._extract_unique_role_from_uc(ref_scheme)

    def has_own_ref_scheme(self, entity_type: qb.Concept) -> bool:
        """
        Returns true if the entity type has a reference scheme defined for it.
        """
        return entity_type in self._concept_identifiers

    def has_simple_ref_scheme(self, entity_type: qb.Concept) -> bool:
        ref_schemes = self.ref_schemes_of(entity_type)
        if len(ref_schemes) == 0:
            raise ValueError(f"No reference scheme found for {entity_type}")
        for uc in ref_schemes:
            if len(uc.roles()) > 1:
                return False
        return True

    def has_composite_ref_scheme(self, entity_type: qb.Concept) -> bool:
        return not self.has_simple_ref_scheme(entity_type)

    def is_constructing_role(self, role: Role) -> bool:
        """
        Returns true if the role is a constructing role (i.e., it is used to construct an entity type).
        """
        return role in self._constructor_roles

    def concept_identifiers(self) -> dict[qb.Concept, OrderedSet[Unique]]:
        """
        Returns a mapping of entity types to their reference schemes.
        """
        return self._concept_identifiers

    def is_identifier_relationship(self, relationship: Relationship) -> bool:
        """
        Returns true if the relationship is an identifier relationship (i.e., it is used to construct an entity type).
        """
        if not relationship._binary():
            return False
        for role in relationship._roles():
            if self.is_constructing_role(role):
                return True
        return False

    def lookup_identifier_constraint(self, relationship: Relationship) -> Unique:
        """
        Returns the corresponding identifier constraint for an identifier relationship.
        """
        if not self.is_identifier_relationship(relationship):
            raise ValueError(f"Expected an identifier relationship, but got {relationship}")
        concept_role = None
        constructing_role = None
        for role in relationship._roles():
            if self.is_constructing_role(role):
                concept_role = role.sibling()
                constructing_role = role
            else:
                constructing_role = role.sibling()
                concept_role = role
        assert concept_role is not None and constructing_role is not None, \
            f"Expected both roles to be defined in {relationship}"
        for constraint in self._concept_identifiers[concept_role.player()]:
            if constructing_role in constraint.roles():
                return constraint
        raise ValueError(f"No identifier constraint found for {relationship}")

    def identifies_concept(self, constraint: Unique) -> qb.Concept:
        """
        Returns the concept that is identified by the given uniqueness constraint.
        """
        if constraint not in self._constraint_identifies:
            raise KeyError(f"No concept identified by {constraint}")
        return self._constraint_identifies[constraint]

    def is_composite_concept(self, concept: qb.Concept) -> bool:
        """
        Returns true if the concept is a composite concept (i.e., it has a composite reference scheme).
        """
        ref_schemes = self.ref_schemes_of(concept)
        if len(ref_schemes) == 0:
            return False
        for uc in ref_schemes:
            if len(uc.roles()) > 1:
                return True
        return False

    def is_exclusive_entity_type(self, entity_type: qb.Concept) -> bool:
        """
        Returns true if the entity type is an exclusive entity type).
        """
        return entity_type in self._exclusive_entity_types or self._check_exclusive_supertype(entity_type)

    def _check_exclusive_supertype(self, entity_type: qb.Concept) -> bool:
        """
        Checks if the entity type is an exclusive supertype.
        """
        if self.has_own_ref_scheme(entity_type):
            return False
        subtypes = self._subtype_map.get(entity_type)
        is_exclusive = subtypes is not None
        if is_exclusive:
            self._exclusive_entity_types.add(entity_type)
        return is_exclusive

    def subtype_exclusive_supertype(self, subtype: qb.Concept) -> Optional[qb.Concept]:
        """
        Returns the exclusive supertype of the given subtype if it exists.
        """
        supertypes = self._supertype_map.get(subtype)
        if not supertypes:
            return None
        for supertype in supertypes:
            if self.is_exclusive_entity_type(supertype):
                return supertype
        return None

    def in_subtype_closure(self, sub: qb.Concept, sup: qb.Concept) -> bool:
        """
        Returns true if sub is in the subtype closure of sup.
        """
        return sub in self._subtype_closure.get(sup, OrderedSet())

    def is_mandatory_role(self, role: Role) -> bool:
        """
        Returns true if the role is a mandatory role.
        """
        return role in self._mandatory_roles

    def is_one_role(self, role: Role) -> bool:
        """
        Returns true if the role is a "one" role (as opposed to a "many" role),
          i.e. it is not spanned by an internal uniqueness constraint.
        """
        return not any(c in self._internal_unique_constraints for c in self._role_unique_constraints.get(role, OrderedSet()))

    def are_roles_compatible(self, role1: Role, role2: Role) -> bool:
        """
        Returns true if the two roles are compatible, i.e. they have the same player or
        one is a subtype of the other.
        """
        return (
            role1.player() is role2.player() or
            self.in_subtype_closure(role1.player(), role2.player()) or
            self.in_subtype_closure(role2.player(), role1.player())
        )

    # [REKS: TODO] Need to improve to handle multiple inheritance properly
    def least_supertype(self, concept1: qb.Concept, concept2: qb.Concept) -> Optional[qb.Concept]:
        """
        Returns the least common supertype of the two concepts, if it exists.
        """
        supertypes1 = ordered_set(concept1, *self._supertype_closure.get(concept1, OrderedSet()))
        supertypes2 = ordered_set(concept2, *self._supertype_closure.get(concept2, OrderedSet()))
        common = supertypes1 & supertypes2
        return common.first() if common else None

    def internal_ucs_of(self, relationship: Union[qb.Relationship, qb.RelationshipReading]) -> OrderedSet[Unique]:
        """
        Returns the set of internal uniqueness constraints that span any role that
        is part of relationship
        """
        oset = OrderedSet()
        ucdict = self._role_unique_constraints
        for role in relationship._roles():
            if role in ucdict:
                for uc in ucdict[role]:
                    if uc in self._internal_unique_constraints:
                        oset.add(uc)
        return oset


    # Let *role* be a Role of some Relationship R. The *point multiplicity* of
    # role considers maximal subsets F of facts of R in which, for every Role r
    # where:
    #
    #     r in roles(R) \ {role}
    #
    # there exists some object o that plays r in each fact in F. That is, each
    # F is some set of R facts in which every Role but *role* is bound to the
    # same object in each fact in F.
    #
    # The point multiplicity of *role* is then either:
    #   - AT_MOST_ONE, if for every F, |F| <= 0
    #   - EXACTLY_ONE, if for every F, |F| == 1
    #   - ZERO_OR_MORE, otherwise
    #
    def point_multiplicity(self, role: Role) -> Multiplicity:
        relationship = role._part_of()
        ucs = self.internal_ucs_of(relationship)
        if len(ucs) > 0:
            # If there exists a UC that does NOT span role, then
            # that UC determines the multiplicity of role.
                for uc in ucs:
                    if role not in uc.roles():
                        # Then multiplicity is either AT_MOST_ONE or ONE
                        sibling_role = role.sibling()
                        if sibling_role is not None and self.is_mandatory_role(sibling_role):
                            return Multiplicity.EXACTLY_ONE
                        return Multiplicity.AT_MOST_ONE
        return Multiplicity.ZERO_OR_MORE

    @staticmethod
    def _extract_unique_role_from_uc(uc: Unique) -> Role:
        """
        Extracts the unique role from a uniqueness constraint.
        """
        roles = uc.roles()
        if len(roles) != 1:
            raise ValueError(f"Expected exactly one role in uniqueness constraint, but got {len(roles)}")
        return roles[0]


    def _update_type_hierarchy(self, new_entity_type: qb.Concept):
        parent_concepts = new_entity_type._extends
        for parent_concept in parent_concepts:
            self._subtype_map.setdefault(parent_concept, OrderedSet()).add(new_entity_type)
            self._supertype_map.setdefault(new_entity_type, OrderedSet()).add(parent_concept)

    def _update_type_closures(self, new_entity_type: qb.Concept):
        parent_concepts = new_entity_type._extends
        self._supertype_closure.setdefault(new_entity_type, OrderedSet()).update(parent_concepts)
        for parent_concept in parent_concepts:
            self._supertype_closure[new_entity_type].update(self._supertype_closure[parent_concept])
        self._type_closure.setdefault(new_entity_type, OrderedSet()).update(self._supertype_closure[new_entity_type])

        for supertype in self._supertype_closure[new_entity_type]:
            self._subtype_closure.setdefault(supertype, OrderedSet()).add(new_entity_type)
            self._type_closure.setdefault(supertype, OrderedSet()).add(new_entity_type)

    def _inherit_parent_identifiers(self, new_entity_type: qb.Concept):
        for parent in new_entity_type._extends:
            self._supertype_identifiers.setdefault(new_entity_type, OrderedSet()).update(
                self._supertype_identifiers.get(parent, OrderedSet())).update(
                    self._concept_identifiers.get(parent, OrderedSet()))

            
    def _process_uniqueness_constraint(self, constraint: Unique):
        for role in constraint.roles():
            self._role_unique_constraints.setdefault(role, OrderedSet()).add(constraint)

        if len(set(r._part_of() for r in constraint.roles())) == 1:
            self._internal_unique_constraints.add(constraint)
        
        # note: ignoring the ones that are not preferred identifiers for now
        if not constraint.is_preferred_identifier:
            return

        roles = constraint.roles()
        self._constructor_roles.update(roles)  # mark as ctor roles

        constructed_concept = None
        if constraint._is_internal():
            # simple ref scheme
            constructed_concept = self._process_simple_ref_scheme(constraint)
        else:
            # composite ref scheme
            constructed_concept = self._process_composite_ref_scheme(constraint)
        self._update_subtype_identifiers(constructed_concept, constraint)

    def _process_simple_ref_scheme(self, constraint: Unique):
        role = constraint.roles()[0]
        relation = role._relationship  # actually a DSL Relation
        if relation._arity() != 2:
            raise ValueError(f"Identifier relationship {relation} should have arity 2, but got {relation._arity()}")
        sibling_role = role.sibling()
        if sibling_role is None:
            raise ValueError(f"Unable to find the sibling role for {role}")
        constructed_concept = sibling_role.player()
        self._concept_identifiers.setdefault(constructed_concept, OrderedSet()).add(constraint)
        self._constraint_identifies[constraint] = constructed_concept
        return constructed_concept

    def _process_composite_ref_scheme(self, constraint: Unique):
        roles = constraint.roles()
        if len(roles) <= 1: 
            raise ValueError(f"External uniqueness constraint should have more than one role, but got {len(roles)}")
        role = roles[0]  # take an arbitrary role to get the constructed concept
        sibling_role = role.sibling()
        if sibling_role is None:
            raise ValueError(f"Unable to find the sibling role for {role}")
        constructed_concept = sibling_role.player()
        self._concept_identifiers.setdefault(constructed_concept, OrderedSet()).add(constraint)
        self._constraint_identifies[constraint] = constructed_concept
        return constructed_concept
    
    def _update_subtype_identifiers(self, entity_type: qb.Concept, constraint: Unique):
        # Clear subtype identifiers for the entity type that now has its own, if they exist
        self._subtype_identifiers.pop(entity_type, None)

        # For all subtypes that now have their own (or parent's) identifiers, clear subtype identifiers
        subtypes = self._subtype_closure.get(entity_type, OrderedSet())
        for subtype in subtypes:
            if subtype._ref_scheme():
                self._subtype_identifiers.pop(subtype, None)

            self._supertype_identifiers.setdefault(subtype, OrderedSet()).add(constraint)

        # For all supertypes that do not have their own (or parent's) identifiers, add the current constraint
        supertypes = self._supertype_closure.get(entity_type, OrderedSet())
        for supertype in supertypes:
            if not supertype._ref_scheme():
                self._subtype_identifiers.setdefault(supertype, OrderedSet()).add(constraint)

    def _process_mandatory_constraint(self, constraint: Mandatory):
        role = constraint.roles()[0]
        self._mandatory_roles.add(role)
