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
# This module defines generic expressions (Exprs). These are
# extended for use in Schema and Type constraints in other
# modules.
#
from abc import abstractmethod

from v0.relationalai.early_access.dsl.core.context import ContextStack

contextStack = ContextStack()


class Expr:

    # We can assert equality (==) between any pair of Exprs, though the
    # meaning varies depending on whether self is an ScalarExpr or
    # a RelationExpr
    #
    def __eq__(self, other): # type: ignore
        contextStack.root_context().build_comparison(self, "=", other)

    # Returns a printable form of this Expr.
    #
    @abstractmethod
    def display(self) -> str: pass

    # Returns a copy of this Expr with renaming applied to replace
    # any variable that occurs in the renaming dictionary, which is
    # keyed by the names of the variables to rename. For instance,
    # if expr had the form (x + 2), then:
    #
    #    expr.rename({"x": y})
    #
    # would have the form (y + 2)
    #
    @abstractmethod
    def rename(self, renaming) -> 'Expr': pass

    # Returns a copy of this Expr with vmap applied to replace
    # any variable that occurs in the vmap dictionary, which is
    # keyed by the identifier of the variables to revar. For
    # instance, if expr had the form (x + 2) and the entityid
    # of x was 100, then:
    #
    #    expr.revar({100: y})
    #
    # would have the form (y + 2)
    #
    @abstractmethod
    def revar(self, vmap) -> 'Expr': pass

    # Returns a dictionary of ScalarVariables referenced by this Expr,
    # with variable names (strings) as keys
    #
    def scalar_refs(self): return {}

    # Returns an integer (hash) that identifies this Expr, allowing us
    # to treat Exprs sort of like entity types for which we had declared
    # a preferred identifier so as to allow different physical objects
    # to unify to the same entity. Contrast this with the "id" method
    # which would not allow us to do this unification.
    #
    @abstractmethod
    def entityid(self) -> int: pass

    # This predicate returns True if this Expr refers to a variable
    # with this varname and False otherwise.
    #
    @abstractmethod
    def refersto(self, varname: str) -> bool: pass

    # This predicate returns True if this Expr references any kind of
    # Relation and False otherwise.
    #
    def relational(self) -> bool: return False

    # This predicate returns True if this Expr is a (scalar or relation)
    # variable and False otherwise.
    #
    def variable(self) -> bool: return False


class Wildcard(Expr):
    def __init__(self): pass

    def display(self): return "_"

    def grounded_using(self, groundings): return True

    def refersto(self, varname: str): return False

    def rename(self, renaming): return self

    def revar(self, vmap): return self

    def substitute(self, bindings): return self

    def entityid(self): return hash(Wildcard)


# Declare this variable for use in Datalog-style rules
#
_ = Wildcard()
