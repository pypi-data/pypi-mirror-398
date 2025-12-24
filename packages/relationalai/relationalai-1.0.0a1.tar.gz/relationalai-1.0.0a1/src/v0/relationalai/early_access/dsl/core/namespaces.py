from v0.relationalai.early_access.dsl.core.exprs import contextStack


class Namespace:
    top: 'Namespace'
    std: 'Namespace'

    def __enter__(self):
        contextStack.push(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        contextStack.pop()
        pass

    def __init__(self, nm, par=None):
        self._name = nm
        self._parent = par

    def name(self):
        return self._name

    def qualified_name(self):
        if self._parent is None or self._parent == Namespace.top:
            return self.name()
        else:
            # TODO: [VAMI] We changed `::` to `__` to spead up E2E testing. We should change it back to `::` before release.
            return f"{self._parent.name()}__{self.name()}"


Namespace.top = Namespace("")
Namespace.std = Namespace("std", Namespace.top)
