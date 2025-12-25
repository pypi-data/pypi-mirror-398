from __future__ import annotations
from typing import Dict, List, Optional
from ..constants import DATA_STAGES
from ..utils import utc_now_iso

class StoreService:
    def __init__(self, backend: str, path: str, default_owner: str, default_mode: str = "live"):
        self.default_owner = (default_owner or "kimdg").lower()
        self._state: Dict = {"tabs": {}}

    def state(self) -> Dict:
        return self._state

    def list_filters_for_tab(self, tab: str):
        t = (tab or "data").lower()
        tree = self._state.get("tabs", {}).get(t, {})
        jobs = tree.get("jobs", {})
        owners = sorted(jobs.keys())
        owner_opts = [{"label": "All", "value": "All"}] + [{"label": o.upper(), "value": o} for o in owners]
        return owner_opts

    def apply_snapshot_with_meta_tab(self, tab: str, items: List[dict], meta: Optional[dict] = None):
        t = (tab or "data").lower()
        tabs = self._state.setdefault("tabs", {})
        tree = tabs.setdefault(t, {"jobs": {}, "meta": {}, "updated_at": None})

        jobs = tree["jobs"]
        for it in items or []:
            owner = (it.get("owner") or self.default_owner).lower()
            mode = (it.get("mode") or "live").lower()
            dn = it.get("data_name") or "unknown"
            stage = it.get("stage") or ("status" if t != "data" else "archive")
            chunks = list(it.get("chunks") or [])
            counts = {}
            for ch in chunks:
                s = (ch.get("status") or "other")
                counts[s] = counts.get(s, 0) + 1

            jobs.setdefault(owner, {}).setdefault(mode, {}).setdefault(dn, {})
            leaf = jobs[owner][mode][dn].setdefault(stage, {})
            leaf["chunks"] = chunks
            leaf["counts"] = counts
            leaf["errors"] = list(it.get("errors") or [])

        tree["meta"] = dict(meta or {})
        if "last_ingest_at" not in tree["meta"]:
            tree["meta"]["last_ingest_at"] = utc_now_iso()
        tree["updated_at"] = utc_now_iso()
