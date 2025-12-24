from v0.relationalai.early_access.dsl.schemas import ConjunctiveSchema, DisjunctiveSchema
from v0.relationalai.early_access.dsl.schemas.components import prefix_concat, SchemaComponent

class StateManager:

    def And(self, *args): return ConjunctiveSchema(*args)
    def Or(self, *args): return DisjunctiveSchema(*args)


class ComponentWrapper:

    class Wrapper:
        def __init__(self, pref, m, k):
            self._prefix = pref
            self._machine = m
            self._funcname = k

        def __call__(self, *args, **kwargs):
            func = getattr(self._machine, self._funcname)
            return { self._prefix: func(*args, **kwargs) }

    def __init__(self, machine, prefix):
        for key, val in vars(machine.__class__).items():
            if callable(val):
                setattr(self, key, ComponentWrapper.Wrapper(prefix, machine, key))

class VarWrapper:

    def __init__(self, comp, container):
        self._comp = comp
        for key, val in vars(comp._prototype).items():
            if isinstance(val, SchemaComponent):
                if key in comp._renamings:
                    c2 = getattr(container, comp._renamings[key])
                else:
                    c2 = getattr(container, comp._decorate_component_name(val.display())) # type: ignore
                setattr(self, key, c2)

class StateComponent:

    def __init__(self, compname, machine, renamings):
        self._compname = compname
        self._machine = machine
        self._prototype = machine.top()
        self._renamings = renamings

    def __call__(self, proto=None):
        if proto is None:
            state = self._prototype
        else:
            state = proto

        s = self._decorate(state)
        map = {}
        for r in self._renamings:
            nm = self._decorate_component_name(r)
            map[nm] = self._renamings[r]
        return s.sync(map)

    def _decorate(self, proto_state): return proto_state.prefix(self._compname)
    def _decorate_component_name(self, nm): return prefix_concat(self._compname, nm)

    def machine(self): return self._machine

    def var_wrapper(self, container):
        return VarWrapper(self, container)

class UndecoratedStateComponent(StateComponent):

    def __init__(self, compname, machine, renamings):
        super().__init__(compname, machine, renamings)

    def _decorate(self, proto_state): return proto_state
    def _decorate_component_name(self, nm): return nm


class TransitionComponent:

    def __init__(self, compname, trans, renamings):
        self._compname = compname
        self._trans = trans
        self._prototype = trans.top()
        self._renamings = renamings

    def __call__(self, proto=None):
        if proto is None:
            trans = self._prototype
        else:
            trans = proto

        t = self._decorate(trans)

        # Rename before-state variables according to renamings
        before_var_prior_to_rename = {}
        map = {}
        for r in self._renamings:
            nm = self._decorate_component_name(r)
            before_var_prior_to_rename[r] = getattr(t, nm)    # [REKS: Use a more direct way to lookup component by name]
            map[nm] = self._renamings[r]
        t2 = t.sync(map)

        before_var_after_rename = {}
        for r in self._renamings:
            renamed = self._renamings[r]
            if isinstance(renamed, str):
                before_var_after_rename[r] = getattr(t2, self._renamings[r])
            else:
                before_var_after_rename[r] = renamed

        after_renamings = {}
        for r in self._renamings:
            after_renamings = after_renamings | before_var_prior_to_rename[r].after.sync_with(before_var_after_rename[r].after)

        # Rename after-state variables according to renamings

        return t2.sync(after_renamings)

    def _decorate(self, proto_trans): return proto_trans.prefix(self._compname)
    def _decorate_component_name(self, nm): return prefix_concat(self._compname, nm)

    def manager(self): return self._trans

class UndecoratedTransitionComponent(TransitionComponent):

    def __init__(self, compname, trans, renamings):
        super().__init__(compname, trans, renamings)

    def _decorate(self, proto_trans): return proto_trans
    def _decorate_component_name(self, nm): return nm