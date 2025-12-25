# dataset_dashboard/components/table.py
from typing import List, Optional, Tuple, Dict
from urllib.parse import quote_plus
from dash import html, dcc
import dash_bootstrap_components as dbc

from dataset_dashboard.constants import DATA_STAGES, rgb_for_tab, status_order_for_tab
from dataset_dashboard.components.compute import best_status  # keep if you use elsewhere


class TableComponent:
    """
    - Data tab: Dataset + ONLY the visible_stages columns (defaults to all DATA_STAGES).
    - All tab: Separate tables for Data, Features, Alphas, Strategies with horizontal stacking and margins.
    - Other tabs (features/alphas/strategies): Name + single Status column
    """

    def __init__(self, log_linker, clipboard_fallback_open: bool):
        self.linker = log_linker
        # When True -> show per-chunk clipboard inside each cell (heavier but convenient)
        # When False -> NO per-cell clipboard; use the single central copy button in the selection panel
        self.fallback_open = bool(clipboard_fallback_open)

    # ---------- helpers ----------
    @staticmethod
    def _safe(map_like: Optional[dict]) -> dict:
        return map_like or {}

    @staticmethod
    def _shade(tab: str, status: Optional[str], alpha=0.18):
        if not status:
            return {"backgroundColor": "#FFFFFF"}
        r, g, b = rgb_for_tab(tab).get(status, (230, 230, 230))
        return {"backgroundColor": f"rgba({r},{g},{b},{alpha})"}

    def _text_color(self, tab: str, status: Optional[str]) -> str:
        r, g, b = rgb_for_tab(tab).get((status or "other"), (120, 120, 120))
        return f"rgb({r},{g},{b})"

    def _tabs_root(self, tree: dict) -> Optional[dict]:
        if isinstance(tree, dict) and "tabs" in tree and isinstance(tree["tabs"], dict):
            return tree
        return None

    def _lookup_name_and_leaf(self, tabs_root: dict, tab_name: str, owner: str, mode: str, dataset: str):
        jobs = self._safe(self._safe(self._safe(tabs_root.get("tabs")).get(tab_name)).get("jobs"))
        # try exact owner/mode first
        name_map = self._safe(jobs.get(owner, {}).get(mode) or jobs.get(owner, {}).get("live", {}))
        if isinstance(name_map, dict) and dataset in name_map:
            leaf = self._safe(self._safe(name_map.get(dataset)).get("status"))
            return dataset, {"counts": self._safe(leaf.get("counts")), "chunks": list(self._safe(leaf.get("chunks")))}
        # fallback: search other owners/modes for same dataset key
        for o_map in jobs.values():
            for m_map in self._safe(o_map).values():
                if dataset in self._safe(m_map):
                    node = self._safe(m_map.get(dataset))
                    leaf = self._safe(node.get("status"))
                    return dataset, {"counts": self._safe(leaf.get("counts")), "chunks": list(self._safe(leaf.get("chunks")))}
        return None, {"counts": {}, "chunks": []}

    def _worst_status_from_chunks(self, tab: str, chunks: List[dict]) -> Optional[str]:
        """Return the WORST status by tab vocabulary order (index 0 = worst)."""
        vocab = status_order_for_tab(tab)
        rank = {s: i for i, s in enumerate(vocab)}
        worst = None
        worst_i = 10**9
        for ch in (chunks or []):
            s = ch.get("status") or "other"
            i = rank.get(s, len(rank) + 1)
            if i < worst_i:
                worst_i = i
                worst = s
        return worst

    # ---------- per-chunk rendering ----------
    def _chunk_inline_links(
        self,
        tab: str,
        dataset: str,
        idx: int,
        ch: dict,
        *,
        source_tab: Optional[str] = None,
        source_stage: Optional[str] = None,
    ):
        """
        Render a lightweight inline set per chunk:
          - clickable 'c{idx}' that sets #pick?dataset=...&idx=...&tab=...&stage=...
          - 'p' link to proc (if available)
          - OPTIONAL per-chunk clipboard (only when self.fallback_open == True)
        """
        # choose palette based on where this chunk logically lives
        color_tab = (source_tab or tab or "data").lower()

        status = (ch.get("status") or "other")
        proc = ch.get("proc")
        raw = ch.get("log")
        href = None
        if self.linker and raw:
            try:
                href = self.linker.href_for(raw)
            except Exception:
                href = None

        label = f"C{idx}"

        nodes: List[html.Component] = [
            html.A(
                label,
                # href=f"#pick?{qs}",
                title=f"Select {dataset}[{idx}]",
                style={
                    "fontWeight": 600,
                    "color": self._text_color(color_tab, status),  # colored label
                    "textDecoration": "none",
                    "marginRight": "6px",
                },
            )
        ]

        if proc:
            nodes.append(
                html.A(
                    "p",
                    href=proc,
                    target="_blank",
                    title="Open process UI",
                    style={"textDecoration": "underline", "marginRight": "8px"},
                )
            )

        # Either per-cell clipboard (heavier) OR central clipboard (lighter)
        if self.fallback_open and (raw or href):
            # small clipboard overlay next to the chunk
            clip_target = str(raw or href)
            nodes.append(
                html.Span(
                    [
                        html.Span("📋", title="Copy log path", style={"fontSize": "12px", "opacity": 0.85}),
                        dcc.Clipboard(
                            content=clip_target,
                            title="Copy",
                            style={
                                "position": "absolute",
                                "left": 0, "top": 0,
                                "width": "1.2em", "height": "1.2em",
                                "opacity": 0.01, "zIndex": 5, "cursor": "pointer",
                                "border": 0, "background": "transparent",
                            },
                        ),
                    ],
                    style={"position": "relative", "display": "inline-block", "marginRight": "8px"},
                )
            )

        return nodes

    def _chunk_block(
    self,
    tab: str,
    chunks: List[dict],
    chunks_per_line: int,
    prefix: str,
    dataset_name: Optional[str] = None,
    compact: bool = False,
    allow_copy: bool = True,
    ):
        """
        Lightweight inline rendering of all chunks as rows with up to `chunks_per_line` items:
        c0 [p]  c1 [p]  c2 [p]      (next line...)
        Each 'c#' updates #pick?... so the selection area updates without server trips.
        """
        if not chunks:
            return html.I("—", className="text-muted")

        ds = dataset_name or ""
        cpl = max(1, int(chunks_per_line or 6))

        # Group inline links into rows of length `cpl`
        lines: List[html.Div] = []
        row_nodes: List = []
        for i, ch in enumerate(chunks):
            row_nodes.extend(self._chunk_inline_links(tab, ds, i, ch))
            if (i + 1) % cpl == 0:
                # one visual row; keep each row nowrap to avoid breaking inside labels
                lines.append(html.Div(row_nodes, style={"whiteSpace": "nowrap"}))
                row_nodes = []
        if row_nodes:
            lines.append(html.Div(row_nodes, style={"whiteSpace": "nowrap"}))

        # Stack rows with small gap
        return html.Div(lines, style={"display": "grid", "rowGap": "2px"})

    # ---------- table builders ----------
    def _build_section_table(
        self,
        section_tab: str,
        entries_sorted: List[Tuple[int, str, str, str, dict]],
        gpr: int,
        chunks_per_line: int,
        state: dict,
        vis_stages: List[str],
        is_data: bool = False,
        compact: bool = False,
    ):
        title_txt = "Data" if is_data else (section_tab or "").capitalize()

        head_cells = []
        if is_data:
            per_group = [html.Th("Name", style={"whiteSpace": "nowrap"})] + [
                html.Th(s.title(), style={"whiteSpace": "nowrap"}) for s in vis_stages
            ]
        else:
            per_group = [html.Th("Name", style={"whiteSpace": "nowrap"}), html.Th("Status", style={"whiteSpace": "nowrap"})]
        for _ in range(gpr):
            head_cells.extend(per_group)
        head = html.Thead(html.Tr(head_cells))

        def _chunked(lst: List, n: int) -> List[List]:
            return [lst[i:i + n] for i in range(0, len(lst), n)]

        body_rows: List[html.Tr] = []
        for row_groups in _chunked(entries_sorted, gpr):
            tds: List[html.Td] = []
            for _, own, md, dn, d_map in row_groups:
                if is_data:
                    cells = [html.Td(dn, style={"fontWeight": "600", "whiteSpace": "nowrap"})]
                    for stg in vis_stages:
                        leaf = self._safe(d_map.get(stg))
                        chunks = list(self._safe(leaf.get("chunks")))
                        worst = self._worst_status_from_chunks("data", chunks)
                        cells.append(
                            html.Td(
                                self._chunk_block(
                                    "data",
                                    chunks,
                                    chunks_per_line,
                                    prefix="c",
                                    dataset_name=dn,
                                    compact=compact,
                                ),
                                style={
                                    "verticalAlign": "top",
                                    "padding": "6px 10px",
                                    "whiteSpace": "nowrap",
                                    **self._shade("data", worst, 0.18),
                                },
                            )
                        )
                    tds.extend(cells)
                else:
                    nm, leaf = self._lookup_name_and_leaf(self._tabs_root(state), section_tab, own, md, dn)
                    ds_name = nm or dn or "—"
                    chunks = list(self._safe(leaf.get("chunks")))
                    worst = self._worst_status_from_chunks(section_tab, chunks)
                    cells = [html.Td(ds_name, style={"fontWeight": "600", "whiteSpace": "nowrap"})]
                    cells.append(
                        html.Td(
                            self._chunk_block(
                                section_tab,
                                chunks,
                                chunks_per_line,
                                prefix=self._prefix_for_tab(section_tab),
                                dataset_name=ds_name,
                                compact=compact,
                            ),
                            style={
                                "verticalAlign": "top",
                                "padding": "6px 10px",
                                "whiteSpace": "nowrap",
                                **self._shade(section_tab, worst, 0.18),
                            },
                        )
                    )
                    tds.extend(cells)
            body_rows.append(html.Tr(tds))

        if not body_rows:
            return None  # Don't render empty tables

        table = dbc.Table(
            [head, html.Tbody(body_rows)],
            bordered=True,
            hover=False,
            size="sm",
            className="mb-1",
            style={
                "tableLayout": "auto",
                "width": "auto",
                "display": "inline-table",
            },
        )

        # Wrap with a title (keeps original inline layout/gaps in 'all' view)
        return html.Div(
            [
                html.Div(title_txt, className="h6", style={"fontWeight": 700, "margin": "0 0 6px 0"}),
                table,
            ],
            style={"display": "inline-block", "marginRight": "10ch"},
        )

    def render(
    self,
    tab: str,
    entries_sorted: List[Tuple[int, str, str, str, dict]],
    groups_per_row: int,
    chunks_per_line: int,
    state: dict,
    vis_stages: List[str] = DATA_STAGES,
    entries_by_section: Optional[Dict[str, List[Tuple[int, str, str, str, dict]]]] = None,
    page_meta: Optional[Dict] = None,
    ):
        gpr = max(1, int(groups_per_row or 2))
        if tab == "all":
            tables = []
            data_entries = (entries_by_section or {}).get("data", entries_sorted)
            features_entries = (entries_by_section or {}).get("features", entries_sorted)
            alphas_entries = (entries_by_section or {}).get("alphas", entries_sorted)
            strategies_entries = (entries_by_section or {}).get("strategies", entries_sorted)

            data_table = self._build_section_table("data", data_entries, gpr, chunks_per_line, state, vis_stages, True)
            if data_table:
                tables.append(data_table)
            features_table = self._build_section_table("features", features_entries, gpr, chunks_per_line, state, [], False)
            if features_table:
                tables.append(features_table)
            alphas_table = self._build_section_table("alphas", alphas_entries, gpr, chunks_per_line, state, [], False)
            if alphas_table:
                tables.append(alphas_table)
            strategies_table = self._build_section_table("strategies", strategies_entries, gpr, chunks_per_line, state, [], False)
            if strategies_table:
                tables.append(strategies_table)

            # Key change: prevent flex from stretching all tables to the tallest one
            return html.Div(
                tables,
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "gap": "10ch",
                    "flexWrap": "nowrap",
                    "alignItems": "flex-start",     # <- no equal-height stretching
                    "alignContent": "flex-start",
                    "overflowX": "auto",
                },
            )
        else:
            return self._build_section_table(
                tab,
                entries_sorted,
                gpr,
                chunks_per_line,
                state,
                vis_stages,
                (tab == "data"),
            )

    def _prefix_for_tab(self, tab: str) -> str:
        return {"data": "c", "features": "f", "alphas": "a", "strategies": "s"}.get((tab or "").lower(), "c")