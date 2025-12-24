from __future__ import annotations
from collections import defaultdict
from contextvars import ContextVar
import numbers
from typing import Any, Generic, Iterable, List, Set, TypeVar, cast
from typing_extensions import TypeGuard

from .rel_emitter import Emitter

from .metamodel import Behavior, Builtins, Action, ActionType, Type, Var, Task
from . import metamodel as m
from . import compiler as c
from .clients import config
from .dsl import build
from . import dsl

gather_vars = m.Utils.gather_vars
gather_task_vars = m.Utils.gather_task_vars

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def is_static(x:Any):
    if isinstance(x, m.Action):
        return all([is_static(z) for z in x.bindings.values()])
    if isinstance(x, Var):
        return x.value is not None
    if isinstance(x, Type):
        return True
    if isinstance(x, str):
        return True
    if isinstance(x, numbers.Number):
        return True
    if isinstance(x, list):
        return all(is_static(i) for i in x)
    if isinstance(x, tuple):
        return all(is_static(i) for i in x)
    if isinstance(x, dict):
        return all(is_static(i) for i in x.values())
    return False

def prepend_bindings(prefix:List[Var], action:Action):
    neue_bindings = {}
    for i, var in enumerate(prefix):
        neue_bindings[Builtins.Relation.properties[i]] = var
    prop_len = len(neue_bindings)
    for v in action.bindings.values():
        neue_bindings[Builtins.Relation.properties[prop_len]] = v
        prop_len += 1
    action.bindings = neue_bindings

def add_deps_to_binds(root:Task, bound_item:Task, deps:List[Var], replace_task=None):
    has_binds = False
    for item in root.items:
        if item.is_subtask_call():
            assert isinstance(item.entity.value, Task)
            has_binds |= add_deps_to_binds(item.entity.value, bound_item, deps, replace_task=replace_task)
        if item.action == ActionType.Bind and item.entity.value == bound_item:
            if replace_task:
                item.entity.value = replace_task
            prepend_bindings(deps, item)
            has_binds = True
    return has_binds

def flatten(items:List[Any]):
    neue = []
    for item in items:
        if isinstance(item, list):
            neue.extend(flatten(item))
        elif isinstance(item.value, list):
            for i in item.value:
                if isinstance(i, Var):
                    neue.append(i)
        elif isinstance(item, Var):
            neue.append(item)
    return neue

def is_base_type(val:m.Value|None) -> TypeGuard[m.Type]:
    return type(val) is m.Type and (not val.isa(Builtins.Relation) or val.isa(Builtins.Type))

def is_prop(val:m.Value|None) -> TypeGuard[m.Property]:
    return isinstance(val, m.Property) or isinstance(val, Type) and val.isa(Builtins.Property)

def pr(*args:Any):
    def stringify(x):
        if isinstance(x, list) or isinstance(x, set):
            return [stringify(i) for i in x]
        if isinstance(x, OrderedSet):
            return stringify(list(x))
        return str(x)
    return print(*[stringify(x) for x in args])

intermediate_annotations = ContextVar("intermediate_annotations", default=[Builtins.PipelineAnnotation])

def annotate_intermediate(task: Task):
    for annotation in intermediate_annotations.get():
        if annotation not in task.parents:
            task.parents.append(annotation)

#--------------------------------------------------
# OrderedSet
#--------------------------------------------------

T = TypeVar('T')
class OrderedSet(Generic[T]):
    def __init__(self):
        self.set:Set[T] = set()
        self.list:List[T] = []

    def add(self, item:T):
        if item not in self.set:
            self.set.add(item)
            self.list.append(item)

    def update(self, items:Iterable[T]):
        for item in items:
            self.add(item)

    def remove(self, item:T):
        if item in self.set:
            self.set.remove(item)
            self.list.remove(item)

    def clear(self):
        self.set.clear()
        self.list.clear()

    def __getitem__(self, ix):
        if len(self.list) <= ix:
            return None
        return self.list[ix]

    def __contains__(self, item:T):
        return item in self.set

    def __bool__(self):
        return bool(self.set)

    def __iter__(self):
        return iter(self.list)

    def __len__(self):
        return len(self.list)

    def __or__(self, other: OrderedSet[T]) -> OrderedSet[T]:
        result = OrderedSet[T]()
        result.update(self.list)
        result.update(other.list)
        return result

class ActionSet(OrderedSet[Action]):
    def __init__(self):
        super().__init__()

    def add(self, item:Action):
        for sub in self.list:
            if item.equiv(sub):
                return
        super().add(item)

#--------------------------------------------------
# Flow
#--------------------------------------------------

class FlowFrame:
    def __init__(self, flow:Flow, parent=None) -> None:
        self.flow = flow
        self.parent = parent
        self.sources = defaultdict(ActionSet)
        self.refs:defaultdict[Var, ActionSet] = defaultdict(ActionSet)
        self.queued:list[Action] = []
        self.multi = set()
        self.var_counts = defaultdict(int)
        self.var_max_order = defaultdict(int)

        if parent:
            for k, v in parent.sources.items():
                self.sources[k].update(v)
            for k, v in parent.refs.items():
                self.refs[k].update(v)
            for v in parent.multi:
                self.multi.add(v)
            for v, c in parent.var_counts.items():
                self.var_counts[v] = c
            for v, c in parent.var_max_order.items():
                self.var_max_order[v] = c

class Flow:
    multi_names = set()

    def __init__(self) -> None:
        self.tasks:list[Task] = []
        self.stack:list[FlowFrame] = []
        self.item_order = dict()
        self.item_is_source = defaultdict(bool)

    def push(self, no_parent=False):
        parent = None if no_parent else self.stack[-1] if self.stack else None
        self.stack.append(FlowFrame(self, parent))

    def pop(self):
        return self.stack.pop()

    @property
    def sources(self):
        return self.stack[-1].sources

    @property
    def refs(self):
        return self.stack[-1].refs

    @property
    def queued(self):
        return self.stack[-1].queued

    @property
    def multi(self):
        return self.stack[-1].multi

    def reset(self):
        self.tasks.clear()

    def peek_action(self, item:Action):
        if item not in self.item_order:
            self.item_order[item] = len(self.item_order)
        return self.item_order[item]

    def action(self, item:Action):
        self.peek_action(item)
        params = [p for p in flatten(item.params_list()) if p.value is None]
        if item.entity.isa(Builtins.GlobalFilter) or not params:
            self.queued.append(item)
            return

        has_source = False
        for param in params:
            if not self.sources[param]:
                has_source |= self.var_has_uses(param)
                self.sources[param].add(item)
            self.refs[param].add(item)

        self.item_is_source[item] = has_source

        if is_prop(item.entity.value):
            prop = item.entity.value
            var = params[-1]
            if var.value is None:
                self.sources[var].add(item)
            else:
                self.sources[params[0]].add(item)
            if prop.name in self.multi_names or Builtins.MultiValued in prop.parents:
                self.multi_names.add(prop.name)
                if var and var.value is None:
                    self.multi.add(var)
        elif is_base_type(item.entity.value) or item.entity.isa(Builtins.Filter) or item.entity.isa(Builtins.Extender) or not has_source:
            for param in params:
                self.sources[param].add(item)

    def remove_action(self, item:Action):
        for param in item.params_list():
            self.refs[param].remove(item)
            self.sources[param].remove(item)

    def action_has_source(self, item:Action):
        return self.item_is_source[item]

    def var(self, var:Var, max_order:int):
        self.stack[-1].var_counts[var] += 1
        self.stack[-1].var_max_order[var] = max(max_order, self.stack[-1].var_max_order.get(var, 0))

    def var_order(self, var:Var):
        return self.stack[-1].var_max_order.get(var, 0)

    def var_uses(self, var:Var):
        return self.stack[-1].var_counts[var] - 1

    def var_has_uses(self, var:Var):
        return self.stack[-1].var_counts[var] > 1

    def keys(self, var:Var):
        ks = []
        for ref in self.sources[var]:
            params = ref.params_list()
            if is_prop(ref.entity.value) and params[1] == var:
                ks.append(params[0])
            if is_base_type(ref.entity.value):
                return [var]
            if (ref.entity.isa(Builtins.Aggregate)
                and not ref.entity.isa(Builtins.Extender)
                and params[-1] == var
                and len(params) > 1):
                # if the source is an aggregate and there are grouping vars,
                # then the key is the grouping vars. Any vars before the agg value
                # are the group vars. Sorts (which are extender aggs) are ignored
                # as this would add the sort projection as keys.
                return params[:-1]
        return ks

    def _action_vars(self, item:Action, to_check:List[Var]):
        params = [v for v in flatten(item.params_list()) if v not in to_check and v.value is None]
        return params

    def demand_filters(self, var:Var, outs:ActionSet, to_check:List[Var], seen:set[Var]):
        if var in seen:
            return
        seen.add(var)
        if len(self.sources[var]) > 1:
            for sub in self.sources[var]:
                outs.add(sub)
                to_check.extend(self._action_vars(sub, to_check))
        for ref in self.refs[var]:
            if ref in outs:
                continue
            for param in self._action_vars(ref, to_check):
                self.demand_filters(param, outs, to_check, seen)

    def demand(self, var:Var, outs:ActionSet, to_check:List[Var], seen:set[Var]):
        sources = self.sources[var]
        seen = seen.copy()
        for ref in self.refs[var]:
            if ref in sources:
                outs.add(ref)
                to_check.extend(self._action_vars(ref, to_check))
            elif ref in outs:
                continue
            for param in self._action_vars(ref, to_check):
                self.demand_filters(param, outs, to_check, seen)

        return outs

    def demand_vars(self, vars:Iterable[Var], seen:set[Var]|None=None):
        outs:ActionSet = ActionSet()
        if seen is None:
            seen = set()
        to_check = list(vars)

        if self.queued:
            for item in self.queued:
                outs.add(item)
                to_check.extend(self._action_vars(item, to_check))
            self.queued.clear()

        for var in to_check:
            if var in seen:
                continue
            self.demand(var, outs, to_check, seen)
            seen.add(var)

        return sorted(outs.list, key=lambda x: self.item_order.get(x, 0))

    def task(self, task:Task):
        self.tasks.append(task)

    def find_uses(self, task:Task, uses:dict[Task, list[tuple[Task, Action]]]):
        for item in task.items:
            if item.entity.isa(Builtins.Intermediate) and item.action == ActionType.Get:
                assert isinstance(item.entity.value, Task)
                uses[item.entity.value].append((task, item))
            for v in item.params_list():
                if isinstance(v.value, Task) and v.value.items:
                    self.find_uses(v.value, uses)

    def finalize(self):
        assert not self.stack, "Flow still has frames on the stack"

        auto_inline = True
        if auto_inline:
            uses = defaultdict(list)
            replaced = {}
            collapsed_tasks = []
            for task in reversed(self.tasks):
                self.find_uses(task, uses)
                if task.isa(Builtins.Intermediate) and len(uses[task]) == 1:
                    sub, sub_action = uses[task][0]
                    if replaced.get(sub):
                        sub = replaced[sub]
                    replaced[task] = sub
                    sub.items.remove(sub_action)
                    for item in reversed(task.items):
                        if not (item.action == ActionType.Bind and item.entity.value is task):
                            sub.items.insert(0, item)
                    dedeuped = ActionSet()
                    for item in sub.items:
                        dedeuped.add(item)
                    sub.items = dedeuped.list
                else:
                    collapsed_tasks.append(task)

            items = [
                build.relation_action(ActionType.Call, task, []) for task in reversed(collapsed_tasks)
            ]
        else:
            items = [
                build.relation_action(ActionType.Call, task, []) for task in self.tasks
            ]

        return items


#--------------------------------------------------
# Dataflow
#--------------------------------------------------

class Dataflow(c.Pass):
    def __init__(self, copying=True) -> None:
        super().__init__(copying)
        self.flow = Flow()

    def reset(self):
        super().reset()
        self.flow.reset()

    #--------------------------------------------------
    # Query
    #--------------------------------------------------

    def query(self, query: Task, parent=None):
        self.flow.push()
        self.handle_items(query.items)
        self.flow.pop()
        final = self.flow.finalize()
        if final:
            query.behavior = Behavior.Sequence
        query.items = final

    def handle_items(self, items:list[Action]):
        ix = 0
        # count the number of times a variable appears in the items
        for item in items:
            item_ix = self.flow.peek_action(item)
            for v in item.vars(recursive=True, with_subs=True):
                self.flow.var(v, item_ix)

        while ix < len(items):
            item = items[ix]
            if item.is_subtask_call():
                task = item.entity.value
                assert isinstance(task, Task)
                if task.behavior == Behavior.Union:
                    self.handle_union(item)
                elif task.behavior == Behavior.OrderedChoice:
                    self.handle_choice(item)
                else:
                    self.handle_subtask(item)
                ix += 1

            # gather all the consecutive binds and handle them together
            elif item.action.is_effect():
                sub_ix = ix + 1
                while sub_ix < len(items) and items[sub_ix].action.is_effect():
                    sub_ix += 1
                binds = items[ix:sub_ix]
                self.handle_binds(binds)
                ix = sub_ix

            elif item.entity.isa(Builtins.Aggregate):
                self.handle_aggregate(item)
                ix += 1

            elif item.entity.isa(Builtins.Quantifier):
                self.handle_quantifier(item)
                ix += 1

            elif item.entity.isa(Builtins.Install):
                sub_ix = ix + 1
                while sub_ix < len(items) and items[sub_ix].entity.isa(Builtins.Install):
                    sub_ix += 1
                binds = items[ix:sub_ix]
                self.handle_installs(binds)
                ix = sub_ix

            # otherwise we consume the action and decide what to do with it later
            else:
                self.flow.action(item)
                ix += 1

    def determine_keys(self, var:Var, seen:set[Var]|None=None):
        if var in self.flow.multi:
            return [var]
        if keys := self.flow.keys(var):
            return keys

        if seen is None:
            seen = set()
        seen.add(var)
        keys = []
        for ref in self.flow.sources[var]:
            # ignore filters, they can't produce values
            if ref.entity.isa(Builtins.Filter):
                continue
            if ref.entity.isa(Builtins.Expensive):
                return [var]
            for v in flatten(ref.params_list()):
                if v not in seen:
                    keys.extend(self.determine_keys(v, seen))
        return keys

    def gather_incomputable_vars(self, var:Var, vars:OrderedSet[Var], seen:set[Var]):
        if var in seen or var.value is not None or not self.flow.var_has_uses(var):
            return
        seen.add(var)
        keys = self.flow.keys(var)
        is_multi = var in self.flow.multi
        if is_multi:
            if len(self.flow.sources[var]) > 1:
                vars.add(var)
            if len(self.flow.refs[var]) > 1:
                vars.add(var)
        elif keys:
            vars.update(keys)
            seen.update(keys)
        # else:
        sources = self.flow.sources[var]
        for ref in sources:
            if ref.entity.isa(Builtins.Expensive) and self.flow.var_uses(var) > 0:
                vars.add(var)
            elif ref.action == ActionType.Call \
                and not ref.entity.isa(Builtins.Filter) \
                and not ref.entity.isa(Builtins.SingleValued):
                vars.add(var)
            for v in flatten(ref.params_list()):
                self.gather_incomputable_vars(v, vars, seen)
        if sources:
            first = sources.list[0]
            vs = {
                param for param in flatten(first.params_list())
                if param.value is None \
                    and self.flow.sources[param][0] == first \
                    and self.flow.var_has_uses(param)
            }
            if len(vs) > 1:
                vars.update(vs)

    def gather_action_vars(self, actions:Iterable[Action]):
        vars = OrderedSet()
        seen = set()
        all_actions = list(actions)
        for action in all_actions:
            for v in action.params_list():
                self.gather_incomputable_vars(v, vars, seen)
            if action.is_subtask_call():
                assert isinstance(action.entity.value, Task)
                all_actions.extend(action.entity.value.items)
        return vars

    def _downstream(self, min_order:int, var:Var, seen:set[Var], available_vars:set[Var], depth=1):
        # This function finds the most downstream variable that is sourced from var and
        # is referenced at or after min_order
        if self.flow.var_order(var) >= min_order:
            return var

        seen.add(var)
        desired = OrderedSet()
        for ref in self.flow.refs[var]:
            for dep in ref.vars(recursive=True, with_subs=True):
                if dep.value is None and dep not in seen:
                    downstream = self._downstream(min_order, dep, seen, available_vars, depth+1)
                    if downstream:
                        desired.add(downstream)

        # if any desired variables aren't actually available then we must return this var
        # as it'll be used to compute those later
        if any([v not in available_vars for v in desired]):
            return var

        # if there are multiple desired, then this is the most upstream ancestor
        if len(desired) > 1:
            return var

        return desired[0]

    def create_intermediate(self, actions:list[Action]):
        vars = self.gather_action_vars(actions)

        min_order = min([self.flow.item_order.get(x, 0) for x in actions])
        outs = self.flow.demand_vars(vars)

        get = outs[0] if outs else None
        if len(outs) > 1:
            # find the minimal set of vars that are needed downstream and use those
            # as the head of the intermediate
            cur_vars = set(vars)
            out_vars = OrderedSet()
            if len(vars) > 1:
                available_vars = set(flatten([action.params_list() for action in outs]))
                for v in vars:
                    down = self._downstream(min_order, v, cur_vars.copy(), available_vars)
                    if down:
                        out_vars.add(down)
            else:
                out_vars = vars

            # this intermediate will now be the source for those
            for v in out_vars:
                self.flow.sources[v].clear()
                to_remove = [ref for ref in self.flow.refs[v] if ref in outs]
                for ref in to_remove:
                    self.flow.refs[v].remove(ref)

            intermediate = Task(items=[*outs], parents=[Builtins.Intermediate, Builtins.Expensive])
            intermediate.items.append(build.relation_action(ActionType.Bind, intermediate, out_vars))
            self.flow.task(intermediate)
            get = build.relation_action(ActionType.Get, intermediate, out_vars)
            self.flow.action(get)
            for action in outs:
                action_params = action.params_list()
                keys = set()
                can_remove = True
                for param in action_params:
                    keys.update(self.determine_keys(param))
                    if self.flow.sources[param][0] == action:
                        can_remove = False
                        break
                if keys.issubset(vars) and can_remove:
                    self.flow.remove_action(action)

            vars = list(out_vars)
        return get, vars

    def _split_return(self, bind, params, vars, ret_vars, get, demand=True):
        action_type = bind.action
        is_export = bind.entity.isa(Builtins.ExportReturn)
        for (ix, v) in enumerate(params):
            sub = list(self.flow.demand_vars([v], seen=set(vars))) if demand else []
            if get:
                sub.insert(0, get)
            col = Var(Builtins.Symbol, value=f"col{ix:03}")
            if is_export:
                rel = dsl.rel.Export_Relation._rel
                uuid_str = dsl.rel.uuid_string._rel
                v2 = Var()
                sub.append(build.relation_action(ActionType.Call, dsl.rel.pyrel_default._rel, [uuid_str, v, v, v2]))
                sub.append(build.relation_action(action_type, rel, [col, *ret_vars, v2]))
            else:
                rel = dsl.rel.output.cols._rel
                sub.append(build.relation_action(action_type, rel, [col, *ret_vars, v]))
            self.flow.task(Task(items=sub))


    def handle_binds(self, binds:List[Action]):
        get, vars = self.create_intermediate(binds)

        # for each bind, generate the output action
        statics = []
        for bind in binds:
            self.flow.push()
            action_type = bind.action
            params = bind.params_list()
            if is_static(bind) and not bind.entity.isa(Builtins.Return):
                statics.append(bind)
            elif (bind.entity.isa(Builtins.Distinct) and not set(vars).issubset(set(params))) or (bind.entity.isa(Builtins.Return) and set(vars) == set(params)):
                sub_raw = list(self.flow.demand_vars(params, seen=set(vars)))
                sub = []
                for item in sub_raw:
                    if isinstance(item.entity.value, m.Property):
                        [k, v] = item.params_list()
                        sub.append(build.relation_action(ActionType.Call, dsl.rel.pyrel_default._rel, [item.entity.value, dsl.rel.Missing, k, v]))
                    else:
                        sub.append(item)
                if get and get not in sub:
                    sub.insert(0, get)

                intermediate = Task(items=sub)
                hash_var = Var(name="hash")
                sub.append(build.call(Builtins.make_identity, [Var(value=list(params)), hash_var]))
                sub.append(build.relation_action(action_type, intermediate, params + [hash_var]))
                self.flow.task(Task(items=sub))
                intermediate_get = build.relation_action(ActionType.Get, intermediate, params + [hash_var])
                self._split_return(bind, params, vars, [hash_var], intermediate_get, demand=False)

            elif bind.entity.isa(Builtins.Return):
                ret_vars = self.gather_action_vars([bind])
                if not ret_vars:
                    ret_vars = [Var(value=bind.id)]
                self._split_return(bind, params, vars, ret_vars, get)
            else:
                sub = list(self.flow.demand_vars(params, seen=set(vars)))
                if get and get not in sub:
                    sub.insert(0, get)
                sub.append(bind)
                self.flow.task(Task(items=sub))
            self.flow.pop()

        if statics:
            self.flow.push()
            if get:
                statics.insert(0, get)
            self.flow.task(Task(items=statics))
            self.flow.pop()

    def handle_aggregate(self, item:Action):
        agg = cast(Task, item.entity.value)
        is_extender = agg.isa(Builtins.Extender)
        (args, group, pre_args, ret) = item.params_list()
        group_vars = cast(List[Var], group.value)
        arg_vars = cast(List[Var], args.value)
        pre_arg_vars = cast(List[Var], pre_args.value)

        flattened_call = build.relation_action(ActionType.Get, agg, [*pre_arg_vars, *group_vars, *arg_vars])
        self.flow.item_order[flattened_call] = self.flow.item_order.get(item, 0)
        get, vars = self.create_intermediate([flattened_call])

        # to prevent shadowing errors we need to map the inner vars to new vars
        mapped = [Var(name=var.name, type=var.type, value=var.value) for var in arg_vars]

        # create the inner relation we'll aggregate over
        inner_items = list(self.flow.demand_vars([*arg_vars, *group_vars], seen=set(vars)))
        inner_vars = arg_vars.copy()
        if get:
            inner_items.insert(0, get)

        #de-shadow any arguments that are also in the group by
        for ix, arg in enumerate(arg_vars):
            if arg in group_vars:
                inner_vars[ix] = Var(name=f"inner_{arg.name}", type=arg.type, value=arg.value)
                inner_items.append(build.eq(inner_vars[ix], arg))

        inner = Task(items=inner_items)
        inner_items.append(build.relation_action(ActionType.Bind, inner, inner_vars))

        agg_bindings = [ret] if not is_extender else [ret, *mapped]
        agg_call = build.relation_action(ActionType.Call, agg, [*pre_arg_vars, Var(value=inner), *agg_bindings])


        outer = Task(items=[agg_call], parents=[Builtins.Aggregate])
        if is_extender:
            outer.parents.append(Builtins.Extender)
        outer_params = [*group_vars, ret] if not is_extender else [ret, *group_vars, *mapped]
        outer.items.append(build.relation_action(ActionType.Bind, outer, outer_params))
        self.flow.task(outer)

        get_params = outer_params if not is_extender else [ret, *group_vars, *arg_vars]
        get = build.relation_action(ActionType.Get, outer, get_params)
        self.flow.action(get)

    def handle_subtask(self, item:Action):
        subtask = cast(Task, item.entity.value)
        get, vars = self.create_intermediate(subtask.items)
        sub_items = [get] + subtask.items if get else subtask.items
        self.flow.push()
        self.handle_items(sub_items)
        self.flow.pop()

    def handle_quantifier(self, item:Action):
        quantifier = item.entity.value
        assert isinstance(quantifier, Task)
        group, task_var = [*item.bindings.values()]
        sub_task = task_var.value
        assert isinstance(sub_task, Task)

        if isinstance(group.value, list) and len(group.value):
            raise Exception("TODO: grouped quantifiers")

        shared = self.gather_action_vars(sub_task.items)
        if len(sub_task.items) > 1:
            task_to_quantify = Task(items=[
                *sub_task.items,
            ], parents=[Builtins.InlineAnnotation])
            task_to_quantify.items.append(build.relation_action(ActionType.Bind, task_to_quantify, shared))
            self.flow.task(task_to_quantify)
            action = build.relation_action(ActionType.Get, task_to_quantify, shared)
        else:
            cur = sub_task.items[0]
            bindings = {k: v if v in shared else Var(name="_") for k,v in cur.bindings.items()}
            action = Action(action=cur.action, entity=cur.entity, types=cur.types, bindings=bindings)


        # create the quantified task, which just gets the subtask
        quantifed_task = Task()
        quantifed_task.items.append(action)

        call = build.call(quantifier, [group, Var(value=quantifed_task)])
        self.flow.action(call)

    def handle_union(self, action:Action):
        union_task = action.entity.value
        assert isinstance(union_task, Task)
        union_task.parents.append(Builtins.Intermediate)

        self.flow.push()
        get, shared = self.create_intermediate(union_task.items)
        shared = list(shared)
        has_outputs = False
        for item in union_task.items:
            assert isinstance(item.entity.value, Task)
            sub = item.entity.value
            has_outputs |= add_deps_to_binds(sub, union_task, shared)
            self.flow.push()
            items = [get] + sub.items if get else sub.items
            self.handle_items(items)
            self.flow.pop()

        self.flow.pop()

        # Get the result of the union
        if has_outputs:
            get = build.relation_action(ActionType.Get, union_task, shared + action.params_list())
            # self.action(get)
            for v in shared:
                self.flow.sources[v].clear()
                self.flow.sources[v].add(get)
                # self.flow.refs[v].clear()
            self.flow.action(get)
            # for var in get.params_list():
            #     # self.flow.sources[var].append(get)
            #     self.flow.sources[var].add(get)

    def handle_choice(self, action:Action):
        choice = action.entity.value
        assert isinstance(choice, Task)
        choice.parents.append(Builtins.EDB)
        choice_params = action.params_list()
        prevs = []

        self.flow.push()
        get, shared = self.create_intermediate(choice.items)
        shared = list(shared)
        has_outputs = False

        for item in choice.items:
            cur_task = item.entity.value
            assert isinstance(cur_task, Task)
            # cur_task.parents.append(Builtins.InlineAnnotation)
            # add deps to the binds and also replace the task so that we write to the current
            # branch rather than the final return
            cur_has_outputs = add_deps_to_binds(cur_task, choice, shared, replace_task=cur_task)
            has_outputs |= cur_has_outputs

            # Negate all the previous branches to ensure we only return a value if
            # we're at our position in the order
            for prev in reversed(prevs):
                fetch = build.relation_action(ActionType.Get, prev, shared + [Var(name="_") for _ in choice_params])
                prev_task = Task(items=[fetch])
                cur_task.items.insert(0, build.call(Builtins.Not, [Var(value=[]), Var(value=prev_task)]))

            self.flow.push()
            if get:
                self.flow.queued.append(get)
            items = cur_task.items
            if not cur_has_outputs:
                items.append(build.relation_action(ActionType.Bind, cur_task, shared + choice_params))
            # items.append(
            #     build.relation_action(ActionType.Bind, choice, shared + choice_params),
            # )
            self.handle_items(items)
            self.flow.pop()

            self.flow.push(no_parent=True)
            self.handle_items([
                build.relation_action(ActionType.Get, cur_task, shared + choice_params),
                build.relation_action(ActionType.Bind, choice, shared + choice_params),
            ])
            self.flow.pop()

            prevs.append(cur_task)

        self.flow.pop()

        # Get the result of the choice
        if has_outputs:
            get = build.relation_action(ActionType.Get, choice, shared + choice_params)
            for v in shared:
                self.flow.sources[v].clear()
                self.flow.sources[v].add(get)
            self.flow.action(get)

    def handle_installs(self, installs:list[Action]):
        self.flow.task(Task(items=installs))


#--------------------------------------------------
# Shredder
#--------------------------------------------------

class Shredder(c.Pass):
    def query(self, query: Task, parent=None):
        neue_actions = []
        for item in query.items:
            if item.action not in [ActionType.Call, ActionType.Construct] and not item.entity.isa(Builtins.Relation):
                ident, action = item.entity, item.action
                for type in item.types:
                    neue_actions.append(build.relation_action(action, type, [ident]))
                for prop, value in item.bindings.items():
                    neue_actions.append(build.relation_action(action, prop, [ident, value]))
            else:
                walked = self.walk(item)
                neue_actions.append(walked)
        query.items = neue_actions

#--------------------------------------------------
# Splinter
#--------------------------------------------------

class Splinter(c.Pass):

    def query(self, query: Task, parent=None):
        grouped_effects = defaultdict(list)
        prev_fetches = []
        effects = []
        non_effects = []
        neue_items = []
        non_effects_vars = OrderedSet()

        def process_grouped_effects():
            nonlocal neue_items, grouped_effects, non_effects, effects, non_effects_vars
            if len(grouped_effects) > 1:
                non_effects_vars.update(gather_vars(non_effects))
                fetch = None
                if non_effects:
                    fetch = self.create_fetch(prev_fetches + non_effects, non_effects_vars)
                    neue_items.append(fetch)
                    assert isinstance(fetch.entity.value, Type)
                    prev_fetches.append(build.relation_action(ActionType.Get, fetch.entity.value, non_effects_vars))

                for (k, b) in grouped_effects.items():
                    effect_query = self.create_effect_query(b, non_effects_vars, prev_fetches)
                    neue_items.append(effect_query)
            elif grouped_effects:
                neue_items.append(build.call(Task(items=prev_fetches + non_effects + effects), []))

            grouped_effects.clear()
            non_effects.clear()
            effects.clear()

        for item in query.items:
            if item.action.is_effect():
                grouped_effects[(item.action, item.entity.value)].append(item)
                effects.append(item)
            else:
                if grouped_effects:
                    process_grouped_effects()
                non_effects.append(item)

        if grouped_effects:
            process_grouped_effects()
        elif non_effects:
            neue_items.append(build.call(Task(items=[*prev_fetches, *non_effects]), []))

        if len(neue_items) > 1:
            query.behavior = Behavior.Sequence
            query.items = neue_items

    #--------------------------------------------------
    # Subtask creation
    #--------------------------------------------------

    def create_fetch(self, non_effects: List[Action], effects_vars: Iterable[Var]):
        fetch = Task()
        annotate_intermediate(fetch)
        non_effects = non_effects.copy()
        non_effects.append(build.relation_action(ActionType.Bind, fetch, effects_vars))
        fetch.items = non_effects
        return build.call(fetch, [])

    def create_effect_query(self, effects: List[Action], effects_vars: Iterable[Var], fetches: Any):
        neue = Task()
        effects = effects.copy()
        for fetch in reversed(fetches):
            effects.insert(0, fetch)
        neue.items = effects
        return build.call(neue, [])

#--------------------------------------------------
# SetCollector
#--------------------------------------------------

set_types = [ActionType.Bind, ActionType.Persist, ActionType.Unpersist]

class SetCollector(c.Pass):
    def query(self, query: Task, parent=None):
        binds = [i for i in query.items if i.action in set_types]
        if len(binds) > 1:
            neue_items = []
            for item in query.items:
                if item.action not in set_types:
                    neue_items.append(item)
            neue_items.extend(self.create_raw(binds))
            query.items = neue_items

    def create_raw(self, binds: List[Action]):
        vals = [Var(value=[]) for i in range(len(binds[0].bindings))]
        vars = [Var() for v in vals]

        for bind in binds:
            for ix, var in enumerate(bind.bindings.values()):
                cast(List[Var], vals[ix].value).append(var)

        return [
            build.relation_action(ActionType.Get, Builtins.RawData, vals + vars),
            build.relation_action(binds[0].action, cast(Type, binds[0].entity.value), vars)
        ]

#--------------------------------------------------
# Compiler
#--------------------------------------------------

class Clone(c.Pass):
    pass

class Compiler(c.Compiler):
    def __init__(self, config:config.Config):
        self.config = config
        super().__init__(Emitter(config), [
            Clone(),
            Shredder(),
            Dataflow(),
            Splinter(),
            SetCollector(),
        ])

    def compile(self, task: Task):
        token = None
        if self.config.get("use_inlined_intermediates", False):
            token = intermediate_annotations.set([Builtins.InlineAnnotation])

        try:
            return super().compile(task)
        finally:
            if token:
                intermediate_annotations.reset(token)
