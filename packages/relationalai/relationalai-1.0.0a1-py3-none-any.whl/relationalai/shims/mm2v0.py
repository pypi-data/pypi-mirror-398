from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace as dc_replace
from typing import  Dict, Sequence as seq, Iterable
from enum import Enum
from math import pi

# PyRel imports
from ..util.naming import sanitize
from ..semantics.metamodel import metamodel as mm
from ..semantics.metamodel.builtins import builtins as b, is_abstract
from ..semantics.metamodel.metamodel_analyzer import Normalize
# ensure std libs are loaded
from ..semantics.metamodel.metamodel_analyzer import VarFinder
from ..semantics.metamodel.rewriter import Walker
from ..semantics.std import aggregates, common, math, numbers, re, strings, decimals, datetime, floats
from ..semantics.backends.lqp import annotations as lqp_annotations

# V0 imports
from v0.relationalai.semantics.metamodel import ir as v0, builtins as v0_builtins, types as v0_types, factory as f
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet, frozen, ordered_set, filter_by_type, OrderedSet
from v0.relationalai.semantics.internal.internal import literal_value_to_type

from .hoister import Hoister
from .helpers import is_output_update, is_main_output

#------------------------------------------------------
# Simplified translation API
#------------------------------------------------------
def translate(model: mm.Model) -> v0.Model:
    return Translator().translate_model(model)

#------------------------------------------------------
# Implementation
#------------------------------------------------------
class Context(Enum):
    # when translating tasks (i.e. runtime behavior)
    TASK = 1
    # when translating the static structure of the model (types, relations, etc.)
    MODEL = 2

@dataclass
class Translator():

    stack: list[mm.Node] = field(default_factory=list)

    # maps from mm.Node id to the v0.Node created for it
    # for Context=TASK
    task_map: Dict[int, v0.Node] = field(default_factory=dict)
    # for Context=MODEL
    model_map: Dict[int, v0.Node] = field(default_factory=dict)

    # map from a var that is bound to a table, to the list of vars that were used to construct
    # this var. This var is going to be used as a key to an output.
    key_map: Dict[mm.Var, seq[v0.Var]] = field(default_factory=dict)

    # map from a var that is bound to a data, to the data itself. This is used to translate
    # lookups on this var into v0 Data nodes.
    data_map: Dict[mm.Var, mm.Var] = field(default_factory=dict)

    # map from a var that is bound to an external table, to the vars of its fields
    column_map: defaultdict[mm.Var, dict[mm.Relation, v0.Value]] = field(default_factory=lambda: defaultdict(dict))

    # used tables
    used_tables: OrderedSet[mm.Table] = field(default_factory=lambda: ordered_set())

    # when translating a relation that has multiple readings, we need to translate to multiple
    # relations in v0, and we need to add rules to populate those relations. We also need rules
    # to populate super types from sub types.
    maintenance_rules: list[v0.Logical] = field(default_factory=list)

    # outputs that are exports
    exports: set[v0.Output] = field(default_factory=set)

    hoister = Hoister()
    normalize = Normalize()

    def get(self, ctx: Context, node: mm.Node):
        if ctx == Context.MODEL:
            return self.model_map.get(node.id, None)
        else:
            return self.task_map.get(node.id, None)
    def set(self, ctx: Context, node: mm.Node, value: v0.Node):
        if ctx == Context.MODEL:
            self.model_map[node.id] = value  # type: ignore
        else:
            self.task_map[node.id] = value  # type: ignore

    def translate_node(self, node: mm.Node, parent=None, ctx=Context.TASK) -> v0.Node|seq[v0.Node]:
        x = self.get(ctx, node)
        if x is not None:
            return x

        source_class_name = node.__class__.__name__.lower()
        translator = getattr(self, f"translate_{source_class_name}", None)
        if translator is None:
            raise NotImplementedError(f"No translator for node type: {source_class_name}")

        if parent:
            self.stack.append(parent)
        result = translator(node, parent, ctx)
        if parent:
            self.stack.pop()

        self.set(ctx, node, result)
        return result

    def translate_value(self, value: mm.Value, parent, ctx) -> v0.Value:
        # Value = _Union[Var, Literal, Type, Relation, seq["Value"], None]
        if value is None:
            return None
        elif isinstance(value, mm.ScalarType) or isinstance(value, mm.Relation):
            return self.translate_node(value, parent, Context.MODEL) # type: ignore
        elif isinstance(value, seq):
            return self.translate_seq(value, parent, ctx) # type: ignore
        return self.translate_node(value, parent, ctx) # type: ignore


    def translate_seq(self, nodes: seq[mm.Node], parent, ctx) -> tuple[v0.Node,...]:
        res = []
        for n in nodes:
            x = self.translate_node(n, parent, ctx)
            # flat map would be great here
            if isinstance(x, list) or isinstance(x, tuple):
                res.extend(x)
            elif x is not None:
                res.append(x)
        return tuple(res)

    def translate_frozen(self, nodes: seq[mm.Node], parent, ctx) -> FrozenOrderedSet[v0.Node]:
        return frozen(*self.translate_seq(nodes, parent, ctx))


    #-----------------------------------------------------------------------------
    # Capabilities, Reasoners
    #-----------------------------------------------------------------------------

    def translate_capability(self, c: mm.Capability, parent: mm.Reasoner, ctx) -> v0.Capability:
        return v0.Capability(name=c.name)

    def translate_reasoner(self, r: mm.Reasoner|None, parent, ctx) -> v0.Engine|None:
        if r is None:
            return None
        return v0.Engine(
            name=f"{r.id}", # no name field in v0, so use id
            platform=r.type,
            info=r.info,
            capabilities=self.translate_frozen(r.capabilities, r, ctx), # type: ignore
            relations=self.translate_frozen(r.relations, r, ctx), # type: ignore
            annotations=self.translate_frozen(r.annotations, r, ctx) # type: ignore
        )

    # -----------------------------------------------------------------------------
    # Relation
    # -----------------------------------------------------------------------------

    def translate_field(self, f: mm.Field, parent, ctx) -> v0.Field:
        return v0.Field(
            name=f.name,
            type=self.translate_node(f.type, f, Context.MODEL), # type: ignore
            input=f.input,
        )

    def translate_reading(self, r: mm.Reading, parent: mm.Relation, ctx) -> v0.Relation:
        # Readings in v0 are represented as separate Relation nodes with different field orders
        fields = []
        for i in r.field_order:
            fields.append(self.translate_field(parent.fields[i], r, ctx))

        # this is not totally correct, we are translating the parent's overloads here, but
        # the order of fields would be different. However, it's unlikely we will have multiple
        # readings AND overloads in the same relation, so this is acceptable for now.
        return v0.Relation(
            name=f"{parent.name}_{parent.readings.index(r)}",
            fields=tuple(fields),
            requires=frozen(),
            annotations=frozen(),
            overloads=self.translate_frozen(parent.overloads, parent, ctx), # type: ignore
        )

    def translate_overload(self, o: mm.Overload, parent: mm.Relation, ctx) -> v0.Relation:
        # Overloads in v0 are represented as separate Relation nodes with different types
        fields = []
        for field, typ in zip(parent.fields, o.types):
            fields.append(
                v0.Field(name=field.name, type=self.translate_node(typ, field, ctx), input=field.input) # type: ignore
            )
        return v0.Relation(
            name=parent.name,
            fields=tuple(fields),
            requires=frozen(),
            annotations=frozen(),
            overloads=frozen()
        )

    # map builtin relations by name
    BUILTIN_RELATION_MAP = {}
    RENAMES = {
        "degrees": "rad2deg",
        "radians": "deg2rad",
        "len": "num_chars",
        "power": "pow",
        "^": "pow",
        "like": "like_match",
        "regex_escape": "escape_regex_metachars",
    }
    for lib in ["core", "aggregates", "common", "datetime", "floats", "math", "numbers", "strings", "re", "lqp"]:
        for x in b._libraries[lib].data.values():
            v0_name = RENAMES.get(x.name, x.name)
            if v0_name in v0_builtins.builtin_relations_by_name:
                BUILTIN_RELATION_MAP[x] = v0_builtins.builtin_relations_by_name[v0_name]

    def translate_relation(self, r: mm.Relation, parent, ctx):
        if r in self.BUILTIN_RELATION_MAP:
            return self.BUILTIN_RELATION_MAP[r]

        if r is b.numbers.parse_number:
            if isinstance(parent, mm.Lookup):
                assert(isinstance(parent.args[1], mm.Var))
                out_type = parent.args[1].type
                assert(isinstance(out_type, mm.NumberType))
                if out_type.scale == 0:
                    return v0_builtins.parse_int128 if out_type.precision > 19 else v0_builtins.parse_int64
                else:
                    return v0_builtins.parse_decimal

        # relations can be accessed by any context; if it exists in the other context, use it
        other_ctx = Context.MODEL if ctx == Context.TASK else Context.TASK
        x = self.get(other_ctx, r)
        if x is not None:
            return x  # type: ignore

        if len(r.readings) > 1:
            # if there are multiple readings, create a relation per reading
            relations = self.translate_seq(r.readings, r, ctx) # type: ignore

            # also create a rule to populate the other readings from the main relation
            main_relation = relations[0]
            assert isinstance(main_relation, v0.Relation)
            main_relation_args = tuple(v0.Var(type=field.type, name=field.name) for field in main_relation.fields)
            for reading in r.readings[1:]:
                relation = relations[r.readings.index(reading)]
                assert isinstance(relation, v0.Relation)
                # lookup from main_relation and derive into this relation
                self.maintenance_rules.append(v0.Logical(
                    engine=None,
                    hoisted=(),
                    body=(
                        v0.Lookup(
                            engine=None,
                            relation=main_relation,
                            args=main_relation_args,
                            annotations=frozen(),
                        ),
                        v0.Update(
                            engine=None,
                            relation=relation,
                            args=tuple([main_relation_args[idx] for idx in reading.field_order]),
                            effect=v0.Effect.derive,
                            annotations=frozen(),
                        )
                    ),
                    annotations=frozen(),
                ))
            return relations
        else:
            # if there are no readings or a single reading, create a single relation

            # if this is a placeholder relation, fill overloads with all non-placeholder relations
            # with the same name
            overloads = ordered_set()
            if all(field.type == b.core.Any for field in r.fields):
                for rr in self.relations_by_name[r.name]:
                    if any(field.type != b.core.Any for field in rr.fields):
                        x = self.translate_relation(rr, r, ctx)
                        if isinstance(x, v0.Relation):
                            overloads.add(x)
                        else:
                            overloads.update(x) # type: ignore
            overloads.update(self.translate_frozen(r.overloads, r, ctx))  # type: ignore

            return v0.Relation(
                name=r.name,
                fields=self.translate_frozen(r.fields, r, ctx), # type: ignore
                requires=self.translate_frozen(r.requires, r, ctx), # type: ignore
                annotations=self.translate_frozen(r.annotations, r, ctx), # type: ignore
                overloads=overloads.frozen(), # type: ignore
            )

    def translate_unresolvedrelation(self, r: mm.UnresolvedRelation, parent, ctx):
        # treat unresolved relations the same as normal relations for now
        return self.translate_relation(r, parent, ctx)

    #------------------------------------------------------
    # Annotation
    #------------------------------------------------------

    def translate_annotation(self, a: mm.Annotation, parent, ctx) -> v0.Annotation:
        if a.relation.name in v0_builtins.builtin_annotations_by_name:
            return getattr(v0_builtins, a.relation.name + "_annotation")  # type: ignore

        return v0.Annotation(
            relation=self.translate_node(a.relation, a, Context.MODEL), # type: ignore
            args=tuple(self.translate_value(arg, a, ctx) for arg in a.args)
        )

    #-----------------------------------------------------------------------------
    # Types
    #-----------------------------------------------------------------------------

    BUILTIN_TYPE_MAP = {
        # Abstract types (should be removed once our typer is done because they should not
        # show up in the typed metamodel.)
        b.core.Any: v0_types.Any,
        # b.core.AnyEntity: v0_types.AnyEntity,
        b.core.Number: v0_types.Number, # v0 typer can figure the rest out
        # Concrete types
        b.core.Boolean: v0_types.Bool,
        b.core.String: v0_types.String,
        b.core.Date: v0_types.Date,
        b.core.DateTime: v0_types.DateTime,
        b.core.Float: v0_types.Float,
    }

    def translate_scalartype(self, t: mm.ScalarType, parent: mm.Node, ctx) -> v0.ScalarType|v0.Relation|None:
        if t in self.BUILTIN_TYPE_MAP:
            return self.BUILTIN_TYPE_MAP[t]

        if ctx == Context.TASK:
            # in task context, this is a lookup or update on a concept population relation
            # TODO - removing this filter for now
            actual_type = self.translate_node(t, t, Context.MODEL)
            assert isinstance(actual_type, v0.ScalarType)
            fields = [v0.Field(name="entity", type=actual_type, input=False)] # type: ignore
            annotations = [v0_builtins.concept_relation_annotation]
            if isinstance(t, mm.Table):
                annotations.append(v0_builtins.external_annotation)
                annotations.append(v0_builtins.from_cdc_annotation)
                for col in t.columns:
                    fields.append(v0.Field(
                        name=col.name,
                        type=self.translate_node(col.fields[-1].type, col, Context.MODEL), # type: ignore
                        input=False
                    ))

            type_relation = v0.Relation(
                name=t.name,
                fields=tuple(fields), # type: ignore
                requires=frozen(),
                annotations=frozen(*annotations), # type: ignore
                overloads=frozen()
            )
            for super_type in t.super_types:
                super_rel = self.translate_node(super_type, t, Context.TASK)
                if not super_rel:
                    continue
                assert isinstance(super_rel, v0.Relation)
                v = v0.Var(type=actual_type, name=type_relation.name.lower())
                self.maintenance_rules.append(v0.Logical(
                    engine=None,
                    hoisted=(),
                    body=(
                        v0.Lookup(
                            engine=None,
                            relation=type_relation,
                            args=(v,),
                            annotations=frozen(),
                        ),
                        v0.Update(
                            engine=None,
                            relation=super_rel,
                            args=(v,),
                            effect=v0.Effect.derive,
                            annotations=frozen(),
                        )
                    ),
                    annotations=frozen(),
                ))
            return type_relation

        extends=[]
        if isinstance(t, mm.Table):
            extends.append(v0_types.RowId)

        for st in t.super_types:
            # for now make all value types extending number be Int64, we will fix this with a new typer
            if st == b.core.Number:
                translated_st = v0_types.Number
            else:
                translated_st = self.translate_node(st, t, ctx)
            extends.append(translated_st)

        return v0.ScalarType(
            name=t.name,
            super_types=frozen(*extends), # type: ignore
            # super_types=self.translate_frozen(t.super_types, t, ctx), # type: ignore
            annotations=self.translate_frozen(t.annotations, t, ctx) # type: ignore
        )

    def translate_numbertype(self, t: mm.NumberType, parent, ctx):
        if t.scale == 0:
            return v0_types.Int128 if t.precision > 19 else v0_types.Int64
        return v0.DecimalType(
            name=t.name,
            precision=t.precision,
            scale=t.scale,
            super_types=frozen(),
            annotations=self.translate_frozen(t.annotations, t, ctx) # type: ignore
        )

    def translate_uniontype(self, t: mm.UnionType, parent, ctx) -> v0.UnionType:
        return v0.UnionType(
            types=self.translate_frozen(t.types, t, ctx), # type: ignore
        )

    def translate_listtype(self, t: mm.ListType, parent, ctx) -> v0.ListType:
        return v0.ListType(
            element_type=self.translate_node(t.element_type, t, ctx), # type: ignore
        )

    def translate_tupletype(self, t: mm.TupleType, parent, ctx) -> v0.TupleType:
        return v0.TupleType(
            types=self.translate_seq(t.element_types, t, ctx), # type: ignore
        )


    #------------------------------------------------------
    # Table
    #------------------------------------------------------

    # TODO - this depends on what is using it, it may become an Output
    # class Table(ScalarType):
    #     columns: seq[Relation] = tuple_field()
    #     uri: str = ""

    def translate_table(self, t: mm.Table, parent, ctx):
        return self.translate_scalartype(t, parent, ctx)


    # -----------------------------------------------------------------------------
    # Values
    # -----------------------------------------------------------------------------

    # Primitive = _Union[str, int, float, bool, _dt.datetime, None]

    def translate_var(self, v: mm.Var, parent, ctx) -> v0.Var:
        if isinstance(parent, mm.Lookup):
            root_type = parent.relation.fields[0].type
            root_arg = parent.args[0]
            if isinstance(root_arg, mm.Var) \
                and isinstance(root_type, mm.Table) \
                and (existing := self.column_map[root_arg].get(parent.relation)):
                return existing # type: ignore

        return v0.Var(
            type=self.translate_node(v.type, v, Context.MODEL), # type: ignore
            name=v.name
        )

    def translate_literal(self, l: mm.Literal, parent, ctx) -> v0.Literal:
        typ = None
        if l.type is None or is_abstract(l.type):
            # force int64 for literals, it can be widened later if needed
            if  type(l.value) == int:
                typ = v0_types.Int64
            else:
                # using v0's map of literal to type
                typ = literal_value_to_type(l.value)
        else:
            typ = self.translate_node(l.type, l, Context.MODEL)
        if type is None:
            pass
        return v0.Literal(
            type=typ, # type: ignore
            value=l.value
        )

    # Value = _Union[Var, Literal, Type, Relation, seq["Value"], None]

    # # -----------------------------------------------------------------------------
    # # Tasks (process algebra)
    # # -----------------------------------------------------------------------------

    # @dataclass(frozen=True, kw_only=True)
    # class Task(Node):
    #     reasoner: Optional[Reasoner] = None

    # -----------------------------
    # Control Flow
    # -----------------------------

    def _merge_outputs(self, children: seq[v0.Node], outputs:list[v0.Output]):
        # We need to always rewrite the outputs, even if there's only one, because
        # we may need to mark it as an export and handle the NO_KEYS case.
        # if len(outputs) < 2:
        #     return children

        children = list(children)

        # merge all outputs, accumulating keys and aliases
        keys = ordered_set()
        aliases = ordered_set()
        for output in outputs:
            assert isinstance(output, v0.Output)
            children.remove(output)
            if output.keys is not None:
                keys.update(output.keys)
            aliases.update(output.aliases)

        # add a single, merged output
        is_export = any(output in self.exports for output in outputs)
        annos = (v0_builtins.export_annotation,) if is_export else ()
        if is_export and not keys:
            key_var = v0.Var(type=v0_types.Hash, name="export_key")
            vals = [alias[1] for alias in aliases]
            children.append(v0.Construct(
                engine=None,
                values=(v0.Literal(type=v0_types.String, value="NO_KEYS"), *vals),
                id_var=key_var,
            ))
            keys.add(key_var)

        children.append(
                v0.Output(
                    engine=None,
                    aliases=frozen(*aliases),
                    keys=frozen(*keys),
                    annotations=frozen(*annos)
                )
            )
        return tuple(children)

    def get_outputs(self, children: seq[v0.Node]) -> list[v0.Output]:
        return list(filter(lambda o: isinstance(o, v0.Output), children)) # type: ignore

    def translate_logical(self, l: mm.Logical, parent, ctx):
        # first process children
        children = self.translate_seq(l.body, l, ctx)

        # inline logicals if possible
        new_children = []
        for c in children:
            if isinstance(c, v0.Logical) and not c.hoisted and len(c.body) == 1:
                new_children.extend(c.body)
            else:
                new_children.append(c)
        # children = children if len(children) == len(new_children) else tuple(new_children)
        children = tuple(new_children)

        # compute variables to hoist, wrapping in Default if the logical is optional
        if l.optional:
            hoisted = tuple([v0.Default(self.translate_node(v, l, ctx), None) for v in self.hoister.hoisted(l)]) # type: ignore
        else:
            hoisted = tuple([self.translate_node(v, l, ctx) for v in self.hoister.hoisted(l)]) # type: ignore

        # Nots can never hoist variables upwards
        if isinstance(parent, mm.Not):
            hoisted = ()

        # if there are no outputs, just return the logical
        outputs = self.get_outputs(children)
        if not outputs:
            return v0.Logical(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                hoisted=hoisted, # type: ignore
                body=children, # type: ignore
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )


        # if there's a main output here, we need to merge all outputs as a single one
        has_main_output = any(is_main_output(c) for c in l.body)
        if has_main_output:
            return v0.Logical(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                hoisted=hoisted, # type: ignore
                body=self._merge_outputs(children, outputs), # type: ignore
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )
        else:
            # this logical has an output but it's not the main one; so we return the outputs
            # side-by-side with the logical. This assumes that the parent is a logical that
            # will splat these tasks and we will eventually get into a logical with a main
            # output that will merge them all.

            # remove outputs from children
            children = tuple([c for c in children if not isinstance(c, v0.Output)])
            if not children:
                return outputs

            # if this is an optional logical but we're not hoisting anything and not updating,
            # then it's effectively a no-op since it cannot affect the query. Just return the outputs.
            # this is important because the LQP stack blows up if there's a logical with no effect
            if l.optional and not hoisted and not any(isinstance(c, v0.Update) for c in children):
                return outputs

            # return outputs + a logical with the other children
            outputs.append(
                v0.Logical(
                    engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                    hoisted=hoisted, # type: ignore
                    body=children, # type: ignore
                    annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
                ))
            return outputs




    def translate_sequence(self, s: mm.Sequence, parent, ctx) -> v0.Sequence:
        return v0.Sequence(
            engine=self.translate_reasoner(s.reasoner, s, Context.MODEL),
            hoisted=self.translate_seq(self.hoister.hoisted(s), s, ctx), # type: ignore
            tasks=self.translate_seq(s.tasks, s, ctx), # type: ignore
            annotations=self.translate_frozen(s.annotations, s, ctx) # type: ignore
        )

    def translate_union(self, u: mm.Union, parent, ctx) -> v0.Union:
        return v0.Union(
            engine=self.translate_reasoner(u.reasoner, u, Context.MODEL),
            hoisted=self.translate_seq(self.hoister.hoisted(u), u, ctx), # type: ignore
            tasks=self.translate_seq(u.tasks, u, ctx), # type: ignore
            annotations=self.translate_frozen(u.annotations, u, ctx) # type: ignore
        )

    def translate_match(self, m: mm.Match, parent, ctx) -> v0.Match:
        return v0.Match(
            engine=self.translate_reasoner(m.reasoner, m, Context.MODEL),
            hoisted=self.translate_seq(self.hoister.hoisted(m), m, ctx), # type: ignore
            tasks=self.translate_seq(m.tasks, m, ctx), # type: ignore
            annotations=self.translate_frozen(m.annotations, m, ctx) # type: ignore
        )

    def translate_until(self, u: mm.Until, parent, ctx) -> v0.Until:
        return v0.Until(
            engine=self.translate_reasoner(u.reasoner, u, Context.MODEL),
            hoisted=self.translate_seq(self.hoister.hoisted(u), u, ctx), # type: ignore
            check=self.translate_node(u.check, u, ctx), # type: ignore
            body=self.translate_node(u.body, u, ctx), # type: ignore
            annotations=self.translate_frozen(u.annotations, u, ctx) # type: ignore
        )

    def translate_wait(self, w: mm.Wait, parent, ctx) -> v0.Wait:
        return v0.Wait(
            engine=self.translate_reasoner(w.reasoner, w, Context.MODEL),
            hoisted=self.translate_seq(self.hoister.hoisted(w), w, ctx), # type: ignore
            check=self.translate_node(w.check, w, ctx), # type: ignore
            annotations=self.translate_frozen(w.annotations, w, ctx) # type: ignore
        )

    def translate_loop(self, l: mm.Loop, parent, ctx) -> v0.Loop:
        # TODO - loop is incompatible because over has multiple vars, so this is a best
        # attempt (does not matter much as this is not used in practice)
        return v0.Loop(
            engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
            hoisted=self.translate_seq(self.hoister.hoisted(l), l, ctx), # type: ignore
            iter=self.translate_node(l.over[0], l, ctx), # type: ignore
            body=self.translate_node(l.body, l, ctx), # type: ignore
            annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
        )

    def translate_break(self, b: mm.Break, parent, ctx) -> v0.Break:
        return v0.Break(
            engine=self.translate_reasoner(b.reasoner, b, Context.MODEL),
            check=self.translate_node(b.check, b, ctx), # type: ignore
            annotations=self.translate_frozen(b.annotations, b, ctx) # type: ignore
        )

    # -----------------------------
    # Constraints
    # -----------------------------

    def translate_require(self, r: mm.Require, parent, ctx) -> v0.Require|None:
        # check if this is a unique_fields constraint
        assert isinstance(r.domain, mm.Logical)
        assert isinstance(r.check, mm.Logical)
        if not r.domain.body and all(isinstance(c, mm.Lookup) and c.relation is b.constraints.unique_fields for c in r.check.body):
            return
            v0_reqs = []
            # v0 expects a check with both the domain and the relation in it followed by the unique
            # constraint, so we construct a logical with all of that in it
            for c in r.check.body:
                assert isinstance(c, mm.Lookup)
                fields = c.args[0] # tuple of fields
                assert isinstance(fields, tuple) and all(isinstance(f, mm.Field) for f in fields)
                first_field = fields[0]
                if isinstance(first_field.type, mm.Table):
                    # skip union types for now
                    continue
                assert isinstance(first_field, mm.Field)
                relation = first_field._relation
                domain = self.translate_node(mm.Logical(()), r, ctx)
                all_vars =  [mm.Var(type=field.type, name=field.name + "_var") for field in relation.fields]
                check_tasks = [
                    mm.Lookup(relation, tuple(all_vars)),
                    mm.Lookup(b.constraints.unique, (tuple(all_vars[0:len(fields)]),))
                ]
                check_logical = self.translate_node(mm.Logical(tuple(check_tasks)), r, Context.TASK)
                check = v0.Check(
                    check=check_logical, # type: ignore
                    error=None,
                    annotations=self.translate_frozen(r.annotations, r, ctx) # type: ignore
                )
                v0_reqs.append(v0.Require(
                    engine=self.translate_reasoner(r.reasoner, r, Context.MODEL),
                    domain=domain, # type: ignore
                    checks=(check,), # type: ignore
                    annotations=self.translate_frozen(r.annotations, r, ctx) # type: ignore
                ))
            return v0_reqs # type: ignore

        # check = v0.Check(
        #     check=self.translate_node(r.check, r, ctx), # type: ignore
        #     error=self.translate_node(r.error, r, ctx) if r.error else None, # type: ignore
        #     annotations=self.translate_frozen(r.annotations, r, ctx) # type: ignore
        # )
        # return v0.Require(
        #     engine=self.translate_reasoner(r.reasoner, r, Context.MODEL),
        #     domain=self.translate_node(r.domain, r, ctx), # type: ignore
        #     checks=(check,), # type: ignore
        #     annotations=self.translate_frozen(r.annotations, r, ctx) # type: ignore
        # )
        return None

    # -----------------------------
    # Quantifiers
    # -----------------------------

    def translate_not(self, n: mm.Not, parent, ctx) -> v0.Not:
        return v0.Not(
            engine=self.translate_reasoner(n.reasoner, n, Context.MODEL),
            task=self.translate_node(n.task, n, ctx), # type: ignore
            annotations=self.translate_frozen(n.annotations, n, ctx) # type: ignore
        )

    def translate_exists(self, e: mm.Exists, parent, ctx) -> v0.Exists:
        return v0.Exists(
            engine=self.translate_reasoner(e.reasoner, e, Context.MODEL),
            vars=self.translate_seq(e.vars, e, ctx), # type: ignore
            task=self.translate_node(e.task, e, ctx), # type: ignore
            annotations=self.translate_frozen(e.annotations, e, ctx) # type: ignore
        )

    # -----------------------------
    # Relation Ops
    # -----------------------------

    def translate_effect(self, e: mm.Effect, parent, ctx) -> v0.Effect:
        if e == mm.Effect.derive:
            return v0.Effect.derive
        elif e == mm.Effect.insert:
            return v0.Effect.insert
        elif e == mm.Effect.delete:
            return v0.Effect.delete

    def translate_lookup(self, l: mm.Lookup, parent, ctx):
        # Data Node lookups
        if isinstance(l.relation, mm.Data):
            vars = [self.translate_value(l.args[0], l, ctx)]
            for col in l.relation.columns:
                v = v0.Var(
                    type=self.translate_node(col.fields[-1].type, col, Context.MODEL), # type: ignore
                    name=f"{col.name}"
                )
                vars.append(v)
                assert isinstance(l.args[0], mm.Var)
                self.column_map[l.args[0]][col] = v
            return v0.Data(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                data=l.relation.data,
                vars=frozen(*vars) # type: ignore
            )
        elif l.args and l.args[0] in self.column_map and l.relation in self.column_map[l.args[0]]: # type: ignore
            assert isinstance(l.args[0], mm.Var)
            var = self.translate_value(l.args[1], l, ctx)
            col_var = self.column_map[l.args[0]][l.relation]  # ensure entry exists
            if var != col_var:
                return v0.Lookup(
                    engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                    relation=v0_builtins.eq,
                    args=(var, col_var), # type: ignore
                    annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
                )
            else:
                return None

        relation, args = self._resolve_reading(l, ctx)
        if relation is None:
            return None

        # External Table Column lookups
        # we have to take the 6nf column relations and pull them into a single wide lookup
        # making sure that the variable get mapped correctly. To match the expectations of
        # v0, we also have to make sure that if we're looking up the table row itself, that
        # it is wrapped in its own logical
        root_type = l.relation.fields[0].type
        if isinstance(root_type, mm.Table):
            self.used_tables.add(root_type)
            assert isinstance(l.args[0], mm.Var)
            is_col = l.relation in root_type.columns
            is_table = l.relation == root_type
            if is_col:
                self.column_map[l.args[0]][l.relation] = args[-1]
                # we always lookup the full table, so replace the relation and args
                relation = self.translate_node(root_type, l, ctx)

            # this is a lookup on the table itself or the columns, translate to the column vars
            if is_col or is_table:
                mapped = self.column_map.get(l.args[0], {})
                col_args = []
                for col in root_type.columns:
                    v = mapped.setdefault(col, v0.Var(
                        type=self.translate_node(col.fields[-1].type, col, Context.MODEL), # type: ignore
                        name=f"{col.name}"
                    ))
                    col_args.append(v)
                args = tuple([args[0], *col_args]) # type: ignore

        # Specific rewrites
        rewrite = self.rewrite_lookup(l, parent, ctx)
        if rewrite is None:
            # General translation
            rewrite = v0.Lookup(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                relation=relation, # type: ignore
                args=args,
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )

        return rewrite


    def translate_update(self, u: mm.Update, parent, ctx) -> v0.Update|v0.Output|None:
        if isinstance(u.relation, mm.Table):
            # ignore updates to tables for now
            return None

        if is_output_update(u):
            # this is an output, the last arg is the value for the output column, the other
            # args are part of the key

            # get the list of key vars created during construction
            keys = list(self.key_map[u.args[0]]) # type: ignore
            # if there are no keys in the key map, this is a constructor of output without
            # keys; we still need to remove the output from the args, so count is 1
            arg_count = len(keys) if keys else 1
            # append any other args used for the key
            for arg in u.args[arg_count:-1]:
                x = self.translate_value(arg, u, ctx)
                keys.append(x) # type: ignore
            if any(anno.relation is b.core["output_value_is_key"] for anno in u.annotations):
                # if the output_value_is_key annotation is present, add the output value to the keys
                keys.append(self.translate_value(u.args[-1], u, ctx)) # type: ignore

            # there will be a single alias here, the output column
            aliases = ordered_set((u.relation.name, self.translate_value(u.args[-1], u, ctx))).frozen()

            out = v0.Output(
                engine=self.translate_reasoner(u.reasoner, u, Context.MODEL),
                keys=frozen(*keys), # type: ignore
                aliases=aliases,
                annotations=self.translate_frozen(u.annotations, u, ctx) # type: ignore
            )
            table = u.relation.fields[0].type
            if isinstance(table, mm.Table) and not table.uri.startswith("dataframe://"):
                self.exports.add(out)
            return out
        else:
            relation, args = self._resolve_reading(u, ctx)

            return v0.Update(
                engine=self.translate_reasoner(u.reasoner, u, Context.MODEL),
                relation=relation, # type: ignore
                args=args,
                effect=self.translate_effect(u.effect, u, ctx),
                annotations=self.translate_frozen(u.annotations, u, ctx) # type: ignore
            )

    def _resolve_reading(self, task: mm.Lookup|mm.Update, ctx):
        relation = self.translate_node(task.relation, task, ctx)
        args = tuple(self.translate_value(arg, task, ctx) for arg in task.args)
        if isinstance(relation, seq):
            # Updates should always write to the root so that the reading maintenance rules
            # can populate the other readings
            if task.reading_hint is not None and isinstance(task, mm.Lookup):
                relation = relation[task.relation.readings.index(task.reading_hint)]
                args = tuple([args[i] for i in task.reading_hint.field_order])
            else:
                relation = relation[0]

        return relation, args


    def translate_aggregate(self, a: mm.Aggregate, parent, ctx) -> v0.Aggregate:

        # hoist the return variables (those that are not inputs to the aggregation)
        return_args = []
        for field, arg in zip(a.aggregation.fields, a.args):
            if not field.input:
                return_args.append(arg)
        hoisted=self.translate_seq(return_args, a, ctx)

        # body must contain the aggregate body plus the aggregate itself
        body = self.translate_node(a.body, a, ctx)
        body = list(body.body if isinstance(body, v0.Logical) else [body])

        # construct the aggregate node
        engine = self.translate_reasoner(a.reasoner, a, Context.MODEL)
        aggregation = self.translate_node(a.aggregation, a, ctx)
        projection = self.translate_seq(a.projection, a, ctx)
        group = self.translate_seq(a.group, a, ctx)
        args = tuple(self.translate_value(arg, a, ctx) for arg in a.args)
        annotations = self.translate_frozen(a.annotations, a, ctx)

        v0_agg = None
        if a.aggregation == b.aggregates.rank:
            assert isinstance(args[0], tuple)
            assert isinstance(args[1], tuple)
            v0_agg = v0.Rank(engine, projection, group, args[0], tuple(l.value for l in args[1]), args[-1], 0, annotations,) # type: ignore
        elif a.aggregation == b.aggregates.limit:
            assert isinstance(args[0], v0.Literal)
            assert isinstance(args[1], tuple)
            assert isinstance(args[2], tuple)
            result = v0.Var(type=v0_types.Int64, name="limit_result")
            v0_agg = v0.Rank(engine, projection, group, args[1], tuple(l.value for l in args[2]), result, args[0].value, annotations,) # type: ignore
        else:
            v0_agg = v0.Aggregate(engine, aggregation, projection, group, args, annotations) # type: ignore

        body.append(v0_agg)
        return v0.Logical(
            engine=None,
            hoisted=hoisted, # type: ignore
            body=tuple(body) # type: ignore
        )

    def translate_construct(self, c: mm.Construct, parent, ctx) -> v0.Construct|None:
        if isinstance(c.id_var.type, mm.Table):
            # we are constructing the key for an output. If there are no values, there is no
            # key in v0, so we can just ignore this
            if not c.values:
                self.key_map[c.id_var] = []
                return None
            # now create a new v0 var to represent the hashed key, record that this key is
            # to be used by updates, and generate the constructor
            v = v0.Var(type=v0_types.Hash, name=c.id_var.name)
            self.key_map[c.id_var] = [v]
            values = [v0_types.Hash]
            values.extend(self.translate_seq(c.values, c, ctx)) # type: ignore
            return v0.Construct(
                engine=self.translate_reasoner(c.reasoner, c, Context.MODEL),
                values=tuple(values), # type: ignore
                id_var=v,
                annotations=self.translate_frozen(c.annotations, c, ctx) # type: ignore
            )
        return v0.Construct(
            engine=self.translate_reasoner(c.reasoner, c, Context.MODEL),
            values=self.translate_seq(c.values, c, ctx), # type: ignore
            id_var=self.translate_node(c.id_var, c, ctx), # type: ignore
            annotations=self.translate_frozen(c.annotations, c, ctx) # type: ignore
        )


    def translate_data(self, d: mm.Data, parent, ctx):
        if isinstance(parent, mm.Field) or isinstance(parent, mm.Var):
            return v0_types.Int128

    # -----------------------------------------------------------------------------
    # Model
    # -----------------------------------------------------------------------------

    def translate_model(self, source_model: mm.Model, parent=None, ctx=None) -> v0.Model:
        try:
            # first analyze the model to compute variables that need to be hoisted
            self.hoister.analyze(source_model)

            self.relations_by_name = defaultdict(list)
            for r in source_model.relations:
                self.relations_by_name[r.name].append(r)

            # translate root first as it may create relations from types (e.g. concept populations)
            root = self.translate_node(source_model.root, source_model, Context.TASK)

            # translate all declared relations
            relations:OrderedSet[v0.Relation] = ordered_set(*self.translate_seq(source_model.relations, source_model, Context.MODEL)) # type: ignore
            # add relations created during task translation
            relations.update(filter_by_type(self.task_map.values(), v0.Relation)) # type: ignore
            # v0 needs all overloads also added to the model
            for r in list(relations):
                relations.update(r.overloads) # type: ignore

            # if there are reading maintenance rules, add them as well
            if self.maintenance_rules:
                root = v0.Logical(
                    engine=None,
                    hoisted=(),
                    body=(
                        root, # type: ignore
                        *self.maintenance_rules
                    ),
                    annotations=frozen()
                )
            engines=self.translate_frozen(source_model.reasoners, source_model, Context.MODEL) # type: ignore
            types=self.translate_frozen(source_model.types, source_model, Context.MODEL) # type: ignore

            return v0.Model(
                engines=engines, # type: ignore
                relations=relations.frozen(), # type: ignore
                types=types, # type: ignore
                root=root # type: ignore
            )
        finally:
            self.hoister.clear()

    # -----------------------------------------------------------------------------
    # Translate query
    # -----------------------------------------------------------------------------

    def translate_query(self, source_query: mm.Task) -> v0.Logical:
        try:
            # first analyze the model to compute variables that need to be hoisted
            self.hoister.analyze_task(source_query)

            # translate the query logical
            return self.translate_node(source_query, source_query, Context.TASK) # type: ignore
        finally:
            self.hoister.clear()

    # -----------------------------------------------------------------------------
    # Library-specific rewrites
    # -----------------------------------------------------------------------------

    def adjust_index(self, l: mm.Lookup, indices: list[int], ctx, args=None, no_outputs=False):
        """ Rewrite the lookup such that the args at `indices` are adjusted to convert from
        0-based indexing (as in the mm) to 1-based indexing (as in v0's backend).

        If the field at the given index is input, we increment the arg by 1 before passing
        it to the lookup. If the field is output, we create a tmp var to hold the result
        of the lookup, and then create a subsequent task to decrement the tmp var by 1.

        `args` can be used to provide a different set of args than l.args, in case they need
        reordering (e.g. strings.split).
        """
        if args is None:
            args = l.args
        # vars to hold the result from the v0 lookup
        tmps = {}
        for i in indices:
            index_type = l.relation.fields[i].type
            tmps[i] = mm.Var(type=index_type, name=f"tmp")
        # insert tmp at index
        replaced_args = []
        for i, arg in enumerate(args):
            if i in indices:
                replaced_args.append(tmps[i])
            else:
                replaced_args.append(arg)
        # translate the lookup
        lookup = v0.Lookup(
            engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
            relation=self.translate_node(l.relation), # type: ignore
            args=tuple(self.translate_value(arg, l, ctx) for arg in replaced_args),
            annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
        )
        # subtract 1 from the index to convert from 1-based to 0-based
        tasks = []
        for index in indices:
            arg = args[index]
            if isinstance(arg, mm.Literal):
                if l.relation.fields[index].input:
                    new = mm.Literal(arg.type, arg.value + 1) # type: ignore
                else:
                    new = mm.Literal(arg.type, arg.value + 1) # type: ignore
                tasks.append(v0.Lookup(
                        engine=None,
                        relation=v0_builtins.eq, # type: ignore
                        args=(
                            self.translate_value(tmps[index], lookup, ctx),
                            self.translate_value(new, lookup, ctx),
                        )
                ))
            elif l.relation.fields[index].input:
                tasks.append(v0.Lookup(
                        engine=None,
                        relation=v0_builtins.plus, # type: ignore
                        args=(
                            self.translate_value(args[index], lookup, ctx),
                            v0.Literal(v0_types.Int128, 1),
                            self.translate_value(tmps[index], lookup, ctx),
                        ),
                    )
                )
            else:
                tasks.append(v0.Lookup(
                        engine=None,
                        relation=v0_builtins.minus, # type: ignore
                        args=(
                            self.translate_value(tmps[index], lookup, ctx),
                            v0.Literal(v0_types.Int128, 1),
                            self.translate_value(args[index], lookup, ctx),
                        ),
                    )
                )
        # do casts
        tasks.extend(self.cast(lookup, ctx, no_outputs=no_outputs))

        return tasks

    def decrement(self, l: mm.Lookup, index: int, ctx):
        """ Rewrite the lookup such that the arg at `index` is decremented by 1 before the
        lookup.  """
        tmp = self.translate_value(mm.Var(type=b.core.Number, name="tmp"), l, ctx)
        # lookup(..., tmp, ...)
        new = v0.Lookup(
                engine=None,
                relation=self.translate_node(l.relation), # type: ignore
                args=tuple(self.translate_value(arg, l, ctx) if i != index else tmp for i, arg in enumerate(l.args)),
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
        )
        casted = self.cast(new, ctx)
        return (
            # tmp = l.args[index] - 1
            v0.Lookup(
                engine=None,
                relation=v0_builtins.minus, # type: ignore
                args=(
                    self.translate_value(l.args[index], l, ctx),
                    v0.Literal(v0_types.Int128, 1),
                    tmp,
                ),
            ),
            *casted
        )

    def cast(self, l: v0.Lookup, ctx, no_outputs=False):
        # note that everything here is in v0
        inputs = []
        outputs = []
        args = []
        for arg, field in zip(l.args, l.relation.fields):
            target_type = field.type
            if target_type is None or not isinstance(arg, (v0.Var, v0.Literal)) or arg.type == target_type:
                args.append(arg)
                continue
            if field.input:
                cast_var = v0.Var(type=target_type, name="cast_var")
                args.append(cast_var)
                inputs.append(v0.Lookup(
                    engine=None,
                    relation=v0_builtins.cast, # type: ignore
                    args=(target_type, arg, cast_var),
                ))
            elif not no_outputs:
                cast_var = v0.Var(type=target_type, name="cast_var")
                args.append(cast_var)
                outputs.append(v0.Lookup(
                    engine=None,
                    relation=v0_builtins.cast, # type: ignore
                    args=(arg.type, cast_var, arg),
                ))
            else:
                # This is ridiculous, but there are cases where we need to force the type
                # of the var, but not through an actual cast operation. E.g. due to the way
                # the LQP stack handles dates.
                object.__setattr__(arg, 'type', target_type)
                args.append(arg)

        lookup = v0.Lookup(
            engine=l.engine,
            relation=l.relation,
            args=tuple(args),
            annotations=l.annotations
        )
        if no_outputs:
            outputs = []
        return [*inputs, lookup, *outputs]

    def rewrite_lookup(self, l: mm.Lookup, parent, ctx):
        """ Special cases for v1 builtins that either have some different shape in v0 or
        do not exist as a primitive in the engine, so we want to compose the result so that
        LQP works. Return None if no rewrite is needed.

        Note that this type of adjustment will need to be made by emitters anyways, so we
        will want to have a good API for them. But in that case, they should do
        transformations still in the mm, whereas this is doing it during translation to v0.
        """

        # -----------------------------------------------------------------------------
        # Common
        # -----------------------------------------------------------------------------
        if l.relation == b.common.range:
            # python/PyRel range has inclusive start but exclusive stop, whereas LQP/Rel has
            # inclusive stop, so we have to decrement the stop index by 1
            # tmp, lookup = self.decrement(l, 1, ctx)
            # return [tmp] + self.cast(lookup, [v0_types.Int64, v0_types.Int64, v0_types.Int64, v0_types.Int64], ctx)
            return self.decrement(l, 1, ctx)

        elif l.relation == b.core.cast:
            return v0.Lookup(
                engine=self.translate_reasoner(l.reasoner, l, Context.TASK),
                relation=v0_builtins.builtin_relations_by_name["cast"], # type: ignore
                args=(
                    self.translate_value(l.args[0], l, Context.MODEL),
                    self.translate_value(l.args[1], l, Context.TASK),
                    self.translate_value(l.args[2], l, Context.TASK)
                ),
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )

        # -----------------------------------------------------------------------------
        # Strings
        # -----------------------------------------------------------------------------

        elif l.relation == b.strings.len:
            lookup = v0.Lookup(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                relation=v0_builtins.builtin_relations_by_name["num_chars"], # type: ignore
                args=(
                    self.translate_value(l.args[0], l, ctx),
                    self.translate_value(l.args[1], l, ctx),
                ),
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )
            return self.cast(lookup, ctx)

        elif l.relation == b.strings.split:
            # swap first two args because that's how rel and v0 expect them
            args = l.args[1], l.args[0], l.args[2], l.args[3]
            return self.adjust_index(l, [2], ctx, args=args)

        elif l.relation == b.strings.substring:
            return self.adjust_index(l, [1], ctx)

        # -----------------------------------------------------------------------------
        # RE
        # -----------------------------------------------------------------------------
        elif l.relation == b.re.regex_match_all:
            return self.adjust_index(l, [2], ctx)

        # -----------------------------------------------------------------------------
        # Math
        # -----------------------------------------------------------------------------
        elif l.relation == b.math.degrees:
            # degrees(radians, x) = /(radians, (pi/180.0), x)
            return v0.Lookup(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                relation=v0_builtins.builtin_relations_by_name["/"], # type: ignore
                args=(
                    self.translate_value(l.args[0], l, ctx),
                    v0.Literal(v0_types.Float, pi / 180.0),
                    self.translate_value(l.args[1], l, ctx)
                ),
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )
        elif l.relation == b.math.radians:
            # radians(degrees, x) = /(degrees, (180.0/pi), x)
            return v0.Lookup(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                relation=v0_builtins.builtin_relations_by_name["/"], # type: ignore
                args=(
                    self.translate_value(l.args[0], l, ctx),
                    v0.Literal(v0_types.Float, 180.0 / pi),
                    self.translate_value(l.args[1], l, ctx)
                ),
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )

        # -----------------------------------------------------------------------------
        # Datetime
        # -----------------------------------------------------------------------------
        #
        # elif l.relation == b.datetime.date_range:
        #     return self.rewrite_date_range(l, parent, ctx)
        # elif l.relation == b.datetime.datetime_range:
        #     pass

        elif l.relation == b.datetime.date_add:
            return v0.Lookup(
                engine=self.translate_reasoner(l.reasoner, l, Context.MODEL),
                relation=self.translate_relation(l.relation, l, ctx), # type: ignore
                args=self.translate_seq(l.args, l, ctx), # type: ignore
                annotations=self.translate_frozen(l.annotations, l, ctx) # type: ignore
            )

        if b.datetime[l.relation.name] is l.relation:
            return self.adjust_index(l, [], ctx, no_outputs=True)

        v0_rel = self.translate_node(l.relation, l, ctx)
        if isinstance(v0_rel, v0.Relation) and any(f.type == v0_types.Int64 for f in v0_rel.fields):
            return self.adjust_index(l, [], ctx)

        return None


    # TODO - Currently implemented in the std.datetime itself.
    # def rewrite_date_range(self, l: mm.Lookup, parent, ctx: Context):
    #     start, end, freq, date = l.args
    #     result = []

    #     range_end = num_days = mm.Var(type=b.core.Number, name="num_days")
    #     result.append(mm.Lookup(b.datetime.dates_period_days, (start, end, num_days)))

    #     assert isinstance(freq, mm.Literal) and isinstance(freq.value, str)
    #     if freq.value in ["W", "M", "Y"]:
    #         range_end = mm.Var(type=b.core.Number, name="range_end")
    #         x = mm.Var(type=b.core.Number, name="x")
    #         result.append(mm.Lookup(b.core.mul, (num_days, mm.Literal(b.core.Float, _days[freq.value]), x)))
    #         result.append(mm.Lookup(b.math.ceil, (x, range_end)))

    #     # date_range is inclusive. add 1 since std.range is exclusive
    #     tmp = mm.Var(type=b.core.Number, name="tmp")
    #     result.append(mm.Lookup(b.core["+"], (range_end, mm.Literal(b.core.Number, 1), tmp)))
    #     ix = mm.Var(type=b.core.Number, name="ix")
    #     result.append(mm.Lookup(b.common.range, (mm.Literal(b.core.Number, 0), tmp, mm.Literal(b.core.Number, 1), ix)))

    #     tmp2 = mm.Var(type=b.core.Number, name="tmp2")
    #     result.append(mm.Lookup(_periods[freq.value], (ix, tmp2)))
    #     result.append(mm.Lookup(b.datetime.date_add, (start, tmp2, date)))

    #     result.append(mm.Lookup(b.core[">="], (end, date)))

    #     return self.translate_node(mm.Logical(
    #         body=tuple(result)
    #     ))
