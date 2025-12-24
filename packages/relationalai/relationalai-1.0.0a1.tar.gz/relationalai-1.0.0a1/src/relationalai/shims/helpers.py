from __future__ import annotations

from dataclasses import dataclass
from typing import  Iterable, Sequence as seq

from relationalai.semantics.metamodel import metamodel as mm
from relationalai.semantics.metamodel.builtins import builtins as b
from relationalai.semantics.metamodel.rewriter import NO_WALK, Walker
from relationalai.util.structures import OrderedSet


class ContainerWalker(Walker):
    """ Walker that redirects all container nodes to a common handler. """

    def enter_container(self, container: mm.Container, children: seq[mm.Node]) -> object |  None:
        return None

    def exit_container(self, container: mm.Container, children: seq[mm.Node]) -> object |  None:
        return container

    #------------------------------------------------------
    # Redirect containers to common handlers
    #------------------------------------------------------

    def enter_logical(self, logical: mm.Logical):
        return self.enter_container(logical, logical.body)

    def logical(self, logical: mm.Logical):
        return self.exit_container(logical, logical.body)

    def enter_sequence(self, sequence: mm.Sequence):
        return self.enter_container(sequence, sequence.tasks)

    def sequence(self, sequence: mm.Sequence):
        return self.exit_container(sequence, sequence.tasks)

    def enter_union(self, union: mm.Union):
        return self.enter_container(union, union.tasks)

    def union(self, union: mm.Union):
        return self.exit_container(union, union.tasks)

    def enter_match(self, match: mm.Match):
        return self.enter_container(match, match.tasks)

    def match(self, match: mm.Match):
        return self.exit_container(match, match.tasks)

    def enter_until(self, until: mm.Until):
        return self.enter_container(until, [until.check, until.body])

    def until(self, until: mm.Until):
        self.exit_container(until, [until.check, until.body])

    def enter_wait(self, wait: mm.Wait):
        return self.enter_container(wait, [wait.check])

    def wait(self, wait: mm.Wait):
        return self.exit_container(wait, [wait.check])

    def enter_loop(self, loop: mm.Loop):
        return self.enter_container(loop, [loop.body])

    def loop(self, loop: mm.Loop):
        return self.exit_container(loop, [loop.body])

    def enter_require(self, require: mm.Require):
        return self.enter_container(require, [require.domain, require.check])

    def require(self, require: mm.Require):
        return self.exit_container(require, [require.domain, require.check])

    def enter_not(self, not_: mm.Not):
        return self.enter_container(not_, [not_.task])

    def not_(self, not_: mm.Not):
        return self.exit_container(not_, [not_.task])

    def enter_exists(self, exists: mm.Exists):
        return self.enter_container(exists, [exists.task])

    def exists(self, exists: mm.Exists):
        return self.exit_container(exists, [exists.task])


class VarFinder(ContainerWalker):
    """ Find all variables used in a set of nodes. """

    def enter_container(self, container, children):
         if self.shallow:
            return NO_WALK
         return None

    def find_vars(self, node:mm.Node|Iterable[mm.Node], positive_only=False, shallow=False) -> OrderedSet[mm.Var]:
        self.vars:OrderedSet[mm.Var] = OrderedSet()
        self.positive_only = positive_only
        self.shallow = shallow
        self(node)
        return self.vars

    def enter_not(self, not_:mm.Not):
        if self.positive_only:
            return NO_WALK

    def var(self, node:mm.Var):
        self.vars.add(node)

#------------------------------------------------------
# Helper functions shared across shim modules
#------------------------------------------------------

def is_output_update(u: mm.Task) -> bool:
    return (
        isinstance(u, mm.Update) and
        len(u.args) > 0 and
        isinstance(u.args[0], mm.Var) and
        isinstance(u.args[0].type, mm.Table) and
        (u.relation is u.args[0].type or u.relation in u.args[0].type.columns)
        # In v0 all outputs, including exports, end up as v0.Output so we actually
        # don't want to limit this to just arrow results
        # u.args[0].type.uri.startswith("dataframe://")
    )

def is_main_output(u: mm.Task) -> bool:
    """ This task is an update to dataframe, and represents the main output (it has only keys, no values)."""
    return isinstance(u, mm.Update) and is_output_update(u) and isinstance(u.relation, mm.Table)
