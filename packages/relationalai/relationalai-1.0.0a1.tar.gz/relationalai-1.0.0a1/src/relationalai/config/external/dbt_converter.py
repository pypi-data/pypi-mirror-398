"""
Converter for DBT profiles.yml to RAI Config format.
"""

from __future__ import annotations

import os
import re
from typing import Any

from .dbt_models import DBTProfile, DBTProfilesFile


def render_jinja_value(value: str) -> str:
    """
    Render Jinja2 env_var() templates in DBT profiles.

    Supports: {{ env_var('VAR_NAME') }} or {{ env_var("VAR_NAME") }}
    """
    pattern = r"\{\{\s*env_var\(['\"]([^'\"]+)['\"]\)\s*\}\}"

    def replace_env_var(match):
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            raise ValueError(
                f"Environment variable '{var_name}' referenced in profiles.yml is not set"
            )
        return env_value

    return re.sub(pattern, replace_env_var, value)


def process_value(value: Any) -> Any:
    if isinstance(value, str):
        return render_jinja_value(value)
    elif isinstance(value, dict):
        return {k: process_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [process_value(v) for v in value]
    else:
        return value


def convert_dbt_to_rai(
    dbt_profiles: dict[str, Any],
    profile_name: str | None = None,
    target_name: str | None = None
) -> dict[str, Any]:
    profiles_file = DBTProfilesFile(**dbt_profiles)
    dbt_profiles = profiles_file.model_dump()

    dbt_profiles = process_value(dbt_profiles)

    if not profile_name:
        profile_name = os.environ.get("DBT_PROFILE")

    if not profile_name:
        profile_names = [k for k in dbt_profiles.keys() if k != "config" and not k.startswith("config_")]
        if not profile_names:
            raise ValueError("No profiles found in profiles.yml")
        profile_name = profile_names[0]

    if profile_name not in dbt_profiles:
        available = [k for k in dbt_profiles.keys() if k != "config"]
        raise ValueError(
            f"Profile '{profile_name}' not found. Available profiles: {available}"
        )

    profile_data = dbt_profiles[profile_name]
    profile = DBTProfile(**profile_data)

    # outputs existence validated by DBTProfile model
    # Get target (from parameter, env var, target field, or 'dev')
    if not target_name:
        target_name = os.environ.get("DBT_TARGET")
    if not target_name:
        target_name = profile.target
    if not target_name:
        # Try 'dev' first, then first output
        if "dev" in profile.outputs:
            target_name = "dev"
        else:
            target_name = next(iter(profile.outputs.keys()))

    if target_name not in profile.outputs:
        available = list(profile.outputs.keys())
        raise ValueError(
            f"Target '{target_name}' not found in profile '{profile_name}'. "
            f"Available targets: {available}"
        )

    output = profile.outputs[target_name]

    connection = output.convert()
    connection_name = output.provider

    return {
        "connections": {connection_name: connection},
        "default_connection": connection_name,
    }
