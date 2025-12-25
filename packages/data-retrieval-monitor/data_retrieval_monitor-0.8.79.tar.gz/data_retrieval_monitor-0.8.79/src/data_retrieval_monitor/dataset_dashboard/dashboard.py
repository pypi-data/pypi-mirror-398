from dash import html, dcc
import dash_bootstrap_components as dbc
from .config import AppConfig
from .services.store import StoreService
from .services.logs import LogLinker, register_log_routes
from .components import BannerComponent, ControlsComponent, KpiStrip, PieChartComponent, TableComponent
from .components.html import PageLayout

class DashboardHost:
    def __init__(self, app, cfg: AppConfig):
        self.app = app
        self.cfg = cfg

        self.store = StoreService(cfg.store_backend, cfg.store_path, cfg.default_owner, "live")
        self.log_linker = LogLinker(cfg.log_root)

        self.banner = BannerComponent()
        self.controls = ControlsComponent()
        self.kpis = KpiStrip(cfg.max_kpi_width)
        self.pies = PieChartComponent()
        self.table = TableComponent(self.log_linker, clipboard_fallback_open=cfg.clipboard_fallback_open)

        register_log_routes(app.server, self.log_linker)

        tabs = dcc.Tabs(
            id="main-tabs",
            value="all",
            children=[
                dcc.Tab(label="All",        value="all",        style={"width":"20%", "textAlign":"center"}, selected_style={"width":"20%", "textAlign":"center"}),
                dcc.Tab(label="Data",       value="data",       style={"width":"20%", "textAlign":"center"}, selected_style={"width":"20%", "textAlign":"center"}),
                dcc.Tab(label="Features",   value="features",   style={"width":"20%", "textAlign":"center"}, selected_style={"width":"20%", "textAlign":"center"}),
                dcc.Tab(label="Alphas",     value="alphas",     style={"width":"20%", "textAlign":"center"}, selected_style={"width":"20%", "textAlign":"center"}),
                dcc.Tab(label="Strategies", value="strategies", style={"width":"20%", "textAlign":"center"}, selected_style={"width":"20%", "textAlign":"center"}),      
            ],
            style={"width":"1000px"},
            className="mb-2",
        )

        page_layout = PageLayout(cfg, self.controls, self.kpis, self.pies)

        self.layout = html.Div([
            dcc.Location(id="url", refresh=False),
            self.banner.render(cfg.app_title),
            tabs,
            page_layout.build(),
            dcc.Store(id="table-page", data=0),
        ],
        className="app-zoom"
        )