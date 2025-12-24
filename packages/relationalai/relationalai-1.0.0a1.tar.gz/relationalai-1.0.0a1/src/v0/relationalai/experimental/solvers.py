from __future__ import annotations
import time
from typing import Any, List, Optional
from dataclasses import dataclass
import textwrap
from .. import dsl, std
from ..std import rel
from ..metamodel import Builtins
from ..tools.cli_controls import Spinner
from ..tools.constants import DEFAULT_QUERY_TIMEOUT_MINS
from .. import debugging
from .. errors import ResponseStatusException
import uuid
import v0.relationalai
import json
from ..clients.util import poll_with_specified_overhead
from ..clients.snowflake import Resources as SnowflakeResources
from ..clients.snowflake import DirectAccessClient, DirectAccessResources
from ..util.timeout import calc_remaining_timeout_minutes

rel_sv = rel._tagged(Builtins.SingleValued)

APP_NAME = v0.relationalai.clients.snowflake.APP_NAME

ENGINE_TYPE_SOLVER = "SOLVER"
# TODO (dba) The ERP still uses `worker` instead of `engine`. Change
# this once we fix this in the ERP.
WORKER_ERRORS = ["worker is suspended", "create/resume", "worker not found", "no workers found", "worker was deleted"]
ENGINE_ERRORS = ["engine is suspended", "create/resume", "engine not found", "no engines found", "engine was deleted"]
ENGINE_NOT_READY_MSGS = ["worker is in pending", "worker is provisioning", "worker is not ready to accept jobs"]

# --------------------------------------------------
# SolverModel object.
# --------------------------------------------------

class SolverModel:
    def __init__(self, graph:dsl.Graph):
        self.graph = graph
        self.id = dsl.next_id()
        self.scope = f"solvermodel{self.id}_"
        scope = self.scope
        self.Variable = dsl.Type(graph, "variables", scope=scope)
        self.MinObjective = dsl.Type(graph, "min_objectives", scope=scope)
        self.MaxObjective = dsl.Type(graph, "max_objectives", scope=scope)
        self.Constraint = dsl.Type(graph, "constraints", scope=scope)
        self.Solution = dsl.Type(graph, "solutions", scope=scope)
        self.components = [
            (self.MinObjective, "minimization objectives"),
            (self.MaxObjective, "maximization objectives"),
            (self.Constraint, "constraints"),
        ]
        self.solve_index = 0
        self.is_solved = False

        # Install model helpers.
        self.graph.install_raw(textwrap.dedent(f"""
            @inline
            def _solverlib_ho_appl(op, {{R}}, s): rel_primitive_solverlib_ho_appl(R, op, s)

            @inline
            def _solver_unwrap({{R}}, h, x...): exists((v) | R(v, x...) and pyrel_unwrap(v, h))

            declare {scope}variable_name
            declare {scope}component_name
            declare {scope}serialized
            declare {scope}primal_start

            def {scope}component_string(h, s):
                rel_primitive_solverlib_print_expr(
                    {scope}serialized[h], _solver_unwrap[{scope}variable_name], s
                )

            declare {scope}solve_output
        """))
        return None

    # Add an entity to the variable set, (optionally) set a string name from the
    # arguments and add domain constraints on the variable.
    def variable(
        self,
        var, # variable entity
        name_args:List|None=None, # list of strings to concatenate into a string name
        type:str|None=None, # variable type: "integer" or "zero_one"
        lower:int|float|None=None, # lower bound
        upper:int|float|None=None, # upper bound
        fixed:int|float|None=None, # fixed value
        start:int|float|None=None, # (primal) start value
    ):
        if type not in {"integer", "zero_one", None}:
            raise Exception(f"Invalid domain type: {type}.")
        var.set(self.Variable)

        # Set variable name.
        if name_args:
            var.set(**{f"{self.scope}variable_name": make_string(name_args)})

        # Add domain constraints.
        cons = []
        if fixed is not None:
            cons.append(eq(var, fixed))
        if type == "zero_one":
            cons.append(zero_one(var))
        if lower is not None and upper is not None:
            if type == "integer":
                cons.append(integer_interval(var, lower, upper))
            else:
                cons.append(interval(var, lower, upper))
        else:
            if type == "integer":
                cons.append(integer(var))
            if lower is not None:
                cons.append(gte(var, lower))
            if upper is not None:
                cons.append(lte(var, upper))
        if len(cons) == 1:
            self.constraint(cons[0])
        elif len(cons) > 1:
            self.constraint(and_(*cons))

        # Set primal start.
        if start is not None:
            var.set(**{f"{self.scope}primal_start": start})
        return var

    # Get variable string name.
    def variable_name(self, var):
        return std.alias(getattr(var, f"{self.scope}variable_name"), "name")

    # Add a constraint, minimization objective, or maximization objective.
    def constraint(self, expr, name_args:List|None=None):
        return self._add_component(self.Constraint, expr, name_args)

    def min_objective(self, expr, name_args:List|None=None):
        return self._add_component(self.MinObjective, expr, name_args)

    def max_objective(self, expr, name_args:List|None=None):
        return self._add_component(self.MaxObjective, expr, name_args)

    def _add_component(self, typ, expr, name_args:List|None):
        comp = typ.add(serialized=_wrap_expr(expr))
        if name_args:
            comp.set(component_name=make_string(name_args))
        return comp

    # Get component string name.
    def component_name(self, comp):
        return std.alias(comp.component_name, "name")

    # Get serialized component string in human-readable format.
    def component_string(self, comp):
        return std.alias(comp.component_string, "string")

    # Summarize the model by printing the number of variables and components.
    # Use outside a rule/query.
    def summarize(self):
        with self.graph.query() as select:
            vars = select(std.aggregates.count(self.Variable()))
        s = f"Model has: {vars.results.iat[0, 0]} variables"
        for (c_type, c_name) in self.components:
            with self.graph.query() as select:
                exprs = select(std.aggregates.count(c_type()))
            if not exprs.results.empty:
                s += f", {exprs.results.iat[0, 0]} {c_name}"
        print(s)
        return None

    # Print the model in human-readable format. Use outside a rule/query.
    def print(self):
        with self.graph.query() as select:
            vars = select(rel.last(getattr(rel, f"{self.scope}variable_name")))
        print("variables:")
        print(vars.results.to_string(index=False, header=False))
        for (c_type, c_name) in self.components:
            with self.graph.query() as select:
                exprs = select(self.component_string(c_type()))
            if not exprs.results.empty:
                print(c_name + ":")
                print(exprs.results.to_string(index=False, header=False))
        return None

    # Solve the model given a solver and solver options. Use outside a rule/query.
    def solve(self, solver: Solver, log_to_console=True, **kwargs):
        self.is_solved = False
        self.solve_index += 1
        self.solve_output = dsl.RelationNS([f"{self.scope}solve_output"], f"i_{self.solve_index}")

        options = kwargs
        options["version"] = 1

        # Validate options.
        for k, v in options.items():
            if not isinstance(k, str):
                raise Exception(f"Invalid parameter key. Expected string, got {type(k)} for {k}.")
            if not isinstance(v, (int, float, str, bool)):
                raise Exception(
                    f"Invalid parameter value. Expected string, integer, float, or boolean, got {type(v)} for {k}."
                )

        # Run the solve query and insert the solve_output result.
        scope = self.scope
        variable_name_string = f"{scope}variable_name" if "print_format" in options else "{}"
        component_name_string = f"{scope}component_name" if "print_format" in options else "{}"

        input_id = uuid.uuid4()
        model_uri = f"snowflake://APP_STATE.RAI_INTERNAL_STAGE/job-inputs/solver/{input_id}/model.binpb"
        sf_input_uri = f"snowflake://job-inputs/solver/{input_id}/model.binpb"

        payload: dict[str, Any] = {"solver": solver.solver_name.lower()}
        payload["options"] = options
        payload["model_uri"] = sf_input_uri

        rai_config = self.graph._config
        query_timeout_mins = kwargs.get("query_timeout_mins", None)
        if query_timeout_mins is None and (timeout_value := rai_config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
            query_timeout_mins = int(timeout_value)
        config_file_path = getattr(rai_config, 'file_path', None)
        start_time = time.monotonic()
        remaining_timeout_minutes = query_timeout_mins
        response = self.graph.exec_raw(
            textwrap.dedent(f"""
            @inline
            def {scope}specialized_components(t, h, s):
                exists((v) | {{
                    (:min_objective, {scope}min_objectives);
                    (:max_objective, {scope}max_objectives);
                    (:constraint, {scope}constraints);
                    }}(t, v) and pyrel_unwrap(v, h) and {scope}serialized(v, s)
                )

            @no_diagnostics(:EXPERIMENTAL)
            def {scope}model_string {{
                rel_primitive_solverlib_model_string[{{
                    (:variable, _solver_unwrap[{scope}variables]);
                    {scope}specialized_components;
                    (:variable_name, _solver_unwrap[{variable_name_string}]);
                    (:expression_name, _solver_unwrap[{component_name_string}]);
                    (:primal_start, _solver_unwrap[{scope}primal_start]);
                }}]
            }}

            ic model_not_empty("Solver model is empty.") requires not empty({scope}model_string)

            def config[:envelope, :content_type]: "application/octet-stream"
            def config[:envelope, :payload, :data]: {scope}model_string
            def config[:envelope, :payload, :path]: "{model_uri}"
            def export {{ config }}
            """),
            query_timeout_mins=remaining_timeout_minutes,
        )
        txn = response.transaction or {}
        # The above `exec_raw` will throw an error if the transaction
        # gets aborted. But in the case it gets cancelled, by the user
        # or the system, it won't throw. In that case we also did not
        # upload the input model.
        if txn["state"] == "":
            txn = solver.provider.resources.get_transaction(txn["id"]) or {}
        if txn["state"] != "COMPLETED":
            raise Exception(f"Transaction that materializes the solver inputs did not complete! ID: `{txn['id']}` State `{txn['state']}`")

        # 2. Execute job and wait for completion.
        remaining_timeout_minutes = calc_remaining_timeout_minutes(
            start_time, query_timeout_mins, config_file_path=config_file_path
        )
        job_id = solver._exec_job(payload, log_to_console=log_to_console, query_timeout_mins=remaining_timeout_minutes)

        # 3. Extract result.
        remaining_timeout_minutes = calc_remaining_timeout_minutes(
            start_time, query_timeout_mins, config_file_path=config_file_path
        )
        res = self.graph.exec_raw(
            textwrap.dedent(f"""
            ic result_not_empty("Solver result is empty.") requires not empty(result)

            def result {{load_binary["snowflake://APP_STATE.RAI_INTERNAL_STAGE/job-results/{job_id}/result.binpb"] }}
            def delete[:{scope}solve_output, :"i_{self.solve_index}"]: {scope}solve_output[:"i_{self.solve_index}"]

            @no_diagnostics(:EXPERIMENTAL)
            def insert[:{scope}solve_output, :"i_{self.solve_index}"]:
                rel_primitive_solverlib_extract[result]

            def output[:solver_error]: {scope}solve_output[:"i_{self.solve_index}", :error]
            """),
            readonly=False,
            query_timeout_mins=remaining_timeout_minutes,
        )
        errors = []
        for result in res.results:
            if result["relationId"] == "/:output/:solver_error/String":
                errors.extend(result["table"]["v1"])

        # 4. Map results to solution.
        with self.graph.rule(dynamic=True):
            sol = self.Solution.add(index = self.solve_index)
            for name in {"error", "termination_status", "solve_time_sec", "objective_value", "solver_version", "printed_model"}:
                val = dsl.create_var()
                getattr(self.solve_output, name)(val)
                sol.set(**{name:val})

        self.is_solved = True

        if len(errors) > 0:
            raise Exception("\n".join(errors))

        return None

    # Get scalar result information after solving.
    def __getattr__(self, name:str):
        if not self.is_solved:
            raise Exception("Model has not been solved yet.")
        if name in {"error", "termination_status", "solve_time_sec", "objective_value", "solver_version", "printed_model"}:
            return getattr(self.Solution(index = self.solve_index), name)
        else:
            return None

    # Get variable point values after solving. If `index` is specified, get the value
    # of the variable in the return the `index`-th solution.
    def value(self, var, index:int|None=None):
        if not self.is_solved:
            raise Exception("Model has not been solved yet.")
        val = dsl.create_var()
        unwrap_var = rel_sv.pyrel_unwrap(var)
        if index:
            self.solve_output.points(unwrap_var, index, val)
        else:
            self.solve_output.point(unwrap_var, val)
        std.alias(val, "value")
        return val

# --------------------------------------------------
# Operator definitions
# --------------------------------------------------

# Builtin binary operators

def plus(left, right):
    return _make_fo_expr(10, left, right)

def minus(left, right):
    return _make_fo_expr(11, left, right)

def mult(left, right):
    return _make_fo_expr(12, left, right)

def div(left, right):
    return _make_fo_expr(13, left, right)

def pow(left, right):
    return _make_fo_expr(14, left, right)

def eq(left, right):
    return _make_fo_expr(30, left, right)

def neq(left, right):
    return _make_fo_expr(31, left, right)

def lte(left, right):
    return _make_fo_expr(32, left, right)

def gte(left, right):
    return _make_fo_expr(33, left, right)

def lt(left, right):
    return _make_fo_expr(34, left, right)

def gt(left, right):
    return _make_fo_expr(35, left, right)

# First order operators

def abs(arg):
    return _make_fo_expr(20, arg)

def exp(arg):
    return _make_fo_expr(21, arg)

def log(arg):
    return _make_fo_expr(22, arg)

def integer(arg):
    return _make_fo_expr(41, arg)

def zero_one(arg):
    return _make_fo_expr(42, arg)

def interval(arg, low, high):
    return _make_fo_expr(51, low, high, arg)

def integer_interval(arg, low, high):
    return _make_fo_expr(50, low, high, 1, arg)

def if_then_else(cond, left, right):
    return _make_fo_expr(60, cond, left, right)

def not_(arg):
    return _make_fo_expr(61, arg)

def implies(left, right):
    return _make_fo_expr(62, left, right)

def iff(left, right):
    return _make_fo_expr(63, left, right)

def xor(left, right):
    return _make_fo_expr(64, left, right)

def and_(*args):
    return _make_fo_expr(70, *args)

def or_(*args):
    return _make_fo_expr(71, *args)

# Aggregate operators

def sum(*args, per=[]) -> Any:
    return _make_ho_expr(80, args, per)

def product(*args, per=[]) -> Any:
    return _make_ho_expr(81, args, per)

def min(*args, per=[]) -> Any:
    return _make_ho_expr(82, args, per)

def max(*args, per=[]) -> Any:
    return _make_ho_expr(83, args, per)

def count(*args, per=[]) -> Any:
    return _make_ho_expr(84, args, per)

def all_different(*args, per=[]) -> Any:
    return _make_ho_expr(90, args, per)

# --------------------------------------------------
# Symbolic expression helpers
# --------------------------------------------------

def _make_fo_expr(*args):
    expr = rel_sv.rel_primitive_solverlib_fo_appl(*args)
    expr.__class__ = SolverExpression
    return expr

# TODO(coey) test:
# dsl.tag(rel_sv.rel_primitive_solverlib_fo_appl, Builtins.Expensive)

def _make_ho_expr(op, args, per):
    return SolverExpression(dsl.get_graph(), _ho_appl_def, [args, per, [op]])

_ho_appl_def = dsl.build.aggregate_def("_solverlib_ho_appl")

class SolverExpression(dsl.Expression):
    def __init__(self, graph, op, args):
        super().__init__(graph, op, args)

def _wrap_expr(e):
    # If expression is not known to produce a serialized expression string,
    # wrap it with the identity operation just in case
    return e if isinstance(e, SolverExpression) else _make_fo_expr(0, e)

# Symbolic expression context, in which some builtin infix operators are redefined
# TODO(coey) handle comparison chains (e.g. 0 < x < y <= 1) or throw error
class Operators(dsl.Context):
    def _supports_binary_op(self, op):
        return op in _builtin_binary_map

    def _make_binary_op(self, op, left, right):
        return _make_fo_expr(_builtin_binary_map[op], left, right)

def operators():
    return Operators(dsl.get_graph())

# Maps for Builtins operator to SolverLib operator ID
_builtin_binary_map = {
    Builtins.plus: 10,
    Builtins.minus: 11,
    Builtins.mult: 12,
    Builtins.div: 13,
    Builtins.pow: 14,
    Builtins.approx_eq: 30,
    Builtins.neq: 31,
    Builtins.lte: 32,
    Builtins.gte: 33,
    Builtins.lt: 34,
    Builtins.gt: 35,
}

# Concatenate arguments into a string separated by underscores
def make_string(args:List):
    string = args[0]
    for arg in args[1:]:
        string = rel_sv.concat(rel_sv.concat(string, "_"), arg)
    return string


# --------------------------------------------------
# Solver
# --------------------------------------------------


@dataclass
class PollingState:
    job_id: str
    continuation_token: str
    is_done: bool
    log_to_console: bool


class Solver:
    def __init__(
        self,
        solver_name: str,
        engine_name: str | None = None,
        engine_size: str | None = None,
        auto_suspend_mins: int | None = None,
        resources: SnowflakeResources | None = None,
    ):
        self.provider = Provider(resources=resources)
        self.solver_name = solver_name.lower()

        self.rai_config = self.provider.resources.config
        settings: dict[str, Any] = {}
        if "experimental" in self.rai_config:
            exp_config = self.rai_config.get("experimental", {})
            if isinstance(exp_config, dict):
                if "solvers" in exp_config:
                    settings = exp_config["solvers"].copy()

        # Engine configuration fields are not necessary for the solver
        # settings so we `pop` them from the settings object. Default
        # size and auto_suspend_mins are set in the `Provider` methods.
        engine_name = engine_name or settings.pop("engine", None)
        if not engine_name:
            engine_name = self.provider.resources.get_user_based_engine_name()
        self.engine_name = engine_name

        self.engine_size = engine_size or settings.pop("engine_size", None)
        self.engine_auto_suspend_mins = auto_suspend_mins or settings.pop("auto_suspend_mins", None)

        # The settings are used when creating a solver engine, they
        # may configure each individual solver.
        self.engine_settings = settings

        # Optimistically set the engine object to a `READY` engine to
        # avoid checking the engine status on each execution.
        self.engine:Optional[dict[str,Any]] = {"name": engine_name, "state": "READY"}

        return None

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------
    def _auto_create_solver_async(self):
        name = self.engine_name
        auto_suspend_mins = self.engine_auto_suspend_mins
        size = self.engine_size
        settings = self.engine_settings
        with Spinner(
            "Checking solver status",
            leading_newline=True,
        ) as spinner:
            engine = None
            engines = [e for e in self.provider.list_solvers() if e["name"] == name]
            assert len(engines) == 1 or len(engines) == 0
            if len(engines) != 0:
                engine = engines[0]

            if engine:
                # TODO (dba) Logic engines support altering the
                # auto_suspend_mins setting. Currently, we don't have
                # this capability for solver engines, so users need to
                # recreate or use another engine. For both the size
                # and Gurobi configuration the user anyways has to
                # create a new one as this configuration must happen
                # when the engine is created.
                settings_cannot_be_altered_msg = "The configuration of a solver engine happens when the engine is created and _cannot_ be changed. You either need to specify a new engine name or delete the current engine.\n\nSee `solvers.Provider().delete_solver()`."
                # Make sure that the solver requested is enabled
                # on the engine.
                if self.solver_name not in engine["solvers"]:
                    raise Exception(
                        f"Solver `{self.solver_name}` is not enabled on `{name}`.\n\n" + settings_cannot_be_altered_msg
                    )

                # Make sure size and auto_suspend_mins settings match
                # what the user requests.
                if size is not None and size != engine["size"]:
                    raise Exception(
                        f"Engine `{name}` has size setting of `{engine['size']}` but size is requested to be `{size}`.\n\n" + settings_cannot_be_altered_msg
                    )

                if auto_suspend_mins is not None and auto_suspend_mins != engine["auto_suspend_mins"]:
                    raise Exception(
                        f"Engine `{name}` has auto_suspend_mins setting of `{engine['auto_suspend_mins']}` but auto_suspend_mins is requested to be `{auto_suspend_mins}`.\n\n" + settings_cannot_be_altered_msg
                    )

                if engine["state"] == "PENDING":
                    spinner.update_messages(
                        {
                            "finished_message": f"Solver {name} is starting",
                        }
                    )
                    pass
                elif engine["state"] == "SUSPENDED":
                    spinner.update_messages(
                        {
                            "finished_message": f"Resuming solver {name}",
                        }
                    )
                    self.provider.resume_solver_async(name)
                elif engine["state"] == "READY":
                    spinner.update_messages(
                        {
                            "finished_message": f"Solver {name} is ready",
                        }
                    )
                    pass
                else:
                    spinner.update_messages(
                        {
                            "message": f"Restarting solver {name}",
                        }
                    )
                    self.provider.delete_solver(name)
                    engine = None
            if not engine:
                # Validate Gurobi config.
                if self.solver_name == "gurobi":
                    is_gurobi_configured = False
                    gurobi_config = settings.get("gurobi", {})
                    if all(
                        k in gurobi_config
                        for k in ["license_secret_name", "external_access_integration"]
                    ):
                        is_gurobi_configured = True
                    if not is_gurobi_configured:
                        raise Exception(
                            "Gurobi is not properly configured. You need to provide both `license_secret_name` and `external_access_integration` in its configuration, see https://docs.relational.ai/build/reasoners/prescriptive/solver-backends/gurobi/#usage"
                        )
                self.provider.create_solver_async(name, settings=settings, size=size, auto_suspend_mins=auto_suspend_mins)
                engine = self.provider.get_solver(name)
                spinner.update_messages(
                    {
                        "finished_message": f"Starting solver {name}...",
                    }
                )

            self.engine = engine

    def _exec_job(self, payload, log_to_console=True, query_timeout_mins: Optional[int]=None):
        if self.engine is None:
            raise Exception("Engine not initialized.")

        with debugging.span("job") as job_span:
            # Retry logic. If creating a job fails with an engine
            # related error we will create/resume/... the engine and
            # retry.
            try:
                job_id = self.provider.create_job_async(self.engine["name"], payload, query_timeout_mins=query_timeout_mins)
            except Exception as e:
                err_message = str(e).lower()
                if isinstance(e, ResponseStatusException):
                    err_message = e.response.json().get("message", "")
                if any(kw in err_message.lower() for kw in ENGINE_ERRORS + WORKER_ERRORS + ENGINE_NOT_READY_MSGS):
                    self._auto_create_solver_async()
                    # Wait until the engine is ready.
                    poll_with_specified_overhead(lambda: self._is_solver_ready(), 0.1)
                    job_id = self.provider.create_job_async(self.engine["name"], payload, query_timeout_mins=query_timeout_mins)
                else:
                    raise e

            job_span["job_id"] = job_id
            debugging.event("job_created", job_span, job_id=job_id, engine_name=self.engine["name"], job_type=ENGINE_TYPE_SOLVER)
            if not isinstance(job_id, str):
                job_id = ""
            polling_state = PollingState(job_id, "", False, log_to_console)

            try:
                with debugging.span("wait", job_id=job_id):
                    poll_with_specified_overhead(
                        lambda: self._check_job_status(polling_state), 0.1
                    )
            except KeyboardInterrupt as e:
                print(f"Canceling job {job_id}")
                self.provider.cancel_job(job_id)
                raise e

            return job_id

    def _is_solver_ready(self):
        if self.engine is None:
            raise Exception("Engine not initialized.")

        result = self.provider.get_solver(self.engine["name"])

        if result is None:
            raise Exception("No engine available.")
            
        self.engine = result
        state = result["state"]
        if state != "READY" and state != "PENDING":
            # Might have suspended or otherwise gone. Recreate.
            self._auto_create_solver_async()
        return state == "READY"

    def _check_job_status(self, state):
        response = self.provider.get_job(state.job_id)
        assert response, f"No results from get_job('{state.job_id}')"

        status: str = response["state"]

        self._print_solver_logs(state)

        return status == "COMPLETED" or status == "FAILED" or status == "CANCELED"

    def _print_solver_logs(self, state: PollingState):
        if state.is_done:
            return

        resp = self.provider.get_job_events(state.job_id, state.continuation_token)

        # Print solver logs to stdout.
        for event in resp["events"]:
            if event["type"] == "LogMessage":
                if state.log_to_console:
                    print(event["event"]["message"])
            else:
                continue

        state.continuation_token = resp["continuation_token"]
        if state.continuation_token == "":
            state.is_done = True


# --------------------------------------------------
# Provider
# --------------------------------------------------
#
# TODO (dba) We use an experimental and unified engine API for
# solvers. Once it is no longer experimental we can remove the
# provider here and use the normal PyRel provider.


class Provider:
    def __init__(self, resources=None):
        if not resources:
            resources = v0.relationalai.Resources()
        if not isinstance(resources, v0.relationalai.clients.snowflake.Resources):
            raise Exception("Solvers are only supported on SPCS.")

        self.resources = resources
        self.direct_access_client: Optional[DirectAccessClient] = None

        if isinstance(self.resources, DirectAccessResources):
            self.direct_access_client = self.resources.direct_access_client

    def create_solver(
        self,
        name: str,
        size: str | None = None,
        settings: dict | None = None,
        auto_suspend_mins: int | None = None,
    ):
        if size is None:
            size = "HIGHMEM_X64_S"
        if settings is None:
            settings = {}
        engine_config: dict[str, Any] = {"settings": settings}
        if auto_suspend_mins is not None:
            engine_config["auto_suspend_mins"] = auto_suspend_mins
        self.resources._exec_sql(
            f"CALL {APP_NAME}.experimental.create_engine('{ENGINE_TYPE_SOLVER}', '{name}', '{size}', {engine_config});", None
        )

    def create_solver_async(
        self,
        name: str,
        size: str | None = None,
        settings: dict | None = None,
        auto_suspend_mins: int | None = None,
    ):
        if size is None:
            size = "HIGHMEM_X64_S"

        if self.direct_access_client is not None:
            payload:dict[str, Any] = {
                "name": name,
                "settings": settings,
               }
            if auto_suspend_mins is not None:
                payload["auto_suspend_mins"] = auto_suspend_mins
            if size is not None:
                payload["size"] = size
            response = self.direct_access_client.request(
                "create_engine",
                payload=payload,
                path_params={"engine_type": "solver"},
               )
            if response.status_code != 200:
                raise ResponseStatusException(
                    f"Failed to create engine {name} with size {size}.", response
                )
        else:
            engine_config: dict[str, Any] = {}
            if settings is not None:
                engine_config["settings"] = settings
            if auto_suspend_mins is not None:
                engine_config["auto_suspend_mins"] = auto_suspend_mins
            self.resources._exec_sql(
                f"CALL {APP_NAME}.experimental.create_engine_async('{ENGINE_TYPE_SOLVER}', '{name}', '{size}', {engine_config});",
                None
               )

    def delete_solver(self, name: str):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "delete_engine", path_params = {"engine_type": ENGINE_TYPE_SOLVER, "engine_name": name}
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to delete engine.", response)
            return None
        else:
            self.resources._exec_sql(
                f"CALL {APP_NAME}.experimental.delete_engine('{ENGINE_TYPE_SOLVER}', '{name}');",
                None
            )

    def resume_solver_async(self, name: str):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "resume_engine", path_params = {"engine_type": ENGINE_TYPE_SOLVER, "engine_name": name}
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to resume engine.", response)
            return None
        else:
            self.resources._exec_sql(
                f"CALL {APP_NAME}.experimental.resume_engine_async('{ENGINE_TYPE_SOLVER}', '{name}');",
                None
            )
            return None

    def get_solver(self, name: str):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "get_engine", path_params = {"engine_type": ENGINE_TYPE_SOLVER, "engine_name": name}
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to get engine.", response)
            solver = response.json()
            if not solver :
                return None
            solver_state = {
                "name": solver["name"],
                "id": solver["id"],
                "size": solver["size"],
                "state": solver["status"], # callers are expecting 'state'
                "created_by": solver["created_by"],
                "created_on": solver["created_on"],
                "updated_on": solver["updated_on"],
                "version": solver["version"],
                "auto_suspend": solver["auto_suspend_mins"],
                "suspends_at": solver["suspends_at"],
                "solvers": []
                if solver["settings"] == ""
                else [
                        k
                        for (k,v) in json.loads(solver["settings"]).items()
                        if isinstance(v, dict) and v.get("enabled", False)
                ],
                }
            return solver_state
        else:
            results = self.resources._exec_sql(
                f"CALL {APP_NAME}.experimental.get_engine('{ENGINE_TYPE_SOLVER}', '{name}');",
                None
               )
            return solver_list_to_dicts(results)[0]

    def list_solvers(self, state: str | None = None):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "list_engines"
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to list engines.", response)
            response_content = response.json()
            if not response_content:
                return []
            engines = [
                {
                    "name": engine["name"],
                    "id": engine["id"],
                    "size": engine["size"],
                    "state": engine["status"], # callers are expecting 'state'
                    "created_by": engine["created_by"],
                    "created_on": engine["created_on"],
                    "updated_on": engine["updated_on"],
                    "auto_suspend_mins": engine["auto_suspend_mins"],
                    "solvers": []
                    if engine["settings"] == ""
                    else [
                        k
                        for (k, v) in json.loads(engine["settings"]).items()
                        if isinstance(v, dict) and v.get("enabled", False)
                           ],
                }
                for engine in response_content.get("engines", [])
                if (state is None or engine.get("status") == state) and (engine.get("type") == ENGINE_TYPE_SOLVER)
               ]
            return sorted(engines, key=lambda x: x["name"])
        else:
            where_clause = f"WHERE TYPE='{ENGINE_TYPE_SOLVER}'"
            where_clause = (
                f"{where_clause} AND STATUS = '{state.upper()}'" if state else where_clause
               )
            statement = f"SELECT NAME,ID,SIZE,STATUS,CREATED_BY,CREATED_ON,UPDATED_ON,AUTO_SUSPEND_MINS,SETTINGS FROM {APP_NAME}.experimental.engines {where_clause};"
            results = self.resources._exec_sql(statement, None)
            return solver_list_to_dicts(results)

    # --------------------------------------------------
    # Job API
    # --------------------------------------------------

    def create_job_async(self, engine_name, payload, query_timeout_mins: Optional[int]=None):
        payload_json = json.dumps(payload)

        if query_timeout_mins is None and (timeout_value := self.resources.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
            query_timeout_mins = int(timeout_value)
            
        if self.direct_access_client is not None:
            job = {
                "job_type":ENGINE_TYPE_SOLVER,
                "worker_name": engine_name,
                "timeout_mins": query_timeout_mins,
                "payload": payload_json,
            }
            response = self.direct_access_client.request(
                "create_job",
                payload=job,
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to create job.", response)
            response_content = response.json()
            return response_content["id"]
        else:
            if query_timeout_mins is not None:
                sql_string = textwrap.dedent(f"""
                CALL {APP_NAME}.experimental.exec_job_async('{ENGINE_TYPE_SOLVER}', '{engine_name}', '{payload_json}', null, {query_timeout_mins})
                """)
            else:
                sql_string = textwrap.dedent(f"""
                CALL {APP_NAME}.experimental.exec_job_async('{ENGINE_TYPE_SOLVER}', '{engine_name}', '{payload_json}')
                """)
            res = self.resources._exec_sql(sql_string, None)
            return res[0]["ID"]

    def list_jobs(self, state=None, limit=None):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "list_jobs"
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to list jobs.", response)
            response_content = response.json()
            if not response_content:
                return []
            jobs = [
                {
                    "id": job["id"],
                    "state": job["state"],
                    "created_by": job["created_by"],
                    "created_on": job["created_on"],
                    "finished_at": job.get("finished_at", None),
                    "duration": job["duration"] if "duration" in job else 0,
                    "solver": json.loads(job["payload"]).get("solver", ""),
                    "engine": job.get("engine_name", job["worker_name"]),
                }
                for job in response_content.get("jobs", [])
                if state is None or job.get("state") == state
               ]
            return sorted(jobs, key=lambda x: x["created_on"], reverse=True)
        else:
            state_clause = f"AND STATE = '{state.upper()}'" if state else ""
            limit_clause = f"LIMIT {limit}" if limit else ""
            results = self.resources._exec_sql(
                f"SELECT ID,STATE,CREATED_BY,CREATED_ON,FINISHED_AT,DURATION,PAYLOAD,ENGINE_NAME FROM {APP_NAME}.experimental.jobs where type='{ENGINE_TYPE_SOLVER}' {state_clause} ORDER BY created_on DESC {limit_clause};",
                None
               )
            return job_list_to_dicts(results)

    def get_job(self, id: str):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "get_job", path_params = {"job_type": ENGINE_TYPE_SOLVER, "job_id": id}
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to get job.", response)
            response_content = response.json()
            return response_content["job"]
        else:
            results = self.resources._exec_sql(
                f"CALL {APP_NAME}.experimental.get_job('{ENGINE_TYPE_SOLVER}', '{id}');",
                None
            )
            return job_list_to_dicts(results)[0]

    def get_job_events(self, job_id: str, continuation_token: str = ""):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "get_job_events",
                path_params = {"job_type": ENGINE_TYPE_SOLVER, "job_id": job_id, "stream_name": "progress"},
                query_params={"continuation_token": continuation_token},
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to get job events.", response)
            response_content = response.json()
            if not response_content:
                return {
                    "events": [],
                    "continuation_token": None
                }
            return response_content
        else:
            results = self.resources._exec_sql(
                f"SELECT {APP_NAME}.experimental.get_job_events('{ENGINE_TYPE_SOLVER}', '{job_id}', '{continuation_token}');",
                None
               )
            if not results:
                return {"events": [], "continuation_token": None}
            row = results[0][0]
            if not isinstance(row, str):
                row = ""
            return json.loads(row)

    def cancel_job(self, id: str):
        if self.direct_access_client is not None:
            response = self.direct_access_client.request(
                "cancel_job", path_params = {"job_type": ENGINE_TYPE_SOLVER, "job_id": id}
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to cancel job.", response)
            return None
        else:
            self.resources._exec_sql(
                f"CALL {APP_NAME}.experimental.cancel_job('{ENGINE_TYPE_SOLVER}', '{id}');",
                None
            )
            return None


def solver_list_to_dicts(results):
    if not results:
        return []
    return [
        {
            "name": row["NAME"],
            "id": row["ID"],
            "size": row["SIZE"],
            "state": row["STATUS"],  # callers are expecting 'state'
            "created_by": row["CREATED_BY"],
            "created_on": row["CREATED_ON"],
            "updated_on": row["UPDATED_ON"],
            "auto_suspend_mins": row["AUTO_SUSPEND_MINS"],
            "solvers": []
            if row["SETTINGS"] == ""
            else [
                k
                for (k, v) in json.loads(row["SETTINGS"]).items()
                if isinstance(v, dict) and v.get("enabled", False)
            ],
        }
        for row in results
    ]

def job_list_to_dicts(results):
    if not results:
        return []
    return [
        {
            "id": row["ID"],
            "state": row["STATE"],
            "created_by": row["CREATED_BY"],
            "created_on": row["CREATED_ON"],
            "finished_at": row["FINISHED_AT"],
            "duration": row["DURATION"] if "DURATION" in row else 0,
            "solver": json.loads(row["PAYLOAD"])["solver"],
            "engine": row["ENGINE_NAME"],
        }
        for row in results
    ]
