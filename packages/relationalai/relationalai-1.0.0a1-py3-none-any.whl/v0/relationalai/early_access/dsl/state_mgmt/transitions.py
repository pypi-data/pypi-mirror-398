from v0.relationalai.early_access.dsl.state_mgmt import ComponentWrapper, StateManager, TransitionComponent, UndecoratedStateComponent, UndecoratedTransitionComponent

class Transition(StateManager):

    def __init__(self, sm):
        self._state_chart = sm

    # The transition that when fired activates this state machine from its
    # declared start state. Users override this method to declare more precise
    # effects of this operation.
    #
    def activate(self):
        return self.And(self.top(),
                        self._state_chart.inactive(),
                        self._state_chart.active().decorate())

    # An active transition starts and ends in the Active state. Most user-declared
    # transitions will be either activate or active transitions.
    #
    def active(self):
        return self.And(self.top(),
                        self.state_chart().active(),
                        self.state_chart().active().decorate())

    def after_state(self): return self._state_chart.after_state()
    def before_state(self): return self._state_chart.top()

    def top(self):
        return self.And(self.before_state(),
                        self.after_state())

    def state_chart(self): return self._state_chart

class SimpleTransition(Transition):

    def __init__(self, sm):
        super().__init__(sm)

    # The transition method of a SimpleTransition composes the transition
    # by conjoining before and after instances of the state machine being managed.
    # By default, these are the values returned by the before_state and after_state
    # methods respectively, but these may be overridden by keyword arguments 'before'
    # and 'after'.
    #
    def transition(self, **kwargs):
        if len(kwargs) > 2:
            raise Exception("Not possible")

        for a in kwargs:
            if a != 'before' and a != 'after':
                raise Exception("Only permissible keyword arguments to SimpleTransition.transition are 'before' and 'after'")
        if 'after' in kwargs:
            after_state = kwargs['after']
        else:
            after_state = self.after_state()

        if 'before' in kwargs:
            before_state = kwargs['before']
        else:
            before_state = self.before_state()

        return self.And(before_state, after_state)

class CompositeTransition(Transition):

    def __init__(self, sm):
        super().__init__(sm)
        self._components = {}

        comps = sm._components
        for c in comps:
            comp = comps[c]
            if isinstance(comp, UndecoratedStateComponent):
                self.add_undecorated_component(c, comp.machine().transition_manager())
            else:
                self.add_component(c, comp.machine().transition_manager())

    def activate(self):
        t = super().activate()

        transitions = []
        for c in self._components.values():
            transitions.append(c(c.manager().activate()))

        return self.And(t, *tuple(transitions))

    def add_component(self, compname, transm):
        state_mgr = self._state_chart
        state_components = state_mgr._components
        renamings = {}
        if compname in state_components:
            renamings = state_components[compname]._renamings

        self._components[compname] = TransitionComponent(compname, transm, renamings)
        self.__setattr__(compname, ComponentWrapper(transm, compname))

    def add_undecorated_component(self, compname, machine):
        state_mgr = self._state_chart
        state_components = state_mgr._components
        renamings = {}
        if compname in state_components:
            renamings = state_components[compname]._renamings
        self._components[compname] = UndecoratedTransitionComponent(compname, machine, renamings)
        self.__setattr__(compname, ComponentWrapper(machine, compname))

    def component(self, name): return self._components[name]

    def top(self):
        t = super().top()
        t2 = self.transition({})
        return self.And(t, t2)

    def transition(self, *transitions):
        component_transitions = {}
        for d in transitions:
           component_transitions = component_transitions | d

        transitions = []
        for c in self._components:
            comp = self._components[c]
            if c in component_transitions:
                transitions.append(comp(component_transitions[c]))
            else:
                transitions.append(comp(comp._prototype))
        return self.And(*tuple(transitions))

    def join_operations(self, *transitions):
        return self.And(self.active(),
                        self.transition(*transitions))

