from enum import Enum

from v0.relationalai.early_access.dsl.core import tempvar
from v0.relationalai.early_access.dsl.core.builders.logic import LogicBuilder
from v0.relationalai.early_access.dsl.core.exprs import contextStack
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarExprBuilder
from v0.relationalai.early_access.dsl.core.logic import LogicFragment, RelVariable
from v0.relationalai.early_access.dsl.core.logic.exists import ExistentialConstraint
from v0.relationalai.early_access.dsl.core.types import Type


class Annotation(Enum):
    FUNCTION = 1
    INLINE = 2
    ITER = 3
    INNER_LOOP = 4
    INNER_LOOP_NON_STRATIFIED = 5
    FORCE_DNF = 6

    def display(self):
        return f"@{self}"

    def __str__(self):
        return self.name.lower()


class Rule(LogicFragment, ScalarExprBuilder):

    def __enter__(self):
        contextStack.push(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        contextStack.pop()

    # Partially construct this Rule by creating a head atom and an array of free variables
    # from a Relation (rel)
    #
    def __init__(self, rel):
        LogicFragment.__init__(self)
        fvars = []
        for i in range(rel._signature.arity()):
            type = rel._signature._types[i]
            var = self.build_scalar_variable([type, tempvar(i)], {})
            fvars.append(var)

        self.head = LogicBuilder.build_atom(self, rel, fvars)
        self._populates = rel
        self._freevars = fvars
        self._annotations = []

    def annotate(self, a):
        self._annotations.append(a)
        return self

    # Elaborates the body of this rule by invoking a Python function that, when
    # supplied with the array of free variables declared by this rule will populate
    # the conjuncts that make up the body of the rule.
    #
    def elaborate(self, func):
        with self.genexists(): # type: ignore
            func(*(self.freevars()))
        return self

    def genexists(self):
        x = ExistentialConstraint.build_existential()
        self._existentials[id(x)] = x
        return x

    def freevars(self):
        return tuple(self._freevars)

    def populates(self): return self._populates

    def pprint(self):
        annotations = "\n".join([a.display() for a in self._annotations])
        head = self.head.pprint()
        body = self.rel_formula()
        rule = f"def {head}:\n{body}"
        if annotations != "":
            return annotations + "\n" + rule
        else:
            return rule

    # Returns a new Rule that duplicates self after mapping every
    # Relation referred to by an atom through relmap
    #
    def map(self, relmap):
        newrel = relmap[self.populates().entityid()]
        r = Rule(newrel)
        r._sconstraints = self._sconstraints
        r._atoms = {}
        for a in self._atoms:
            newatom = a.map(relmap)
            r._atoms[newatom.entityid()] = newatom
        r._existentials = {}
        for e in self._existentials.values():
            ext = e.map(relmap)
            r._existentials[ext.entityid()] = ext
        return r

def Vars(*args: Type):
    vars = []
    size = contextStack.size()
    for i, t in enumerate(args):
        if isinstance(t, RelVariable):
            vars.append(t)
        else:
            vars.append(t(f'_x{i}_{size}'))
    if len(vars) == 1:
        return vars[0]
    return tuple(vars)