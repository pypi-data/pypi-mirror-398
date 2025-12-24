from __future__ import annotations
from typing import Union
import textwrap
import uuid
import time

from v0.relationalai.semantics.snowflake import Table
from v0.relationalai.semantics import std
from v0.relationalai.semantics.internal import internal as b
from v0.relationalai.semantics.rel.executor import RelExecutor
from v0.relationalai.semantics.lqp.executor import LQPExecutor
from v0.relationalai.tools.constants import DEFAULT_QUERY_TIMEOUT_MINS
from v0.relationalai.util.timeout import calc_remaining_timeout_minutes

from .common import make_name
from v0.relationalai.experimental.solvers import Solver

_Any = Union[b.Producer, str, float, int]
_String = Union[b.Producer, str]
_Number = Union[b.Producer, float, int]

class SolverModelDev:
    def __init__(self, model: b.Model, num_type: str):
        self._model = model
        assert num_type in ("cont", "int")
        data_type = "int" if num_type == "int" else "float"
        self._data_type = data_type
        self._variable_relationships = set()
        self._expr_id = 0
        Relationship = model.Relationship

        # TODO workaround for QB not distinguishing string names for Concepts/Relationships, only a problem with raw Rel for result extraction maybe
        sm_id = next(b._global_id)
        def _name(s: str) -> str:
            return f"{s}_{sm_id}"

        # variable relations
        self.variables = Relationship("{node} is variable", short_name=_name("variables"))
        self.variable_type = Relationship("{node} has {type:str}", short_name=_name("variable_type")) # TODO use codes/enum
        self.variable_name = Relationship("{node} has {name:str}", short_name=_name("variable_name"))
        self.variable_start = Relationship(f"{{node}} has {{start:{data_type}}}", short_name=_name("variable_start"))

        # expression relations
        self.operator = Relationship("{node} has {op:str}", short_name=_name("operator")) # TODO use codes/enum
        self.ordered_args_hash = Relationship("{node} arg {i:int} is {arg}", short_name=_name("ordered_args_hash"))
        self.ordered_args_data = Relationship(f"{{node}} arg {{i:int}} is {{arg:{data_type}}}", short_name=_name("ordered_args_data"))
        self.unordered_args_hash = Relationship("{node} arg {i} is {arg}", short_name=_name("unordered_args_hash"))
        self.min_objectives = Relationship("{node} is min objective", short_name=_name("min_objectives"))
        self.max_objectives = Relationship("{node} is max objective", short_name=_name("max_objectives"))
        self.constraints = Relationship("{node} is constraint", short_name=_name("constraints"))
        self.expression_name = Relationship("{node} has {name:str}", short_name=_name("expression_name")) # TODO use codes/enum

        # solver result relations
        self.result_info = model.Relationship("{key:str} has {val:str}", short_name=_name("result_info"))
        self.point = model.Relationship(f"{{var}} has {{point:{data_type}}}", short_name=_name("point"))
        self.points = model.Relationship(f"point {{i:int}} for {{var}} has {{point:{data_type}}}", short_name=_name("points"))
        # self.objective_values = model.Relationship(f"point {{i:int}} has objective value {{val:{data_type}}}", short_name=_name("objective_values"))
        # self.primal_statuses = model.Relationship("point {i:int} has primal status {status:str}", short_name=_name("primal_statuses"))

        self._model_info = {
            "num_variables": self.variables,
            "num_constraints": self.constraints,
            "num_min_objectives": self.min_objectives,
            "num_max_objectives": self.max_objectives,
        }

    # TODO(coey) assert that it is a property? not just a relationship.
    def solve_for(self, expr, where: list = [], populate: bool = True, **kwargs):
        if isinstance(expr, b.Fragment):
            # TODO(coey) remove in future
            raise ValueError("select fragment argument to `solve_for` is deprecated; instead use `where = [conditions...]` kwarg to specify optional grounding conditions")
        elif isinstance(expr, b.Expression):
            # must be of the form rel(a, ..., x) where the last element is the decision variable
            rel = expr._op
            assert isinstance(rel, b.Relationship)
            params = expr._params
        elif isinstance(expr, b.Relationship):
            rel = expr
            params = [b.field_to_type(self._model, f) for f in rel._fields]
        else:
            raise ValueError(f"Invalid expression type {type(expr)} for `solve_for`")
        assert len(params) == len(rel._fields)
        assert rel not in self._variable_relationships

        self._variable_relationships.add(rel)
        node = b.Hash.ref()
        defs = [self.variables(node)]

        # handle optional variable properties
        new_kwargs = kwargs.copy()
        if "type" not in new_kwargs:
            new_kwargs["type"] = "cont" if self._data_type == "float" else "int"
        for (key, val) in new_kwargs.items():
            if key == "name":
                assert isinstance(val, _Any) or isinstance(val, list), f"Expected {key} to be a value or list, got {type(val)}"
                defs.append(self.variable_name(node, make_name(val)))
            elif key == "type":
                assert val in ("cont", "int", "bin"), f"Unsupported variable type {val} for `solve_for`; must be cont, int, or bin"
                defs.append(self.variable_type(node, val))
            elif key in ("lower", "upper", "fixed", "start"):
                assert isinstance(val, _Number), f"Expected {key} to be a number, got {type(val)}"
                if key == "start":
                    defs.append(self.variable_start(node, val))
                else:
                    # TODO use lower/upper/fixed tables in future rather than making constraints
                    op = ">=" if key == "lower" else ("<=" if key == "upper" else "=")
                    self.satisfy(b.require(b.Expression(b.Relationship.builtins[op], rel, val)).where(*where))
            else:
                raise ValueError(f"Invalid keyword argument {key} for `solve_for`")
        b.define(*defs).where(*where, _make_hash((rel._short_name, rel._parent or 0), node))

        if populate:
            # get variable values from the result point (populated by the solver)
            # TODO maybe instead delete/insert into variable relationships after solve.
            val = b.Number.ref()
            b.define(rel(val)).where(self.point(node, val), *where)

        return None

    def minimize(self, expr, name: _String | list | None = None):
        return self._handle_expr(self.min_objectives, expr, name)

    def maximize(self, expr, name: _String | list | None = None):
        return self._handle_expr(self.max_objectives, expr, name)

    def satisfy(self, expr: b.Fragment, check: bool = False, name: _String | list | None = None):
        assert expr._require, "Fragment input for `satisfy` must have a require clause"
        assert not expr._select and not expr._define, "Fragment input for `satisfy` must not have a select or define clause"
        if not check:
            # remove the `require` from the model roots so it is not checked
            b._remove_roots([expr])
        for req in expr._require:
            self._handle_expr(self.constraints, req, name, where=expr._where)
        return None

    def _handle_expr(self, root_type, expr, name: _String | list | None, where: list = []):
        ctx = ExprContext(self)
        ctx.where.extend(where)
        root = _rewrite(expr, ctx)
        assert root is not None, f"Cannot symbolify {expr}"
        ctx.define.append(root_type(root))
        # if name is not None:
        #     # TODO not printing expression names yet, so skip for now
        #     assert isinstance(name, (_String, list)), f"Expected name to be a string or list, got {type(name)}"
        #     ctx.define.append(self.expression_name(root, make_name(name)))
        self._handle_ctx(ctx)
        return None

    def _handle_ctx(self, ctx: ExprContext, where: list = []):
        all_where = ctx.where + where
        b.define(*ctx.define).where(*all_where)
        for subctx in ctx.subcontext:
            self._handle_ctx(subctx, where=all_where)

    # print the variables and components of the model in human-readable format
    def print(self, verbose: bool = True, expr_names: bool = False):
        # summarize variables
        var_types = ["int", "bin", "cont"]
        vi = b.Hash.ref()
        var_counts = b.select(*[b.count(vi).where(self.variable_type(vi, t)) | 0 for t in var_types]).to_df()
        assert var_counts.shape == (1, 3)
        (int_count, bin_count, cont_count) = var_counts.iloc[0]

        # summarize expressions
        expr_types = [
            (self.min_objectives, "Minimization objectives"),
            (self.max_objectives, "Maximization objectives"),
            (self.constraints, "Constraints"),
        ]
        ei = b.Hash.ref()
        expr_counts = b.select(*[b.count(ei).where(E(ei)) | 0 for (E, _) in expr_types]).to_df()
        assert expr_counts.shape == (1, 3)
        (min_count, max_count, cons_count) = expr_counts.iloc[0]

        # print summary
        print("Solver model has:")
        print(f"• {int_count} integer variables, {bin_count} binary variables, {cont_count} continuous variables")
        print(f"• {min_count} minimization objectives, {max_count} maximization objectives, {cons_count} constraints")
        if not verbose:
            return None

        # print variable names
        vn, vt = b.String.ref(), b.String.ref()
        var_names = b.select(vn.alias("name"), vt.alias("type")).where(self.variable_name(vi, vn), self.variable_type(vi, vt)).to_df()
        assert not var_names.empty, "No variable names found in the model"
        print("Variables:")
        print(var_names.to_string(index=False, header=True))

        # print expressions TODO print expression names optionally
        for (E, s) in expr_types:
            expr_strings = self._expr_strings(E)
            if expr_strings:
                print(s + ":")
                print("\n".join(expr_strings))
        return None

    def _expr_strings(self, roots):
        # materialize data
        iv = b.Hash.ref()
        roots_df = b.select(iv).where(roots(iv)).to_df()
        if roots_df.empty:
            return []
        nodes = roots_df.iloc[:, 0].tolist()

        sv = b.String.ref()
        names_dict = {k: v for k, v in b.select(iv, sv).where(self.variable_name(iv, sv))}
        ops_dict = {k: v for k, v in b.select(iv, sv).where(self.operator(iv, sv))}

        args_dict = {}
        iv2 = b.Hash.ref()
        iv3 = b.Hash.ref()
        # unordered args
        for k, _, v in b.select(iv, iv2, iv3).where(self.unordered_args_hash(iv, iv2, iv3)):
            if k not in args_dict:
                args_dict[k] = []
            args_dict[k].append(v)
        ordered_args_dict = {}
        iv2 = b.Integer.ref()
        for k, i, v in b.select(iv, iv2, iv3).where(self.ordered_args_hash(iv, iv2, iv3)):
            if k not in ordered_args_dict:
                ordered_args_dict[k] = []
            ordered_args_dict[k].append((i, v))
        vv = b.python_types_str_to_concepts[self._data_type].ref()
        for k, i, v in b.select(iv, iv2, vv).where(self.ordered_args_data(iv, iv2, vv)):
            if k not in ordered_args_dict:
                ordered_args_dict[k] = []
            ordered_args_dict[k].append((i, v))
        # convert ordered args to dict
        for k, t in ordered_args_dict.items():
            # sort by index
            t.sort(key=lambda x: x[0])
            args_dict[k] = [v for (_, v) in t]

        # compute strings
        return sorted(_expr_strings_rec(n, names_dict, ops_dict, args_dict) for n in nodes)

    # solve the model given a solver and solver options
    def solve(self, solver: Solver, log_to_console: bool = False, **kwargs):
        # validate options
        for k, v in kwargs.items():
            if not isinstance(k, str):
                raise ValueError(f"Invalid parameter key. Expected string, got {type(k)} for {k}.")
            if not isinstance(v, (int, float, str, bool)):
                raise ValueError(
                    f"Invalid parameter value. Expected string, integer, float, or boolean, got {type(v)} for {k}."
                )

        # set up
        input_id = uuid.uuid4().hex.upper()
        executor = self._model._to_executor()
        assert isinstance(executor, (RelExecutor, LQPExecutor))
        resources = executor.resources
        app_name = resources.get_app_name()
        print(app_name)

        # Note: currently the query timeout is not propagated to the steps 'export model
        # relations', and 'import result relations'. For those steps the default query
        # timeout value defined in the config will apply.
        # TODO: propagate the query timeout to those steps as well.
        query_timeout_mins = kwargs.get("query_timeout_mins", None)
        config = self._model._config
        if query_timeout_mins is None and (timeout_value := config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
            query_timeout_mins = int(timeout_value)
        config_file_path = getattr(config, 'file_path', None)
        start_time = time.monotonic()

        # 1. export model relations
        print("export model relations")
        # TODO(coey) perf: only export the relations that are actually used in the model
        to_export = [
            "variables",
            "variable_type",
            # "variable_name",
            # "operator",
            # "ordered_args_hash",
            # "ordered_args_data",
            # "unordered_args_hash",
            # "min_objectives",
            # "max_objectives",
            # "constraints",
        ]
        for name in to_export:
            print(f"exporting {name}")
            rel = getattr(self, name)
            table_name = f"{app_name}.RESULTS.SOLVER_{input_id}_{name.upper()}"
            table = Table(table_name, cols=[c.upper() for c in rel._field_names])
            b.select(*rel._field_refs).where(rel(*rel._field_refs)).into(table)

        # 2. execute solver job and wait for completion
        remaining_timeout_minutes = calc_remaining_timeout_minutes(
            start_time, query_timeout_mins, config_file_path=config_file_path,
        )
        print("execute solver job")
        payload = {
            "solver": solver.solver_name.lower(),
            "options": kwargs,
            "input_id": input_id,
            "data_type": self._data_type
        }
        job_id = solver._exec_job(
            payload, log_to_console=log_to_console, query_timeout_mins=remaining_timeout_minutes,
        )
        print(f"job id: {job_id}") # TODO(coey) maybe job_id is not useful

        # 3. import result relations
        print("import result relations")
        # TODO(coey) perf: only import the relations that are actually used
        to_import = [
            "result_info",
            "point",
            # "points",
            # "objective_values",
            # "primal_statuses",
        ]
        for name in to_import:
            print(f"importing {name}")
            rel = getattr(self, name)
            table_name = f"{app_name}.RAI_SOLVER.{input_id}_{name.upper()}"
            table = Table(table_name, cols=[c.upper() for c in rel._field_names])
            wheres = [getattr(table, n.upper())(r) for (n, r) in zip(rel._field_names, rel._field_refs)]
            b.define(rel(*rel._field_refs)).where(*wheres)

        print("finished solve")
        return None

    # load a particular point index from `points` into `point`
    # so it is accessible from the variable relationship
    def load_point(self, i: int):
        if not isinstance(i, int) and i >= 0:
            raise ValueError(f"Expected nonnegative integer index for point, got {i}")
        executor = self._model._to_executor()
        assert isinstance(executor, RelExecutor)
        executor.execute_raw(textwrap.dedent(f"""
        def delete[:{self.point._name}]: {self.point._name}
        def insert(:{self.point._name}, var, val): {self.points._name}(int128[{i}], var, val)
        """), readonly=False)
        return None

    # print summary of the solver result
    def summarize_result(self):
        to_get = ["error", "termination_status", "solve_time_sec", "objective_value", "solver_version", "result_count"]
        k, v = b.String.ref(), b.String.ref()
        df = b.select(k, v).where(self.result_info(k, v), k.in_(to_get)).to_df()
        print(df.to_string(index=False, header=False))
        return df

    # select variable names and values in the primal result point(s)
    def variable_values(self, multiple: bool = False):
        var = b.Hash.ref()
        val = b.Number.ref()
        s = b.String.ref()
        if multiple:
            i = b.Integer.ref()
            return b.select(i, s, val).where(self.points(i, var, val), self.variable_name(var, s))
        else:
            return b.select(s, val).where(self.point(var, val), self.variable_name(var, s))

    # get scalar information
    def __getattr__(self, name: str):
        df = None
        if name in self._model_info:
            node = b.Hash.ref()
            df = b.select(b.count(node).where(self._model_info[name](node)) | 0).to_df()
        elif name in {"error", "termination_status", "solver_version", "printed_model", "solve_time_sec", "objective_value", "result_count"}:
            val = b.String.ref()
            df = b.select(val).where(self.result_info(name, val)).to_df()
        if df is not None:
            if not df.shape == (1, 1):
                raise ValueError(f"Expected exactly one value for {name}, but df has shape {df.shape}")
            v = df.iloc[0, 0]
            if isinstance(v, str):
                if name == "solve_time_sec":
                    return float(v)
                elif name == "objective_value":
                    return int(v) if self._data_type == "int" else float(v)
                elif name == "result_count":
                    return int(v)
            return v
        return None


class ExprContext():
    def __init__(self, solver_model):
        self.solver_model = solver_model
        self.define = []
        self.where = []
        self.subcontext = []

def _rewrite(expr: b.Producer | b.Fragment, ctx: ExprContext):
    if isinstance(expr, (int, float, str)):
        return None

    elif isinstance(expr, (b.TypeRef, b.Concept)):
        return None

    elif isinstance(expr, b.Ref):
        thing = _rewrite(expr._thing, ctx)
        if thing:
            assert isinstance(thing, b.Producer)
            return thing.ref()
        return None

    elif isinstance(expr, (b.Relationship, b.RelationshipRef, b.RelationshipFieldRef)):
        rel = expr if isinstance(expr, b.Relationship) else expr._relationship
        if rel in ctx.solver_model._variable_relationships:
            return std.hash(rel._short_name, expr._parent or 0)
        return None

    elif isinstance(expr, b.Union):
        # return union of the symbolified expressions, if any are symbolic
        args_rewritten = False
        args = []
        for arg in expr._args:
            ra = _rewrite(arg, ctx)
            if ra:
                args_rewritten = True
                args.append(ra)
            else:
                args.append(arg)
        if args_rewritten:
            return b.union(*args)
        return None

    elif isinstance(expr, b.Expression):
        assert isinstance(expr._op, b.Relationship)
        assert _rewrite(expr._op, ctx) is None # shouldn't contain variables
        sym_args = [_rewrite(a, ctx) for a in expr._params]
        if all(a is None for a in sym_args):
            return None
        op = expr._op._name
        assert op in infixs or op in prefix_ops, f"Operator {op} not supported in first order solver rewrites"

        # some arguments involve solver variables, so rewrite the expression
        new_args = sym_args if op in infix_comps else sym_args[:-1] # drop last arg introduced by builder
        sm = ctx.solver_model
        node = b.Hash.ref()
        sm._expr_id += 1
        ctx.define.append(sm.operator(node, op))
        hash_args = []
        for (i, a) in enumerate(new_args):
            if a is None:
                d = sm.ordered_args_data(node, i, expr._params[i])
                hash_args.append(expr._params[i])
            else:
                d = sm.ordered_args_hash(node, i, a)
                hash_args.append(a)
            ctx.define.append(d)
        ctx.where.append(_make_hash((sm._expr_id, *hash_args), node))
        return node

    elif isinstance(expr, b.Aggregate):
        # only the last argument can be symbolic
        pre_args = expr._args[:-1]
        sym_arg = _rewrite(expr._args[-1], ctx)
        if not sym_arg:
            return None
        op = expr._op._name
        assert op in agg_ops, f"Operator {op} not supported in aggregate rewrites"

        sm = ctx.solver_model
        node = b.Hash.ref()
        ctx.where.append(_make_hash((sm._expr_id, *expr._group), node))
        # only apply where conditions in subcontext
        subctx = ExprContext(sm)
        ctx.subcontext.append(subctx)
        subctx.where.extend(expr._where._where)
        sm._expr_id += 1
        subctx.define.append(sm.operator(node, op))

        # special_ordered_set_type_2 has two ordered arguments: rank and variables
        if op == "special_ordered_set_type_2":
            assert len(pre_args) == 1, "special_ordered_set_type_2 expects exactly 2 arguments (rank, variables)"
            subctx.define.append(sm.ordered_args_hash(node, pre_args[0], sym_arg))
        else:
            # other aggregate operators use unordered args
            arg_hash = b.Hash.ref()
            subctx.where.append(_make_hash((sm._expr_id, *pre_args), arg_hash))
            subctx.define.append(sm.unordered_args_hash(node, arg_hash, sym_arg))
        return node

    elif isinstance(expr, b.Fragment):
        # only support selects with one item
        assert not expr._define and not expr._require and len(expr._select) == 1
        sym_select = _rewrite(expr._select[0], ctx)
        if sym_select:
            return b.select(sym_select).where(*expr._where)
        return None

    raise NotImplementedError(f"Solver rewrites cannot handle {expr} of type {type(expr)}")

def _expr_strings_rec(x, names_dict, ops_dict, args_dict):
    if x in names_dict:
        # this is a variable node
        return names_dict[x]
    elif x not in ops_dict:
        # this is a value
        return str(x)

    # this is an expression
    assert x in ops_dict
    arg_strs = []
    op = ops_dict[x]

    for k in args_dict.get(x, []):
        s = _expr_strings_rec(k, names_dict, ops_dict, args_dict)
        if op in infix_ops and k in ops_dict and ops_dict[k] in infixs:
            # add parentheses to avoid precedence issues
            s = f"({s})"
        arg_strs.append(s)

    if op in agg_ops and not op == "special_ordered_set_type_2":
        # sort unordered args to improve determinism
        arg_strs.sort()

    if op in infixs:
        # infix operator, e.g. x + y
        assert len(arg_strs) == 2 # TODO could relax e.g. for +, *
        return f"{arg_strs[0]} {op} {arg_strs[1]}"
    else:
        # prefix operator, e.g. abs(x)
        assert len(arg_strs) >= 1
        return f"{op}({', '.join(arg_strs)})"

def _make_hash(tup, res):
    return b.Expression(b.Relationship.builtins["hash"], b.TupleArg(tup), res)

infix_ops = set(["+", "-", "*", "/", "^"])
infix_comps = set(["=", "!=", "<", "<=", ">", ">=", "implies"])
infixs = infix_ops.union(infix_comps)
prefix_ops = set(["abs", "log", "exp"])
agg_ops = set(["sum", "count", "min", "max", "all_different", "special_ordered_set_type_2"])

# _variable_types = {
#     "cont": 40,
#     "int": 41,
#     "bin": 42,
# }

# _fo_operators = {
#     "+": 10,
#     "-": 11,
#     "*": 12,
#     "/": 13,
#     "^": 14,
#     "abs": 20,
#     "exp": 21,
#     "log": 22,
#     "range": 50,
# }

# _fo_comparisons = {
#     "=": 30,
#     "!=": 31,
#     "<=": 32,
#     ">=": 33,
#     "<": 34,
#     ">": 35,
#     "implies": 62,
# }

# _ho_operators = {
#     "sum": 80,
#     # "product":81,
#     "min": 82,
#     "max": 83,
#     "count": 84,
#     "all_different": 90,
# }
