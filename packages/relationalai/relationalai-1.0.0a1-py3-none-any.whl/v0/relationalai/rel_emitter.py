from __future__ import annotations
import json
from typing import Any, List, Set, cast
from datetime import datetime, date
import pandas as pd
from zoneinfo import ZoneInfo

from v0.relationalai.errors import RAIException
from v0.relationalai.rel_utils import RESERVED_WORDS, sanitize_identifier

from .metamodel import Builtins, Action, ActionType, Namer, Property, Type, Var, Task, Value
from . import metamodel as m
from . import compiler as c
import re

gather_vars = m.Utils.gather_vars

#--------------------------------------------------
# Emitter
#--------------------------------------------------

rel_infix = [">", "<", ">=", "<=", "=", "!=", "+", "-", "*", "/", "^", "~="]
rel_sanitize_re = re.compile(r'[^\w:\[\]\^" ,]|^(?=\d)', re.UNICODE)
unsafe_symbol_pattern = re.compile(r"[^a-zA-Z0-9_]", re.UNICODE)

def sanitize(input_string, is_rel_name_or_symbol = False):
    # Replace non-alphanumeric characters with underscores
    if is_rel_name_or_symbol and "[" in input_string:
        string_parts = input_string.split('[', 1)
        sanitized_name_or_symbol = sanitize_identifier(string_parts[0])
        sanitized_rest = re.sub(rel_sanitize_re, "_", string_parts[1])
        sanitized = f"{sanitized_name_or_symbol}[{sanitized_rest}"
    else:
        if "::" in input_string: # TODO: This is a temp solution to avoid sanitizing the namespace
            sanitized = re.sub(rel_sanitize_re, "_", input_string)
        else:
            sanitized = sanitize_identifier(input_string)

    # Check if the resulting string is a keyword and append an underscore if it is
    if sanitized in RESERVED_WORDS:
        sanitized += "_"

    return sanitized

class Emitter(c.Emitter):

    def __init__(self, config):
        super().__init__()
        self.namer = Namer()
        self.stack:List[Set[Var]] = []
        self.mapped = {}
        self.config = config

    def reset(self):
        self.namer.reset()
        self.stack = []
        self.mapped = {}

    #--------------------------------------------------
    # Emit
    #--------------------------------------------------

    def emit(self, task: Task|Var):
        self.mapped.clear()
        code = ""
        try:
            if isinstance(task, Task):
                code = getattr(self, task.behavior.value)(task)
            elif isinstance(task, Var):
                code = self.emit_var(task)
        except Exception as e:
            # print("EMIT FAILED:", e)
            raise e
        return code

    #--------------------------------------------------
    # Helpers
    #--------------------------------------------------

    def sanitize(self, input_string, is_rel_name = False):
        return sanitize(input_string, is_rel_name)

    #--------------------------------------------------
    # Vars
    #--------------------------------------------------

    def emit_val(self, value: Value, var:Var|None=None):
        if value is True:
            return 'boolean_true'
        if value is False:
            return 'boolean_false'
        if isinstance(value, list):
            return f"{', '.join([self.emit_var(v) for v in value])}"
        if isinstance(value, Task) and (value.items or not value.name):
            return self.to_inline_relation(value)
        if isinstance(value, Task) and value.name:
            return f"{{{value.name}}}"
        if isinstance(value, bytes):
            if var and var.type.isa(Builtins.ValueType):
                return f"^{self.sanitize(var.name).capitalize()}Type[0x{value.hex()}]"
            return f"0x{value.hex()}"
        if isinstance(value, Property):
            return "{" + self.sanitize(value.name) + "}"
        if isinstance(value, Type):
            return "{" + self.sanitize(value.name, value.isa(Builtins.Relation)) + "}"
        if isinstance(value, pd.Timestamp):
            t = value.tz_localize('UTC')
            return t.isoformat()
        if isinstance(value, datetime):
            t = value.astimezone(ZoneInfo('UTC'))
            return t.isoformat(timespec='milliseconds')
        if isinstance(value, date):
            t = value
            return t.isoformat()
        if isinstance(value, str):
            # % is the string interpolation character in rel
            return json.dumps(value).replace("%", "\\%")
        return json.dumps(value)

    def emit_var(self, var: Var|Value):
        if not isinstance(var, Var):
            return self.emit_val(var)
        if var in self.mapped:
            return self.mapped[var]
        if var.type.isa(Builtins.Symbol):
            if unsafe_symbol_pattern.search(cast(str, var.value)):
                return f":\"{var.value}\""
            return f":{self.sanitize(var.value)}"
        if var.value is not None:
            return self.emit_val(var.value, var)
        if var.name == "_":
            return "_"
        name = self.namer.get(var)
        return f"_{self.sanitize(name)}"

    def to_name(self, value: Value|Var|None) -> str:
        if value is not None and hasattr(value, "name"):
            name = getattr(value, "name") # @NOTE: Working around pyright
            if name:
                return name

        raise RAIException(f"Unable to determine the appropriate name for value of type: {type(value)} ({value})")

    #--------------------------------------------------
    # Sequence
    #--------------------------------------------------

    def sequence_action(self, action: Action):
        if action.entity.value == Builtins.RawCode:
            return str([*action.bindings.values()][0].value)
        elif isinstance(action.entity.value, Task):
            return self.emit(action.entity.value)
        else:
            raise Exception(f"TODO: Rel emit for action type {action.action}")

    def sequence(self, task: Task):
        items = [ self.sequence_action(i) for i in task.items ]
        return "\n\n".join(items)

    #--------------------------------------------------
    # Query helpers
    #--------------------------------------------------

    def to_relation(self, action: Action, vars: set, body:List[str], in_head = False):
        root = cast(Type, action.entity.value)
        rel_name = root.name
        if not rel_name and isinstance(root, Task):
            rel_name = f"T{root.id}"
        elif not rel_name:
            rel_name = f"R_{root.id}"
        args = []
        for var in action.bindings.values():
            emitted = self.emit_var(var)
            vars.add(var)
            if in_head and emitted in args:
                name = self.namer.get(var)
                orig = emitted
                emitted = self.sanitize(f"_{self.namer.get_safe_name(name)}")
                body.append(f"{emitted} = {orig}")
            elif in_head and var.value is not None and var.isa(Builtins.ValueType):
                name = self.namer.get(var)
                emitted = self.sanitize(f"_{self.namer.get_safe_name(name)}")
                body.append(f"{emitted} = {self.emit_val(var.value, var)}")
            elif in_head and isinstance(var.value, bool):
                name = self.namer.get(var)
                orig = emitted
                emitted = self.sanitize(f"_{self.namer.get_safe_name(name)}")
                body.append(f"{emitted} = {orig}")
            args.append(emitted)
        if rel_name in rel_infix:
            if len(args) == 2:
                return f"{args[0]} {rel_name} {args[1]}"
            else:
                return f"{args[2]} = {args[0]} {rel_name} {args[1]}"
        rel_name = self.sanitize(rel_name, True)
        if isinstance(root, Task) and root.isa(Builtins.Quantifier):
            # TODO: handle quantifier grouping
            args = args[1:]
            rel_name = root.name.lower()
            if root.isa(Builtins.Exists):
                rel_name = "not empty"
        if action.action == ActionType.Persist:
            rel_name = f"insert[:{rel_name}]"
        elif action.action == ActionType.Unpersist:
            rel_name = f"delete[:{rel_name}]"
        partial_appl = rel_name.find('[')
        if partial_appl >= 0:
            final_rel_name = rel_name[:partial_appl]
            if len(args):
                final_args = f"{rel_name[partial_appl+1:-1]}, {', '.join(args)}"
            else:
                final_args = ', '.join(args)
            final = f"{final_rel_name}({final_args})"
        else:
            final = f"{rel_name}({', '.join(args)})"
        return final

    def to_return(self, action: Action, vars: set, body:List[str]):
        args = []
        for var in action.bindings.values():
            emitted = self.emit_var(var)
            vars.add(var)
            if emitted in args:
                name = self.namer.get(var)
                orig = emitted
                emitted = self.sanitize(f"_{self.namer.get_safe_name(name)}")
                body.append(f"{emitted} = {orig}")
            elif var.value is not None and var.isa(Builtins.ValueType):
                name = self.namer.get(var)
                emitted = self.sanitize(f"_{self.namer.get_safe_name(name)}")
                body.append(f"{emitted} = {self.emit_val(var.value, var)}")
            elif isinstance(var.value, bool):
                name = self.namer.get(var)
                orig = emitted
                emitted = self.sanitize(f"_{self.namer.get_safe_name(name)}")
                body.append(f"{emitted} = {orig}")
            args.append(emitted)
        return f"output({', '.join(args)})"

    def to_set(self, action: Action, vars: set):
        vals:Any = [v for v in action.bindings.values()]
        mid_point = len(vals) // 2
        vars_str = ", ".join([self.emit_var(i) for i in vals[mid_point:]])
        rows = []
        for ix in range(len(vals[0].value)):
            row_vals = vals[:mid_point]
            product_str = ",".join([self.emit_var(col.value[ix]) for col in row_vals])
            if len(row_vals) > 1:
                rows.append(f"({product_str})")
            else:
                rows.append(product_str)
        row_str = "; ".join(rows)
        return f"{{{row_str}}}({vars_str})"

    def to_inline_set(self, action: Action, vars: set):
        vals:Any = [v for v in action.bindings.values()]
        rows = []
        for ix in range(len(vals[0].value)):
            row_vals = vals[:-1]
            product_str = ",".join([self.emit_var(col.value[ix]) for col in row_vals])
            if len(row_vals) > 1:
                rows.append(f"({product_str})")
            else:
                rows.append(product_str)
        row_str = "; ".join(rows)
        return (vals[-1], f"{{{row_str}}}")

    def to_inline_relation(self, task:Task, existing_vars=set()):
        return f"{{{self.query(task, True)}}}"

    #--------------------------------------------------
    # Query
    #--------------------------------------------------

    def query(self, task: Task, inline = False):
        supporting_rules = []
        head = ""
        body = []
        body_vars = set()
        head_vars = set()

        task_vars = set(gather_vars(task.items))
        self.stack.append(task_vars)

        for i in task.items:
            if i.action in [ActionType.Get, ActionType.Call]:
                if i.entity.value == Builtins.RawData:
                    body.append(self.to_set(i, body_vars))
                elif i.entity.value == Builtins.InlineRawData:
                    (v, data) = self.to_inline_set(i, body_vars)
                    self.mapped[v] = data
                    head_vars.add(v)
                elif i.entity.value == Builtins.Install:
                    (item,) = i.bindings.values()
                    supporting_rules.append(f"declare {self.sanitize(self.to_name(item.value), True)}")
                    if isinstance(item.value, Type) and item.value.isa(Builtins.ValueType):
                        vtype = self.sanitize(item.value.name, True).capitalize() + "Type"
                        supporting_rules.append(f"value type {vtype} {{ UInt128 }}")
                        supporting_rules.append(f"@inline def pyrel_unwrap(y in {vtype}, x): ^{vtype}(x, y)")
                        supporting_rules.append(f"def ::std::common::uuid_string(x in {vtype}, y): exists((z) | pyrel_unwrap(x, z) and uuid_string(z, y))")
                        for op in ["<", ">"]:
                            supporting_rules.append(f"def ::std::common::({op})[x in {vtype}, y in {vtype}]: exists((a, b) | ^{vtype}(a, x) and ^{vtype}(b, y) and a {op} b)")
                            if self.config.get("compiler.use_monotype_operators", False):
                                supporting_rules.append(f"def ::std::monotype::({op})[x in {vtype}, y in {vtype}]: exists((a, b) | ^{vtype}(a, x) and ^{vtype}(b, y) and a {op} b)")
                        for op in ["minimum", "maximum"]:
                            supporting_rules.append(f"def ::std::common::{op}(x in {vtype}, y in {vtype}, z in {vtype}): exists((a, b) | ^{vtype}(minimum[a, b], z) and ^{vtype}(a, x) and ^{vtype}(b, y))")
                else:
                    body.append(self.to_relation(i, body_vars, body))
            elif i.action == ActionType.Bind and i.entity.value == Builtins.Return:
                head_rel = self.to_return(i, head_vars, body)
                head = f"def {head_rel}:\n    "
            elif i.action in [ActionType.Bind, ActionType.Persist, ActionType.Unpersist]:
                if not inline:
                    head_rel = self.to_relation(i, head_vars, body, True)
                    annotations = set(["from_pyrel"])
                    # If optimized rel is requested, add desired attribute
                    opt = self.config.get(name="describe_optimization", strict=False)
                    if opt == "simple" :
                        annotations.add(Builtins.InspectOptimizedSimple.name.lower())
                    elif opt == "verbose" :
                        annotations.add(Builtins.InspectOptimizedVerbose.name.lower())
                    ent = i.entity.value
                    if isinstance(ent, Type) or isinstance(ent, Property):
                        for parent in ent.parents:
                            if parent.isa(Builtins.Annotation):
                                annotations.add(parent.name.lower())
                    if annotations:
                        annotation_str = " ".join([f"@{a}" for a in annotations])
                        head = f"{annotation_str}\ndef {head_rel}:\n    "
                    else:
                        head = f"def {head_rel}:\n    "
                else:
                    props = list(i.bindings.values())
                    head_vars.update(props)
                    head = f"({', '.join([self.emit_var(v) for v in props])}): "
            elif i.action == ActionType.Construct:
                inputs = [*i.bindings.values()]
                input_str =', '.join([self.emit_var(v) for v in inputs[:-1]])
                output = self.emit_var(inputs[-1])
                body_vars.update(inputs)
                body.append(f"{output} = ^{self.sanitize(self.to_name(i.entity.value)).capitalize()}Type[{input_str}]")
            else:
                raise Exception(f"TODO: Rel emit for action type {i.action}")
        body_str = " and\n    ".join(body)
        existing_vars = set()
        for vars in self.stack[:-1]:
            existing_vars.update(vars)
        from_vars = [self.emit_var(v) for v in (body_vars - head_vars - existing_vars) if v.value is None]
        if len(from_vars) and not inline:
            body_str = f"exists(({', '.join(from_vars)}) |\n    {body_str})"
        if head and len(from_vars) and inline:
            body_str = f"exists(({', '.join(from_vars)}) | {body_str})"


        self.stack.pop()

        if not head and inline:
            return body_str
        elif not head:
            head = f"def T{task.id}():\n    "

        support_str = ""
        if len(supporting_rules):
            support_str = "\n\n".join(supporting_rules) + "\n\n"

        if support_str and not head_vars and not body_str:
            return support_str

        if not body_str:
            body_str = "{()}"


        return f"{support_str}{head}{body_str}"
