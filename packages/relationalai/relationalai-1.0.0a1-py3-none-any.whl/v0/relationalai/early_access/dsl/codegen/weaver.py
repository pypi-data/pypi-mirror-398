from collections import OrderedDict
from itertools import product
from types import MappingProxyType
from typing import Union, Sequence

import v0.relationalai.semantics as qb
from v0.relationalai.semantics import where
from v0.relationalai.early_access.dsl.bindings.common import Binding, RoleBinding, IdentifierConceptBinding, BindableTable, \
    BindableAttribute, SubtypeConceptBinding, ReferentConceptBinding
from v0.relationalai.early_access.dsl.codegen.binder import Binder
from v0.relationalai.early_access.dsl.codegen.common import BoundIdentifierConstraint, BoundRelationship
from v0.relationalai.early_access.dsl.codegen.relations import ValueMap, CompositeEntityMap, EntitySubtypeMap, \
    UnionEntityMap, AbstractEntityMap, SimpleConstructorEntityMap, ReferentEntityMap, InlineValueMap, \
    Map, MaterializedEntityMap, AbstractInlineEntityMap
from v0.relationalai.semantics.metamodel.util import OrderedSet

DEFAULT_WEAVER_CONFIG = MappingProxyType({
    'inline_value_maps': False,
    'inline_entity_maps': False,
})


class Weaver:

    def __init__(self, model, config=None):
        self._model = model
        self._config = config or DEFAULT_WEAVER_CONFIG
        self._reasoner = self._model.reasoner()
        self._binder = Binder(self._model)

        # Lookup dictionaries for generated relations
        self._binding_to_value_map: dict[Binding, Union[ValueMap, InlineValueMap]] = OrderedDict()
        self._ctor_binding_to_entity_map:\
            dict[IdentifierConceptBinding, Union[AbstractInlineEntityMap, MaterializedEntityMap]] = OrderedDict()
        self._ref_binding_to_entity_map:\
            dict[ReferentConceptBinding, Union[AbstractInlineEntityMap, MaterializedEntityMap]] = OrderedDict()
        self._bound_identifier_to_composite_entity_map:\
            dict[BoundIdentifierConstraint, OrderedSet[Union[AbstractInlineEntityMap, MaterializedEntityMap]]] = OrderedDict()
        self._subtype_binding_to_entity_map:\
            dict[Union[IdentifierConceptBinding, ReferentConceptBinding], Union[AbstractInlineEntityMap, MaterializedEntityMap]] = OrderedDict()
        self._filtering_subtype_binding_to_entity_map:\
            dict[SubtypeConceptBinding, Union[AbstractInlineEntityMap, MaterializedEntityMap]] = OrderedDict()
        self._supertype_to_entity_map: dict[qb.Concept, UnionEntityMap] = OrderedDict()

    def generate(self):
        self._generate_value_maps()
        self._generate_entity_maps()
        self._generate_semantic_predicates()

    def _generate_value_maps(self):
        for binding in self._binder.value_type_bindings():
            self._generate_value_map(binding)

    def _generate_value_map(self, binding: Binding):
        role = self._binder.lookup_binding_role(binding)
        if self._cfg_should_inline_value_maps():
            value_map = InlineValueMap(self._model, binding, role)
        else:
            value_map = ValueMap(self._model, binding, role)
        self._binding_to_value_map[binding] = value_map

    def _look_up_value_map(self, binding: Binding):
        """
        Look up a value map in the model by value type binding.
        """
        return self._binding_to_value_map[binding]

    def _generate_entity_maps(self):
        self._generate_simple_ctor_entity_maps()
        self._generate_referent_entity_maps()
        self._generate_composite_entity_maps()
        self._generate_subtype_entity_maps()
        self._generate_filtered_subtype_entity_maps()
        self._generate_supertype_entity_maps()

    def _generate_simple_ctor_entity_maps(self):
        for binding in self._binder.constructor_bindings():
            self._generate_simple_ctor_entity_map(binding)

    def _generate_simple_ctor_entity_map(self, binding: IdentifierConceptBinding):
        ctor_role = self._binder.lookup_binding_role(binding)
        role = ctor_role.sibling()
        assert role is not None, "Constructor binding must have a sibling role"
        identifier_to_role_map = self._lookup_supertype_identifier_role_maps(binding)

        entity_map = SimpleConstructorEntityMap(self._model, binding, role, identifier_to_role_map)
        entity_map = self._try_materialize_entity_map(entity_map)
        self._ctor_binding_to_entity_map[binding] = entity_map

    def _lookup_supertype_identifier_role_maps(self, binding: IdentifierConceptBinding):
        """
        Build a mapping from each reference scheme of the binding's concept to the corresponding constructing role map.
        """
        concept = binding.entity_type
        ref_scheme_to_role_map = OrderedDict()

        for ref_scheme in self._reasoner.ref_schemes_of(concept):
            constructed_concept = self._reasoner.identifies_concept(ref_scheme)

            #=
            # May need to look up the constructor binding for another concept with (.id) in the concept's hierarchy.
            # E.g., if the concept is a subtype with multiple ref schemes, we need to look up the respective constructor
            # binding for each supertype with a reference scheme.
            #=
            constructor_binding = (
                binding if constructed_concept is concept
                else self._binder.lookup_constructor_binding_by_source(constructed_concept, binding.column.table)
            )

            ctor_role = self._binder.lookup_binding_role(constructor_binding)
            player = ctor_role.player()

            # If the constructor role is played by a primitive, use its sibling's player
            if player._is_primitive():
                sibling = ctor_role.sibling()
                assert sibling is not None, "Constructor roles must have a sibling role"
                player = sibling.player()

            role_map = self._lookup_constructing_role_map(constructor_binding, player)
            ref_scheme_to_role_map[ref_scheme] = role_map
        return ref_scheme_to_role_map

    def _lookup_constructing_role_map(self, binding: Union[IdentifierConceptBinding, ReferentConceptBinding],
                                      concept: qb.Concept):
        if self._binder.is_value_type_binding(binding):
            role_map = self._binding_to_value_map[binding]
        elif isinstance(binding, IdentifierConceptBinding):
            #=
            # This call is needed to ensure we look up the ctor binding for the concept, which may not be the same as
            # the one in the binding. This is because the reference scheme may have an entity type in the constructing
            # role, hence we need to look up the constructor binding and then the role map for that binding.
            #=
            ctor_binding = self._binder.lookup_constructor_binding(concept, binding.column)
            assert isinstance(ctor_binding, IdentifierConceptBinding)
            role_map = self._ctor_binding_to_entity_map[ctor_binding]
        elif isinstance(binding, ReferentConceptBinding):
            # TODO: check why we need `binder.lookup_constructor_binding` above?
            role_map = self._ref_binding_to_entity_map[binding]
        else:
            raise ValueError(f'Cannot lookup constructing role map for binding {binding} and concept {concept}')
        return role_map

    def _generate_referent_entity_maps(self):
        for binding in self._binder.referent_concept_bindings():
            self._generate_referent_entity_map(binding)

    def _generate_referent_entity_map(self, binding: ReferentConceptBinding):
        ctor_role = self._binder.lookup_binding_role(binding)
        role = ctor_role.sibling()
        assert role is not None, "Referent concept binding must have a sibling role"
        constructing_role_map = self._lookup_constructing_role_map(binding, binding.entity_type)
        entity_map = ReferentEntityMap(self._model, binding, role, constructing_role_map)
        entity_map = self._try_materialize_entity_map(entity_map)
        self._ref_binding_to_entity_map[binding] = entity_map

    def _generate_composite_entity_maps(self):
        for constraint in self._binder.bound_identifier_constraints():
            if constraint.is_external():
                # generate a composite entity map
                self._generate_composite_entity_map(constraint)

    def _generate_composite_entity_map(self, constraint: BoundIdentifierConstraint):
        role_map_combinations = self._composite_entity_map_combinations(constraint)
        entity_concept = constraint.concept
        for role_maps in role_map_combinations:
            entity_map = CompositeEntityMap(self._model, entity_concept, *role_maps)
            entity_map = self._try_materialize_entity_map(entity_map)
            self._bound_identifier_to_composite_entity_map.setdefault(constraint, OrderedSet()).add(entity_map)

    def _composite_entity_map_combinations(self, bound_uc: BoundIdentifierConstraint) -> Sequence[Sequence[Map]]:
        role_bindings = bound_uc.role_bindings
        # Build a list of binding lists for each role in the right order
        role_binding_lists = [role_bindings[role] for role in bound_uc.constraint.roles()]
        # Generate all possible combinations of bindings and convert each combination to a list
        all_combinations = [list(combination) for combination in product(*role_binding_lists)]  # pyright: ignore[reportArgumentType, reportCallIssue]
        # Construct entity map combinations using the _ref_entity_map method
        role_map_combinations = [
            [self._lookup_ref_role_map(binding) for binding in combination]
            for combination in all_combinations
        ]
        return role_map_combinations

    def _lookup_ref_role_map(self, binding: RoleBinding):
        concept = binding.role.player()
        if concept._is_primitive():
            role_map = self._binding_to_value_map[binding]
        else:
            ctor_binding = self._binder.lookup_constructor_binding(concept, binding.column)
            role_map = self._lookup_ref_role_map_by_ctor_binding(ctor_binding)
        return role_map

    def _lookup_ref_role_map_by_ctor_binding(self, binding: Union[IdentifierConceptBinding, ReferentConceptBinding]):
        if isinstance(binding, IdentifierConceptBinding):
            role_map = self._ctor_binding_to_entity_map[binding]
        elif isinstance(binding, ReferentConceptBinding):
            role_map = self._ref_binding_to_entity_map[binding]
        else:
            raise ValueError(f'Cannot lookup role map for binding {binding} - invalid type of binding')
        return role_map

    def _lookup_ref_entity_maps_by_column(self, concept: qb.Concept, column: BindableAttribute):
        if self._reasoner.is_composite_concept(concept):  # composite entity type
            identifier_constraint = self._binder.lookup_bound_identifier_constraint_by_column(concept, column)
            entity_map_candidates = self._bound_identifier_to_composite_entity_map[identifier_constraint]
            # note: for now, we look up by table, though needs fixing
            return self._find_matching_entity_maps(entity_map_candidates, concept, column.table)
        elif self._reasoner.has_own_ref_scheme(concept):  # simple entity type
            entity_map_candidates = (list(self._ctor_binding_to_entity_map.values()) +
                                     list(self._ref_binding_to_entity_map.values()))
            return self._find_matching_entity_maps(entity_map_candidates, concept, column)
        elif self._reasoner.is_exclusive_entity_type(concept):  # exclusive entity type
            entity_map_candidates = self._supertype_to_entity_map.values()
            # note: for now, we look up by table, though needs fixing
            return self._find_matching_entity_maps(entity_map_candidates, concept, column.table, strict_match=True)
        else:  # entity subtype
            entity_map_candidates = self._subtype_binding_to_entity_map.values()
            return self._find_matching_entity_maps(entity_map_candidates, concept, column)

    def _lookup_ref_entity_maps_by_source(self, concept: qb.Concept, source: BindableTable):
        if self._reasoner.is_composite_concept(concept):  # composite entity type
            identifier_constraints = self._binder.lookup_bound_identifier_constraint_by_source(concept, source)
            entity_map_candidates = [entity_map for identifier_constraint in identifier_constraints
                                     for entity_map in
                                     self._bound_identifier_to_composite_entity_map[identifier_constraint]]
            return self._find_matching_entity_maps(entity_map_candidates, concept, source)
        elif self._reasoner.has_own_ref_scheme(concept):  # simple entity type
            entity_map_candidates = (list(self._ctor_binding_to_entity_map.values()) +
                                     list(self._ref_binding_to_entity_map.values()))
            return self._find_matching_entity_maps(entity_map_candidates, concept, source)
        elif self._reasoner.is_exclusive_entity_type(concept):  # exclusive entity type
            entity_map_candidates = self._supertype_to_entity_map.values()
            return self._find_matching_entity_maps(entity_map_candidates, concept, source, strict_match=True)
        else:  # entity subtype
            entity_map_candidates = (list(self._subtype_binding_to_entity_map.values()) +
                                     list(self._filtering_subtype_binding_to_entity_map.values()))
            return self._find_matching_entity_maps(entity_map_candidates, concept, source)
        # TODO : revise the above logic and see if uniqueness check is needed for anythine else

    @staticmethod
    def _find_matching_entity_maps(entity_maps, concept: qb.Concept,
                                   source_or_col: Union[BindableTable, BindableAttribute],
                                   strict_match: bool=False):
        strictly_matching = OrderedSet()
        loosely_matching = OrderedSet()
        for entity_map in entity_maps:
            value_player = entity_map.value_player()
            if Weaver._matches_source(entity_map, source_or_col):
                if concept is value_player:
                    strictly_matching.add(entity_map)
                elif concept._isa(value_player):
                    loosely_matching.add(entity_map)
        matching_entity_maps = strictly_matching if bool(strictly_matching) or strict_match else loosely_matching
        if not matching_entity_maps:
            raise ValueError(f'No entity map found for concept {concept} and {source_or_col}')
        return matching_entity_maps

    @staticmethod
    def _matches_source(entity_map, source_or_col: Union[BindableTable, BindableAttribute]):
        if isinstance(source_or_col, BindableTable):
            return entity_map.table() == source_or_col
        elif isinstance(source_or_col, BindableAttribute):
            return entity_map.column() is source_or_col
        else:
            return False

    def _generate_subtype_entity_maps(self):
        for binding in self._binder.subtype_ctor_bindings():
            self._generate_subtype_entity_map(binding)

    def _generate_subtype_entity_map(self, binding: Union[IdentifierConceptBinding, ReferentConceptBinding]):
        if isinstance(binding, ReferentConceptBinding):
            ctor_entity_map = self._ref_binding_to_entity_map[binding]
        else:
            ctor_binding = self._binder.lookup_subtype_reference_binding(binding)
            ctor_entity_map = self._lookup_ref_role_map_by_ctor_binding(ctor_binding)
        entity_map = EntitySubtypeMap(self._model, binding, ctor_entity_map)
        entity_map = self._try_materialize_entity_map(entity_map)
        self._subtype_binding_to_entity_map[binding] = entity_map

    def _generate_filtered_subtype_entity_maps(self):
        for binding in self._binder.subtype_filtering_bindings():
            self._generate_filtered_subtype_entity_map(binding)

    def _generate_filtered_subtype_entity_map(self, binding: SubtypeConceptBinding):
        ctor_binding = self._binder.lookup_subtype_reference_binding(binding)
        ctor_entity_map = self._lookup_ref_role_map_by_ctor_binding(ctor_binding)
        entity_map = EntitySubtypeMap(self._model, binding, ctor_entity_map)
        entity_map = self._try_materialize_entity_map(entity_map)
        self._filtering_subtype_binding_to_entity_map[binding] = entity_map

    def _generate_supertype_entity_maps(self):
        simple_subtype_maps = self._subtype_binding_to_entity_map.values()
        filtering_subtype_maps = self._filtering_subtype_binding_to_entity_map.values()
        subtype_maps = (OrderedSet()
                        .update(simple_subtype_maps)
                        .update(filtering_subtype_maps))
        for subtype_map in subtype_maps:
            self._generate_supertype_entity_map(subtype_map)
        # after generating all supertype maps, try to materialize them
        [entity_map.materialize_population() for entity_map in self._supertype_to_entity_map.values()]

    def _generate_supertype_entity_map(self, subtype_map: AbstractEntityMap):
        subtype = subtype_map.value_player()
        supertype = self._reasoner.subtype_exclusive_supertype(subtype)
        if not supertype:
            return
        supertype_map = self._supertype_to_entity_map.get(supertype)
        if supertype_map is None:
            supertype_map = UnionEntityMap(self._model, supertype, subtype_map, generate_population=True)
            self._supertype_to_entity_map[supertype] = supertype_map
        else:
            supertype_map.update(subtype_map)
        # go higher in the hierarchy
        self._generate_supertype_entity_map(supertype_map)

    def _generate_semantic_predicates(self):
        for bound_relationship in self._binder.bound_relationships():
            self._generate_semantic_predicate(bound_relationship)

    def _generate_semantic_predicate(self, bound_relationship: BoundRelationship):
        if bound_relationship.relationship._unary():
            self._generate_unary_predicate_rule(bound_relationship)
        else:
            self._generate_nary_predicate_rule(bound_relationship)

    def _generate_unary_predicate_rule(self, bound_relationship: BoundRelationship):
        relationship = bound_relationship.relationship
        roles = relationship._roles()
        assert len(roles) == 1, "Unary predicate should have exactly one role"
        unary_role = roles[0]
        bound_concept = unary_role.player()
        if bound_concept._is_primitive():
            raise ValueError(f'Unary relationships cannot be defined on value types: {relationship}')
        role_bindings = bound_relationship.bindings
        for binding in role_bindings:
            if not self._binder.is_filtering_binding(binding):
                raise ValueError(f'Unary relationship roles must be bound by a filtering binding (use `filter_by`): {relationship}')
            self._generate_unary_predicate_rule_body(bound_concept, binding, relationship)

    def _generate_unary_predicate_rule_body(self, concept_player: qb.Concept, binding: Binding, relationship):
        entity_maps = self._lookup_ref_entity_maps_by_column(concept_player, binding.column)
        if not entity_maps:
            raise ValueError(
                f'Cannot generate semantic predicate for {relationship}, no role maps found')
        for entity_map in entity_maps:
            entity_ref, subformula_atoms = entity_map.formula()
            where(
                *subformula_atoms,
                where(binding.filter_by)
            ).define(relationship(entity_ref))

    def _generate_nary_predicate_rule(self, bound_relationship: BoundRelationship):
        relationship = bound_relationship.relationship
        roles = relationship._roles()
        #=
        # Each role should either be covered by a value map (value type role), or by an entity map (entity type role).
        # The entity map either can be inferred if unique exists for the entity type, or must be generated by
        # the respective EntityBinding.
        #=
        role_to_role_maps = OrderedDict()
        role_map_casts_to = OrderedDict()
        for role in roles:
            role_concept = role.player()
            if role_concept._is_primitive():
                # TODO: [SB] I suppose we can do bound_relationship.role_bindings[role] here?
                role_bindings = self._binder.lookup_role_bindings(role, bound_relationship.table)
                role_maps = [self._binding_to_value_map[binding] for binding in role_bindings]
            else:
                role_is_bound = self._binder.is_role_bound(role, bound_relationship.table)
                if role_is_bound:
                    # lookup referent entity maps
                    role_bindings = self._binder.lookup_role_bindings(role, bound_relationship.table)
                    role_maps = [entity_map for binding in role_bindings
                                 for entity_map in self._lookup_ref_entity_maps_by_column(role.player(), binding.column)]
                    for role_map in role_maps:
                        role_map_concept = role_map.value_player()
                        if role_map_concept is not role_concept and self._reasoner.in_subtype_closure(role_concept, role_map_concept):
                            role_map_casts_to[role_map] = role_concept
                else:
                    # lookup inferred entity map (note: must be unique?)
                    role_maps = [entity_map
                                 for entity_map in self._lookup_ref_entity_maps_by_source(role.player(), bound_relationship.table)]
            if not role_maps:
                raise ValueError(f'Cannot generate semantic predicate for {relationship},'
                                 f' no role maps found for role {role}')
            role_to_role_maps[role] = role_maps
        # if we got all roles with role maps, we can generate the rules
        role_map_combinations = [list(combination) for combination in product(*role_to_role_maps.values())]  # pyright: ignore[reportCallIssue]
        for role_maps in role_map_combinations:
            assert len(role_maps) > 0, "Must have at least one role map to derive a relationship"
            casted_var_refs, atoms = [], []
            for role_map in role_maps:
                var_ref, subformula = role_map.formula()
                if role_map in role_map_casts_to:
                    var_ref = role_map_casts_to[role_map](var_ref)
                casted_var_refs.append(var_ref)
                atoms.extend(subformula)
            where(*atoms).define(relationship(*casted_var_refs))

    def _try_materialize_entity_map(self, entity_map: AbstractInlineEntityMap) -> Union[AbstractInlineEntityMap, MaterializedEntityMap]:
        if self._cfg_should_inline_entity_maps():
            entity_map.materialize_population()
            return entity_map
        else:
            return entity_map.materialize()

    def _cfg_should_inline_value_maps(self):
        """
        Check if the config should inline value maps.
        """
        return self._config.get('inline_value_maps', DEFAULT_WEAVER_CONFIG['inline_value_maps'])

    def _cfg_should_inline_entity_maps(self):
        """
        Check if the config should inline entity maps.
        """
        return self._config.get('inline_entity_maps', DEFAULT_WEAVER_CONFIG['inline_entity_maps'])
