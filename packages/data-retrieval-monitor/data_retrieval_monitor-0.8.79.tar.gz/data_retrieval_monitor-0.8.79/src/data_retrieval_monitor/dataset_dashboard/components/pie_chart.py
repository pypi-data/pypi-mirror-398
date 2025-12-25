from typing import Dict, List, Optional
from ..constants import status_order_for_tab, rgb_for_tab

class PieChartComponent:
    def figure(self, tab: str, title_text: str, counts: Dict[str,int], labels_order: Optional[List[str]] = None):
        labels = labels_order or status_order_for_tab(tab)
        colors_map = rgb_for_tab(tab)
        vals = [int(counts.get(s, 0) or 0) for s in labels]
        total = sum(vals)

        def color_for(name: str) -> str:
            r,g,b = colors_map.get(name, colors_map.get("other", (153,153,153)))
            return f"rgba({r},{g},{b},{0.9 if counts.get(name,0)>0 else 0.12})"

        colors = [color_for(s) for s in labels]
        texttempl = [("" if counts.get(s,0)==0 else "%{label} %{percent}") for s in labels]
        hover = "%{label}: %{value}<extra></extra>"

        trace = {
            "type": "pie",
            "labels": labels,
            "values": [v if total>0 else 1 for v in vals],
            "hole": 0.45,
            "marker": {"colors": colors, "line": {"width": 0}},
            "texttemplate": texttempl,
            "textposition": "outside",
            "hovertemplate": hover,
            "showlegend": True,
        }
        return {
            "data": [trace],
            "layout": {
                "annotations": [{
                    "text": title_text, "xref": "paper", "yref": "paper",
                    "x": 0.5, "y": 1.2, "xanchor": "center", "yanchor": "top",
                    "showarrow": False, "font": {"size": 13}
                }],
                "margin": {"l": 10, "r": 10, "t": 26, "b": 10},
                "legend": {"orientation": "h"},
                "title": {"text": ""}
            }
        }
