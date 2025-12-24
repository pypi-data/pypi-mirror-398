from __future__ import annotations

from typing import Iterable, Dict, Optional, List, cast, TYPE_CHECKING
import json
import logging
import uuid

from v0.relationalai import debugging
from v0.relationalai.clients.cache_store import GraphIndexCache
from v0.relationalai.clients.util import (
    get_pyrel_version,
    normalize_datetime,
    poll_with_specified_overhead,
)
from v0.relationalai.errors import (
    ERPNotRunningError,
    EngineProvisioningFailed,
    SnowflakeChangeTrackingNotEnabledException,
    SnowflakeTableObjectsException,
    SnowflakeTableObject,
)
from v0.relationalai.tools.cli_controls import (
    DebuggingSpan,
    create_progress,
    TASK_CATEGORY_INDEXING,
    TASK_CATEGORY_PROVISIONING,
    TASK_CATEGORY_CHANGE_TRACKING,
    TASK_CATEGORY_CACHE,
    TASK_CATEGORY_RELATIONS,
    TASK_CATEGORY_STATUS,
    TASK_CATEGORY_VALIDATION,
)
from v0.relationalai.tools.constants import WAIT_FOR_STREAM_SYNC, Generation

# Set up logger for this module
logger = logging.getLogger(__name__)


try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None

if TYPE_CHECKING:
    from v0.relationalai.clients.snowflake import Resources
    from v0.relationalai.clients.snowflake import DirectAccessResources

# Maximum number of items to show individual subtasks for
# If more items than this, show a single summary subtask instead
MAX_INDIVIDUAL_SUBTASKS = 5

# Special engine name for CDC managed engine
CDC_MANAGED_ENGINE = "CDC_MANAGED_ENGINE"

# Maximum number of data source subtasks to show simultaneously
# When one completes, the next one from the queue will be added
MAX_DATA_SOURCE_SUBTASKS = 10

# How often to check ERP status (every N iterations)
# To limit performance overhead, we only check ERP status periodically
ERP_CHECK_FREQUENCY = 15

# Polling behavior constants
POLL_OVERHEAD_RATE = 0.1  # Overhead rate for exponential backoff
POLL_MAX_DELAY = 2.5  # Maximum delay between polls in seconds

# SQL query template for getting stream column hashes
# This query calculates a hash of column metadata (name, type, precision, scale, nullable)
# to detect if source table schema has changed since stream was created
STREAM_COLUMN_HASH_QUERY = """
WITH stream_columns AS (
    SELECT
        fq_object_name,
        HASH(
            value:name::VARCHAR,
            CASE
                WHEN value:precision IS NOT NULL AND value:scale IS NOT NULL THEN CASE value:type::VARCHAR
                    WHEN 'FIXED' THEN 'NUMBER'
                    WHEN 'REAL' THEN 'FLOAT'
                    WHEN 'TEXT' THEN 'TEXT'
                    ELSE value:type::VARCHAR
                END || '(' || value:precision || ',' || value:scale || ')'
                WHEN value:precision IS NOT NULL AND value:scale IS NULL THEN CASE value:type::VARCHAR
                    WHEN 'FIXED' THEN 'NUMBER'
                    WHEN 'REAL' THEN 'FLOAT'
                    WHEN 'TEXT' THEN 'TEXT'
                    ELSE value:type::VARCHAR
                END || '(0,' || value:precision || ')'
                WHEN value:length IS NOT NULL THEN CASE value:type::VARCHAR
                    WHEN 'FIXED' THEN 'NUMBER'
                    WHEN 'REAL' THEN 'FLOAT'
                    WHEN 'TEXT' THEN 'TEXT'
                    ELSE value:type::VARCHAR
                END || '(' || value:length || ')'
                ELSE CASE value:type::VARCHAR
                    WHEN 'FIXED' THEN 'NUMBER'
                    WHEN 'REAL' THEN 'FLOAT'
                    WHEN 'TEXT' THEN 'TEXT'
                    ELSE value:type::VARCHAR
                END
            END,
            IFF(value:nullable::BOOLEAN, 'YES', 'NO')
        ) AS column_signature
    FROM {app_name}.api.data_streams,
        LATERAL FLATTEN(input => columns)
    WHERE rai_database = '{rai_database}'
        AND fq_object_name IN ({fqn_list})
)
SELECT
    fq_object_name AS FQ_OBJECT_NAME,
    HEX_ENCODE(HASH_AGG(column_signature)) AS STREAM_HASH
FROM stream_columns
GROUP BY fq_object_name;
"""


class UseIndexPoller:
    """
    Encapsulates the polling logic for `use_index` streams.
    """

    def _add_stream_subtask(self, progress, fq_name: str, status: str, batches_count: int) -> bool:
        """Add a stream subtask if we haven't reached the limit.

        Returns:
            True if subtask was added, False if limit reached
        """
        if fq_name not in self.stream_task_ids and len(self.stream_task_ids) < MAX_DATA_SOURCE_SUBTASKS:
            # Get the position in the stream order (should already be there)
            if fq_name in self.stream_order:
                stream_position = self.stream_order.index(fq_name) + 1
            else:
                # Fallback if not in order (shouldn't happen)
                stream_position = 1

            # Build initial message based on status and batch count
            if status == "synced":
                initial_message = f"{fq_name} already synced"
            elif batches_count > 0:
                # Show stream position (x/y) before batch count
                initial_message = f"Syncing {fq_name} ({stream_position}/{self.total_streams}), batches: {batches_count}"
            else:
                initial_message = f"Syncing {fq_name} ({stream_position}/{self.total_streams})"

            self.stream_task_ids[fq_name] = progress.add_sub_task(initial_message, task_id=fq_name, category=TASK_CATEGORY_INDEXING)

            # Complete immediately if already synced (without recording completion time)
            if status == "synced":
                progress.complete_sub_task(fq_name, record_time=False)

            return True
        return False

    def __init__(
        self,
        resource: "Resources",
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: Optional[str],
        language: str = "rel",
        program_span_id: Optional[str] = None,
        headers: Optional[Dict] = None,
        generation: Optional[Generation] = None,
    ):
        self.res = resource
        self.app_name = app_name
        self.sources = list(sources)
        self.model = model
        self.engine_name = engine_name
        self.engine_size = engine_size or self.res.config.get_default_engine_size()
        self.language = language
        self.program_span_id = program_span_id
        self.headers = headers or {}
        self.counter = 1
        self.check_ready_count = 0
        self.tables_with_not_enabled_change_tracking: List = []
        self.table_objects_with_other_errors: List = []
        self.engine_errors: List = []
        # Flag to only ensure the engine is created asynchronously the initial call
        self.init_engine_async = True
        # Initially, we assume that cdc is not checked,
        # then on subsequent calls, if we get if cdc is enabled, if it is not, we will check it
        # on every 5th iteration we reset the cdc status, so it will be checked again
        self.should_check_cdc = True

        self.wait_for_stream_sync = self.res.config.get(
            "wait_for_stream_sync", WAIT_FOR_STREAM_SYNC
        )
        current_user = self.res.get_sf_session().get_current_user()
        assert current_user is not None, "current_user must be set"
        self.data_freshness = self.res.config.get_data_freshness_mins()
        self.cache = GraphIndexCache(current_user, model, self.data_freshness, self.sources)
        self.sources = self.cache.choose_sources()
        # execution_id is allowed to group use_index call, which belongs to the same loop iteration
        self.execution_id = str(uuid.uuid4())

        self.pyrel_version = get_pyrel_version(generation)

        self.source_info = self.res._check_source_updates(self.sources)

        # Track subtask IDs for streams, engines, and relations across multiple poll iterations
        self.stream_task_ids = {}
        self.engine_task_ids = {}
        self.relations_task_id = None
        self._erp_check_task_id = None

        # Track total number of streams and current stream position for (x/y) progress display
        self.total_streams = 0
        self.stream_position = 0
        self.stream_order = []  # Track the order of streams as they appear in data

        # Timing will be tracked by TaskProgress

    def poll(self) -> None:
        """
        Standard stream-based polling for use_index.
        """
        # Read show_duration_summary config flag (defaults to True for backward compatibility)
        show_duration_summary = bool(self.res.config.get("show_duration_summary", True))

        with create_progress(
            description="Initializing data index",
            success_message="",  # We'll handle this in the context manager
            leading_newline=True,
            trailing_newline=True,
            show_duration_summary=show_duration_summary,
        ) as progress:
            # Set process start time
            progress.set_process_start_time()
            progress.update_main_status("Validating data sources")
            self._maybe_delete_stale(progress)

            # Add cache usage subtask
            self._add_cache_subtask(progress)

            progress.update_main_status("Initializing data index")
            self._poll_loop(progress)
            self._post_check(progress)

            # Set process end time (summary will be automatically printed by __exit__)
            progress.set_process_end_time()

    def _add_cache_subtask(self, progress) -> None:
        """Add a subtask showing cache usage information only when cache is used."""
        if self.cache.using_cache:
            # Cache was used - show how many sources were cached
            total_sources = len(self.cache.sources)
            cached_sources = total_sources - len(self.sources)

            # Get the timestamp when sources were cached
            entry = self.cache._metadata.get("cachedIndices", {}).get(self.cache.key, {})
            cached_timestamp = entry.get("last_use_index_update_on", "")

            message = f"Using cached data for {cached_sources}/{total_sources} data streams"
            # Format the message with timestamp
            if cached_timestamp:
                message += f" (cached at {cached_timestamp})"

            progress.add_sub_task(message, task_id="cache_usage", category=TASK_CATEGORY_CACHE)
            # Complete the subtask immediately since it's just informational
            progress.complete_sub_task("cache_usage")

    def _get_stream_column_hashes(self, sources: List[str], progress) -> Dict[str, str]:
        """
        Query data_streams to get current column hashes for the given sources.

        Args:
            sources: List of source FQNs to query
            progress: TaskProgress instance for updating status on error

        Returns:
            Dict mapping FQN -> column hash

        Raises:
            ValueError: If the query fails (permissions, table doesn't exist, etc.)
        """
        from v0.relationalai.clients.snowflake import PYREL_ROOT_DB

        # Build FQN list for SQL IN clause
        fqn_list = ", ".join([f"'{source}'" for source in sources])

        # Format query template with actual values
        hash_query = STREAM_COLUMN_HASH_QUERY.format(
            app_name=self.app_name,
            rai_database=PYREL_ROOT_DB,
            fqn_list=fqn_list
        )

        try:
            hash_results = self.res._exec(hash_query)
            return {row["FQ_OBJECT_NAME"]: row["STREAM_HASH"] for row in hash_results}

        except Exception as e:
            logger.error(f"Failed to query stream column hashes: {e}")
            logger.error(f"  Query: {hash_query[:200]}...")
            logger.error(f"  Sources: {sources}")
            progress.update_main_status("❌ Failed to validate data stream metadata")
            raise ValueError(
                f"Failed to validate stream column hashes. This may indicate a permissions "
                f"issue or missing data_streams table. Error: {e}"
            ) from e

    def _filter_truly_stale_sources(self, stale_sources: List[str], progress) -> List[str]:
        """
        Filter stale sources to only include those with mismatched column hashes.

        Args:
            stale_sources: List of source FQNs marked as stale
            progress: TaskProgress instance for updating status on error

        Returns:
            List of truly stale sources that need to be deleted/recreated

        A source is truly stale if any of the following apply:
        - The stream doesn't exist (needs to be created)
        - The source table was recreated after the stream (table creation timestamp is newer)
        - The column hashes don't match (schema drift needs cleanup)
        """
        stream_hashes = self._get_stream_column_hashes(stale_sources, progress)

        truly_stale = []
        for source in stale_sources:
            source_hash = self.source_info[source].get("columns_hash")
            stream_hash = stream_hashes.get(source)
            table_created_at_raw = self.source_info[source].get("table_created_at")
            stream_created_at_raw = self.source_info[source].get("stream_created_at")

            table_created_at = normalize_datetime(table_created_at_raw)
            stream_created_at = normalize_datetime(stream_created_at_raw)

            recreated_table = False
            if table_created_at is not None and stream_created_at is not None:
                # If the source table was recreated (new creation timestamp) but kept
                # the same column definitions, we still need to recycle the stream so
                # that Snowflake picks up the new table instance.
                recreated_table = table_created_at > stream_created_at

            # Log hash comparison for debugging
            logger.debug(f"Source: {source}")
            logger.debug(f"  Source table hash: {source_hash}")
            logger.debug(f"  Stream hash: {stream_hash}")
            logger.debug(f"  Match: {source_hash == stream_hash}")
            if recreated_table:
                logger.debug("  Table appears to have been recreated (table_created_at > stream_created_at)")
                logger.debug(f"    table_created_at: {table_created_at}")
                logger.debug(f"    stream_created_at: {stream_created_at}")

            if stream_hash is None or source_hash != stream_hash or recreated_table:
                logger.debug("  Action: DELETE (stale)")
                truly_stale.append(source)
            else:
                logger.debug("  Action: KEEP (valid)")

        logger.debug(f"Stale sources summary: {len(truly_stale)}/{len(stale_sources)} truly stale")

        return truly_stale

    def _add_deletion_subtasks(self, progress, sources: List[str]) -> None:
        """Add progress subtasks for source deletion.

        Args:
            progress: TaskProgress instance
            sources: List of source FQNs to be deleted
        """
        if len(sources) <= MAX_INDIVIDUAL_SUBTASKS:
            for i, source in enumerate(sources):
                progress.add_sub_task(
                    f"Removing stale stream {source} ({i+1}/{len(sources)})",
                    task_id=f"stale_source_{i}",
                    category=TASK_CATEGORY_VALIDATION
                )
        else:
            progress.add_sub_task(
                f"Removing {len(sources)} stale data sources",
                task_id="stale_sources_summary",
                category=TASK_CATEGORY_VALIDATION
            )

    def _complete_deletion_subtasks(self, progress, sources: List[str], deleted_count: int) -> None:
        """Complete progress subtasks for source deletion.

        Args:
            progress: TaskProgress instance
            sources: List of source FQNs that were processed
            deleted_count: Number of sources successfully deleted
        """
        if len(sources) <= MAX_INDIVIDUAL_SUBTASKS:
            for i in range(len(sources)):
                if f"stale_source_{i}" in progress._tasks:
                    progress.complete_sub_task(f"stale_source_{i}")
        else:
            if "stale_sources_summary" in progress._tasks:
                if deleted_count > 0:
                    s = "s" if deleted_count > 1 else ""
                    progress.update_sub_task(
                        "stale_sources_summary",
                        f"Removed {deleted_count} stale data source{s}"
                    )
                progress.complete_sub_task("stale_sources_summary")

    def _maybe_delete_stale(self, progress) -> None:
        """Check for and delete stale data streams that need recreation.

        Args:
            progress: TaskProgress instance for tracking deletion progress
        """
        with debugging.span("check_sources"):
            stale_sources = [
                source
                for source, info in self.source_info.items()
                if info.get("state") == "STALE"
            ]

        if not stale_sources:
            return

        with DebuggingSpan("validate_sources"):
            try:
                # Validate which sources truly need deletion by comparing column hashes
                truly_stale = self._filter_truly_stale_sources(stale_sources, progress)

                if not truly_stale:
                    return

                # Delete truly stale streams
                from v0.relationalai.clients.snowflake import PYREL_ROOT_DB
                query = f"CALL {self.app_name}.api.delete_data_streams({truly_stale}, '{PYREL_ROOT_DB}');"

                self._add_deletion_subtasks(progress, truly_stale)

                delete_response = self.res._exec(query)
                delete_json_str = delete_response[0]["DELETE_DATA_STREAMS"].lower()
                delete_data = json.loads(delete_json_str)
                deleted_count = delete_data.get("deleted", 0)

                self._complete_deletion_subtasks(progress, truly_stale, deleted_count)

                # Check for errors
                diff = len(truly_stale) - deleted_count
                if diff > 0:
                    errors = delete_data.get("errors", None)
                    if errors:
                        raise Exception(f"Error(s) deleting streams with modified sources: {errors}")

            except Exception as e:
                # Complete any remaining subtasks
                self._complete_deletion_subtasks(progress, stale_sources, 0)
                if "stale_sources_summary" in progress._tasks:
                    progress.update_sub_task(
                        "stale_sources_summary",
                        f"❌ Failed to remove stale sources: {str(e)}"
                    )

                # Don't raise if streams don't exist - this is expected
                if "data streams do not exist" not in str(e).lower():
                    raise e from None

    def _poll_loop(self, progress) -> None:
        """Main polling loop for use_index streams.

        Args:
            progress: TaskProgress instance for tracking polling progress
        """
        source_references = self.res._get_source_references(self.source_info)
        sources_object_references_str = ", ".join(source_references)

        def check_ready(progress) -> bool:
            self.check_ready_count += 1

            # To limit the performance overhead, we only check if ERP is running every N iterations
            if self.check_ready_count % ERP_CHECK_FREQUENCY == 0:
                with debugging.span("check_erp_status"):
                    # Add subtask for ERP status check
                    if self._erp_check_task_id is None:
                        self._erp_check_task_id = progress.add_sub_task("Checking system status", task_id="erp_check", category=TASK_CATEGORY_STATUS)

                    if not self.res.is_erp_running(self.app_name):
                        progress.update_sub_task("erp_check", "❌ System status check failed")
                        progress.complete_sub_task("erp_check")
                        raise ERPNotRunningError
                    else:
                        progress.update_sub_task("erp_check", "System status check complete")
                        progress.complete_sub_task("erp_check")

            use_index_id = f"{self.model}_{self.execution_id}"

            params = json.dumps({
                "model": self.model,
                "engine": self.engine_name,
                "default_engine_size": self.engine_size, # engine_size
                "user_agent": self.pyrel_version,
                "use_index_id": use_index_id,
                "pyrel_program_id": self.program_span_id,
                "wait_for_stream_sync": self.wait_for_stream_sync,
                "should_check_cdc": self.should_check_cdc,
                "init_engine_async": self.init_engine_async,
                "language": self.language,
                "data_freshness_mins": self.data_freshness,
            })

            request_headers = debugging.add_current_propagation_headers(self.headers)

            sql_string = f"CALL {self.app_name}.api.use_index([{sources_object_references_str}], PARSE_JSON(?), {request_headers});"

            with debugging.span("wait", counter=self.counter, use_index_id=use_index_id) as span:
                results = self.res._exec(sql_string, [params])

                # Extract the JSON string from the `USE_INDEX` field
                use_index_json_str = results[0]["USE_INDEX"]

                # Parse the JSON string into a Python dictionary
                try:
                    use_index_data = json.loads(use_index_json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from use_index API: {e}")
                    logger.error(f"Raw response (first 500 chars): {use_index_json_str[:500]}")
                    progress.update_main_status("❌ Received invalid response from server")
                    raise ValueError(f"Invalid JSON response from use_index: {e}") from e

                span.update(use_index_data)

                # Log the full use_index_data for debugging if needed
                logger.debug(f"use_index_data: {json.dumps(use_index_data, indent=4)}")

                all_data = use_index_data.get("data", [])
                ready = use_index_data.get("ready", False)
                engines = use_index_data.get("engines", [])
                errors = use_index_data.get("errors", [])
                relations = use_index_data.get("relations", {})
                cdc_enabled = use_index_data.get("cdcEnabled", False)
                if self.check_ready_count % ERP_CHECK_FREQUENCY == 0 or not cdc_enabled:
                    self.should_check_cdc = True
                else:
                    self.should_check_cdc = False

                if engines and self.init_engine_async:
                    self.init_engine_async = False

                break_loop = False
                has_stream_errors = False
                has_general_errors = False

                # Update main progress message
                if ready:
                    progress.update_main_status("Done")

                # Handle streams data
                if not ready and all_data:
                    progress.update_main_status("Processing background tasks. This may take a while...")

                    # Build complete stream order first (only on first iteration with data)
                    if self.total_streams == 0:
                        for data in all_data:
                            if data is None:
                                continue
                            fq_name = data.get("fq_object_name", "Unknown")
                            if fq_name not in self.stream_order:
                                self.stream_order.append(fq_name)

                        # Set total streams count based on complete order (only once)
                        self.total_streams = len(self.stream_order)

                    # Add new streams as subtasks if we haven't reached the limit
                    for data in all_data:
                        fq_name = data.get("fq_object_name", "Unknown")
                        status = data.get("data_sync_status", "").lower() if data else ""
                        batches_count = data.get("pending_batches_count", 0)

                        # Only add if we haven't seen this stream and we're under the limit
                        self._add_stream_subtask(progress, fq_name, status, batches_count)

                        # Handle errors for existing streams
                        if fq_name in self.stream_task_ids and data.get("errors", []):
                            for error in data.get("errors", []):
                                error_msg = f"{error.get('error')}, source: {error.get('source')}"
                                self.table_objects_with_other_errors.append(
                                    SnowflakeTableObject(error_msg, fq_name)
                                )
                            # Mark stream as failed
                            progress.update_sub_task(fq_name, f"❌ Failed: {fq_name}")
                            has_stream_errors = True

                        # Update stream status (only for streams that aren't already completed)
                        if fq_name in self.stream_task_ids and fq_name in progress._tasks and not progress._tasks[fq_name].completed:
                            # Get the stream position from the stream order
                            if fq_name in self.stream_order:
                                stream_position = self.stream_order.index(fq_name) + 1
                            else:
                                # Fallback to 1 if not in order (shouldn't happen)
                                stream_position = 1

                            # Build status message
                            if batches_count > 0 and status == 'syncing':
                                status_message = f"Syncing {fq_name} ({stream_position}/{self.total_streams}), batches: {batches_count}"
                            else:
                                status_message = f"Pending {fq_name} ({stream_position}/{self.total_streams})..."

                            progress.update_sub_task(fq_name, status_message)

                            # Complete the stream if it's synced
                            if status == "synced":
                                progress.complete_sub_task(fq_name)

                    # Add more streams from the queue if we have space and more streams exist
                    if len(self.stream_task_ids) < MAX_DATA_SOURCE_SUBTASKS:
                        for data in all_data:
                            fq_name = data.get("fq_object_name", "Unknown")
                            status = data.get("data_sync_status", "").lower()
                            batches_count = data.get("pending_batches_count", 0)

                            self._add_stream_subtask(progress, fq_name, status, batches_count)

                    self.counter += 1

                # Handle engines data
                if not ready and engines:
                    # Add new engines as subtasks if they don't exist
                    for engine in engines:
                        if not engine or not isinstance(engine, dict):
                            continue
                        size = self.engine_size
                        name = engine.get("name", "Unknown")
                        status = (engine.get("status") or "").lower()
                        sub_task_id = self.engine_task_ids.get(name, None)
                        sub_task_status_message = ""

                        # Complete the sub task if it exists and the engine status is ready
                        if sub_task_id and name in progress._tasks and not progress._tasks[name].completed and (status == "ready"):
                            sub_task_status_message = f"Engine {name} ({size}) ready"
                            progress.update_sub_task(name, sub_task_status_message)
                            progress.complete_sub_task(name)

                        # Add the sub task if it doesn't exist and the engine status is pending
                        if not sub_task_id and status == "pending":
                            writer = engine.get("writer", False)
                            engine_type = "writer engine" if writer else "engine"
                            sub_task_status_message = f"Provisioning {engine_type} {name} ({size})"
                            self.engine_task_ids[name] = progress.add_sub_task(sub_task_status_message, task_id=name, category=TASK_CATEGORY_PROVISIONING)

                    # Special handling for CDC_MANAGED_ENGINE - mark ready when any stream starts processing
                    cdc_task = progress._tasks.get(CDC_MANAGED_ENGINE) if CDC_MANAGED_ENGINE in progress._tasks else None
                    if CDC_MANAGED_ENGINE in self.engine_task_ids and cdc_task and not cdc_task.completed:

                        has_processing_streams = any(
                            stream.get("next_batch_status", "") == "processing"
                            for stream in all_data
                        )
                        if has_processing_streams and cdc_task and not cdc_task.completed:
                            progress.update_sub_task(CDC_MANAGED_ENGINE, f"Engine {CDC_MANAGED_ENGINE} ({self.engine_size}) ready")
                            progress.complete_sub_task(CDC_MANAGED_ENGINE)

                    self.counter += 1

                # Handle relations data
                if relations and isinstance(relations, dict):
                    txn = relations.get("txn", {}) or {}
                    txn_id = txn.get("id", None)

                    # Only show relations subtask if there is a valid txn object
                    if txn_id:
                        status = relations.get("status", "").upper()

                        # Create relations subtask if it doesn't exist
                        if self.relations_task_id is None:
                            self.relations_task_id = progress.add_sub_task("Populating relations", task_id="relations", category=TASK_CATEGORY_RELATIONS)

                        # Set the start time from the JSON if available (always update)
                        start_time_ms = relations.get("start_time")
                        if start_time_ms:
                            start_time_seconds = start_time_ms / 1000.0
                            progress._tasks["relations"].added_time = start_time_seconds

                        # Update relations status
                        if status == "COMPLETED":
                            progress.update_sub_task("relations", f"Relations populated (txn: {txn_id})")

                            # Set the completion time from the JSON if available
                            end_time_ms = relations.get("end_time")
                            if end_time_ms:
                                end_time_seconds = end_time_ms / 1000.0
                                progress._tasks["relations"].completed_time = end_time_seconds

                            progress.complete_sub_task("relations", record_time=False)  # Don't record local time
                        else:
                            progress.update_sub_task("relations", f"Relations populating (txn: {txn_id})")

                        self.counter += 1

                # Handle errors
                if not ready and errors:
                    for error in errors:
                        if error is None:
                            continue
                        if error.get("type") == "data":
                            message = error.get("message", "").lower()
                            if ("change_tracking" in message or "change tracking" in message):
                                err_source = error.get("source")
                                err_source_type = self.source_info.get(err_source, {}).get("type")
                                self.tables_with_not_enabled_change_tracking.append((err_source, err_source_type))
                            else:
                                self.table_objects_with_other_errors.append(
                                    SnowflakeTableObject(error.get("message"), error.get("source"))
                                )
                        elif error.get("type") == "engine":
                            self.engine_errors.append(error)
                        else:
                            # Other types of errors, e.g. "validation"
                            self.table_objects_with_other_errors.append(
                                SnowflakeTableObject(error.get("message"), error.get("source"))
                            )
                    has_general_errors = True

                # If ready, complete all remaining subtasks
                if ready:
                    self.cache.record_update(self.source_info)
                    # Complete any remaining stream subtasks
                    for fq_name in self.stream_task_ids:
                        if fq_name in progress._tasks and not progress._tasks[fq_name].completed:
                            progress.complete_sub_task(fq_name)
                    # Complete any remaining engine subtasks
                    for name in self.engine_task_ids:
                        if name in progress._tasks and not progress._tasks[name].completed:
                            progress.complete_sub_task(name)
                    # Complete relations subtask if it exists and isn't completed
                    if self.relations_task_id and "relations" in progress._tasks and not progress._tasks["relations"].completed:
                        progress.complete_sub_task("relations")
                    break_loop = True
                elif has_stream_errors or has_general_errors:
                    # Break the loop if there are errors, but only after reporting all progress
                    break_loop = True

                return break_loop

        poll_with_specified_overhead(lambda: check_ready(progress), overhead_rate=POLL_OVERHEAD_RATE, max_delay=POLL_MAX_DELAY)

    def _post_check(self, progress) -> None:
        """Run post-processing checks including change tracking enablement.

        Args:
            progress: TaskProgress instance for tracking progress

        Raises:
            SnowflakeChangeTrackingNotEnabledException: If change tracking cannot be enabled
            SnowflakeTableObjectsException: If there are table-related errors
            EngineProvisioningFailed: If engine provisioning fails
        """
        num_tables_altered = 0
        failed_tables = []  # Track tables that failed to enable change tracking

        enabled_tables = []
        if (
            self.tables_with_not_enabled_change_tracking
            and self.res.config.get("ensure_change_tracking", False)
        ):
            tables_to_process = self.tables_with_not_enabled_change_tracking
            # Track timing for change tracking

            # Add subtasks based on count
            if len(tables_to_process) <= MAX_INDIVIDUAL_SUBTASKS:
                # Add individual subtasks for each table
                for i, table in enumerate(tables_to_process):
                    fqn, kind = table
                    progress.add_sub_task(f"Enabling change tracking on {fqn} ({i+1}/{len(tables_to_process)})", task_id=f"change_tracking_{i}", category=TASK_CATEGORY_CHANGE_TRACKING)
            else:
                # Add single summary subtask for many tables
                progress.add_sub_task(f"Enabling change tracking on {len(tables_to_process)} tables", task_id="change_tracking_summary", category=TASK_CATEGORY_CHANGE_TRACKING)

            # Process tables
            for i, table in enumerate(tables_to_process):
                fqn, kind = table  # Unpack outside try block to ensure fqn is defined

                try:
                    # Validate table_type to prevent SQL injection
                    # Should only be TABLE or VIEW
                    if kind not in ("TABLE", "VIEW"):
                        logger.error(f"Invalid table kind '{kind}' for {fqn}, skipping")
                        failed_tables.append((fqn, f"Invalid table kind: {kind}"))
                        # Mark as failed in progress
                        if len(tables_to_process) <= MAX_INDIVIDUAL_SUBTASKS:
                            if f"change_tracking_{i}" in progress._tasks:
                                progress.update_sub_task(f"change_tracking_{i}", f"❌ Invalid type: {fqn}")
                                progress.complete_sub_task(f"change_tracking_{i}")
                        continue

                    # Execute ALTER statement
                    # Note: fqn should already be properly quoted from source_info
                    self.res._exec(f"ALTER {kind} {fqn} SET CHANGE_TRACKING = TRUE;")
                    enabled_tables.append(table)
                    num_tables_altered += 1

                    # Update progress based on subtask type
                    if len(tables_to_process) <= MAX_INDIVIDUAL_SUBTASKS:
                        # Complete individual table subtask
                        progress.complete_sub_task(f"change_tracking_{i}")
                    else:
                        # Update summary subtask with progress
                        progress.update_sub_task("change_tracking_summary",
                            f"Enabling change tracking on {len(tables_to_process)} tables... ({i+1}/{len(tables_to_process)})")
                except Exception as e:
                    # Log the error for debugging
                    logger.warning(f"Failed to enable change tracking on {fqn}: {e}")
                    failed_tables.append((fqn, str(e)))

                    # Handle errors based on subtask type
                    if len(tables_to_process) <= MAX_INDIVIDUAL_SUBTASKS:
                        # Mark the individual subtask as failed and complete it
                        if f"change_tracking_{i}" in progress._tasks:
                            progress.update_sub_task(f"change_tracking_{i}", f"❌ Failed: {fqn}")
                            progress.complete_sub_task(f"change_tracking_{i}")
                    # Continue processing other tables despite this failure

            # Complete summary subtask if used
            if len(tables_to_process) > MAX_INDIVIDUAL_SUBTASKS and "change_tracking_summary" in progress._tasks:
                if num_tables_altered > 0:
                    s = "s" if num_tables_altered > 1 else ""
                    success_msg = f"Enabled change tracking on {num_tables_altered} table{s}"
                    if failed_tables:
                        success_msg += f" ({len(failed_tables)} failed)"
                    progress.update_sub_task("change_tracking_summary", success_msg)
                elif failed_tables:
                    progress.update_sub_task("change_tracking_summary", f"❌ Failed on {len(failed_tables)} table(s)")
                progress.complete_sub_task("change_tracking_summary")

            # Log summary of failed tables
            if failed_tables:
                logger.warning(f"Failed to enable change tracking on {len(failed_tables)} table(s)")
                for fqn, error in failed_tables:
                    logger.warning(f"  {fqn}: {error}")

            # Remove the tables that were successfully enabled from the list of not enabled tables
            # so that we don't raise an exception for them later
            self.tables_with_not_enabled_change_tracking = [
                t for t in self.tables_with_not_enabled_change_tracking if t not in enabled_tables
            ]

        if self.tables_with_not_enabled_change_tracking:
            progress.update_main_status("Errors found. See below for details.")
            raise SnowflakeChangeTrackingNotEnabledException(
                self.tables_with_not_enabled_change_tracking
            )

        if self.table_objects_with_other_errors:
            progress.update_main_status("Errors found. See below for details.")
            raise SnowflakeTableObjectsException(self.table_objects_with_other_errors)
        if self.engine_errors:
            progress.update_main_status("Errors found. See below for details.")
            # if there is an engine error, probably auto create engine failed
            # Create a synthetic exception from the first engine error
            first_error = self.engine_errors[0]
            error_message = first_error.get("message", "Unknown engine error")
            synthetic_exception = Exception(f"Engine error: {error_message}")
            raise EngineProvisioningFailed(self.engine_name, synthetic_exception)

        if num_tables_altered > 0:
            self._poll_loop(progress)

class DirectUseIndexPoller(UseIndexPoller):
    """
    Extends UseIndexPoller to handle direct-access prepare_index when no sources.
    """
    def __init__(
        self,
        resource: "DirectAccessResources",
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: Optional[str],
        language: str = "rel",
        program_span_id: Optional[str] = None,
        headers: Optional[Dict] = None,
        generation: Optional[Generation] = None,
    ):
        super().__init__(
            resource=resource,
            app_name=app_name,
            sources=sources,
            model=model,
            engine_name=engine_name,
            engine_size=engine_size,
            language=language,
            program_span_id=program_span_id,
            headers=headers,
            generation=generation,
        )
        from v0.relationalai.clients.snowflake import DirectAccessResources
        self.res: DirectAccessResources = cast(DirectAccessResources, self.res)

    def poll(self) -> None:
        if not self.sources:
            from v0.relationalai.errors import RAIException
            collected_errors: List[Dict] = []
            attempt = 1

            def check_direct(progress) -> bool:
                nonlocal attempt
                with debugging.span("wait", counter=self.counter) as span:
                    span.update({"attempt": attempt, "engine_name": self.engine_name, "model": self.model})
                    # we are skipping pulling relations here, as direct access only handle non-sources cases
                    # and we don't need to pull relations for that, therefore, we pass empty list for rai_relations
                    # and set skip_pull_relations to True
                    resp = self.res._prepare_index(
                        model=self.model,
                        engine_name=self.engine_name,
                        engine_size=self.engine_size,
                        language=self.language,
                        rai_relations=[],
                        pyrel_program_id=self.program_span_id,
                        skip_pull_relations=True,
                        headers=self.headers,
                    )
                    span.update(resp)
                    caller_engine = resp.get("caller_engine", {})
                    # Handle case where caller_engine might be None
                    ce_status = caller_engine.get("status", "").lower() if caller_engine else ""
                    errors = resp.get("errors", [])

                    ready = resp.get("ready", False)

                    # Update main progress message
                    if ready:
                        progress.update_main_status("Done")
                    else:
                        progress.update_main_status("Preparing your data...")

                    if ready:
                        return True
                    else:
                        if ce_status == "pending":
                            # Add or update engine subtask
                            engine_name = caller_engine.get('name', self.engine_name)
                            if not hasattr(progress, '_engine_task_id'):
                                progress._engine_task_id = progress.add_sub_task(f"Waiting for engine '{engine_name}' to be ready...", task_id=engine_name)
                            else:
                                progress.update_sub_task(engine_name, f"Waiting for engine '{engine_name}' to be ready...")
                        else:
                            # Handle errors as subtasks
                            if errors:
                                progress.update_main_status("Encountered errors during preparation...")
                                for i, err in enumerate(errors):
                                    error_id = f"error_{i}"
                                    if not hasattr(progress, f'_error_task_id_{i}'):
                                        error_msg = err.get('message', 'Unknown error')
                                        setattr(progress, f'_error_task_id_{i}', progress.add_sub_task(f"❌ {error_msg}", task_id=error_id))
                                    else:
                                        error_msg = err.get('message', 'Unknown error')
                                        progress.update_sub_task(error_id, f"❌ {error_msg}")
                                    collected_errors.append(err)

                    attempt += 1
                    return False

            # Read show_duration_summary config flag (defaults to True for backward compatibility)
            show_duration_summary = bool(self.res.config.get("show_duration_summary", True))

            with create_progress(
                description="Preparing your data...",
                success_message="Done",
                leading_newline=True,
                trailing_newline=True,
                show_duration_summary=show_duration_summary,
            ) as progress:
                # Add cache usage subtask
                self._add_cache_subtask(progress)

                with debugging.span("poll_direct"):
                    poll_with_specified_overhead(lambda: check_direct(progress), overhead_rate=POLL_OVERHEAD_RATE, max_delay=POLL_MAX_DELAY)

                # Run the same post-check logic as UseIndexPoller
                self._post_check(progress)

            if collected_errors:
                msg = "; ".join(e.get("message", "") for e in collected_errors)
                raise RAIException(msg)
        else:
            super().poll()
