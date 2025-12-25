# core_tearsheet.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt


# -----------------------------------------------------------------------------
# Small filesystem helper
# -----------------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# -----------------------------------------------------------------------------
# Base class
# -----------------------------------------------------------------------------
@dataclass
class TearsheetMeta:
    title: str
    output_dir: str
    fig_dir: str
    html_path: str
    manifest_path: str


class TearsheetBase:
    """
    Shared scaffold for our dashboards.

    Responsibilities:
      - directories and file paths
      - shared Pandas (render only) helpers
      - figure saving helper
      - shared HTML/CSS/JS writer (left figures + right tables + resizable slider)
      - manifest writer (JSON)
    """
    def __init__(self, *, title: str, output_dir: str) -> None:
        self.title = title
        self.output_dir = output_dir
        _ensure_dir(self.output_dir)
        self.fig_dir = os.path.join(self.output_dir, "figures")
        _ensure_dir(self.fig_dir)
        self.html_path = os.path.join(self.output_dir, "dashboard.html")
        self.manifest_path = os.path.join(self.output_dir, "available_manifest.json")

    # -------------------------------------------------------------------------
    # Rendering helpers (Pandas conversion ONLY for rendering)
    # -------------------------------------------------------------------------
    @staticmethod
    def _pd_from_pl_df(df: pl.DataFrame, date_col: Optional[str] = None, index_from_date: bool = False) -> pd.DataFrame:
        """
        Convert Polars (eager) -> Pandas.
        If index_from_date: set DatetimeIndex from date_col and drop the column.
        Strictly for rendering; avoid compute use of pandas.
        """
        pdf = df.to_pandas()
        if index_from_date and date_col and (date_col in pdf.columns):
            dt = pd.to_datetime(pdf[date_col], errors="coerce")
            try:
                dt = dt.dt.tz_localize(None)
            except Exception:
                dt = pd.DatetimeIndex(dt).tz_localize(None)
            pdf = pdf.drop(columns=[date_col])
            pdf.index = pd.DatetimeIndex(dt)
            pdf.sort_index(inplace=True)
        return pdf

    @staticmethod
    def _pd_series_from_pl_two_cols(df: pl.DataFrame, date_col: str, val_col: str, name: Optional[str] = None) -> pd.Series:
        pdf = TearsheetBase._pd_from_pl_df(df.select([pl.col(date_col), pl.col(val_col)]), date_col=date_col, index_from_date=True)
        s = pdf.iloc[:, 0]
        s.name = str(name or val_col)
        return s

    # -------------------------------------------------------------------------
    # Figure save helper (matplotlib)
    # -------------------------------------------------------------------------
    def _save_fig(self, fig: Optional[plt.Figure], filename: str) -> Optional[str]:
        if fig is None:
            return None
        path = os.path.join(self.fig_dir, filename)
        fig.savefig(path, dpi=144, bbox_inches="tight")
        try:
            plt.close(fig)
        except Exception:
            pass
        return path

    # -------------------------------------------------------------------------
    # Shared HTML writer (same layout for all dashboards)
    # -------------------------------------------------------------------------
    def write_html(self, *, figures_html: str, tables_html: str, subtitle_html: str = "") -> None:
        """
        Write the full HTML page using the standard two-pane layout:
          - left: figures (auto grid)
          - right: tables (resizable wrapper with invisible handle; width snaps to content)
        The caller passes the raw HTML strings for figures and tables.
        """
        css = r"""
<style>
:root {
  --gutter: 10px;
  --left-col: 40%;
  --right-col: 60%;
  --tables-w: 640px;
  --handle-left: var(--tables-w);
}
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; background:#fff; }

.page { padding: 14px; }
.titlebar { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }
.titlebar h1 { margin:0; font-size:20px; }
.titlebar .sub { color:#555; font-size:13px; }
.meta { margin: 4px 0 8px 0; color:#666; font-size:12px; }

/* --- panes + splitters --- */
.outer-split{display:grid;grid-template-columns:var(--left-col) var(--gutter) var(--right-col);width:100%;height:calc(100vh - 110px);min-height:540px}
.left-pane,.right-pane{overflow:auto}

/* Left gutter: invisible until hover anywhere on the split */
.gutter{background:transparent;cursor:col-resize;width:var(--gutter);opacity:0.2;transition:opacity .12s ease}
.outer-split:hover .gutter{opacity:.28}
.gutter:hover{opacity:.32}

/* Tables wrapper + right handle */
.tables-wrap {
  position: relative;
  height: 100%;
  overflow: hidden;
}
.tables-content {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: calc(var(--tables-w) + 48px);
  overflow: auto;
  padding: 4px 36px 14px 12px; /* right padding requested */
  background: transparent;
}
.right-handle {
  position: absolute;
  top: 0; bottom: 0;
  left: var(--handle-left);
  width: 10px;
  cursor: col-resize;
  background: rgba(0,0,0,0.03);
  z-index: 5;
  opacity: 0.25; /* always slightly visible */
  transition: opacity .12s ease;
}
.tables-wrap:hover .right-handle { opacity: .35; }
body.dragging-right .right-handle { background: rgba(0,0,0,0.08); opacity: .6; }

/* Figures */
.fig-row { margin: 6px 8px 18px 2px; }
.fig-title { font-size:14px; font-weight:600; margin: 4px 2px 8px 2px; color:#333; }
.fig-note { font-size:12px; color:#555; margin: 0 2px 8px 2px; line-height:1.4; }
.fig-grid { display: grid; gap: 10px; }
.thumb { border: 1px solid #e4e4e4; border-radius: 6px; overflow: hidden; background:#fff; padding: 6px; }
.thumb.placeholder { visibility: hidden; }
.thumb .fig-header { font-size: 12px; font-weight: 600; margin: 0 0 6px 0; color:#333; text-align:left; }
.thumb img { display:block; width:100%; height:auto; cursor: zoom-in; }

/* Base table style */
.table-block { margin: 8px 4px 18px 4px; }
.table-block h3 { font-size:14px; margin: 0 0 6px 0; color:#222; }
.table-block table { border-collapse: collapse; background:#fff; width: auto; table-layout: auto; font-size:12px; }
.table-block thead th { background:#f6f6f6; color:#333; padding: 6px 10px; border: none; text-align: right; font-weight:600; }
.table-block thead th:first-child { text-align: left; }
.table-block tbody td { padding: 6px 10px; border: none; text-align: right; }
.table-block tbody td:first-child { text-align: left; }

/* Grouped metrics table (sticky first column) */
.metrics-grouped { border-collapse: collapse; background:#fff; width: auto; table-layout: auto; font-size:12px; }
.metrics-grouped thead th { background:#f6f6f6; font-weight:600; padding:6px 10px; border:none; text-align:right; font-size:12px; }
.metrics-grouped thead th.sticky-col { text-align:left; position: sticky; left: 0; background:#f6f6f6; z-index:2; }
.metrics-grouped tbody td { padding:6px 10px; border:none; font-size:12px; }
.metrics-grouped td.mname.sticky-col { position: sticky; left: 0; background:#fff; z-index:1; color:#333; font-weight:500; }
.metrics-grouped tr.sep td { border-bottom:1px solid #d0d0d0; height:6px; padding:0; }
.metrics-grouped tr.glabel td.gtitle { color:#222; font-size:13px; font-weight:700; letter-spacing: .2px; padding: 6px 4px 4px 4px; border-top: 1px solid #ddd; }

/* Controlled tables (right pane slider respects width) */
.table-block[data-group="controlled"] table { width: var(--tables-w); white-space: nowrap; }

/* Zoom modal */
.modal { position: fixed; inset: 0; display:none; align-items:center; justify-content:center; background: rgba(0,0,0,0.76); z-index: 1000; }
.modal img { max-width: 98vw; max-height: 96vh; display:block; box-shadow:0 10px 26px rgba(0,0,0,0.45); border-radius: 10px; }
.modal.show { display:flex; }
</style>
"""

        js = r"""
<script>
(function(){
  const root   = document.documentElement;
  const outer  = document.querySelector('.outer-split');
  const gutter = document.getElementById('left-gutter');
  const wrap   = document.getElementById('tables-wrap');
  const handle = document.getElementById('right-handle');

  function cssPx(name, fallback=0){
    const v = getComputedStyle(root).getPropertyValue(name).trim();
    if (!v) return fallback;
    return v.endsWith('px') ? parseFloat(v) : (parseFloat(v) || fallback);
  }
  function setVarPx(name, px){ root.style.setProperty(name, px + 'px'); }
  function setLeftRightPx(leftPx, rightPx){
    const total = leftPx + cssPx('--gutter',10) + rightPx;
    root.style.setProperty('--left-col',  (leftPx/total*100) + '%');
    root.style.setProperty('--right-col', (rightPx/total*100) + '%');
  }
  function clampTablesW(px){
    const r = wrap.getBoundingClientRect();
    const minW = 420;
    const maxW = Math.max(minW, r.width - 42);
    return Math.max(minW, Math.min(maxW, px));
  }
  function positionHandle(){
    const r  = wrap.getBoundingClientRect();
    const tw = cssPx('--tables-w', 640);
    const available = Math.max(0, r.width - 10);
    const left = Math.max(0, Math.min(available, tw));
    setVarPx('--handle-left', left);
  }
  function initTablesWidthToContent(){
    let maxW = 480;
    document.querySelectorAll('.table-block[data-group="controlled"] table').forEach(t => {
      const wrapRect = wrap.getBoundingClientRect();
      const wrapLimit = Math.max(420, wrapRect.width - 24);
      const needed = Math.max(t.scrollWidth, t.offsetWidth, 420);
      maxW = Math.min(Math.max(maxW, needed), wrapLimit);
    });
    setVarPx('--tables-w', maxW);
    positionHandle();
  }

  // resize split
  let dragL=false;
  if (gutter) {
    gutter.addEventListener('mousedown', e => { dragL=true; e.preventDefault(); document.body.style.userSelect='none'; });
    window.addEventListener('mousemove', e => {
      if (!dragL) return;
      const rect = outer.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const minL = 260, maxL = rect.width - 360;
      const clamped = Math.max(minL, Math.min(maxL, x));
      const leftPx = clamped;
      const rightPx = rect.width - clamped - cssPx('--gutter',10);
      setLeftRightPx(leftPx, rightPx);
      positionHandle();
    });
    window.addEventListener('mouseup', () => { if (dragL){ dragL=false; document.body.style.userSelect=''; } });
  }

  // right slider
  let dragR=false;
  if (handle) {
    handle.addEventListener('mousedown', e => { dragR=true; e.preventDefault(); document.body.style.userSelect='none'; document.body.classList.add('dragging-right'); });
    window.addEventListener('mousemove', e => {
      if (!dragR) return;
      const r = wrap.getBoundingClientRect();
      let x = e.clientX - r.left;
      x = clampTablesW(x);
      setVarPx('--tables-w', x);
      positionHandle();
    });
    window.addEventListener('mouseup', () => { if (dragR){ dragR=false; document.body.style.userSelect=''; document.body.classList.remove('dragging-right'); } });
  }

  window.addEventListener('load', () => { initTablesWidthToContent(); });
  window.addEventListener('resize', () => { positionHandle(); });

  // Zoom modal
  const modal = document.getElementById('zoom-modal');
  const modalImg = document.getElementById('zoom-image');
  document.querySelectorAll('img[data-zoom="1"]').forEach(img => {
    img.addEventListener('click', () => { modalImg.src = img.src; modal.classList.add('show'); });
  });
  if (modal) {
    modal.addEventListener('click', (e) => { if (e.target === modal || e.target.id === 'zoom-image') modal.classList.remove('show'); });
    window.addEventListener('keydown', (e) => { if (e.key === 'Escape') modal.classList.remove('show'); });
  }

  // support TabbedDashboard postMessage to recalc table widths after tab switch
  window.addEventListener('message', (e) => {
    if (e && e.data === 'recalc_tables') {
      try { initTablesWidthToContent(); positionHandle(); } catch(err){}
    }
  });
})();
</script>
"""

        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{self.title}</title>
{css}
</head>
<body>
<div class="page">
  <div class="titlebar">
    <h1>{self.title}</h1>
    {'<div class="sub">'+subtitle_html+'</div>' if subtitle_html else ''}
  </div>

  <div class="outer-split">
    <div class="left-pane">
      {figures_html}
    </div>
    <div class="gutter" id="left-gutter" title="Drag to resize"></div>
    <div class="right-pane">
      <div class="tables-wrap" id="tables-wrap">
        <div class="tables-content" id="tables-content">
          {tables_html}
        </div>
        <div class="right-handle" id="right-handle" title="Drag to resize"></div>
      </div>
    </div>
  </div>
</div>

<div class="modal" id="zoom-modal">
  <img id="zoom-image" src="" alt="Zoom"/>
</div>

{js}
</body>
</html>
"""
        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Dashboard written to: {self.html_path}")

    # -------------------------------------------------------------------------
    # Manifest writer (optional)
    # -------------------------------------------------------------------------
    def write_manifest(self, payload: Dict[str, Any]) -> None:
        import json
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"[manifest] wrote: {self.manifest_path}")
