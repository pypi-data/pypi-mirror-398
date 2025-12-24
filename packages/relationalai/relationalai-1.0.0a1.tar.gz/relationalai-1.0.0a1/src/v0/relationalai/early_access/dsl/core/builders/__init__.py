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
# This module declares various kinds of logic builders, many of which
# must be accessed via facades in order to break circular dependencies
# among core classes. We declare the abstract builders here and their
# concrete main
#
from abc import abstractmethod

from v0.relationalai.early_access.dsl.core.exprs import Expr


# We use ExprBuilders to build instances of Expr objects
#
class ExprBuilder:

    @abstractmethod
    def build_divide(self, left, right) -> Expr: pass

    @abstractmethod
    def build_plus(self, left, right) -> Expr: pass

    @abstractmethod
    def build_minus(self, left, right) -> Expr: pass

    @abstractmethod
    def build_modulus(self, left, right) -> Expr: pass

    @abstractmethod
    def build_negate(self, expr) -> Expr: pass

    @abstractmethod
    def build_times(self, left, right) -> Expr: pass


