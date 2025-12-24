from typing import cast
from ..metamodel import Action, Builtins, Task, ActionType, Behavior, Var
import json
import rich

#--------------------------------------------------
# Mehcanism
#--------------------------------------------------

class Mechanism():
    def __init__(self, task:Task) -> None:
        self.stack = []
        self.sequence()
        self.task = task
        self.interpret(task)

    #--------------------------------------------------
    # IDs
    #--------------------------------------------------

    current_id = 0

    @staticmethod
    def get_next_id():
        Mechanism.current_id += 1
        return Mechanism.current_id

    #--------------------------------------------------
    # Containers
    #--------------------------------------------------

    def sequence(self):
        self.stack.append({"id": self.get_next_id(), "type": "sequence", "items": []})

    def union(self, result):
        self.stack.append({"id": self.get_next_id(), "type": "union", "items": [], "result": self._var(result)})

    def choice(self):
        self.stack.append({"id": self.get_next_id(), "type": "choice", "items": []})

    def pop(self):
        cur = self.stack.pop()
        self.stack[-1]["items"].append(cur)

    #--------------------------------------------------
    # Actions
    #--------------------------------------------------

    def _append(self, item):
        self.stack[-1]["items"].append(item)

    def _var(self, var:Var):
        if var.value is not None:
            return str(var)
        else:
            return {"id": var.id, "name": var.name}

    def get(self, entity, types, props):
        props = {key: self._var(value) for key, value in props.items()}
        self._append({"id": self.get_next_id(), "type": "get", "entity": self._var(entity), "types": types, "props": props})

    def filter(self, op, args):
        self._append({"id": self.get_next_id(), "type": "filter", "op":op, "args": [self._var(arg) for arg in args]})

    def compute(self, op, args, ret):
        self._append({"id": self.get_next_id(), "type": "compute", "op":op, "args": [self._var(arg) for arg in args], "ret": self._var(ret)})

    def effect(self, op, entity, types, props):
        props = {key: self._var(value) for key, value in props.items()}
        self._append({"id": self.get_next_id(), "type": "effect", "op": op, "entity": self._var(entity), "types": types, "props": props})

    def return_(self, vars):
        self._append({"id": self.get_next_id(), "type": "return", "values":[self._var(v) for v in vars]})

    def install(self, item):
        self._append({"id": self.get_next_id(), "type": "install", "item":self._var(item)})

    def aggregate(self, op, args, group, ret):
        self._append({"id": self.get_next_id(), "type": "aggregate", "op":op, "args": [self._var(arg) for arg in args], "group": [self._var(g) for g in group], "ret": self._var(ret)})

    def quantify(self, quantifier, group):
        self._append({"id": self.get_next_id(), "type": "quantify", "quantifier": quantifier, "group": [self._var(g) for g in group]})

    def to_dict(self):
        return self.stack[-1]

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def debug(self, item = None, indent = 0):
        pad = "    " * indent
        if not item:
            item = self.stack[-1]

        def var(v):
            if isinstance(v, dict):
                return f"<{v['name']} ({v['id']})>"
            return v

        if "items" in item:
            res = f" -> {var(item['result'])}" if "result" in item else ""
            rich.print(f"{pad}{item['type']}{res}")
            for child in item['items']:
                if item is not None:
                    self.debug(child, indent + 1)

        elif item['type'] == "get" or item['type'] == "effect":
            rich.print(f"{pad}{item['type']} {var(item['entity'])} {item['types']} {{{', '.join(f'{k}={var(v)}' for k, v in item['props'].items())}}}")
        elif item['type'] == "filter":
            rich.print(f"{pad}{item['type']} {item['op']} [{', '.join(var(v) for v in item['args'])}]")
        elif item['type'] == "compute":
            rich.print(f"{pad}{item['type']} {item['op']} [{', '.join(var(v) for v in item['args'])}] -> {var(item['ret'])}")
        elif item['type'] == "return":
            rich.print(f"{pad}{item['type']} [{', '.join(var(v) for v in item['values'])}]")
        elif item['type'] == "aggregate":
            rich.print(f"{pad}{item['type']} {item['op']} [{', '.join(var(v) for v in item['args'])}] per [{', '.join(var(v) for v in item['group'])}] -> {item['ret']}")
        elif item['type'] == "quantify":
            rich.print(f"{pad}{item['type']} {item['quantifier']} per [{', '.join(var(v) for v in item['group'])}]")
        else:
            rich.print(f"{pad}{item['type']} ???")

    #--------------------------------------------------
    # Interpret
    #--------------------------------------------------

    def find_min(self, item:Action):
        if item.is_subtask_call():
            return min(getattr(item.entity.value, "id", item.id), *[self.find_min(subtask) for subtask in cast(Task, item.entity.value).items])
        elif item.entity.isa(Builtins.Quantifier):
            return cast(Task, [*item.bindings.values()][1].value).id
        return item.id

    def interpret(self, task):
        # hack to get around the way stratification currently works, in our mechanistic
        # diagram we want to see the effects last in queries. This will change once we
        # have order dependence in the v2 compiler
        items = task.items[:]
        # Subtask calls get added during the dsl stack collapse and so end up with a much
        # later id. Their "place" in the original query is determined by the id of the
        # subtask rather than the call
        items.sort(key=self.find_min)
        for item in items:
            if item.action == ActionType.Get:
                for type_ in item.types:
                    self.get(item.entity, [type_.name], {})
                for key, value in item.bindings.items():
                    self.get(item.entity, [], {key.name: value})
            elif item.action == ActionType.Call:
                func = item.entity
                params = list(item.bindings.values())
                if item.is_subtask_call():
                    sub_task = func.value
                    if sub_task.behavior == Behavior.Query or sub_task.behavior == Behavior.Sequence:
                        self.sequence()
                        self.interpret(sub_task)
                        self.pop()
                    elif sub_task.behavior == Behavior.Union:
                        params = list(item.bindings.values())
                        if params:
                            self.union(params[0])
                            self.interpret(sub_task)
                            self.pop()

                    elif sub_task.behavior == Behavior.OrderedChoice:
                        # print("CHOICE")
                        pass
                    else:
                        raise Exception(f"UNKNOWN SUB TASK {sub_task.behavior}")
                elif func.isa(Builtins.Install):
                    self.install(params[0])
                elif func.isa(Builtins.Quantifier):
                    self.sequence()
                    self.interpret(params[1].value)
                    if func.isa(Builtins.Not):
                        quantifier = "not"
                    elif func.isa(Builtins.Exists):
                        quantifier = "exists"
                    elif func.isa(Builtins.Every):
                        quantifier = "every"
                    else:
                        raise Exception()
                    self.quantify(quantifier, params[0].value)
                    self.pop()

                elif func.isa(Builtins.Aggregate):
                    # print("Aggregate")
                    pass
                elif func.isa(Builtins.Infix) and len(params) == 2:
                    self.filter(func.value.name, params)
                else:
                    self.compute(func.value.name, params[:-1], params[-1])
            elif item.action == ActionType.Bind and item.entity.isa(Builtins.Return):
                self.return_(item.bindings.values())
            elif item.action.is_effect():
                op = item.action.name
                props = {key.name: value for key,value in item.bindings.items()}
                self.effect(op, item.entity, [type.name for type in item.types], props)
            else:
                # print("hey!", item)
                pass
