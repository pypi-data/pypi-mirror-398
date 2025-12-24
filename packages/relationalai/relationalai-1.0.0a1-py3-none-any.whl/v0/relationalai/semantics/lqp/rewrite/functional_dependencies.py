from __future__ import annotations
from typing import Optional, Sequence
from v0.relationalai.semantics.internal import internal
from v0.relationalai.semantics.metamodel.ir import (
    Node, Require, Logical, Var, Relation, Lookup, ScalarType
)
from v0.relationalai.semantics.metamodel import builtins


"""
Helper functions for converting `Require` nodes with unique constraints to functional
dependencies. The main functionalities provided are:
    1. Check whether a `Require` node is a valid unique constraint representation
    2. Represent the uniqueness constraint as a functional dependency
    3. Check if the functional dependency is structural i.e., can be represented with
         `@function(k)` annotation on a single relation.

=========================== Structure of unique constraints ================================
A `Require` node represents a _unique constraint_ if it meets the following criteria:
 * the `Require` node's `domain` is an empty `Logical` node
 * the `Require` node's `checks` has a single `Check` node
 * the single `Check` node has `Logical` task that is a list of `Lookup` tasks
 * precisely one `Lookup` task in the `Check` uses the `unique` builtin relation name
 * the `unique` lookup has precisely one argument, which is a `TupleArg` or a `tuple`
   containing at least one `Var`
 * all `Lookup` nodes use variables only (no constants)
 * the variables used in the `unique` lookup are a subset of the variables used in other
   lookups
============================================================================================

We use the following unique constraint as the running example.

```
Require
  domain
    Logical
  checks:
    Check
      check:
        Logical
          Person(person::Person)
          first_name(person::Person, firstname::String)
          last_name(person::Person, lastname::String)
          unique((firstname::String, lastname::String))
      error:
        ...
```

=========================== Semantics of unique constraints ================================
A unique constraint states that the columns declared in the `unique` predicate must be
unique in the result of the conjunctive query consisting of all remaining predicates.
============================================================================================

In the running example, the conjunctive query computes a table with 3 columns, the person id
`person::Person`, the first name `firstname::String`, and the last name `lastname::String`.
The uniqueness predicate `unique((firstname::String, lastname::String))` states that no person
can have more than a single combination of first and last name.

The unique constraint in the running example above corresponds to the following functional
dependency.

```
Person(x) ∧ first_name(x, y) ∧ last_name(x, z): {y, z} -> {x}
```

------------------------------ Redundant Type Atoms ----------------------------------------
At the time of writing, PyRel does not yet remove redundant unary atoms. For instance, in
the running example, the atom `Person(person::Person)` is redundant because the type of the
`person` variable is specified in the other two atoms `first_name` and `last_name`.
Consequently, we identify redundant atoms and remove them from the definition of the
corresponding functional dependency.

Formally, a _guard_ atom is any `Lookup` node whose relation name is not `unique`. Now, a
unary guard atom `T(x::T)` is _redundant_ if the uniqueness constraint has a non-unary guard
atom `R(...,x::T,...)`.

================================ Normalized FDs ============================================
Now, the _(normalized)_ functional dependency_ corresponding to a unique constraint is an
object of the form `φ: X → Y`, where :
 1. `φ` is the set of all non-redundant guard atoms.
 2. `X` is the set of variables used in the `unique` atom
 3. `Y` is the set of all other variables used in the constraint
============================================================================================

The normalized functional dependency corresponding to the unique constraints from the running
example is :
```
first_name(person::Person, firstname::String) ∧ last_name(person::Person, lastname::String): {firstname:String, lastname:String} -> {person:Person}
```
Note that the unary atom `Person(person::Person)` is redundant and thus omitted from the
decomposition.

Some simple functional dependencies can, however, be expressed simply with `@function(k)`
attribute of a single relation.  Specifically, a functional dependency `φ: X → Y` is
_structural_ if φ consists of a single atom `R(x1,...,xm,y1,...,yk)` and `X = {x1,...,xm}`.
"""

#
# Checks that an input `Require` node is a valid unique constraint. Returns `None` if not.
# If yes, we return the decomposition of the unique constraint as a tuple
# `(all_vars, unique_vars, guard)`, where
# - `all_vars` is the list of all variables used in the constraint
# - `unique_vars` is the list of variables used in the `unique` atom
# - `guard` is the list of all other `Lookup` atoms
#
def _split_unique_require_node(node: Require) -> Optional[tuple[list[Var], list[Var], list[Lookup]]]:
    if not isinstance(node.domain, Logical):
        return None
    if len(node.domain.body) != 0:
        return None
    if len(node.checks) != 1:
        return None
    check = node.checks[0]
    if not isinstance(check.check, Logical):
        return None

    unique_atom: Optional[Lookup] = None
    guard: list[Lookup] = []
    for task in check.check.body:
        if not isinstance(task, Lookup):
            return None
        if task.relation.name == builtins.unique.name:
            if unique_atom is not None:
                return None
            unique_atom = task
        else:
            guard.append(task)

    if unique_atom is None:
        return None

    # collect variables
    all_vars: list[Var] = []
    for lookup in guard:
        for arg in lookup.args:
            if not isinstance(arg, Var):
                return None
            if arg in all_vars:
                continue
            all_vars.append(arg)

    unique_vars: list[Var] = []
    if len(unique_atom.args) != 1:
        return None
    if not isinstance(unique_atom.args[0], (internal.TupleArg, tuple)):
        return None
    if len(unique_atom.args[0]) == 0:
        return None
    for arg in unique_atom.args[0]:
        if not isinstance(arg, Var):
            return None
        if arg in unique_vars:
            return None
        unique_vars.append(arg)

    # check that unique vars are a subset of other vars
    if not set(unique_vars).issubset(set(all_vars)):
        return None

    return list(all_vars), list(unique_vars), guard


def is_valid_unique_constraint(node: Require) -> bool:
    """
    Checks whether the input `Require` node is a valid unique constraint. See description at
    the top of the file for details.
    """
    return _split_unique_require_node(node) is not None

#
# A unary guard atom `T(x::T)` is redundant if the constraint contains a non-unary atom
# `R(...,x::T,...)`.  We discard all redundant guard atoms in the constructed fd.
#
def normalized_fd(node: Require) -> Optional[FunctionalDependency]:
    """
    If the input `Require` node is a uniqueness constraint, constructs its reduced
    functional dependency `φ: X -> Y`, where `φ` contains all non-redundant guard atoms,
    `X` are the variables used in the `unique` atom, and `Y` are the remaining variables.
    Returns `None` if the input node is not a valid uniqueness constraint.
    """
    parts = _split_unique_require_node(node)
    if parts is None:
        return None
    all_vars, unique_vars, guard_atoms = parts

    # remove redundant lookups
    redundant_guard_atoms: list[Lookup] = []
    for atom in guard_atoms:
        # the atom is unary A(x::T)
        if len(atom.args) != 1:
            continue
        var = atom.args[0]
        assert isinstance(var, Var)
        # T is a scalar type (which includes entity types)
        var_type = var.type
        if not isinstance(var_type, ScalarType):
            continue
        # the atom is a entity typing T(x::T) i.e., T = A (and hence not a Boolean property)
        var_type_name = var_type.name
        rel_name = atom.relation.name
        if rel_name != var_type_name:
            continue
        # Found an atom of the form T(x::T)
        # check if there is another atom R(...,x::T,...)
        for typed_atom in guard_atoms:
            if len(typed_atom.args) == 1:
                continue
            if var in typed_atom.args:
                redundant_guard_atoms.append(atom)
                break

    guard = [atom for atom in guard_atoms if atom not in redundant_guard_atoms]
    keys = unique_vars
    values = [v for v in all_vars if v not in keys]

    return FunctionalDependency(guard, keys, values)

class FunctionalDependency:
    """
    Represents a functional dependency of the form `φ: X -> Y`, where
     - `φ` is a set of `Lookup` atoms
     - `X` and `Y` are disjoint and covering sets of variables used in `φ`
    """
    def __init__(self, guard: Sequence[Lookup], keys: Sequence[Var], values: Sequence[Var]):
        self.guard = tuple(guard)
        self.keys = tuple(keys)
        self.values = tuple(values)
        assert set(self.keys).isdisjoint(set(self.values)), "Keys and values must be disjoint"

        # for structural fd check
        self._is_structural:bool = False
        self._structural_relation:Optional[Relation] = None
        self._structural_rank:Optional[int] = None

        self._determine_is_structural()

    # A functional dependency `φ: X → Y` is _k-functional_ if `φ` consists of a single atom
    # `R(x1,...,xm,y1,...,yk)` and `X = {x1,...,xm}`. Not all functional dependencies are
    # k-functional. For instance, `R(x, y, z): {y, z} → {x}` cannot be expressed with
    # `@function`. neither can `R(x, y) ∧ P(x, z) : {x} → {y, z}`.
    def _determine_is_structural(self):
        if len(self.guard) != 1:
            self._is_structural = False
            return
        atom = next(iter(self.guard))
        atom_vars = atom.args
        if len(atom_vars) <= len(self.keys): # @function(0) provides no information
            self._is_structural = False
            return
        prefix_vars = atom_vars[:len(self.keys)]
        if set(prefix_vars) != set(self.keys):
            self._is_structural = False
            return
        self._is_structural = True
        self._structural_relation = atom.relation
        self._structural_rank = len(atom_vars) - len(self.keys)

    @property
    def is_structural(self) -> bool:
        """
        Whether the functional dependency is functional, i.e., can be represented
        with `@function(k)` annotation on a single relation.
        """
        return self._is_structural

    @property
    def structural_relation(self) -> Relation:
        """
        The structural relation of a functional dependency. Raises ValueError if the functional
        dependency is not structural.
        """
        if not self._is_structural:
            raise ValueError("Functional dependency is not structural")
        assert self._structural_relation is not None
        return self._structural_relation

    @property
    def structural_rank(self) -> int:
        """
        The structural rank k of k-structural fd. Raises ValueError if the structural
        dependency is not k-structural.
        """
        if not self._is_structural:
            raise ValueError("Functional dependency is not structural")
        assert self._structural_rank is not None
        return self._structural_rank

    def __str__(self) -> str:
        guard_str = " ∧ ".join([str(atom) for atom in self.guard]).strip()
        keys_str = ", ".join([str(var) for var in self.keys]).strip()
        values_str = ", ".join([str(var) for var in self.values]).strip()
        return f"{guard_str}: {{{keys_str}}} -> {{{values_str}}}"

def contains_only_declarable_constraints(node: Node) -> bool:
    """
    Checks whether the input `Logical` node contains only `Require` nodes annotated with
    `declare_constraint`.
    """
    if not isinstance(node, Logical):
        return False
    if len(node.body) == 0:
        return False
    for task in node.body:
        if not isinstance(task, Require):
            return False
        if not is_declarable_constraint(task):
            return False
    return True

def is_declarable_constraint(node: Require) -> bool:
    """
    Checks whether the input `Require` node is annotated with `declare_constraint`.
    """
    return builtins.declare_constraint_annotation in node.annotations
