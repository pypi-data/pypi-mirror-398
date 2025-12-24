import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, Union


# ─── Module-level in-memory cache and version ──────────────────────────────
_IN_MEMORY_CACHE: dict[str, dict] = {}
METADATA_VERSION = "0.1.0"  # bump when schema changes

class GraphIndexCache:
    def __init__(
        self,
        user: str,
        model: str,
        freshness_mins: Union[int, None],
        sources: Iterable[str],
        metadata_path: str = "metadata.json",
    ):
        self.metadata_path = Path(metadata_path)
        self.key = f"{user}:{model}"
        self.freshness_mins = freshness_mins
        self.sources = list(sources)
        self.using_cache = False

        # Load metadata into memory: prefer in-memory cache, then file
        raw = _IN_MEMORY_CACHE.get(self.key)
        if raw is not None:
            # Use the notebook/session in-memory entry
            self._metadata = {
                "version": METADATA_VERSION,
                "cachedIndices": {self.key: raw},
            }
        else:
            # Fall back to reading from disk
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    md = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                md = {}
            # Discard if version mismatched
            if md.get("version") != METADATA_VERSION:
                md = {"version": METADATA_VERSION, "cachedIndices": {}}
            self._metadata = md

    def is_valid(self) -> bool:
        """
        Return True if we have a valid, unexpired cache for this user:model
        covering at least the given sources.
        """
        entry = self._metadata.get("cachedIndices", {}).get(self.key)
        if not entry or self.freshness_mins is None or self.freshness_mins <= 0:
            return False

        # timestamp check
        ts = entry.get("last_use_index_update_on", "")
        try:
            last_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return False

        if (
            datetime.now(timezone.utc) - last_ts
        ).total_seconds() > self.freshness_mins * 60:
            return False

        # sources subset check
        if not set(self.sources).issubset(set(entry.get("Sources", []))):
            return False

        self.using_cache = True
        return True

    def choose_sources(self) -> list[str]:
        """
        Return [] if cache is valid, else the full list of sources.
        """
        return [] if self.is_valid() else list(self.sources)

    def record_update(self, sources_info: dict) -> None:
        """
        Write a fresh metadata entry when the index is rebuilt.
        Always update the in-memory cache, then also write to file.
        """
        if self.using_cache:
            return

        # Prepare the new entry
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {"last_use_index_update_on": now, "Sources": list(sources_info.keys())}

        # 1) update module-level in-memory cache
        _IN_MEMORY_CACHE[self.key] = entry
        # 2) merge into our in-memory metadata
        self._metadata.setdefault("cachedIndices", {})[self.key] = entry
        # 3) bump version
        self._metadata["version"] = METADATA_VERSION

        # 4) Persist to disk so the cache survives across processes
        parent = self.metadata_path.parent
        if parent and not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                return  # cannot create directory → skip file write

        # 5) write out
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2)
        except OSError:
            pass
