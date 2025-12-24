from abc import abstractmethod
from typing import Union

from v0.relationalai.early_access.dsl.core.exprs.relational import RelationVariable
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarVariable
from v0.relationalai.early_access.dsl.core.relations import Relation
from v0.relationalai.early_access.dsl.core.types import Type
from v0.relationalai.early_access.dsl.schemas.exprs import Domain, Range
from v0.relationalai.early_access.dsl.core.constraints.predicate.universal import RelationalEqualityConstraint
from v0.relationalai.early_access.dsl.relations import EmptyRelation


#
# The abstract class SchemaComponent models a component that is introduced in the
# "declaration part" of a Schema
#
# Each declaration has the form:
#    v : t
# where v is a Var and t is a Type or Relation signature (arity and column types).
# The interpretation is that v is an element of Type t or has signature t.
#
class SchemaComponent:

    def __init__(self, name, dashes=0):
        self._name = name
        self._dashes:int = dashes
        self.before = None

    def basevar(self):
        if self.undecorated():
            return self

        if hasattr(self, 'before') and self.before is not None:
            return self.before.basevar()

        raise Exception("Need to extend SchemaComponent.basevar to create undecorated vars.")

    @abstractmethod
    def duplicate(self, name, t) -> 'SchemaComponent':
        pass

    @abstractmethod
    def relational(self) -> bool:
        pass

    @abstractmethod
    def typeof(self) -> Union[Type, Relation]:
        pass

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):
        return f"{self.name()} : {self.typeof().display()}"

    @abstractmethod
    def prefix(self, pref) -> 'SchemaComponent':
        pass

    def display_name(self):
        return self.name()

    def entityid(self):
        return hash(self.name())

    def decorated(self) -> bool:
        return self._dashes > 0

    def name(self):
        nm = self._name if isinstance(self._name, str) else self._name.display()
        return nm + self._dashes * "'"

    def sync_with(self, peer):
        return {self.name(): peer}

    def undash(self):
        if self._dashes > 0:
            return self.before
        return self

    def undecorated(self) -> bool:
        return self._dashes == 0


class RelationEmptyConstraint(RelationalEqualityConstraint):

    def __init__(self, left, sig):
        super().__init__(left, EmptyRelation(sig))


class RelationalComponent(RelationVariable, SchemaComponent):

    def __init__(self, name, t, dashes=0):
        super().__init__(name, dashes)
        self.relation = t
        if dashes < 2:
            self.after = RelationalComponent(name, t, dashes + 1)
            self.after.before = self

    def arity(self):
        return self.relation.arity()

    def display(self):
        return self.name()

    def domain(self):
        return Domain(self)

    def duplicate(self, name, t) -> 'RelationalComponent':
        return RelationalComponent(name, t, self._dashes)

    def empty(self):
        return RelationEmptyConstraint(self, self.relation)

    def entityid(self):
        return SchemaComponent.entityid(self)

    def prefix(self, pref):
        comp = RelationalComponent(prefix_concat(pref, self._name), self.relation)
        for i in range(self._dashes):
            comp = comp.after
        return comp

    def range(self):
        return Range(self)

    def rename(self, renaming):
        vname = self.display()
        if vname in renaming:
            var = renaming[vname]
            if isinstance(var, str):
                return RelationalComponent(var, self.relation, self._dashes)
            return var
        else:
            return self

    def refersto(self, varname: str):
        return self.display() == varname

    def relational(self) -> bool:
        return True

    def typeof(self):
        return self.relation

    def substitute(self, bindings):
        vname = self.display()
        if vname in bindings:
            return bindings[vname]
        else:
            return self


class ScalarComponent(ScalarVariable, SchemaComponent):

    def __init__(self, name, t, dashes=0):
        super().__init__(name, dashes)
        self._scalartype = t
        if dashes < 2:
            newcomp = ScalarComponent(name, t, dashes + 1)
            newcomp.before = self
            self.after = newcomp

    def entityid(self):
        return SchemaComponent.entityid(self)

    def prefix(self, pref):
        comp = ScalarComponent(prefix_concat(pref, self._name), self._scalartype)
        for i in range(self._dashes):
            comp = comp.after
        return comp

    def physical_typeof(self):
        return self._scalartype.root_unconstrained_type()

    def typeof(self):
        return self._scalartype

    def display(self):
        return self.name()

    def duplicate(self, name, t) -> 'ScalarComponent':
        return ScalarComponent(name, t, self._dashes)

    def rename(self, renaming):
        vname = self.display()
        if vname in renaming:
            var = renaming[vname]
            if isinstance(var, str):
                return ScalarComponent(var, self._scalartype, self._dashes)
            return var
        else:
            return self

    def simplify(self):
        return self


def prefix_concat(s1, s2):
    if not s1:
        return s2
    if not s2:
        return s1
    return s1 + s2[0].capitalize() + s2[1:]
