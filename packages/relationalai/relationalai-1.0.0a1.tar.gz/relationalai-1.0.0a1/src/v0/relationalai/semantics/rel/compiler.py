from __future__ import annotations
from typing import Any, Iterable, Sequence as PySequence, cast, Tuple, Union
from dataclasses import dataclass, field
from decimal import Decimal as PyDecimal

from v0.relationalai.semantics.metamodel import ir, compiler as c, builtins as bt, types, visitor, helpers, factory as f
from v0.relationalai.semantics.metamodel.typer import Checker, InferTypes
from v0.relationalai.semantics.metamodel.typer.typer import to_base_primitive, to_type, _NON_PARAMETRIC_PRIMITIVES
from v0.relationalai.semantics.metamodel.visitor import ReadWriteVisitor
from v0.relationalai.semantics.metamodel.util import OrderedSet, group_by, NameCache, ordered_set

from v0.relationalai.semantics.rel import rel, rel_utils as u, builtins as rel_bt

from ..metamodel.rewrite import (Flatten, ExtractNestedLogicals, DNFUnionSplitter, DischargeConstraints, FormatOutputs)
from ..lqp.rewrite import CDC, ExtractCommon, ExtractKeys, FunctionAnnotations, QuantifyVars, Splinter, SplitMultiCheckRequires

import math


#--------------------------------------------------
# Compiler
#--------------------------------------------------

class Compiler(c.Compiler):
    def __init__(self):
        super().__init__([
            SplitMultiCheckRequires(),
            FunctionAnnotations(),
            DischargeConstraints(),
            Checker(),
            CDC(), # specialize to physical relations before extracting nested and typing
            ExtractNestedLogicals(), # before InferTypes to avoid extracting casts
            InferTypes(),
            DNFUnionSplitter(),
            ExtractKeys(),
            FormatOutputs(),
            ExtractCommon(),
            Flatten(),
            Splinter(),
            QuantifyVars(),
        ])
        self.model_to_rel = ModelToRel()

    def do_compile(self, model: ir.Model, options:dict={}) -> str:
        return str(self.model_to_rel.to_rel(model, options=options))

COMPILER_OPTIONS = [
    # do not generated declarations for relations read by the model but not written to
    "no_declares",
    # do not GNF the output relation, keeping it wide
    "wide_outputs"
]

@dataclass
class ModelToRel:
    """ Generates Rel from an IR Model, assuming the compiler rewrites were done. """

    relation_name_cache: NameCache = field(default_factory=NameCache)
    rule_name_cache: NameCache = field(default_factory=NameCache)

    # Map a rel variable to one with a different name
    var_map: dict[rel.Var, rel.Var] = field(default_factory=dict)

    #--------------------------------------------------
    # Public API
    #--------------------------------------------------

    def to_rel(self, model: ir.Model, options:dict = {}) -> rel.Program:
        self._register_external_relations(model)

        rules = self._generate_rules(model)
        reads = self._rel_reads(rules)
        declares = [] if options.get("no_declares") else self._generate_declares(model)
        self._rel_reads(declares, reads)
        return rel.Program(tuple([
            *self._generate_builtin_defs(model, reads),
            *declares,
            *rules,
        ]))

    #--------------------------------------------------
    # Top level handlers
    #--------------------------------------------------

    def _generate_builtin_defs(self, model: ir.Model, reads:OrderedSet[str]) -> list[rel.Def]:
        defs = []

        for t in model.types:
            # TODO - some of these types are never used, we should not generate them, but we
            # need to replace the rel_reads function with something that collects those types
            # during generation
            if isinstance(t, ir.DecimalType):
                defs.append(
                    rel.Def(u.rel_typename(t),
                        tuple([rel.Var("x")]),
                        rel.atom("::std::common::FixedDecimal",
                            tuple([rel.MetaValue(types.digits_to_bits(t.precision)), rel.MetaValue(t.scale), rel.Var("x")])),
                        tuple([rel.Annotation("inline", ())]),
                    ),
                )

        if "pyrel_inf" in reads:
            defs.append(
                rel.Def("pyrel_inf",
                    tuple([rel.Var("x")]),
                    rel.atom("::std::common::infinity", tuple([rel.MetaValue(64), rel.Var("x")])),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_NaN" in reads:
            defs.append(
                rel.Def("pyrel_NaN",
                    tuple([rel.Var("x")]),
                    rel.atom("::std::common::nan", tuple([rel.MetaValue(64), rel.Var("x")])),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_ID" in reads:
            defs.append(rel.Def("pyrel_ID",
                tuple([rel.Var("x")]),
                rel.Or(OrderedSet[rel.Expr].from_iterable([
                    rel.atom("::std::common::UInt128", tuple([rel.Var("x")])),
                    rel.atom("::std::common::Missing", tuple([rel.Var("x")])),
                ])),
                tuple([rel.Annotation("inline", ())]),
            ))

        if "pyrel_count" in reads:
            defs.append(
                rel.Def("pyrel_count",
                    tuple([rel.Var("{R}"), rel.Var("y")]),
                    rel.Exists(
                        tuple([rel.Var("z")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::count", tuple([rel.Var("R"), rel.Var("z")])),
                            rel.Atom(self._convert_abs(types.Int64, types.Int128), tuple([rel.Var("z"), rel.Var("y")])),
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_sort" in reads:
            defs.append(
                rel.Def("pyrel_sort",
                    tuple([rel.Var("{R}"), rel.Var("n"), rel.Var("r", varargs=True)]),
                    rel.Exists(
                        tuple([rel.Var("z")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::sort", tuple([rel.Var("R"), rel.Var("z"), rel.Var("r", varargs=True)])),
                            rel.Atom(self._convert_abs(types.Int64, types.Int128), tuple([rel.Var("z"), rel.Var("n")])),
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_reverse_sort" in reads:
            defs.append(
                rel.Def("pyrel_reverse_sort",
                    tuple([rel.Var("{R}"), rel.Var("n"), rel.Var("r", varargs=True)]),
                    rel.Exists(
                        tuple([rel.Var("z")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::reverse_sort", tuple([rel.Var("R"), rel.Var("z"), rel.Var("r", varargs=True)])),
                            rel.Atom(self._convert_abs(types.Int64, types.Int128), tuple([rel.Var("z"), rel.Var("n")])),
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_top" in reads:
            defs.append(
                rel.Def("pyrel_top",
                    tuple([rel.Var("k"), rel.Var("{R}"), rel.Var("n"), rel.Var("r", varargs=True)]),
                    rel.Exists(
                        tuple([rel.Var("z")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::top", tuple([rel.Var("k"), rel.Var("R"), rel.Var("z"), rel.Var("r", varargs=True)])),
                            rel.Atom(self._convert_abs(types.Int64, types.Int128), tuple([rel.Var("z"), rel.Var("n")])),
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_bottom" in reads:
            defs.append(
                rel.Def("pyrel_bottom",
                    tuple([rel.Var("k"), rel.Var("{R}"), rel.Var("n"), rel.Var("r", varargs=True)]),
                    rel.Exists(
                        tuple([rel.Var("z")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::bottom", tuple([rel.Var("k"),rel.Var("R"), rel.Var("z"), rel.Var("r", varargs=True)])),
                            rel.Atom(self._convert_abs(types.Int64, types.Int128), tuple([rel.Var("z"), rel.Var("n")])),
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                ),
            )

        if "pyrel_dates_period_days" in reads:
            defs.append(
                rel.Def("pyrel_dates_period_days",
                    tuple([rel.Var("a"), rel.Var("b"), rel.Var("c")]),
                    rel.Exists(
                        tuple([rel.Var("d")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::dates_period_days",
                                     tuple([rel.Var("a"), rel.Var("b"), rel.Var("d")])),
                            rel.atom("::std::common::^Day",
                                     tuple([rel.Var("c"), rel.Var("d")]))
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                    ),
            )

        if "pyrel_datetimes_period_milliseconds" in reads:
            defs.append(
                rel.Def("pyrel_datetimes_period_milliseconds",
                    tuple([rel.Var("a"), rel.Var("b"), rel.Var("c")]),
                    rel.Exists(
                        tuple([rel.Var("m")]),
                        rel.And(ordered_set(
                            rel.atom("::std::common::datetimes_period_milliseconds",
                                     tuple([rel.Var("a"), rel.Var("b"), rel.Var("m")])),
                            rel.atom("::std::common::^Millisecond",
                                     tuple([rel.Var("c"), rel.Var("m")]))
                        )),
                    ),
                    tuple([rel.Annotation("inline", ())]),
                    ),
            )

        if "pyrel_regex_search" in reads:
            raise NotImplementedError("pyrel_regex_search is not implemented")

        return defs

    @staticmethod
    def _convert_abs(from_type: ir.Type, to_type: ir.Type):
        if from_type == types.Int64 and to_type == types.Float:
            return rel.Identifier("::std::common::int_float_convert")
        elif from_type == types.Float and to_type == types.Int64:
            return rel.Identifier("::std::common::float_int_convert")
        else:
            input_type = u.rel_typename(from_type)
            output_type = u.rel_typename(to_type)
            return rel.RelationalAbstraction(
                tuple([rel.Var("val_x", type=input_type), rel.Var("val_y", type=output_type)]),
                rel.Exists(
                    tuple([rel.Var("type_x"), rel.Var("type_y")]),
                    rel.And(ordered_set(
                        # Since we declared them to be the types we're converting from and to, we can just use the types of x and y here.
                        # The Rel compiler will use the static type of the variable to compute the Type values.
                        rel.atom("rel_primitive_typeof", tuple([rel.Var("val_x"), rel.Var("type_x")])),
                        rel.atom("rel_primitive_typeof", tuple([rel.Var("val_y"), rel.Var("type_y")])),
                        rel.atom("rel_primitive_convert", tuple([rel.Var("type_x"), rel.Var("type_y"), rel.Var("val_x"), rel.Var("val_y")])),
                    )),
                )
            )

    def _generate_declares(self, m: ir.Model) -> list[rel.Declare]:
        """
        Generate declare statements for relations declared by the model and:
            - not built-ins
            - not used as an annotation
            - not annotated as external
            - do not start with ^ (for hardcoded Rel constructors)
            - and are never the target of an update
        """
        rw = ReadWriteVisitor()
        m.accept(rw)

        root = cast(ir.Logical, m.root)

        annotations = [anno.relation for anno in visitor.collect_by_type(ir.Annotation, m.root)]
        reads = m.relations - rw.writes(root) - bt.builtin_relations - bt.builtin_overloads - bt.builtin_annotations - annotations
        reads = list(filter(lambda r: not r.name.startswith('^') and not helpers.is_external(r), reads))

        primitive_type_names = OrderedSet.from_iterable([t.name for t in _NON_PARAMETRIC_PRIMITIVES])
        declares: list[rel.Declare] = []
        for r in reads:
            if r.name in rel.infix or r.name in u.OPERATORS:
                continue

            if helpers.is_from_cast(r):
                continue

            # TODO: should address the root of the issue
            # In some cases we might end up with explicit Concepts for primitives in the model
            if r.name in primitive_type_names or r.name.startswith("Decimal("):
                continue

            # In case parameter name starts with ':' use its name instead of type name
            def requires_name(fld: ir.Field):
                if isinstance(fld.type, ir.ScalarType):
                    t = fld.type
                    if t == types.Symbol:
                        return rel.MetaValue(fld.name[1:])
                    else:
                        return rel.Var(name=u.sanitize(fld.name.lower()), type=u.rel_typename(t))
                else:
                    return rel.Var(u.sanitize(fld.name.lower()))
            head = tuple([requires_name(f) for f in r.fields])

            # Example: declare test(:a, _x0 in Int, _x1 in String) requires true
            declares.append(rel.Declare(
                rel.atom(self._relation_name(r), head),
                rel.true  # `requires true` does not generate any constraints, that affects performance on the RAI side
            ))
        return declares

    def _generate_rules(self, m: ir.Model) -> list[Union[rel.Def, rel.RawSource]]:
        """ Generate rules for the root of this model.

        Assumes the model already was processed such that it contains a root Logical with
        children that are also Logical tasks representing the rules to generate.
        """
        rules: list[Union[rel.Def, rel.RawSource]] = []
        root = cast(ir.Logical, m.root)
        for child in root.body:
            rules.extend(self._generate_rule(cast(ir.Logical, child)))
        return rules

    def _generate_rule(self, rule: ir.Logical) -> list[Union[rel.Def, rel.RawSource]]:
        """ Generate rules for a nested Logical in a model.

        This is for a top-level Logical, under the root Logical.
        """
        # reset the name cache for each rule
        self.rule_name_cache = NameCache()
        effects, other, aggregates, ranks = self._split_tasks(rule.body)
        if not effects or (aggregates and ranks):
            # nothing to generate for this Logical
            return []

        elif len(effects) == 1:
            # a single effect with a body becomes a single rule
            effect = effects[0]

            # deal with raw sources
            if isinstance(effect, ir.Update) and effect.relation == bt.raw_source:
                # TODO: remove this once the type checker checks this.
                assert(len(effect.args) == 2 and isinstance(effect.args[0], ir.Literal) and isinstance(effect.args[1], ir.Literal))
                if effect.args[0].value != "rel":
                    return []
                return [rel.RawSource(cast(str, effect.args[1].value))]
            else:
                args, lookups, rel_equiv = self._effect_args(effect)
                if lookups:
                    other.extend(lookups)
                return [rel.Def(
                    self._effect_name(effect),
                    args,
                    rel.create_and([
                        self.generate_logical_body(other, aggregates, ranks),
                        *rel_equiv
                    ]),
                    self.generate_annotations(effect.annotations)
                )]
        else:
            # currently we can only deal with multiple effects if they are all updates with
            # no body, which is the pattern for inserting hardcoded data.
            if other or aggregates:
                raise NotImplementedError("Body in logical task with multiple effects.")
            if any(isinstance(effect, ir.Output) for effect in effects):
                raise NotImplementedError("Output in logical task with multiple effects.")
            sample = cast(ir.Update, effects[0]).effect
            if any(cast(ir.Update, effect).effect != sample for effect in effects):
                raise NotImplementedError("Different types of effects in logical task.")

            # Group updates by relation name
            relation_groups = group_by(cast(list[ir.Update], effects), lambda e: self._relation_name(e.relation))

            # Process each relation group
            defs = []
            for name, updates in relation_groups.items():
                effects_to_union = []
                for update in updates:
                    update_args, lookups, rel_equiv = self._effect_args(update)
                    if update_args:
                        defs.append(
                            rel.Def(
                                name,
                                update_args,
                                rel.create_and([
                                    self.generate_body_expr(lookups),
                                    *rel_equiv
                                ]),
                                self.generate_annotations(update.annotations)
                            )
                        )
                    else:
                        effects_to_union.append(update)

                if effects_to_union:
                    update = updates.some()
                    args, lookups, rel_equiv = self._effect_args(update)
                    bodies = []
                    for update in effects_to_union:
                        bodies.append(self.handle(update))
                    for lookup in lookups:
                        bodies.append(self.handle(lookup))

                    defs.append(
                        rel.Def(
                            name,
                            args,
                            rel.create_and([
                                rel.Union(tuple(bodies)),
                                *rel_equiv
                            ]),
                            self.generate_annotations(update.annotations)
                        )
                    )
            return defs

    def generate_logical_body(self, other, aggregates, ranks):
        """ Generate the body of a rule for a Logical that contains these aggregates/ranks
        and other tasks (i.e., no effects)."""

        if aggregates:
            # push the body into the aggregates; this assumes a rewrite pass already
            # prepared the body to contain only what's needed by the aggregates
            exprs = []
            for agg in aggregates:
                # The variables declared in the relational abstraction are the agg's "projection" + "over"
                abs_vars = OrderedSet.from_iterable(agg.projection)
                result = []
                for arg in agg.args:
                    if helpers.is_aggregate_input(arg, agg):
                        new_arg = arg if isinstance(arg, ir.Var) else self.handle(arg)
                        abs_vars.add(new_arg)
                    else:
                        result.append(self.handle(arg))

                old_var_map = self.var_map
                self.var_map = {}

                common_vars = OrderedSet.from_iterable(agg.projection) & agg.group
                abs_body_exprs = []
                for v in common_vars:
                    orig_rel_v = self.handle_var(v)
                    inner_rel_v = rel.Var("_t" + orig_rel_v.name)
                    self.var_map[orig_rel_v] = inner_rel_v
                    eq_expr = rel.BinaryExpr(orig_rel_v, "=", inner_rel_v)
                    abs_body_exprs.append(eq_expr)

                abs_head = self.handle_list(tuple(abs_vars))
                abs_body = self.generate_body_expr(other)
                if abs_body_exprs:
                    abs_body = rel.create_and([abs_body, *abs_body_exprs])
                rel_abstraction = rel.RelationalAbstraction(abs_head, abs_body)

                self.var_map = old_var_map

                exprs.append(rel.atom(
                    u.rel_operator(agg.aggregation.name),
                    tuple([ rel_abstraction, *result ])
                ))
            return exprs[0] if len(exprs) == 1 else rel.create_and(exprs)
        elif ranks:
            # push the body into the aggregates; this assumes a rewrite pass already
            # prepared the body to contain only what's needed by the aggregates
            exprs = []
            for rank in ranks:
                rel_name, has_limit = self.compute_rank_limit_info(rank)
                old_var_map = self.var_map
                self.var_map = {}

                abs_vars = ordered_set()
                abs_body_exprs = []
                # Rename the sorted vars to avoid conflicts with the result vars.
                # We sort the requested args, augmented with the keys (projection).
                # The keys have to be present to preserve bag semantics, but should
                # not affect the ranking. Thus they have to go at the end of the list.
                # Create a set to deduplicate vars appearing in both.
                raw_args = OrderedSet.from_iterable(rank.args + rank.projection)
                for ir_v in raw_args:
                    orig_rel_v = self.handle_var(ir_v)
                    if ir_v in rank.projection and ir_v not in rank.group:
                        inner_rel_v = rel.Var("_t" + orig_rel_v.name)
                        self.var_map[orig_rel_v] = inner_rel_v
                    else:
                        inner_rel_v = rel.Var("_t" + orig_rel_v.name)
                        self.var_map[orig_rel_v] = inner_rel_v
                        # inner_rel_v = rel.Var(orig_rel_v.name)
                    if ir_v in rank.group:
                        eq_expr = rel.BinaryExpr(orig_rel_v, "=", inner_rel_v)
                        abs_body_exprs.append(eq_expr)
                    abs_vars.add(inner_rel_v)

                abs_body = self.generate_body_expr(other)
                if abs_body_exprs:
                    abs_body = rel.create_and([abs_body, *abs_body_exprs])
                rel_abstraction = rel.RelationalAbstraction(tuple(abs_vars), abs_body)

                self.var_map = old_var_map

                out_vars = [self.handle_var(v) for v in raw_args]
                params = [rel_abstraction, self.handle_var(rank.result), *out_vars]
                if has_limit:
                    params.insert(0, rank.limit)
                exprs.append(rel.atom(rel_name, tuple(params)))

            return exprs[0] if len(exprs) == 1 else rel.create_and(exprs)
        else:
            # no aggregates or ranks, just return an expression for the body
            return self.generate_body_expr(other)

    def compute_rank_limit_info(self, rank: ir.Rank):
        if all(o for o in rank.arg_is_ascending):
            ascending = True
        elif all(not o for o in rank.arg_is_ascending):
            ascending = False
        else:
            raise Exception("Mixed orderings in rank are not supported yet.")
        has_limit = rank.limit != 0

        if ascending:
            rel_name = "pyrel_top" if has_limit else "pyrel_sort"
        else:
            rel_name = "pyrel_bottom" if has_limit else "pyrel_reverse_sort"
        return rel_name, has_limit

    def generate_body_expr(self, tasks: list[ir.Task]):
        """ Helper to generate the an expression from the tasks, wrapping in Ands if necessary. """
        if not tasks:
            return rel.true
        elif len(tasks) == 1:
            return self.handle(tasks[0])
        else:
            return rel.create_and([self.handle(b) for b in tasks])

    #--------------------------------------------------
    # IR handlers
    #--------------------------------------------------

    def handle(self, n: ir.Node):
        """ Dispatch to the appropriate ir.Node handler. """
        handler = getattr(self, f"handle_{n.kind}", None)
        if handler:
            return handler(n)
        else:
            raise Exception(f"Rel Compiler handler for '{n.kind}' node not implemented.")

    def handle_list(self, n: Iterable[ir.Node]):
        """ Dispatch each node to the appropriate ir.Node handler. """
        return tuple([self.handle(x) for x in n])

    def handle_value(self, type: ir.Type|None, value: Any) -> Union[rel.Primitive, rel.RelationalAbstraction, rel.MetaValue, rel.Var]:
        """ Handle the value (Node or Value) and wrap in a Metavalue if the type is Symbol. """
        # only handle if it is a Node (e.g. ir.Var or ir.Literal)
        v = self.handle(value) if isinstance(value, ir.Node) else value

        # type might be None for these so we have to handle them before the check below.
        if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
            x = rel.Var("_float")
            rel_name = "::std::common::infinity" if math.isinf(v) else "::std::common::nan"
            return rel.RelationalAbstraction(
                tuple([x]),
                rel.atom(rel_name, tuple([rel.MetaValue(64), x])),
            )

        if type is None:
            return cast(Union[rel.Primitive, rel.RelationalAbstraction, rel.MetaValue, rel.Var], v)

        # only wrap if v is a primitive (i.e. not a metavalue or a var, for example).
        base = to_base_primitive(type) or type
        if type == types.Symbol and isinstance(v, (str, int, float, bool)):
            return rel.MetaValue(v)
        elif isinstance(v, PyDecimal):
            if base == types.GenericDecimal:
                # generic decimals arrive here if that's the type of the field in the relation;
                # in that case, the typer made sure that the value is a Literal and the type in
                # the literal is the exact decimal we need. We can clean this up once we remove
                # support for native literals here, since it's not supported in the IR anymore.
                assert isinstance(value, ir.Literal)
                type = value.type
                assert isinstance(type, ir.DecimalType)
                precision = types.digits_to_bits(type.precision)
            else:
                # if it's not an GenericDecimal, it is a specific decimal and we just use it.
                assert isinstance(type, ir.DecimalType)
                precision = types.digits_to_bits(type.precision)
            x = rel.Var("_dec")
            return rel.RelationalAbstraction(
                tuple([x]),
                rel.atom("::std::common::decimal", tuple([rel.MetaValue(precision), rel.MetaValue(type.scale), v, x]))
            )

        elif base == types.Int128 and isinstance(v, int):
            x = rel.Var("_int")
            return rel.RelationalAbstraction(
                tuple([x]),
                rel.atom("::std::common::int", tuple([128, v, x]))
            )
        elif (base == types.UInt128 or base == types.RowId) and isinstance(v, int):
            x = rel.Var("_uint")
            return rel.RelationalAbstraction(
                tuple([x]),
                rel.atom("::std::common::uint", tuple([128, v, x]))
            )
        else:
            return cast(Union[rel.Primitive, rel.RelationalAbstraction, rel.MetaValue, rel.Var], v)

    def handle_value_list(self, types, values) -> list[Union[rel.Primitive, rel.MetaValue, rel.RelationalAbstraction, rel.Var]]:
        result = []
        for t, v in zip(types, values):
            # splat values that are "varargs"
            if isinstance(v, tuple) and isinstance(t, ir.ListType):
                for item in v:
                    result.append(self.handle_value(t, item))
            else:
                result.append(self.handle_value(t, v))
        return result

    #
    # DATA MODEL
    #
    def handle_scalartype(self, n: ir.ScalarType):
        return n.name
    # TODO - what to generate for other kinds of types?




    #
    # TASKS
    #
    def handle_logical(self, n: ir.Logical) -> rel.Expr:
        # Generate nested expressions for a nested logical
        effects, other, aggregates, ranks = self._split_tasks(n.body)
        if effects:
            raise Exception("Cannot process nested logical with effects.")
        elif aggregates and ranks:
            raise Exception("Cannot process nested logical with both aggregates and ranks.")
        return self.generate_logical_body(other, aggregates, ranks)

    def handle_union(self, n: ir.Union) -> rel.Expr:
        # Generate nested expressions for a nested logical
        body:list[rel.Expr] = []
        for t in n.tasks:
            body.append(self.handle(t))
        return rel.Or(OrderedSet.from_iterable(body))

    def handle_rank(self, n: ir.Rank) -> rel.Expr:
        return rel.atom("rank", tuple([self.handle_var(n.result)]))

    #
    # LOGICAL QUANTIFIERS
    #
    def handle_not(self, n: ir.Not):
        return rel.Not(self.handle(n.task))

    def handle_exists(self, n: ir.Exists):
        vars = self._remove_wildcards(n.vars)
        if vars:
            return rel.Exists(
                self.handle_vars(vars),
                self.handle(n.task)
            )
        else:
            # all vars are wildcards, no need for exists
            return self.handle(n.task)

    #
    # ITERATION
    #

    #
    # RELATIONAL OPERATIONS
    #

    def handle_vars(self, vars: Tuple[ir.Var, ...]):
        return tuple([self.handle_var(v) for v in vars])

    def handle_var(self, n: ir.Var):
        name = n.name if (n.name == "_" or n.name.startswith(':')) else f"_{self._var_name(n)}"
        v = rel.Var(name)
        return self.var_map.get(v, v)

    def handle_literal(self, n: ir.Literal):
        return self.handle_value(n.type, n.value)

    def handle_data(self, n: ir.Data):
        return rel.Atom(rel.Union(tuple([self.handle_value(None, d) for d in n])), tuple([self.handle(d) for d in n.vars]))

    def generate_annotations(self, annos: Iterable[ir.Annotation]):
        """ Helper to cast the handling of ir.Annotations into a tuple of rel.Annotations. """
        filtered_annos = list(filter(lambda anno: anno.relation.name in rel_bt.builtin_annotation_names, annos))
        rel_annos = cast(Tuple[rel.Annotation, ...], self.handle_list(filtered_annos))
        return rel_annos

    # standard handling mistreats the integer arg of ranked `@function(:checked, k)`
    def handle_ranked_function_annotation(self, n: ir.Annotation):
        assert n.relation == bt.function_ranked and len(n.args) == 2
        checked_lit = n.args[0]
        rank_lit = n.args[1]
        assert isinstance(checked_lit, ir.Literal) and isinstance(rank_lit, ir.Literal)
        checked = rel.MetaValue(checked_lit.value)
        rank = rank_lit.value
        return rel.Annotation(
            n.relation.name,
            (checked, rank)
        )

    def handle_annotation(self, n: ir.Annotation):
        # special treatment for (ranked) @function(:checked, k)
        if n.relation == bt.function_ranked:
            return self.handle_ranked_function_annotation(n)

        # we know that annotations won't have vars, so we can ignore that type warning
        return rel.Annotation(
            n.relation.name,
            tuple(self.handle_value_list(self._relation_types(n.relation), n.args)) # type:ignore
        )

    def handle_update(self, n: ir.Update):
        return rel.atom(
            self._relation_name(n.relation),
            tuple(self.handle_value_list(self._relation_types(n.relation), n.args))
        )


    def handle_lookup(self, n: ir.Lookup):
        # special cases
        if n.relation == bt.cast:
            return self.handle_cast(n)
        if n.relation == bt.parse_decimal:
            return self.handle_parse_decimal(n)
        if n.relation == bt.join:
            return self.handle_join(n)
        # only translate names to Rel operators if the relation is a built-in
        name = self._relation_name(n.relation)
        if bt.is_builtin(n.relation):
            name = u.rel_operator(name)
        types = self._relation_types(n.relation)
        return rel.atom(name, tuple(self.handle_value_list(types, n.args)))

    def handle_construct(self, n: ir.Construct):
        args = self.handle_value_list([None] * len(n.values), n.values) + [self.handle(n.id_var)]
        return rel.atom("rel_primitive_hash_tuple_uint128", tuple(args))


    #--------------------------------------------------
    # Built-in special cases
    #--------------------------------------------------
    def handle_cast(self, n: ir.Lookup):
        assert len(n.args) == 3
        (target_type, source, target) = n.args
        assert isinstance(target_type, ir.Type), f"Expected Type, got {type(target_type)}"
        from_type = to_type(source)
        rel_abstraction = self._convert_abs(from_type, target_type)
        types = (from_type, target_type)
        return rel.Atom(rel_abstraction, tuple(self.handle_value_list(types, (source, target))))

    def handle_parse_decimal(self, n: ir.Lookup):
        # parse_decimal in the metamodel is a binary relation, (value:String, var:DecimalType)
        # but we need to expand the lookup to (bits(var.precision), var.scale, value, var),
        # so we special case it here
        assert len(n.args) == 2
        value, var  = n.args
        assert isinstance(value, ir.Node)
        assert isinstance(var, ir.Var)
        typ = var.type
        assert isinstance(typ, ir.DecimalType)
        args = [
            rel.MetaValue(types.digits_to_bits(typ.precision)),
            rel.MetaValue(typ.scale),
            self.handle(value),
            self.handle(var)
        ]
        return rel.Atom(rel.Identifier("rel_primitive_parse_decimal"), tuple(args))

    def handle_join(self, n: ir.Lookup):
        assert len(n.args) == 3
        (strs, separator, target) = n.args
        # prepare binary relation for string_join.
        # string_join example: string_join[", ", {(1, "a"); (2, "b"); (3, "c")}]
        assert isinstance(separator, ir.Node)
        assert isinstance(target, ir.Var)
        assert isinstance(strs, tuple)
        str_args = []
        for i, s in enumerate(strs):
            assert isinstance(s, ir.Node)
            str_args.append(rel.Product((i, self.handle(s))))
        args = [
            self.handle(separator),
            rel.Union(tuple(str_args)),
            self.handle(target)
        ]
        return rel.Atom(rel.Identifier("::std::common::string_join"), tuple(args))

    #--------------------------------------------------
    # Helpers
    #--------------------------------------------------

    def _relation_types(self, relation: ir.Relation):
        return [f.type for f in relation.fields]

    def _relation_name(self, relation: ir.Relation):
        if helpers.is_external(relation) or helpers.builtins.is_builtin(relation):
            return relation.name
        return self.relation_name_cache.get_name(relation.id, relation.name, helpers.relation_name_prefix(relation))

    def _var_name(self, var: ir.Var):
        if var.name == "_":
            return "_"
        return self.rule_name_cache.get_name(var.id, u.sanitize(var.name.lower()))

    def _remove_wildcards(self, vars: tuple[ir.Var, ...]):
        return tuple(filter(lambda v: v.name != "_", vars))

    def _register_external_relations(self, model: ir.Model):
        # force all external relations to get a name in the cache, so that internal relations
        # cannot use those names in _relation_name
        for r in model.relations:
            if helpers.is_external(r):
                self.relation_name_cache.get_name(r.id, r.name)

    def _split_tasks(self, tasks: PySequence[ir.Task]) -> tuple[list[Union[ir.Update, ir.Output]], list[ir.Task], list[ir.Aggregate], list[ir.Rank]]:
        effects = []
        aggregates = []
        other_body = []
        ranks = []
        for task in tasks:
            if isinstance(task, (ir.Update, ir.Output)):
                effects.append(task)
            elif isinstance(task, ir.Aggregate):
                aggregates.append(task)
            elif isinstance(task, ir.Rank):
                ranks.append(task)
            else:
                other_body.append(task)
        return effects, other_body, aggregates, ranks


    def _effect_name(self, n: ir.Task):
        """ Return the name to be used for the effect (e.g. the relation name, output, etc). """
        if isinstance(n, ir.Output) and bt.export_annotation in n.annotations:
            return "Export_Relation"
        elif isinstance(n, ir.Output):
            return "output"
        elif isinstance(n, ir.Update):
            return self._relation_name(n.relation)
        else:
            raise Exception(f"Cannot retrieve effect name from node {type(n)}")

    def _effect_args(self, n: ir.Task) -> Tuple[Tuple[Any], list[ir.Task], list[rel.Expr]]:
        """
            Return the arguments for the head of an effect rule and a list of lookups to add
            to the body of the rule.

            The lookups may be necessary because Rel does not allow "missing" in the head,
            so we create a new variable, set the variable to missing in the body (the
            lookup) and use the variable in the head.

            E.g. output(None) becomes output(x): { x = missing }
        """
        orig_args = []
        handled_args = []
        if isinstance(n, ir.Output):
            args = helpers.output_values(n.aliases)
            orig_args.extend(args)
            handled_args.extend(self.handle_value_list([None] * len(args), args))
        elif isinstance(n, ir.Update):
            orig_args.extend(n.args)
            handled_args.extend(self.handle_value_list(self._relation_types(n.relation), n.args))
        else:
            raise Exception(f"Cannot retrieve effect params from node {type(n)}")

        assert len(orig_args) == len(handled_args)
        args, lookups, rel_equiv = [], [], []
        for idx, handled in enumerate(handled_args):
            if handled is None:
                var = ir.Var(types.Any, "head")
                args.append(self.handle(var))
                lookups.append(f.lookup(bt.eq, [var, orig_args[idx]]))
            elif isinstance(handled, rel.RelationalAbstraction):
                var = ir.Var(types.Any, "head")
                rel_var = self.handle(var)
                args.append(rel_var)
                rel_equiv.append(rel.create_eq(rel_var, handled))
            elif isinstance(handled, bool):
                # boolean constants need to be bound to a var in the body which is used in the head
                var = ir.Var(types.Any, "head")
                args.append(self.handle(var))
                lookups.append(f.lookup(bt.eq, [var, ir.Literal(types.Bool, handled)]))
            elif not isinstance(handled, rel.Var):
                # other constants
                args.append(handled)
            else:
                orig = orig_args[idx]
                assert isinstance(orig, ir.Var)

                # Count how many times this argument has been seen before
                cnt = handled_args[:idx].count(handled)
                if cnt == 0:
                    arg_type = self._ir_var_to_rel_type(orig)
                    args.append(rel.Var(handled.name, False, arg_type) if arg_type else handled)
                    continue

                # Deduplicate variable
                new_var = ir.Var(orig.type, handled.name + "_dup" + str(cnt))
                rel_var = self.handle_var(new_var)
                arg_type = self._ir_var_to_rel_type(orig)
                args.append(rel.Var(rel_var.name, False, arg_type) if arg_type else rel_var)
                rel_equiv.append(rel.create_eq(rel_var, handled))
        return tuple(args), lookups, rel_equiv

    def _ir_var_to_rel_type(self, v: ir.Var) -> str:
        if isinstance(v.type, ir.DecimalType):
            return u.rel_typename(v.type)
        primitive_type = to_base_primitive(v.type)
        if primitive_type:
            return u.rel_typename(primitive_type)
        elif v.type != types.Any and v.type != types.Enum:
            return "pyrel_ID"
        return ""

    def _rel_reads(self, root, reads:OrderedSet[str]|None = None) -> OrderedSet[str]:
        if reads is None:
            reads = OrderedSet()

        if isinstance(root, (tuple, list)):
            for r in root:
                self._rel_reads(r, reads)

        if isinstance(root, rel.Var):
            if root.type is not None and not root.type.startswith("::std::common::"):
                reads.add(root.type)

        elif isinstance(root, rel.Declare):
            assert isinstance(root.premise, rel.Atom)
            self._rel_reads(root.premise.args, reads)
            self._rel_reads(root.requires, reads)

        elif isinstance(root, rel.Def):
            self._rel_reads(root.params, reads)
            self._rel_reads(root.body, reads)

        elif isinstance(root, rel.Atom):
            if isinstance(root.expr, rel.Identifier):
                reads.add(root.expr.name)
            else:
                self._rel_reads(root.expr, reads)
            self._rel_reads(root.args, reads)

        elif isinstance(root, rel.RelationalAbstraction):
            self._rel_reads(root.head, reads)
            self._rel_reads(root.body, reads)

        elif isinstance(root, rel.And):
            for arg in root.body:
                self._rel_reads(arg, reads)

        elif isinstance(root, rel.Or):
            for arg in root.body:
                self._rel_reads(arg, reads)

        elif isinstance(root, rel.Exists):
            self._rel_reads(root.body, reads)

        elif isinstance(root, rel.ForAll):
            self._rel_reads(root.body, reads)

        elif isinstance(root, rel.Not):
            self._rel_reads(root.body, reads)

        elif isinstance(root, rel.BinaryExpr):
            self._rel_reads(root.lhs, reads)
            self._rel_reads(root.rhs, reads)
            reads.add(root.op)

        elif isinstance(root, rel.Product):
            for arg in root.body:
                self._rel_reads(arg, reads)

        elif isinstance(root, rel.Union):
            for arg in root.body:
                self._rel_reads(arg, reads)

        return reads
