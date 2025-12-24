from v0.relationalai.early_access.dsl.core.builders.logic import LogicBuilder
from v0.relationalai.early_access.dsl.core.constraints.predicate.universal import RelationalEqualityConstraint
from v0.relationalai.early_access.dsl.core.exprs import contextStack
from v0.relationalai.early_access.dsl.core.exprs.scalar import ScalarExprBuilder
from v0.relationalai.early_access.dsl.core.types.constrained import ConstrainedValueType
from v0.relationalai.early_access.dsl.constants import PRIME, DASHES
from v0.relationalai.early_access.dsl.schemas.components import RelationalComponent, ScalarComponent
from v0.relationalai.early_access.dsl.types.entities import AbstractEntityType


def remove_prefix(nm, prefix):
    lpref = len(prefix)
    if lpref == 0 or not nm.startswith(prefix):
        return nm
    else:
        truncated = nm[lpref:]
        if len(truncated) == 1:
            return truncated.lower()
        else:
            newstr = truncated[0].lower() + truncated[1:]
            return newstr


def extract_name(nm, dashes, prefix):
    dash_suffix = dashes * PRIME
    index = nm.rfind(dash_suffix)
    if index == -1:
        return remove_prefix(nm, prefix)
    else:
        return remove_prefix(nm[0:index], prefix)


def properly_decorated_name(nm, dashes, prefix):
    if dashes != 0:
        dash_suffix = dashes * PRIME
        if nm.rfind(dash_suffix) == -1:
            return False
    return nm.startswith(prefix)


class SchemaContext(LogicBuilder, ScalarExprBuilder):

    @staticmethod
    def close():
        contextStack.pop()

    @staticmethod
    def open(schema):
        ctx = SchemaContext(schema)
        contextStack.push(ctx)
        return ctx

    def __init__(self, schema):
        self.schema = schema

    def build_atom(self, rel, args):
        s = self.schema
        atom = s.build_atom(rel, args)
        s.add_atomic_constraint(atom)
        return atom

    def build_comparison(self, left, op, right):
        s = self.schema
        if left.relational():
            if not right.relational() or op != "=":
                bad_expr = f"{left.display()} {op} {right.display()}"
                raise Exception(
                    f"Currently cannot declare anything other than equality constraints on relations. Saw {bad_expr}")
            c = RelationalEqualityConstraint(left, right)
            s.add_predicate_constraint(c)
            return c
        else:
            c = s.build_comparison(left, op, right)
            s.add_scalar_constraint(c)
            return c

    def build_element_of(self, e, set):
        s = self.schema
        s.add_atomic_constraint(s.build_element_of(e, set))

    def build_scalar_variable(self, args, kwargs):

        dashes = kwargs[DASHES] if DASHES in kwargs else 0

        tp = args[0]
        nameorvar = args[1]
        if isinstance(nameorvar, str):
            name = nameorvar

            if self.schema.disjunctive():
                raise Exception("Cannot add a component directly to a disjunctive schema")

            decl = ScalarComponent(name, tp, dashes)
            self.schema.add_component(decl)
            return decl
        else:
            if isinstance(tp, AbstractEntityType):
                rel = tp.population()
                relname = rel.qualified_name()
                ctx = self.schema
                if ctx.has_relation_component(relname):
                    comp = ctx.retrieve_relation_component(relname)
                else:
                    # Then add a new component for this relation to the
                    # schema that is under construction
                    #
                    # todo: figure out if we use `build_scalar_variable` at all
                    comp = rel.signature(relname) # type: ignore

                # Now assert the atom
                comp(nameorvar)
            else:
                raise Exception(f"Illegal to range over the population of infinite type {tp.display()}")

    def build_relation_variable(self, args, kwargs):

        dashes = kwargs[DASHES] if DASHES in kwargs else 0

        tp = args[0]

        # [REKS] Very subtle. This is needed because when tp is a ConstrainedValueType,
        #        this method will be called. Correct during type analysis, but incorrect
        #        during Schema declaration
        #
        if isinstance(tp, ConstrainedValueType):
            return self.build_scalar_variable(args, kwargs)

        nameorvar = args[1]
        if isinstance(nameorvar, str):
            name = nameorvar

            if self.schema.disjunctive():
                raise Exception("Cannot add a component directly to a disjunctive schema")

            decl = RelationalComponent(name, tp, dashes)

            self.schema.add_relational_component(decl)
            return decl
        else:
            if isinstance(tp, AbstractEntityType):
                rel = tp.population()
                relname = rel.qualified_name()
                ctx = self.schema
                if ctx.has_relation_component(relname):
                    comp = ctx.retrieve_relation_component(relname)
                else:
                    # Then add a new component for this relation to the
                    # schema that is under construction
                    #
                    # todo: figure out if we use `build_relation_variable` at all
                    comp = rel.signature(relname) # type: ignore

                # Now assert the atom
                comp(nameorvar)
            else:
                raise Exception(f"Illegal to range over the population of infinite type {tp.display()}")
