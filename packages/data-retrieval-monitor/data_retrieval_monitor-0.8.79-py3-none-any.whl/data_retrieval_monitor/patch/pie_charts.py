# qsg/app/dashboard/components/pie_chart.py

from __future__ import annotations

from typing import Dict, List, Optional

from qsg.app.dashboard.constants import rgb_for_tab, status_order_for_tab


class PieChartComponent:
    """
    Build Plotly pie-chart figures with consistent per-status colors.

    - No on-slice text (no "X – 0%"), details are only via hover + legend.
    - If total == 0, we return an *empty* figure (no fake 1-slice pies).
    """

    def figure(
        self,
        tab: str,
        title_text: str,
        counts: Dict[str, int],
        labels_order: Optional[List[str]] = None,
    ) -> Dict:
        # Decide which labels to show
        preferred = status_order_for_tab(tab)
        if labels_order:
            labels = [s for s in labels_order if (s in counts) or (s in preferred)]
        else:
            labels = preferred + [s for s in counts.keys() if s not in preferred]

        palette = rgb_for_tab(tab)

        def color_for(label: str) -> str:
            r, g, b = palette.get(label, palette.get("other", (153, 153, 153)))
            return f"rgb({r},{g},{b})"

        values = [int(counts.get(label, 0)) for label in labels]
        total = sum(values)

        # If no data at all (e.g. alphas/strategies with 0 pipelines), return an empty figure.
        if total == 0:
            layout = {
                "annotations": [
                    {
                        "text": title_text,
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 1.0,
                        "showarrow": False,
                        "font": {"size": 13},
                    }
                ],
                "margin": {"t": 18, "l": 10, "r": 26, "b": 10},
                "legend": {"orientation": "h"},
                "title": {"text": ""},
            }
            return {"data": [], "layout": layout}

        colors = [color_for(label) for label in labels]

        # Hover only – no text on the slices themselves.
        hovertemplate = "%{label}: %{value} (%{percent:.1%})<extra></extra>"

        trace = {
            "type": "pie",
            "labels": labels,
            "values": values,
            "hole": 0.45,
            "marker": {"colors": colors, "line": {"width": 0}},
            "hovertemplate": hovertemplate,
            "showlegend": True,
            "textinfo": "none",  # critical: no "x – 0%" clutter
        }

        layout = {
            "annotations": [
                {
                    "text": title_text,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 1.15,
                    "showarrow": False,
                    "font": {"size": 13},
                }
            ],
            "margin": {"t": 18, "l": 10, "r": 26, "b": 10},
            "legend": {"orientation": "h"},
            "title": {"text": ""},
        }

        return {"data": [trace], "layout": layout}