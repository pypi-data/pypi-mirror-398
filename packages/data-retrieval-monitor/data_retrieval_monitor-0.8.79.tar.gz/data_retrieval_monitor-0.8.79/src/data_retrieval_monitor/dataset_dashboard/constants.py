from typing import Dict, List, Tuple

DATA_STAGES = ["archive", "stage", "enrich", "consolidate"]  # Assuming based on code context
TAB_IDS = ["data", "features", "alphas", "strategies"]
FEATURE_STAGES = ["status"]
ALPHA_STAGES = ["status"]
STRAT_STAGES = ["status"]
                
DATA_STATUS_ORDER = [
    "failed", "overdue", "manual", "retrying", "running", "waiting",
    "succeeded", "queued", "allocated", "other"
]
FEATURES_STATUS_ORDER = ["F-Stat-001", "F-Stat-002", "F-Stat-003", "other"]
ALPHAS_STATUS_ORDER    = ["A-Stat-001", "A-Stat-002", "A-Stat-003", "other"]
STRATS_STATUS_ORDER    = ["S-Stat-001", "S-Stat-002", "S-Stat-003", "other"]


def status_order_for_tab(tab: str) -> List[str]:
    t = (tab or "data").lower()
    if t == "features": return FEATURES_STATUS_ORDER
    if t == "alphas":   return ALPHAS_STATUS_ORDER
    if t == "strategies": return STRATS_STATUS_ORDER
    return DATA_STATUS_ORDER

def _hex_to_rgb(h: str) -> Tuple[int,int,int]:
    h=h.lstrip("#"); return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

_BASE = {
    "waiting":"#F0E442","retrying":"#E69F00","running":"#56B4E9",
    "failed":"#D55E00","overdue":"#A50E0E","manual":"#808080",
    "succeeded":"#009E73","queued":"#9370DB","allocated":"#8B4513","other":"#999999",
}
BASE_RGB = {k:_hex_to_rgb(v) for k,v in _BASE.items()}

def rgb_for_tab(tab: str) -> Dict[str, Tuple[int,int,int]]:
    t = (tab or "data").lower()
    if t == "features":
        return {
            "F-Stat-001": _hex_to_rgb("#1f77b4"),
            "F-Stat-002": _hex_to_rgb("#ff7f0e"),
            "F-Stat-003": _hex_to_rgb("#2ca02c"),
            "other": BASE_RGB.get("other", (153,153,153)),
        }
    if t == "alphas":
        return {
            "A-Stat-001": _hex_to_rgb("#9467bd"),
            "A-Stat-002": _hex_to_rgb("#8c564b"),
            "A-Stat-003": _hex_to_rgb("#17becf"),
            "other": BASE_RGB.get("other", (153,153,153)),
        }
    if t == "strategies":
        return {
            "S-Stat-001": _hex_to_rgb("#d62728"),
            "S-Stat-002": _hex_to_rgb("#bcbd22"),
            "S-Stat-003": _hex_to_rgb("#7f7f7f"),
            "other": BASE_RGB.get("other", (153,153,153)),
        }
    return {s: BASE_RGB.get(s, BASE_RGB.get("other",(153,153,153))) for s in DATA_STATUS_ORDER}

def status_scores_for_tab(tab: str) -> Dict[str, float]:
    t = (tab or "data").lower()
    if t == "features":
        return {"F-Stat-001": -0.8, "F-Stat-002": 0.2, "F-Stat-003": 0.8, "other": -0.2}
    if t == "alphas":
        return {"A-Stat-001": -0.8, "A-Stat-002": 0.2, "A-Stat-003": 0.8, "other": -0.2}
    if t == "strategies":
        return {"S-Stat-001": -0.8, "S-Stat-002": 0.2, "S-Stat-003": 0.8, "other": -0.2}
    return {
        "failed": -1.0, "overdue": -0.8, "retrying": -0.4, "running": 0.5,
        "waiting": 0.0, "manual": 0.1, "queued": -0.1, "allocated": 0.2,
        "succeeded": 1.0, "other": -0.2,
    }
