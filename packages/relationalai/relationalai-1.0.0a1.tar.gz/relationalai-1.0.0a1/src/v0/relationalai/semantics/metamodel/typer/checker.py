"""
Type checking for the IR.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Union as PyUnion, Tuple, cast

from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set
from v0.relationalai.semantics.metamodel import ir, types, visitor, compiler
import rich


@dataclass
class CheckError:
    """A model well-formedness error."""
    msg: str
    node: ir.Node

    def __str__(self):
        return f"[red bold][Model Error][/red bold] {self.msg}: [white]{str(self.node).strip()}[/white]"


@dataclass
class CheckEnv:
    """Environment for checking that a model is well-formed."""

    # The model being type-checked.
    model: ir.Model

    # Diagnostics. For now, this is just strings.
    diags: List[CheckError]

    # How verbose to be with debug info, 0 for off.
    verbosity: int

    def __init__(self, model: ir.Model, verbosity: int=0):
        self.model = model
        self.diags = []
        self.verbosity = verbosity

    def _complain(self, node: ir.Node, msg: str):
        """Report an error."""
        self.diags.append(CheckError(msg, node))


@dataclass
class Checker(compiler.Pass):
    """
    A pass that checks that a model is well-formed.
    Diagnostics are reported for ill-formed models.
    """

    # How verbose to be with debug output, 0 is off.
    verbosity: int = field(default=0, init=False)

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        # Type checking.
        env = CheckEnv(model, self.verbosity)
        checker = CheckModel(env)
        model.accept(checker)

        # Report any well-formedness errors
        if env.diags:
            for diag in env.diags:
                rich.print(str(diag))
            if self.verbosity:
                rich.print("[dim]-----[/dim]")
                rich.print(str(model))

        return model


@dataclass
class CheckModel(visitor.DAGVisitor):
    """
    A visitor that checks that a model is well-formed.
    """
    def __init__(self, env: CheckEnv):
        super().__init__()
        self.env = env

    def visit_model(self, node: ir.Model, parent: Optional[ir.Node]=None) -> None:
        env = self.env
        model = node

        # Check that all types are present in the model.
        @dataclass
        class CheckPresence(visitor.Visitor):
            model: ir.Model = field(init=True)
            env: CheckEnv = field(init=True)
            def visit_scalartype(self, node: ir.ScalarType, parent: Optional[ir.Node]=None) -> None:
                if node not in self.model.types:
                    self.env.diags.append(CheckError(f"Type {ir.node_to_string(node).strip()} not found in the model.", node))
            def visit_decimaltype(self, node: ir.DecimalType, parent: Optional[ir.Node]=None) -> None:
                if node not in self.model.types:
                    self.env.diags.append(CheckError(f"Type {ir.node_to_string(node).strip()} not found in the model.", node))
            def visit_listtype(self, node: ir.ListType, parent: Optional[ir.Node]=None) -> None:
                if node not in self.model.types:
                    self.env.diags.append(CheckError(f"Type {ir.node_to_string(node).strip()} not found in the model.", node))
            def visit_uniontype(self, node: ir.UnionType, parent: Optional[ir.Node]=None) -> None:
                if node not in self.model.types:
                    self.env.diags.append(CheckError(f"Type {ir.node_to_string(node).strip()} not found in the model.", node))
            def visit_tupletype(self, node: ir.TupleType, parent: Optional[ir.Node]=None) -> None:
                if node not in self.model.types:
                    self.env.diags.append(CheckError(f"Type {ir.node_to_string(node).strip()} not found in the model.", node))

        for t in model.types:
            t.accept(CheckPresence(model, env))

        # Check that the types are acyclic and that the supertype relation is acyclic.
        def check_type_cycles(t: ir.Type, subtypes: OrderedSet[ir.Type]=ordered_set(), containers: OrderedSet[ir.Type]=ordered_set()) -> None:
            if t in subtypes:
                env.diags.append(CheckError(f"Type {t} is involved in a subtyping cycle with {', '.join(str(s) for s in (subtypes - {t}))}.", t))
            if t in containers:
                env.diags.append(CheckError(f"Type {t} is infinitely recursive. It is contained within itself.", t))
            if isinstance(t, ir.ScalarType):
                for s in t.super_types:
                    check_type_cycles(s, subtypes | {t}, containers)
            if isinstance(t, ir.ListType):
                check_type_cycles(t.element_type, subtypes, containers | {t})
            if isinstance(t, ir.UnionType):
                for s in t.types:
                    check_type_cycles(s, subtypes, containers | {t})
            if isinstance(t, ir.TupleType):
                for s in t.types:
                    check_type_cycles(s, subtypes, containers | {t})

        # Check that the types are well-formed and acyclic.
        for t in model.types:
            check_type_cycles(t)
            # Lists must have scalar element types.
            if isinstance(t, ir.ListType):
                if not isinstance(t.element_type, ir.ScalarType):
                    env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an list type, but extends non-scalar element type {ir.type_to_string(t.element_type)}.", t))
            # Tuples must have scalar element types.
            elif isinstance(t, ir.TupleType):
                for s in t.types:
                    if not isinstance(s, ir.ScalarType):
                        env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an tuple type, but extends non-scalar element type {ir.type_to_string(s)}.", t))
            # Union types must have scalar element types.
            elif isinstance(t, ir.UnionType):
                for s in t.types:
                    if not isinstance(s, ir.ScalarType):
                        env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an union type, but extends non-scalar element type {ir.type_to_string(s)}.", t))
            elif isinstance(t, ir.ScalarType):
                # Supertypes of scalar types must be scalar types.
                for s in t.super_types:
                    if not isinstance(s, ir.ScalarType):
                        env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an scalar type, but extends a non-scalar type {ir.type_to_string(s)}.", t))
                if types.is_any(t):
                    # The Any type should not have supertypes.
                    if len(t.super_types) > 0:
                        env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is the Any type, but extends some supertypes. The Any type should not have supertypes.", t))
                elif types.is_value_base_type(t):
                    # Value base types should not have supertypes.
                    if len(t.super_types) > 0:
                        if len(t.super_types) != 1 or (t.super_types[0] != types.Number and t.super_types[0] != types.String and t.super_types[0] != types.GenericDecimal):
                            env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an value base type, but extends one or more supertypes. Value base types should not have supertypes (except for Number, GenericDecimal or String).", t))
                elif types.is_value_type(t):
                    # By construction, a value type should either be a value base type or extend a value base type, so there's no need to check that.
                    # Value types should have exactly one supertype.
                    if len(t.super_types) > 1:
                        env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an value type, but extends multiple supertypes. User-defined value types must have exactly one supertype.", t))
                    # Value types cannot extend Hash.
                    if types.is_subtype(t, types.Hash):
                        env.diags.append(CheckError(f"Type {ir.type_to_string(t)} is an value type, but extends the entity type `Hash`. Entity types and value types must be disjoint.", t))

        # Recurse to check the rest of the model.
        return super().visit_model(node, parent)

    def visit_engine(self, node: ir.Engine, parent: Optional[ir.Node]=None):
        # Check that each relation requires a subset of the engine capabilities.
        for r in node.relations:
            for c in r.requires:
                if c not in node.capabilities:
                    self.env._complain(node, f"Relation `{r.name}` requires capability {c}, but engine `{node.name}` only has {', '.join([str(x) for x in node.capabilities])}.")
        # Do not recurse. We already checked the relations at the model level.
        pass

    def visit_scalartype(self, node: ir.Type, parent: Optional[ir.Node]=None):
        # Do not recurse.
        pass

    def visit_listtype(self, node: ir.ListType, parent: Optional[ir.Node]=None):
        # List types are allowed before type inference.
        # Type inference will complain if the element is inferred to be a list type.
        # Do not recurse.
        pass

    def visit_relation(self, node: ir.Relation, parent: Optional[ir.Node]=None):
        # don't check relations used in annotations
        if parent and isinstance(parent, ir.Annotation):
            return

        if node not in self.env.model.relations:
            self.env._complain(node, f"Relation `{node.name}` (id={node.id}) is not declared in the model.")
        field_names = [f.name for f in node.fields]
        duplicate_names = [name for name in field_names if field_names.count(name) > 1]
        if duplicate_names:
            self.env._complain(node, f"Relation `{node.name}` has duplicate field names: {', '.join(duplicate_names)}.")
        # Check that all overloads are proper subtypes of the original relation
        for r in node.overloads:
            if r is node:
                self.env._complain(node, f"Relation `{node.name}` has an overload that is itself.")
            if r.name != node.name:
                self.env._complain(r, f"Relation `{node.name}` has an overload that has a different name.")
            if len(r.fields) != len(node.fields):
                self.env._complain(r, f"Relation `{node.name}` has an overload that has a different number of fields.")
            # TODO this test is disabled until we add back Int <: Number
            # from relationalai.semantics.metamodel import helpers
            # if not helpers.relation_is_proper_subtype(r, node):
            #     self.env._complain(r, f"Relation `{r.name}` is an overload but is not a proper subtype of the original relation.")
            if r.overloads:
                self.env._complain(r, f"Relation `{r.name}` has an overload that has an overload.")
            for f1, f2 in zip(r.fields, node.fields):
                if f1.input and not f2.input:
                    self.env._complain(r, f"Relation `{r.name}` has an overload that has an input field that is not present in the original relation.")
                if not f1.input and f2.input:
                    self.env._complain(r, f"Relation `{node.name}` has an input field that is not present in the overload.")

        # Recurse to visit the fields.
        return super().visit_relation(node, parent)

    def visit_var(self, node: ir.Var, parent: Optional[ir.Node]=None):
        # Do not constrain field types to be <: Any.
        if not isinstance(node.type, ir.UnionType) and not isinstance(node.type, ir.ScalarType):
            self.env._complain(node, f"Variable `{node.name}` has type {ir.type_to_string(node.type)}, which is not a scalar or union type.")
        # Do not recurse. No need to visit the type.
        return super().visit_var(node, parent)

    def visit_logical(self, node: ir.Logical, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.body):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_logical(node, parent)

    def visit_union(self, node: ir.Union, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.tasks):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_union(node, parent)

    def visit_sequence(self, node: ir.Sequence, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.tasks):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_sequence(node, parent)

    def visit_match(self, node: ir.Match, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.tasks):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_match(node, parent)

    def visit_until(self, node: ir.Until, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.body):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_until(node, parent)

    def visit_wait(self, node: ir.Wait, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.check):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_wait(node, parent)

    def visit_exists(self, node: ir.Exists, parent: Optional[ir.Node]=None):
        # The quantified variables should occur in the body.
        for x in node.vars:
            if not CheckModel._variable_occurs_in(x, node.task):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is quantified but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_exists(node, parent)

    def visit_forall(self, node: ir.ForAll, parent: Optional[ir.Node]=None):
        # The quantified variables should occur in the body.
        for x in node.vars:
            if not CheckModel._variable_occurs_in(x, node.task):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is quantified but not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_forall(node, parent)

    def visit_output(self, node: ir.Output, parent: Optional[ir.Node]):
        # Outputs are expected to be children of Logicals.
        if not isinstance(parent, ir.Logical):
            self.env._complain(node, f"Output is not a child of a Logical, but a {type(parent)}.")

        super().visit_output(node, parent)

    @staticmethod
    def _variable_occurs_in(node: ir.VarOrDefault, body: PyUnion[ir.Task, Tuple[ir.Task, ...]]) -> bool:
        if isinstance(body, tuple):
            return any(CheckModel._variable_occurs_in(node, b) for b in body)
        if isinstance(node, ir.Var):
            return node in visitor.collect_by_type(ir.Var, cast(ir.Node, body))
        elif isinstance(node, ir.Default):
            return node.var in visitor.collect_by_type(ir.Var, cast(ir.Node, body))
        else:
            return False

    def visit_loop(self, node: ir.Loop, parent: Optional[ir.Node]=None):
        # The hoisted variables should occur in the body.
        for x in node.hoisted:
            if not CheckModel._variable_occurs_in(x, node.body):
                self.env._complain(node, f"Variable {ir.node_to_string(x).strip()} is hoisted but not used in the body of {ir.node_to_string(node).strip()}.")
        if not CheckModel._variable_occurs_in(node.iter, node.body):
            self.env._complain(node, f"Variable {node.iter} is the loop iterator but is not used in the body of {ir.node_to_string(node).strip()}.")
        return super().visit_loop(node, parent)

    def visit_update(self, node: ir.Update, parent: Optional[ir.Node]=None):
        if len(node.args) != len(node.relation.fields):
            self.env._complain(node, f"{ir.node_to_string(node).strip()} has {len(node.args)} arguments but relation {node.relation.name} has {len(node.relation.fields)} fields")
        # Updates are expected to be children of Logicals.
        if not isinstance(parent, ir.Logical):
            self.env._complain(node, f"Update is not a child of a Logical, but a {type(parent)}.")
        return super().visit_update(node, parent)

    def visit_lookup(self, node: ir.Lookup, parent: Optional[ir.Node]=None):
        if len(node.args) != len(node.relation.fields):
            self.env._complain(node, f"{ir.node_to_string(node).strip()} has {len(node.args)} arguments but relation {node.relation.name} has {len(node.relation.fields)} fields")
        return super().visit_lookup(node, parent)

    def visit_construct(self, node: ir.Construct, parent: Optional[ir.Node]=None):
        if not node.values:
            self.env._complain(node, f"Construct {ir.node_to_string(node).strip()} should have at least 1 value. You cannot construct something from nothing.")
        return super().visit_construct(node, parent)

    def visit_aggregate(self, node: ir.Aggregate, parent: Optional[ir.Node]=None):
        agg = node.aggregation
        if len(agg.fields) < 1:
            self.env._complain(node, f"Aggregation `{agg.name}` should have at least 1 field, found {len(agg.fields)}.")
            return

        inputs = []
        outputs = []
        for f in agg.fields:
            if f.input:
                if outputs:
                    self.env._complain(node, f"Aggregation `{agg.name}` should declare all input fields before any output fields.")
                inputs.append(f)
            else:
                outputs.append(f)

        # Now let's wire up the types.

        # Inputs and outputs.
        if len(node.args) != len(inputs) + len(outputs):
            self.env._complain(node, f"Aggregation `{agg.name}` expects {len(inputs) + len(outputs)} arguments, but has {len(node.args)} arguments instead.")

        return super().visit_aggregate(node, parent)
