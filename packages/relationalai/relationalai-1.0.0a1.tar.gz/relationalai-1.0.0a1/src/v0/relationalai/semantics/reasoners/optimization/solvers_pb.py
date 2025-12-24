"""Solver model implementation using protobuf format.

This module provides the SolverModelPB class for defining optimization and
constraint programming problems that are serialized to protobuf format and
solved by external solver engines.

Note: This protobuf-based implementation will be deprecated in favor of the
      development version (solvers_dev.py) in future releases.
"""

from __future__ import annotations

import textwrap
import time
import uuid
from typing import Any, Optional

from v0.relationalai.experimental.solvers import Solver
from v0.relationalai.semantics.internal import internal as b
from v0.relationalai.semantics.rel.executor import RelExecutor
from v0.relationalai.tools.constants import DEFAULT_QUERY_TIMEOUT_MINS
from v0.relationalai.util.timeout import calc_remaining_timeout_minutes

from .common import make_name


# =============================================================================
# Solver ProtoBuf Format Constants and Helpers
# =============================================================================

# Variable type codes for the solver protobuf format
# cont: continuous (real-valued), int: integer, bin: binary (0/1)
_VARIABLE_TYPE_CODES: dict[str, int] = {
    "cont": 40,
    "int": 41,
    "bin": 42,
}

# First-order operators: arithmetic and mathematical functions
_FIRST_ORDER_OPERATOR_CODES: dict[str, int] = {
    "+": 10,
    "-": 11,
    "*": 12,
    "/": 13,
    "^": 14,
    "abs": 20,
    "exp": 21,
    "log": 22,
    "range": 50,
}

# First-order comparison operators: relational constraints
_FIRST_ORDER_COMPARISON_CODES: dict[str, int] = {
    "=": 30,
    "!=": 31,
    "<=": 32,
    ">=": 33,
    "<": 34,
    ">": 35,
    "implies": 62,
}

# Higher-order operators: aggregation and global constraints
_HIGHER_ORDER_OPERATOR_CODES: dict[str, int] = {
    "sum": 80,
    "min": 82,
    "max": 83,
    "count": 84,
    "all_different": 90,
}

# Mapping from bound type keywords to comparison operators
_BOUND_TO_COMPARISON_OPERATOR: dict[str, str] = {
    "lower": ">=",
    "upper": "<=",
    "fixed": "=",
}


def _make_first_order_application_with_result(
    operator_code: int, *args: Any
) -> b.Expression:
    """Create a first-order application with a result variable."""
    return _make_first_order_application(operator_code, *args, b.String.ref("res"))


def _make_first_order_application(operator_code: int, *args: Any) -> b.Expression:
    """Create a first-order application expression."""
    if not (2 <= len(args) <= 4):
        raise ValueError(
            f"First-order application requires 2-4 arguments, but got {len(args)}."
        )
    result_ref = args[-1]
    if not isinstance(result_ref, b.Ref):
        raise TypeError(
            f"Last argument must be a Ref, got {type(result_ref).__name__}."
        )
    if result_ref._thing != b.String:
        result_ref = b.String.ref("res")
    application_builtin = b.Relationship.builtins["rel_primitive_solverlib_fo_appl"]
    # Wrap operands in TupleArg for the vararg solverlib_fo_appl primitive:
    # fo_appl(op, (operands...), result)
    return b.Expression(
        application_builtin, operator_code, b.TupleArg(args[:-1]), result_ref
    )


# =============================================================================
# Main Solver Model Class
# =============================================================================


class SolverModelPB:
    """Solver model interface using protobuf format for optimization problems."""

    def __init__(self, model: b.Model, num_type: str) -> None:
        """Initialize solver model.

        Args:
            model: The RelationalAI model.
            num_type: Variable type - 'cont' or 'int'.
        """
        if num_type not in ["cont", "int"]:
            raise ValueError(
                f"Invalid numerical type '{num_type}'. Must be 'cont' or 'int'."
            )
        self._model = model
        self._num_type = num_type
        self._id = next(b._global_id)
        # Maps relationships to their corresponding variable concepts
        self._variable_relationships: dict[b.Relationship, b.Concept] = {}
        prefix_uppercase = f"SolverModel_{self._id}_"
        prefix_lowercase = prefix_uppercase.lower()

        # Create core concepts for model components
        self.Variable = Variable = model.Concept(prefix_uppercase + "Variable")
        self.MinObjective = model.Concept(prefix_uppercase + "MinObjective")
        self.MaxObjective = model.Concept(prefix_uppercase + "MaxObjective")
        self.Constraint = model.Concept(prefix_uppercase + "Constraint")
        self._model_info = {
            "num_variables": Variable,
            "num_min_objectives": self.MinObjective,
            "num_max_objectives": self.MaxObjective,
            "num_constraints": self.Constraint,
        }
        # Add printed_expr property to objectives and constraints for human-readable output
        for concept in [self.MinObjective, self.MaxObjective, self.Constraint]:
            concept.printed_expr = model.Property(
                f"{{{concept._name}}} has {{printed_expr:str}}"
            )

        # Create relationships for result extraction
        result_type = "int" if num_type == "int" else "float"
        self.result_info = model.Relationship(
            "{key:str} has {value:str}", short_name=(prefix_lowercase + "result_info")
        )
        # TODO(coey) PyRel is not able to handle "Variable._name" instead of "var" below due
        # to some internal naming bug; this leads to a "Unresolved Type" warning that we
        # will have to live with for now
        self.point = model.Property(
            f"{{var}} has {{value:{result_type}}}",
            short_name=(prefix_lowercase + "point"),
        )
        self.points = model.Property(
            f"point {{i:int}} for {{var}} has {{value:{result_type}}}",
            short_name=(prefix_lowercase + "points"),
        )

        # Install raw rel to work around lack of support for rel_primitive_solverlib_print_expr
        install_rel = f"""
        declare {self.MinObjective._name}
        declare {self.MaxObjective._name}
        declare {self.Constraint._name}

        declare {prefix_lowercase}variable_name
        declare {prefix_lowercase}minobjective_name
        declare {prefix_lowercase}maxobjective_name
        declare {prefix_lowercase}constraint_name
        declare {prefix_lowercase}minobjective_serialized
        declare {prefix_lowercase}maxobjective_serialized
        declare {prefix_lowercase}constraint_serialized

        def {prefix_lowercase}minobjective_printed_expr(h, s):
            rel_primitive_solverlib_print_expr({prefix_lowercase}minobjective_serialized[h], {prefix_lowercase}variable_name, s)

        def {prefix_lowercase}maxobjective_printed_expr(h, s):
            rel_primitive_solverlib_print_expr({prefix_lowercase}maxobjective_serialized[h], {prefix_lowercase}variable_name, s)

        def {prefix_lowercase}constraint_printed_expr(h, s):
            rel_primitive_solverlib_print_expr({prefix_lowercase}constraint_serialized[h], {prefix_lowercase}variable_name, s)
        """
        b.define(b.RawSource("rel", textwrap.dedent(install_rel)))

    # -------------------------------------------------------------------------
    # Variable Handling
    # -------------------------------------------------------------------------

    def solve_for(
        self,
        expr,
        where: Optional[list[Any]] = None,
        populate: bool = True,
        **kwargs: Any,
    ) -> b.Concept:
        """Define decision variables.

        Args:
            expr: Relationship or expression defining variables.
            where: Optional grounding conditions.
            populate: Whether to populate relationship with solver results.
            **kwargs: Optional properties (name, type, lower, upper, fixed).

        Returns:
            Variable concept.
        """
        if where is None:
            where = []
        if isinstance(expr, b.Fragment):
            # TODO(coey): Remove in future
            raise ValueError(
                "The select fragment argument to `solve_for` is deprecated. "
                "Instead, use the `where = [conditions...]` kwarg to specify optional grounding conditions."
            )
        elif isinstance(expr, b.Expression):
            relationship = expr._op
            if not isinstance(relationship, b.Relationship):
                raise TypeError(
                    f"Expression operator must be a Relationship, got {type(relationship).__name__}."
                )
            params = expr._params
        elif isinstance(expr, b.Relationship):
            relationship = expr
            params = [
                b.field_to_type(self._model, field) for field in relationship._fields
            ]
        else:
            raise TypeError(
                f"Invalid expression type for solve_for: {type(expr).__name__}. "
                f"Expected Relationship or Expression."
            )

        if len(params) != len(relationship._fields):
            raise ValueError(
                f"Parameter count mismatch: Got {len(params)} params "
                f"but relationship has {len(relationship._fields)} fields."
            )
        if relationship in self._variable_relationships:
            raise ValueError(
                f"Variables are already defined for relationship {relationship}."
            )

        # Create a specialized Variable concept for this relationship
        # Each decision variable gets its own concept subtype
        Var = self._model.Concept(
            f"{self.Variable._name}_{str(relationship).replace('.', '_')}",
            extends=[self.Variable],
        )
        self._variable_relationships[relationship] = Var

        # Build field dict from relationship parameters (excluding the value field)
        fields = {}
        for i in range(len(params) - 1):
            if i == 0 and relationship._parent is not None:
                concept = relationship._parent
                if not isinstance(concept, b.Concept):
                    raise TypeError(
                        f"Relationship parent must be a Concept, got {type(concept).__name__}."
                    )
            else:
                concept = params[i]
            field_name = relationship._field_names[i]
            # Prevent "Implicit Subtype Relationship" warnings by explicitly registering
            # the relationship on the parent Variable concept before using it on subtypes
            self.Variable._relationships[field_name] = self.Variable._get_relationship(
                field_name
            )
            fields[field_name] = concept
        var = Var.new(**fields)
        b.define(var).where(*where)

        # Handle optional variable properties
        for key, value in kwargs.items():
            if key == "name":
                definition = self.Variable.name(var, make_name(value))
            elif key == "type":
                if not isinstance(value, str):
                    raise TypeError(
                        f"Variable 'type' must be a string, but got {type(value).__name__}."
                    )
                if value not in _VARIABLE_TYPE_CODES:
                    valid_types = ", ".join(_VARIABLE_TYPE_CODES.keys())
                    raise ValueError(
                        f"Invalid variable type '{value}'. Valid types are: {valid_types}."
                    )
                serialized_expr = _make_first_order_application_with_result(
                    _VARIABLE_TYPE_CODES[value], var
                )
                definition = self.Constraint.new(serialized=serialized_expr)
            elif key in ("lower", "upper", "fixed"):
                if not isinstance(value, (b.Producer, float, int)):
                    raise TypeError(
                        f"Variable '{key}' must be a number, but got {type(value).__name__}."
                    )
                # Map bound types to comparison operators
                operator = _BOUND_TO_COMPARISON_OPERATOR[key]
                serialized_expr = _make_first_order_application_with_result(
                    _FIRST_ORDER_COMPARISON_CODES[operator], var, value
                )
                definition = self.Constraint.new(serialized=serialized_expr)
            else:
                raise ValueError(f"Invalid keyword argument '{key}' for solve_for.")
            b.define(definition).where(*where)

        if populate:
            # Automatically populate the variable relationship with solver results
            # This defines the original relationship to pull values from self.point after solving
            value_ref = (b.Integer if self._num_type == "int" else b.Float).ref()
            b.define(
                relationship(
                    *[getattr(Var, field_name) for field_name in fields], value_ref
                )
            ).where(self.point(Var, value_ref))

        return Var

    # -------------------------------------------------------------------------
    # Objective Functions
    # -------------------------------------------------------------------------

    def minimize(
        self,
        expr: b.Producer | float | int | b.Fragment,
        name: Optional[str | list[str]] = None,
    ) -> None:
        """Add minimization objective.

        Args:
            expr: Expression to minimize.
            name: Optional objective name.
        """
        return self._add_objective(self.MinObjective, expr, name)

    def maximize(
        self,
        expr: b.Producer | float | int | b.Fragment,
        name: Optional[str | list[str]] = None,
    ) -> None:
        """Add maximization objective.

        Args:
            expr: Expression to maximize.
            name: Optional objective name.
        """
        return self._add_objective(self.MaxObjective, expr, name)

    def _add_objective(
        self,
        objective_concept: b.Concept,
        expr: b.Producer | float | int | b.Fragment,
        name: Optional[str | list[str]],
    ) -> None:
        context = SymbolifyContext(self)
        symbolic_expr = context.rewrite(expr)
        if not isinstance(symbolic_expr, Symbolic):
            # Expr is not symbolic (a constant) - wrap it as a trivial expression
            symbolic_expr = _make_first_order_application_with_result(0, expr)
        else:
            # Unwrap the symbolic expression
            unwrapped_expr = symbolic_expr.expr
            # Check if it's a bare variable (needs wrapping for protobuf)
            is_bare_variable = isinstance(unwrapped_expr, b.ConceptMember)
            is_fragment_with_variable = (
                isinstance(unwrapped_expr, b.Fragment)
                and unwrapped_expr._select
                and isinstance(unwrapped_expr._select[0], b.ConceptMember)
            )
            if is_bare_variable or is_fragment_with_variable:
                # The protobuf format requires all objectives to be expressions, not bare variables
                symbolic_expr = _make_first_order_application_with_result(
                    0, unwrapped_expr
                )
            else:
                symbolic_expr = unwrapped_expr

        if isinstance(symbolic_expr, Symbolic):
            raise ValueError(
                "Internal error. Expression is still Symbolic after unwrapping."
            )

        objective = objective_concept.new(serialized=symbolic_expr)
        definitions = [objective]
        if name is not None:
            definitions.append(objective.name(make_name(name)))
        b.define(*definitions)

    def satisfy(
        self,
        expr: b.Fragment,
        check: bool = False,
        name: Optional[str | list[str]] = None,
    ) -> None:
        """Add constraints.

        Args:
            expr: Fragment with require clause.
            check: Whether to keep require in model validation.
            name: Optional constraint name.
        """
        if not isinstance(expr, b.Fragment):
            raise TypeError(
                f"The satisfy method expects a Fragment, but got {type(expr).__name__}."
            )
        if not expr._require:
            raise ValueError("Fragment for satisfy must have a require clause.")
        if expr._select or expr._define:
            raise ValueError(
                "Fragment for satisfy must not have select or define clauses."
            )
        if not check:
            # Remove the `require` from the model roots so it is not checked as an integrity constraint
            b._remove_roots([expr])
        context = SymbolifyContext(self)

        symbolic_where_clauses = context.rewrite_where(*expr._where)
        definitions = []
        for requirement in expr._require:
            symbolic_requirement = context.rewrite(requirement)
            if not isinstance(symbolic_requirement, Symbolic):
                raise ValueError(
                    f"Cannot symbolify requirement {requirement} in satisfy. "
                    f"The requirement must contain solver variables or expressions."
                )
            constraint = self.Constraint.new(serialized=symbolic_requirement.expr)
            definitions.append(constraint)
            if name is not None:
                definitions.append(constraint.name(make_name(name)))
        b.define(*definitions).where(*symbolic_where_clauses)

    # -------------------------------------------------------------------------
    # Model Inspection and Display
    # -------------------------------------------------------------------------

    @staticmethod
    def _print_dataframe(df: Any) -> None:
        """Print dataframe with consistent formatting for long strings."""
        for row in df.itertuples(index=False):
            print("    ".join(str(val) for val in row))
        print()

    def summarize(self) -> None:
        """Print counts of variables, objectives, and constraints in the model."""
        counts_df = b.select(
            *[(b.count(item) | 0) for (_, item) in self._model_info.items()]
        ).to_df()
        if counts_df.shape != (1, 4):
            raise ValueError("Unexpected counts dataframe shape.")
        num_vars, num_min_objs, num_max_objs, num_constraints = counts_df.iloc[0]
        print(
            f"Solver model has {num_vars} variables, {num_min_objs} minimization objectives, {num_max_objs} maximization objectives, and {num_constraints} constraints."
        )

    def print(self, with_names: bool = False) -> None:
        """Print model components.

        Args:
            with_names: Whether to print expression string names (if available).
        """
        # Print variables
        var_df = b.select(self.Variable.name | "_").where(self.Variable).to_df()
        if var_df.empty:
            print("No variables defined.")
            return
        print("Solver model:")
        print()
        print(f"Variables ({var_df.shape[0]}):")
        self._print_dataframe(var_df)

        # Print components
        components = [
            (self.MinObjective, "Min objectives"),
            (self.MaxObjective, "Max objectives"),
            (self.Constraint, "Constraints"),
        ]
        printed_expr_ref = b.String.ref()
        for component_concept, component_label in components:
            selection = (
                [component_concept.name | "", printed_expr_ref]
                if with_names
                else [printed_expr_ref]
            )
            component_df = (
                b.select(*selection)
                .where(component_concept.printed_expr(printed_expr_ref))
                .to_df()
            )
            if not component_df.empty:
                print(f"{component_label} ({component_df.shape[0]}):")
                self._print_dataframe(component_df)

    # -------------------------------------------------------------------------
    # Solving and Result Handling
    # -------------------------------------------------------------------------

    def solve(
        self, solver: Solver, log_to_console: bool = False, **kwargs: Any
    ) -> None:
        """Solve the model.

        Args:
            solver: Solver instance.
            log_to_console: Whether to show solver output.
            **kwargs: Solver options and parameters.
        """
        options = {**kwargs, "version": 1}

        # Validate solver options
        for option_key, option_value in options.items():
            if not isinstance(option_key, str):
                raise TypeError(
                    f"Solver option keys must be strings, but got {type(option_key).__name__} for key {option_key!r}."
                )
            if not isinstance(option_value, (int, float, str, bool)):
                raise TypeError(
                    f"Solver option values must be int, float, str, or bool, "
                    f"but got {type(option_value).__name__} for option {option_key!r}."
                )

        # Three-phase solve process:
        # 1. Export model to Snowflake as protobuf
        # 2. Execute solver job (external solver reads from Snowflake)
        # 3. Extract and load results back into the model
        input_id = uuid.uuid4()
        model_uri = f"snowflake://APP_STATE.RAI_INTERNAL_STAGE/job-inputs/solver/{input_id}/model.binpb"
        sf_input_uri = f"snowflake://job-inputs/solver/{input_id}/model.binpb"
        payload: dict[str, Any] = {"solver": solver.solver_name.lower()}
        payload["options"] = options
        payload["model_uri"] = sf_input_uri

        executor = self._model._to_executor()
        if not isinstance(executor, RelExecutor):
            raise ValueError(f"Expected RelExecutor, got {type(executor).__name__}.")
        prefix_lowercase = f"solvermodel_{self._id}_"

        query_timeout_mins = kwargs.get("query_timeout_mins", None)
        config = self._model._config
        if (
            query_timeout_mins is None
            and (
                timeout_value := config.get(
                    "query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS
                )
            )
            is not None
        ):
            query_timeout_mins = int(timeout_value)
        config_file_path = getattr(config, "file_path", None)
        start_time = time.monotonic()
        remaining_timeout_minutes = query_timeout_mins

        # Step 1: Materialize the model and store it in Snowflake
        print("export model")
        # TODO(coey): Weird hack to avoid uninitialized properties error
        # This forces evaluation of the Variable concept before export
        b.select(b.count(self.Variable)).to_df()
        export_model_relation = f"""
        // TODO maybe only want to pass names if printing - like in old setup
        // Collect all model components into a relation for serialization
        def model_relation {{
            (:variable, {self.Variable._name});
            (:variable_name, {prefix_lowercase}variable_name);
            (:min_objective, {prefix_lowercase}minobjective_serialized);
            (:max_objective, {prefix_lowercase}maxobjective_serialized);
            (:constraint, {prefix_lowercase}constraint_serialized);
        }}

        @no_diagnostics(:EXPERIMENTAL)
        def model_string {{ rel_primitive_solverlib_model_string[model_relation] }}

        ic model_not_empty("Solver model is empty.") requires not empty(model_string)

        def config[:envelope, :content_type]: "application/octet-stream"
        def config[:envelope, :payload, :data]: model_string
        def config[:envelope, :payload, :path]: "{model_uri}"
        def export {{ config }}
        """
        executor.execute_raw(
            textwrap.dedent(export_model_relation),
            query_timeout_mins=remaining_timeout_minutes,
        )

        # Step 2: Execute solver job and wait for completion
        print("execute solver job")
        remaining_timeout_minutes = calc_remaining_timeout_minutes(
            start_time,
            query_timeout_mins,
            config_file_path=config_file_path,
        )
        job_id = solver._exec_job(
            payload,
            log_to_console=log_to_console,
            query_timeout_mins=remaining_timeout_minutes,
        )

        # Step 3: Extract and insert solver results into the model
        print("extract result")
        remaining_timeout_minutes = calc_remaining_timeout_minutes(
            start_time,
            query_timeout_mins,
            config_file_path=config_file_path,
        )
        extract_results_relation = f"""
        def raw_result {{
            load_binary["snowflake://APP_STATE.RAI_INTERNAL_STAGE/job-results/{job_id}/result.binpb"]
        }}

        ic result_not_empty("Solver result is empty.") requires not empty(raw_result)

        @no_diagnostics(:EXPERIMENTAL)
        def extracted {{ rel_primitive_solverlib_extract[raw_result] }}

        def delete[:{self.result_info._name}]: {self.result_info._name}
        def delete[:{self.point._name}]: {self.point._name}
        def delete[:{self.points._name}]: {self.points._name}

        def insert(:{self.result_info._name}, key, value):
            exists((original_key) | string(extracted[original_key], value) and ::std::mirror::lower(original_key, key))
        """
        if self._num_type == "int":
            insert_points_relation = f"""
            def insert(:{self.point._name}, variable, value):
                exists((float_value) | extracted(:point, variable, float_value) and
                    ::std::mirror::convert(std::mirror::typeof[Int128], float_value, value)
                )
            def insert(:{self.points._name}, point_index, variable, value):
                exists((float_index, float_value) | extracted(:points, variable, float_index, float_value) and
                    ::std::mirror::convert(std::mirror::typeof[Int128], float_index, point_index) and
                    ::std::mirror::convert(std::mirror::typeof[Int128], float_value, value)
                )
            """
        else:
            insert_points_relation = f"""
            def insert(:{self.point._name}, variable, value): extracted(:point, variable, value)
            def insert(:{self.points._name}, point_index, variable, value):
                exists((float_index) | extracted(:points, variable, float_index, value) and
                    ::std::mirror::convert(std::mirror::typeof[Int128], float_index, point_index)
                )
            """
        executor.execute_raw(
            textwrap.dedent(extract_results_relation)
            + textwrap.dedent(insert_points_relation),
            readonly=False,
            query_timeout_mins=remaining_timeout_minutes,
        )

        print("finished solve")
        print()

    def load_point(self, point_index: int) -> None:
        """Load a solution point.

        Args:
            point_index: Solution point index (0-based).
        """
        if not isinstance(point_index, int):
            raise TypeError(
                f"Point index must be an integer, but got {type(point_index).__name__}."
            )
        if point_index < 0:
            raise ValueError(
                f"Point index must be non-negative, but got {point_index}."
            )
        executor = self._model._to_executor()
        if not isinstance(executor, RelExecutor):
            raise ValueError(
                f"Expected RelExecutor, but got {type(executor).__name__}."
            )
        load_point_relation = f"""
        def delete[:{self.point._name}]: {self.point._name}
        def insert(:{self.point._name}, variable, value): {self.points._name}(int128[{point_index}], variable, value)
        """
        executor.execute_raw(textwrap.dedent(load_point_relation), readonly=False)

    def summarize_result(self) -> Any:
        """Print solver result summary.

        Returns:
            DataFrame with result information.
        """
        info_keys_to_retrieve = [
            "error",
            "termination_status",
            "solve_time_sec",
            "objective_value",
            "solver_version",
            "result_count",
        ]
        key, value_ref = b.String.ref(), b.String.ref()
        result_df = (
            b.select(key, value_ref)
            .where(self.result_info(key, value_ref), key.in_(info_keys_to_retrieve))
            .to_df()
        )
        if result_df.empty:
            raise ValueError(
                "No result information is available. Has the model been solved?"
            )
        print("Solver result:")
        print(result_df.to_string(index=False, header=False))
        print()
        return result_df

    def variable_values(self, multiple: bool = False) -> b.Fragment:
        """Retrieve variable values.

        Args:
            multiple: Whether to return all solution points.

        Returns:
            Fragment for selecting values.
        """
        variable_ref = self.Variable.ref()
        value_ref = (b.Integer if self._num_type == "int" else b.Float).ref()
        if multiple:
            point_index = b.Integer.ref()
            return b.select(point_index, variable_ref.name, value_ref).where(
                self.points(point_index, variable_ref, value_ref)
            )
        return b.select(variable_ref.name, value_ref).where(
            self.point(variable_ref, value_ref)
        )

    # Valid result info keys that can be accessed as attributes
    _RESULT_INFO_KEYS = frozenset(
        [
            "error",
            "termination_status",
            "solver_version",
            "printed_model",
            "solve_time_sec",
            "objective_value",
            "result_count",
        ]
    )

    def __getattr__(self, name: str) -> Any:
        """Get result attribute (e.g., num_variables, termination_status, objective_value).

        Args:
            name: Attribute name.

        Returns:
            Attribute value or None.
        """
        # Try to get dataframe from model info or result info
        if name in self._model_info:
            result_df = b.select(b.count(self._model_info[name]) | 0).to_df()
        elif name in self._RESULT_INFO_KEYS:
            value_ref = b.String.ref()
            result_df = (
                b.select(value_ref).where(self.result_info(name, value_ref)).to_df()
            )
        else:
            return None

        # Extract and convert scalar value
        if result_df.shape != (1, 1):
            raise ValueError(
                f"Expected exactly one value for attribute '{name}', "
                f"but got dataframe with shape {result_df.shape}."
            )

        result_value = result_df.iloc[0, 0]
        if not isinstance(result_value, str):
            return result_value

        # Convert string results to appropriate types
        if name == "solve_time_sec":
            return float(result_value)
        if name == "objective_value":
            return int(result_value) if self._num_type == "int" else float(result_value)
        if name == "result_count":
            return int(result_value)
        return result_value


# =============================================================================
# Symbolic Expression Classes
# =============================================================================


class Symbolic:
    """Wrapper for symbolified solver expressions."""

    def __init__(self, expr: Any) -> None:
        if isinstance(expr, Symbolic):
            raise TypeError("Cannot wrap a Symbolic expression in another Symbolic.")
        self.expr = expr


class SymbolifyContext:
    """Context for rewriting expressions into solver-compatible symbolic form."""

    def __init__(self, solver_model: SolverModelPB) -> None:
        self.model = solver_model._model
        self.solver_model = solver_model
        # Maps original variables (or refs) to symbolic variables bound in where clauses
        self.variable_map: dict[Any, Any] = {}

    # -------------------------------------------------------------------------
    # Public Rewriting Methods
    # -------------------------------------------------------------------------

    def rewrite_where(self, *exprs: Any) -> list[Any]:
        """Rewrite where clause expressions.

        Args:
            *exprs: Where clause expressions.

        Returns:
            Rewritten expressions.
        """
        rewritten_expressions: list[Any] = []
        # Two-pass strategy: first handle variable relationships to populate variable_map,
        # then rewrite other expressions that may reference those variables
        # First pass: identify and handle variable relationship expressions
        for expression in exprs:
            if (
                isinstance(expression, b.Expression)
                and isinstance(expression._op, b.Relationship)
                and expression._op in self.solver_model._variable_relationships
            ):
                rewritten_expressions.append(
                    self._handle_variable_relationship(expression)
                )
            else:
                rewritten_expressions.append(None)
        # Second pass: rewrite remaining non-variable expressions
        for i, expr in enumerate(exprs):
            if rewritten_expressions[i] is None:
                rewritten_expressions[i] = (
                    expr
                    if expr in self.variable_map
                    else self._rewrite_nonsymbolic(expr)
                )
        return rewritten_expressions

    def rewrite(self, expr: Any) -> Optional[Symbolic | Any]:
        """Rewrite expressions to symbolify solver variables."""
        if expr is None:
            return None

        elif isinstance(expr, (int, float, str)):
            return None

        elif isinstance(expr, b.ConceptFilter):
            concept = expr._op
            assert isinstance(concept, b.Concept)
            (ident, kwargs) = expr._params
            assert ident is None
            assert isinstance(kwargs, dict)
            new_kwargs = {}
            values_were_rewritten = False
            for key, value in kwargs.items():
                rewritten_value = self.rewrite(value)
                if isinstance(rewritten_value, Symbolic):
                    raise ValueError(
                        f"Cannot symbolify ConceptFilter argument {key} with symbolic value."
                    )
                if rewritten_value is not None:
                    values_were_rewritten = True
                    new_kwargs[key] = rewritten_value
                else:
                    new_kwargs[key] = value
            if values_were_rewritten:
                return b.ConceptFilter(concept, ident, new_kwargs)
            return None

        elif isinstance(expr, (b.DataColumn, b.TypeRef, b.Concept)):
            return None

        elif isinstance(expr, b.Alias):
            return self.rewrite(expr._thing)

        elif isinstance(expr, b.Ref):
            if expr in self.variable_map:
                return Symbolic(self.variable_map[expr])
            thing = self.rewrite(expr._thing)
            if thing is not None:
                raise ValueError(
                    f"Internal error. Ref._thing rewrite unexpectedly returned {thing}."
                )
            return None

        elif isinstance(expr, b.Relationship):
            if expr in self.variable_map:
                return Symbolic(self.variable_map[expr])
            variable_result = self._get_variable_ref(expr, expr._parent)
            if variable_result is not None:
                self.variable_map[expr] = variable_result
                return Symbolic(variable_result)
            return None

        elif isinstance(expr, b.RelationshipRef):
            if expr in self.variable_map:
                return Symbolic(self.variable_map[expr])
            relationship = expr._relationship
            if isinstance(relationship, b.Relationship):
                variable_result = self._get_variable_ref(relationship, expr._parent)
                if variable_result is not None:
                    self.variable_map[expr] = variable_result
                    return Symbolic(variable_result)
            rewritten_parent = self.rewrite(expr._parent)
            if isinstance(rewritten_parent, Symbolic):
                raise ValueError(
                    "Internal error. RelationshipRef parent rewrite returned Symbolic."
                )
            if rewritten_parent is not None:
                return b.RelationshipRef(rewritten_parent, relationship)
            return None

        elif isinstance(expr, b.RelationshipFieldRef):
            relationship = expr._relationship
            if not isinstance(relationship, b.Relationship):
                # TODO(coey): Handle relationship:RelationshipReading
                return None

            # Rewrite the relationship reference
            relationship_expression = (
                relationship
                if expr._parent is None
                else b.RelationshipRef(expr._parent, relationship)
            )
            variable_result = self.rewrite(relationship_expression)
            if variable_result is None:
                return None

            # Handle symbolic result - return as-is if it's the last field
            if isinstance(variable_result, Symbolic):
                if expr._field_ix == len(relationship._fields) - 1:
                    return variable_result
                variable_result = variable_result.expr

            return getattr(variable_result, relationship._field_names[expr._field_ix])

        elif isinstance(expr, b.Expression):
            operator = self.rewrite(expr._op)
            if isinstance(operator, Symbolic):
                raise ValueError(
                    "Internal error: Expression operator rewrite returned Symbolic."
                )
            params_were_rewritten = False
            has_symbolic_params = False
            params = []
            for param in expr._params:
                rewritten_param = self.rewrite(param)
                if isinstance(rewritten_param, Symbolic):
                    has_symbolic_params = True
                    params_were_rewritten = True
                    params.append(rewritten_param.expr)
                elif rewritten_param is not None:
                    params_were_rewritten = True
                    params.append(rewritten_param)
                else:
                    params.append(param)
            if operator is not None:
                if has_symbolic_params:
                    raise NotImplementedError(
                        f"Solver rewrites cannot handle expression {expr} "
                        f"with both a symbolic operator and symbolic parameters."
                    )
                return b.Expression(operator, *params)
            if not has_symbolic_params:
                return b.Expression(expr._op, *params)
            if not params_were_rewritten:
                return None

            # Some arguments involve solver variables, so rewrite into solver protobuf format
            # This converts operations like x + y into fo_appl(ADD_OP, (x, y), res)
            if not has_symbolic_params:
                raise ValueError(
                    "Internal error. Expected symbolic parameters but none were found."
                )
            if not isinstance(expr._op, b.Relationship):
                raise NotImplementedError(
                    f"Solver rewrites cannot handle expression {expr} "
                    f"with operator type {type(expr._op).__name__}."
                )
            operator_name = expr._op._name
            if not isinstance(operator_name, str):
                raise ValueError(
                    f"Internal error. Operator name is {type(operator_name).__name__}, expected str."
                )
            if operator_name in _FIRST_ORDER_OPERATOR_CODES:
                return Symbolic(
                    _make_first_order_application(
                        _FIRST_ORDER_OPERATOR_CODES[operator_name], *params
                    )
                )
            elif operator_name in _FIRST_ORDER_COMPARISON_CODES:
                return Symbolic(
                    _make_first_order_application_with_result(
                        _FIRST_ORDER_COMPARISON_CODES[operator_name], *params
                    )
                )
            else:
                raise NotImplementedError(
                    f"Solver rewrites cannot handle operator '{operator_name}'."
                )

        elif isinstance(expr, b.Aggregate):
            # Only the last argument can be symbolic
            preceding_args = [self._rewrite_nonsymbolic(arg) for arg in expr._args[:-1]]
            group = [self._rewrite_nonsymbolic(arg) for arg in expr._group]
            # TODO(coey): Should this be done with a subcontext (for variable_map)?
            where = self.rewrite_where(*expr._where._where)
            rewritten = (
                preceding_args != expr._args[:-1]
                or group != expr._group
                or where != expr._where
            )
            symbolic_arg = self.rewrite(expr._args[-1])
            if symbolic_arg is None and not rewritten:
                return None
            if not isinstance(symbolic_arg, Symbolic):
                if symbolic_arg is None:
                    symbolic_arg = expr._args[-1]
                aggregate_expr = b.Aggregate(expr._op, *preceding_args, symbolic_arg)
                return aggregate_expr.per(*group).where(*where)

            # The last argument is symbolic - convert to higher-order application
            # Example: sum(x for x in variables) becomes ho_appl(..., x, SUM_OP)
            operator_name = expr._op._name
            if not isinstance(operator_name, str):
                raise ValueError(
                    f"Internal error. Aggregate operator name is {type(operator_name).__name__}, expected str."
                )
            if operator_name not in _HIGHER_ORDER_OPERATOR_CODES:
                raise NotImplementedError(
                    f"Solver rewrites cannot handle aggregate operator '{operator_name}'. "
                    f"Supported operators: {', '.join(_HIGHER_ORDER_OPERATOR_CODES.keys())}"
                )
            higher_order_application_builtin = b.Relationship.builtins[
                "rel_primitive_solverlib_ho_appl"
            ]
            aggregate_expr = b.Aggregate(
                higher_order_application_builtin,
                *preceding_args,
                symbolic_arg.expr,
                _HIGHER_ORDER_OPERATOR_CODES[operator_name],
            )
            return Symbolic(aggregate_expr.per(*group).where(*where))

        elif isinstance(expr, b.Union):
            # Return union of the symbolified expressions, if any are symbolic
            args_were_rewritten = False
            has_symbolic_args = False
            args = []
            for union_arg in expr._args:
                rewritten_arg = self.rewrite(union_arg)
                if isinstance(rewritten_arg, Symbolic):
                    has_symbolic_args = True
                    args.append(rewritten_arg.expr)
                elif rewritten_arg is not None:
                    args_were_rewritten = True
                    args.append(rewritten_arg)
                else:
                    args.append(union_arg)
            if has_symbolic_args:
                return Symbolic(b.union(*args))
            elif args_were_rewritten:
                return b.union(*args)
            return None

        elif isinstance(expr, b.Fragment):
            # Only support selects with one item
            if expr._define or expr._require:
                raise ValueError(
                    "Solver rewrites do not support fragments with define or require clauses."
                )
            if len(expr._select) != 1:
                raise ValueError(
                    f"Solver rewrites require fragments with exactly one select item, "
                    f"but got {len(expr._select)}."
                )
            # TODO(coey): Should this be done with a subcontext (for variable_map)?
            where = self.rewrite_where(*expr._where)
            symbolic_select = self.rewrite(expr._select[0])
            if isinstance(symbolic_select, Symbolic):
                return Symbolic(b.select(symbolic_select.expr).where(*where))
            elif symbolic_select is not None:
                return b.select(symbolic_select).where(*where)
            return None

        raise NotImplementedError(
            f"Solver rewrites cannot handle {expr} of type {type(expr).__name__}."
        )

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _handle_variable_relationship(self, expr: b.Expression) -> Any:
        """Create symbolic reference for variable relationship expression."""
        relationship = expr._op
        if not isinstance(relationship, b.Relationship):
            raise TypeError(
                f"Expected Relationship in variable expression, but got {type(relationship).__name__}."
            )
        params = expr._params
        if len(params) != len(relationship._fields):
            raise ValueError(
                f"Parameter count mismatch: Got {len(params)} params "
                f"but relationship has {len(relationship._fields)} fields."
            )
        last_param = params[-1]
        if isinstance(last_param, b.Alias):
            last_param = last_param._thing
        if not isinstance(last_param, (b.Concept, b.Ref)):
            raise TypeError(
                f"Last parameter must be a Concept or Ref, but got {type(last_param).__name__}."
            )
        # Extract and rewrite field parameters to build the symbolic variable reference
        # This maps the relationship fields to their grounding values
        fields = {}
        for i in range(len(params) - 1):
            rewritten_param = self.rewrite(params[i])
            assert not isinstance(rewritten_param, Symbolic)
            fields[relationship._field_names[i]] = (
                rewritten_param if rewritten_param is not None else params[i]
            )
        # Create new ref corresponding to the decision variable
        variable_ref = self.solver_model._variable_relationships[relationship].ref()
        self.variable_map[last_param] = variable_ref
        # Return new condition to ground the variable
        return b.where(
            *[
                getattr(variable_ref, field_name) == field_value
                for field_name, field_value in fields.items()
            ]
        )

    def _rewrite_nonsymbolic(self, expr: Any) -> Any:
        """Rewrite expression ensuring non-symbolic result."""
        new_expr = self.rewrite(expr)
        if isinstance(new_expr, Symbolic):
            raise ValueError(
                f"Internal error. Non-symbolic rewrite unexpectedly returned Symbolic for {expr}."
            )
        return expr if new_expr is None else new_expr

    def _get_variable_ref(
        self, relationship: b.Relationship, parent_producer: b.Producer | None
    ) -> Optional[Any]:
        """Get variable reference for relationship, or None if not a solver variable."""
        # Check if this relationship corresponds to a decision variable
        VariableConcept = self.solver_model._variable_relationships.get(relationship)
        if VariableConcept is None:
            return None

        properties = {}
        if parent_producer is not None:
            properties[relationship._field_names[0]] = parent_producer
        return VariableConcept(VariableConcept.ref(), **properties)
