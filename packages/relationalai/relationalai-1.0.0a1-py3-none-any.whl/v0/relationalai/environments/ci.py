from __future__ import annotations
import os

from .generic import GenericEnvironment

class CIEnvironment(GenericEnvironment):
    @classmethod
    def detect(cls):
        """Detect if we're running in a CI environment."""
        # Check for actual CI environments (not just environment variables that might be set locally)
        if os.getenv("CI") == "true" and (
            os.getenv("GITHUB_ACTIONS") == "true" or
            os.getenv("GITLAB_CI") == "true" or
            os.getenv("JENKINS_URL") or
            os.getenv("TRAVIS") == "true" or
            os.getenv("CIRCLECI") == "true"
        ):
            return True

        # Check for GitHub Actions specifically (more reliable than GITHUB_REF_NAME)
        if os.getenv("GITHUB_ACTIONS") == "true":
            return True

        return False
