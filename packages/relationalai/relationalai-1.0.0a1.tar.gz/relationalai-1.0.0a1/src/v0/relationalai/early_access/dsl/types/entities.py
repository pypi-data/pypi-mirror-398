from typing import Optional

from v0.relationalai.early_access.dsl import ExternalRelation, EntityPopulationRelation, Namespace
from v0.relationalai.early_access.dsl.core.exprs import _
from v0.relationalai.early_access.dsl.core.relations import RelationSignature, rule, EntityInstanceRelation
from v0.relationalai.early_access.dsl.core.rules import Rule, Vars
from v0.relationalai.early_access.dsl.core.types.standard import standard_value_types, Hash
from v0.relationalai.early_access.dsl.types import AbstractConcept
from v0.relationalai.early_access.dsl.core.types import Type as CoreType


class AbstractEntityType(AbstractConcept, CoreType):

    def __init__(self, model, name):
        super().__init__(model, name)
        CoreType.__init__(self, name)
        self._poprel = None

    def population(self):
        if self._poprel is None:
            self._poprel = EntityPopulationRelation(self.namespace(), self.display(), RelationSignature(self))
        return self._poprel

    def ctor_name(self): return f"^{self.display()}"

    def entity(self): return True

    def addrule(self, rule):
        relation = self.population()
        self._model._add_relation(relation)
        if not isinstance(rule, Rule):
            # Assume that rule is a Python function that, when invoked can build a rule
            rule = Rule(relation).elaborate(rule)
        relation._rules.append(rule)
        return rule

    def entity_instance_relation(self, name:str, namespace: Optional[Namespace]=None):
        rel = EntityInstanceRelation(namespace, name, RelationSignature(self))
        self._add_relation(rel)
        return rel

    @staticmethod
    def root_unconstrained_type():
        return standard_value_types['Hash']

class EntityType(AbstractEntityType):

    def __init__(self, model, nm, *args, ref_schema_name: Optional[str] = None):
        super().__init__(model, nm)
        self._domain = [*args]
        self._constructor = None
        self._ref_schema_name = ref_schema_name

    def __xor__(self, args):
        ctr = self.constructor()
        if ctr is None:
            raise Exception(
                f"Entity '{self.display()}' domain is empty or this Entity is not a subtype of another EntityType with constructor")
        return ctr(*args)

    def build_relation_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in EntityType {self.display()}")

        if len(args) > 1:
            raise Exception(f"Cannot declare type variable of EntityType {self.display()} by supplying more than a type")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for EntityType {self.display()}")

        type = args[0]
        self._domain.append(type)
        return type

    def build_scalar_variable(self, args, kwargs):
        if len(args) == 0:
            raise Exception(f"Unexpected error in EntityType {self.display()}")

        if len(args) > 1:
            raise Exception(f"Cannot declare type variable of EntityType {self.display()} by supplying more than a type")

        if len(kwargs) != 0:
            raise Exception(
                f"Cannot use keyword arguments when instantiating a type parameter for EntityType {self.display()}")

        type = args[0]
        self._domain.append(type)
        return type

    # An EntityTypeConstructor is an n-ary functional Relation that maps tuples of
    # arity (n-1) to instances of the EntityType.
    def constructor(self):
        if self._constructor is None:
            # Create a constructor function (relation) when this EntityType is created
            ctortype = self.domain().copy()
            ctortype.append(self)
            self._constructor = ExternalRelation(self.namespace(),
                                                 self.ctor_name(),
                                                 RelationSignature(*tuple(ctortype)))
        return self._constructor

    def first(self, relation):
        with self:
            @rule()
            def r(e):
                relation(e, _)

    def filtered_by(self, filter, value):
        with self:
            @rule()
            def r(e):
                v = Vars(Hash)
                #
                value(v)
                filter(e, v)

    def qualified_name(self):
        return self._name

    def domain(self):
        return self._domain

    def is_composite(self):
        return len(self._domain) > 1

    def ref_schema_name(self):
        return self._ref_schema_name

    def pprint(self):
        domain_str = ", ".join([f"x{i} in {t.display()}" for i, t in enumerate(self._domain)])
        return f"entity type {self.display()}({domain_str})"

    def __str__(self):
        return f'EntityType({self.display()})'
