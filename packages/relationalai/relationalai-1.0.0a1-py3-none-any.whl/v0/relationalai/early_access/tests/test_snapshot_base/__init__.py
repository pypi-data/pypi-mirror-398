import warnings

from v0.relationalai.semantics.tests.test_snapshot_base import SnapshotTestBase

__all__ = ["SnapshotTestBase"]

warnings.warn(
    "relationalai.early_access.tests.test_snapshot_base is deprecated. "
    "Please migrate to relationalai.semantics.tests.test_snapshot_base",
    DeprecationWarning,
    stacklevel=2,
)