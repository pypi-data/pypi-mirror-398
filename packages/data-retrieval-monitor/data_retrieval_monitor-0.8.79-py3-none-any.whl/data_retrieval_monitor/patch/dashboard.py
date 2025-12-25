from .library import get_import_failures

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
        self.table = TableComponent(self.log_linker, cfg.clipboard_fallback_open)

        register_log_routes(app.server, self.log_linker)

        # Tabs definition (unchanged) ...
        tabs = dcc.Tabs(
            id="main-tabs",
            value="all",
            children=[...],
            style={"width": "1000px"},
            className="mb-2",
        )

        page_layout = PageLayout(cfg, self.controls, self.kpis, self.pies)

        # NEW: import failure warnings
        failures = get_import_failures()
        warnings_bar = None
        if failures:
            warnings_bar = html.Div(
                [
                    html.Div(
                        msg,
                        className="text-danger small",
                        style={"marginRight": "1rem"},
                    )
                    for _tab, msg in failures.items()
                ],
                style={
                    "paddingLeft": "10ch",
                    "paddingRight": "10ch",
                    "paddingTop": "4px",
                    "paddingBottom": "4px",
                },
            )

        children = [
            dcc.Location(id="url", refresh=False),
            self.banner.render(cfg.app_title),
        ]
        if warnings_bar is not None:
            children.append(warnings_bar)
        children.extend(
            [
                tabs,
                page_layout.build(),
                dcc.Store(id="table-page", data=0),
            ]
        )

        self.layout = html.Div(
            children,
            className="app-zoom",
        )