# type: ignore
import re
from typing import Union, Callable, Tuple, List, Optional, Sequence as PySequence

from v0.relationalai.early_access.dsl import Relation, AssertedRelation
from v0.relationalai.early_access.dsl.core.relations import ExportRelation
from v0.relationalai.early_access.dsl.ontologies.export import Export
from v0.relationalai.early_access.dsl.ontologies.raw_source import RawSource
from v0.relationalai.semantics.metamodel import ir, builtins, types, factory as f
from v0.relationalai.semantics.metamodel.types import Any, Symbol
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set

from v0.relationalai.early_access.dsl.core.constraints.predicate.atomic import Atom
from v0.relationalai.early_access.dsl.core.constraints.scalar import ScalarConstraint
from v0.relationalai.early_access.dsl.core.exprs import Wildcard
from v0.relationalai.early_access.dsl.core.exprs.scalar import Literal, BinaryScalarExpr
from v0.relationalai.early_access.dsl.core.logic import RelVariable
from v0.relationalai.early_access.dsl.core.logic.aggregation import Aggregation
from v0.relationalai.early_access.dsl.core.logic.exists import ExistentialConstraint
from v0.relationalai.early_access.dsl.core.rules import Rule, Annotation
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.core.types.standard import Boolean, Hash, Integer, Decimal, Float, Double, \
    BigInteger, String, Date, DateTime, RowId
from v0.relationalai.early_access.dsl.ontologies.models import Model

class CompilerContext:
    def __init__(self):
        self.var_map:dict[int, ir.Var] = {}
        self.items:OrderedSet[ir.Task] = OrderedSet()
        self.project_away_vars_count:int = -1
        self.project_away_vars:OrderedSet[ir.Var] = OrderedSet()

    def to_var(self, item:Union[RelVariable, Literal], t:Optional[ir.Type] = None) -> ir.Var:
        entity_id  = item.entityid()
        if entity_id not in self.var_map:
            if isinstance(item, RelVariable):
                self.var_map[entity_id] = f.var(item.display(), t)
            else:
                self.var_map[entity_id] = f.lit(item.val)
        return self.var_map[entity_id]

    def project_away_var_name(self) -> str:
        self.project_away_vars_count += 1
        return f"_pa_{self.project_away_vars_count}"

    def to_project_away_var(self, t: ir.Type) -> ir.Var:
        var = f.var(self.project_away_var_name(), t)
        self.project_away_vars.add(var)
        return var

    def add(self, item:ir.Task):
        self.items.add(item)

    def clone(self):
        c = CompilerContext()
        c.var_map = self.var_map.copy()
        return c

class Compiler:
    def __init__(self):
        self.types: dict[Type, ir.Type] = {
                Hash: f.scalar_type("UInt128"),
                Boolean: types.Bool,
                Integer: types.Int128,
                Decimal: types.Decimal,
                Float: types.Number,
                Double: types.Number,
                String: types.String,
                BigInteger: f.scalar_type("Int128"),
                Date: f.scalar_type("Date"),
                DateTime: f.scalar_type("DateTime"),
                Symbol: types.Symbol,
                RowId: types.Sha1,
                Any: types.Any
        }
        self.relations: dict[int, ir.Relation] = {}

    def to_type(self, t: Type) -> ir.Type:
        if t not in self.types:
            if t._name in types.builtin_scalar_types_by_name:
                self.types[t] = types.builtin_scalar_types_by_name[t._name]
            else:
                self.types[t] = f.scalar_type(t._name)
        return self.types[t]

    @staticmethod
    def _parse_relation_name(name: str, producer: Callable[[str, Any], Union[ir.Field, ir.Var]]) \
            -> Tuple[str, List[Union[ir.Field, ir.Var]]]:
        parts = re.split(r'(?<!:):(?!:)', name)
        if len(parts) > 1:
            var_list = [producer(f":{part}", types.Symbol) for part in parts[1:]]
            return parts[0], var_list
        return name, []

    def to_relation(self, ctx: CompilerContext, item:Atom, name:str) -> ir.Relation:
        # We use `item.relcomp.entityid()` instead of `item.entityid()`
        # to ensure that there is only one instance of a relation instead of multiple instances.
        #
        # Example:
        # - `test(x in Int, y in DateTime)`
        # - `test(y in Int, x in DateTime)`
        #
        # These will be considered the same relation.
        entity_id = item.relcomp.entityid()
        if entity_id not in self.relations:
            if name in builtins.builtin_relations_by_name:
                self.relations[entity_id] = builtins.builtin_relations_by_name[name]
            else:
                name, fields = self._parse_relation_name(name, f.field)
                fields.extend(
                    f.field(
                        arg.display() if not isinstance(arg, Wildcard) else ctx.project_away_var_name(),
                        self.to_type(role.root_unconstrained_type())
                    )
                    for arg, role in zip(item.args, item.relcomp._signature._types)
                )
                annotations = [builtins.external_annotation] if isinstance(item.relcomp, AssertedRelation) else []
                self.relations[entity_id] = f.relation(name, fields, annos=annotations)
        return self.relations[entity_id]

    def to_args(self, ctx: CompilerContext, item: Atom) -> tuple[list[ir.Value], list[ir.Value]]:
        args_list = []
        project_away_vars = []

        for arg, role in zip(item.args, item.relcomp._signature._types):
            if isinstance(arg, Wildcard):
                project_away_var = ctx.to_project_away_var(self.to_type(role.root_unconstrained_type()))
                project_away_vars.append(project_away_var)
                args_list.append(project_away_var)
            else:
                args_list.append(self.to_var(ctx, arg))

        return args_list, project_away_vars

    def to_vars(self, ctx:CompilerContext, item:ExistentialConstraint) -> set[ir.Var]:
        return {self.to_var(ctx, cur) for cur in item._scalars.values()}

    def to_var(self, ctx:CompilerContext, item:Union[RelVariable, Literal]) -> ir.Var:
        return ctx.to_var(item, self.to_type(item._type.root_unconstrained_type())) \
            if isinstance(item, RelVariable) else ctx.to_var(item)

    def compile_head(self, ctx:CompilerContext, head:Atom, original_name:str,
                     annotations: Optional[PySequence[ir.Annotation]]=None) -> ir.Task:
        name, sig_vars = self._parse_relation_name(original_name, f.var)
        sig_vars.extend(self.to_var(ctx, cur) for cur in head.args)
        return self._compile_output(head, sig_vars) if name == 'output' \
            else f.derive(self.to_relation(ctx, head, original_name), sig_vars, annotations)

    @staticmethod
    def _compile_output(item:Atom, sig_vars: List[Union[ir.Field, ir.Var]]):
        annotations = [builtins.export_annotation, builtins.external_annotation] \
            if isinstance(item.relcomp, ExportRelation) else []
        return f.output([(var.name, var) for var in sig_vars], annos=annotations)

    @staticmethod
    def _compile_annotations(annotations:PySequence[Annotation]) -> Optional[PySequence[ir.Annotation]]:
        return [f.annotation(f.relation(str(a), []), []) for a in annotations]

    def compile_atom(self, ctx:CompilerContext, atom:Atom) -> Union[ir.Construct, ir.Lookup, ir.Not]:
        original_name = atom.relcomp.qualified_name()
        name, args = self._parse_relation_name(original_name, f.var)
        if name.startswith('^'):
            vs = tuple(self.to_var(ctx, arg) for arg in atom.args[:-1])
            return ir.Construct(None, (name[1:], *vs), self.to_var(ctx, atom.args[-1]))
        else:
            atom_args, project_away_vars = self.to_args(ctx, atom)
            args.extend(atom_args)
            task = f.lookup(self.to_relation(ctx, atom, original_name), args)
            if len(project_away_vars) > 0:
                task = f.exists(list(project_away_vars), f.logical([task]))
            return f.not_(task) if atom.negated else task

    def _compile_scalar_expressions(self, ctx, scalar_constraint):
        left = scalar_constraint.left
        right = scalar_constraint.right

        expr = right if isinstance(right, (BinaryScalarExpr, Aggregation)) else left
        other = left if expr is right else right

        return (
            self._compile_binary_scalar_expressions(ctx, expr, other)
            if isinstance(expr, BinaryScalarExpr)
            else self._compile_aggregation(ctx, expr, other)
        )

    # Example of a binary scalar expression: ( c = a / b ) or ( a / b = c )
    def _compile_binary_scalar_expressions(self, ctx, left:BinaryScalarExpr, right:RelVariable):
        args = [self.to_var(ctx, left._left), self.to_var(ctx, left._right), self.to_var(ctx, right)]
        return f.lookup(builtins.builtin_relations_by_name[left.op()], args)

    # Example of an aggregation:
    #   - ( d = sum[(e): l1(c, e) and l2(a, e) ] ) or
    #   - ( sum[(e): l1(c, e) and l2(a, e) ] = d )
    # Expected IR:
    #   Logical
    #     Lookup l1(c, e)
    #     Lookup l2(a, e)
    #     Aggregate sum( [], [a, c], [e, d] )
    #     Hoist d a c
    #
    # We need to handle `count` aggregation differently.
    #   - ( d = count[(e): l1(e) ] )
    # Expected IR:
    #   Logical
    #     Lookup l1(e)
    #     Aggregate count( [e], [], [d] )
    #     Hoist d
    def _compile_aggregation(self, ctx, left:Aggregation, right:RelVariable) -> ir.Aggregate:
        method = left._method
        result_var = self.to_var(ctx, right)
        vargs = [self.to_var(ctx, var) for var in left._scalars.values()]
        items, lookup_args = self._compile_atoms_and_scalar_constraints(ctx, left._atoms.values(), left._sconstraints.values())
        group_vars = lookup_args - vargs
        agg_relation = builtins.builtin_relations_by_name[method]
        projection = vargs if self._is_count_aggregation(method) else vargs[:-1]
        args = [result_var] if self._is_count_aggregation(method) else [vargs[-1], result_var]
        items.add(f.aggregate(agg_relation, projection, group_vars.list, args))
        return f.logical(list(items), [result_var, *group_vars.list])

    def compile_scalar_constraint(self, ctx:CompilerContext, scalar_constraint:ScalarConstraint) -> ir.Task:
        if all(isinstance(side, BinaryScalarExpr) for side in (scalar_constraint.left, scalar_constraint.right)):
            raise Exception("It's not allowed for left and right operands to be BinaryScalarExpr.")
        if any(isinstance(side, (BinaryScalarExpr, Aggregation)) for side in (scalar_constraint.right, scalar_constraint.left)):
            return self._compile_scalar_expressions(ctx, scalar_constraint)
        else:
            args = [self.to_var(ctx, scalar_constraint.left), self.to_var(ctx, scalar_constraint.right)]
            return f.lookup(builtins.builtin_relations_by_name[scalar_constraint.op], args)

    # TODO: Replace to this one when we implement this in the to Rel Emitter
    # def compile_existential(self, ctx:CompilerContext, existential:ExistentialConstraint) -> ir.Task:
    #     items, vargs = (self._compile_atoms_and_scalar_constraints(ctx, existential._atoms.values(), existential._sconstraints.values()))
    #     return f.logical(list(items), (vargs - self.to_vars(ctx, existential)).list)

    def compile_existential(self, ctx:CompilerContext, existential:ExistentialConstraint) -> ir.Task:
        items = ordered_set()
        for atom in existential._atoms.values():
            items.add(self.compile_atom(ctx, atom))
        for scalar_constraint in existential._sconstraints.values():
            items.add(self.compile_scalar_constraint(ctx, scalar_constraint))
        return f.exists(list(self.to_vars(ctx, existential)), f.logical(list(items)))

    def _compile_atoms_and_scalar_constraints(self, ctx: CompilerContext, atoms: [Atom], scalar_constraints: [ScalarConstraint]) \
            -> Tuple[OrderedSet[ir.Task], OrderedSet[ir.Var]]:
        items = ordered_set()
        vargs = ordered_set()
        for atom in atoms:
            comp_atom = self.compile_atom(ctx, atom)
            if not isinstance(comp_atom, ir.Construct):
                vargs.update(arg for arg in comp_atom.args if self._arg_filter(arg))
            items.add(comp_atom)
        for scalar_constraint in scalar_constraints:
            comp_scalar = self.compile_scalar_constraint(ctx, scalar_constraint)
            if isinstance(comp_scalar, ir.Lookup):
                vargs.update(arg for arg in comp_scalar.args if self._arg_filter(arg))
            elif isinstance(comp_scalar, ir.Logical):
                vargs.update(comp_scalar.hoisted)
            items.add(comp_scalar)
        return items, vargs

    @staticmethod
    def _arg_filter(arg):
        return not isinstance(arg, ir.Literal) and not arg.name.startswith(":")

    @staticmethod
    def _is_count_aggregation(method: str) -> bool:
        return method == "count"

    def compile_rule(self, rule:Rule, name:str) -> ir.Task:
        ctx = CompilerContext()
        for existential in rule._existentials.values():
            if len(existential._scalars) != 0:
                ctx.add(self.compile_existential(ctx, existential))
            else:
                for atom in existential._atoms.values():
                    ctx.add(self.compile_atom(ctx, atom))
                for scalar_constraint in existential._sconstraints.values():
                    ctx.add(self.compile_scalar_constraint(ctx, scalar_constraint))
        for atom in rule._atoms.values():
            ctx.add(self.compile_atom(ctx, atom))
        for scalar_constraint in rule._sconstraints.values():
            ctx.add(self.compile_scalar_constraint(ctx, scalar_constraint))
        ctx.add(self.compile_head(ctx, rule.head, name, self._compile_annotations(rule._annotations)))
        return f.logical(list(ctx.items))

    def compile_raw_sources(self, raw_sources: OrderedSet[RawSource]) -> ir.Model:
        return f.compute_model(
            f.logical([
                f.logical([f.derive(builtins.raw_source, [rs.language, rs.raw_source])])
                for rs in raw_sources
            ])
        )

    def compile_model(self, model: Model) -> ir.Model:
        return f.compute_model(
            f.logical(
                [self.compile_rule(rule, relation.qualified_name())
                 for relation in model._relations.values()
                 for rule in relation._rules]
            )
        )

    def compile_queries(self, queries: OrderedSet[Relation]) -> ir.Model:
        return f.compute_model(
            f.logical([
                self.compile_rule(rule, query.qualified_name())
                for query in queries
                for rule in query._rules
            ])
        )

    def compile_export(self, export: Export) -> ir.Model:
        return f.compute_model(
            f.logical([
                self.compile_rule(rule, column.qualified_name())
                for column in export.columns
                for rule in column._rules
            ])
        )
