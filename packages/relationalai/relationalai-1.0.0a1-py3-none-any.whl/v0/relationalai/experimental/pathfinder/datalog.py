from typing import Optional, Callable, NamedTuple, Tuple, Union, List, Dict
from v0.relationalai.dsl import Graph, create_vars
from v0.relationalai.std import rel
from v0.relationalai.metamodel import Builtins
from v0.relationalai.experimental.pathfinder.utils import get_lambda_str
from v0.relationalai.experimental.pathfinder.filter import EdgeLabel

# -----------------------------------------------------------------------------------------
# Rules and Atoms
# -----------------------------------------------------------------------------------------
# Currently, the datalog programs that we generate consist of rules with essentially
# positive conjunctive bodies. Multiple rules may use the same head, thus the rules are in
# fact disjunctions of conjunctive queries. Furthermore, rules may be recursive.
#
# A rule has a n-ary relation head `R(x₁,...,xₙ)` and uses only the following kind of atoms
# in its body:
# - `A(x₁,...,xₖ)` -- a k-ary relation, where `A` is a derived or base relation
#   name, and `x₁,...,xₖ` are variables.
# - `f(i)` or `f(i, j) -- either unary or binary anonymous unary filter atom, where `f` is a
#   unary or binary function that emits PyRel code to filter for the input variables
# - `x = y` -- an equality atom of two variables
# - `x = c` -- an equality atom of a variable and a constant (integer)
#
# For simplicity, in our representation we use consecutive integers 0, 1, ... to name
# variables in rules. As it is custom, variables that are not present in the head are
# (implicitly) existentially quantified.
#
# Examples:
# The following rule
# Rule:
# * head = RelAtom('R', (0, 3))
# * n = 4 # number of variables in the rule
# * body = [
#       RelAtom('S', (0, 1, 2)),
#       VariableEqualityAtom((1, 3)),
#       ConstantEqualityAtom((2, 105768493)),
#       AnonymousFilterAtom(lambda x, y: x < y, (0, 1))
#   ]
# represent the following Rel/Datalog rule
#
# def R(x0, x3): exists((x1, x2) | S(x0, x1, x2) and x1 = x3 and x2 = 105768493 and x0 < x1)
#
# It could be argued that the anonymous filter atoms supplant equality atoms but we keep
# them to make their use more explicit. Anonymous filter atoms will always originate from
# the anonymous filter expressions in the RPQs.
# -----------------------------------------------------------------------------------------

class RelAtom(NamedTuple):
    rel_name: str
    vars: Tuple[int,...]

    def __repr__(self):
        return f"{self.rel_name}({', '.join([f'x{v}' for v in self.vars])})"

    def to_dict(self):
        return {
            "type": "RelAtom",
            "rel_name": self.rel_name,
            "vars": list(self.vars)
        }

# FilterAtom(lambda x: x == 1, (0,)) -> {lambda x: x < 1}(x0) -> x0 < 1
class AnonymousFilterAtom(NamedTuple):
    function: Callable
    vars: Union[Tuple[int], Tuple[int, int]]

    def __repr__(self):
        return '{' + get_lambda_str(self.function) + '}(' + ', '.join([f'x{v}' for v in self.vars]) + ')'

    def to_dict(self):
        return {
            "type": "AnonymousFilterAtom",
            "function": get_lambda_str(self.function),
            "vars": list(self.vars)
        }

# VariableEqualityAtom((0, 1)) -> x0 = x1
class VariableEqualityAtom(NamedTuple):
    vars: Tuple[int, int]

    def __repr__(self):
        return f'x{self.vars[0]} = x{self.vars[1]}'

    def to_dict(self):
        return {
            "type": "VariableEqualityAtom",
            "vars": list(self.vars)
        }

# ConstantEqualityAtom((0, 1234)) -> x0 = 1234
# NOTE: Currently, we only use equality atoms in product graph definition to indicate the
# state of the automaton. Hence, logging the constant value is safe; User defined equality
# tests are encapsulated in anonymous filter atoms, which are serialized in a way that
# obscures any values (and logic) used in the filter.
class ConstantEqualityAtom(NamedTuple):
    vars: Tuple[int, int]

    def __repr__(self):
        return f'x{self.vars[0]} = {self.vars[1]}'

    def to_dict(self):
        return {
            "type": "ConstantEqualityAtom",
            "vars": list(self.vars)
        }

# Atoms used in the body of a rule
Atom = Union[
   RelAtom, AnonymousFilterAtom, VariableEqualityAtom, ConstantEqualityAtom
]

# Rule(RelAtom('R', (0, 2)), 3, [RelAtom('S', (0, 1)), VariableEqualityAtom((1, 2))])
# -> R(x0, x2) :- ∃ x1. S(x0, x1), x1 = x2
class Rule(NamedTuple):
    head: RelAtom
    n: int   # number of variables in the rule
    body: List[Atom]

    def __repr__(self):
        return f"def {self.head}:\n    " + ' ∧\n    '.join([str(a) for a in self.body])

    def to_dict(self):
        return {
            "type": "Rule",
            "head": self.head.to_dict(),
            "n": self.n,
            "body": [a.to_dict() for a in self.body]
        }

# -----------------------------------------------------------------------------------------
# Datalog Program
# -----------------------------------------------------------------------------------------
# The result of compiling a RPQ into a Datalog program, which includes:
# - `root_rel` a dictionary mapping distinguished relations to their names.
# - `rel_attrs` a dictionary mapping relation names to their attributes:
#   a possibly empty subset of {'@inline', '@no_inline', '@pipeline'}
# - `rules` a list of rules,
# - `edge_label_map` a dictionary mapping hash values to the edge labels.
# -----------------------------------------------------------------------------------------
class DatalogProgram(NamedTuple):
    root_rel: Dict[str, str]
    rel_attrs: Dict[str, List[str]]
    rules: List[Rule]
    edge_label_map: Optional[Dict[int, EdgeLabel]]

    def __repr__(self):
        return '\n'.join([str(rule) for rule in self.rules])

    def to_dict(self):
        d = {
            "type": "DatalogProgram",
            "root_rel": self.root_rel,
            "rel_attrs": self.rel_attrs,
            "rules": [rule.to_dict() for rule in self.rules],
        }
        if self.edge_label_map:
            d["edge_label_map"] = {k: v.to_dict() for k, v in self.edge_label_map.items()}
        return d

# -----------------------------------------------------------------------------------------
# Installing the compiled RPQ
# -----------------------------------------------------------------------------------------
# An RPQ is compiled into a simple Datalog program, which needs to be installed in the
# model. The program introduces a number of relations, some of which must be decorated with
# specific attributes (such as `@inline` or `@pipeline`).
# -----------------------------------------------------------------------------------------

def install_program(model: Graph, program: DatalogProgram, options):
    declare_relations(model, program)
    emit_pyrel(model, program)

def declare_relations(model: Graph, program: DatalogProgram):
    rel_names = {rule.head.rel_name for rule in program.rules}
    rel_names.update(program.rel_attrs.keys())
    rel_names.update(program.root_rel.keys())
    for rel_name in rel_names:
        declare_relation(model, rel_name, program)

def declare_relation(model, rel_name, program):
    T = model.Type("_pathfinder_dummy_type_for_predicate_declarations")
    getattr(T, rel_name).declare()
    pred = getattr(rel, rel_name)
    for kind in program.rel_attrs.get(rel_name, []):
        if kind == '@no_inline':
            pred._rel.parents.append(Builtins.NoInlineAnnotation)
        elif kind == '@inline':
            pred._rel.parents.append(Builtins.InlineAnnotation)
        elif kind == '@pipeline':
            pred._rel.parents.append(Builtins.PipelineAnnotation)
        elif kind == '@track':
            pred._rel.parents.append(Builtins.TrackConnAnnotation)
        else:
            raise ValueError(f"Invalid predicate kind {kind}")

def emit_pyrel(model: Graph, program: DatalogProgram):
    for rule in program.rules:
        if len(rule.body) == 0:
            continue
        with model.rule(dynamic=True):
            rule_vars = create_vars(rule.n)
            for atom in rule.body:
                if isinstance(atom, RelAtom):
                    getattr(rel, atom.rel_name)(*[rule_vars[v] for v in atom.vars])
                elif isinstance(atom, AnonymousFilterAtom):
                    atom.function(*[rule_vars[v] for v in atom.vars])
                elif isinstance(atom, VariableEqualityAtom):
                      rule_vars[atom.vars[0]]._wrapped_op(
                          Builtins.eq, rule_vars[atom.vars[0]], rule_vars[atom.vars[1]])
                elif isinstance(atom, ConstantEqualityAtom):
                    rule_vars[atom.vars[0]]._wrapped_op(
                        Builtins.eq, rule_vars[atom.vars[0]], atom.vars[1])
                else:
                    raise ValueError(f"Invalid atom {atom}")
            getattr(rel, rule.head.rel_name).add(*[rule_vars[v] for v in rule.head.vars])