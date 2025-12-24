import logging
import os
import uuid
import sys
import datetime
from abc import abstractmethod, ABC

from v0.relationalai.semantics.tests.logging import Capturer
from v0.relationalai.semantics.tests.utils import reset_state
from v0.relationalai.semantics.internal import internal
from v0.relationalai.clients.result_helpers import sort_data_frame_result
from v0.relationalai.clients.util import IdentityParser
from v0.relationalai.clients.snowflake import Provider as SFProvider
from v0.relationalai import Provider
from typing import cast, Dict, Union
from pathlib import Path

class AbstractSnapshotTest(ABC):

    provider:Provider = cast(SFProvider, Provider()) # type: ignore

    def run_snapshot_test(self, snapshot, script_path, db_schema=None, use_sql=False, use_lqp=True, use_rel=False,
                          use_direct_access=False, e2e=False, use_csv=True, e2e_only=False):
        # Resolve use_lqp
        use_lqp = use_lqp and (not use_rel) # use_rel overrides because use_lqp is default.

        """Run a snapshot test.

        This method assumes content is already in the correct string format.
        Subclasses should handle any necessary compilation or conversion.
        """
        logger = logging.getLogger("pyrellogger")
        handler = Capturer()
        logger.addHandler(handler)

        # reset state across test runs
        reset_state()

        # Track which modules are already loaded
        before_modules = set(sys.modules.keys())
        unique_name = f"md{str(uuid.uuid4())[-12:]}"
        export_fqn = None
        dry_run = not e2e
        try:
            overrides = {
                'dry_run': dry_run,
                'model_suffix': "" if not e2e else f"_{unique_name}",
                'use_sql': use_sql,
                'reasoner.rule.use_lqp': use_lqp,
                'keep_model': False,
                # fix the current time to keep snapshots stable
                'datetime_now': datetime.datetime.fromisoformat("2025-12-01T12:00:00+00:00"),
            }
            if use_direct_access:
                # for direct access we can not use user/password authentication
                # so we override the config to use key pair authentication
                override_config: Dict[str, Union[str, bool]] = {
                    'use_direct_access': True,
                }
                if os.getenv("AUTHENTICATOR"):
                    override_config["authenticator"] = os.getenv("AUTHENTICATOR", "")
                if os.getenv("PRIVATE_KEY_FILE"):
                    override_config["private_key_file"] = os.getenv("PRIVATE_KEY_FILE", "")
                if os.getenv("SF_TEST_ACCOUNT_KEY_PASSPHRASE"):
                    override_config["private_key_file_pwd"] = os.getenv("SF_TEST_ACCOUNT_KEY_PASSPHRASE", "")
                overrides['config'] = override_config

            with internal.with_overrides(**overrides):
                with open(script_path, "r") as f:
                    # Compile with the correct filename
                    code = compile(f.read(), script_path, "exec")
                    # Execute the compiled code
                    if db_schema:
                        export_fqn = f"{db_schema}.{unique_name}"
                    exec_globals = {"EXPORT_TABLE": export_fqn}
                    exec(code, exec_globals)
        finally:
            # Remove any modules that were imported during exec()
            after_modules = set(sys.modules.keys())
            new_modules = after_modules - before_modules
            for mod in new_modules:
                sys.modules.pop(mod, None)
            # Remove handler
            logger.removeHandler(handler)
            # check if script created an export table
            export_exists = not dry_run and self.is_export_exists(export_fqn)
            # match snapshots
            self.assert_match_snapshots(script_path, snapshot, handler, export_exists, export_fqn, use_sql=use_sql,
                                        use_lqp=use_lqp, e2e=e2e, use_csv=use_csv, e2e_only=e2e_only)
            # cleanup resources created during a test run
            self.cleanup(export_exists, export_fqn)

    def assert_match_snapshots(self, script_path, snapshot, handler, export_exists=False, export_fqn=None, use_sql=False,
                               use_lqp=True, e2e=False, use_csv=True, e2e_only=False):
        if not e2e_only:
            self.assert_match_internal_results_snapshots(snapshot, handler, use_sql, use_lqp)
        if e2e:
            self.assert_match_results_snapshots(script_path, snapshot, handler)
        if export_fqn and export_exists:
            result_df = sort_data_frame_result(self.provider.sql(f"SELECT * FROM {export_fqn}", format="pandas"))
            if use_csv:
                snapshot.assert_match(result_df.to_csv(index=False).strip('"').strip('\n"'), "export_result.csv")
            else:
                snapshot.assert_match(result_df.to_string(), "export_result.df")

    def assert_match_internal_results_snapshots(self, snapshot, handler, use_sql, use_lqp):
        # default: do nothing
        return

    @abstractmethod
    def assert_match_results_snapshots(self, script_path, snapshot, handler):
        pass

    def cleanup(self, export_exists=False, export_fqn=None):
        if export_fqn and export_exists :
            self.provider.sql(f"DROP TABLE IF EXISTS {export_fqn}")

    def is_export_exists(self, export_fqn=None):
        if export_fqn is None:
            return False
        database, schema, table, _ = IdentityParser(export_fqn, require_all_parts=True).to_list()
        return self.provider.sql(f"""
            SELECT EXISTS(
                SELECT 1
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema}'
                AND TABLE_NAME = '{table}'
            ) AS TABLE_EXISTS;
        """)[0]["TABLE_EXISTS"]

    @staticmethod
    def parent_tests(file: str):
        return AbstractSnapshotTest.discover_test_scripts(Path(file).parent)

    @staticmethod
    def discover_test_scripts(path: Path):
        scripts_dir = path / "tests"
        return sorted(scripts_dir.glob("**/*.py"))

    @staticmethod
    def get_id(p):
        p_name = p.parent.name
        return p.stem if p_name == "tests" else f"{p_name}_{p.stem}"
