from v0.relationalai.early_access.dsl.core.exprs import contextStack
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarExpr
from v0.relationalai.early_access.dsl.core.logic import LogicFragment


class Aggregation(LogicFragment, ScalarExpr):

    # Each Schema object is a ContextManager
    def __enter__(self):
        contextStack.push(self)  # open a new context for this Schema
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        contextStack.pop()

    def __init__(self, method):
        LogicFragment.__init__(self)
        self._method = method
        self._aggregates = None
        self._schema = self

    def aggregates(self, var):
        self._aggregates = var

    def display(self):
        vars = [v.display() for v in self._scalars.values()]

        args = ", ".join(vars)
        body = self.rel_formula()
        return f"{self._method}[" + args + ":" + body + "]"

    def grounded(self): return False

    def rename(self, renaming) -> 'Aggregation':
        new_vars = {}
        for d in self._scalars:
            dv = self._scalars[d]
            if d in renaming:
                new_vars[d] = dv.rename(renaming[d])
            else:
                new_vars[d] = dv

        renamed_agg = Aggregation(self._method)
        renamed_agg._aggregates = self._aggregates
        renamed_agg._scalars = new_vars

        renamed_agg._existentials = self._existentials
        renamed_agg._atoms = self._atoms
        renamed_agg._sconstraints = self._sconstraints

        return renamed_agg

    def pprint(self): return self.display()

    @staticmethod
    def max(var):
        return Aggregation._agg(var, "max")

    @staticmethod
    def min(var):
        return Aggregation._agg(var, "min")

    @staticmethod
    def argmax(var):
        return Aggregation._agg(var, "argmax")

    @staticmethod
    def argmin(var):
        return Aggregation._agg(var, "argmin")

    @staticmethod
    def sum(var):
        return Aggregation._agg(var, "sum")

    @staticmethod
    def count(var):
        return Aggregation._agg(var, "count")

    @staticmethod
    def _agg(var, method):
        agg = Aggregation(method)
        var == agg
        return agg

    def map_builder(self, builder):
        new_agg = Aggregation(self._method)
        new_agg._aggregates = self._aggregates
        new_agg._scalars = self._scalars
        for a in self._sconstraints.values():
            ap = a.map_builder(builder)
            new_agg._sconstraints[ap.entityid()] = ap
        for a in self._atoms.values():
            new_atom = a.map_builder(builder)
            new_agg._atoms[new_atom.entityid()] = new_atom
        for ex in self._existentials.values():
            new_ex = ex.map_builder(builder)
            new_agg._existentials[new_ex.entityid()] = new_ex
        return new_agg
