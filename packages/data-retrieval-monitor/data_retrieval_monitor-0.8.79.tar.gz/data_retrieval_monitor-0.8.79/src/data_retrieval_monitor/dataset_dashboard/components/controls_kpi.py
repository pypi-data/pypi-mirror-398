from dash import html, dcc
import dash_bootstrap_components as dbc
from ..constants import DATA_STAGES
from dash import html
import dash_bootstrap_components as dbc
from typing import Dict, List, Optional

class ControlsComponent:
    def render(self, cfg):
        return dbc.Card(
            dbc.CardBody([
                html.H5("Controls", className="mb-3"),

                # Owner
                html.Div("Owner", className="text-muted small"),
                dcc.Dropdown(
                    id="owner-filter",
                    options=[],
                    value="All",
                    clearable=False,
                    className="mb-2",
                    style={"minWidth": "180px"},
                ),

                # ---- Stage filter lives in its own wrapper (can be hidden via advanced-controls.style)
                html.Div(
                    id="advanced-controls",
                    children=[
                        html.Div("Stage filter (ANY of)", className="text-muted small"),
                        dcc.Dropdown(
                            id="stage-filter",
                            options=[{"label": s.title(), "value": s} for s in DATA_STAGES],
                            value=DATA_STAGES,
                            multi=True,
                            className="mb-2",
                        ),
                    ],
                    style={"display": "block"},
                ),

                # ---- Status filter gets its OWN wrapper (always visible unless you choose to hide it)
                html.Div(
                    id="status-controls",
                    children=[
                        html.Div("Status filter (ANY of)", className="text-muted small"),
                        dcc.Dropdown(
                            id="status-filter",
                            options=[],     # options are still populated by the callback
                            value=[],        # multi-select; empty means “no filter”
                            multi=True,
                            placeholder="(none)",
                        ),
                    ],
                    style={"display": "block"},
                ),

                # Table settings
                html.Div("Table groups per row", className="text-muted small mt-2"),
                dcc.Dropdown(
                    id="table-groups",
                    options=[{"label": str(n), "value": n} for n in (1, 2, 3, 4, 5, 6)],
                    value=2,
                    clearable=False,
                    style={"width": "120px"},
                ),

                html.Div("Chunks per line", className="text-muted small mt-2"),
                dcc.Dropdown(
                    id="chunks-per-line",
                    options=[{"label": str(n), "value": n} for n in (1, 2, 3, 4, 6, 8, 10, 12, 16)],
                    value=6,
                    clearable=False,
                    style={"width": "120px"},
                ),
                

                html.Div("Sort by", className="text-muted small mt-2"),
                dcc.Dropdown(
                    id="sort-by",
                    options=[
                        {"label": "Data Name (A–Z)", "value": "name_asc"},
                        {"label": "Chunk Avg Score (worst→best)", "value": "chunk_asc"},
                        {"label": "Chunk Avg Score (best→worst)", "value": "chunk_desc"},
                    ],
                    value="name_asc",
                    clearable=False,
                    style={"minWidth": "220px"},
                ),

                html.Div("Rows per page", className="text-muted small mt-2"),
                dcc.Dropdown(
                    id="rows-per-page",
                    options=[{"label": str(n), "value": n} for n in (100, 150, 200, 300, 400)] + [{"label": "All", "value": 999999}],
                    value=300,
                    clearable=False,
                    style={"width": "120px"},
                ),

                html.Div(id="kpi-container", className="mt-3"),
            ]),
            style={"margin": "0"},
        )


class KpiStrip:
    """Uniform KPI cards; exactly 3 per row via CSS grid."""
    def __init__(self, max_width: Optional[int] = None) -> None:
        self.max_width = max_width

    def _kpi_card(self, label: str, value: int):
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(label, className="text-muted small"),
                    html.H5(f"{int(value)}", className="mb-0 mt-1"),
                ]
            ),
            className="shadow-sm",
        )

    def render(self, tab: str, vocab: List[str], counts: Dict[str, int], per_row: int = 3):
        cards = [self._kpi_card(s, int(counts.get(s, 0) or 0)) for s in vocab]
        # IMPORTANT: do NOT set id="kpi-container" here; the layout already has that id
        return html.Div(
            cards,
            className="kpi-strip",
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(3, minmax(100px, 1fr))",  # exactly 3 per row
                "gap": "12px",
                "maxWidth":  "100%",
                "text-align"    : "center",
                "marginTop": "8px",
                "marginBottom": "8px",
            },
        )