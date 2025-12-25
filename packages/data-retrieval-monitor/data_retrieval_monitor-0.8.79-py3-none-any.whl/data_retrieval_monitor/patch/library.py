# qsg/app/dashboard/library.py (or dataset_dashboard/library.py)

from __future__ import annotations

from typing import Dict, List

from .constants import TAB_IDS  # or dataset_dashboard.constants, depending on package

IMPORT_FAILURES: Dict[str, str] = {}

# ---- dataset library -------------------------------------------------

try:
    # replace this with your real import
    import datasetlibrary as ds_library  # e.g. from qsg.dataset.library import DatasetLibrary as ds_library

except Exception as e:
    ds_library = None
    # Map failure to the DATA tab
    IMPORT_FAILURES["data"] = (
        f"DATA tab: dataset library import failed "
        f"({type(e).__name__}: {e})"
    )

# ---- feature library -------------------------------------------------

try:
    # replace this with your real import
    import featurelibrary as f_library  # e.g. from qsg.feature.library import FeatureLibrary as f_library

except Exception as e:
    f_library = None
    # Map failure to the FEATURES tab
    IMPORT_FAILURES["features"] = (
        f"FEATURES tab: feature library import failed "
        f"({type(e).__name__}: {e})"
    )

# If you have alpha/strategy libs, you can repeat the same pattern:
# try: import alpha_library as a_library; except: IMPORT_FAILURES["alphas"] = ...

def get_import_failures() -> Dict[str, str]:
    """
    Return a map: tab_id -> human-readable import failure message.
    """
    return dict(IMPORT_FAILURES)

def make_data_payload_for_owner(cfg, owner, ...):
    if ds_library is None:
        # either return empty payload or raise a *controlled* error
        return [], {"env": cfg.environment_label, "ingested_at": utc_now_iso(), "import_error": True}
    ...