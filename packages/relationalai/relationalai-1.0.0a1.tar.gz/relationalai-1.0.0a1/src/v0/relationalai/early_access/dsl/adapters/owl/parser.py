import re
import warnings

from owlready2 import owl, get_ontology
from v0.relationalai.early_access.dsl.adapters.owl.model import OWLClass, OWLObjectProperty, OWLDatatypeProperty


class OWLParser:
    _inverse_pattern = re.compile(r'Inverse\((.*?)\)')
    _disjoint_pattern = re.compile(r'Not\((.*?)\)')

    def __init__(self, owl_file_path):
        self._ontology = get_ontology(owl_file_path).load()
        self._ontology_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._ontology.name).lower()
        self._prefix = f"{self._ontology.name}."
        self._classes = self._parse_classes()
        self._parse_subclasses()
        self._object_properties = self._parse_object_properties()
        self._datatype_properties = self._parse_datatype_properties()

    def ontology(self):
        return self._ontology

    def ontology_name(self):
        return self._ontology_name

    def classes(self):
        return self._classes

    def object_properties(self):
        return self._object_properties

    def datatype_properties(self):
        return self._datatype_properties

    def _parse_classes(self):
        owl_classes = {}
        for ontology_class in self._ontology.classes():
            class_name = self._clean_name(str(ontology_class))
            owl_classes[class_name] = OWLClass(class_name)
        return owl_classes

    def _parse_subclasses(self):
        for owl_class in self._ontology.classes():
            class_name = self._clean_name(str(owl_class))
            parents = set()
            children = set()
            for sub_class in list(owl_class.subclasses()):
                sub_class_name = self._clean_name(str(sub_class))
                parents.add(class_name)
                children.add(sub_class_name)
                if len(parents) > 0:
                    if self._classes[sub_class_name].parents is not None:
                        self._classes[sub_class_name].parents.update(parents)
                    else:
                        self._classes[sub_class_name].parents = parents
            if len(children) > 0:
                self._classes[class_name].children = children
            self._parse_class_partition(owl_class)
            self._parse_disjoint_classes(owl_class)
            self._parse_mandatory_constraints(owl_class)

    def _parse_object_properties(self):
        object_properties = {}
        for object_property in self._ontology.object_properties():
            object_property_name = self._clean_name(str(object_property))
            owl_object_property = OWLObjectProperty(object_property_name, [], [])
            for domain_class in object_property.domain:
                owl_object_property.domain.append(self._clean_name(str(domain_class)))
            for range_class in object_property.range:
                owl_object_property.range.append(self._clean_name(str(range_class)))
            if object_property.inverse_property is not None:
                inverse_property_name = self._clean_name(str(object_property.inverse_property))
                owl_object_property.inverse_property = inverse_property_name
            if self._is_functional(object_property):
                owl_object_property.functional = True
            if self._is_inverse_functional(object_property):
                owl_object_property.inverse_functional = True
            object_properties[object_property_name] = owl_object_property
        return object_properties

    def _parse_datatype_properties(self):
        datatype_properties = {}
        for datatype_property in self._ontology.data_properties():
            datatype_property_name = self._clean_name(str(datatype_property))
            datatype_properties[datatype_property_name] = OWLDatatypeProperty(datatype_property_name, [], [])
            for domain_class in datatype_property.domain:
                datatype_properties[datatype_property_name].domain.append(self._clean_name(str(domain_class)))
            for range_iri in datatype_property.range:
                datatype_properties[datatype_property_name].range.append(range_iri)
            if self._is_functional(datatype_property):
                datatype_properties[datatype_property_name].functional = True
        return datatype_properties

    def _parse_mandatory_constraints(self, owl_class):
        class_name = self._clean_name(str(owl_class))
        mandatory_properties = set()
        inverse_mandatory_properties = set()
        for isa in owl_class.is_a:
            if "some" in str(isa):
                match = self._inverse_pattern.search(str(isa.property))
                if match:
                    result = match.group(1)
                    inverse_mandatory_properties.add(self._clean_name(result))
                else:
                    mandatory_properties.add(self._clean_name(str(isa.property)))
        if len(mandatory_properties) > 0:
            self._classes[class_name].mandatory_properties = mandatory_properties
        if len(inverse_mandatory_properties) > 0:
            self._classes[class_name].inverse_mandatory_properties = inverse_mandatory_properties

    def _parse_class_partition(self, owl_class):
        owl_class_name = self._clean_name(str(owl_class))
        partition = set()
        for equivalent_class in owl_class.equivalent_to:
            if "&" in str(equivalent_class):
                warnings.warn(f"Unable to parse complex expression: {owl_class_name} equivalent to {owl_class.equivalent_to}. Skipping this axiom")
            elif "|" in str(equivalent_class):
                for partition_class in equivalent_class.Classes:
                    partition.add(self._clean_name(str(partition_class)))
        if len(partition) > 0:
            self._classes[owl_class_name].partition = partition

    def _parse_disjoint_classes(self, owl_class):
        owl_class_name = self._clean_name(str(owl_class))
        disjoints = set()
        for isa in owl_class.is_a:
            match = self._disjoint_pattern.search(str(isa))
            if match:
                disjoints.add(self._clean_name(match.group(1)))
        if len(disjoints) > 0:
            self._classes[owl_class_name].disjoint = disjoints

    def _clean_name(self, name):
        return name.removeprefix(self._prefix)

    @staticmethod
    def _is_functional(object_property):
        return owl.FunctionalProperty in object_property.is_a

    @staticmethod
    def _is_inverse_functional(object_property):
        return owl.InverseFunctionalProperty in object_property.is_a

    def is_partitioned_into_disjoint_subclasses(self, owl_class: OWLClass):
        if owl_class.partition is not None:
            for sub_class in owl_class.partition:
                disjoint = self._classes[sub_class].disjoint
                if disjoint is not None and owl_class.partition.difference(disjoint) != {sub_class}:
                    return False
            return True
        return False

    @staticmethod
    def is_partitioned_into_subclasses(owl_class: OWLClass):
        return owl_class.partition is not None

    @staticmethod
    def is_root_class(owl_class: OWLClass):
        return owl_class.parents is None
