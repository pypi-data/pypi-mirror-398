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
# This module declares a simple propositional constraint language that admits
# scalar, atomic, and predicate constraints
#
# These are used to represent both Schema- and ValueType- constraints, the
# differences being what counts for a leaf variable and the expressive power.
from abc import abstractmethod


class Constraint:

    # Returns an integer (hash) that identifies this Expr, allowing us
    # to treat Exprs sort of like entity types for which we had declared
    # a preferred identifier so as to allow different physical objects
    # to unify to the same entity. Contrast this with the "id" method
    # which would not allow us to do this unification.
    #
    @abstractmethod
    def entityid(self) -> int: pass


class TrueConstraint(Constraint):

    def __init__(self): pass

    def pprint(self): return 'true'

    def refersto(self, varname: str): return False

    def rename(self, renaming): return self

    def entityid(self):
        return hash(TrueConstraint)


class FalseConstraint(Constraint):
    def __init__(self): pass

    def pprint(self): return 'false'

    def refersto(self, varname: str): return False

    def rename(self, renaming): return self

    def entityid(self):
        return hash(TrueConstraint)


# We represent "constraint sets" as dictionaries that are keyed by the entityid
# of each constraint in the set.
#

# Returns the set difference of two constraint sets C1 and C2
#
def diffof(C1, C2):
    return {c: C1[c] for c in C1 if c not in C2}


# Returns the disjoint union of two constraint sets C1 and C2
#
def disjoint_union_of(C1, C2):
    C = C1.copy()
    for c in C2:
        if c in C1:
            raise Exception(f"Common constraint {c.pprint()} found in a disjoint union of two sets")
        C[c] = C2[c]
    return C
