import typing

from v0.relationalai.early_access.dsl.orm.printer import Printer, _sort_dependency_graph, InterfacePrinter
from v0.relationalai.early_access.dsl.orm.models import Model
from v0.relationalai.early_access.dsl.orm.types import Concept

SPACE_INDENT = "    "
TAB_INDENT = "\t"

class ObjectOrientedPrinter(Printer):
    _indent: str

    def __init__(self, io: typing.Optional[typing.IO[str]] = None, space_indent: bool= False):
        super().__init__(io)
        object.__setattr__(self, '_indent', SPACE_INDENT if space_indent else TAB_INDENT)

    def to_string(self, model: Model, enums_enabled: bool = False, pyi_enabled: bool = False) -> None:
        self._process_constraints(model)

        self._print_nl("from typing import Any, Sequence, Union, TypeVar")
        self._print_nl("import relationalai.semantics.internal as qb")
        self._print_nl("import relationalai.semantics.internal.internal as builder")
        self._print_nl("from relationalai.early_access.dsl.orm.models import Model")
        if pyi_enabled:
            self._print_nl("from relationalai.early_access.dsl.orm.models import Concept")
        self._print_nl("from relationalai.early_access.dsl.orm.relationships import Role")
        self._print_nl("from relationalai.early_access.dsl.orm.constraints import Range")
        self._print_nl("from relationalai.early_access.dsl.orm.constraints import RingType")
        self._print_nl("from relationalai.early_access.dsl.orm.constraints import ValueComparisonType")
        self._nl()

        self._handle_concepts_declaration(model, enums_enabled, pyi_enabled)
        self._nl()
        self._print_nl("class OntologyBase:\n"
                       f'{self._indent}"""Represents an Ontology."""')
        self._nl()
        self._print_nl(f"{self._indent}def __init__(self, model: Model):\n"
                       f"{self._indent}{self._indent}self.model = model")
        self._nl()
        self._print_nl(f"{self._indent}def generate_model_rules(self):\n"
                       f"{self._indent}{self._indent}self.model.generate_model_rules()")
        self._nl()
        if not pyi_enabled:
            self._print_nl(f"{self._indent}def Concept(self, name: str, extends: list[Any] = [], identify_by:dict[str, Any]={{}}):\n"
                           f"{self._indent}{self._indent}return self.model.Concept(name, extends, identify_by)")
        if enums_enabled:
            self._print_nl(f"{self._indent}def Enum(self):\n"
                           f"{self._indent}{self._indent}return self.model.Enum()")
        self._print_nl(f"{self._indent}def Relationship(self, reading: Any, short_name:str=\"\") -> qb.Relationship:\n"
                       f"{self._indent}{self._indent}return self.model.Relationship(reading, short_name)")
        self._print_nl(f"{self._indent}def Unique(self, *roles):\n"
                       f"{self._indent}{self._indent}self.model.unique(*roles)")
        self._print_nl(f"{self._indent}def Mandatory(self, role):\n"
                       f"{self._indent}{self._indent}self.model.mandatory(role)")
        self._print_nl(f"{self._indent}T = TypeVar('T', int, float, str)")
        self._print_nl(f"{self._indent}def RoleValueConstraint(self, role: Role, values: Sequence[Union[T, Range[T]]]):\n"
                       f"{self._indent}{self._indent}self.model.role_value_constraint(role, values)")
        self._print_nl(f"{self._indent}def InclusiveSubtypeConstraint(self, *concepts: Concept):\n"
                       f"{self._indent}{self._indent}self.model.inclusive_subtype_constraint(*concepts)")
        self._print_nl(f"{self._indent}def ExclusiveSubtypeConstraint(self, *concepts: Concept):\n"
                       f"{self._indent}{self._indent}self.model.exclusive_subtype_constraint(*concepts)")
        self._print_nl(f"{self._indent}def InclusiveRoleConstraint(self, *roles):\n"
                       f"{self._indent}{self._indent}self.model.inclusive_roles(*roles)")
        self._print_nl(f"{self._indent}def ExclusiveRoleConstraint(self, *role_sequences):\n"
                       f"{self._indent}{self._indent}self.model.exclusive_roles(*role_sequences)")
        self._print_nl(f"{self._indent}def RingConstraint(self, *roles):\n"
                       f"{self._indent}{self._indent}self.model.ring(*roles)")
        self._print_nl(f"{self._indent}def ValueComparisonConstraint(self, constraint_type, *roles):\n"
                       f"{self._indent}{self._indent}self.model.value_comparison(constraint_type, *roles)")
        self._print_nl(f"{self._indent}def RoleSubsetConstraint(self, *role_sequences):\n"
                       f"{self._indent}{self._indent}self.model.role_subset(*role_sequences)")
        self._print_nl(f"{self._indent}def EqualityConstraint(self, *role_sequences):\n"
                       f"{self._indent}{self._indent}self.model.equality(*role_sequences)")
        self._print_nl(f"{self._indent}def FrequencyConstraint(self, frequency, *role_sequences):\n"
                       f"{self._indent}{self._indent}self.model.frequency(frequency, *role_sequences)")
        self._print_nl(
            f"{self._indent}def CardinalityConstraint(self, concept: Concept, values: Sequence[Union[int, Range[int]]]):\n"
            f"{self._indent}{self._indent}self.model.cardinality(concept, values)")
        self._print_nl(f"{self._indent}def RoleCardinalityConstraint(self, role: Role, values: Sequence[Union[int, Range[int]]]):\n"
                       f"{self._indent}{self._indent}self.model.role_cardinality(role, values)")
        self._print_nl(f"{self._indent}def ValueConstraint(self, concept: Concept, values: Sequence[Union[T, Range[T]]]):\n"
                       f"{self._indent}{self._indent}self.model.value_constraint(concept, values)")

        self._nl()
        self._print_nl("class ORMOntology(OntologyBase):")
        self._print_nl(f'{self._indent}"""Represents an Ontology generated from an ORM file."""')
        self._nl()
        self._print_nl(f"{self._indent}def __init__(self, model: Model):")
        self._print_nl(f"{self._indent}{self._indent}super().__init__(model)")
        self._nl()
        self._handle_concepts(model, enums_enabled, pyi_enabled)
        self._nl()
        self._handle_relationships(model)

        self._nl()
        self._handle_ref_schemes(model)

        if self._unique_constraints:
            self._nl()
            self._handle_uniqueness_constraints()

        if self._mandatory_constraints:
            self._nl()
            self._handle_mandatory_constraints()

        if self._role_value_constraints:
            self._nl()
            self._handle_role_value_constraints()

        if self._inclusive_subtype_constraints or self._exclusive_subtype_constraints:
            self._nl()
            self._handle_subtype_constraints()

        if self._inclusive_role_constraints:
            self._nl()
            self._handle_inclusive_role_constraints()

        if self._exclusive_role_constraints:
            self._nl()
            self._handle_exclusive_role_constraints()

        if self._ring_constraints:
            self._nl()
            self._handle_ring_constraints()

        if self._value_comparison_constraints:
            self._nl()
            self._handle_value_comparison_constraints()

        if self._role_subset_constraints:
            self._nl()
            self._handle_role_subset_constraints()

        if self._equality_constraints:
            self._nl()
            self._handle_equality_constraints()

        if self._frequency_constraints:
            self._nl()
            self._handle_frequency_constraints()

        if self._cardinality_constraints:
            self._nl()
            self._handle_cardinality_constraints()

        if self._role_cardinality_constraints:
            self._nl()
            self._handle_role_cardinality_constraints()

        if self._value_constraints:
            self._nl()
            self._handle_value_constraints()

    def _handle_concepts_declaration(self, model: Model, enums_enabled: bool, pyi_enabled: bool) -> None:
        concepts_map = model.concepts_map()
        sorted_concepts = _sort_dependency_graph(model.concepts())
        # print Concept classes
        if pyi_enabled:
            for name in sorted_concepts:
                c = concepts_map.get(name)
                if c is None:
                    raise ValueError(f"The concept '{name}' was not declared but used as concept domain.")
                # skip enums when they are enabled for printer
                if c._is_enum() and enums_enabled:
                    continue
                extends = [f"{e._name}Concept" for e in c._extends if not e._is_primitive()]
                self._print_nl(f"class {name}Concept({', '.join(extends) if extends else 'Concept'}):")
                self._print_nl(f'{self._indent}"""Represents {name} concept."""')
            self._nl()

    def _handle_concepts(self, model: Model, enums_enabled: bool, pyi_enabled: bool) -> None:
        concepts_map = model.concepts_map()
        enums_map = model.enums_map()
        sorted_concepts = _sort_dependency_graph(model.concepts())
        for name in sorted_concepts:
            c = concepts_map.get(name)
            if c is None:
                raise ValueError(f"The concept '{name}' was not declared but used as concept domain.")
            if enums_enabled and c._is_enum():
                self._print_nl(f"{self._indent}{self._indent}self.{name} = model.Enum('{name}', {[e.name for e in enums_map[name]]})")
            else:
                extends = c._extends
                if not enums_enabled and c._is_enum():
                    # todo: derive enum type
                    # ORM adapter produces only string enums
                    extends_elements = ["qb.String"]
                else:
                    extends_elements = [f"self.{self._get_type(ext)}" if not self._get_type(ext).startswith(
                        "qb.") and not self._get_type(ext).startswith("builder.") else self._get_type(ext) for ext in
                                        extends]
                extends_str = f", extends=[{', '.join(extends_elements)}]" if extends else ""
                concept_class = name + 'Concept' if pyi_enabled else 'model.Concept'
                params = f"({'model, ' if pyi_enabled else ''}'{name}'{extends_str})"
                self._print_nl(f"{self._indent}{self._indent}self.{name} = {concept_class}{params}")

    def _handle_relationships(self, model: Model) -> None:
        for rel in model.relationships():
            # skip autogenerated 'name' Relationship for Enums
            if rel._name == 'name' and rel._parent is not None and rel._parent._is_enum():
                continue
            # print a root Relationship
            self._print_nl(f"{self._indent}{self._indent}self.{self._get_relationship_name(rel)} = "
                           f"model.Relationship('{rel._madlib}'{self._print_if_not_empty_and_not_equal('short_name', rel._passed_short_name, rel._name)})")

            # print remaining RelationshipReadings if any
            for r in rel._readings[1:]:
                self._print_nl(f"{self._indent}{self._indent}self.{self._get_relationship_name(r)} = "
                               f"self.{self._get_relationship_name(rel)}.alt('{r._madlib}'{self._print_if_not_empty_and_not_equal('short_name', r._passed_short_name, r._name)})")

    def _handle_ref_schemes(self, model: Model) -> None:
        for concept_name, concept in model.entity_types_map().items():
            if not isinstance(concept, Concept) or not concept._reference_schemes:
                continue

            for ref_scheme in concept._reference_schemes:
                rel_names = [f"self.{self._get_relationship_name(rel)}" for rel in ref_scheme]
                self._print_nl(f"{self._indent}{self._indent}self.{concept_name}.identify_by({', '.join(rel_names)})")

    def _handle_uniqueness_constraints(self) -> None:
        for constraint in self._unique_constraints:
            if not constraint.is_preferred_identifier:
                elements = [f"self.{self._get_role_name(role)}" for role in constraint.roles()]
                self._print_nl(f"{self._indent}{self._indent}self.Unique({', '.join(elements)})")

    def _handle_mandatory_constraints(self):
        for constraint in self._mandatory_constraints:
            role = constraint.roles()[0]
            role_name = self._get_role_name(role)
            self._print_nl(f"{self._indent}{self._indent}self.Mandatory(self.{role_name})")

    def _handle_role_value_constraints(self) -> None:
        for constraint in self._role_value_constraints:
            role = constraint.roles()[0]
            elements = self._get_constraint_values(constraint)
            role_name = f"self.{self._get_role_name(role)}"
            self._print_nl(f"{self._indent}{self._indent}self.RoleValueConstraint({role_name}, [{', '.join(elements)}])")

    def _handle_inclusive_role_constraints(self):
        for constraint in self._inclusive_role_constraints:
            roles = [f"self.{self._get_role_name(r)}" for r in constraint.roles()]
            self._print_nl(f"{self._indent}{self._indent}self.InclusiveRoleConstraint({', '.join(roles)})")

    def _handle_exclusive_role_constraints(self):
        self._emit_role_sequence_constraints(self._exclusive_role_constraints, "ExclusiveRoleConstraint")

    def _handle_ring_constraints(self):
        for constraint in self._ring_constraints:
            elements = [f"self.{self._get_role_name(role)}" for role in constraint.roles()]
            cst_types = [f"{tp}" for tp in constraint.types]
            self._print_nl(f"{self._indent}{self._indent}self.RingConstraint([{', '.join(cst_types)}], {', '.join(elements)})")

    def _handle_value_comparison_constraints(self):
        for constraint in self._value_comparison_constraints:
            elements = [f"self.{self._get_role_name(role)}" for role in constraint.roles()]
            self._print_nl(f"{self._indent}{self._indent}self.ValueComparisonConstraint({constraint.type}, {', '.join(elements)})")

    def _handle_frequency_constraints(self):
        for constraint in self._frequency_constraints:
            elements = [f"self.{self._get_role_name(role)}" for role in constraint.roles()]
            self._print_nl(f"{self._indent}{self._indent}self.FrequencyConstraint(({', '.join(constraint.frequency)}), {', '.join(elements)})")

    def _handle_cardinality_constraints(self):
        for constraint in self._cardinality_constraints:
            elements = self._get_constraint_values(constraint)
            self._print_nl(
                f"{self._indent}{self._indent}self.CardinalityConstraint(self.{constraint.concept()._name}, [{', '.join(elements)}])")

    def _handle_role_cardinality_constraints(self):
        for constraint in self._role_cardinality_constraints:
            elements = self._get_constraint_values(constraint)
            self._print_nl(
                f"{self._indent}{self._indent}self.RoleCardinalityConstraint(self.{self._get_role_name(constraint.roles()[0])}, [{', '.join(elements)}])")

    def _handle_value_constraints(self):
        for constraint in self._value_constraints:
            elements = self._get_constraint_values(constraint)
            self._print_nl(f"{self._indent}{self._indent}self.ValueConstraint(self.{constraint.concept()._name}, [{', '.join(elements)}])")

    def _emit_role_sequence_constraints(self, constraints, constraint_type: str):
        for constraint in constraints:
            role_sequences = [[f"self.{self._get_role_name(r)}" for r in ro_list] for ro_list in
                              constraint.role_sequences()]
            if self._is_complex_role_sequence(role_sequences):
                self._print_nl(
                    f"{self._indent}{self._indent}self.{constraint_type}([{'], ['.join(', '.join(ro_list) for ro_list in role_sequences)}])")
            else:
                self._print_nl(
                    f"{self._indent}{self._indent}self.{constraint_type}({', '.join(', '.join(ro_list) for ro_list in role_sequences)})")

    def _emit_subtype_constraints(self, constraints, constraint_type: str):
        for constraint in constraints:
            concepts = [f"self.{self._get_type(c)}" for c in constraint.concepts().values()]
            self._print_nl(f"{self._indent}{self._indent}self.{constraint_type}({', '.join(concepts)})")


EXCLUDED_RELATIONSHIPS = ["shape"]


class ObjectOrientedInterfacePrinter(InterfacePrinter):
    _indent: str

    def __init__(self, io: typing.Optional[typing.IO[str]] = None, space_indent: bool=False):
        # Set the base class field (frozen)
        super().__init__(io)
        object.__setattr__(self, '_indent', SPACE_INDENT if space_indent else TAB_INDENT)

    def to_string(self, model: Model, enums_enabled: bool = False) -> None:
        if enums_enabled:
            self._print_nl("from enum import Enum")
        self._print_nl("from typing import Union")
        self._print_nl("import relationalai.semantics.internal as qb")
        self._print_nl("import relationalai.semantics.internal.internal as builder")
        self._print_nl("from relationalai.early_access.dsl.orm.models import Concept")
        self._nl()
        if enums_enabled:
            self._handle_enums(model)
        self._handle_concepts(model, enums_enabled)

    def _handle_concepts(self, model: Model, enums_enabled) -> None:
        concepts_map = model.concepts_map()
        sorted_concepts = _sort_dependency_graph(model.concepts())
        for name in sorted_concepts:
            c = concepts_map.get(name)
            if c is None:
                raise ValueError(f"The concept '{name}' was not declared but used as concept domain.")
            if enums_enabled and c._is_enum():
                continue
            exclude_list = list(EXCLUDED_RELATIONSHIPS)
            # when enum is declared but enums are disabled print it as a Concept without "name" Relationship
            if c._is_enum():
                exclude_list.append("name")
            extends = [f"{e._name}Concept" for e in c._extends if not e._is_primitive()]
            self._print_nl(f"class {name}Concept({', '.join(extends) if extends else 'Concept'}):")
            rel_strs = self._get_declared_relationships(c, exclude_list)
            self._print_nl(f"{self._indent}pass" if len(rel_strs) == 0 else "\n".join(rel_strs))
            self._nl()
        self._print_nl("class ORMOntology:")
        for name in sorted_concepts:
            c = concepts_map.get(name)
            if c:
                if c._is_enum() and enums_enabled:
                    self._print_nl(f"{self._indent}{c._name}: {c._name}")
                else:
                    self._print_nl(f"{self._indent}{c._name}: {c._name}Concept")
