"""Optimization and constraint programming solver interfaces.

This package provides solver model interfaces for defining and solving
mathematical optimization and constraint programming problems using
RelationalAI's solver infrastructure.
"""

from __future__ import annotations

from typing import Union
import warnings

from v0.relationalai.experimental.solvers import Provider, Solver
from v0.relationalai.semantics.internal import Model

from .common import all_different, implies, make_name, special_ordered_set_type_2
from .solvers_dev import SolverModelDev
from .solvers_pb import SolverModelPB

__version__ = "0.0.0"


# Copied from graphs library:
# warn on import that this package is at an early stage of development.
warnings.warn(
    (
        "\n\nThis library is still in early stages of development and is intended "
        "for internal use only. Among other considerations, interfaces will change, "
        "and performance is appropriate only for relatively small problems. Please "
        "see this package's README for additional information.\n\n"
        "If you are an internal user seeing this, please also contact "
        "the symbolic reasoning team such that we can track usage, get "
        "feedback, and help you through breaking changes.\n"
    ),
    FutureWarning,
    stacklevel=2
)


def SolverModel(
    model: Model, num_type: str, use_pb: bool = True
) -> Union[SolverModelPB, SolverModelDev]:
    """Create a solver model for an optimization or constraint programming problem.

    Args:
        model: The RelationalAI model to attach the solver to.
        num_type: Numeric type for decision variables ('cont' or 'int').
        use_pb: Whether to use protobuf format (True) or development format (False).
            Defaults to True. Note: protobuf format will be deprecated in favor
            of the development format.

    Returns:
        A SolverModelPB or SolverModelDev instance.
    """
    return (SolverModelPB if use_pb else SolverModelDev)(model, num_type)


__all__ = [
    "Solver",
    "Provider",
    "SolverModel",
    "SolverModelPB",
    "SolverModelDev",
    "make_name",
    "all_different",
    "implies",
    "special_ordered_set_type_2",
]
