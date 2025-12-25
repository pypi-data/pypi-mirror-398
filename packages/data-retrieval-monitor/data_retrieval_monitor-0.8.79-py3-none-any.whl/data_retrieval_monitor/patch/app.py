# run_dashboard.py (or whatever your entrypoint is)

import dash
import dash_bootstrap_components as dbc
from flask import request

from qsg.app.dashboard.config import load_config
from qsg.app.dashboard.dashboard import DashboardHost


def create_app():
    cfg = load_config()

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=False,
    )
    host = DashboardHost(app, cfg)
    app.layout = host.layout

    # <-- HERE is where you hook the after_request
    @app.server.after_request
    def add_security_headers(response):
        # Ensure charset=utf-8
        if response.mimetype == "text/html":
            response.headers["Content-Type"] = "text/html; charset=utf-8"

        # Cache control:
        # - HTML: no-store (so the main page always refreshes)
        # - Static assets: long cache with immutable
        if response.mimetype and response.mimetype.startswith("text/html"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
        else:
            # static / other: let browser cache aggressively
            response.headers.setdefault(
                "Cache-Control",
                "public, max-age=31536000, immutable",
            )

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Use CSP frame-ancestors instead of X-Frame-Options
        csp = response.headers.get("Content-Security-Policy", "")
        if "frame-ancestors" not in csp:
            # basic example; tune for your deployment
            extra = "frame-ancestors 'none';"
            response.headers["Content-Security-Policy"] = (csp + " " + extra).strip()

        # Remove or simplify legacy / noisy headers
        for h in ("X-XSS-Protection", "X-Frame-Options", "Expires"):
            response.headers.pop(h, None)

        # Optional: simplify Server header
        if "Server" in response.headers:
            response.headers["Server"] = "dash-server"

        return response

    # Also set a custom index string so <html> has lang="en"
    app.index_string = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
      </head>
      <body>
        {%app_entry%}
        <footer>
          {%config%}
          {%scripts%}
          {%renderer%}
        </footer>
      </body>
    </html>
    """

    return app


if __name__ == "__main__":
    app = create_app()
    app.run_server(
        host="0.0.0.0",
        port=8050,
        debug=False,
        use_reloader=False,
        threaded=True,    # let Flask handle multiple concurrent requests
    )