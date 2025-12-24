from v0.relationalai.semantics.tests.test_snapshot_abstract import AbstractSnapshotTest

class SnapshotTestBase(AbstractSnapshotTest):
    """Base class for tests with snapshots."""

    def assert_match_results_snapshots(self, script_path, snapshot, handler):
        for i, msg in enumerate(handler.results, start=1):
            if "results" in msg:
                snapshot.assert_match(msg["results"].to_csv(index=False).strip('"').strip('\n"'), f"result_{i}.csv")