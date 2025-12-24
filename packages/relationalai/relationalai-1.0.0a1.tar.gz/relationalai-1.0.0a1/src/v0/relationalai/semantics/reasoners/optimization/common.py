"""Common utilities for solver models.

This module provides shared helper functions and constraint constructors used
across solver model implementations (both protobuf and development versions).
"""

from __future__ import annotations

from typing import Any, Optional, Union

from v0.relationalai.semantics import std
from v0.relationalai.semantics.internal import internal as b


# =============================================================================
# Utilities
# =============================================================================


def make_name(*args, sep: Optional[str] = "_") -> Union[str, b.Expression]:
    """Construct a name by concatenating arguments into a string expression.

    Args:
        *args: Arguments to concatenate (strings, numbers, or lists).
        sep: Separator between arguments. Defaults to "_", use None for no separator.

    Returns:
        A string or expression representing the concatenated name.
    """
    if not args:
        raise ValueError("No arguments provided to `make_name`")
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, str):
            return arg
        elif isinstance(arg, list):
            return make_name(*arg, sep=sep)
        else:
            return std.strings.string(arg)
    elif sep:
        str_args = []
        for a in args:
            str_args.append(std.strings.string(a))
            str_args.append(sep)
        str_args.pop()
    else:
        str_args = map(std.strings.string, args)
    return std.strings.concat(*str_args)


# =============================================================================
# Constraint Constructors
# =============================================================================


def all_different(*args: Any) -> b.Aggregate:
    """Create an all_different constraint requiring all arguments to have distinct values.

    Args:
        *args: Variables or expressions that must all have different values.
    """
    return b.Aggregate(b.Relationship.builtins["all_different"], *args)


def implies(left: Any, right: Any) -> b.Expression:
    """Create a logical implication constraint (left => right).

    Args:
        left: The antecedent (condition) of the implication.
        right: The consequent (result) of the implication.
    """
    return b.Expression(b.Relationship.builtins["implies"], left, right)


def special_ordered_set_type_2(rank: Any, variables: Any) -> b.Aggregate:
    """Create a special ordered set type 2 (SOS2) constraint.

    In an SOS2 constraint, at most two variables can be non-zero, and they
    must be consecutive in the given order. This is useful for piecewise-linear
    approximations where the variables represent weights on ordered breakpoints.

    Args:
        rank: An expression that specifies the order/rank of each variable.
            Variables are ordered by their rank values to determine which pairs
            are consecutive.
        variables: The decision variables that form the special ordered set.
    """
    return b.Aggregate(b.Relationship.builtins["special_ordered_set_type_2"], rank, variables)
