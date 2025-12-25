from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from ..constants import status_scores_for_tab, status_order_for_tab, DATA_STAGES
from collections import defaultdict
from typing import Optional, Tuple
from ..caching import cache
from ..config import load_config, RUNTIME

_DEFAULT_TIMEOUT = load_config().cache_default_timeout

def _data_overview_unique_counts(state, owner_sel=None):
    """
    Build Data-tab 'Overview' counts where each DATASET is counted once.
    We merge counts from all data stages for a dataset, compute a single
    status via compute.best_status(..., 'data'), then tally one hit.
    Owner filter is respected by reusing filtered_sorted_entries.
    """
    # Pull entries for data with all stages visible so we can merge them
    entries = compute.filtered_sorted_entries(
        state, owner_sel, DATA_STAGES, [], "data", sort_by=None
    )

    vocab = status_order_for_tab("data")
    out = {s: 0 for s in vocab}

    for _, _own, _mode, _dn, d_map in entries:
        merged = {}
        for stg in DATA_STAGES:
            cnts = ((d_map or {}).get(stg) or {}).get("counts") or {}
            for k, v in cnts.items():
                merged[k] = merged.get(k, 0) + int(v or 0)

        status = compute.best_status(merged, "data") if merged else "other"
        if status not in out:
            status = "other"
        out[status] += 1

    return out

def best_status(counts: Dict[str,int], tab: str) -> Optional[str]:
    scores = status_scores_for_tab(tab)
    best = None
    best_s = -10**9
    for k,v in counts.items():
        s = scores.get(k, -0.2)
        if v>0 and s>best_s: best_s, best = s, k
    return best

def chunk_avg_score_for_leaf(leaf: Dict, tab: str) -> float:
    scores = status_scores_for_tab(tab)
    chunks = list(leaf.get("chunks") or [])
    if not chunks: return 0.0
    tot = 0.0; n=0
    for ch in chunks:
        st = (ch.get("status") or "other")
        tot += float(scores.get(st, -0.2)); n += 1
    return (tot / max(1,n))

def make_sort_key(tab: str, d_map: Dict, dn: str, own: str, sel_stages: List[str], sort_by: str):
    t = (tab or "data").lower()
    if sort_by == "name_asc":
        return (dn.lower(),)
    elif sort_by in ("chunk_asc", "chunk_desc"):
        if t == "data":
            vals = [chunk_avg_score_for_leaf(d_map.get(stg,{}), "data") for stg in sel_stages]
            avg = sum(vals)/max(1,len(vals))
        else:
            avg = chunk_avg_score_for_leaf(d_map.get("status",{}), t)
        return ((avg if sort_by=="chunk_asc" else -avg), dn.lower())
    else:
        return (dn.lower(),)


def aggregate_counts(state: dict, tab: str) -> dict:
    """
    For tabs != 'data':
      - Sum the per-dataset 'status.counts' (existing behavior).

    For tab == 'data':
      - Build a union of chunks across all DATA_STAGES **per dataset**.
      - Identify a chunk by its 'log' (or fallback key).
      - Collapse each chunk to its *worst* status using the tab's order.
      - Count each unique chunk exactly once.
    """
    tab = (tab or "data").lower()
    tabs = (state.get("tabs") or {})
    tree = (tabs.get(tab) or {})
    jobs = (tree.get("jobs") or {})
    out = defaultdict(int)

    if tab != "data":
        for o_map in jobs.values():
            for m_map in (o_map or {}).values():
                for ds_node in (m_map or {}).values():
                    st = (ds_node or {}).get("status") or {}
                    counts = (st.get("counts") or {})
                    for k, v in (counts or {}).items():
                        out[str(k)] += int(v or 0)
        return dict(out)

    # --- data overview: dedupe by chunk-id across stages, count worst status once
    order = status_order_for_tab("data")
    rank = {s: i for i, s in enumerate(order)}
    def worst_status(statuses):
        return min(statuses, key=lambda s: rank.get(s, len(order)+1)) if statuses else "other"

    for o_map in jobs.values():
        for m_map in (o_map or {}).values():
            for _ds_name, ds_node in (m_map or {}).items():
                by_chunk = {}  # chunk_id -> list(statuses seen across stages)
                for stg in DATA_STAGES:
                    st_node = (ds_node or {}).get(stg) or {}
                    chunks = (st_node.get("chunks") or [])
                    for i, ch in enumerate(chunks):
                        cid = ch.get("log") or ch.get("raw_log") or f"{stg}:{i}"
                        s = (ch.get("status") or "other")
                        (by_chunk.setdefault(cid, [])).append(s)
                for sts in by_chunk.values():
                    out[worst_status(sts)] += 1

    return dict(out)

def filtered_stage_counts(state: Dict, owner_sel: Optional[str], stage: str, tab: str = "data") -> Dict[str,int]:
    tabs = state.get("tabs", {})
    tree = tabs.get("data", {})
    out: Dict[str,int] = {}
    want_owner = None if str(owner_sel or "All").lower() in ("all","") else str(owner_sel).lower()
    for own, o_map in (tree.get("jobs") or {}).items():
        if want_owner and own != want_owner: continue
        for m_map in o_map.values():
            for d_map in m_map.values():
                leaf = d_map.get(stage, {})
                for k,v in (leaf.get("counts") or {}).items():
                    out[k] = out.get(k, 0) + int(v or 0)
    return out

def filtered_sorted_entries(
    state: Dict,
    owner_sel: Optional[str],
    sel_stages: List[str],
    status_filter: List[str],
    tab: str,
    sort_by: str
) -> List[Tuple[int, str, str, str, Dict]]:
    entries: List[Tuple[str, str, str, Dict]] = []
    want_owner = None if str(owner_sel or "All").lower() == "all" else str(owner_sel).lower()
    status_set = set(status_filter)
    use_filter = bool(status_set)
    tab_sub = "data" if tab == "all" else tab
    tree = state.get("tabs", {}).get(tab_sub, {})
    jobs = tree.get("jobs", {})
    
    for own in sorted(jobs.keys()):
        if want_owner and own != want_owner:
            continue
        o_map = jobs[own]
        for md in sorted(o_map.keys()):
            m_map = o_map[md]
            for dn in sorted(m_map.keys()):
                d_map = m_map[dn]
                if use_filter:
                    include = False
                    if tab_sub == "data":
                        check_stages = sel_stages if sel_stages else DATA_STAGES
                        if tab == "all":
                            check_stages = DATA_STAGES  # Ignore sel_stages for filtering in "all"
                        for stg in check_stages:
                            leaf = d_map.get(stg, {})
                            for ch in leaf.get("chunks", []):
                                st = ch.get("status") or "other"
                                if st in status_set:
                                    include = True
                                    break
                            if include:
                                break
                    else:
                        leaf = d_map.get("status", {})
                        for ch in leaf.get("chunks", []):
                            st = ch.get("status") or "other"
                            if st in status_set:
                                include = True
                                break
                    if not include:
                        continue
                entries.append((own, md, dn, d_map))
    
    def sk(e):
        stages_for_sort = sel_stages if sel_stages else DATA_STAGES
        return make_sort_key(tab, e[3], e[2], e[0], stages_for_sort, sort_by)
    
    entries_sorted = sorted(entries, key=sk)
    return [(i, own, md, dn, d_map) for i, (own, md, dn, d_map) in enumerate(entries_sorted)]



def bind_store(store_obj) -> None:
    """Bind the shared store once during app startup."""
    RUNTIME.fastpaths_store = store_obj

def _state():
    if RUNTIME.fastpaths_store is None:
        raise RuntimeError("compute.cached: store not bound. Call compute.bind_store(host.store) during app init.")
    return RUNTIME.fastpaths_store.state()



@cache.memoize(timeout=_DEFAULT_TIMEOUT)
def aggregate_counts_cached(version: int, tab: str) -> dict:
    """Versioned + cached aggregate counts for a tab."""
    st = _state()
    return aggregate_counts(st, tab)

@cache.memoize(timeout=_DEFAULT_TIMEOUT)
def filtered_stage_counts_cached(version: int, tab: str, owner_sel: Optional[str], stage: str) -> dict:
    """Versioned + cached stage counts (DATA tab)."""
    st = _state()
    return filtered_stage_counts(st, owner_sel, stage, tab)

@cache.memoize(timeout=_DEFAULT_TIMEOUT)
def filtered_sorted_entries_cached(
    version: int,
    tab: str,
    owner_sel: Optional[str],
    vis_stages: Tuple[str, ...],
    status_filter: Tuple[str, ...],
    sort_by: str,
) -> list:
    """Versioned + cached filtered/sorted entries for a tab."""
    st = _state()
    return filtered_sorted_entries(
        st,
        owner_sel,
        list(vis_stages or ()),
        list(status_filter or ()),
        tab,
        sort_by,
    )