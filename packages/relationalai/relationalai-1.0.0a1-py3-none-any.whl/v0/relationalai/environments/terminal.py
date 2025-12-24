from __future__ import annotations
import sys
import os

from .generic import GenericEnvironment

class TerminalEnvironment(GenericEnvironment):
    @classmethod
    def detect(cls):
        """Detect if we're running in a console/terminal environment."""
        # First, check if we're in CI - if so, we're not in a terminal
        from .ci import CIEnvironment
        if CIEnvironment.detect():
            return False

        # Check for actual terminal/console environment
        # Must have TTY attached and be interactive
        if (hasattr(sys, 'stdin') and sys.stdin.isatty() and
            hasattr(sys, 'stdout') and sys.stdout.isatty()):

            # Check for common terminal environment variables
            terminal_vars = ['TERM', 'COLORTERM', 'SSH_CLIENT', 'SSH_CONNECTION']
            if any(os.getenv(var) for var in terminal_vars):
                return True

            # Check if we have an interactive shell (ps1/ps2 attributes)
            if hasattr(sys, 'ps1') or hasattr(sys, 'ps2'):
                return True

        return False
