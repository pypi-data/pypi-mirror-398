from typing import cast

from v0.relationalai.clients.config import Config
from v0.relationalai.clients.snowflake import Resources, ResourcesBase
from v0.relationalai.environments import runtime_env, SnowbookEnvironment

def configure_otel(enable_otel_handler: bool, config: Config, resources: ResourcesBase):
    # allow to enable the OpenTelemetry handler only for internal snowflake accounts
    # Skip OTEL handling entirely for warehouse environments,
    # skipping is possible because it is not set up in the warehouse environment
    if isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner == "warehouse":
        pass
    elif (
            enable_otel_handler
            and config.get("platform") == "snowflake"
            and config.is_internal_account()
    ):
        from .otel_handler import enable_otel_export
        enable_otel_export(
            cast(Resources, resources),
            config.get('rai_app_name', 'RELATIONALAI')
        )
    else:
        from .otel_handler import disable_otel_handling
        disable_otel_handling()
