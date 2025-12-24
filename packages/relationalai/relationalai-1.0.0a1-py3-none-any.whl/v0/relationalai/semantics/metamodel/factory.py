"""
    Functions to simplify the creation of IR nodes using some common variations.
"""
from __future__ import annotations
from typing import Any, Tuple, Optional, Sequence as PySequence, Union
import datetime
import decimal


from v0.relationalai.semantics.metamodel import ir, types
from v0.relationalai.semantics.metamodel.util import OrderedSet, FrozenOrderedSet, ordered_set, frozen

import pandas as pd

#-------------------------------------------------
# Public Types - Model
#-------------------------------------------------

def model(
        engines: OrderedSet[ir.Engine],
        relations: OrderedSet[ir.Relation],
        types: OrderedSet[ir.Type],
        root: ir.Task,
        annos: PySequence[ir.Annotation]=[]):
    return ir.Model(
        engines.frozen(),
        relations.frozen(),
        types.frozen(),
        root,
        FrozenOrderedSet(annos)
    )

def compute_model(root: ir.Task) -> ir.Model:
    from v0.relationalai.semantics.metamodel.visitor import collect_by_type
    return model(
        collect_by_type(ir.Engine, root),
        collect_by_type(ir.Relation, root),
        _collect_reachable_types(collect_by_type(ir.Type, root)),
        root
    )

def _collect_reachable_types(type_set: OrderedSet[ir.Type]) -> OrderedSet[ir.Type]:
    """ Collect all types reachable from these types + builtins, including super types, element types, etc. """
    # add all built-in types
    type_set.update(types.builtin_types)

    # add super types and element types of collections
    to_visit = type_set.get_list().copy()
    while to_visit:
        t = to_visit.pop()
        type_set.add(t)
        if isinstance(t, ir.ScalarType):
            to_visit.extend(t.super_types)
        elif isinstance(t, (ir.ListType)):
            to_visit.append(t.element_type)
        elif isinstance(t, (ir.UnionType, ir.TupleType)):
            to_visit.extend(t.types)
    return type_set

#-------------------------------------------------
# Public Types - Engine
#-------------------------------------------------

def capability(name: str):
    return ir.Capability(name)

def engine(name: str, platform: str, relations:OrderedSet[ir.Relation], info: Any=None, capabilities: OrderedSet[ir.Capability]=ordered_set(), annos: PySequence[ir.Annotation]=[]):
    return ir.Engine(name, platform, info, capabilities.frozen(), relations.frozen(), FrozenOrderedSet(annos))

#-------------------------------------------------
# Public Types - Data
#-------------------------------------------------

def scalar_type(name: str, super_types:list[ir.ScalarType]=[], annos: PySequence[ir.Annotation]=[]):
    return ir.ScalarType(name, FrozenOrderedSet(super_types), FrozenOrderedSet(annos))

def decimal_type(name: str, precision: int, scale: int, annos: PySequence[ir.Annotation]=[]):
    return ir.DecimalType(name, frozen(), FrozenOrderedSet(annos), precision, scale)

def list_type(element_type: ir.Type):
    return ir.ListType(element_type)

def union_type(types: list[ir.Type]):
    return ir.UnionType(FrozenOrderedSet(types))

def field(name: str, type: ir.Type, input: bool=False):
    return ir.Field(name, type, input)

def input_field(name:str, type: ir.Type):
    return ir.Field(name, type, True)


# property helpers
def relation(name: str, fields: list[ir.Field], requires: OrderedSet[ir.Capability]=ordered_set(), annos: PySequence[ir.Annotation]=[], overloads: PySequence[ir.Relation]=[]):
    return ir.Relation(name, tuple(fields), requires.frozen(), FrozenOrderedSet(annos), FrozenOrderedSet(overloads))

def entity(type: ir.ScalarType):
    return relation(type.name, [field("id", type)])

def property(name: str, key_name: str, key_type: ir.Type, value_name:str, value_type: ir.Type):
    return relation(
        name,
        [field(key_name, key_type), field(value_name, value_type)]
    )

#-------------------------------------------------
# Public Types - Tasks
#-------------------------------------------------

def success():
    return ir.Task(None)

#
# Task composition
#

def logical(body: PySequence[ir.Task], hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Logical(engine, tuple(hoisted), tuple(body), FrozenOrderedSet(annos))

def sequence(tasks: PySequence[ir.Task], hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Sequence(engine, tuple(hoisted), tuple(tasks), FrozenOrderedSet(annos))

def union(tasks: PySequence[ir.Task], hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Union(engine, tuple(hoisted), tuple(tasks), FrozenOrderedSet(annos))

def match(tasks: PySequence[ir.Task], hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Match(engine, tuple(hoisted), tuple(tasks), FrozenOrderedSet(annos))

def until(check: ir.Task, body: ir.Task, hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Until(engine, tuple(hoisted), check, body, FrozenOrderedSet(annos))

def wait(check: ir.Task, hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Wait(engine, tuple(hoisted), check, FrozenOrderedSet(annos))

#
# Constraints
#

def check(check:ir.Task, error:Optional[ir.Task], annos: PySequence[ir.Annotation]=[]):
    return ir.Check(check, error, FrozenOrderedSet(annos))

def require(domain:ir.Task, checks:PySequence[ir.Check], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Require(engine, domain, tuple(checks), FrozenOrderedSet(annos))

#
# Relational Operations
#

def var(name: str, type: Union[ir.Type, None] = None) -> ir.Var:
    if type is None:
        return ir.Var(types.Any, name)
    else:
        return ir.Var(type, name)

def default(var: ir.Var, value: ir.Value) -> ir.Default:
    return ir.Default(var, value)

def wild(type: ir.Type) -> ir.Var:
    return var("_", type)

def literal(value: Any, type: Union[ir.Type, None] = None) -> ir.Value:
    """ Create a Literal with this type. If type is not present, attempt to figure out the
    appropriate type. See: `l`. """
    if type is None:
        return lit(value)
    else:
        return ir.Literal(type, value)

def data(df: pd.DataFrame, vars: PySequence[ir.Var], engine:Optional[ir.Engine]=None) -> ir.Data:
    """ Create a DataFrame literal. """
    return ir.Data(engine, df, tuple(vars))

def lit(value: Any) -> ir.Value:
    """ Ensure this value is an appropriate ir.Value. This function wraps common python values
     in ir.Literals, and supports lists of values. """
    if isinstance(value, ir.Literal):
        return value
    elif isinstance(value, str):
        return ir.Literal(types.String, value)
    elif isinstance(value, int):
        return ir.Literal(types.Int128, value)
    elif isinstance(value, float):
        return ir.Literal(types.Float, value)
    elif isinstance(value, bool):
        return ir.Literal(types.Bool, value)
    elif isinstance(value, decimal.Decimal):
        return ir.Literal(types.Decimal, value)
    # datetime.datetime is a subclass of datetime.date, so check it first
    elif isinstance(value, datetime.datetime):
        return ir.Literal(types.DateTime, value)
    elif isinstance(value, datetime.date):
        return ir.Literal(types.Date, value)
    elif isinstance(value, list):
        return tuple([lit(v) for v in value])
    else:
        raise NotImplementedError(f"literal value: {value} of type {type(value)}")

def annotation(relation: ir.Relation, args: PySequence[ir.Value]) -> ir.Annotation:
    return ir.Annotation(relation, tuple(args))

def derive(relation: ir.Relation, args: PySequence[ir.Value], annos: PySequence[ir.Annotation]=[], engine: Optional[ir.Engine]=None):
    return ir.Update(engine, relation, tuple(args), ir.Effect.derive, FrozenOrderedSet(annos))

def insert(relation: ir.Relation, args: PySequence[ir.Value], annos: PySequence[ir.Annotation]=[], engine: Optional[ir.Engine]=None):
    return ir.Update(engine, relation, tuple(args), ir.Effect.insert, FrozenOrderedSet(annos))

def delete(relation: ir.Relation, args: PySequence[ir.Value], annos: PySequence[ir.Annotation]=[], engine: Optional[ir.Engine]=None):
    return ir.Update(engine, relation, tuple(args), ir.Effect.delete, FrozenOrderedSet(annos))

def lookup(relation: ir.Relation, args: PySequence[ir.Value], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Lookup(engine, relation, tuple(args), FrozenOrderedSet(annos))

def update(relation: ir.Relation, args: PySequence[ir.Value], effect: ir.Effect, annos: PySequence[ir.Annotation]=[], engine: Optional[ir.Engine]=None):
    return ir.Update(engine, relation, tuple(args), effect, FrozenOrderedSet(annos))

def output(values: PySequence[Union[ir.Value, Tuple[str, ir.Value]]], keys: Optional[PySequence[ir.Var]] = None, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    """Create an output task that will return values bound to these variables. The values
    sequence can contain plain Values, in which case the alias used in the output is the
    variable name. This alias can be customized by adding a tuple (alias, Value) to values.
    """
    s = ordered_set()
    for x in values:
        if isinstance(x, ir.Var):
            s.add((x.name, x))
        else:
            s.add(x)
    return ir.Output(engine, s.frozen(), keys if keys is None else FrozenOrderedSet.from_iterable(keys), FrozenOrderedSet(annos))


def construct(var: ir.Var, bindings: dict[ir.Relation, Any], prefix: Optional[list[Any]]=None, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    """
    Create a Construct node that will create an id and bind to this var.

    The id will be a hash composed of:
    - the prefix values if they are set; otherwise the prefix is the type of the var.
    - followed by the name and value of each of the bindings.
    """
    values = []
    if prefix:
        values.extend(prefix)
    else:
        values.append(var.type)
    for relation, value in bindings.items():
        values.append(ir.Literal(types.String, relation.name))
        if isinstance(value, ir.Node):
            values.append(value)
        else:
            values.append(lit(value))
    return ir.Construct(engine, tuple(values), var, FrozenOrderedSet(annos))

def aggregate(aggregation: ir.Relation, projection: PySequence[ir.Var], group: PySequence[ir.Var], args: PySequence[Any], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Aggregate(engine, aggregation, tuple(projection), tuple(group), tuple(args), FrozenOrderedSet(annos))

def rank(projection: PySequence[ir.Var], group: PySequence[ir.Var], args: PySequence[ir.Var], arg_is_ascending: PySequence[bool], result: ir.Var, limit: int = 0, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Rank(engine, tuple(projection), tuple(group), tuple(args), tuple(arg_is_ascending), result, limit, FrozenOrderedSet(annos))


#
# Logical Quantifiers
#

def not_(task: ir.Task, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return Not(task, engine, annos)

def Not(task: ir.Task, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Not(engine, task, FrozenOrderedSet(annos))

def exists(vars: PySequence[ir.Var], task: ir.Task, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Exists(engine, tuple(vars), task, FrozenOrderedSet(annos))

def for_all(vars: PySequence[ir.Var], task: ir.Task, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.ForAll(engine, tuple(vars), task, FrozenOrderedSet(annos))


#
# Iteration (Loops)
#

# loops body until a break condition is met
def loop(iter: ir.Var, body: ir.Task, hoisted: PySequence[ir.VarOrDefault]=[], engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Loop(engine, tuple(hoisted), iter, body, FrozenOrderedSet(annos))

def break_(check: ir.Task, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return Break(check, engine, annos)

def Break(check: ir.Task, engine: Optional[ir.Engine]=None, annos: PySequence[ir.Annotation]=[]):
    return ir.Break(engine, check, FrozenOrderedSet(annos))
