from __future__ import annotations
from typing import List, TypeVar, cast
from .metamodel import Behavior, Type, Property, Task, Var, Action, Agent, next_id, AllItems
import copy
from . import debugging
import time


#--------------------------------------------------
# Compiler Pass
#--------------------------------------------------

T = TypeVar('T', bound='AllItems')

class Pass:
    backlinks = {}
    forwardlinks = {}

    def __init__(self, copying = True) -> None:
        self.seen = set()
        self.copying = copying

    def clone(self, item:T) -> T:
        copied = copy.copy(item)
        copied.id = next_id()
        Pass.backlinks[copied] = item
        Pass.forwardlinks[item] = copied
        return copied

    def walk(self, item: T, parent=None) -> T:
        orig = item
        if not item or item in self.seen:
            return Pass.forwardlinks.get(item, item)
        if self.copying and not Pass.backlinks.get(item) and not isinstance(item, Var) and (isinstance(item, Task) or not isinstance(item, Type)):
            item = self.clone(item)
        elif self.copying and isinstance(item, Var) and isinstance(item.value, Task) and len(item.value.items):
            item = self.clone(item)
        self.seen.update([item, orig])

        if isinstance(item, Task):
            self.task(cast(Task, item), parent)
        elif isinstance(item, Type):
            self.type(item, parent)
        elif isinstance(item, Property):
            self.property(item, parent)
        elif isinstance(item, Agent):
            self.agent(item, parent)
        elif isinstance(item, Var):
            self.var(item, parent)
        elif isinstance(item, Action):
            self.action(item, parent)

        return item

    def walk_all(self, items, parent=None):
        if self.copying:
            return [self.walk(item, parent) for item in items]
        else:
            for item in items:
                self.walk(item, parent)
            return items

    def reset(self):
        self.seen.clear()

    def type(self, type: Type, parent=None):
        type.properties = self.walk_all(type.properties, type)

    def property(self, property: Property, parent=None):
        property.type = self.walk(property.type)

    def task(self, task: Task, parent=None):
        # task.properties = self.walk_all(task.properties, task)
        if task.agent:
            task.agent = self.walk(task.agent)
        if task.behavior == Behavior.Sequence:
            self.sequence(task, parent)
        elif task.behavior == Behavior.Query:
            self.query(task, parent)
        elif task.behavior == Behavior.Union:
            self.union(task, parent)
        elif task.behavior == Behavior.OrderedChoice:
            self.ordered_choice(task, parent)
        elif task.behavior == Behavior.Catch:
            self.catch(task, parent)

    def sequence(self, seq: Task, parent=None):
        seq.items = self.walk_all(seq.items, seq)

    def query(self, query: Task, parent=None):
        query.items = self.walk_all(query.items, query)

    def union(self, union: Task, parent=None):
        union.items = self.walk_all(union.items, union)

    def ordered_choice(self, ordered_choice: Task, parent=None):
        ordered_choice.items = self.walk_all(ordered_choice.items, ordered_choice)

    def catch(self, catch: Task, parent=None):
        catch.items = self.walk_all(catch.items, catch)

    def agent(self, agent: Agent, parent=None):
        pass

    def var(self, var: Var, parent=None):
        var.type = self.walk(var.type, parent)
        if (isinstance(var.value, Type) or isinstance(var.value, Property)) \
            and (not isinstance(var.value, Task) or len(var.value.items)):
            var.value = self.walk(var.value, parent)

    def action(self, action: Action, parent=None):
        action.entity = self.walk(action.entity, parent)
        action.types = self.walk_all(action.types, parent)
        action.bindings = {k: self.walk(v, parent) for k, v in action.bindings.items()}

#--------------------------------------------------
# Emitter
#--------------------------------------------------

class Emitter:
    def reset(self):
        pass

    def emit(self, task: Task|Var) -> str:
        return ""

#--------------------------------------------------
# Compilation
#--------------------------------------------------

class Compilation:
    def __init__(self, task:Task, debug=debugging.DEBUG):
        self.task = task
        self.passes = []
        self.emitted = ""
        self.emit_time = 0.0
        self.debug = debug

    def pass_result(self, pass_:Pass, rewritten_task:Task, elapsed:float):
        if self.debug:
            self.passes.append((pass_.__class__.__name__, str(rewritten_task), elapsed))

    def get_source(self):
        pyrel_info = debugging.get_source(self.task)
        if not pyrel_info:
            sources = []
            for i in self.task.items:
                source = debugging.get_source(i)
                if source:
                    if not pyrel_info:
                        pyrel_info = source
                    if source.source not in sources:
                        sources.append(source.source)
            pyrel_block = "\n".join(sources)
        else:
            pyrel_block = pyrel_info.source
        if not pyrel_info:
            pyrel_info = debugging.SourceInfo()
        return (pyrel_info.file, pyrel_info.line, pyrel_block)

#--------------------------------------------------
# Compiler
#--------------------------------------------------

class Compiler:
    def __init__(self, emitter:Emitter, passes:List[Pass] = []):
        self.emitter = emitter
        self.passes = passes

    def rewrite(self, task: Task, compilation:Compilation):
        for pass_ in self.passes:
            start = time.perf_counter()
            pass_.reset()
            task = pass_.walk(task)
            compilation.pass_result(pass_, task, time.perf_counter() - start)
        return task

    def compile(self, task: Task):
        compilation = Compilation(task)
        task = self.rewrite(task, compilation)
        start = time.perf_counter()
        self.emitter.reset()
        code = self.emitter.emit(task)
        compilation.emitted = code
        compilation.emit_time = time.perf_counter() - start
        debugging.handle_compilation(compilation)
        return code
