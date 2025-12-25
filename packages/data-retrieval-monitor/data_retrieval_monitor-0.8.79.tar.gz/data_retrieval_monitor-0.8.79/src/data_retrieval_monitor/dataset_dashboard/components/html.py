from dash import html, dcc
import dash_bootstrap_components as dbc
from ..utils import px

class BannerComponent:
    def render(self, title: str):
        return html.Div([
            html.H2(title, className="fw-bold mb-1"),
            html.Div(id="now-indicator", className="text-muted small")
        ], style={"paddingTop":"8px","paddingBottom":"2px"})

class PageLayout:
    def __init__(self, cfg, controls_component, kpi_strip, pie_component):
        self.cfg = cfg
        self.controls = controls_component
        self.kpis = kpi_strip
        self.pies = pie_component

    def build(self):
        controls = self.controls.render(self.cfg)

        def pie_holder(_id, title, max_graph_width: int):
            return dcc.Graph(
                id=_id,
                figure={"layout": {"title": {"text": title}}},
                style={"height": "320px", "maxWidth": px(max_graph_width), "margin": "0"},
            )

        pies_block = html.Div(
            [
                pie_holder("pie-overview", "Overview", self.cfg.max_graph_width),
                pie_holder("pie-archive", "Archive", self.cfg.max_graph_width),
                pie_holder("pie-stage", "Stage", self.cfg.max_graph_width),
                pie_holder("pie-enrich", "Enrich", self.cfg.max_graph_width),
                pie_holder("pie-consolidate", "Consolidate", self.cfg.max_graph_width),
            ],
            className="mb-2",
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "paddingBottom": "8px"},
        )

        left = html.Div(
            [controls, pies_block],
            style={
                "width": px(self.cfg.max_left_width),
                "minWidth": px(self.cfg.max_left_width),
                "maxWidth": px(self.cfg.max_left_width),
                "flex": "0 0 auto",
            },
        )

        right = html.Div(
            [
                html.Div(
                    [
                        html.H4(id="table-title", className="fw-semibold", style={"margin": "0", "whiteSpace": "nowrap"}),
                        html.Div(id="table-container", style={"flex": "1 1 auto", "minWidth": "0"}),
                    ],
                    style={"display": "flex", "alignItems": "flex-start", "gap": "8px", "width": "auto"},
                ),
                dbc.Pagination(
                    id="table-pager",
                    min_value=1,
                    max_value=1,
                    active_page=1,
                    first_last=True,
                    previous_next=True,
                    size="sm",
                    className="mt-2",
                    style={"display": "none"},  # Initially hidden
                ),
            ],
            style={"flex": "1 1 auto", "minWidth": "0"},
        )

        page = html.Div(
            [
                left,
                right,
                # UI refresh interval (keep your existing behavior)
                dcc.Interval(id="interval", interval=1500, n_intervals=0),

                # NEW: ingestion interval (driven by cfg.refresh_ms)
                dcc.Interval(
                    id="ingest-interval",
                    interval=int(getattr(self.cfg, "refresh_ms", 30000) or 30000),
                    n_intervals=0,
                ),
                # Hidden sentinel so we can see ticks in logs and to avoid "no outputs" errors
                html.Div(id="ingest-sentinel", style={"display": "none"}),
            ],
            style={
                "display": "flex",
                "flexWrap": "nowrap",
                "alignItems": "flex-start",
                "gap": "16px",
                "width": "100%",
                "margin": "0 auto",
                "paddingLeft": "10ch",
                "paddingRight": "10ch",
                "marginTop": "24px",
            },
        )
        return page