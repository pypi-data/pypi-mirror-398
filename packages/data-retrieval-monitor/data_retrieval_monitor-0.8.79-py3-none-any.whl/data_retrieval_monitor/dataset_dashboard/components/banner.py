from dash import html, dcc

class BannerComponent:
    def __init__(self, gutter_ch: int = 10):
        self.gutter_ch = gutter_ch

    def render(self, title: str):
        pad = f"{self.gutter_ch}ch"
        # NOTE: include copy-dummy here so it's present in the *initial* layout
        return html.Div(
            [
                html.Div(title, className="h2 fw-bold"),
                html.Div(id="now-indicator", className="text-muted"),
                dcc.Store(id="copy-dummy"),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "width": "100%",
                "paddingLeft": pad,
                "paddingRight": pad,
            },
        )