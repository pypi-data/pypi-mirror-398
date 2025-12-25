# run_dashboard.py  (new helper script)

from qsg.app.dashboard.config import load_config
from qsg.app.dashboard.dashboard import DashboardHost
from qsg.app.dashboard.caching import configure_cache

import dash
import dash_bootstrap_components as dbc


def create_app():
    cfg = load_config()

    dash_app = dash.Dash(
        "dataset-dashboard",
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=False,
    )
    host = DashboardHost(dash_app, cfg)
    dash_app.layout = host.layout

    configure_cache(dash_app.server, cfg)

    # Register callbacks AFTER host / layout to avoid circular imports
    from qsg.app.dashboard.inject import register_callbacks

    register_callbacks(dash_app, cfg, host)
    return dash_app


if __name__ == "__main__":
    app = create_app()
    # threaded=True allows many concurrent requests;
    # debug=False and use_reloader=False for performance & stability.
    app.run_server(
        host="0.0.0.0",
        port=8050,
        debug=False,
        use_reloader=False,
        threaded=True,
    )