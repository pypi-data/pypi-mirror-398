"""
Converter for Snowflake config.toml to RAI Config format.
"""

from __future__ import annotations

from typing import Any

from .snowflake_models import SnowflakeConfigFile


def convert_snowflake_to_rai(
    sf_config: dict[str, Any],
    connection_name: str | None = None
) -> dict[str, Any]:
    config_file = SnowflakeConfigFile(**sf_config)

    # Determine connection to use (default_connection_name validity checked by model)
    if not connection_name:
        if config_file.default_connection_name:
            connection_name = config_file.default_connection_name
        elif "default" in config_file.connections:
            connection_name = "default"
        else:
            connection_name = next(iter(config_file.connections.keys()))

    if connection_name not in config_file.connections:
        available = list(config_file.connections.keys())
        raise ValueError(
            f"Connection '{connection_name}' not found. Available connections: {available}"
        )

    connection = config_file.connections[connection_name]

    # Convert connection using the model's convert() method
    connection_dict = connection.convert()

    return {
        "connections": {"snowflake": connection_dict},
        "default_connection": "snowflake",
    }
