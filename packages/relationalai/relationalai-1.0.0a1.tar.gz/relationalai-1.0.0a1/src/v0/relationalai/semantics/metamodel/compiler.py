from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Iterable, Sequence as PySequence, Union

from v0.relationalai import debugging
from v0.relationalai.semantics.metamodel import ir, visitor
from v0.relationalai.semantics.metamodel.util import OrderedSet, ordered_set, group_by



@dataclass(frozen=True)
class Compiler():
    """ Compilers can rewrite a model into a different model, and can compile a model into
    a String, usually of a different language like Rel or SQL. """
    # configurable sequence of passes
    passes: list[Pass]

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        """ Apply a sequence of transformation passes over a model, creating a new model. """
        with debugging.span("passes") as span:
            for p in self.passes:
                with debugging.span(p.name) as span:
                    model = p.rewrite(model, options)
                    span["metamodel"] = str(model.root)
                p.reset()
        return model

    def compile(self, model: ir.Model, options:dict={}) -> Any:
        return self.compile_inner(model, options)[0]

    def compile_inner(self, model: ir.Model, options:dict={}) -> tuple[Any, ir.Model]:
        model = self.rewrite(model, options)
        return self.do_compile(model, options), model

    def do_compile(self, model: ir.Model, options:dict={}) -> Any:
        """ Perform the compilation from model to string. The default implementation simply
        pretty prints the model IR. """
        return ir.node_to_string(model)


@dataclass
class Pass():
    """
    A compiler rewrite pass.
    """
    @property
    def name(self):
        return self.__class__.__name__

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        raise NotImplementedError(f"{self.name} rewrite not implemented")

    def reset(self):
        pass

# TODO - maybe extract these into a compiler_utils module?

def group_tasks(tasks: PySequence[ir.Task], categories: dict[str, Union[type, tuple[type, ...]]]) -> dict[str, OrderedSet[ir.Task]]:
    """ Categorize these tasks in these categories, based on their types. The categories
    dict contains a category name to the set of types that should be in this category. The
    result is a dict from that name to the Tasks in that category. There is a special
    "other" category for uncategorized tasks. """
    def categorize(n):
        for category, types in categories.items():
            if isinstance(n, types):
                return category
        return "other"

    groups = group_by(tasks, lambda t: categorize(t))
    # ensure all categories have an entry
    for key in categories:
        if key not in groups:
            groups[key] = ordered_set()
    if "other" not in groups:
            groups["other"] = ordered_set()
    return groups


@dataclass(frozen=True)
class VarMap:
    """ Maintain a map from variables in the original metamodel to the corresponding
    variables in the rewritten metamodel. """
    mapping: dict[ir.Var, ir.Var] = field(default_factory=dict)

    def get(self, v: ir.Var) -> ir.Var:
        if v not in self.mapping:
            self.mapping[v] = ir.Var(v.type, v.name)
        return self.mapping[v]

    def get_many(self, vars: Iterable[ir.Var]) -> list[ir.Var]:
        return [self.get(v) for v in vars]

    def __contains__(self, var: ir.Var):
        return var in self.mapping


@dataclass
class ReplaceVars(visitor.Rewriter):
    """ A pass that replaces variables found with the mapping from the VarMap. """
    varmap: VarMap = field(init=True)

    def handle_var(self, node: ir.Var, parent: ir.Node, ctx:Optional[Any]=None):
        if node in self.varmap:
            return self.varmap.get(node)
        return node

@dataclass
class DumpModel(Pass):
    """ A pass that dumps the model, verbosely. """
    header: str = field(init=True, default="")

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        if self.header:
            print("-" * 80)
            print(self.header)
            print()
        ir.dump(model)
        print()
        return model

@dataclass
class PrintModel(Pass):
    """ A pass that prints the model. """
    header: str = field(init=True, default="")

    def rewrite(self, model: ir.Model, options:dict={}) -> ir.Model:
        if self.header:
            print("-" * 80)
            print(self.header)
            print()
        print(model)
        print()
        return model
