import runpy

from v0.relationalai.early_access.dsl.core.types.standard import standard_value_types
from v0.relationalai.early_access.dsl.bindings.legacy import binding_models
from v0.relationalai.early_access.dsl.ontologies import models, constraints
from v0.relationalai.early_access.dsl.serialize.binding_model import BindingModelObject, BindingObject, BoundRole, BoundAttribute, \
    DataTransformerApplication, DataTransformer, EntityMapRef, Pattern
from v0.relationalai.early_access.dsl.serialize.model import ValueType, ModelObject, DataType, EntityType, Role, Reading, SubtypeArrow, \
    Relationship,UniqueConstraint, MandatoryConstraint, Model, Constraints, Concepts

ENTITY_PATTERN_NAME = 'Entity'


def export_models(ontology_paths) -> list[ModelObject]:
    result = []

    # Add standard Data Types
    data_types_list = []
    for vt in standard_value_types.values():
        data_types_list.append(DataType(id=vt.guid(), name=vt.display()))

    # Scan for Models in given paths
    for path in ontology_paths:
        module_globals = runpy.run_path(path)
        value_types_list = []
        entity_types_list = []
        relationships_list = []
        subtype_arrows_list = []
        has_primary = False
        for var in module_globals:
            obj = module_globals[var]
            if isinstance(obj, models.Model):
                if has_primary and obj.is_primary:
                    raise ValueError('Only one primary model per ontology is allowed.')
                if obj.is_primary:
                    has_primary = True

                uniqueness_list = []
                mandatory_list = []

                for vt in obj._value_types.values():
                    decl = vt._params[0].decl
                    value_types_list.append(
                        ValueType(id=vt.guid(), name=vt.display(), data_type=decl.guid(), data_type_name=decl.display()))

                for et in obj._entity_types.values():
                    entity_types_list.append(
                        EntityType(id=et.guid(), name=et.display(), domain=list(map(lambda d: d.display(), et._domain))))

                for rel in obj._relationships.values():
                    rel_roles = []
                    for role in rel._rolemap.values():
                        rel_roles.append(
                            Role(id=role.guid(), name=role.name(), role_player=role.player().guid(),
                                 role_player_name=role.player().display(),
                                 pre_bound_text=role._prefix,
                                 post_bound_text=role._postfix))

                    rel_readings = []
                    for reading in rel.readings():
                        rel_readings.append(Reading(id=reading.guid(), text=reading.template(),
                                                    roles=list(map(lambda r: r.guid(), reading.roles))))

                    relationships_list.append(
                        Relationship(id=rel.guid(), name=rel._name(), roles=rel_roles, readings=rel_readings,
                                     is_subtype=rel._is_subtype))

                for c in obj._constraints:
                    if isinstance(c, constraints.Unique):
                        uniqueness_list.append(
                            UniqueConstraint(id=c.guid(), roles=list(map(lambda r: r.guid(), c.roles())),
                                             is_preferred_identifier=c.is_preferred_identifier))
                    elif isinstance(c, constraints.Mandatory):
                        mandatory_list.append(MandatoryConstraint(id=c.guid(), roles=[c.role.guid()]))

                for a in obj._subtype_arrows:
                    subtype_arrows_list.append(
                        SubtypeArrow(id=a.guid(), start=a.start.guid(), end=a.end.guid(), start_name=a.start.display(),
                                     end_name=a.end.display()))

                result.append(ModelObject(model=Model(id=obj.guid(), name=obj.name, is_primary=obj.is_primary,
                                                      concepts=Concepts(value_types=value_types_list,
                                                                        entity_types=entity_types_list),
                                                      relationships=relationships_list,
                                                      constraints=Constraints(uniqueness=uniqueness_list,
                                                                              mandatory=mandatory_list),
                                                      data_types=data_types_list,
                                                      subtype_arrows=subtype_arrows_list)))
    return result


def export_model_json(ontology: list[ModelObject]) -> str:
    return ModelObject.schema().dumps(ontology, many=True) # type: ignore


def export_binding_model(binding_model_path) -> BindingModelObject:
    module_globals = runpy.run_path(binding_model_path)
    binding_list = []
    data_transformer_list = []
    # Reification pattern support is a TODO
    pattern_list = []
    entity_map_list = []
    for var in module_globals:
        obj = module_globals[var]
        if isinstance(obj, binding_models.BindingModel):
            for b in obj._bindings:
                ro = b.role
                col = b.column
                attr = BoundAttribute(
                    name=col.name,
                    source=col.part_of.name,
                    hasValue=b.has_value,
                ) if col is not None else None
                bo = BindingObject(
                    id=b.guid(),
                    role=BoundRole(
                        player=ro.player_type._name,
                        relationship=ro.part_of._name(),
                        entityMapRef=b.entity_map.name if b.entity_map is not None else None),
                    attribute=attr,
                )
                # Filter out potential None values then flatten the list first if it becomes (single) nested
                b._applied_transformations = list(filter(lambda x: x is not None, b._applied_transformations))
                b._applied_transformations = [item for sublist in b._applied_transformations for item in sublist]
                if b._applied_transformations and len(b._applied_transformations) > 0:
                    bo.transformations = list(
                        map(
                            lambda t: DataTransformerApplication(transformer=t._relname),
                            b._applied_transformations
                        )
                    )
                binding_list.append(bo)
            data_transformer_list = list(map(
                lambda kv: DataTransformer(
                    name=kv[0],
                    sourceType=kv[1][0]._name.upper(),
                    targetType=kv[1][1]._name.upper()
                ),
                obj._transformers.items()
            ))
            entity_map_list = list(map(
                lambda kv: EntityMapRef(
                    name=kv.name,
                    source=kv.source.name,
                    entityType=kv.entity_type._name,
                    relation=kv.relation.qualified_name()
                ),
                obj._entity_maps.values()
            ))
            pattern_list = list(map(
                lambda kv: Pattern(
                    conceptName=kv[0].__name__,
                    # We use a little different naming convention for entity reificaiton pattern
                    pattern=kv[1].__name__.replace(EntityType.__name__, ENTITY_PATTERN_NAME)
                ),
                obj._patterns.items()
            ))
    return BindingModelObject(bindings=binding_list, patterns=pattern_list, dataTransformers=data_transformer_list,
                              entityMaps=entity_map_list)


def export_binding_model_json(binding_model: BindingModelObject) -> str:
    return BindingModelObject.schema().dumps(binding_model) # type: ignore
