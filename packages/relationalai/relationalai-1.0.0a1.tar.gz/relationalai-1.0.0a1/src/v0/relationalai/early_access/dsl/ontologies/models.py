from collections import OrderedDict
from typing import Optional, List

from pandas import DataFrame

from v0.relationalai import Config
from v0.relationalai.early_access.dsl.core.namespaces import Namespace
from v0.relationalai.early_access.dsl.core.relations import Relation, RelationSignature, rule, ExternalRelation, \
    AbstractRelation, AbstractRelationSignature
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid, to_pascal_case
from v0.relationalai.util.graph import is_acyclic_graph
from v0.relationalai.early_access.dsl.ontologies.constraints import Unique, Mandatory, Constraint, RoleValueConstraint
from v0.relationalai.early_access.dsl.ontologies.export import Export
from v0.relationalai.early_access.dsl.ontologies.raw_source import RawSource
from v0.relationalai.early_access.dsl.ontologies.relationships import Relationship, Attribute
from v0.relationalai.early_access.dsl.ontologies.subtyping import SubtypeArrow, InclusiveSubtypeConstraint, \
    ExclusiveSubtypeConstraint
from v0.relationalai.early_access.dsl.types.concepts import Concept
from v0.relationalai.early_access.dsl.types.entities import EntityType
from v0.relationalai.early_access.dsl.types.values import ValueType, ValueSubtype
from v0.relationalai.semantics.metamodel.util import OrderedSet


class Model:
    def __init__(
            self,
            name: str,
            is_primary: bool = True,
            dry_run: bool = False,
            config: Optional[Config] = None
    ):
        self.name = name
        self.is_primary = is_primary
        self._dry_run = dry_run
        self._config = config or Config()
        self._value_types = OrderedDict()
        self._entity_types = OrderedDict()
        self._relationships = OrderedDict()
        self._constraints = OrderedSet()
        self._subtype_arrows = OrderedSet()
        self._subtype_constraints = OrderedSet()
        self._relations = OrderedDict()
        self._entity_to_identifier = OrderedDict()
        self._bindable_tables = OrderedDict()
        self._bindings = []
        self._executor = None
        self._rel_executor = None
        self._weaver = None
        self._queries = OrderedSet()
        self._exports = OrderedSet()
        self._raw_sources = OrderedSet()

    def guid(self):
        return generate_stable_uuid(self.name)

    def value_type(self, name: str, *args) -> ValueType:
        name = to_pascal_case(name)
        vt = ValueType(self, name, *args)
        self._validate_type_name(name)
        self._value_types[name] = vt
        return vt

    def value_sub_type(self, name: str, super_type: Type) -> ValueSubtype:
        name = to_pascal_case(name)
        vt = ValueSubtype(self, name, super_type)
        self._validate_type_name(name)
        self._value_types[name] = vt
        return vt

    def entity_type(self, name: str, *args, ref_mode: Optional[str] = None) -> EntityType:
        name = to_pascal_case(name)
        et = EntityType(self, name, *args, ref_schema_name=ref_mode)
        self._validate_type_name(name)
        self._entity_types[name] = et
        # in case of a single argument, we generate an identifier relationship
        if len(args) == 1:
            vt = args[0]
            self._generate_id_relationship(et, vt, ref_mode)
        elif len(args) > 1 and ref_mode is not None:
            raise Exception('Reference mode cannot be specified with composite reference schemas')
        return et

    def _generate_id_relationship(self, et: EntityType, vt: Type, refmode: Optional[str] = None):
        """
        Creates an identifier relationship with two readings:
        - {value:vt} identifies {entity:et}
        - {entity:et} has {value:vt} | name=refmode|'id'

        Does not create one in case of a composite identifier (i.e. `len(args) > 1`). In that case, the user should
        manually create the preferred identifier constraint.
        """
        refmode = refmode or 'id'
        with self.relationship() as rel:
            rel._set_identifier()
            rel.role(et)
            rel.role(vt, primary_key=True)
            rel.relation(rel.role_at(0), 'is identified by', rel.role_at(1), name=refmode, functional=True)
            rel.relation(rel.role_at(1), 'identifies', rel.role_at(0), functional=True)
        self._entity_to_identifier[et] = rel

    def concept(self, name: str, extends: Optional[Type]=None) -> Concept:
        name = to_pascal_case(name)
        vt = Concept(self, name, extends)
        self._validate_type_name(name)
        self._value_types[name] = vt
        return vt

    def entity_sub_type(self, name: str, super_type: Type) -> EntityType:
        et = self.entity_type(name)
        self.subtype_arrow(super_type, [et])
        return et

    def exclusive_entity_type(self, name: str, *args) -> EntityType:
        et = self.entity_type(name)
        self.subtype_arrow(et, list(args), exclusive=True)
        return et

    def inclusive_entity_type(self, name: str, *args) -> EntityType:
        et = self.entity_type(name)
        self.subtype_arrow(et, list(args), inclusive=True)
        return et

    def subtype_arrow(self, type: Type, sub_types:list[Type], exclusive=False, inclusive=False) -> OrderedSet[SubtypeArrow]:
        arrows = OrderedSet()
        for sub in sub_types:
            # For example: AdminAccount -> Account
            a = SubtypeArrow(sub, type)
            arrows.add(a)
            self._subtype_arrows.add(a)
            if isinstance(type, EntityType) and isinstance(sub, EntityType):
                # TODO: [AN]: we generate these relations to be compatible with SLS. We need to get rid of subtype relationship notion from ontology later.
                self._generate_subtype_relationship(sub, type)
                # use parent's constructor if there is no override (empty domain)
                if sub._constructor is None and len(sub.domain()) == 0:
                    sub._constructor = type.constructor()
        self._validate_cyclic_arrows()
        if exclusive:
            self._subtype_constraints.add(ExclusiveSubtypeConstraint(arrows))
        if inclusive:
            self._subtype_constraints.add(InclusiveSubtypeConstraint(arrows))
        return arrows

    def exclusive_subtype_constraint(self, *arrows: SubtypeArrow) -> ExclusiveSubtypeConstraint:
        cnstr = ExclusiveSubtypeConstraint(OrderedSet.from_iterable(arrows))
        self._subtype_constraints.add(cnstr)
        return cnstr

    def inclusive_subtype_constraint(self, *arrows: SubtypeArrow) -> InclusiveSubtypeConstraint:
        cnstr = InclusiveSubtypeConstraint(OrderedSet.from_iterable(arrows))
        self._subtype_constraints.add(cnstr)
        return cnstr

    def relationship(self, *args, relation_name: Optional[str] = None) -> Relationship:
        """
        Create a new relationship with the given reading.
        'args' contains Sequence of Types followed by text fragments.
        """
        return Relationship(self, *args, relation_name=relation_name)

    def identifier_of(self, entity_type: EntityType):
        return self._entity_to_identifier.get(entity_type)

    def external_relation(self, name: str, *sig: Type, namespace: Namespace = Namespace.top,
                          functional: bool = False) -> AbstractRelation:
        """
        Create a new external relation with the given namespace, name and signature.
        """
        return self._add_relation(
            ExternalRelation(namespace, name, RelationSignature(*sig, functional=functional)))

    def attribute(
            self,
            concept,
            attr,
            mandatory: bool = False,
            primary_key: bool = False,
            reading_text: Optional[str] = None,
            reverse_reading_text: Optional[str] = None
    ) -> Attribute:
        """
        Creates a new attribute relationship with the given parameters.

        Parameters:
            concept: The concept the attribute is associated with.
            attr: The entity type or value type playing the attribute role.
            mandatory (bool, optional): Whether the concept's role in this relationship is mandatory. Defaults to False.
            primary_key (bool, optional): Whether the attribute is a preferred identifier for the concept. Defaults to False.
            reading_text (str, optional): The forward reading description of the relationship (e.g., "is classified by").
            reverse_reading_text (str, optional): The reverse reading description of the relationship (e.g., "classifies").

        Example:
            # Equivalent logic:

            rel = model.relationship(concept, 'has', attr)
            rel.relation(rel.role_at(1), reverse_reading_text, rel.role_at(0), name=reverse_rel_name)
            model.unique(rel.concept)
            model.mandatory(rel.concept)

        Returns:
            Attribute: The newly created attribute relationship.
        """
        return Attribute(
            model=self,
            concept=concept,
            attr=attr,
            mandatory=mandatory,
            primary_key=primary_key,
            reading_text=reading_text,
            reverse_reading_text=reverse_reading_text
        )

    def constraint(self, constraint):
        # Generic constraint addition with validation
        self._validate_constaint_roles(constraint)
        self._constraints.add(constraint)

    def role_value_constraint(self, relation:Relation, values:List[str]):
        if not relation.binary():
            raise Exception("The relation should be binary to apply role value constraint")
        type = relation.first()
        if not isinstance(type, EntityType):
            raise Exception("A role value constraint can only be applied to roles played by entities")
        for val in values:
            rel = type.entity_instance_relation(val)
            self._add_relation(rel)
            with type.__dict__[val]:
                @rule()
                def r(v): type^(val, v)

        self._constraints.add(RoleValueConstraint(relation.reading().roles[1], values))

    # Syntactic sugar methods
    def unique(self, *roles):
        self.constraint(Unique(*roles))

    def ref_scheme(self, *relations:Relation):
        self._validate_ref_scheme_input_relations(relations)
        if len(relations) == 1:
            # binary case, internal UC
            role = relations[0].reading().roles[1]
            self._internal_preferred_uc(role)
        else:
            roles = [rel.reading().roles[1] for rel in relations]
            self._composite_preferred_uc(*roles)

    @staticmethod
    def _validate_ref_scheme_input_relations(relations):
        if not relations:
            raise ValueError("ref_scheme requires at least one relation")
        ref_rel = relations[0]
        for rel in relations:
            if not isinstance(rel, Relation):
                raise ValueError("ref_scheme can only be applied on Relation instances")
            if rel.arity() != 2:
                raise ValueError("ref_scheme can only be applied on binary relations")
            if rel.first() != ref_rel.first():
                raise ValueError("For ref_scheme all relations must have the same role player in position 0")

    def _internal_preferred_uc(self, role):
        rel = role.part_of
        if rel.arity() != 2:
            raise Exception("The relationship should be binary to apply preferred identifier constraint")
        # mark the role as preferred identifier
        self.constraint(Unique(role, is_preferred_identifier=True))
        # mark the sibling role as mandatory and unique
        sibling = role.sibling()
        sibling_player = sibling.player()
        # update the domain of the entity type with the identifier
        if len(sibling_player.domain()) > 0:
            raise Exception(f"The preferred uc has already been set for entity type {sibling_player.display()}")
        sibling_player.domain().append(role.player_type)
        self.mandatory(sibling)
        self.unique(sibling)
        self._entity_to_identifier[sibling_player] = rel

    def _composite_preferred_uc(self, *roles):
        sibling = None
        for role in roles:
            sibling = role.sibling()
            if not sibling:
                raise Exception("Composite preferred identifier constraint should be applied on binary relationships")
            # update the domain of the entity type with the identifiers
            if len(sibling.player_type.domain()) > len(roles):
                raise Exception(f"The preferred uc has already been set for entity type {sibling.player_type.display()}")
            sibling.player_type.domain().append(role.player_type)
            self.mandatory(sibling)
            self.unique(sibling)
        pref_uc = Unique(*roles, is_preferred_identifier=True)
        self.constraint(pref_uc)
        if sibling is None:
            raise Exception("Composite preferred identifier constraint should be applied on binary relationships")
        self._entity_to_identifier[sibling.player()] = pref_uc

    def mandatory(self, role):
        self.constraint(Mandatory(role))

    def lookup_concept(self, name) -> Optional[Type]:
        name = to_pascal_case(name)
        if name in self._value_types:
            return self._value_types[name]
        if name in self._entity_types:
            return self._entity_types[name]
        return None

    def lookup_relationship(self, name) -> Optional[Relationship]:
        if name in self._relationships:
            return self._relationships[name]
        return None

    def query(self, *sig: Type):
        rel = ExternalRelation(Namespace.top, "output", RelationSignature(*sig))
        self._queries.add(rel)
        return rel

    def export(self, key: list[Type], into: str) -> Export:
        export = Export(key, into)
        self._exports.add(export)
        return export

    def exports(self):
        return self._exports

    def raw_sources(self):
        return self._raw_sources

    def constraints(self):
        """Getter for the _constraints property"""
        return self._constraints

    def subtype_constraints(self):
        """Getter for the _subtype_constraints property"""
        return self._subtype_constraints

    def subtype_arrows(self):
        return self._subtype_arrows

    def queries(self):
        return self._queries

    def value_types(self):
        return list(self._value_types.values())

    def entity_types(self):
        return list(self._entity_types.values())

    def entity_types_map(self):
        return self._entity_types

    def relationships(self):
        return list(self._relationships.values())

    def relations(self):
        return list(self._relations.values())

    def bindable_tables(self):
        return self._bindable_tables

    @staticmethod
    def _declare_subtype_rules(super_type, sub_types):
        with super_type:
            for sub in sub_types:
                @rule()
                def r(t):
                    sub(t)

    def _to_rel_executor(self):
        if not self._rel_executor:
            from v0.relationalai.early_access.dsl.ir.executor import RelExecutor
            self._rel_executor = RelExecutor(
                self.name,
                dry_run=self._dry_run,
                config=self._config,
            )
        return self._rel_executor

    def execute(self, result_cols: Optional[List[str]] = None) -> DataFrame:
        return self._to_rel_executor().execute_model(self, result_cols)

    def _add_rel_raw_source(self, source_name: str, raw_source: str):
        self._raw_sources.add(RawSource("rel", source_name, raw_source))

    def pprint(self) -> str:
        result = [f"Model: {self.name} (Primary: {self.is_primary})"]
        result.append("\nValue Types:")
        for vt in self._value_types.values():
            result.append(f"  {vt.pprint()}")
        result.append("\nEntity Types:")
        for et in self._entity_types.values():
            result.append(f"  {et.pprint()}")
        result.append("\nRelationships:")
        for rel in self._relationships.values():
            result.append(f"  {rel.pprint()}")
        result.append("\nSubtype Arrows:")
        for arrow in self._subtype_arrows:
            result.append(f"  {arrow.pprint()}")
        return "\n".join(result)

    def _add_relationship(self, rel: Relationship):
        self._validate_relationship_name(rel._name())
        self._relationships[rel._name()] = rel

    def _add_relation(self, relation: AbstractRelation) -> AbstractRelation:
        if relation.entityid() in self._relations:
            existed_relation = self._relations[relation.entityid()]
            self._validate_relation(existed_relation, relation.signature())
            return existed_relation
        self._relations[relation.entityid()] = relation
        return relation

    def _validate_type_name(self, name):
        if name in self._entity_types:
            raise Exception(
                f"The name '{name}' is used to declare an entity type.")
        if name in self._value_types:
            raise Exception(
                f"The name '{name}' is used to declare a value type.")

    def _validate_relationship_name(self, name):
        if name in self._relationships:
            raise Exception(
                f"The name '{name}' is used to declare a relationship.")

    def _validate_relation(self, relation: Relation, requested_sig: AbstractRelationSignature):
        if len(requested_sig._types) != len(relation._signature._types):
            raise Exception(
                f"The relation '{relation.qualified_name()}' already exists but provided signature arity doesn't match.")
        for idx in range(len(relation._signature._types)):
            existing_arg = relation._signature._types[idx]
            requested_arg = requested_sig._types[idx]
            if existing_arg != requested_arg:
                raise Exception(
                    f"The relation '{relation.qualified_name()}' already exists but existing signature "
                    f"{relation.signature().display()} doesn't match with provided {requested_sig.display()}.")

    def _validate_constaint_roles(self, constraint: Constraint):
        for role in constraint.roles():
            if role.part_of.is_empty():
                raise Exception(
                    f"Failed add constraint {constraint}. Role {role.ref_name()} is part of relation without readings.")

    def _validate_cyclic_arrows(self):
        if not is_acyclic_graph(list(self._entity_types.keys()), list(map(lambda a: a.to_name_tuple(), self._subtype_arrows))):
            raise Exception("Failed to add subtype arrow. The model graph should be acyclic.")

    def _generate_subtype_relationship(self, entity_type, super_type):
        rel = self.relationship()
        (
            rel._set_subtype()
                .role(super_type, unique=True)
                .role(entity_type, unique=True, mandatory=True)
                .relation(rel.role_at(1), "is a subtype of", rel.role_at(0))
        )
