import dataclasses
from typing import Optional

from v0.relationalai.early_access.dsl.core.namespaces import Namespace
from v0.relationalai.early_access.dsl.core.relations import Relation, RelationSignature
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.utils import generate_stable_uuid
from v0.relationalai.early_access.dsl.ontologies.relationships import Relationship
from v0.relationalai.early_access.dsl.ontologies.roles import Role
from v0.relationalai.early_access.dsl.physical_metadata.tables import Column, Table, TemporalTable
from v0.relationalai.early_access.dsl.types.entities import EntityType
from v0.relationalai.early_access.dsl.types.values import ValueType

from v0.relationalai.early_access.dsl import ExternalRelation


@dataclasses.dataclass
class EntityMapRef:
    name: str
    source: Table
    entity_type: EntityType
    relation: Relation


@dataclasses.dataclass
class ReificationPattern:
    concept: type
    reifies_as: type


class Binding:

    def __init__(self, role: Role, column: Optional[Column] = None, entity_map: Optional[EntityMapRef] = None):
        self._role = role
        self._column = column
        self._entity_map = entity_map
        self._has_value: Optional[str] = None
        self._applied_transformations = []
        self._check_either_column_or_entity_map_provided()

    def guid(self):
        salt = self._column.guid() if self._column is not None else self._entity_map.name if self._entity_map is not None else None
        return generate_stable_uuid(f"{salt}_{self._role.guid()}")

    def transform(self, transformer: Relation):
        self._applied_transformations.append(transformer)
        return self

    @property
    def role(self):
        return self._role

    @property
    def column(self):
        return self._column

    @property
    def entity_map(self):
        return self._entity_map

    @property
    def has_value(self) -> Optional[str]:
        return self._has_value

    @has_value.setter
    def has_value(self, value: str):
        if value is not None:
            self._has_value = value
            Binding._check_has_value_applicable(self._role.part_of)

    def __str__(self):
        binds_to = self._column.pprint() if self._column is not None else self._entity_map.name if self._entity_map is not None else None
        return f"{self._role.verbalize()}: {binds_to}"

    def _check_either_column_or_entity_map_provided(self):
        if self._column is None and self._entity_map is None:
            raise Exception("Either a column or an entity map must be provided")

    @staticmethod
    def _check_has_value_applicable(relationship):
        if not (relationship.arity() == 1 or relationship.is_subtype()):
            raise Exception(
                f"The 'has_value' setting requires a unary or a subtype relationship, "
                f"but non-subtype relationship '{relationship.name()}' has arity {relationship.arity()}")


class BindingModel:
    def __init__(self):
        self._bindings = []
        self._patterns = {}
        self._transformers = {}
        self._entity_maps = {}

    def bind_role(self, role: Role, column: Optional[Column] = None, entity_map: Optional[EntityMapRef] = None,
                  data_transformers: Optional[list[Relation]] = None, has_value: Optional[str] = None):
        if column is not None and isinstance(column.part_of, TemporalTable):
            if column.part_of.temporal_col.name not in column.part_of.columns:
                raise Exception(f"Cannot bind attribute {column.name} of TemporalTable {column.part_of.name} as it uses"
                                f" missing temporal column: column {column.part_of.temporal_col} is not in the table")
        b = Binding(role, column, entity_map)
        self._register_transformations(b, data_transformers)
        b._has_value = has_value
        self._bindings.append(b)
        return b

    def bind_attribute(self, relationship: Relationship, column: Column,
                       data_transformers: Optional[list[Relation]] = None, has_value: Optional[str] = None):
        b = Binding(relationship.attr(), column)
        self._register_transformations(b, data_transformers)
        b._has_value = has_value
        self._bindings.append(b)
        return b

    def transformer(self, name: str, sig: tuple[Type, Type]):
        self._transformers[name] = sig
        signature = RelationSignature(*sig)
        t = ExternalRelation(Namespace.top, name, signature)
        if len(sig) < 2:
            raise Exception(f"Signature \"{sig}\" provided for the relation {name} used as transformer must be exactly"
                            f" a tuple of two types (source type [0] and target type [1])")
        return t

    def entity_map(self, name: str, source: Table, entity_type: EntityType, relation: Relation):
        emap = EntityMapRef(name, source, entity_type, relation)
        if name in self._entity_maps:
            raise Exception(f"Entity map reference with name {name} already declared")
        self._entity_maps[name] = emap
        return emap

    def pattern(self, concept: type, reifies_as: type):
        if type is not EntityType or type is not ValueType:
            raise Exception(f"Reification pattern must use EntityType or ValueType, but for {concept} got {reifies_as}")
        self._patterns[concept] = reifies_as
        return ReificationPattern(concept, reifies_as)

    def pprint(self):
        return "\n".join([str(b) for b in self._bindings])

    @staticmethod
    def _register_transformations(b: Binding, *transformations):
        if transformations is not None:
            for t in transformations:
                b.transform(t)
