from __future__ import annotations

from typing import Dict, List, Optional

import copy
import threading

from ..constants import DATA_STAGES, status_order_for_tab
from ..utils import utc_now_iso


class StoreService:
    """
    Thread-safe in-memory store.

    self._state structure:

        {
          "tabs": {
            "<tab>": {
              "jobs": {
                "<owner>": {
                  "<mode>": {
                    "<dataset>": {
                      "<stage_or_status>": {
                        "chunks": [...],
                        "counts": {status -> int},
                        "errors": [...],
                      }
                    }
                  }
                }
              },
              "meta": {...},
              "updated_at": "...",
            }
          }
        }
    """

    def __init__(
        self,
        backend: str,
        path: str,
        default_owner: str,
        default_mode: str = "live",
    ) -> None:
        # backend/path kept for API compatibility (we're using memory only here)
        self.backend = backend
        self.path = path

        self.default_owner = (default_owner or "kimdg").lower()
        self.default_mode = (default_mode or "live").lower()

        self._state: Dict = {"tabs": {}}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def state(self) -> Dict:
        """
        Return a deep copy of the entire state.

        This makes it safe for many concurrent Dash callbacks to iterate
        over the tree while an ingest is mutating it under the lock.
        """
        with self._lock:
            return copy.deepcopy(self._state)

    def list_filters_for_tab(self, tab: str):
        """
        Owner filter options for this tab.

        NOTE: "All" uses value 'all' (lowercase) to match the controls /
        callbacks in the rest of the app.
        """
        with self._lock:
            t = (tab or "data").lower()
            tree = self._state.get("tabs", {}).get(t, {}) or {}
            jobs = tree.get("jobs", {}) or {}

            owners = sorted(jobs.keys())
            owner_opts = [{"label": "All", "value": "all"}]
            owner_opts += [{"label": o.upper(), "value": o} for o in owners]
            return owner_opts

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def apply_snapshot_with_meta_tab(
        self,
        tab: str,
        items: List[dict],
        meta: Optional[dict] = None,
    ) -> None:
        """
        Replace the snapshot for a given tab with `items`.

        This is called by the ingest route. It wipes all existing jobs for
        the tab first, so datasets that disappear from the incoming snapshot
        are properly removed.
        """
        t = (tab or "data").lower()

        with self._lock:
            tabs = self._state.setdefault("tabs", {})
            tree = tabs.setdefault(t, {"jobs": {}, "meta": {}, "updated_at": None})

            # AUTHORITATIVE snapshot: drop all previous jobs for this tab.
            tree["jobs"] = {}
            jobs = tree["jobs"]

            status_vocab = status_order_for_tab(t)

            for it in items or []:
                owner = (it.get("owner") or self.default_owner).strip().lower()
                mode = (it.get("mode") or self.default_mode).strip().lower()

                # Use 'dataset' (ingest canonicalizer uses this), fall back
                # to 'data_name' for older payloads.
                dn = (
                    it.get("dataset")
                    or it.get("data_name")
                    or "unknown"
                )
                dn = (dn or "unknown").strip() or "unknown"

                # Stage: data tab uses pipeline stage, others use single "status" bucket.
                if t == "data":
                    stage = (it.get("stage") or "stage").strip().lower()
                    if stage not in DATA_STAGES:
                        stage = "stage"
                else:
                    stage = "status"

                chunks = list(it.get("chunks") or [])

                # Normalize chunk statuses + build counts over vocab.
                counts = {s: 0 for s in status_vocab}
                for ch in chunks:
                    s = (ch.get("status") or "other").strip().lower()
                    if s not in status_vocab:
                        s = "other"
                    ch["status"] = s
                    counts[s] += 1

                leaf = (
                    jobs
                    .setdefault(owner, {})
                    .setdefault(mode, {})
                    .setdefault(dn, {})
                    .setdefault(stage, {})
                )
                leaf["chunks"] = chunks
                leaf["counts"] = counts
                leaf["errors"] = list(it.get("errors") or [])

            # Meta + timestamps
            tree["meta"] = dict(meta or {})
            if "last_ingest_at" not in tree["meta"]:
                tree["meta"]["last_ingest_at"] = utc_now_iso()
            tree["updated_at"] = utc_now_iso()

    # Optional: you can keep or drop these depending on whether anything calls them.

    def reset_tab(self, tab: str) -> None:
        """
        Clear a tab completely.
        """
        from datetime import datetime, timezone

        with self._lock:
            t = (tab or "data").lower()
            tabs = self._state.setdefault("tabs", {})
            tabs[t] = {
                "jobs": {},
                "meta": {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

    def apply_snapshot_full(self, tab: str, items: list, meta: dict) -> None:
        """
        Hard-replace the tab with exactly these items; no merge.
        """
        self.reset_tab(tab)
        self.apply_snapshot_with_meta_tab(tab, items, meta)