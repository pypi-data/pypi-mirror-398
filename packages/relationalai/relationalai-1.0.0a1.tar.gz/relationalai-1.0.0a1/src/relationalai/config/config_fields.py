"""
Nested configuration field models for the multi-connection config system.

This module defines nested config models:
- EngineConfig: Engine execution settings
- DataConfig: Data loading and streaming settings
- CompilerConfig: Compiler-specific settings
- ModelConfig: Model execution settings
- ReasonerConfig: Reasoner execution settings (including nested ReasonerRuleConfig)
- DebugConfig: Debug server settings

These models are used in Config (with default instances) and Profile (as optional overrides).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EngineConfig(BaseModel):
    name: str | None = Field(default=None, description="Engine name for execution")
    size: str | None = Field(default=None, description="Size of the engine")
    auto_suspend_mins: int | None = Field(default=None, description="Auto-suspend engine after N minutes")
    show_all_sizes: bool = Field(
        default=False,
        description="Show all available engine sizes"
    )


class DataConfig(BaseModel):
    wait_for_stream_sync: bool = Field(default=True, description="Wait for stream synchronization before processing")
    ensure_change_tracking: bool = Field(default=False, description="Enable change tracking for data modifications")
    data_freshness_mins: int | None = Field(default=None, description="Data freshness timeout in minutes")
    query_timeout_mins: int | None = Field(
        default=None,
        description="Query timeout in minutes - aborts queries that exceed this duration"
    )
    download_url_type: Literal["internal", "external"] | None = Field(
        default=None,
        description="Type of download URL for data exports (internal or external)"
    )
    check_column_types: bool = Field(
        default=True,
        description="Check column types during data loading"
    )


class CompilerConfig(BaseModel):
    use_monotype_operators: bool = Field(default=False, description="Use monotype operators in compilation")
    show_corerel_errors: bool = Field(default=True, description="Show CoreRel error messages")
    dry_run: bool = Field(default=False, description="Run compilation in dry-run mode")
    inspect_df: bool = Field(default=False, description="Inspect DataFrame during compilation")
    use_value_types: bool = Field(default=False, description="Use value types in compilation")
    debug_hidden_keys: bool = Field(default=False, description="Debug hidden keys in compilation")
    wide_outputs: bool = Field(default=False, description="Use wide output format for query results")
    strict: bool = Field(default=False, description="Enable strict validation mode")

    # Experimental compiler optimizations
    use_inlined_intermediates: bool = Field(default=False, description="Use inlined intermediate results")
    inline_value_maps: bool = Field(default=False, description="Inline value maps in weaver")
    inline_entity_maps: bool = Field(default=False, description="Inline entity maps in weaver")


class ModelConfig(BaseModel):
    keep: bool = Field(default=False, description="Keep model after execution")
    isolated: bool = Field(default=True, description="Run model in isolated mode")
    nowait_durable: bool = Field(default=True, description="Don't wait for durable operations")


class ReasonerRuleConfig(BaseModel):
    use_lqp: bool = Field(default=True, description="Use LQP for reasoner rule execution")


class ReasonerConfig(BaseModel):
    rule: ReasonerRuleConfig = Field(default_factory=ReasonerRuleConfig)
    use_sql: bool = Field(default=False, description="Use SQL execution instead of LQP")


class DebugConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable debug mode")
    host: str | None = Field(default=None, description="Debug server host")
    port: int = Field(default=8080, description="Debug server port")
    show_debug_logs: bool = Field(default=False, description="Show debug log messages")
    show_full_traces: bool = Field(default=False, description="Show full stack traces in errors")
