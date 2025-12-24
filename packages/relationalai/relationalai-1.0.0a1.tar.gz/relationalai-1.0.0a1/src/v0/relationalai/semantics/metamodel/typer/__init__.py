"""
Type inference and checking for the IR.
"""
from .typer import InferTypes
from .checker import Checker

__all__ = ['InferTypes', 'Checker']