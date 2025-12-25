# multi_dashboard.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

@dataclass
class TabSpec:
    title: str
    file_path: str  # path to an already-written HTML file

class TabbedDashboard:
    """
    Simple multi-page tabs wrapper that iframes each dashboard.
    Sends a 'recalc_tables' postMessage to the active iframe after tab change
    so right-pane sliders/tables size correctly.
    """
    def __init__(self, tabs: List[TabSpec], title: str = "Analytics", output_dir: str = "output/tabs") -> None:
        self.tabs = tabs
        self.title = title
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.html_path = os.path.join(self.output_dir, "index.html")
        self._write_html()

    def _write_html(self) -> None:
        # relative src paths
        items = []
        for i, tab in enumerate(self.tabs):
            rel = os.path.relpath(tab.file_path, self.output_dir)
            items.append((tab.title, rel, f"tab{i}"))

        css = r"""
<style>
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; background:#fff; }
.titlebar { padding: 12px 16px 4px 16px; }
.titlebar h1 { margin:0; font-size:18px; color:#222; }

.tabs { display:flex; gap:8px; padding: 8px 12px 0 12px; border-bottom:1px solid #e8e8e8; }
.tab { padding: 8px 12px; border:1px solid #e8e8e8; border-bottom:none; border-radius:6px 6px 0 0; background:#f9f9f9; cursor:pointer; font-size:13px; color:#333; }
.tab.active { background:#fff; font-weight:600; }

.content { position: absolute; top: 74px; left:0; right:0; bottom:0; }
.frame { position:absolute; inset:0; width:100%; height:100%; border:0; display:none; }
.frame.active { display:block; }
</style>
"""
        js = r"""
<script>
(function(){
  let active = 0;
  const frames = [];
  function show(i){
    active = i;
    document.querySelectorAll('.tab').forEach((t, idx) => t.classList.toggle('active', idx===i));
    document.querySelectorAll('.frame').forEach((f, idx) => {
      const show = idx===i;
      f.classList.toggle('active', show);
      if (show) {
        try { f.contentWindow.postMessage('recalc_tables', '*'); } catch(e){}
      }
    });
  }
  window.addEventListener('DOMContentLoaded', () => {
    // attach
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach((t, i) => t.addEventListener('click', () => show(i)));
    show(0);
  });
})();
</script>
"""
        tabs_html = "".join([f'<div class="tab" id="{tid}">{title}</div>' for title, _, tid in items])
        frames_html = "".join([f'<iframe class="frame" src="{src}" title="{title}"></iframe>' for title, src, _ in items])

        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{self.title}</title>
{css}
</head>
<body>
<div class="titlebar"><h1>{self.title}</h1></div>
<div class="tabs">
  {tabs_html}
</div>
<div class="content">
  {frames_html}
</div>
{js}
</body>
</html>
"""
        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Tabbed dashboard written to: {self.html_path}")