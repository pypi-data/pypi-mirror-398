import typing

from v0.relationalai.util.graph import topological_sort
from v0.relationalai.early_access.dsl.orm.constraints import Unique, Mandatory, RoleValueConstraint, \
    InclusiveSubtypeConstraint, ExclusiveSubtypeConstraint, Range, RingConstraint, InclusiveRoleConstraint, \
    ExclusiveRoleConstraint, ValueComparisonConstraint, RoleSubsetConstraint, EqualityConstraint, FrequencyConstraint, \
    CardinalityConstraint, RoleCardinalityConstraint, ValueConstraint
from v0.relationalai.early_access.dsl.orm.models import Model
from v0.relationalai.early_access.dsl.orm.relationships import Role
from v0.relationalai.early_access.dsl.orm.types import Concept
from v0.relationalai.semantics.metamodel.util import Printer as BasePrinter, OrderedSet
import v0.relationalai.semantics as qb

MODEL_VAR_NAME = "model"

class Printer(BasePrinter):
    _unique_constraints: OrderedSet[Unique]
    _mandatory_constraints: OrderedSet[Mandatory]
    _role_value_constraints: OrderedSet[RoleValueConstraint]
    _inclusive_subtype_constraints: OrderedSet[InclusiveSubtypeConstraint]
    _exclusive_subtype_constraints: OrderedSet[ExclusiveSubtypeConstraint]
    _inclusive_role_constraints: OrderedSet[InclusiveRoleConstraint]
    _exclusive_role_constraints: OrderedSet[ExclusiveRoleConstraint]
    _ring_constraints: OrderedSet[RingConstraint]
    _value_comparison_constraints: OrderedSet[ValueComparisonConstraint]
    _role_subset_constraints: OrderedSet[RoleSubsetConstraint]
    _equality_constraints: OrderedSet[EqualityConstraint]
    _frequency_constraints: OrderedSet[FrequencyConstraint]
    _cardinality_constraints: OrderedSet[CardinalityConstraint]
    _role_cardinality_constraints: OrderedSet[RoleCardinalityConstraint]
    _value_constraints: OrderedSet[ValueConstraint]

    def __init__(self, io: typing.Optional[typing.IO[str]] = None):
        # Set the base class field (frozen)
        object.__setattr__(self, 'io', io)

        # Set all mutable fields using object.__setattr__
        object.__setattr__(self, '_unique_constraints', OrderedSet())
        object.__setattr__(self, '_mandatory_constraints', OrderedSet())
        object.__setattr__(self, '_role_value_constraints', OrderedSet())
        object.__setattr__(self, '_inclusive_subtype_constraints', OrderedSet())
        object.__setattr__(self, '_exclusive_subtype_constraints', OrderedSet())
        object.__setattr__(self, '_inclusive_role_constraints', OrderedSet())
        object.__setattr__(self, '_exclusive_role_constraints', OrderedSet())
        object.__setattr__(self, '_ring_constraints', OrderedSet())
        object.__setattr__(self, '_value_comparison_constraints', OrderedSet())
        object.__setattr__(self, '_role_subset_constraints', OrderedSet())
        object.__setattr__(self, '_equality_constraints', OrderedSet())
        object.__setattr__(self, '_frequency_constraints', OrderedSet())
        object.__setattr__(self, '_cardinality_constraints', OrderedSet())
        object.__setattr__(self, '_role_cardinality_constraints', OrderedSet())
        object.__setattr__(self, '_value_constraints', OrderedSet())


    def to_string(self, model: Model, enums_enabled: bool = False, pyi_enabled: bool = False) -> None:
        self._process_constraints(model)

        self._print_nl("import relationalai.semantics.internal as qb")
        self._print_nl("import relationalai.semantics.internal.internal as builder")
        self._print_nl("from relationalai.early_access.dsl.orm.models import Model")
        if pyi_enabled:
            self._print_nl("from relationalai.early_access.dsl.orm.models import Concept")
        self._print_nl("from relationalai.early_access.dsl.orm.constraints import Range")
        self._print_nl("from relationalai.early_access.dsl.orm.constraints import RingType")
        self._print_nl("from relationalai.early_access.dsl.orm.constraints import ValueComparisonType")
        self._nl()

        self._print_nl(f"{MODEL_VAR_NAME} = Model(name='{model.name}', is_primary={model.is_primary}"
                       f"{self._print_if_false('use_lqp', model.qb_model()._use_lqp)}"
                       f"{self._print_if_true('use_sql', model.qb_model()._use_sql)}"
                       f"{self._print_if_true('wide_outputs', model.qb_model()._wide_outputs)}"
                       f"{self._print_if_true('dry_run', model.qb_model()._dry_run)})")
        # use class stubs for new Concepts which extend orm QB Concept
        if not pyi_enabled:
            self._print_nl("Concept = model.Concept")
        if enums_enabled:
            self._print_nl("Enum = model.Enum")
        self._print_nl("Relationship = model.Relationship")
        self._print_nl("Unique = model.unique")
        self._print_nl("Mandatory = model.mandatory")
        self._print_nl("RoleValueConstraint = model.role_value_constraint")
        self._print_nl("InclusiveSubtypeConstraint = model.inclusive_subtype_constraint")
        self._print_nl("ExclusiveSubtypeConstraint = model.exclusive_subtype_constraint")
        self._print_nl("InclusiveRoleConstraint = model.inclusive_roles")
        self._print_nl("ExclusiveRoleConstraint = model.exclusive_roles")
        self._print_nl("RingConstraint = model.ring")
        self._print_nl("ValueComparisonConstraint = model.value_comparison")
        self._print_nl("RoleSubsetConstraint = model.role_subset")
        self._print_nl("EqualityConstraint = model.equality")
        self._print_nl("FrequencyConstraint = model.frequency")
        self._print_nl("CardinalityConstraint = model.cardinality")
        self._print_nl("RoleCardinalityConstraint = model.role_cardinality")
        self._print_nl("ValueConstraint = model.value_constraint")

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

    def _handle_concepts(self, model: Model, enums_enabled: bool, pyi_enabled: bool) -> None:
        concepts_map = model.concepts_map()
        enums_map = model.enums_map()
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
                self._print_nl(f'\t"""Represents {name} concept."""')
            self._nl()
        for name in sorted_concepts:
            c = concepts_map.get(name)
            if c is None:
                raise ValueError(f"The concept '{name}' was not declared but used as concept domain.")
            if enums_enabled and c._is_enum():
                self._print_nl(f"{name} = Enum('{name}', {[e.name for e in enums_map[name]]})")
            else:
                extends = c._extends
                if not enums_enabled and c._is_enum():
                    # todo: derive enum type
                    # ORM adapter produces only string enums
                    extends_elements = ["qb.String"]
                else:
                    extends_elements = [f"{self._get_type(ext)}" for ext in extends]
                extends_str = f", extends=[{', '.join(extends_elements)}]" if extends else ""
                concept_class = name + 'Concept' if pyi_enabled else 'Concept'
                params = f"({'model, ' if pyi_enabled else ''}'{name}'{extends_str})"
                self._print_nl(f"{name} = {concept_class}{params}")

    def _handle_relationships(self, model: Model) -> None:
        for rel in model.relationships():
            # skip autogenerated 'name' Relationship for Enums
            if rel._name == 'name' and rel._parent is not None and rel._parent._is_enum():
                continue
            # print a root Relationship
            self._print_nl(f"{self._get_relationship_name(rel)} = "
                           f"Relationship('{rel._madlib}'{self._print_if_not_empty_and_not_equal('short_name', rel._passed_short_name, rel._name)})")

            # print remaining RelationshipReadings if any
            for r in rel._readings[1:]:
                self._print_nl(f"{self._get_relationship_name(r)} = "
                               f"{self._get_relationship_name(rel)}.alt('{r._madlib}'{self._print_if_not_empty_and_not_equal('short_name', r._passed_short_name, r._name)})")

    def _handle_ref_schemes(self, model: Model) -> None:
        for concept_name, concept in model.entity_types_map().items():
            if not isinstance(concept, Concept) or not concept._reference_schemes:
                continue

            for ref_scheme in concept._reference_schemes:
                rel_names = [self._get_relationship_name(rel) for rel in ref_scheme]
                self._print_nl(f"{concept_name}.identify_by({', '.join(rel_names)})")

    def _handle_uniqueness_constraints(self) -> None:
        for constraint in self._unique_constraints:
            if not constraint.is_preferred_identifier:
                elements = [self._get_role_name(role) for role in constraint.roles()]
                self._print_nl(f"Unique({', '.join(elements)})")

    def _handle_mandatory_constraints(self):
        for constraint in self._mandatory_constraints:
            role = constraint.roles()[0]
            role_name = self._get_role_name(role)
            self._print_nl(f"Mandatory({role_name})")

    def _handle_role_value_constraints(self) -> None:
        for constraint in self._role_value_constraints:
            role = constraint.roles()[0]
            elements = self._get_constraint_values(constraint)
            role_name = self._get_role_name(role)
            self._print_nl(f"RoleValueConstraint({role_name}, [{', '.join(elements)}])")

    def _handle_subtype_constraints(self):
        self._emit_subtype_constraints(self._inclusive_subtype_constraints, "InclusiveSubtypeConstraint")
        self._nl()
        self._emit_subtype_constraints(self._exclusive_subtype_constraints, "ExclusiveSubtypeConstraint")

    def _handle_inclusive_role_constraints(self):
        for constraint in self._inclusive_role_constraints:
            roles = [self._get_role_name(r) for r in constraint.roles()]
            self._print_nl(f"InclusiveRoleConstraint({', '.join(roles)})")

    def _handle_exclusive_role_constraints(self):
        self._emit_role_sequence_constraints(self._exclusive_role_constraints, "ExclusiveRoleConstraint")

    def _handle_ring_constraints(self):
        for constraint in self._ring_constraints:
            elements = [self._get_role_name(role) for role in constraint.roles()]
            cst_types = [f"{tp}" for tp in constraint.types]
            self._print_nl(f"RingConstraint([{', '.join(cst_types)}], {', '.join(elements)})")

    def _handle_value_comparison_constraints(self):
        for constraint in self._value_comparison_constraints:
            elements = [self._get_role_name(role) for role in constraint.roles()]
            self._print_nl(f"ValueComparisonConstraint({constraint.type}, {', '.join(elements)})")

    def _handle_role_subset_constraints(self):
        self._emit_role_sequence_constraints(self._role_subset_constraints, "RoleSubsetConstraint")

    def _handle_equality_constraints(self):
        self._emit_role_sequence_constraints(self._equality_constraints, "EqualityConstraint")

    def _handle_frequency_constraints(self):
        for constraint in self._frequency_constraints:
            elements = [self._get_role_name(role) for role in constraint.roles()]
            self._print_nl(f"FrequencyConstraint(({', '.join(constraint.frequency)}), {', '.join(elements)})")

    def _handle_cardinality_constraints(self):
        for constraint in self._cardinality_constraints:
            elements = self._get_constraint_values(constraint)
            self._print_nl(f"CardinalityConstraint({constraint.concept()._name}, [{', '.join(elements)}])")

    def _handle_role_cardinality_constraints(self):
        for constraint in self._role_cardinality_constraints:
            elements = self._get_constraint_values(constraint)
            self._print_nl(f"RoleCardinalityConstraint({self._get_role_name(constraint.roles()[0])}, [{', '.join(elements)}])")

    def _handle_value_constraints(self):
        for constraint in self._value_constraints:
            elements = self._get_constraint_values(constraint)
            self._print_nl(f"ValueConstraint({constraint.concept()._name}, [{', '.join(elements)}])")

    def _emit_role_sequence_constraints(self, constraints, constraint_type: str):
        for constraint in constraints:
            role_sequences = [[self._get_role_name(r) for r in ro_list] for ro_list in constraint.role_sequences()]
            if self._is_complex_role_sequence(role_sequences):
                self._print_nl(f"{constraint_type}([{'], ['.join(', '.join(ro_list) for ro_list in role_sequences)}])")
            else:
                self._print_nl(f"{constraint_type}({', '.join(', '.join(ro_list) for ro_list in role_sequences)})")

    def _emit_subtype_constraints(self, constraints, constraint_type: str):
        for constraint in constraints:
            concepts = [self._get_type(c) for c in constraint.concepts().values()]
            self._print_nl(f"{constraint_type}({', '.join(concepts)})")

    def _process_constraints(self, model: Model) -> None:
        for c in model.constraints():
            if isinstance(c, Unique):
                self._unique_constraints.add(c)
            elif isinstance(c, Mandatory):
                self._mandatory_constraints.add(c)
            elif isinstance(c, RoleValueConstraint):
                self._role_value_constraints.add(c)
            elif isinstance(c, InclusiveSubtypeConstraint):
                self._inclusive_subtype_constraints.add(c)
            elif isinstance(c, ExclusiveSubtypeConstraint):
                self._exclusive_subtype_constraints.add(c)
            elif isinstance(c, InclusiveRoleConstraint):
                self._inclusive_role_constraints.add(c)
            elif isinstance(c, ExclusiveRoleConstraint):
                self._exclusive_role_constraints.add(c)
            elif isinstance(c, RingConstraint):
                self._ring_constraints.add(c)
            elif isinstance(c, ValueComparisonConstraint):
                self._value_comparison_constraints.add(c)
            elif isinstance(c, RoleSubsetConstraint):
                self._role_subset_constraints.add(c)
            elif isinstance(c, EqualityConstraint):
                self._equality_constraints.add(c)
            elif isinstance(c, FrequencyConstraint):
                self._frequency_constraints.add(c)
            elif isinstance(c, CardinalityConstraint):
                self._cardinality_constraints.add(c)
            elif isinstance(c, RoleCardinalityConstraint):
                self._role_cardinality_constraints.add(c)
            elif isinstance(c, ValueConstraint):
                self._value_constraints.add(c)

    def _get_role_name(self, role: Role) -> str:
        return f"{self._get_relationship_name(role._relationship)}['{role._field_ref._name}']"

    @staticmethod
    def _get_relationship_name(rel: typing.Union[qb.Relationship, qb.RelationshipReading]) -> str:
        if rel._parent and rel._short_name:
            parent_name = rel._parent._name
            prefix = "qb." if parent_name in Concept.builtins else ""
            return f"{prefix}{parent_name}.{rel._short_name}"
        return rel._name

    def _get_type(self, t: Concept) -> str:
        name = _get_concept_name(t)
        if name.startswith("Decimal"):
            return f"builder.decimal_concept_by_name('{name}')"
        else:
            return f"qb.{name}" if name in Concept.builtins else name

    @staticmethod
    def _get_constraint_values(constraint):
        elements = []
        for value in constraint.values():
            if isinstance(value, Range):
                if value._start and value._end:
                    elements.append(f"Range.between({value._start}, {value._end})")
                elif value._end:
                    elements.append(f"Range.to_value({value._end})")
                else:
                    elements.append(f"Range.from_value({value._start})")
            elif isinstance(value, str):
                elements.append(repr(value))
            else:
                elements.append(str(value))
        return elements

    @staticmethod
    def _print_if_not_empty(label: str, value: typing.Optional[str]) -> str:
        return f", {label}='{value}'" if value else ""

    @staticmethod
    def _print_if_not_empty_and_not_equal(label: str, value: typing.Optional[str],
                                          compare_to: typing.Optional[str]) -> str:
        return f", {label}='{value}'" if value and value != compare_to else ""

    @staticmethod
    def _print_if_true(label: str, value: bool) -> str:
        return f", {label}=True" if value else ""

    @staticmethod
    def _print_if_false(label: str, value: bool) -> str:
        return f", {label}=False" if not value else ""

    @staticmethod
    def _is_complex_role_sequence(role_sequences):
        return not all(len(item) == 1 for item in role_sequences)


EXCLUDED_RELATIONSHIPS = ["shape"]


class InterfacePrinter(BasePrinter):

    def __init__(self, io: typing.Optional[typing.IO[str]] = None):
        # Set the base class field (frozen)
        object.__setattr__(self, 'io', io)

    def to_string(self, model: Model, enums_enabled: bool = False) -> None:
        if enums_enabled:
            self._print_nl("from enum import Enum")
        self._print_nl("from typing import Union")
        self._print_nl("import relationalai.semantics.internal as qb")
        self._print_nl("import relationalai.semantics.internal.internal as builder")
        self._print_nl("from relationalai.early_access.dsl.orm.models import Concept, Model")
        self._nl()
        self._print_nl(f"{MODEL_VAR_NAME}: Model")
        self._nl()
        if enums_enabled:
            self._handle_enums(model)
        self._handle_concepts(model, enums_enabled)

    def _handle_enums(self, model: Model) -> None:
        for e in model.enums():
            self._print_nl(f"class {e.__name__}(Enum):")
            for member in e:
                self._print_nl(f"\t{member.name}: {e.__name__}")
            self._print_nl(
                "\n".join(self._get_declared_relationships(e._concept, EXCLUDED_RELATIONSHIPS)))  #type: ignore
            self._nl()

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
            self._print_nl("\tpass" if len(rel_strs) == 0 else "\n".join(rel_strs))
            self._print_nl(f"{c._name}: {c._name}Concept")
            self._nl()

    def _get_declared_relationships(self, c: qb.Concept, exclude_list: list[str]) -> list[str]:
        rel_strs = []
        for rel in c._relationships.keys():
            if rel not in exclude_list:
                rel_strs.append(f"\t{rel}: Union[qb.Relationship, qb.RelationshipReading]")
        return rel_strs


# utility methods
def _is_builtin_type(t: qb.Concept) -> bool:
    return _get_concept_name(t) in Concept.builtins


def _get_concept_name(t: qb.Concept) -> str:
    return 'Integer' if t._name == 'Int' else t._name


def _sort_dependency_graph(concepts: list[qb.Concept]):
    nodes = []
    edges = []
    for concept in concepts:
        name = concept._name
        nodes.append(name)
        for ext in concept._extends:
            if not _is_builtin_type(ext):
                edges.append((ext._name, name))
    return topological_sort(nodes, edges)
