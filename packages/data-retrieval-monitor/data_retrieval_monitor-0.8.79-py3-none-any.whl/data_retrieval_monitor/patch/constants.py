# qsg/app/dashboard/constants.py

from __future__ import annotations

from typing import Dict, List, Tuple

from qsg.core.config import ConfigLoader
from qsg.core.constants import Owner
from qsg.dataset.constants import PipelineMode, PipelineStage

from qsg.app.dashboard.utils import _hex_to_rgb

# ---------------------------------------------------------------------
# Pipeline configuration – stages, tabs, and modes
# ---------------------------------------------------------------------

_data_stages = [
    PipelineStage.Archive,
    PipelineStage.Stage,
    PipelineStage.Enrich,
    PipelineStage.Consolidate,
]

DATA_STAGES: List[str] = [s.name.lower() for s in _data_stages]

TAB_IDS: Tuple[str, ...] = ("data", "features", "alphas", "strategies")

ALPHA_STAGES: List[str] = ["status"]
STRAT_STAGES: List[str] = ["status"]

# All owners registered in config registry.
OWNERS: List[Owner] = ConfigLoader().list()

# Available pipeline modes.
MODES: List[PipelineMode] = [PipelineMode.Backfill, PipelineMode.Live]

# ---------------------------------------------------------------------
# Status order / scoring
# ---------------------------------------------------------------------

DATA_STATUS_ORDER: List[str] = [
    "overdue",
    "failed",
    "retrying",
    "waiting",
    "allocated",
    "running",
    "queued",
    "succeeded",
    "manual",
    "other",
]

FEATURES_STATUS_ORDER = DATA_STATUS_ORDER
ALPHAS_STATUS_ORDER = DATA_STATUS_ORDER
STRATS_STATUS_ORDER = DATA_STATUS_ORDER


def status_order_for_tab(tab: str) -> List[str]:
    t = (tab or "data").lower()
    if t == "features":
        return FEATURES_STATUS_ORDER
    if t == "alphas":
        return ALPHAS_STATUS_ORDER
    if t == "strategies":
        return STRATS_STATUS_ORDER
    return DATA_STATUS_ORDER


JOB_COLORS: Dict[str, str] = {
    "overdue": "#D91113",
    "failed": "#B50000",
    "retrying": "#FF8C00",
    "waiting": "#F6C530",
    "allocated": "#0079C1",
    "running": "#0085D7",
    "queued": "#9B59B6",
    "succeeded": "#00A650",
    "manual": "#888888",
    "other": "#BBBBBB",
}

JOB_RGB: Dict[str, Tuple[int, int, int]] = {
    k: _hex_to_rgb(v) for k, v in JOB_COLORS.items()
}


def rgb_for_tab(tab: str) -> Dict[str, Tuple[int, int, int]]:
    """
    Return a {status -> (r,g,b)} mapping for this tab.

    Uses the tab's status order so pies, tables and legends always agree.
    """
    order = status_order_for_tab(tab)
    return {
        s: JOB_RGB.get(s, JOB_RGB.get("other", (153, 153, 153))) for s in order
    }


# Scoring: how "good" a status is (used for sort-by chunk avg score)
_stat_scores: Dict[str, float] = {
    "overdue": -1.0,
    "failed": -0.8,
    "retrying": -0.3,
    "waiting": -0.1,
    "allocated": 0.2,
    "running": 0.3,
    "queued": 0.2,
    "succeeded": 1.0,
    "manual": 0.2,
    "other": 0.0,
}


def status_scores_for_tab(tab: str) -> Dict[str, float]:
    # In case different tabs should be scored differently later.
    return dict(_stat_scores)


# ---------------------------------------------------------------------
# UI dropdown options
# ---------------------------------------------------------------------

ROWS_PER_PAGE_OPTIONS = [
    {"label": str(v), "value": v} for v in (20, 40, 80, 100, 200, 1000, 2000)
] + [
    {"label": "All", "value": 99999},
]

CHUNKS_PER_LINE_OPTIONS = [
    {"label": str(n), "value": n} for n in (1, 2, 3, 4, 8, 12, 16)
]

TABLE_GROUPS_PER_ROW_OPTIONS = [
    {"label": str(n), "value": n} for n in (1, 2, 3, 4)
]