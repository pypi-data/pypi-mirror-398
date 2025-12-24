import re
import warnings

from v0.relationalai.early_access.dsl.adapters.owl.model import OWLClass
from v0.relationalai.early_access.dsl.adapters.owl.parser import OWLParser
from v0.relationalai.early_access.dsl.core.types.standard import String, Float, Integer, Date, DateTime
from v0.relationalai.early_access.dsl.core.utils import to_pascal_case
from v0.relationalai.early_access.dsl.ontologies.models import Model
from datetime import datetime, date


class OwlAdapter:
    _reading_pattern = re.compile(r'(?<!^)(?=[A-Z])')

    def __init__(self, owl_file_path: str):
        self._parser = OWLParser(owl_file_path)
        self.model = self.owl_to_model()

    def owl_to_model(self):
        model = Model(self._parser.ontology_name() + "Model")
        # IRI ValueType declaration - this will be used as preferred identifier for all entity types
        iri = model.value_type("IRI", String)
        # OWL Things Entity declaration - all the root classes will be subtype of OWL Thing
        model.entity_type("OWLThing", iri)
        self._add_classes(model)
        self._add_sub_classes(model)
        self._add_object_properties(model)
        self._add_datatype_properties(model)
        return model

    def _add_classes(self, model):
        for owl_class in self._parser.classes().values():
            if self._validate_class(owl_class):
                model.entity_type(owl_class.name)

    def _add_sub_classes(self, model):
        owl_thing_entity = model.lookup_concept("OWLThing")
        owl_thing_subclasses = []
        for owl_class in self._parser.classes().values():
            # Classes that do not have any super type are identified by the IRI value type
            # Re-declaring the identifier here even if it is technically inherited from OWL Thing as this
            # class is just a placeholder, and we might drop it later
            class_entity = model.lookup_concept(owl_class.name)
            if class_entity is not None:
                subtype_entities = self._subtype_entities(model, owl_class)
                # Check for inclusive or exclusive type arrows
                if self._parser.is_partitioned_into_disjoint_subclasses(owl_class):
                    model.subtype_arrow(class_entity, subtype_entities, True, True)
                elif self._parser.is_partitioned_into_subclasses(owl_class):
                    model.subtype_arrow(class_entity, subtype_entities, False, True)
                elif owl_class.children is not None:
                    model.subtype_arrow(class_entity, subtype_entities)

                if self._parser.is_root_class(owl_class):
                    owl_thing_subclasses.append(class_entity)

        if owl_thing_entity is not None:
            model.subtype_arrow(owl_thing_entity, owl_thing_subclasses)

    # Object Properties
    def _add_object_properties(self, model):
        for object_property in self._parser.object_properties().values():
            # In OWL, in general domains and ranges can be defined as union or intersection of multiple classes.
            # This has no direct translation to our model, thus we can only cover the cases where the domains and
            # ranges are single expression. We need to check for this here.
            if self._validate_property(object_property):
                domain = object_property.domain[0]
                domain_entity = model.lookup_concept(domain)
                range = object_property.range[0]
                range_entity = model.lookup_concept(range)

                inv_rel_name = ""
                if object_property.inverse_property is not None:
                    inv_rel_name = range.capitalize() + to_pascal_case(object_property.inverse_property) + domain.capitalize()
                inv_rel_entity = model.lookup_relationship(inv_rel_name)

                if inv_rel_entity is None:
                    with model.relationship() as rel:
                        # Check for functionality and mandatory participation for the domain
                        if self._is_mandatory_for_class(object_property, domain) and object_property.functional:
                            rel.role(domain_entity, mandatory=True, unique=True)
                        elif object_property.functional:
                            rel.role(domain_entity, unique=True)
                        else:
                            rel.role(domain_entity, name=object_property.name)
                        # Check for functionality and mandatory participation for the range
                        if self._is_inverse_mandatory_for_class(object_property, range) and object_property.inverse_functional:
                            rel.role(range_entity, mandatory=True, unique=True)
                        elif object_property.inverse_functional:
                            rel.role(range_entity, unique=True)
                        else:
                            rel.role(range_entity)

                    # Readings
                    rel.relation(rel.role_at(0), self._get_reading(object_property.name), rel.role_at(1))
                    if object_property.inverse_property is not None:
                        rel.relation(rel.role_at(1), self._get_reading(object_property.inverse_property), rel.role_at(0))

                    if not object_property.functional and not object_property.inverse_functional:
                        model.unique(rel.role_at(0), rel.role_at(1))

    # Datatype Properties
    def _add_datatype_properties(self, model):
        for datatype_property in self._parser.datatype_properties().values():
            if self._validate_property(datatype_property):

                data_type_entity = model.lookup_concept(datatype_property.name)
                if data_type_entity is None:
                    r = datatype_property.range[0]
                    xsd_type = self._xsd_type_to_rel_type(r)
                    data_type_entity = model.value_type(datatype_property.name, xsd_type)

                d = datatype_property.domain[0]
                domain_entity = model.lookup_concept(d)

                with model.relationship(domain_entity, "has", data_type_entity) as rel:
                    model.unique(rel.role_at(0), rel.role_at(1))

    @staticmethod
    def _subtype_entities(model, owl_class: OWLClass):
        subtype_entities = []
        if owl_class.children is not None:
            for sub_class in sorted(owl_class.children):
                subtype_entity = model.lookup_concept(sub_class)
                if subtype_entity is not None:
                    subtype_entities.append(subtype_entity)
        return subtype_entities

    @staticmethod
    def _validate_class(owl_class: OWLClass):
        if owl_class.parents is not None and len(owl_class.parents) > 1:
            warnings.warn(f"{str(owl_class)} has multiple parents")
            return False
        else:
            return True

    @staticmethod
    def _validate_property(owl_property):
        if not owl_property.domain or len(owl_property.domain) == 0:
            warnings.warn(f"Missing domain for {owl_property.name}, it won't be translated.")
            return False
        elif len(owl_property.domain) > 1:
            warnings.warn(
                f"Unsupported complex expression in the domain of {owl_property.name}, it won't be translated.")
            return False
        elif not owl_property.range or len(owl_property.range) == 0:
            warnings.warn(f"Missing range for {owl_property.name}, it won't be translated.")
            return False
        elif len(owl_property.range) > 1:
            warnings.warn(
                f"Unsupported complex expression in the range of {owl_property.name}, it won't be translated.")
            return False
        else:
            return True

    def _is_mandatory_for_class(self, owl_property, owl_class):
        c = self._parser.classes()[owl_class]
        return c.mandatory_properties and owl_property.name in c.mandatory_properties

    def _is_inverse_mandatory_for_class(self, owl_property, owl_class):
        c = self._parser.classes()[owl_class]
        return c.mandatory_properties and owl_property.name in c.inverse_mandatory_properties

    def _get_reading(self, relationship_name: str):
        return self._reading_pattern.sub(' ', relationship_name).lower()

    @staticmethod
    def _xsd_type_to_rel_type(tp):
        mapping = {
            str: String,
            int: Integer,
            float: Float,
            date: Date,
            datetime: DateTime
        }
        return mapping.get(tp, String)
