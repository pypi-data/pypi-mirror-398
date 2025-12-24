"""
Helpers to analyze the metamodel IR.
"""
from __future__ import annotations

import re
from dataclasses import fields
from typing import cast, Tuple, Iterable, Optional, TypeVar
from v0.relationalai.semantics.metamodel import ir, visitor, builtins, types, factory as f
from v0.relationalai.semantics.metamodel.util import NameCache, OrderedSet, FrozenOrderedSet, flatten_tuple, ordered_set



#--------------------------------------------------
# Name helpers
#--------------------------------------------------

def sanitize(name:str) -> str:
    """ Cleanup the name to make it more palatable to names. """
    x = re.sub(r"[ ,\.\(\)\|]", "_", name)
    return x[0:-1] if x[-1] == "_" else x

#--------------------------------------------------
# Checks
#--------------------------------------------------

def is_concept_lookup(node: ir.Lookup|ir.Relation):
    """ Whether this task is a concept lookup. """
    if isinstance(node, ir.Lookup) and is_concept_lookup(node.relation):
        return True
    return builtins.concept_relation_annotation in node.annotations

def is_external(relation: ir.Relation):
   """ Whether this relation is external, by being marked with the external annotation. """
   return builtins.external_annotation in relation.annotations

def is_from_cast(node: ir.Lookup|ir.Relation):
    """ Whether this relation is from cast, by being marked with the from_cast_annotation annotation. """
    if isinstance(node, ir.Lookup) and is_from_cast(node.relation):
        return True
    return builtins.from_cast_annotation in node.annotations

def is_aggregate_input(var: ir.Var, agg: ir.Aggregate):
    """ Whether this var is an input to this aggregation. """
    return (var in agg.args and agg.aggregation.fields[agg.args.index(var)].input)

def is_effective_logical(n: ir.Task):
    """ Whether this task is a Logical and contains an Update child, recursively. """
    return isinstance(n, ir.Logical) and len(visitor.collect_by_type(ir.Update, n)) > 0

def is_nullable_logical(n: ir.Task):
    """ Whether this task is a Logical that contains a hoisted variable with a None default. """
    return isinstance(n, ir.Logical) and any(isinstance(v, ir.Default) and v.value is None for v in n.hoisted)

def relation_is_subtype(r1: ir.Relation, r2: ir.Relation):
    if r1 is r2:
        return True
    if len(r1.fields) != len(r2.fields):
        return False
    return all(types.is_subtype(f1.type, f2.type) for f1, f2 in zip(r1.fields, r2.fields))

def relation_is_proper_subtype(r1: ir.Relation, r2: ir.Relation):
    if r1 is r2:
        return False
    if relation_is_subtype(r1, r2):
        return any(types.is_proper_subtype(f1.type, f2.type) for f1, f2 in zip(r1.fields, r2.fields))
    else:
        return False

def relation_name_prefix(relation: ir.Relation):
    prefix = ""
    if len(relation.fields) > 0 and not is_concept_lookup(relation):
        main_type = relation.fields[0].type
        if (isinstance(main_type, ir.ScalarType) and
            main_type not in types.builtin_types and
            not relation.name.startswith(main_type.name) and
            not relation.name.startswith("_")):
                prefix = f"{main_type.name.lower()}_"
    return prefix

def get_outputs(lookup: ir.Lookup):
    """
        Return an array with the arguments of this lookup that are referring to output fields
        on the relation being looked up.
    """
    if builtins.is_eq(lookup.relation):
        # special case eq because it can be input or output
        x, y = lookup.args[0], lookup.args[1]
        if isinstance(x, ir.Var) and not isinstance(y, ir.Var):
            return [x]
        elif not isinstance(x, ir.Var) and isinstance(y, ir.Var):
            return [y]
        # both are inputs
        return []
    else:
        outputs = []
        # register variables depending on the input flag of the relation bound to the lookup
        for idx, fld in enumerate(lookup.relation.fields):
            arg = lookup.args[idx]
            if isinstance(arg, Iterable):
                # deal with ListType fields that pack arguments in a tuple
                for element in arg:
                    if isinstance(element, ir.Var) and not fld.input:
                        outputs.append(element)
            else:
                if isinstance(arg, ir.Var) and not fld.input:
                    outputs.append(arg)
        return outputs

def get_agg_outputs(lookup: ir.Aggregate):
    """
        Return an array with the arguments of this aggregate that are referring to output fields
        on the relation being looked up.
    """
    outputs = []
    # register variables depending on the input flag of the relation bound to the lookup
    for idx, fld in enumerate(lookup.aggregation.fields):
        arg = lookup.args[idx]
        if isinstance(arg, Iterable):
            # deal with ListType fields that pack arguments in a tuple
            for element in arg:
                if isinstance(element, ir.Var) and not fld.input:
                    outputs.append(element)
        else:
            if isinstance(arg, ir.Var) and not fld.input:
                outputs.append(arg)
    return outputs

#--------------------------------------------------
# Filters
#--------------------------------------------------

def aggregate_outputs(agg: ir.Aggregate) -> list[ir.Var]:
    """ Get the list of vars bound to the outputs of this aggregation. """
    return list(filter(lambda arg: isinstance(arg, ir.Var) and not is_aggregate_input(arg, agg), agg.args)) # type: ignore

def aggregate_inputs(agg: ir.Aggregate) -> list[ir.Var]:
    """ Get the list of vars bound to the args that are inputs of this aggregation. """
    return list(filter(lambda arg: isinstance(arg, ir.Var) and is_aggregate_input(arg, agg), agg.args)) # type: ignore

def effective_logicals(tasks: OrderedSet[ir.Task]) -> OrderedSet[ir.Logical]:
    """ Filter tasks to return only the Logical tasks that are effective. """
    return OrderedSet.from_iterable(filter(lambda t: is_effective_logical(t), tasks))

def nullable_logicals(tasks: OrderedSet[ir.Task]) -> OrderedSet[ir.Logical]:
    """ Filter tasks to return only the Logical tasks that are nullable. """
    return OrderedSet.from_iterable(filter(lambda t: is_nullable_logical(t), tasks))

def hoisted_vars(hoisted: Iterable[ir.VarOrDefault]) -> list[ir.Var]:
    """ Extract the vars from defaults in the hoisted list, returning just Vars. """
    return [hoisted_var(v) for v in hoisted]

def hoisted_var(hoisted: ir.VarOrDefault) -> ir.Var:
    """ Extract the var from VarOrDefault, returning just Var. """
    return hoisted.var if isinstance(hoisted, ir.Default) else hoisted

def vars(args: Tuple[ir.Value, ...]) -> list[ir.Var]:
    """ Filter this list of values, keeping only Vars. """
    return cast(list[ir.Var], list(filter(lambda v: isinstance(v, ir.Var), flatten_tuple(args, ir.Value))))

def output_vars(aliases: FrozenOrderedSet[Tuple[str, ir.Value]]) -> list[ir.Var]:
    return [alias[1] for alias in aliases if isinstance(alias[1], ir.Var)]

def output_values(aliases: FrozenOrderedSet[Tuple[str, ir.Value]]) -> list[ir.Value]:
    return [alias[1] for alias in aliases]

def output_alias_names(aliases: FrozenOrderedSet[Tuple[str, ir.Value]]) -> list[str]:
    return [alias[0] for alias in aliases]

#--------------------------------------------------
# Visitors/Collectors
#--------------------------------------------------

def collect_vars(*nodes: ir.Node) -> OrderedSet[ir.Var]:
    """ Collect all Vars starting at this node. """
    return cast(OrderedSet[ir.Var],
        visitor.collect_by_type(ir.Var, *nodes)
    )

def collect_quantified_vars(*nodes: ir.Node) -> OrderedSet[ir.Var]:
    """ Collect all Vars that are children of Exists and ForAll. """
    return cast(OrderedSet[ir.Var],
        visitor.collect(
            lambda n, parent: isinstance(n, ir.Var) and isinstance(parent, (ir.Exists, ir.ForAll)),
            *nodes)
    )

def collect_aggregate_vars(*nodes: ir.Node) -> OrderedSet[ir.Var]:
    """ Collect vars that are declared by aggregates in Rel (projection + over). """
    return cast(OrderedSet[ir.Var],
        # TODO - when dealing with multiple aggregations we will need to consider groupbys
        visitor.collect(
            lambda n, parent:
                # parent of var is an aggregate and either
                isinstance(parent, ir.Aggregate) and isinstance(n, ir.Var) and (
                # var is in the projection
                n in parent.projection or
                # var is an input to the aggregation's relation
                is_aggregate_input(n, parent)
                ),
            *nodes)
    )

def collect_rank_vars(*nodes: ir.Node) -> OrderedSet[ir.Var]:
    """ Collect vars that are declared by ranks in Rel (projection + over). """
    return cast(OrderedSet[ir.Var],
        # TODO - when dealing with multiple aggregations we will need to consider groupbys
        visitor.collect(
            lambda n, parent:
                # parent of var is an aggregate and either
                isinstance(parent, ir.Rank) and isinstance(n, ir.Var) and (
                # var is in the projection
                n in parent.projection or
                n in parent.args
                ),
            *nodes)
    )

def collect_implicit_vars(*nodes: ir.Node) -> OrderedSet[ir.Var]:
    """ Collect vars except the quantified and aggregate vars. """
    if not nodes:
        return ordered_set()
    return collect_vars(*nodes) - collect_quantified_vars(*nodes) - collect_aggregate_vars(*nodes) - collect_rank_vars(*nodes)

#--------------------------------------------------
# Useful node categories
#--------------------------------------------------

BINDERS = (ir.Lookup, ir.Construct, ir.Aggregate, ir.Exists, ir.Data, ir.Not)
COMPOSITES = (ir.Logical, ir.Sequence, ir.Union, ir.Match, ir.Until, ir.Wait)
EFFECTS = (ir.Update, ir.Output)

#--------------------------------------------------
# Helper classes
#--------------------------------------------------

class RewriteContext():
    """
    Container of information collected during a rewrite pass.
    """
    def __init__(self):
        # the logicals that will be at the top level at the end of the rewrite
        self.top_level: list[ir.Logical] = []
        # new relations created during the pass
        self.relations: list[ir.Relation] = []


#--------------------------------------------------
# Rewrite helpers
#--------------------------------------------------

def extract(task: ir.Task, body: OrderedSet[ir.Task], exposed_vars: list[ir.Var], ctx: RewriteContext, name: str) -> ir.Relation:
    """
    Extract into this Analysiscontext a new top level Logical that contains this body plus a
    derive task into a new temporary relation, which is also registered with the ctx.
    The exposed_vars determine the arguments of this temporary relation. The prefix
    can be used to customize the name of the relation, which defaults to the task kind.

    Return the temporary relation created for the extraction.
    """
    connection = create_connection_relation(task, exposed_vars, ctx, name)

    # add derivation to the extracted body
    body.add(f.derive(connection, exposed_vars))

    # extract the body
    ctx.top_level.append(clone_task(ir.Logical(task.engine, tuple(), tuple(body))))

    return connection

def create_connection_relation(task: ir.Task, exposed_vars: list[ir.Var], ctx: RewriteContext, name: str) -> ir.Relation:
    """
    Create a new relation with a name based off this task, with fields that represent
    the types and names of these exposed vars, and register in the context.
    """
    connection = f.relation(name, [f.field(v.name, v.type) for v in exposed_vars])
    ctx.relations.append(connection)

    return connection


def create_task_name(name_cache: NameCache, task: ir.Task, prefix: Optional[str]=None) -> str:
    """ Helper to generate consistent names for tasks extracted from a logical. """
    prefix = prefix if prefix else f"_{task.kind}"
    return name_cache.get_name(task.id, prefix)


CLONABLE = (ir.Var, ir.Default, ir.Task)
T = TypeVar('T', bound=ir.Task)
def clone_task(task: T) -> T:
    """
    Create a new task that is a clone of this task. This operation clones only sub-tasks
    and variables, and preserves variable references.

    This is useful when we are rewriting the metamodel and want to copy parts of a task to
    some other place. It is important to clone to avoid having the same object present
    multiple times in the metamodel.
    """

    # map from original object id to the rewritten object
    cache = {}
    def from_cache(original):
        """ Lookup this object from the cache above, dealing with collections and with
        objects that were not rewritten. """
        if isinstance(original, tuple):
            return tuple([from_cache(c) for c in original])
        elif isinstance(original, FrozenOrderedSet):
            return ordered_set(*[from_cache(c) for c in original])
        elif isinstance(original, CLONABLE):
            return cache.get(original.id, original)
        else:
            return original

    # the last node that was processed and rewritten
    prev_node = None
    stack: list[ir.Node] = [task]
    def to_stack(original):
        """ Add this original node to the stack if it is clonable and was never processed;
        return True iff the node was added to the stack. """
        if isinstance(original, CLONABLE) and original.id not in cache:
            stack.append(original)
            return True
        return False

    while stack:
        # peek the current node and get the initializable fields (i.e. ignore Node id)
        curr = stack[-1]
        curr_fields = list(filter(lambda f: f.init, fields(curr)))
        stacked_children = False

        # go over the fields adding to the stack the ones that we need to rewrite
        for field in curr_fields:
            field_value = getattr(curr, field.name)
            if isinstance(field_value, (tuple, FrozenOrderedSet)):
                # node field is a collection (tuple or set)
                for s in field_value:
                    if isinstance(s, tuple):
                        # the value within the collection is a tuple (can happen for lookup args)
                        for c in s:
                            stacked_children = to_stack(c) or stacked_children
                    else:
                        # the value within the collection is a scalar
                        stacked_children = to_stack(s) or stacked_children
            else:
                # node field is a scalar
                stacked_children = to_stack(field_value) or stacked_children

        # if no childrean were stacked, we rewrote all fields of curr, so we can pop it and rewrite it
        if not stacked_children:
            stack.pop()
            if curr.id not in cache:
                children = []
                for f in curr_fields:
                    children.append(from_cache(getattr(curr, f.name)))
                # create a new prev_node with the cloned children
                prev_node = curr.__class__(*children)
                cache[curr.id] = prev_node

    # the last node we processed is the rewritten original node
    assert(isinstance(prev_node, type(task)))
    return prev_node
