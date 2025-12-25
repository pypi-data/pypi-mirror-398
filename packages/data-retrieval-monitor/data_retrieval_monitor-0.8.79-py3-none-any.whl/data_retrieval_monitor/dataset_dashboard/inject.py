# dataset_dashboard/inject.py
from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import pytz
from dash.dependencies import ALL
import dash
from dash import Input, Output, State, html, dcc, no_update
from dash.exceptions import PreventUpdate

import dataset_dashboard.components.compute as compute
from dataset_dashboard.constants import DATA_STAGES, status_order_for_tab
from dataset_dashboard.utils import to_local_str
from dataset_dashboard.components.compute import (
    filtered_sorted_entries_cached,
    aggregate_counts_cached,
    filtered_stage_counts_cached,
)
from .utils import tab_version
# -------------------------
# Lightweight coherent caches (kept for counts; can be removed if you prefer fastpaths everywhere)
# -------------------------


def _subtree_for_tab(state: dict, tab: str) -> dict:
    tabs = state.get("tabs", {}) or {}
    return tabs.get(tab) or {}

# -------------------------
# Selection helpers (kept but UI is hidden; chunks are non-clickable)
# -------------------------
def _list_datasets_for_tab(state: dict, tab: str) -> List[str]:
    tab = (tab or "data").lower()
    jobs = (state.get("tabs", {}).get(tab, {}) or {}).get("jobs", {}) or {}
    names = set()
    for o_map in jobs.values():
        for m_map in (o_map or {}).values():
            for ds in (m_map or {}).keys():
                names.add(str(ds))
    return sorted(names)

def _chunk_indices_for_dataset(state: dict, tab: str, dataset: Optional[str], stage: Optional[str] = None) -> List[int]:
    if not dataset:
        return []
    tab = (tab or "data").lower()
    jobs = (state.get("tabs", {}).get(tab, {}) or {}).get("jobs", {}) or {}
    for o_map in jobs.values():
        for m_map in (o_map or {}).values():
            node = (m_map or {}).get(dataset)
            if not node or not isinstance(node, dict):
                continue
            if tab == "data":
                if not stage:
                    return []
                st_node = (node or {}).get(stage) or {}
                chunks = (st_node.get("chunks") or [])
                return list(range(len(chunks)))
            else:
                st_node = (node or {}).get("status") or {}
                chunks = (st_node.get("chunks") or [])
                return list(range(len(chunks)))
    return []

def _parse_hash(hash_str: Optional[str]):
    """Return (dataset, idx, tab_override, stage_override) parsed from #pick?..."""
    from urllib.parse import parse_qs, unquote_plus
    if not hash_str or not hash_str.startswith("#pick?"):
        return None, None, None, None
    qs = hash_str[6:]
    qs_map = parse_qs(qs, keep_blank_values=True)
    ds = unquote_plus(qs_map.get("dataset", [""])[0]) or None
    idx_s = qs_map.get("idx", [""])[0]
    tab_override = (qs_map.get("tab", [""])[0] or "").lower() or None
    stage_override = (qs_map.get("stage", [""])[0] or "").lower() or None
    try:
        idx = int(idx_s)
    except Exception:
        idx = None
    if tab_override not in ("data", "features", "alphas", "strategies"):
        tab_override = None
    if tab_override != "data":
        stage_override = None
    return ds, idx, tab_override, stage_override

def _effective_tab(main_tab: str, tab_override: Optional[str]) -> str:
    main_tab = (main_tab or "all").lower()
    if main_tab == "all" and tab_override in ("data", "features", "alphas", "strategies"):
        return tab_override
    return main_tab if main_tab in ("data", "features", "alphas", "strategies") else "data"

# -------------------------
# Deduped overview counts for DATA (one count per dataset)
# -------------------------
def _overview_counts_data_dedup(state: dict, owner_sel: Optional[str] = None) -> Dict[str, int]:
    vocab = status_order_for_tab("data")
    rank = {s: i for i, s in enumerate(vocab)}

    def worst_from_counts(counts: Dict[str, int]) -> Optional[str]:
        worst, worst_i = None, 10**9
        for s, c in (counts or {}).items():
            if not c:
                continue
            i = rank.get(s, len(rank) + 1)
            if i < worst_i:
                worst_i, worst = i, s
        return worst

    tabs = state.get("tabs", {}) or {}
    data_tree = tabs.get("data", {}) or {}
    jobs = data_tree.get("jobs", {}) or {}
    owners_to_scan = list(jobs.keys())
    if owner_sel and str(owner_sel).lower() != "all":
        owners_to_scan = [o for o in owners_to_scan if o == owner_sel]

    ds_worst: Dict[str, str] = {}
    for owner in owners_to_scan:
        for mode, name_map in (jobs.get(owner, {}) or {}).items():
            for dataset, node in (name_map or {}).items():
                worst_dataset = None
                worst_i = 10**9
                for stg in DATA_STAGES:
                    st_node = (node or {}).get(stg) or {}
                    counts = (st_node.get("counts") or {})
                    w = worst_from_counts(counts)
                    if w is None:
                        continue
                    i = rank.get(w, len(rank) + 1)
                    if i < worst_i:
                        worst_i = i
                        worst_dataset = w
                if worst_dataset is None:
                    for stg in DATA_STAGES:
                        st_node = (node or {}).get(stg) or {}
                        chunks = (st_node.get("chunks") or [])
                        for ch in chunks:
                            s = ch.get("status") or "other"
                            i = rank.get(s, len(rank) + 1)
                            if i < worst_i:
                                worst_i, worst_dataset = i, s
                if worst_dataset is None:
                    worst_dataset = "other"
                prev = ds_worst.get(dataset)
                if prev is None or rank.get(worst_dataset, 9999) < rank.get(prev, 9999):
                    ds_worst[dataset] = worst_dataset

    out: Dict[str, int] = {s: 0 for s in vocab}
    for s in ds_worst.values():
        out[s] = out.get(s, 0) + 1
    known = set(vocab)
    other_extra = 0
    for s in list(out.keys()):
        if s not in known:
            other_extra += out.pop(s, 0)
    if other_extra:
        out["other"] = out.get("other", 0) + other_extra
    return out

# -------------------------
# Register callbacks
# -------------------------
def register_callbacks(app, cfg, host):
    store = host.store
    pie = host.pies
    linker = getattr(getattr(host, "table", None), "linker", None)

    @app.callback(
        # KPIs
        Output("kpi-container", "children"),

        # Filter options
        Output("owner-filter", "options"),
        Output("stage-filter", "options"),
        Output("status-filter", "options"),

        # External pies (hidden)
        Output("pie-stage", "figure"),
        Output("pie-archive", "figure"),
        Output("pie-enrich", "figure"),
        Output("pie-consolidate", "figure"),
        Output("pie-overview", "figure"),

        # Table + footer + refresh
        Output("table-title", "children"),
        Output("table-container", "children"),
        Output("now-indicator", "children"),
        Output("interval", "interval"),

        # Visibilities
        Output("advanced-controls", "style"),
        Output("pie-stage", "style"),
        Output("pie-archive", "style"),
        Output("pie-enrich", "style"),
        Output("pie-consolidate", "style"),
        Output("pie-overview", "style"),

        Output("table-page", "data", allow_duplicate=True),

        # Pager outputs
        Output("table-pager", "max_value"),
        Output("table-pager", "active_page"),
        Output("table-pager", "style"),

        # Inputs
        Input("interval", "n_intervals"),
        Input("main-tabs", "value"),
        Input("owner-filter", "value"),
        Input("stage-filter", "value"),
        Input("status-filter", "value"),
        Input("table-groups", "value"),
        Input("chunks-per-line", "value"),
        Input("sort-by", "value"),
        Input("rows-per-page", "value"),
        Input("table-pager", "active_page"),
        State("table-page", "data"),
        State("interval", "interval"),
        prevent_initial_call=True,
    )
    def refresh(_n, tab,
                owner_sel, stage_filter, status_filter,
                groups_per_row, chunks_per_line, sort_by, rows_per_page,
                pager_active, current_page, cur_interval):

        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        tab = str(tab or "all").lower()
        state = store.state()
        tab_for_subtree = "data" if tab == "all" else tab
        tree = _subtree_for_tab(state, tab_for_subtree)

        # add these versions up top (we’ll reuse them)
        ver_data = tab_version(store, "data")
        ver_feat = tab_version(store, "features")
        ver_alph = tab_version(store, "alphas")
        ver_stra = tab_version(store, "strategies")

        # Filters
        owner_opts = store.list_filters_for_tab(tab_for_subtree)
        if tab in ("data", "all"):
            stage_opts = [{"label": s.title(), "value": s} for s in DATA_STAGES]
        else:
            stage_opts = []

        if tab == "all":
            union_vocab = sorted(set(
                status_order_for_tab("data")
                + status_order_for_tab("features")
                + status_order_for_tab("alphas")
                + status_order_for_tab("strategies")
            ))
            status_vocab = union_vocab
        else:
            status_vocab = status_order_for_tab(tab_for_subtree)
        status_opts = [{"label": s, "value": s} for s in status_vocab]

        # Hidden external pies (keep valid)
        if tab == "data":
            data_counts = aggregate_counts_cached(ver_data, "data")
            fig_ext_overview = pie.figure("data", "Overview",  data_counts, labels_order=status_vocab)
            fig_ext_stage    = pie.figure("data", "Stage",     filtered_stage_counts_cached(ver_data, "data", owner_sel, "stage"),      labels_order=status_vocab)
            fig_ext_archive  = pie.figure("data", "Archive",   filtered_stage_counts_cached(ver_data, "data", owner_sel, "archive"),    labels_order=status_vocab)
            fig_ext_enrich   = pie.figure("data", "Enrich",    filtered_stage_counts_cached(ver_data, "data", owner_sel, "enrich"),     labels_order=status_vocab)
            fig_ext_cons     = pie.figure("data", "Consolidate",filtered_stage_counts_cached(ver_data, "data", owner_sel, "consolidate"),labels_order=status_vocab)

        elif tab == "all":
            tot_counts = {}
            for tname, ver in (("data", ver_data), ("features", ver_feat), ("alphas", ver_alph), ("strategies", ver_stra)):
                part = aggregate_counts_cached(ver, tname)
                for k, v in part.items():
                    tot_counts[k] = tot_counts.get(k, 0) + int(v or 0)
            fig_ext_overview = pie.figure("all", "Overview", tot_counts, labels_order=status_vocab)
            # keep the data-stage breakdown pies aligned to the data status vocabulary
            fig_ext_stage    = pie.figure("data", "Stage",     filtered_stage_counts_cached(ver_data, "data", owner_sel, "stage"),      labels_order=status_order_for_tab("data"))
            fig_ext_archive  = pie.figure("data", "Archive",   filtered_stage_counts_cached(ver_data, "data", owner_sel, "archive"),    labels_order=status_order_for_tab("data"))
            fig_ext_enrich   = pie.figure("data", "Enrich",    filtered_stage_counts_cached(ver_data, "data", owner_sel, "enrich"),     labels_order=status_order_for_tab("data"))
            fig_ext_cons     = pie.figure("data", "Consolidate",filtered_stage_counts_cached(ver_data, "data", owner_sel, "consolidate"),labels_order=status_order_for_tab("data"))
        else:
            tab_counts = aggregate_counts_cached(
                {"features": ver_feat, "alphas": ver_alph, "strategies": ver_stra}[tab],
                tab
            )
            fig_ext_overview = pie.figure(tab, "Overview", tab_counts, labels_order=status_vocab)
            fig_ext_stage = fig_ext_archive = fig_ext_enrich = fig_ext_cons = fig_ext_overview

        # KPI + vertical pies
        if tab == "all":
            tot_counts = {}
            for tname, ver in (("data", ver_data), ("features", ver_feat), ("alphas", ver_alph), ("strategies", ver_stra)):
                part = aggregate_counts_cached(ver, tname)
                for k, v in part.items():
                    tot_counts[k] = tot_counts.get(k, 0) + int(v or 0)
            pies_for_kpi = [
                pie.figure("all", "Overview",  tot_counts,                           labels_order=status_vocab),
                pie.figure("data", "Data",     aggregate_counts_cached(ver_data, "data"),      labels_order=status_order_for_tab("data")),
                pie.figure("features", "Features", aggregate_counts_cached(ver_feat, "features"), labels_order=status_order_for_tab("features")),
                pie.figure("alphas", "Alphas", aggregate_counts_cached(ver_alph, "alphas"),    labels_order=status_order_for_tab("alphas")),
                pie.figure("strategies", "Strategies", aggregate_counts_cached(ver_stra, "strategies"), labels_order=status_order_for_tab("strategies")),
            ]
            k_counts = tot_counts
        elif tab == "data":
            data_counts = aggregate_counts_cached(ver_data, "data")
            pies_for_kpi = [
                pie.figure("data", "Overview",  data_counts, labels_order=status_vocab),
                pie.figure("data", "Archive",   filtered_stage_counts_cached(ver_data, "data", owner_sel, "archive"),    labels_order=status_vocab),
                pie.figure("data", "Stage",     filtered_stage_counts_cached(ver_data, "data", owner_sel, "stage"),      labels_order=status_vocab),
                pie.figure("data", "Enrich",    filtered_stage_counts_cached(ver_data, "data", owner_sel, "enrich"),     labels_order=status_vocab),
                pie.figure("data", "Consolidate",filtered_stage_counts_cached(ver_data, "data", owner_sel, "consolidate"),labels_order=status_vocab),
            ]
            k_counts = data_counts
        else:
            tab_counts = aggregate_counts_cached(
                {"features": ver_feat, "alphas": ver_alph, "strategies": ver_stra}[tab],
                tab
            )
            pies_for_kpi = [pie.figure(tab, "Overview", tab_counts, labels_order=status_vocab)]
            k_counts = tab_counts

        pie_graphs = [
            dcc.Graph(
                figure=f,
                style={"height": "260px" if i == 0 else "200px",
                       "marginBottom": "8px" if i < len(pies_for_kpi)-1 else "0px",
                       "width": "100%"},
                config={"displayModeBar": False},
            ) for i, f in enumerate(pies_for_kpi)
        ]

        # KPI container (selection UI removed). Keep hidden feedback target for clipboard callback.
        kpi_children = html.Div(
            [
                html.Div(id="copy-feedback", style={"display": "none"}),
                html.Div(host.kpis.render("all" if tab == "all" else tab, status_vocab, k_counts, per_row=3),
                         className="w-100", style={"width": "100%"}),
                html.Div(pie_graphs, style={"display": "flex", "flexDirection": "column", "width": "100%"}),
            ],
            className="w-100",
            style={"width": "100%", "alignSelf": "stretch", "height": "100%"},
        )

        pie_styles = [{"display": "none"}] * 5
        dv_style = {"display": "block"} if tab in ("data", "all") else {"display": "none"}

        # Tables & pagination
        vis_stages = list(stage_filter or DATA_STAGES) if tab in ("data", "all") else []
        rows_per_page = int(rows_per_page) if rows_per_page else 20

        if tab == "all":
            # Use Flask-Caching wrappers for lists (shared across workers)
            ver_data = tab_version(store, "data")
            ver_feat = tab_version(store, "features")
            ver_alph = tab_version(store, "alphas")
            ver_stra = tab_version(store, "strategies")

            data_all = filtered_sorted_entries_cached(
                ver_data, "data", owner_sel,
                tuple(vis_stages or ()),
                tuple(status_filter or ()),
                (sort_by or "name_asc"),
            )
            feats_all = filtered_sorted_entries_cached(
                ver_feat, "features", owner_sel,
                tuple(()), tuple(status_filter or ()),
                (sort_by or "name_asc")
            )
            alphas_all = filtered_sorted_entries_cached(
                ver_alph, "alphas", owner_sel,
                tuple(()), tuple(status_filter or ()),
                (sort_by or "name_asc"),
            )
            strats_all = filtered_sorted_entries_cached(
                ver_stra, "strategies", owner_sel,
                tuple(()), tuple(status_filter or ()),
                (sort_by or "name_asc"),
            )

            totals = {
                "data": len(data_all),
                "features": len(feats_all),
                "alphas": len(alphas_all),
                "strategies": len(strats_all),
            }

            if rows_per_page == 999999:
                total_pages = 1
                current_page = 0
                slices = {"data": data_all, "features": feats_all, "alphas": alphas_all, "strategies": strats_all}
            else:
                total_pages = max(
                    1,
                    *[
                        (totals[k] + rows_per_page - 1) // max(1, rows_per_page)
                        for k in totals
                    ],
                )
                reset_triggers = ['main-tabs', 'owner-filter', 'stage-filter', 'status-filter', 'sort-by', 'rows-per-page']
                if triggered_id == "table-pager":
                    current_page = (pager_active - 1) if pager_active else int(current_page or 0)
                elif triggered_id in reset_triggers:
                    current_page = 0
                else:
                    current_page = int(current_page or 0)
                current_page = max(0, min(current_page, total_pages - 1))

                def _slice(lst):
                    start = current_page * rows_per_page
                    end = min(start + rows_per_page, len(lst))
                    return lst[start:end]

                slices = {
                    "data": _slice(data_all),
                    "features": _slice(feats_all),
                    "alphas": _slice(alphas_all),
                    "strategies": _slice(strats_all),
                }

            table = host.table.render(
                "all",
                slices["data"],
                groups_per_row,
                chunks_per_line,
                state,
                vis_stages=vis_stages,
                entries_by_section=slices,
                page_meta={
                    "mode": "all",
                    "current_page": current_page,
                    "rows_per_page": rows_per_page,
                    "total_pages": total_pages,
                    "totals": totals,
                },
            )

            if total_pages > 1:
                pager_max_value = total_pages
                pager_active_page = current_page + 1
                pager_style = {
                    "display": "inline-flex",
                    "flexWrap": "wrap",
                    "gap": "6px",
                    "alignItems": "center",
                    "maxWidth": "100%",
                }
            else:
                pager_max_value = 1
                pager_active_page = 1
                pager_style = {"display": "none"}

        else:
            ver = tab_version(store, tab)
            entries_sorted = filtered_sorted_entries_cached(
                ver, tab, owner_sel,
                tuple(vis_stages or ()),
                tuple(status_filter or ()),
                (sort_by or "name_asc"),
            )
            total_entries = len(entries_sorted)

            if rows_per_page == 999999:
                rows_per_page = total_entries + 1

            total_pages = max(1, (total_entries + rows_per_page - 1) // rows_per_page)

            reset_triggers = ['main-tabs', 'owner-filter', 'stage-filter', 'status-filter', 'sort-by', 'rows-per-page']
            if triggered_id == "table-pager":
                current_page = (pager_active - 1) if pager_active else int(current_page or 0)
            elif triggered_id in reset_triggers:
                current_page = 0
            else:
                current_page = int(current_page or 0)
            current_page = max(0, min(current_page, total_pages - 1))

            start = current_page * rows_per_page
            end = min(start + rows_per_page, total_entries)
            sliced_entries = entries_sorted[start:end]

            table = host.table.render(
                tab,
                sliced_entries,
                groups_per_row,
                chunks_per_line,
                state,
                vis_stages=vis_stages,
                page_meta={
                    "mode": "single",
                    "current_page": current_page,
                    "rows_per_page": rows_per_page,
                    "total_pages": total_pages,
                    "total_count": total_entries,
                },
            )

            if total_pages > 1:
                pager_max_value = total_pages
                pager_active_page = current_page + 1
                pager_style = {
                    "display": "inline-flex",
                    "flexWrap": "wrap",
                    "gap": "6px",
                    "alignItems": "center",
                    "maxWidth": "100%",
                }
            else:
                pager_max_value = 1
                pager_active_page = 1
                pager_style = {"display": "none"}

        table_children = html.Div([table], style={"width": "100%"})

        # Footer
        meta = tree.get("meta") or {}
        env = meta.get("env", "local")
        last_ingest = meta.get("last_ingest_at")
        now = to_local_str(datetime.now(pytz.utc))
        now_indicator = f"{env.UPPER() if hasattr(env,'UPPER') else str(env).upper()} | {now} | Last ingest: {to_local_str(last_ingest) or '—'}"

        # Interval per cfg
        desired_interval = int(getattr(cfg, "refresh_ms", 30000) or 30000)
        next_interval = no_update if (cur_interval == desired_interval) else desired_interval

        return (
            kpi_children,
            owner_opts,
            stage_opts,
            status_opts,
            fig_ext_stage, fig_ext_archive, fig_ext_enrich, fig_ext_cons, fig_ext_overview,
            "",
            table_children,
            now_indicator,
            next_interval,
            dv_style,
            *([{"display": "none"}] * 5),
            current_page,
            pager_max_value,
            pager_active_page,
            pager_style,
        )

    # Clipboard per-chunk (kept; writes to hidden #copy-feedback)
    app.clientside_callback(
        """
        function(nClicksList) {
            const ctx = dash_clientside.callback_context;
            if (!ctx || !ctx.triggered || !ctx.triggered.length) { return ""; }
            try {
                const prop = ctx.triggered[0].prop_id.split('.')[0];
                const obj = JSON.parse(prop);   // {"type":"copy-chunk-raw","raw":"..."}
                const raw = (obj && obj.raw) ? String(obj.raw) : "";
                if (raw && navigator && navigator.clipboard) {
                    navigator.clipboard.writeText(raw);
                    return "Copied log path.";
                }
            } catch (e) { /* ignore */ }
            return "";
        }
        """,
        Output("copy-feedback", "children", allow_duplicate=True),
        Input({"type": "copy-chunk-raw", "raw": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )

# -------------------------
# Ingest routes (unchanged core; cache clears)
# -------------------------
def register_ingest_routes(server, host):
    from flask import request, jsonify

    def _canon_status(tab: str, raw: Optional[str]) -> str:
        vocab = set(status_order_for_tab(tab))
        s = (raw or "other")
        s = s.lower() if tab == "data" else s
        return s if s in vocab else "other"

    def _canon_stage(tab: str, raw_stage: Optional[str]) -> Optional[str]:
        t = (tab or "data").lower()
        if t != "data":
            return "status"
        s = str(raw_stage or "").strip().lower()
        aliases = {
            "arch": "archive", "archives": "archive", "archive": "archive",
            "stage": "stage", "staging": "stage",
            "enrich": "enrich", "enrichment": "enrich", "enriched": "enrich",
            "consolidate": "consolidate", "consolidation": "consolidate", "cons": "consolidate",
        }
        s = aliases.get(s, s)
        return s if s in set(DATA_STAGES) else None

    def _canon_chunk_fields(tab: str, ch: dict) -> dict:
        ch = dict(ch or {})
        ch["status"] = _canon_status(tab, ch.get("status") or ch.get("state") or ch.get("result"))
        if "log" not in ch or not ch.get("log"):
            for k in ("log_path", "logfile", "logfile_path", "raw_log", "raw", "path"):
                if ch.get(k):
                    ch["log"] = ch[k]; break
        if "proc" not in ch or not ch.get("proc"):
            for k in ("proc_url", "process_url", "ui", "url", "link"):
                if ch.get(k):
                    ch["proc"] = ch[k]; break
        return ch

    def _canon_items(tab: str, items: List[dict]) -> List[dict]:
        out: List[dict] = []
        for it in items or []:
            it = dict(it or {})
            stg = _canon_stage(tab, it.get("stage"))
            if stg is None:
                continue
            chs = [_canon_chunk_fields(tab, ch) for ch in (it.get("chunks") or [])]
            it["stage"] = stg if (tab or "data").lower() == "data" else "status"
            it["chunks"] = chs
            if "data_name" not in it or not it.get("data_name"):
                for k in ("dataset", "name", "data", "id"):
                    if it.get(k):
                        it["data_name"] = it[k]
                        break
            out.append(it)
        return out

    def _apply(tab: str, items: List[dict], meta: Optional[dict]):
        host.store.apply_snapshot_with_meta_tab(tab, items, meta or {})


    @server.route("/ingest_snapshot", methods=["POST"])
    def ingest_snapshot():
        try:
            body = request.get_json(force=True, silent=False)
            if isinstance(body, list):
                items = _canon_items("data", body)
                _apply("data", items, {})
                return jsonify({"ok": True})
            if not isinstance(body, dict):
                return jsonify({"ok": False, "error": "Unsupported payload"}), 400

            tabs_pack = body.get("tabs")
            if isinstance(tabs_pack, dict):
                for t, pack in tabs_pack.items():
                    if not isinstance(pack, dict):
                        continue
                    tab = str(t).lower()
                    if tab == "all":
                        continue
                    items = pack.get("snapshot") or pack.get("items") or []
                    meta = pack.get("meta") or {}
                    items = _canon_items(tab, list(items or []))
                    _apply(tab, items, dict(meta or {}))
                return jsonify({"ok": True})

            tab = str(body.get("tab") or "data").lower()
            if tab == "all":
                return jsonify({"ok": False, "error": "tab 'all' is synthetic"}), 400
            items = body.get("snapshot") or body.get("items") or []
            meta = body.get("meta") or {}
            if not isinstance(items, list):
                return jsonify({"ok": False, "error": "Send {snapshot:[...]} or a JSON array"}), 400
            items = _canon_items(tab, list(items or []))
            _apply(tab, items, dict(meta or {}))
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @server.route("/__debug__/store_summary", methods=["GET"])
    def store_summary():
        from flask import jsonify as _jsonify
        st = host.store.state()
        tabs = st.get("tabs", {})
        out: Dict[str, Dict] = {"tabs": {}}
        for t, tree in tabs.items():
            jobs = tree.get("jobs", {}) or {}
            n = 0
            for o_map in jobs.values():
                for m_map in o_map.values():
                    n += len(m_map)
            meta = tree.get("meta", {}) or {}
            owners = sorted(jobs.keys())
            modes = set()
            for o_map in jobs.values():
                modes.update(o_map.keys())
            out["tabs"][t] = {
                "datasets_total": n,
                "meta": {
                    "env": meta.get("env"),
                    "last_ingest_at": meta.get("last_ingest_at"),
                    "owner_labels": meta.get("owner_labels", {}),
                },
                "modes": sorted(modes),
                "owners": owners,
                "updated_at": tree.get("updated_at"),
            }
        return _jsonify(out)

    @server.route("/__debug__/leaf", methods=["GET"])
    def debug_leaf():
        from flask import request as _req, jsonify as _jsonify
        st = host.store.state()
        tab = _req.args.get("tab", "data")
        owner = _req.args.get("owner", "kimdg")
        mode = _req.args.get("mode", "live")
        dataset = _req.args.get("dataset")
        tree = st.get("tabs", {}).get(tab, {})
        leaf = (tree.get("jobs", {})
                .get(owner, {}).get(mode, {}).get(dataset, {}))
        return _jsonify(leaf)