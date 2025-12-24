from __future__ import annotations
import sys
from typing import Any

from ..clients.config import Config
from .base import SessionEnvironment
from .ipython import IPythonEnvironment

class HexEnvironment(IPythonEnvironment, SessionEnvironment):
    remote = True

    @classmethod
    def detect(cls):
        return "hex" in sys.modules or "hex_data_service" in sys.modules or "hex_api" in sys.modules

    def configure_session(self, config: Config, session: Any | None = None):
        # @NOTE: I have no idea why the exception when user is present exists,
        #        it was copied verbatim from the earlier session setup logic.
        if not session and config.get("user", None) is None:
            raise ValueError("A Session object should be provided when running in Hex. Import `hextoolkit` and supply `connection=hextoolkit.get_data_connection('<your connection name>').get_snowpark_session()` as an argument to `Model`.")

        return session
