# dataset_dashboard/services/injector.py
from __future__ import annotations
import threading, time, random
from typing import Optional, List, Dict

from ..config import AppConfig
from ..constants import TAB_IDS
from ..library import make_multi_owner_payload


class InjectorService:
    """
    Periodically generates synthetic ingestion payloads and applies them to the in-memory store.

    Args:
        cfg: AppConfig (should define ingest_period_sec; defaults to 5).
        store: StoreService with `apply_snapshot_with_meta_tab(tab, items, meta)` and `state()`.
        period_sec: Optional override for the tick period in seconds.
        owners: Optional list of owners to simulate; if None, library falls back to defaults.
        batch_size: Datasets per owner per tab per tick.
    """
    def __init__(
        self,
        cfg: AppConfig,
        store,
        period_sec: Optional[int] = None,
        owners: Optional[List[str]] = None,
        batch_size: int = 3,
    ) -> None:
        self.cfg = cfg
        self.store = store
        self.owners = owners
        self.batch_size = max(1, int(batch_size))
        self._default_period = 5
        self._period_sec = int(period_sec or getattr(cfg, "ingest_period_sec", self._default_period) or self._default_period)
        self._stop = threading.Event()
        self._thr: Optional[threading.Thread] = None

    @property
    def period_sec(self) -> int:
        # pick up live changes to cfg.ingest_period_sec if you tweak it on the fly
        return int(getattr(self.cfg, "ingest_period_sec", self._period_sec) or self._default_period)

    def start(self) -> None:
        if self._thr and self._thr.is_alive():
            return
        self._stop.clear()
        self._thr = threading.Thread(target=self._run, name="InjectorService", daemon=True)
        self._thr.start()

    def stop(self, timeout: Optional[float] = 2.0) -> None:
        self._stop.set()
        if self._thr:
            self._thr.join(timeout=timeout)

    def _run(self) -> None:
        # light jitter so multiple instances don't stampede
        time.sleep(random.uniform(0.0, 0.5))
        while not self._stop.is_set():
            tick_start = time.time()
            try:
                self._inject_once()
            except Exception as e:
                # don't kill the thread on transient errors
                print(f"[InjectorService] inject_once error: {e}")
            # sleep the remainder of the period (and wake early if stopping)
            elapsed = time.time() - tick_start
            period = max(1.0, float(self.period_sec))
            to_sleep = max(0.0, period - elapsed)
            if self._stop.wait(timeout=to_sleep):
                break

    def _inject_once(self) -> None:
        pack = make_multi_owner_payload(
            self.cfg,
            owners=self.owners,
            tabs=TAB_IDS,
            num_items=self.batch_size,
            save_dir=None,  # no file writes from the background loop
        )
        tabs = pack.get("tabs", {})
        for t in TAB_IDS:
            part: Dict = tabs.get(t) or {}
            items = list(part.get("snapshot") or [])
            meta = dict(part.get("meta") or {})
            if items:
                self.store.apply_snapshot_with_meta_tab(t, items, meta)