from __future__ import annotations
import base64
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import numbers
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union, Any, cast
import json
import textwrap
from datetime import datetime, date
import rich

#--------------------------------------------------
# Base
#--------------------------------------------------

id = 0
def next_id():
    global id
    id += 1
    return id

@dataclass
class Base():
    id: int = field(default_factory=next_id, init=False)

    def __str__(self):
        return Printer().print(self)

#--------------------------------------------------
# Data
#--------------------------------------------------

@dataclass
class Type(Base):
    name: str = ""
    properties: List['Property'] = field(default_factory=list)
    parents: List['Type'] = field(default_factory=list)
    agent: Optional['Agent'] = None

    def isa(self, other: 'Type') -> bool:
        if self == other:
            return True
        for p in self.parents:
            if p.isa(other):
                return True
        return False

    def __hash__(self) -> int:
        return self.id

UnknownType = Type("Unknown")

@dataclass
class Property(Base):
    name: str
    type: Type
    is_input: bool = False
    parents: List[Type] = field(default_factory=list)

    def __hash__(self) -> int:
        return self.id

    @staticmethod
    def find(name:str, types:List[Type], ignore_case=False) -> Optional['Property']:
        found = None
        for t in types:
            if found:
                break
            for p in t.properties:
                if p.name == name or (ignore_case and p.name.lower() == name.lower()):
                    found = p
                    break
        return found

@dataclass
class Agent(Base):
    name: str
    platform: str  # SQL, Rel, JS, OpenAI, etc
    info: Any

    def __hash__(self) -> int:
        return self.id

#--------------------------------------------------
# Task
#--------------------------------------------------

class Behavior(Enum):
    Query = "query"
    Union = "union"
    OrderedChoice = "ordered_choice"
    Sequence = "sequence"
    Catch = "catch"

@dataclass
class Task(Type):
    behavior: Behavior = Behavior.Query
    items: List['Action'] = field(default_factory=list)
    bindings: Dict[Property, 'Var'] = field(default_factory=dict)
    inline: bool = False

    _task_builtin: Any = None
    def __post_init__(self):
        self.parents.append(Task._task_builtin)

    def __hash__(self) -> int:
        return self.id

    def return_cols(self, allow_dups=True) -> List[str]:
        namer = Namer()
        for i in self.items:
            ent = i.entity.value
            if i.action == ActionType.Call and isinstance(ent, Task):
                sub = ent.return_cols()
                if len(sub):
                    return sub
            if i.action == ActionType.Bind and i.entity.isa(Builtins.Return):
                cols = []
                for (prop, var) in i.bindings.items():
                    if allow_dups:
                        cols.append(namer.get(var) or namer.get(prop))
                    else:
                        cols.append(namer.get_safe_name(var.name or prop.name))
                return cols
        return []

    def has_persist(self, seen=None) -> bool:
        if seen is None:
            seen = set()
        for i in self.items:
            if i.action in [ActionType.Persist, ActionType.Unpersist]:
                return True
            vs = i.vars()
            for v in vs:
                if v not in seen:
                    seen.add(v)
                    if v.value and isinstance(v.value, Task) and v.value.has_persist(seen):
                        return True
        return False

    def requires_provides(self, seen = None) -> Tuple[Set['Var'], Set['Var'], Set['Var']]:
        sub_requires = set()
        sub_provides = set()
        refs = set()
        for i in self.items:
            r, p, sub_refs = i.requires_provides(seen)
            sub_requires.update(r)
            sub_provides.update(p)
            refs.update(p | sub_refs)
        return sub_requires - sub_provides, sub_provides, refs

    def normalize(self):
        entity_action:Dict[Any, Action] = {}
        seen = set()
        collapsed:List[Action] = []
        for i in self.items:
            if i in seen:
                continue # prevent duplicates
            seen.add(i)

            # recurse on subtasks
            ent = i.entity.value
            if isinstance(ent, Task):
                ent.normalize()
            for (_, var) in i.bindings.items():
                if isinstance(var.value, Task):
                    var.value.normalize()

            # we can only collapse get, bind, persist, unpersist
            if i.action not in [ActionType.Get, ActionType.Bind, ActionType.Persist, ActionType.Unpersist]:
                collapsed.append(i)
                continue

            found = entity_action.get((i.entity, i.action))
            if not found:
                if len(i.types) or len(i.bindings):
                    entity_action[(i.entity, i.action)] = i
                    collapsed.append(i)
            else:
                # merge with existing
                exists = False
                for key, val in i.bindings.items():
                    found_val = found.bindings.get(key)
                    if found_val is not None and found_val is not val: #and (not found_val.value or found_val.value is not val.value):
                        exists = True
                if not exists:
                    found.types.extend([x for x in i.types if x not in found.types])
                    found.bindings.update(i.bindings)
                else:
                    collapsed.append(i)

        if self.behavior == Behavior.Query:
            try:
                self.items = Utils.sort(collapsed)
            except Exception:
                rich.print("[red bold]Stratification failed[/red bold][red]\nThings may not work correctly. Please send us this program so we can take a look!\n")
                self.items = collapsed
        else:
            self.items = collapsed

#--------------------------------------------------
# Var
#--------------------------------------------------

Value = Union[str, numbers.Number, int, float, bool, Task, Property, Type, bytes,
              datetime, date, List['Value'], List['Var']]

@dataclass
class Var(Base):
    id: int = field(default_factory=next_id, init=False)
    type: Type = UnknownType
    name: Optional[str] = None
    value: Optional[Value] = None

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, other: object) -> bool:
        if type(other) is not Var:
            return False
        if super().__eq__(other):
            return True
        if other.value is not None and self.value is not None:
            return other.value is self.value
        return False

    def isa(self, other: Type) -> bool:
        return bool(self.type.isa(other) or (self.value and isinstance(self.value, Type) and self.value.isa(other)))

#--------------------------------------------------
# Action
#--------------------------------------------------

class ActionType(Enum):
    Get = "get"
    Call = "call"
    Persist = "persist"
    Unpersist = "unpersist"
    Bind = "bind"
    Construct = "construct"

    def is_effect(self):
        return self in [ActionType.Bind, ActionType.Persist, ActionType.Unpersist]

@dataclass
class Action(Base):
    action: ActionType
    entity: Var
    types: List[Type] = field(default_factory=list)
    bindings: Dict[Property, Var] = field(default_factory=dict)

    def __post_init__(self):
        from . import debugging
        debugging.set_source(self)

    def requires_provides(self, seen = None) -> Tuple[Set[Var], Set[Var], Set[Var]]:
        requires = set()
        provides = set()
        refs = set()
        if not seen:
            seen = set()
        if self in seen:
            return requires, provides, refs

        seen.add(self)
        is_sub_task = self.is_subtask_call()
        if is_sub_task:
            sub_requires = set()
            sub_provides = set()
            for i in cast(Task, self.entity.value).items:
                r, p, sub_refs = i.requires_provides(seen)
                sub_requires.update(r)
                sub_provides.update(p)
                refs.update(p | sub_refs)
            requires.update(sub_requires - sub_provides)

        if self.action == ActionType.Get and self.entity.value is None:
            if len(self.types):
                provides.add(self.entity)
            else:
                requires.add(self.entity)
        elif self.action != ActionType.Call and self.entity.value is None:
            requires.add(self.entity)

        items = [*self.bindings.items()]
        if self.action == ActionType.Construct:
            provides.add(items[-1][1])
            items = items[:-1]

        for k,var in items:
            into = provides
            if self.action in [ActionType.Bind, ActionType.Persist, ActionType.Unpersist, ActionType.Construct]:
                into = requires
            elif k.is_input:
                into = requires

            if var.value is not None and isinstance(var.value, list):
                for v in var.value:
                    if isinstance(v, Var) and v.value is None:
                        into.add(v)
            elif var.value is None:
                into.add(var)

        refs.update(requires)
        return requires - provides, provides, refs

    def vars(self, recursive=False, with_subs=False) -> Set[Var]:
        vars = set(self.bindings.values())
        vars.add(self.entity)
        if recursive:
            for v in list(vars):
                if isinstance(v.value, list):
                    for var in v.value:
                        if isinstance(var, Var) and var.value is None:
                            vars.add(var)
        if with_subs and self.is_subtask_call():
            for i in cast(Task, self.entity.value).items:
                vars.update(i.vars(recursive, with_subs))
        return vars

    def is_subtask_call(self) -> bool:
        return self.action == ActionType.Call \
                and isinstance(self.entity.value, Task) \
                and len(self.entity.value.items) > 0

    def append(self, item: Union[Type, Property, Task, Agent, Var], var: Optional[Var] = None):
        if isinstance(item, Type):
            self.types.append(item)
        elif isinstance(item, Property) and var:
            self.bindings[item] = var
        elif isinstance(item, Var):
            self.entity = item

    def equiv(self, other: 'Action') -> bool:
        if self is other:
            return True
        return self.action == other.action \
                and self.entity == other.entity \
                and self.types == other.types \
                and self.bindings == other.bindings

    def params_list(self) -> List[Var]:
        return list(self.bindings.values())

    def __hash__(self) -> int:
        return self.id

#--------------------------------------------------
# All
#--------------------------------------------------

AllItems = Union[Type, Property, Task, Agent, Var, Action]

#--------------------------------------------------
# Builtins
#--------------------------------------------------

class BuiltinsClass:
    def __init__(self) -> None:
        self.Primitive = Type("Primitive")

        self.Unknown = UnknownType
        self.Any = Type("Any")
        self.String = Type("String", parents=[self.Primitive])
        self.Number = Type("Number", parents=[self.Primitive])
        self.Int = Type("Int", parents=[self.Number])
        self.Decimal = Type("Decimal", parents=[self.Number])
        self.Bool = Type("Bool", parents=[self.Primitive])
        self.Type = Type("Type", parents=[self.Primitive])
        self.Property = Type("Property", parents=[self.Primitive])
        self.ValueType = Type("ValueType", parents=[self.Type])
        self.Symbol = Type("Type", parents=[self.Primitive])
        self.Missing = Type("Missing", parents=[self.Primitive])
        self.Relation = Type("Relation", parents=[self.Primitive], properties=[Property(f"v{i}", self.Any) for i in range(1000)])
        self.Anonymous = Type("Anonymous") # A thing we assume to exist in the host DB for which we don't have information.
        self.Task = Type("Task", parents=[self.Type, self.Relation])
        Task._task_builtin = self.Task
        self.Install = Task("Install", parents=[self.Task], properties=[Property("item", self.Any)])
        self.Distinct = Type("Distinct", parents=[])
        self.Return = Type("Return", parents=[self.Relation], properties=[Property(f"v{i}", self.Any) for i in range(20)])
        self.ReturnDistinct = Type("ReturnDistinct", parents=[self.Return, self.Distinct], properties=[Property(f"v{i}", self.Any) for i in range(20)])
        self.ExportReturn = Type("ExportReturn", parents=[self.Return], properties=[Property(f"v{i}", self.Any) for i in range(20)])
        self.ExportReturnDistinct = Type("ExportReturnDistinct", parents=[self.ExportReturn, self.Distinct], properties=[Property(f"v{i}", self.Any) for i in range(20)])
        self.RawCode = Type("RawCode", properties=[Property("code", self.String)])
        self.RawData = Type("RawData", parents=[self.Relation])
        self.Inline = Type("Inline", parents=[])
        self.Intermediate = Type("Intermediate", parents=[self.Relation])
        self.InlineRawData = Type("InlineRawData", parents=[self.RawData])
        self.InlineExpression = Type("InlineExpression", parents=[])
        self.Aggregate = Type("Aggregate", parents=[self.Task])
        self.Extender = Type("Extender", parents=[self.Aggregate])

        self.Annotation = Type("Annotation")
        self.InspectOptimizedSimple = Type("Inspect(:rel, 1)", parents=[self.Annotation])
        self.InspectOptimizedVerbose = Type("Inspect(:rel, 2)", parents=[self.Annotation])
        self.InlineAnnotation = Type("Inline", parents=[self.Annotation])
        self.NoInlineAnnotation = Type("No_Inline", parents=[self.Annotation])
        self.PipelineAnnotation = Type("Pipeline", parents=[self.Annotation])
        self.FunctionAnnotation = Type("Function", parents=[self.Annotation])
        self.PQEdgeAnnotation = Type("PQ_Edge", parents=[self.Annotation])
        self.PQFilterAnnotation = Type("PQ_Filter", parents=[self.Annotation])
        self.TrackConnAnnotation = Type("Track(:graphlib, :pathfinder_conn)", parents=[self.Annotation])

        self.Expensive = Type("Expensive")

        self.SingleValued = Type("SingleValued")
        self.MultiValued = Type("MultiValued")

        self.Identity = Type("Identity", parents=[self.String])
        self.make_identity = Task("make_identity", properties=[
            Property("params", self.Any, True),
            Property("identity", self.Any)
        ], parents=[self.Expensive])

        self.Infix = Type("Infix")
        self.Filter = Type("Filter")
        self.GlobalFilter = Type("GlobalFilter")

        self.Quantifier = Type("Quantifier", parents=[self.Task, self.GlobalFilter])
        self.Not = Task("Not", parents=[self.Quantifier], properties=[Property("group", self.Any, True), Property("task", self.Task, True)])
        self.Exists = Task("Exists", parents=[self.Quantifier], properties=[Property("group", self.Any, True), Property("task", self.Task, True)])
        self.Every = Task("Every", parents=[self.Quantifier], properties=[Property("group", self.Any, True), Property("task", self.Task, True)])

        self.NonFiltering = Type("NonFiltering", parents=[])
        self.BoolFilter = Type("pyrel_bool_filter", parents=[self.Relation, self.NonFiltering, self.SingleValued], properties=[
            Property("left", self.Any, True),
            Property("right", self.Any, True),
            Property("result", self.Bool, False),
            Property("relation", self.Relation, True),
        ])
        self.Default = Type("pyrel_default", parents=[self.Relation, self.NonFiltering, self.SingleValued], properties=[
            Property("relation", self.Relation, True),
            Property("default", self.Any, True),
            Property("ent", self.Any, True),
            Property("result", self.Any, False),
        ])

        self.ExternalInput = Type("External")
        self.EDB = Type("EDB", parents=[])

        def binary_op(op, with_result=False):
            t = Task(name=op, parents=[self.Infix, self.SingleValued], properties=[
                Property("a", self.Number, True),
                Property("b", self.Number, True),
            ])
            if with_result:
                t.properties.append(Property("result", self.Number))
            else:
                t.parents.append(self.Filter)
            return t

        def aggregate(op):
            return Task(name=op, parents=[self.Aggregate], properties=[
                Property("projection", self.Any, True),
                Property("group", self.Any, True),
                Property("pre_args", self.Any, True),
                Property("result", self.Number),
            ])

        self.gt = binary_op(">")
        self.gte = binary_op(">=")
        self.lt = binary_op("<")
        self.lte = binary_op("<=")
        self.eq = binary_op("=")
        self.approx_eq = binary_op("~=")
        self.neq = binary_op("!=")

        self.plus = binary_op("+", True)
        self.minus = binary_op("-", True)
        self.mult = binary_op("*", True)
        self.div = binary_op("/", True)
        self.floor_div = binary_op("::std::common::floor_divide", True)
        self.floor_div.parents = []

        self.pow = binary_op("^", True)
        self.mod = binary_op("::std::common::modulo", True)
        self.mod.parents = []

        self.count = aggregate("::std::common::count")
        self.prod = aggregate("::std::common::product")
        self.sum = aggregate("::std::common::sum")
        self.avg = aggregate("::std::common::average")
        self.min = aggregate("::std::common::min")
        self.max = aggregate("::std::common::max")

Builtins = BuiltinsClass()

#--------------------------------------------------
# Builder
#--------------------------------------------------

class Builder():
    def __init__(self, to_var):
        self.to_var = to_var

    def call(self, op, params:List[Any]):
        a = Action(ActionType.Call, Var(Builtins.Task, value=op))
        for ix, p in enumerate(params):
            a.append(op.properties[ix], self.to_var(p))
        return a

    def return_(self, params:List[Any], export=False, distinct=False):
        if export and distinct:
            return self.relation_action(ActionType.Bind, Builtins.ExportReturnDistinct, params)
        elif export:
            return self.relation_action(ActionType.Bind, Builtins.ExportReturn, params)
        elif distinct:
            return self.relation_action(ActionType.Bind, Builtins.ReturnDistinct, params)
        else:
            return self.relation_action(ActionType.Bind, Builtins.Return, params)

    def relation(self, name:str, field_count:int):
        return Type(name,
                    parents=[Builtins.Relation, Builtins.Anonymous],
                    properties=[Builtins.Relation.properties[i] for i in range(field_count)])

    def relation_action(self, action_type:ActionType, op:Type|Property, params:Iterable[Any]):
        a = Action(action_type, Var(Builtins.Type, value=op))
        for ix, p in enumerate(params):
            a.append(Builtins.Relation.properties[ix], self.to_var(p))
        return a

    def ident(self, action:Action, omit_type_in_hash=False) -> List[Action]:
        params = []
        if not omit_type_in_hash:
            params = [Var(value=t.name) for t in action.types]
        params.extend(action.bindings.values())
        actions = []
        ident = action.entity
        if action.entity.isa(Builtins.ValueType):
            ident = Var()
            actions.append(self.construct(action.entity.type, [ident, action.entity]))
        actions.append(self.call(Builtins.make_identity, [Var(value=params), ident]))
        actions.reverse()
        return actions

    def install(self, item:Type|Property):
        return self.call(Builtins.Install, [item])

    def construct(self, item:Type|Property, params:List[Any]):
        return self.relation_action(ActionType.Construct, item, params)

    def property_named(self, name:str, types:List[Type]):
        found = Property.find(name, types)
        if not found:
            ifound = Property.find(name, types, ignore_case=True)
            if ifound:
                from . import errors
                errors.PropertyCaseMismatch(name, ifound.name)
            found = Property(name, Builtins.Any)
        for t in types:
            if found not in t.properties:
                t.properties.append(found)
        return found

    def raw(self, code:str):
        code = textwrap.dedent(code)
        return self.relation_action(ActionType.Call, Builtins.RawCode, [code])

    def raw_task(self, code:str):
        return Task(behavior=Behavior.Sequence, items=[self.raw(textwrap.dedent(code))])

    def aggregate_def(self, op:str):
        return Task(name=op, parents=[Builtins.Aggregate], properties=[
            Property("group", Builtins.Any, True),
            Property("projection", Builtins.Any, True),
            Property("pre_args", Builtins.Any, True),
            Property("result", Builtins.Any),
        ])

    def eq(self, a:Any, b:Any, approx=False):
        if approx:
            return self.call(Builtins.approx_eq, [a, b])
        return self.call(Builtins.eq, [a, b])

#--------------------------------------------------
# Printer
#--------------------------------------------------

class Namer():
    def __init__(self, unnamed_vars=False):
        self.name_mapping = {}
        self.names = set()
        self.unnamed_vars = unnamed_vars

    def get_safe_name(self, name:str):
        name = name.lower()
        if name in self.names:
            ix = 2
            while f"{name}{ix}" in self.names:
                ix += 1
            name = f"{name}{ix}"
        self.names.add(name)
        return name

    def get(self, item:Var|Task|Type|Property):
        if item.id in self.name_mapping:
            return self.name_mapping[item.id]

        name = item.name if not self.unnamed_vars or not isinstance(item, Var) else None
        name = name or ("t" if isinstance(item, Task) else "v")
        name = self.get_safe_name(name)
        self.name_mapping[item.id] = name
        return name

    def reset(self):
        self.name_mapping.clear()
        self.names.clear()

class Printer():
    def __init__(self, unnamed_vars=False):
        self.indent = 0
        self.namer = Namer(unnamed_vars=unnamed_vars)

    def indent_str(self):
        return " " * 4 * self.indent

    def print(self, item:AllItems|Base|Value, is_sub=False):
        if isinstance(item, Task):
            return self.task(item, is_sub)
        elif isinstance(item, Type):
            return self.type(item, is_sub)
        elif isinstance(item, Property):
            return self.property(item, is_sub)
        elif isinstance(item, Agent):
            return self.agent(item, is_sub)
        elif isinstance(item, Var):
            return self.var(item, is_sub)
        elif isinstance(item, Action):
            return self.action(item, is_sub)
        elif isinstance(item, bytes):
            return base64.b64encode(item).decode()[:-2]
        elif isinstance(item, list):
            vs = [self.print(i, is_sub) for i in item]
            if len(item) > 20:
                return f"[{', '.join(vs[0:5])}, ... {', '.join(vs[-2:])}]"
            return f"[{', '.join(vs)}]"
        elif isinstance(item, str) or isinstance(item, bool) or isinstance(item, numbers.Number):
            return json.dumps(item)
        elif isinstance(item, datetime) or isinstance(item, date):
            return item.isoformat()
        return "UNKNOWN"
        # raise Exception(f"Unknown item type: {type(item)}")

    def type(self, type:Type, is_sub=False):
        return type.name

    def property(self, property:Property, is_sub=False):
        return property.name

    def task(self, task:Task, is_sub=False):
        self.indent += 1
        items = '\n'.join([self.print(i, is_sub) for i in task.items])
        self.indent -= 1
        behavior = task.behavior.value
        if is_sub:
            final = f"""{behavior}\n{items}\n"""
        else:
            final = f"""{self.indent_str()}{behavior}\n{items}\n"""
        return final

    def agent(self, agent:Agent, is_sub=False):
        return agent.name

    def var(self, var:Var, is_sub=False):
        if var.value is not None:
            if isinstance(var.value, Task):
                return "SUBTASK"
            elif isinstance(var.value, Type) or isinstance(var.value, Property):
                return str(var.value)
            return self.print(var.value, is_sub)
        return self.namer.get(var)

    def action(self, action:Action, is_sub=False):
        op = action.action.value
        entity_value = action.entity.value
        as_relation = False
        as_quantifier = False
        subs = []
        body = ""

        if entity_value == Builtins.Return:
            op = "return"
            as_relation = True
        elif isinstance(entity_value, Task):
            if op == "call" and len(entity_value.items):
                subs.append(entity_value)
            elif op == "call" and entity_value.isa(Builtins.Quantifier):
                as_quantifier = True
                subs.append(action.bindings[entity_value.properties[1]].value)
            else:
                as_relation = True
        elif isinstance(entity_value, Property) or isinstance(entity_value, Type):
            as_relation = True

        if as_relation:
            args = " ".join([self.print(v, is_sub) for _,v in action.bindings.items()])
            if op == "return":
                body = args
            else:
                entity_value = cast(Type, entity_value)
                rel_name = entity_value.name or self.namer.get(entity_value)
                body = f"{rel_name}({args})"
        elif as_quantifier:
            entity_value = cast(Task, entity_value)
            group_vars:Any = action.bindings[entity_value.properties[0]].value
            group = ", ".join([self.print(v) for v in group_vars])
            if group:
                body = f"{entity_value.name.lower()}({group}) "
            else:
                body = f"{entity_value.name.lower()} "
        elif not len(subs):
            types = [t.name for t in action.types]
            args = [f"{k.name}({self.print(v, is_sub)})" for k,v in action.bindings.items()]
            body = f"{self.print(action.entity)} | " + " ".join(types + args)

        final = f"{self.indent_str()}{op :>9} | {body}"
        if len(subs):
            self.indent += 1
            final += "\n".join([self.print(s, True) for s in subs])
            self.indent -= 1
        return final


#--------------------------------------------------
# Utils
#--------------------------------------------------

def _graph_debug(actions, in_degree, vars_provided_by):
    rich.print("\n[yellow bold]STRATIFY CHECK")
    for item in actions:
        print("-------------------------------------------")
        print(in_degree.get(item, 0), item)
        (requires, provides, refs) = item.requires_provides()
        if item.is_subtask_call():
            for ref in refs:
                if vars_provided_by.get(ref):
                    requires.add(ref)
        rich.print("    in:", ", ".join([str(r.id) for r in requires]))
        rich.print("    out:", ", ".join([str(p.id) for p in provides]))
        rich.print("    refs:", ", ".join([str(r.id) for r in refs]))

class Utils:

    @staticmethod
    def action_graph(actions:List[Action]):
        graph:Dict[Action, List[Action]] = defaultdict(list)
        in_degree:Dict[Action, int] = defaultdict(int)
        vars_provided_by:Dict[Var, List[Action]] = defaultdict(list)
        vars_required_by:Dict[Var, List[Action]] = defaultdict(list)

        item_refs = {}
        cut_vars = set()

        for item in actions:
            (requires, provides, refs) = item.requires_provides()
            if item.is_subtask_call():
                item_refs[item] = refs
            for var in provides:
                if var in cut_vars:
                    vars_required_by[var].append(item)
                else:
                    vars_provided_by[var].append(item)
            for var in requires:
                vars_required_by[var].append(item)

            if item.entity.isa(Builtins.Aggregate) or item.entity.isa(Builtins.Relation):
                cut_vars.update(provides)


        # ensure that subtasks depend on any var they reference in the outer scope
        for item, refs in item_refs.items():
            for ref in refs:
                if vars_provided_by.get(ref):
                    vars_required_by[ref].append(item)

        for var, requirers in vars_required_by.items():
            providers = vars_provided_by.get(var, [])
            for r in requirers:
                for provider in providers:
                    graph[provider].append(r)
                    in_degree[r] += 1

        # _graph_debug(actions, in_degree, vars_provided_by)

        return graph, in_degree

    #--------------------------------------------------
    # Stratify
    #--------------------------------------------------

    @staticmethod
    def stratify(actions:List[Action]):
        graph, in_degree = Utils.action_graph(actions)
        strata = []
        current_stratum = []
        handled = set()

        while True:
            no_dependencies = [item for item in actions if item not in handled and in_degree[item] == 0]

            if not no_dependencies:
                break

            current_stratum.extend(no_dependencies)
            for item in no_dependencies:
                handled.add(item)
                for dependent in graph[item]:
                    in_degree[dependent] -= 1

                del graph[item]
                del in_degree[item]

            strata.append(current_stratum)
            current_stratum = []

        if graph:
            # for item in graph:
            #     rich.print(f"[red bold]Unresolved dependency[/red bold]: {str(item)}")
            raise ValueError("There is a cycle in the graph!")

        return strata

    #--------------------------------------------------
    # Toposort
    #--------------------------------------------------

    @staticmethod
    def sort(actions:List[Action]):
        strata = Utils.stratify(actions)
        sorted = []
        for stratum in strata:
            stratum.sort(key=lambda x: x.id)
            for item in stratum:
                sorted.append(item)
        return sorted

    #--------------------------------------------------
    # Vars
    #--------------------------------------------------

    @staticmethod
    def gather_vars(task_items:List[Action], with_values=False) -> List[Var]:
        vars_seen = set()
        vars = []
        for item in task_items:
            item_vars = [item.entity, *item.bindings.values()]
            for v in item_vars:
                if isinstance(v.value, list):
                    for var in v.value:
                        if isinstance(var, Var) and (with_values or var.value is None):
                            if var not in vars_seen:
                                vars_seen.add(var)
                                vars.append(var)
                else:
                    if with_values or v.value is None:
                        if v not in vars_seen:
                            vars_seen.add(v)
                            vars.append(v)
        return vars

    @staticmethod
    def gather_task_vars(task:Task, with_values=False, only_direct_children=False, seen=None) -> Set[Var]:
        if seen is None:
            seen = set()
        if task in seen:
            return set()
        seen.add(task)

        refs = set()
        for i in task.items:
            vs = i.vars()
            for v in vs:
                if i.action == ActionType.Call and not only_direct_children and v.value and isinstance(v.value, Task):
                    refs.update(Utils.gather_task_vars(v.value, with_values, only_direct_children, seen))
                elif with_values or (v.value is None and not v.isa(Builtins.InlineRawData)):
                    refs.add(v)
        return refs
