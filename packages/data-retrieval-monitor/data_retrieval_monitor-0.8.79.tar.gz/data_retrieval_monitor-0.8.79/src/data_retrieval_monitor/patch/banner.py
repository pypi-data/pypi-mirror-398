# qsg/app/dashboard/components/banner.py

from __future__ import annotations

from typing import Iterable, List, Optional

from dash import dcc, html


class BannerComponent:
    """
    Top-of-page banner showing the app title, 'now' indicator, and any warnings.

    - render(title)                    -> backwards compatible (no warnings)
    - render(title, warnings=iterable) -> warns on the right-hand side
    """

    def __init__(self, gutter_ch: int = 10) -> None:
        self.gutter_ch = gutter_ch

    def render(
        self,
        title: str,
        warnings: Optional[Iterable[str]] = None,
    ):
        """
        Build the banner row.

        Parameters
        ----------
        title:
            Title text for the app.
        warnings:
            Optional iterable of warning strings; if provided, they are joined
            with " | " and shown in red on the right-hand side.
        """
        pad = f"{self.gutter_ch}ch"
        warnings = list(warnings or [])

        # Optional warnings text
        warning_node = None
        if warnings:
            warning_node = html.Div(
                " | ".join(str(w) for w in warnings),
                id="import-warnings",
                className="text-danger small ms-3",
                style={"whiteSpace": "nowrap"},
            )

        # Right-hand side: now indicator + optional warnings
        right_children: List = [
            html.Div(id="now-indicator", className="text-muted"),
        ]
        if warning_node is not None:
            right_children.append(warning_node)

        # NOTE: include copy-dummy so it's present in the *initial* layout
        return html.Div(
            [
                html.Div(title, className="h2 fw-bold"),
                html.Div(
                    right_children,
                    style={
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "center",
                        "justifyContent": "flex-end",
                        "gap": "12px",
                    },
                ),
                dcc.Store(id="copy-dummy"),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "width": "100%",
                "paddingLeft": pad,
                "paddingRight": pad,
                "paddingTop": "8px",
                "paddingBottom": "8px",
            },
        )