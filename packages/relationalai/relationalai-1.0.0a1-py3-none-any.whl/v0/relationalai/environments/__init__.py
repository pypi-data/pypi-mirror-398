from __future__ import annotations
from typing import Type

from v0.relationalai.environments.base import NotebookRuntimeEnvironment, RuntimeEnvironment, SessionEnvironment
from .generic import GenericEnvironment
from .ipython import IPythonEnvironment
from .jupyter import JupyterEnvironment
from .hex import HexEnvironment
from .colab import ColabEnvironment
from .snowbook import SnowbookEnvironment
from .ci import CIEnvironment
from .terminal import TerminalEnvironment

SessionEnvironment = SessionEnvironment # re-export
NotebookRuntimeEnvironment = NotebookRuntimeEnvironment # re-export

# @NOTE: in order of precedence
ENVIRONMENTS: list[Type[RuntimeEnvironment]] = [
    SnowbookEnvironment,
    ColabEnvironment,
    HexEnvironment,
    JupyterEnvironment,
    IPythonEnvironment,
    CIEnvironment,
    TerminalEnvironment,
    GenericEnvironment
]

# The active environment, used for all env-specific logic.
runtime_env: RuntimeEnvironment = None # type: ignore

for Environment in ENVIRONMENTS:
    if Environment.detect():
        runtime_env = Environment()
        break
