from __future__ import annotations
from collections import OrderedDict
import io
import re
import textwrap
import time
from typing import List, Dict, Tuple, Any, Iterable, cast

from relationalai_test_util.snapshot import exec_traced
from .metamodel import Agent, Base, Namer, Task, Var, Value, Property, Action, ActionType, AllItems, Behavior, Builtins, Type
from . import debugging
from .clients.config import Config
import random
import rich
import json

DEBUG = False

#--------------------------------------------------
# SortedSet
#--------------------------------------------------

class SortedSet:
    def __init__(self, elements=None):
        # Using OrderedDict to maintain insertion order and uniqueness
        self._elements = OrderedDict((element, None) for element in elements) if elements is not None else OrderedDict()

    def add(self, element):
        # Add element only if it does not exist, maintaining insertion order
        self._elements[element] = None

    def remove(self, element):
        # Remove element if it exists
        if element in self._elements:
            del self._elements[element]

    def __contains__(self, element):
        # Check if element is in the set
        return element in self._elements

    def __iter__(self):
        # Allow iteration over elements in their insertion order
        return iter(self._elements)

    def __len__(self):
        # Return the number of unique elements
        return len(self._elements)

    def __str__(self):
        # String representation of the sorted set
        return "SortedSet(" + str(list(self._elements.keys())) + ")"

#--------------------------------------------------
# PyRel emitter
#--------------------------------------------------

op_mapping = {
    "=": "==",
    "^": "**"
}

class PyRelEmitter:
    def __init__(self):
        self.namer = Namer()
        self.bound = {}
        self.used = set()
        self.used_types = set()

    def reset(self, full=False):
        self.namer.reset()
        self.bound.clear()
        self.used.clear()
        if full:
            self.used_types.clear()

    #--------------------------------------------------
    # Helpers
    #--------------------------------------------------

    def sanitize(self, input_string):
        # Replace non-alphanumeric characters with underscores
        sanitized = re.sub(r'[^:\w]|^(?=\d)', '_', input_string)

        # Check if the resulting string is a keyword and append an underscore if it is
        if sanitized in ["from", "is", "not", "or", "and", "as", "assert", "break", "class", "continue"]:
            sanitized += '_'

        return sanitized

    #--------------------------------------------------
    # Emit
    #--------------------------------------------------

    def emit(self, item: AllItems) -> str:
        if isinstance(item, Task):
            return self.emit_task(item)
        elif isinstance(item, Type):
            return self.emit_type(item)
        elif isinstance(item, Var):
            return self.emit_var(item)
        elif isinstance(item, Action):
            return self.emit_action(item)
        elif isinstance(item, Property):
            return self.emit_property(item)
        else:
            raise Exception(f"Unknown item type: {type(item)}")

    #--------------------------------------------------
    # Val handling
    #--------------------------------------------------

    def emit_val(self, value: Value) -> str:
        if value is True or value is False:
            return str(value)
        if isinstance(value, list):
            return f"{', '.join([self.emit_var(v) for v in value])}"
        if isinstance(value, bytes):
            return f"0x{value.hex()}"
        if isinstance(value, Property):
            return self.sanitize(value.name)
        if isinstance(value, Type):
            return self.sanitize(value.name)
        return json.dumps(value)

    #--------------------------------------------------
    # Var handling
    #--------------------------------------------------

    def emit_var_name(self, v:Var) -> str:
        name = self.namer.get(v)
        return name.lower()

    def emit_var(self, var: Var|Value) -> str:
        if not isinstance(var, Var):
            return self.emit_val(var)
        if var.value is not None:
            return self.emit_val(var.value)
        if var.name == "_":
            return "_"
        return self.emit_var_name(var)

    #--------------------------------------------------
    # Types and Properties
    #--------------------------------------------------

    def emit_type(self, t:Type) -> str:
        self.used_types.add(t)
        return self.sanitize(t.name)

    def emit_property(self, p:Property) -> str:
        return self.sanitize(p.name)

    #--------------------------------------------------
    # Actions
    #--------------------------------------------------

    def action_params(self, a:Action, extras:List[str]) -> str:
        params = []
        types = a.types
        if len(types):
            if a.action == ActionType.Get:
                types = types[1:]
            if len(types):
                params.append(f"{', '.join([self.emit(t) for t in types])}")
        for k,v in a.bindings.items():
            if v.value is None and v not in self.bound:
                self.bound[v] = self.emit_var(v)
                extras.append(f"{self.emit_var(v)} = {self.emit_var(a.entity)}.{self.emit(k)}")
                continue
            if v in self.bound:
                v = self.bound[v]
            else:
                v = self.emit(v)
            params.append(f"{self.emit(k)}={v}")
        return ", ".join(params)

    def emit_action(self, a:Action) -> str:
        if a.action == ActionType.Call:
            return self.emit_call(a)
        else:
            var = self.emit_var_name(a.entity)
            if a.entity not in self.bound:
                self.bound[a.entity] = var
            root = self.emit(a.types[0]) if len(a.types) else var
            extras = []
            params = self.action_params(a, extras)
            line = ""
            if a.action == ActionType.Get:
                line = f"{var} = {root}({params})"
            elif a.action == ActionType.Bind:
                line = f"{var}.set({params})"
            elif a.action == ActionType.Persist:
                line = f"{var}.persist({params})"
            elif a.action == ActionType.Unpersist:
                line = f"{var}.unpersist({params})"
            if not len(extras):
                return line
            extras_str = '\n'.join(extras)
            return f"{line}\n{extras_str}"

    #--------------------------------------------------
    # Action: Call
    #--------------------------------------------------

    def emit_call(self, a:Action) -> str:
        if a.entity.isa(Builtins.Infix):
            name = cast(Type, a.entity.value).name
            name = op_mapping.get(name, name)
            args = [self.emit(v) for v in a.bindings.values()]
            if len(args) == 2:
                return f"{args[0]} {name} {args[1]}"
            else:
                return f"{args[2]} = {args[0]} {name} {args[1]}"
        raise Exception(f"Unsupported call type: {a.entity}")

    #--------------------------------------------------
    # Tasks
    #--------------------------------------------------

    def emit_task_items(self, task:Task) -> str:
        items = [self.emit(i) for i in task.items]
        if not len(items):
            items.append("pass")
        return textwrap.indent("\n".join(items), "    ")

    def emit_task(self, task:Task) -> str:
        if task.behavior == Behavior.Query:
            head = "with model.query() as select:"
            return f"{head}\n{self.emit_task_items(task)}"
        return "TASK"

    #--------------------------------------------------
    # Documents
    #--------------------------------------------------

    def emit_header(self) -> str:
        types = []
        for t in self.used_types:
            t_name = self.emit(t)
            types.append(f"{t_name} = model.Type(\"{t_name}\")")
        lines = [
            "import relationalai as rai",
            "",
            "model = rai.Model(\"gentest\", config=config)",
            "",
            *types
        ]
        return "\n".join(lines)

    def emit_doc(self, tasks:List[Task]) -> str:
        task_code = []
        for t in tasks:
            self.reset()
            task_code.append(self.emit(t))
        body = "\n\n".join(task_code)
        return f"{self.emit_header()}\n\n{body}"

#--------------------------------------------------
# GenStats
#--------------------------------------------------

class GenStats:
    def __init__(self, debug=DEBUG):
        self.start = time.perf_counter()
        self.runs = 0
        self.failures = []
        self.debugs = []
        self.gen_time = 0.0
        self.emit_time = 0.0
        self.exec_time = 0.0
        self._debugging = debug

    def success(self):
        self.runs += 1

    def fail(self, seed, expected, actual, mismatches, code, exception=None):
        self.runs += 1
        self.failures.append((seed, expected, actual, mismatches, code, exception))

    def debug(self, seed, expected, actual, code):
        if self._debugging:
            self.debugs.append((seed, expected, actual, code))

    def finish(self):
        self.elapsed = time.perf_counter() - self.start
        return self

    def __rich__(self) -> str:
        failures = len(self.failures)
        results_str = f"[red bold]{failures:,.0f}[/red bold]  [green bold]{self.runs-failures:,.0f}[/green bold]"
        def millis(s, color="white"):
            return f"[{color} bold]{s * 1000:,.0f}[/{color} bold][{color}]ms[/{color}]"
        summary = f"{results_str}  {millis(self.elapsed, 'yellow')}  [dim]|  {millis(self.gen_time)} gen  {millis(self.emit_time)} emit  {millis(self.exec_time)} exec[/dim]"
        return summary

    def print_failures(self, count=None):
        if count is None:
            count = len(self.failures)
        for seed, expected, actual, mismatches, code, exception in self.failures[0:count]:
            rich.print("[red bold]---------------------------------------------------------------")
            rich.print(f"[red bold]SEED: {seed}")
            if exception:
                print("")
                print(exception)
                rich.print("[dim]---------------------------------------------------------------")
            if len(mismatches):
                for mismatch in mismatches:
                    rich.print(f"[red bold]{mismatch[0]}")
                    rich.print(f"[red bold]{mismatch[1]}")
                rich.print("")
                rich.print("[dim]---------------------------------------------------------------")
            print("")
            print(expected)
            print("")
            rich.print("[dim]---------------------------------------------------------------")
            print("")
            print(actual)
            print("")
            rich.print("[dim]---------------------------------------------------------------")
            print("")
            rich.print(code)
            print("")

    def print_debugs(self):
        for seed, expected, actual, code in self.debugs:
            rich.print("[green bold]---------------------------------------------------------------")
            rich.print(f"[green bold]SEED: {seed}")
            print("")
            print(expected)
            rich.print("[dim]---------------------------")
            print("")
            print(code)
            print("")

#--------------------------------------------------
# GenProfile
#--------------------------------------------------

class GenProfile:
    def __init__(self):

        self.identifier_len = (3, 6)
        self.string_len = (3, 5)
        self.number_range = (0, 1000000)

        self.types = (1, 20)
        self.type_properties = (0, 10)

        self.task_actions = (1, 10)

        self.get_weight = 1
        self.get_types = (0, 4)
        self.get_properties = (0, 4)

        self.bind_weight = 1
        self.bind_types = (0, 4)
        self.bind_properties = (0, 4)

        self.call_weight = 1
        self.aggregate_weight = 1

        self.quantifier_weight = 0.2
        self.sub_task_weight = 0.2

#--------------------------------------------------
# Gen
#--------------------------------------------------

class Gen:
    def __init__(self, seed, profile:GenProfile = GenProfile()):
        self.seed = seed
        self.random = random.Random(seed)
        self.eq = Eq()
        self.emitter = PyRelEmitter()
        self.profile = profile
        self.config = Config()

        self.types = []
        for _ in range(self.rand_range(self.profile.types)):
            self.types.append(self.type())
        for t in self.types:
            t.properties = [self.property() for _ in range(self.rand_range(self.profile.type_properties))]

    #--------------------------------------------------
    # Helpers
    #--------------------------------------------------

    def rand_range(self, r):
        return self.random.randint(r[0], r[1])

    def choice(self, enum):
        return self.random.choice(list(enum))

    def choices(self, enum, k):
        options = list(enum)
        return self.random.sample(enum, k=min(k, len(options)))

    #--------------------------------------------------
    # Primitives
    #--------------------------------------------------

    def string(self, prefix="", length=None):
        length = length or self.rand_range(self.profile.string_len)
        return self.emitter.sanitize(prefix + ''.join(self.random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(length)))

    def identifier(self, length=None):
        length = length or self.rand_range(self.profile.identifier_len)
        return self.string("", length)

    def number(self):
        return self.random.randint(0, 1000000)

    def value(self, allowed_types=None) -> Value:
        if not allowed_types:
            allowed_types = [self.number, self.string]
        v = self.random.choice(allowed_types)
        return cast(Value, v())

    #--------------------------------------------------
    # Types and Properties
    #--------------------------------------------------

    def type(self) -> Type:
        name = self.identifier().capitalize()
        properties = []  # [self.generate_random_property() for _ in range(self.random.randint(1, 3))]
        parents = []  # Could recursively add random Types if necessary, but keeping it simple here
        return Type(name=name, properties=properties, parents=parents)

    def property(self) -> Property:
        name = self.identifier()
        type = self.choice(self.types)
        is_input = False
        return Property(name=name, type=type, is_input=is_input)

    def _choose_prop(self, types:List[Type]) -> Property|None:
        type = self.random.choice(types)
        if len(type.properties):
            return self.random.choice(type.properties)

    def prop_value(self, vars:SortedSet, allow_self=True, allowed_types=None) -> Var:
        i = self.random.randint(1, 10)
        if i < 5 and len(vars):
            return self.choice(vars)
        if i < 8 and allow_self:
            return self.var()
        return Var(value=self.value(allowed_types=allowed_types))

    #--------------------------------------------------
    # Var
    #--------------------------------------------------

    def var(self) -> Var:
        # type = self.choice(self.types)
        type = Builtins.Any
        name = None # self.string("Var_") if self.random.choice([True, False]) else None
        value = None  # Could implement logic to generate random Value based on Type
        return Var(type=type, name=name, value=value)

    #--------------------------------------------------
    # Actions: Get
    #--------------------------------------------------

    def action_get(self, vars:SortedSet, sets: Dict[Tuple[Var, Property], Var]) -> Action:
        entity = self.var()
        types = self.choices(self.types, self.rand_range(self.profile.get_types))
        if len(types):
            entity.type = types[0]
        props = SortedSet()
        all_opts = [entity.type, *types]
        for _ in range(self.rand_range(self.profile.get_properties)):
            prop = self._choose_prop(all_opts)
            if prop:
                props.add(prop)
        bindings = {prop: self.prop_value(vars) for prop in props}
        # We can ref our own vars, so we add them to the pool after the fact
        if len(props) or len(types):
            vars.add(entity)
        for k, v in bindings.items():
            if v.value is None:
                vars.add(v)
        return Action(action=ActionType.Get, entity=entity, types=types, bindings=bindings)

    #--------------------------------------------------
    # Actions: Bind
    #--------------------------------------------------

    def bind_var(self, vars:SortedSet) -> Var:
        available = [v for v in vars if v.type in self.types]
        if len(available):
            return self.choice(available)
        return self.var()

    def action_bind(self, vars:SortedSet, sets: Dict[Tuple[Var, Property], Var]) -> Action:
        entity = self.bind_var(vars)
        types = self.choices(self.types, self.rand_range(self.profile.bind_types))
        if len(types):
            entity.type = types[0]
        props = SortedSet()
        all_opts = [entity.type, *types]
        for _ in range(self.rand_range(self.profile.bind_properties)):
            prop = self._choose_prop(all_opts)
            if prop:
                props.add(prop)
        bindings = {prop: self.prop_value(vars, False) for prop in props}
        for k, v in bindings.items():
            sets[(entity, k)] = v

        # We can ref our own vars, so we add them to the pool after the fact
        return Action(action=ActionType.Bind, entity=entity, types=types, bindings=bindings)

    #--------------------------------------------------
    # Actions: Call
    #--------------------------------------------------

    def action_call(self, vars:SortedSet, sets: Dict[Tuple[Var, Property], Var]) -> Action:
        assert len(vars)

        op:Type = self.choice([
            Builtins.gt,
            Builtins.gte,
            Builtins.lt,
            Builtins.lte,
            Builtins.eq,
            Builtins.neq,
            Builtins.plus,
            Builtins.minus,
            Builtins.mult,
            Builtins.div,
            Builtins.pow
        ])
        bindings = {}
        last_input = None
        has_non_value = False
        for prop in op.properties:
            if prop.is_input:
                bindings[prop] = self.prop_value(vars, False, allowed_types=[self.number])
                if bindings[prop].value is None:
                    has_non_value = True
                last_input = prop
            else:
                bindings[prop] = self.var()
        if not has_non_value and last_input:
            bindings[last_input] = [v for v in vars if v.value is None][0]

        return Action(action=ActionType.Call, entity=Var(value=op), bindings=bindings)

    #--------------------------------------------------
    # Task
    #--------------------------------------------------

    def task(self) -> Task:
        behavior = self.choice([Behavior.Query])
        items = []
        vars = SortedSet()
        sets = {}
        for ix in range(self.rand_range(self.profile.task_actions)):
            if ix <= 1 or not len(vars):
                items.append(self.action_get(vars, sets))
            else:
                items.append(self.random.choice([
                    self.action_get,
                    self.action_bind,
                    self.action_call
                ])(vars, sets))
        return Task(behavior=behavior, items=items)

    #--------------------------------------------------
    # Tests
    #--------------------------------------------------

    def test_task(self, seed, stats:GenStats):
        gen_start = time.perf_counter()
        self.random.seed(seed)
        self.emitter.reset(True)
        self.eq.reset()

        expected = self.task()
        expected.normalize()
        stats.gen_time += time.perf_counter() - gen_start

        if not len(expected.items):
            stats.success()
            return

        emit_start = time.perf_counter()
        code = self.emitter.emit_doc([expected])
        stats.emit_time += time.perf_counter() - emit_start
        actual = None
        exception = None

        try:
            exec_time = time.perf_counter()
            result_blocks = exec_traced(code, {"config": self.config})
            if len(result_blocks):
                # When use_value_types is active, the first task is installing all the types
                if self.config.get("compiler.use_value_types", None):
                    actual = result_blocks[1]["task"]
                else:
                    actual = result_blocks[0]["task"]
                actual.normalize()
            stats.exec_time += time.perf_counter() - exec_time

        except Exception:
            output = io.StringIO()
            console = rich.console.Console(file=output, force_terminal=True)
            console.print_exception(extra_lines=0)
            exception = output.getvalue()

        stats.debug(seed, expected, actual, code)

        if not self.eq.eq(expected, actual):
            stats.fail(seed, expected, actual, self.eq.mismatches[:], code, exception)
        else:
            stats.success()

#--------------------------------------------------
# Eq
#--------------------------------------------------

OP_INVERSES = { ">": "<", ">=": "<=", "<": ">", "<=": ">=" }
OP_COMMUTATIVE = { "+", "*", "=", "!=" }

class Eq():
    def __init__(self):
        self.mapping = {}
        self.mismatches = []

    def reset(self):
        self.mapping.clear()
        self.mismatches.clear()

    #--------------------------------------------------
    # eq
    #--------------------------------------------------

    def eq(self, a:AllItems|Base|Value|None, b:AllItems|Base|Value|None):
        if type(a) is not type(b):
            return False
        if isinstance(a, Task) and isinstance(b, Task):
            return self.task(a, b)
        if isinstance(a, Type) and isinstance(b, Type):
            return self.type(a, b)
        if isinstance(a, Property) and isinstance(b, Property):
            return self.property(a, b)
        if isinstance(a, Agent) and isinstance(b, Agent):
            return self.agent(a, b)
        if isinstance(a, Var) and isinstance(b, Var):
            return self.var(a, b)
        if isinstance(a, Action) and isinstance(b, Action):
            return self.action(a, b)
        if isinstance(a, dict) and isinstance(b, dict):
            return self.eq_dict(a, b)
        if isinstance(a, list) and isinstance(b, list):
            return self.eq_list(a, b)

        return a == b

    #--------------------------------------------------
    # Collection eq
    #--------------------------------------------------

    def eq_dict(self, a:Dict[str,Any], b:Dict[str,Any]):
        b_str_ks = {str(k): v for k,v in b.items()}
        a_str_ks = {str(k): v for k,v in a.items()}
        for k,v in a.items():
            if not self.eq(v, b_str_ks.get(str(k))):
                return False
        for k in b_str_ks.keys():
            if k not in a_str_ks:
                return False
        return True

    def eq_list(self, a:List[Any], b:List[Any]):
        for i in range(len(a)):
            if not self.eq(a[i], b[i]):
                return False
        for extra in b[len(a):]:
            return False
        return True

    def eq_attrs(self, a:AllItems, b:AllItems, attrs:List[str]):
        for attr in attrs:
            if not self.eq(getattr(a, attr), getattr(b, attr)):
                return False
        return True

    def eq_set(self, a:Iterable[Any], b:Iterable[Any]):
        for item in a:
            found = False
            for b_item in b:
                if self.eq(item, b_item):
                    found = True
                    break
            if not found:
                return False
        return True

    #--------------------------------------------------
    # Metamodel eq
    #--------------------------------------------------

    def type(self, a:Type, b:Type):
        return self.eq_attrs(a, b, ['name'])

    def property(self, a:Property, b:Property):
        # return self.eq_attrs(a, b, ['name', 'type', 'is_input'])
        return self.eq_attrs(a, b, ['name'])

    def task(self, task:Task, b:Task):
        return self.eq_attrs(task, b, ["name", "parents", "behavior", "items"])
        # return self.eq_attrs(task, b, ["name", "bindings", "properties", "parents", "inline", "behavior", "items"])

    def agent(self, a:Agent, b:Agent):
        return self.eq_attrs(a, b, ['name', 'platform', 'info'])

    def var(self, a:Var, b:Var):
        if self.mapping.get(a):
            return self.mapping[a] is b
        elif self.eq_attrs(a, b, ['value']):
            self.mapping[a] = b
            return True
        return False

    def action(self, a:Action, b:Action):
        eq = self.eq_attrs(a, b, ['action', 'entity', 'bindings', 'types'])
        if a.action == b.action and a.action == ActionType.Call and a.entity.isa(Builtins.Infix):
            expected_name = cast(Type, a.entity.value).name
            actual_name = cast(Type, b.entity.value).name
            if expected_name in OP_COMMUTATIVE or OP_INVERSES.get(expected_name) == actual_name:
                eq = self.eq_set(a.bindings, b.bindings)
        if not eq:
            self.mismatches.append((a, b))
        return eq

#--------------------------------------------------
# Runner
#--------------------------------------------------

def batch(size, ix = 0):
    debugging.DEBUG = False
    gen = Gen(1)
    stats = GenStats()

    for x in range(size):
        gen.test_task(x + ix, stats)

    if DEBUG:
        stats.print_failures()
        stats.print_debugs()

    return stats.finish()

def check_seed(seed):
    return batch(1, seed)

def batches(total=10000, num_processes = None):
    import multiprocessing
    multiprocessing.freeze_support()

    num_processes = num_processes or multiprocessing.cpu_count()  # Or any desired number
    size = total // num_processes

    start = time.perf_counter()
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(batch, [(size, i * size) for i in range(num_processes)])

    return (time.perf_counter() - start, results)
