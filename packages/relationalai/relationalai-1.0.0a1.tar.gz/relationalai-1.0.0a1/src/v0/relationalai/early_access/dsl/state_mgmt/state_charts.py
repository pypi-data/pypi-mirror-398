from abc import abstractmethod

from v0.relationalai.early_access.dsl.schemas import Schema
from v0.relationalai.early_access.dsl.state_mgmt import ComponentWrapper, StateManager, StateComponent, UndecoratedStateComponent

class StateChart(StateManager):

    def after_state(self, parent_state=None):
        if parent_state is None:
            parent_state = self.top()
        return parent_state.decorate()

    # User asserts that relation rel is empty in this state
    #
    def is_empty(self, rel): return self.top().add_predicate_constraint(rel.empty())

    def manage_transitions(self, tm):
        self._transition_mgr = tm

    # User-declared start state for this state machine
    #
    @abstractmethod
    def inactive(self) -> Schema:
        pass

    # Method for constructing a state of this machine from parameters, described
    # in subclasses that override this method.
    #
    @abstractmethod
    def state(self) -> Schema:
        pass

    # User-declared top-state for this state machine
    #
    @abstractmethod
    def top(self) -> Schema:
        pass

    def transition_manager(self): return self._transition_mgr

class SimpleStateChart(StateChart):

    def active(self): return self.top()
    def inactive(self): return self.top()

    # Returns a blank state (no variables or constraints). This will be the
    # prototype from which to fill in the variables and constraints of a
    # simple state machine
    #
    def blank_state(self): return self.And()

    # Generates a state (schema) for this StateChart. If an optional
    # parent state is provided, then the state returned by this method
    # will be a substate of the parent state.
    #
    def state(self, parent_state=None):
        if parent_state is None:
            parent_state = self.top()

        # Return a copy of parent_state so that clients can add variables
        # and constraints without overriding the parent_state
        #
        return self.And(parent_state)

class CompositeStateChart(StateChart):

    def __init__(self):
        self._components = {}

    def add_component(self, compname, machine, *syncs):
        renamings = {}
        for r in syncs:
           renamings = renamings | r
        self._components[compname] = StateComponent(compname, machine, renamings)
        self.__setattr__(compname, ComponentWrapper(machine, compname))

    def add_undecorated_component(self, compname, machine, *syncs):
        renamings = {}
        for r in syncs:
           renamings = renamings | r
        self._components[compname] = UndecoratedStateComponent(compname, machine, renamings)
        self.__setattr__(compname, ComponentWrapper(machine, compname))

    def active(self):
        comp_state = {}
        for c in self._components:
            comp = self._components[c]
            comp_state[c] = comp.machine().active()
        return self.state(comp_state)

    def component(self, name): return self._components[name]

    def component_machine(self, name):
        return self.component(name).machine()

    def inactive(self):
        comp_state = {}
        for c in self._components:
            comp = self._components[c]
            comp_state[c] = comp.machine().inactive()
        return self.state(comp_state)

    # Generates a state (schema) for this CompositeStateChart given
    # a dictionary mapping component names to specifications of the
    # desired state of each component.
    #
    def state(self, *comp_state):
        component_states = {}
        for d in comp_state:
           component_states = component_states | d

        states = []
        for c in self._components:
            comp = self._components[c]
            if c in component_states:
                states.append(comp(component_states[c]))
            else:
                states.append(comp(comp._prototype))
        s = self.And(*tuple(states))

        for c in self._components.values():
            s.__setattr__(c._compname, c.var_wrapper(s))
        return s

    def top(self): return self.state({})
