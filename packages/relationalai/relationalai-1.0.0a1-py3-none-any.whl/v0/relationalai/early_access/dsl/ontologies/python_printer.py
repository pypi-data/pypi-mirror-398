import json
import typing
from collections import defaultdict
from typing import TypeVar

from v0.relationalai.early_access.dsl import Model, ExternalRelation, ValueType, ValueSubtype, Relationship
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.types.standard import standard_value_types
from v0.relationalai.early_access.dsl.ontologies.constraints import Mandatory, Unique, RoleValueConstraint
from v0.relationalai.early_access.dsl.ontologies.roles import AbstractRole
from v0.relationalai.early_access.dsl.ontologies.subtyping import SubtypeConstraint, SubtypeArrow, \
    ExclusiveSubtypeConstraint, InclusiveSubtypeConstraint
from v0.relationalai.early_access.dsl.types.concepts import Concept
from v0.relationalai.semantics.metamodel.util import Printer, OrderedSet

# Define a generic type variable constrained to SubtypeConstraint or its subclasses
T = TypeVar("T", bound=SubtypeConstraint)

class PythonPrinter(Printer):
    _mandatory_roles: 'OrderedSet[AbstractRole]'
    _single_unique_roles: 'OrderedSet[AbstractRole]'
    _composite_preferred_identifiers: 'OrderedSet[Unique]'
    _internal_preferred_identifier_roles: 'OrderedSet[AbstractRole]'
    _relationship_uniqueness_constraints: 'dict[Relationship, OrderedSet[Unique]]'

    def __init__(self, io: typing.Optional[typing.IO[str]] = None):
        # Set the base class field (frozen)
        object.__setattr__(self, 'io', io)

        # Set all mutable fields using object.__setattr__
        object.__setattr__(self, '_mandatory_roles', OrderedSet())
        object.__setattr__(self, '_single_unique_roles', OrderedSet())
        object.__setattr__(self, '_composite_preferred_identifiers', OrderedSet())
        object.__setattr__(self, '_internal_preferred_identifier_roles', OrderedSet())
        object.__setattr__(self, '_relationship_uniqueness_constraints', defaultdict(OrderedSet))

    def to_python_string(self, model: Model) -> None:
        self._process_constraints(model)

        self._print_nl("import relationalai.early_access.dsl as rai")
        self._nl()

        self._print_nl(f"model = rai.Model(name='{model.name}', is_primary={model.is_primary})")
        self._print_nl("Concept = model.concept")
        self._print_nl("ValueType = model.value_type")
        self._print_nl("ValueSubType = model.value_sub_type")
        self._print_nl("EntityType = model.entity_type")
        self._print_nl("SubtypeArrow = model.subtype_arrow")
        self._print_nl("Relationship = model.relationship")
        self._print_nl("RefScheme = model.ref_scheme")
        self._print_nl("ExternalRelation = model.external_relation")
        self._print_nl("Query = model.query")
        self._print_nl("RoleValueConstraint = model.role_value_constraint")
        self._print_nl("CsvTable = model.csv_table")

        self._nl()
        self._handle_value_types(model)

        self._nl()
        self._handle_entity_types(model)

        self._nl()
        self._handle_relationships(model)

        self._handle_composite_reference_schemas()

        self._nl()
        self._handle_subtype_arrows(model)

        self._nl()
        self._handle_external_relations(model)

        self._nl()
        self._handle_role_value_constraints(model)

    def _handle_value_types(self, model: Model) -> None:
        for vt in model.value_types():
            name = vt.display()
            if isinstance(vt, ValueType):
               self._print_nl(f"{name} = ValueType('{name}', {', '.join(self._get_type(t) for t in vt._types)})")
            elif isinstance(vt, ValueSubtype) and vt.parent():
                self._print_nl(f"{name} = ValueSubType('{name}', {self._get_type(vt.parent())})")
            elif isinstance(vt, Concept):
                self._print_nl(f"{name} = ValueType('{name}', {', '.join(self._get_type(t) for t in vt._types)})")

    def _handle_entity_types(self, model: Model) -> None:
        for name, et in model.entity_types_map().items():
            self._print_nl(f"{name} = EntityType('{name}'{self._print_if_not_empty('ref_mode', et.ref_schema_name())})")

    def _handle_relationships(self, model: Model) -> None:
        for rel in model.relationships():
            if not rel.is_subtype():
                self._print_nl("with Relationship() as rel:")
                self._handle_relationship_roles(rel)
                self._handle_relationship_relations(rel)
                self._handle_relationship_uniqueness_constraints(rel, self._relationship_uniqueness_constraints.get(rel, OrderedSet()))
                self._nl()

    def _handle_relationship_roles(self, rel):
        for i, r in enumerate(rel.roles()):
            self._indent_print_nl(1, f"rel.role({self._get_type(r.player())}"
                                     f"{self._print_if_not_empty('name', r.name())}"
                                     f"{self._print_if_true('unique', r in self._single_unique_roles)}"
                                     f"{self._print_if_true('mandatory', r in self._mandatory_roles)}"
                                     f"{self._print_if_true('primary_key', r in self._internal_preferred_identifier_roles)})")
            if r.prefix or r.postfix:
                elements = list(filter(None, [
                    self._print_first_if_not_empty('prefix', r.prefix),
                    self._print_first_if_not_empty('postfix', r.postfix)
                ]))
                self._indent_print_nl(1, f"rel.role_at({i}).verbalization({', '.join(elements)})")

    def _handle_relationship_relations(self, rel):
        for relation in rel.relations():
            reading = relation.reading()
            if reading:

                num_roles = len(reading.roles)
                num_texts = len(reading.text_frags)

                elements = []

                for i in range(num_texts):
                    role = reading.role_at(i)
                    elements.append(f"rel.role_at({rel.role_index(role)})")  # Role first
                    elements.append(f"'{reading.text_frags[i]}'")  # Then text

                if num_roles > num_texts:
                    role = reading.role_at(num_texts)
                    elements.append(f"rel.role_at({rel.role_index(role)})")  # Add last role if needed

                self._indent_print_nl(1, f"rel.relation({', '.join(elements)}"
                                         f"{self._print_if_not_empty('name', reading.rel_name)}"
                                         f"{self._print_if_true('functional', relation.signature().functional())})")

    def _handle_relationship_uniqueness_constraints(self, rel, constraints: OrderedSet[Unique]) -> None:
        for c in constraints:
            elements = [f"rel.role_at({rel.role_index(role)})" for role in c.roles()]
            self._indent_print_nl(1, f"rel.unique({', '.join(elements)})")

    def _handle_composite_reference_schemas(self) -> None:
        for preferred_id in self._composite_preferred_identifiers:

            elements = []

            for role in preferred_id.roles():
                relationship = role.part_of

                relation = self._lookup_relation_by_second_role(relationship, role)

                player_name = self._get_type(relation.first())
                rel_name = relation.rel_name()
                elements.append(f"{player_name}.{rel_name}")

            self._print_nl(f"RefScheme({', '.join(elements)})")

    def _handle_subtype_arrows(self, model:Model) -> None:
        subtype_arrows_by_type = self._group_subtype_arrows_by_type(model)
        inclusive_subtype_constraints_by_type = self._get_inclusive_subtype_constraints_by_type(model)
        exclusive_subtype_constraints_by_type = self._get_exclusive_subtype_constraints_by_type(model)

        for et in model.entity_types():

            subtype_arrows = subtype_arrows_by_type.get(et, OrderedSet())
            inclusive_subtype_constraints = inclusive_subtype_constraints_by_type.get(et, OrderedSet())
            exclusive_subtype_constraints = exclusive_subtype_constraints_by_type.get(et, OrderedSet())

            name = et.display()

            # Common elements in both sets
            common_constraints = [i for i in inclusive_subtype_constraints
                                    for e in exclusive_subtype_constraints
                                    if self.constraints_equal(i, e)]
            if len(common_constraints) > 0:
                for c in common_constraints:
                    self._print_nl(f"SubtypeArrow({name}, [{', '.join(self._get_type(a.start) for a in c.arrows)}], "
                                   f"exclusive=True, inclusive=True)")

            # Only in inclusive (but not in exclusive)
            only_inclusive_constraints = [i for i in inclusive_subtype_constraints
                                            if not any(self.constraints_equal(i, e) for e in exclusive_subtype_constraints)]
            if len(only_inclusive_constraints) > 0:
                for c in only_inclusive_constraints:
                    self._print_nl(f"SubtypeArrow({name}, [{', '.join(self._get_type(a.start) for a in c.arrows)}], "
                                   f"inclusive=True)")

            # Only in exclusive (but not in inclusive)
            only_exclusive_constraints = [e for e in exclusive_subtype_constraints
                                            if not any(self.constraints_equal(e, i) for i in inclusive_subtype_constraints)]
            if len(only_exclusive_constraints) > 0:
                for c in only_exclusive_constraints:
                    self._print_nl(f"SubtypeArrow({name}, [{', '.join(self._get_type(a.start) for a in c.arrows)}], "
                                   f"exclusive=True)")

            # Get all arrows from both inclusive and exclusive constraints
            all_arrows_in_constraints = OrderedSet.from_iterable(a for c in inclusive_subtype_constraints for a in c.arrows) | \
                                        OrderedSet.from_iterable(a for c in exclusive_subtype_constraints for a in c.arrows)

            # Subtract the arrows in constraints from subtype_arrows
            remaining_subtype_arrows = subtype_arrows - all_arrows_in_constraints
            if len(remaining_subtype_arrows) > 0:
                self._print_nl(f"SubtypeArrow({name}, [{', '.join(self._get_type(a.start) for a in remaining_subtype_arrows)}])")

    def _handle_external_relations(self, model: Model) -> None:
        for relation in self._get_external_relations(model):
            name = relation.rel_name()
            type_args = ', '.join(self._get_type(t) for t in relation.signature().types())

            if name == "output":
                self._print_nl(f"Query({type_args})")
            else:
                self._print_nl(f"ExternalRelation('{name}', {type_args})")

    def _handle_role_value_constraints(self, model: Model) -> None:
        for c in self._get_role_value_constraints(model):
            role = c.role()
            relationship = role.part_of

            relation = self._lookup_relation_by_second_role(relationship, role)

            player_name = self._get_type(relation.first())
            rel_name = relation.rel_name()

            self._print_nl(f"RoleValueConstraint({player_name}.{rel_name}, {json.dumps(c.values())})")

    def _process_constraints(self, model: Model) -> None:
        for c in model.constraints():
            if isinstance(c, Mandatory):
                self._mandatory_roles.add(c.role)
            elif isinstance(c, Unique):
                if c.is_preferred_identifier:
                    if len(c.roles()) == 1:
                        self._internal_preferred_identifier_roles.add(c.roles()[0])
                    else:
                        self._composite_preferred_identifiers.add(c)
                elif len(c.roles()) == 1:
                    self._single_unique_roles.add(c.roles()[0])
                else:
                    self._relationship_uniqueness_constraints[c.roles()[0].part_of].add(c)

    @staticmethod
    def _group_subtype_arrows_by_type(model: Model) -> dict[Type, OrderedSet[SubtypeArrow]]:
        subtype_arrows_by_type = defaultdict(OrderedSet)
        for a in model.subtype_arrows():
            subtype_arrows_by_type[a.end].add(a)
        return dict(subtype_arrows_by_type)

    @staticmethod
    def _get_subtype_constraints_by_type(model: Model, constraint_type: typing.Type[T]) -> dict[Type, OrderedSet[SubtypeConstraint]]:
        constraints_by_type: dict[Type, OrderedSet[SubtypeConstraint]] = defaultdict(OrderedSet)

        for c in model.subtype_constraints():
            if isinstance(c, constraint_type):
                for a in c.arrows:
                    constraints_by_type[a.end].add(c)

        return dict(constraints_by_type)

    def _get_exclusive_subtype_constraints_by_type(self, model: Model) -> dict[Type, OrderedSet[SubtypeConstraint]]:
        return self._get_subtype_constraints_by_type(model, ExclusiveSubtypeConstraint)

    def _get_inclusive_subtype_constraints_by_type(self, model: Model) -> dict[Type, OrderedSet[SubtypeConstraint]]:
        return self._get_subtype_constraints_by_type(model, InclusiveSubtypeConstraint)

    @staticmethod
    def _get_role_value_constraints(model: Model) -> OrderedSet[RoleValueConstraint]:
        return OrderedSet.from_iterable(c for c in model.constraints() if isinstance(c, RoleValueConstraint))

    @staticmethod
    def _get_external_relations(model: Model) -> OrderedSet[ExternalRelation]:
        return OrderedSet.from_iterable(r for r in model.relations() if isinstance(r, ExternalRelation))

    @staticmethod
    def _lookup_relation_by_second_role(relationship, role):
        # Find the matching relation where the 2nd role is `role`
        relation = next(
            (rel for rel in relationship.relations() if rel.reading().roles[1] == role),
            None
        )
        if relation is None:
            raise Exception(f"Could not find matching relation for role player {role.player().name()} "
                            f"in relationship {relationship._name()}")
        return relation

    @staticmethod
    def constraints_equal(a: SubtypeConstraint, b: SubtypeConstraint) -> bool:
        return frozenset(a.arrows) == frozenset(b.arrows)

    @staticmethod
    def _get_type(t: Type) -> str:
        return f"rai.{t.display()}" if t.display() in standard_value_types else t.display()

    @staticmethod
    def _print_if_not_empty(label: str, value: str) -> str:
        return f", {label}='{value}'" if value else ""

    @staticmethod
    def _print_first_if_not_empty(label: str, value: str) -> str:
        return f"{label}='{value}'" if value else ""

    @staticmethod
    def _print_if_true(label: str, value: bool) -> str:
        return f", {label}=True" if value else ""