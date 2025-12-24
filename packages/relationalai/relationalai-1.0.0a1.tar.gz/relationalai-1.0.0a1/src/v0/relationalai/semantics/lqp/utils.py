from v0.relationalai.semantics.lqp import ir as lqp
from v0.relationalai.semantics.metamodel import ir
from v0.relationalai.semantics.metamodel.helpers import sanitize
from v0.relationalai.semantics.metamodel.util import FrozenOrderedSet

from hashlib import sha256
from typing import Tuple

class UniqueNames:
    def __init__(self):
        # Track count of seen names
        self.seen = dict[str, int]()
        # Maps id to unique name
        self.id_to_name = dict[int,str]()

    def get_name(self, name: str) -> str:
        # Names will eventually be sanitized, which could cause collisions, so we
        # do the sanitization here.
        name = '_' if name == '_' else sanitize(name)
        if name not in self.seen:
            self.seen[name] = 1
            return f"{name}"

        self.seen[name] += 1
        id = self.seen[name]
        # If the original name has a suffix we can get collisions with generated names,
        # so test the new name.
        while f"{name}_{id}" in self.seen:
            id += 1
            self.seen[name] = id
        new_name = f"{name}_{id}"
        self.seen[new_name] = 1
        return new_name

    # Get a unique name for the given id. If the id is already in the map, return the
    # existing name. Otherwise, generate a new name using the suggested_name and
    # store it in the map.
    def get_name_by_id(self, id: int, suggested_name:str) -> str:
        if id in self.id_to_name:
            return self.id_to_name[id]

        name = self.get_name(suggested_name)
        self.id_to_name[id] = name
        return name

class TranslationCtx:
    def __init__(self, def_names: UniqueNames = UniqueNames()):
        # TODO: comment these fields
        self.def_names = def_names
        self.var_names = UniqueNames()
        self.output_names = UniqueNames()
        # Map relation IDs to their original names for debugging and pretty printing.
        self.rel_id_to_orig_name = {}
        self.output_ids: list[tuple[lqp.RelationId, str]] = []
        self.export_ids: list[tuple[lqp.RelationId, int, lqp.Type]] = []

def gen_rel_id(ctx: TranslationCtx, orig_name: str, suffix: str = "") -> lqp.RelationId:
    relation_id = lqp.RelationId(id=lqp_hash(orig_name + suffix), meta=None)
    ctx.rel_id_to_orig_name[relation_id] = orig_name
    return relation_id

def gen_unique_var(ctx: TranslationCtx, name_hint: str) -> lqp.Var:
    """
    Generate a new variable with a unique name based on the provided hint.
    """
    name = ctx.var_names.get_name(name_hint)
    return lqp.Var(name=name, meta=None)

def is_constant(arg, expected_type):
    """
    Check if the argument is a constant of the expected type.
    """
    if isinstance(arg, ir.Literal):
        return is_constant(arg.value, expected_type)

    return isinstance(arg, expected_type)

def rename_vars_var(var: lqp.Var, var_map: dict[str, lqp.Var]) -> lqp.Var:
    return var_map.get(var.name, var)

def rename_vars_relterm(term: lqp.RelTerm, var_map: dict[str, lqp.Var]) -> lqp.RelTerm:
    if isinstance(term, lqp.Var):
        return rename_vars_var(term, var_map)
    else:
        return term  # Constants do not change

def rename_vars_term(term: lqp.Term, var_map: dict[str, lqp.Var]) -> lqp.Term:
    if isinstance(term, lqp.Var):
        return rename_vars_var(term, var_map)
    else:
        return term  # Constants do not change

def rename_vars_abstraction(abstraction: lqp.Abstraction, var_map: dict[str, lqp.Var]) -> lqp.Abstraction:
    new_vars = [(var_map.get(var.name, var), typ) for (var, typ) in abstraction.vars]
    new_value = rename_vars_formula(abstraction.value, var_map)
    return lqp.Abstraction(vars=new_vars, value=new_value, meta=abstraction.meta)

def rename_vars_formula(formula: lqp.Formula, var_map: dict[str, lqp.Var]) -> lqp.Formula:
    if isinstance(formula, lqp.Primitive):
        return lqp.Primitive(
            name=formula.name,
            terms=[rename_vars_relterm(term, var_map) for term in formula.terms],
            meta=formula.meta
        )
    elif isinstance(formula, lqp.Atom):
        return lqp.Atom(
            name=formula.name,
            terms=[rename_vars_term(term, var_map) for term in formula.terms],
            meta=formula.meta
        )
    elif isinstance(formula, lqp.RelAtom):
        return lqp.RelAtom(
            name=formula.name,
            terms=[rename_vars_relterm(term, var_map) for term in formula.terms],
            meta=formula.meta
        )
    elif isinstance(formula, lqp.Not):
        return lqp.Not(arg=rename_vars_formula(formula.arg, var_map), meta=formula.meta)
    elif isinstance(formula, lqp.Exists):
        return lqp.Exists(body=rename_vars_abstraction(formula.body, var_map), meta=None)
    elif isinstance(formula, lqp.Reduce):
        return lqp.Reduce(
            op=formula.op,
            body=rename_vars_abstraction(formula.body, var_map),
            terms=[rename_vars_term(term, var_map) for term in formula.terms],
            meta=formula.meta
        )
    elif isinstance(formula, lqp.FFI):
        return lqp.FFI(
            meta=formula.meta,
            name=formula.name,
            args=[rename_vars_abstraction(arg, var_map) for arg in formula.args],
            terms=[rename_vars_term(term, var_map) for term in formula.terms]
        )
    elif isinstance(formula, lqp.Conjunction):
        return lqp.Conjunction(
            args=[rename_vars_formula(arg, var_map) for arg in formula.args],
            meta=formula.meta
        )
    elif isinstance(formula, lqp.Disjunction):
        return lqp.Disjunction(
            args=[rename_vars_formula(arg, var_map) for arg in formula.args],
            meta=formula.meta
        )
    elif isinstance(formula, lqp.Cast):
        return lqp.Cast(
            input=rename_vars_term(formula.input, var_map),
            result=rename_vars_term(formula.result, var_map),
            meta=formula.meta,
        )
    else:
        raise NotImplementedError(f"Unknown formula type: {type(formula)}")

def lqp_hash(node: str) -> int:
    h = int.from_bytes(sha256(node.encode()).digest(), byteorder='big', signed=False)
    # Ensure it's within the 128-bit range
    return h % (2**128)

def output_names(aliases: FrozenOrderedSet[Tuple[str, ir.Value]]) -> list[str]:
    return [v[0] for v in aliases]
