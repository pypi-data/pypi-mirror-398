# Copyright 2024 RelationalAI, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# A Schema is a disjunctions of SchemaFragments, each of which is a conjunction
# of predicate and propositional literals.
#
from abc import abstractmethod
from typing import Literal

from v0.relationalai.early_access.dsl.schemas.builder import SchemaBuilder
from v0.relationalai.early_access.dsl.schemas.contexts import SchemaContext, DASHES, ScalarComponent, RelationalComponent
from v0.relationalai.early_access.dsl.schemas.fragments import SchemaFragment

from sys import stderr

class AbstractSchema:

    def __init__(self): pass


class FalseSchema(AbstractSchema):

    def __init__(self):
        super().__init__()

    def display(self): return "False"

    def pprint(self): return "FALSE"


# Schema
class Schema(AbstractSchema, SchemaBuilder):

    # Each Schema object is a ContextManager
    def __enter__(self):
        SchemaContext.open(self)  # open a new context for this Schema
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        SchemaContext.close()
        self.register_attrs()

    # Construct instances of this schema with an optional set of positional
    # arguments and an optional set of keyword arguments.
    #
    # Special keyword arguments -- DASHES and PREFIX -- decorate the Schema that is
    # being constructed. Other keyword arguments denote the renaming of a component
    # using what would otherwise have been the name of the component in the Schema
    # that is being constructed. CompNames inherit these decorations and renamings
    # from context when a Set is ultimately declared using some name. We implement
    # this inheritance using renaming-, dash-, and prefix- context stacks.
    #
    # Also, each Schema instance will contain an instance variable for each of its
    # components so that contexts that use the instane may refer to the components
    # by name. To make these references safe under schema inclusion, we name the
    # variables using the context-free name of the component, which is the name
    # of the component when the Schema is instantiated at the top level (i.e.,
    # not in the context of some containing or including Schema).
    #
    def __init__(self, *args):
        super().__init__()

        self.disjuncts = []

        # Sometimes a Schema can be instantiated with parameters that are not
        # other Schemas, such as happens when we create a disjunction of the
        # evaluation or reduction of schemas that might reduce to 'None'.
        #
        (parts, params) = partition_schema_args(args)

        # Any parts should be merged in because when a Schema is instantiated with
        # other Schemas as parts, they are to be conjoined by schema inclusion.
        #
        for p in parts:
            self.merge(p)

        if len(params) > 0:
            for p in params:
                if p is not None:
                    print(f"[INFO]: Found non-Schema parameter {p} in instaniation of schema {self}", file=stderr)

        self.register_attrs()

    # Allows subclasses of Schema to generate fresh instances of the subclass
    # so that we can declare more methods here in this abstract superclass
    #
    @abstractmethod
    def _generate(self) -> 'Schema':
        pass

    # Let self be an operation schema and pre an undecorated state schema. This operation
    # returns a schema that is self reduced by constraints that are entailed by what remains
    # in self if we assume pre.
    #
    def assume_precondition(self, pre):
        new_schema: Schema = self._generate()
        for t in self.disjuncts:
            for p in pre.disjuncts:
                new_schema.disjuncts.append(t.assume_precondition(p))
        return new_schema

    def build_relation_variable(self, args, kwargs):

        dashes = kwargs[DASHES] if DASHES in kwargs else 0

        tp = args[0]
        name = args[1]

        if self.disjunctive():
            raise Exception("Cannot add a component directly to a disjunctive schema")

        return self.declare_relation(name, tp, dashes)


    def build_scalar_variable(self, args, kwargs):

        dashes = kwargs[DASHES] if DASHES in kwargs else 0

        tp = args[0]
        name = args[1]
        if self.disjunctive():
            raise Exception("Cannot add a component directly to a disjunctive schema")

        return self.declare(name, tp, dashes)


    # Causes this Schema to declare a new ScalarComponent of the given name, type,
    # and decorartion (number of dashes)
    #
    def declare(self, name, type, dashes=0):
        decl = ScalarComponent(name, type, dashes)

        self.add_component(decl)

        v = decl.basevar()
        setattr(self, v.name(), v)

        return decl

    # Causes this Schema to declare a new RelationalComponent of the given name,
    # signature, and decorartion (number of dashes)
    #
    def declare_relation(self, name, signature, dashes=0):
        decl = RelationalComponent(name, signature, dashes)

        self.add_relational_component(decl)
        v = decl.basevar()
        setattr(self, v.name(), v)

        return decl

    def decorate(self):
        new_schema = self._generate()
        for c in self.disjuncts:
            new_schema.disjuncts.append(c.decorate())
        new_schema.register_attrs()
        return new_schema

    # Given a tuple of relational vars, return a new Schema that is a duplicate
    # of self with RelationIsEmpty constraints on all v in vars
    #
    def is_empty(self, *vars):
        new_schema = self._generate()
        for c in self.disjuncts:
            new_schema.disjuncts.append(c.is_empty(*vars))
        new_schema.register_attrs()
        return new_schema

    def register_attrs(self):
        attrs = {}
        for d in self.disjuncts:
            for c in d._scalars.values():
                v = c.basevar()
                attrs[v.name()] = v
            for c in d._relations.values():
                v = c.basevar()
                attrs[v.name()] = v

        for v in attrs.values():
            setattr(self, v.name(), v)

    def constructor(self, *args):
        pass

    def disjunctive(self) -> bool:
        return False

    @abstractmethod
    def merge(self, other) -> 'Schema':
        pass

    # Let self be some operation Schema. For each dashed relation R' in self, if there
    # exists at least one AtomicConstraint involving R' in the constraints of self, we can
    # generate a (potentially recursive) Rel rule that populates R by conjoining the
    # constraints that refer either directly or indirectly to R.
    #
    def genrel(self):
        operation = []

        reduced = self.reduce()
        for s in reduced.disjuncts:
            operation.append(s.refine().pprint())
        return "\n\n".join(operation)

    # Creates a new schema by hiding variables named in args under an existential
    # quantifier. This is just a wrapper to conceal that allows users to directly
    # reference Schema instance variables when declaring Schema classes
    #
    def hide(self, *args):
        if len(args) == 0:
            raise Exception("Must name variables to hide from a schema")

        return self.conceal([var.display() for var in args])

    # Add SchemaComponent d to the declaration part of this Schema
    #
    def add_component(self, d):
        if len(self.disjuncts) == 0:
            self.disjuncts.append(SchemaFragment())

        # By default, we assume that we will need to cache component d.
        for disj in self.disjuncts:
            disj.add_component(d)

    # Add SchemaComponent d to the declaration part of this Schema
    #
    def add_relational_component(self, d):
        if len(self.disjuncts) == 0:
            self.disjuncts.append(SchemaFragment())

        # By default, we assume that we will need to cache component d.
        for disj in self.disjuncts:
            disj.add_relational_component(d)

    def add_scalar_constraint(self, c):
        if len(self.disjuncts) == 0:
            self.disjuncts.append(SchemaFragment())

        for disj in self.disjuncts:
            disj.add_scalar_constraint(c)

    def add_atomic_constraint(self, c):
        if len(self.disjuncts) == 0:
            self.disjuncts.append(SchemaFragment())

        for disj in self.disjuncts:
            disj.add_atomic_constraint(c)

    def add_predicate_constraint(self, c):
        if len(self.disjuncts) == 0:
            self.disjuncts.append(SchemaFragment())

        for disj in self.disjuncts:
            disj.add_predicate_constraint(c)

    # Returns the schema formed by concealing (hiding) variables in the list cvars
    # under an existential quantifier.
    #
    # Note: Clients typically call this method indirectly from the hide method.
    #
    def conceal(self, cvars):
        new_schema = self._generate()
        for disj in self.disjuncts:
            new_schema.disjuncts.append(disj.conceal(cvars))
        return new_schema

    # Partially evaluate this Schema by substituting statically-computable values for
    # its schema variables, simplifying where possible.
    #
    def evaluate(self, bindings):
        new_schema = self._generate()
        for disj in self.disjuncts:
            d = disj.evaluate(bindings)
            if d is not None:
                new_schema.disjuncts.append(d)

        # Check if evaluation violates some schema constraint
        if len(self.disjuncts) > 0 and len(new_schema.disjuncts) == 0:
            return FalseSchema()

        return new_schema

    # Emit this schema to a textual output using the Z display style
    #
    def pprint(self):
        declStrings = []

        declStrings.append("( ")
        disjunctStrings = []
        for disj in self.disjuncts:
            disjunctStrings.append(disj.pprint())
        declStrings.append("\n OR \n".join(disjunctStrings))
        declStrings.append(" )")
        return "\n".join(declStrings)

    def prefix(self, pref):
        new_schema = self._generate()
        for c in self.disjuncts:
            new_schema.disjuncts.append(c.prefix(pref))
        new_schema.register_attrs()
        return new_schema

    # Simplify this Schema by checking the satisfiability of its propositional
    # constraints.
    #
    def reduce(self):
        new_schema = self._generate()
        for disj in self.disjuncts:
            s = disj.reduce()
            if s is not None:
                new_schema.disjuncts.append(s)
        return new_schema

    # Simplify this Schema by projecting out decls that are equated with
    # other decls via predicate constraints. These commonly arise when
    # decorating Schemas using the Xi operator. Note that when reducing
    # we try to remove the SchemaComponent with the larger number of dashes
    # to simplify Rel rule generation.
    #
    def reduce_by_xi(self):
        new_schema = self._generate()
        for disj in self.disjuncts:
            new_schema.disjuncts.append(disj.reduce_by_xi())
        return new_schema

    # Create a new Schema by renaming this Schema's decls.
    # Each arg must be a dictionary that maps component name
    # to some compatible component.
    #
    def rename(self, *args):
        renaming = {}
        for a in args:
            renaming = renaming | a

        new_schema = self._generate()
        for disj in self.disjuncts:
            new_schema.disjuncts.append(disj.rename(renaming))
        new_schema.register_attrs()
        return new_schema

    def sync(self, *args):
        return self.rename(*args)

    # Generates the rule to populate a Rel view that materializes this
    # Schema under the given view name.
    #
    # The rule will be annotated @inline if we cannot statically
    # determine that the Schema is grounded.
    #
    def view(self, viewName):
        s = self.reduce_by_xi().reduce()
        rules = []

        for disj in s.disjuncts:
            rules.append(disj.view(viewName))

        return "\n".join(rules)


class ConjunctiveSchema(Schema):

    def __init__(self, *args):
        Schema.__init__(self, *args)

    def _generate(self): return ConjunctiveSchema()

    # Looks to see if this Schema declares a RelationComponent by this
    # name
    def has_relation_component(self, name) -> bool:
        for d in self.disjuncts:
            if name in d._relations:
                return True
        return False

    # Assuming this Schema already contains a RelationComponent by this
    # name, retrieve and return it to the caller. We use this to support
    # dynamically adding components to a schema when we see references
    # to relations that are defined in an ontology.
    #
    def retrieve_relation_component(self, name):
        for d in self.disjuncts:
            if name in d._relations:
                return d._relations[name]
        return None

    # Merge self with other, mutating self.
    #
    def merge(self, other):
        oldSelfDisjuncts = self.disjuncts
        self.disjuncts = []
        if len(oldSelfDisjuncts) >= 1:
            for d in oldSelfDisjuncts:
                for d2 in other.disjuncts:
                    d3 = d.duplicate()
                    for c in d2._scalars:
                        d3.add_component(d2._scalars[c])
                    for c in d2._relations:
                        d3.add_relational_component(d2._relations[c])
                    for c in d2._sconstraints:
                        d3.add_scalar_constraint(d2._sconstraints[c])
                    for c in d2._atoms:
                        d3.add_atomic_constraint(d2._atoms[c])
                    for c in d2._universals:
                        d3.add_predicate_constraint(d2._universals[c])
                    self.disjuncts.append(d3)
        else:
            self.disjuncts = [d.duplicate() for d in other.disjuncts]
        return self


class DisjunctiveSchema(Schema):

    def __init__(self, *args):
        Schema.__init__(self, *args)

    def _generate(self): return DisjunctiveSchema()

    def disjunctive(self) -> Literal[True]: return True

    def merge(self, other):
        for d in other.disjuncts:
            self.disjuncts.append(d)
        self.register_attrs()
        return self


# When class Schema is instantiated, other Schema instances (parts) can
# be specified, as can arbitrary arguments that are used to parameterize
# the Schema.
#
def partition_schema_args(args):
    parts = []
    params = []
    for a in args:
        if isinstance(a, Schema):
            parts.append(a)
        else:
            params.append(a)
    return (parts, params)
