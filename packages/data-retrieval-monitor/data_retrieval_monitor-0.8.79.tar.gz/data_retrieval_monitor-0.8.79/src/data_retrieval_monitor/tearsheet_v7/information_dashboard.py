from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns

from prediction_metrics import (
    ic_grid_long,
    prediction_summary_metrics,
)


# -----------------------------
# Manifest
# -----------------------------
@dataclass
class InformationManifest:
    factors: Optional[List[str]] = None           # which factors (columns) to show
    lags: Optional[List[int]] = None              # grid lags to compute
    horizons: Optional[List[int]] = None         # grid horizons to compute
    # preferred single (lag, horizon) for summary row values like MAE/MSE/Sign/N:
    summary_lag: Optional[int] = None
    summary_horizon: Optional[int] = None
    # which tables should obey the right slider width
    tables_controlled_by_slider: Optional[List[str]] = None
    strict_groups: bool = True
    data_overrides: Optional[Dict[str, Union[str, Callable[[Any], Any]]]] = None
    custom_figures: Optional[List["CustomFigureSpec"]] = None
    custom_tables: Optional[List["CustomTableSpec"]] = None
    figure_data_overrides: Optional[Dict[str, str]] = None
    table_data_overrides: Optional[Dict[str, str]] = None
    include_core_figures: bool = True
    include_core_tables: bool = True
    figures: Optional[List[str]] = None
    tables: Optional[List[str]] = None


@dataclass
class CustomFigureSpec:
    key: str
    data_key: Optional[str]
    builder: Callable[[Any, "PredictionDashboard"], Optional[List[Tuple[str, str]]]]
    title: Optional[str] = None
    description: Optional[str] = None
    output_prefix: Optional[str] = None


@dataclass
class CustomTableSpec:
    key: str
    data_key: Optional[str]
    builder: Callable[[Any, "PredictionDashboard"], Optional[str]]
    title: Optional[str] = None
    controlled: bool = True


# -----------------------------
# Dashboard
# -----------------------------
class InformationTearsheet:
    """
    Left: figures (IC / t / Sign heatmaps per factor)
    Right: tables (Key Prediction Metrics + IC Diagnostics per factor)
    All compute in Polars; Pandas used only for HTML render.
    """
    def __init__(
        self,
        *,
        preds_lf: Optional[pl.LazyFrame | pl.DataFrame] = None,    # [date, factor1, factor2, ...]
        target_lf: Optional[pl.LazyFrame | pl.DataFrame] = None,   # [date, factor1, factor2, ...] (targets)
        title: str = "Prediction Tearsheet",
        output_dir: str = "output/prediction",
        manifest: Optional[InformationManifest] = None,
        data_source: Optional[Any] = None,
        figures: Optional[List[str]] = None,
        tables: Optional[List[str]] = None,
        data_overrides: Optional[Dict[str, Union[str, Callable[[Any], Any]]]] = None,
    ) -> None:
        self.title = title
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.fig_dir = os.path.join(self.output_dir, "figures")
        os.makedirs(self.fig_dir, exist_ok=True)
        self.html_path = os.path.join(self.output_dir, "dashboard.html")

        self.manifest = manifest or InformationManifest()
        if figures is not None:
            self.manifest.figures = figures
        if tables is not None:
            self.manifest.tables = tables
        if data_overrides:
            merged = dict(self.manifest.data_overrides or {})
            merged.update(data_overrides)
            self.manifest.data_overrides = merged
        self.tables_controlled = self.manifest.tables_controlled_by_slider or ["pred_metrics", "ic_diag"]
        self._custom_fig_counter = 0
        self.data_sources: Dict[str, Any] = {}
        resolved_data_overrides = self.manifest.data_overrides or {}
        self.include_core_figures = bool(self.manifest.include_core_figures)
        self.include_core_tables = bool(self.manifest.include_core_tables)
        self._figures_specified = self.manifest.figures is not None
        self._tables_specified = self.manifest.tables is not None
        self.enabled_core_figures = [f.lower() for f in (self.manifest.figures or ["ic", "t", "sign"])]
        self.enabled_core_tables = [t.lower() for t in (self.manifest.tables or ["pred_metrics", "ic_diag"])]

        base_source = data_source if data_source is not None else None
        if base_source is None and not self._is_polars_like(preds_lf):
            base_source = preds_lf
        if base_source is None and not self._is_polars_like(target_lf):
            base_source = target_lf
        self.source_obj = base_source

        preds_obj = preds_lf
        target_obj = target_lf

        if self.source_obj is not None and "preds" in resolved_data_overrides:
            preds_obj = self._resolve_data_spec(resolved_data_overrides["preds"], self.source_obj)
        elif not self._is_polars_like(preds_obj):
            if self.source_obj is None:
                raise TypeError("A data source object is required when preds_lf is not Polars-like.")
            preds_spec = data_overrides.get("preds")
            if preds_spec is None:
                for attr in ("preds_lf", "predictions", "preds"):
                    if hasattr(self.source_obj, attr):
                        preds_spec = attr
                        break
            if preds_spec is None:
                raise TypeError("Unable to infer predictions data; set manifest.data_overrides['preds'].")
            preds_obj = self._resolve_data_spec(preds_spec, self.source_obj)

        if self.source_obj is not None and "target" in resolved_data_overrides:
            target_obj = self._resolve_data_spec(resolved_data_overrides["target"], self.source_obj)
        elif not self._is_polars_like(target_obj):
            base = self.source_obj or target_obj
            if self.source_obj is None:
                raise TypeError("A data source object is required when target_lf is not Polars-like.")
            target_spec = data_overrides.get("target")
            if target_spec is None:
                for attr in ("target_lf", "targets", "target"):
                    if hasattr(self.source_obj, attr):
                        target_spec = attr
                        break
            if target_spec is None:
                raise TypeError("Unable to infer target data; set manifest.data_overrides['target'].")
            target_obj = self._resolve_data_spec(target_spec, self.source_obj)

        self.data_sources["preds"] = preds_obj
        self.data_sources["target"] = target_obj

        if preds_obj is None or target_obj is None:
            raise TypeError("Provide preds_lf/target_lf or configure manifest.data_overrides to resolve them from data_source.")

        if self.source_obj is not None:
            for key, spec in resolved_data_overrides.items():
                if key in ("preds", "target"):
                    continue
                try:
                    value = self._resolve_data_spec(spec, self.source_obj)
                except Exception as err:
                    print(f"[manifest:data_overrides] {key} failed: {err}")
                    continue
                self.data_sources[key] = value
            self.data_sources.setdefault("source", self.source_obj)

        # Normalize inputs
        self.P = self._to_lazy(preds_obj)
        self.T = self._to_lazy(target_obj)

        # Factor list
        self.factors = self.manifest.factors or self._infer_factors()

        # Grid to compute
        self.lags = self.manifest.lags or [0, 1, 5]
        self.horizons = self.manifest.horizons or [1, 5, 20]

        # Preferred cell for summary
        self.summary_lag = 0 if self.manifest.summary_lag is None else int(self.manifest.summary_lag)
        self.summary_horizon = 1 if self.manifest.summary_horizon is None else int(self.manifest.summary_horizon)

        # Compute once (Polars)
        self.grid_map: Dict[str, pl.DataFrame] = ic_grid_long(
            self.P, self.T, factors=self.factors, lags=self.lags, horizons=self.horizons
        )

        # Summary table (uses summary_lag/summary_horizon for single-cell stats;
        # IR still uses the full grid)
        self.summary = prediction_summary_metrics(
            self.P,
            self.T,
            factors=self.factors,
            lags=self.lags,
            horizons=self.horizons,
            lag=self.summary_lag,
            horizon=self.summary_horizon,
        )

        # Figures (save PNGs)
        self.fig_paths: Dict[str, Dict[str, str]] = {f: {} for f in self.factors}
        if self.include_core_figures:
            heatmap_specs = [
                ("IC", "ic", "IC Heatmap", "RdYlGn"),
                ("t", "t", "t-stat Heatmap", "PuOr"),
                ("sign", "sign", "SignAcc Heatmap", "viridis"),
            ]
            requested_figs = {label.lower() for label in self.enabled_core_figures}
            for factor in self.factors:
                df = self.grid_map.get(factor, pl.DataFrame())
                if df.is_empty():
                    continue
                for label, value_col, title_prefix, cmap in heatmap_specs:
                    if self._figures_specified and label.lower() not in requested_figs:
                        continue
                    path = self._render_heatmap_tile(df, value_col, factor, title_prefix, cmap)
                    if path:
                        self.fig_paths[factor][label] = path
        self.custom_fig_columns: List[Dict[str, Any]] = []
        if self.manifest.custom_figures:
            for spec in self.manifest.custom_figures:
                data_obj = self._manifest_data(spec.data_key)
                if data_obj is None:
                    continue
                try:
                    raw = spec.builder(data_obj, self)
                except Exception as err:
                    print(f"[custom_fig] {spec.key} failed: {err}")
                    continue
                tiles = self._normalize_custom_fig_output(raw, spec.key, prefix=spec.output_prefix or spec.key)
                if not tiles:
                    continue
                self.custom_fig_columns.append({
                    "title": spec.title or spec.key,
                    "description": spec.description,
                    "tiles": tiles,
                })

        # Tables HTML
        self.metrics_html = ""
        self.ic_diag_html_blocks: List[str] = []
        table_whitelist = {label.lower() for label in self.enabled_core_tables}
        show_metrics = self.include_core_tables and (
            ("pred_metrics" in table_whitelist) or (not self._tables_specified and not table_whitelist)
        )
        show_diag = self.include_core_tables and (
            ("ic_diag" in table_whitelist) or (not self._tables_specified and not table_whitelist)
        )
        if show_metrics:
            self.metrics_html = self._render_metrics_grouped(self.summary, [
                {"Prediction": ["IC", "t-stat", "R²", "IR (grid)"]},
                {"Errors": ["MAE", "MSE"]},
                {"Other": ["Sign Acc.", "N"]},
            ])

        if show_diag:
            self.ic_diag_html_blocks = self._render_ic_diagnostics_tables()

        self.custom_table_blocks: List[str] = []
        if self.manifest.custom_tables:
            for spec in self.manifest.custom_tables:
                data_obj = self._manifest_data(spec.data_key)
                if data_obj is None:
                    continue
                try:
                    table_html = spec.builder(data_obj, self)
                except Exception as err:
                    print(f"[custom_table] {spec.key} failed: {err}")
                    continue
                if not table_html:
                    continue
                block = f"""
                <div class=\"table-block\" data-table=\"{spec.key}\" data-group=\"{'controlled' if spec.controlled else 'free'}\">
                  <h3>{spec.title or spec.key}</h3>
                  {table_html}
                </div>
                """
                self.custom_table_blocks.append(block)

        # Write
        self._write_html()

    # ---------------------------------
    # internals
    # ---------------------------------
    @staticmethod
    def _is_polars_like(obj: Any) -> bool:
        return isinstance(obj, (pl.LazyFrame, pl.DataFrame))

    @staticmethod
    def _to_lazy(obj: Any) -> pl.LazyFrame:
        if isinstance(obj, pl.LazyFrame):
            return obj
        if isinstance(obj, pl.DataFrame):
            return obj.lazy()
        if isinstance(obj, pd.DataFrame):
            return pl.from_pandas(obj).lazy()
        if isinstance(obj, pd.Series):
            pdf = obj.to_frame()
            pdf["date"] = pd.to_datetime(pdf.index)
            return pl.from_pandas(pdf).lazy()
        if isinstance(obj, dict):
            return pl.DataFrame(obj).lazy()
        raise TypeError("Provided data must be convertible to a Polars LazyFrame.")

    def _resolve_data_spec(self, spec: Union[str, Callable[[Any], Any], Any], base: Any) -> Any:
        if callable(spec):
            return spec(base)
        if isinstance(spec, str):
            target = base
            for attr in spec.split("."):
                if not hasattr(target, attr):
                    raise AttributeError(f"Attribute '{attr}' not found while resolving data spec '{spec}'.")
                target = getattr(target, attr)
            return target
        return spec

    def _manifest_data(self, key: Optional[str]) -> Any:
        if key is None:
            return self.source_obj or self.data_sources.get("preds")
        if key in self.data_sources:
            return self.data_sources[key]
        if self.source_obj is not None:
            try:
                value = self._resolve_data_spec(key, self.source_obj)
            except Exception:
                return None
            self.data_sources[key] = value
            return value
        return None

    def save_custom_figure(self, fig, filename: Optional[str] = None, prefix: Optional[str] = None) -> Optional[str]:
        self._custom_fig_counter += 1
        name = filename
        if name is None:
            base = prefix or f"custom_fig_{self._custom_fig_counter}"
            name = f"{base}_{self._custom_fig_counter}.png"
        if hasattr(fig, "savefig"):
            path = os.path.join(self.fig_dir, name)
            fig.savefig(path, dpi=144, bbox_inches="tight")
            try:
                plt.close(fig)
            except Exception:
                pass
            return path
        return None

    def _normalize_custom_fig_output(
        self,
        result: Any,
        default_label: str,
        prefix: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        tiles: List[Tuple[str, str]] = []
        if result is None:
            return tiles
        if isinstance(result, (list, tuple)) and not (
            len(result) == 2 and isinstance(result[0], str) and isinstance(result[1], (str, os.PathLike))
        ):
            for entry in result:
                tiles.extend(self._normalize_custom_fig_output(entry, default_label, prefix))
            return tiles
        if isinstance(result, dict):
            label = str(result.get("label", default_label))
            path = result.get("path")
            fig = result.get("figure")
            fname = result.get("filename")
            pref = result.get("prefix", prefix)
            if fig is not None and path is None:
                path = self.save_custom_figure(fig, fname, pref)
            if path:
                tiles.append((label, str(path)))
            return tiles
        if isinstance(result, (tuple, list)):
            if len(result) == 2 and isinstance(result[0], str):
                label, path = result
                if path:
                    tiles.append((label or default_label, str(path)))
            else:
                for entry in result:
                    tiles.extend(self._normalize_custom_fig_output(entry, default_label, prefix))
            return tiles
        if isinstance(result, str):
            tiles.append((default_label, result))
            return tiles
        if hasattr(result, "savefig"):
            path = self.save_custom_figure(result, prefix=prefix)
            if path:
                tiles.append((default_label, path))
            return tiles
        return tiles

    # ---------------------------------
    # internals
    # ---------------------------------
    def _infer_factors(self) -> List[str]:
        names = self.P.collect_schema().names()
        return [c for c in names if c != "date"]

    def _render_metrics_grouped(self, df: pd.DataFrame, groups: List[Dict[str, List[str]]]) -> str:
        if df is None or df.empty:
            return "<div style='padding:12px;color:#888;'>No metrics.</div>"

        # pretty (2dp)
        d = df.copy()
        def fmt(v):
            if pd.isna(v):
                return "-"
            if isinstance(v, (int, float, np.floating)):
                return f"{float(v):.2f}"
            return str(v)
        d = d.applymap(fmt)

        cols = list(d.columns)
        idx_labels = {str(lbl).lower(): lbl for lbl in d.index}

        html = []
        html.append('<table class="metrics-grouped">')
        html.append('<thead><tr>')
        html.append('<th class="sticky-col">Metric</th>')
        for c in cols:
            html.append(f'<th>{c}</th>')
        html.append('</tr></thead><tbody>')

        used: set[str] = set()
        first_group = True
        for grp in groups:
            (gname, keys) = next(iter(grp.items()))
            if not first_group:
                html.append(f'<tr class="sep"><td colspan="{len(cols)+1}"></td></tr>')
            first_group = False
            html.append(f'<tr class="glabel"><td class="gtitle sticky-col" colspan="{len(cols)+1}">{gname}</td></tr>')

            for key in keys:
                nk = str(key).lower()
                if nk not in idx_labels:
                    continue
                label = idx_labels[nk]
                used.add(label)
                row = d.loc[label]
                html.append('<tr>')
                html.append(f'<td class="mname sticky-col">{label}</td>')
                for c in cols:
                    html.append(f'<td class="mval">{str(row.get(c, "-"))}</td>')
                html.append('</tr>')

        leftovers = [lbl for lbl in d.index if lbl not in used]
        if leftovers:
            html.append(f'<tr class="sep"><td colspan="{len(cols)+1}"></td></tr>')
            html.append(f'<tr class="glabel"><td class="gtitle sticky-col" colspan="{len(cols)+1}">Other</td></tr>')
            for label in leftovers:
                row = d.loc[label]
                html.append('<tr>')
                html.append(f'<td class="mname sticky-col">{label}</td>')
                for c in cols:
                    html.append(f'<td class="mval">{str(row.get(c, "-"))}</td>')
                html.append('</tr>')

        html.append('</tbody></table>')
        return "".join(html)

    def _render_ic_diagnostics_tables(self) -> List[str]:
        """
        Build a sortable LONG table per factor:
          columns: Lag, Horizon, IC, t-stat, MAE, Sign, N
        """
        blocks: List[str] = []
        for f in self.factors:
            df = self.grid_map.get(f, pl.DataFrame())
            if df.is_empty():
                continue
            pdf = df.select(["lag","horizon","ic","t","mae","sign","n"]).to_pandas()
            for c in ["lag","horizon","n"]:
                if c in pdf.columns:
                    pdf[c] = pd.to_numeric(pdf[c], errors="coerce")
            disp = pdf.copy()
            disp["IC"] = disp["ic"].map(lambda v: "-" if pd.isna(v) else f"{float(v):.3f}")
            disp["t-stat"] = disp["t"].map(lambda v: "-" if pd.isna(v) else f"{float(v):.2f}")
            disp["MAE"] = disp["mae"].map(lambda v: "-" if pd.isna(v) else f"{float(v):.4f}")
            disp["Sign"] = disp["sign"].map(lambda v: "-" if pd.isna(v) else f"{float(v):.2f}")
            disp["N"] = disp["n"].map(lambda v: "-" if pd.isna(v) else f"{int(round(float(v)))}")
            disp = disp.rename(columns={"lag":"Lag","horizon":"Horizon"})
            disp = disp[["Lag","Horizon","IC","t-stat","MAE","Sign","N"]]

            table_html = disp.to_html(border=0, escape=False, index=False, classes=["sortable"])
            blocks.append(f"""
            <div class="table-block" data-table="ic_diag" data-group="controlled">
              <h3>IC Diagnostics — {f}</h3>
              <div class="sort-tips">Click headers to sort; Shift+Click for multi-column sort.</div>
              {table_html}
            </div>
            """)

        return blocks

    def _render_heatmap_tile(self, df: pl.DataFrame, value_col: str, factor: str, title_prefix: str, cmap: str) -> Optional[str]:
        if df.is_empty():
            return None
        pdf = df.select(['lag', 'horizon', value_col]).to_pandas()
        if pdf.empty:
            return None
        pivot = pdf.pivot_table(index='lag', columns='horizon', values=value_col)
        pivot = pivot.sort_index().sort_index(axis=1)
        lag_labels = [int(l) for l in pivot.index]
        horizon_labels = [int(h) for h in pivot.columns]
        data = pivot.to_numpy(dtype=float)
        if np.isfinite(data).any():
            vmin = float(np.nanmin(data))
            vmax = float(np.nanmax(data))
            if value_col in {"ic", "t"}:
                clim = max(abs(vmin), abs(vmax)) or 1.0
                vmin, vmax = -clim, clim
            elif np.isclose(vmin, vmax):
                delta = abs(vmin) if vmin != 0 else 1.0
                vmin, vmax = vmin - delta, vmax + delta
        else:
            vmin, vmax = -1.0, 1.0

        fig_width = max(3.5, len(horizon_labels) * 0.9)
        fig_height = max(2.6, len(lag_labels) * 0.7)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_visible(False)

        center = 0 if value_col in {"ic", "t"} else None
        heatmap = sns.heatmap(
            pivot,
            ax=ax,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            center=center,
            annot=True,
            fmt=".2f",
            annot_kws={"size": 8, "weight": "bold", "color": "#1b1b1b"},
            linewidths=0.4,
            linecolor="#f0f0f0",
            cbar=False,
            square=False,
        )

        ax.set_xlabel("Horizon", fontsize=10, fontweight="bold")
        ax.set_ylabel("Lag", fontsize=10, fontweight="bold")
        ax.set_xticks(range(len(horizon_labels)))
        ax.set_xticklabels([str(h) for h in horizon_labels], fontsize=8)
        ax.set_yticks(range(len(lag_labels)))
        ax.set_yticklabels([str(l) for l in lag_labels], fontsize=8)
        ax.tick_params(colors="#666666")
        ax.set_title(f"{title_prefix} — {factor}", fontsize=12, pad=8)
        fig.tight_layout()
        file_name = f"{value_col}_{factor}.png"
        output_path = os.path.join(self.fig_dir, file_name)
        fig.savefig(output_path, dpi=144, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def _write_html(self) -> None:
        # Figures grid: each factor becomes a column, stacking IC → t → Sign vertically
        columns_html: List[str] = []
        for idx, factor in enumerate(self.factors):
            fig_tiles: List[str] = []
            figs = self.fig_paths.get(factor, {})
            order = [k for k in ("IC", "t", "sign") if k in figs]
            order += [k for k in figs.keys() if k not in order]
            for key in order:
                path = figs.get(key)
                if not path:
                    continue
                fig_tiles.append(
                    f"""<div class="thumb">
                           <div class="fig-header">{key} — {factor}</div>
                           <img src="{os.path.relpath(path, self.output_dir)}" alt="{key} - {factor}" data-zoom="1"/>
                        </div>"""
                )
            for tile in getattr(self, "custom_fig_columns", []):
                col_tiles = tile.get("tiles", [])
                if idx < len(col_tiles):
                    label, path = col_tiles[idx]
                    if path:
                        rel = os.path.relpath(path, self.output_dir)
                        fig_tiles.append(
                            f"""<div class="thumb">
                                   <div class="fig-header">{label}</div>
                                   <img src="{rel}" alt="{label}" data-zoom="1"/>
                                </div>"""
                        )
            if fig_tiles:
                columns_html.append(
                    f"""<div class="fig-column">
                           <div class="fig-title">{factor}</div>
                           <div class="fig-stack">
                             {''.join(fig_tiles)}
                           </div>
                        </div>"""
                )
        if columns_html:
            figures_html = f"""<div class="fig-column-grid" style="grid-template-columns: repeat({len(columns_html)}, minmax(0, 1fr));">
                       {''.join(columns_html)}
                    </div>"""
        else:
            figures_html = "<div style='padding:12px;color:#888;'>No figures.</div>"

        # Tables
        blocks = []
        if self.include_core_tables and self.metrics_html:
            blocks.append(f"""
            <div class="table-block" data-table="pred_metrics" data-group="controlled">
              <h3>Key Prediction Metrics</h3>
              {self.metrics_html}
            </div>
            """)
        if self.include_core_tables and self.ic_diag_html_blocks:
            blocks.extend(self.ic_diag_html_blocks)
        if getattr(self, "custom_table_blocks", None):
            blocks.extend(self.custom_table_blocks)
        tables_html = "\n".join(blocks) if blocks else "<div style='padding:12px;color:#888;'>No tables.</div>"

        # CSS/JS (right slider, padding, sortable tables)
        css = r"""
<style>
:root {
  --gutter: 10px;
  --left-col: 65%;
  --right-col: 35%;
  --tables-w: 720px;
  --handle-left: var(--tables-w);
}
* { box-sizing: border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; background:#fff; }
.page { padding: 16px; }
.titlebar { display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }
.titlebar h1 { margin:0; font-size:20px; }
.meta { margin: 4px 0 0 0; color:#666; font-size:12px; }

.outer-split { display:grid; grid-template-columns:var(--left-col) var(--gutter) var(--right-col); width:100%; height:calc(100vh - 120px); min-height:540px; }
.left-pane, .right-pane { overflow:auto; }
.gutter { background:transparent; cursor:col-resize; width:var(--gutter); opacity:.18; transition:opacity .12s ease; }
.outer-split:hover .gutter { opacity:.28; }
.gutter:hover { opacity:.32; }

.tables-wrap { position:relative; height:100%; overflow:hidden; }
.tables-content { position:absolute; left:0; top:0; bottom:0; width:calc(var(--tables-w) + 60px); overflow:auto; padding:4px 44px 20px 10px; background:transparent; }
.right-handle { position:absolute; top:0; bottom:0; left:var(--handle-left); width:10px; cursor:col-resize; background:rgba(0,0,0,0.06); z-index:5; opacity:0.24; transition:opacity .12s ease, background .12s ease; }
.tables-wrap:hover .right-handle { opacity:.35; }
body.dragging-right .right-handle { background:rgba(0,0,0,0.08); opacity:.6; }

.fig-column-grid { display:grid; gap:16px; margin:6px 8px 18px 2px; align-items:start; }
.fig-column { display:flex; flex-direction:column; gap:10px; }
.fig-title { font-size:14px; font-weight:600; margin:4px 2px 0 2px; color:#333; }
.fig-description { font-size:12px; margin:2px 2px 0 2px; color:#555; line-height:1.4; }
.fig-stack { display:flex; flex-direction:column; gap:10px; }
.fig-grid { display:grid; gap:10px; }
.thumb { border:1px solid #e4e4e4; border-radius:6px; overflow:hidden; background:#fff; padding:6px; }
.thumb .fig-header { font-size:12px; font-weight:600; margin:0 0 6px 0; color:#333; text-align:left; }
.thumb img { display:block; width:100%; height:auto; cursor:zoom-in; }

.metrics-grouped { border-collapse:collapse; background:#fff; width:auto; table-layout:auto; font-size:12px; }
.metrics-grouped thead th { background:#f6f6f6; font-weight:600; padding:6px 10px; border:none; text-align:right; font-size:12px; }
.metrics-grouped thead th.sticky-col { text-align:left; position:sticky; left:0; background:#f6f6f6; z-index:2; }
.metrics-grouped tbody td { padding:6px 10px; border:none; font-size:12px; }
.metrics-grouped td.mname.sticky-col { position:sticky; left:0; background:#fff; z-index:1; color:#333; font-weight:500; }
.metrics-grouped tr.sep td { border-bottom:1px solid #d0d0d0; height:6px; padding:0; }
.metrics-grouped tr.glabel td.gtitle { color:#222; font-size:13px; font-weight:700; letter-spacing:.2px; padding:6px 4px 4px 4px; border-top:1px solid #ddd; }

.table-block { margin:8px 4px 18px 4px; }
.table-block h3 { font-size:14px; margin:0 0 6px 0; color:#222; }
.table-block table { border-collapse:collapse; background:#fff; width:var(--tables-w); white-space:nowrap; font-size:12px; }
.table-block thead th { background:#f6f6f6; color:#333; padding:6px 10px; border:none; text-align:right; font-weight:600; }
.table-block thead th:first-child { text-align:left; }
.table-block tbody td { padding:6px 10px; border:none; text-align:right; }
.table-block tbody td:first-child { text-align:left; }
.sort-tips { color:#777; font-size:11px; margin:2px 0 8px 2px; }

.modal { position:fixed; inset:0; display:none; align-items:center; justify-content:center; background:rgba(0,0,0,0.76); z-index:1000; }
.modal img { max-width:98vw; max-height:96vh; display:block; box-shadow:0 10px 26px rgba(0,0,0,0.45); border-radius:10px; }
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
  if (!wrap || !root) { return; }

  function cssPx(name, fallback=0){
    const v = getComputedStyle(root).getPropertyValue(name).trim();
    if (!v) return fallback;
    return v.endsWith('px') ? parseFloat(v) : (parseFloat(v) || fallback);
  }
  function setVarPx(name, px){ root.style.setProperty(name, px + 'px'); }
  function setLeftRightPx(leftPx, rightPx){
    const total = leftPx + cssPx('--gutter',10) + rightPx;
    if (total <= 0) return;
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
    const tw = cssPx('--tables-w', 720);
    const left = Math.max(0, Math.min(r.width - 10, tw));
    setVarPx('--handle-left', left);
  }
  function initTablesWidthToContent(){
    let maxW = 480;
    document.querySelectorAll('.table-block[data-group=\"controlled\"] table').forEach(t => {
      maxW = Math.max(maxW, t.scrollWidth + 24);
    });
    setVarPx('--tables-w', maxW);
    positionHandle();
  }

  let dragL = false;
  if (gutter && outer) {
    gutter.addEventListener('mousedown', e => { dragL=true; e.preventDefault(); document.body.style.userSelect='none'; });
    window.addEventListener('mousemove', e => {
      if (!dragL) return;
      const rect = outer.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const minL = 260;
      const maxL = rect.width - 360;
      const clamped = Math.max(minL, Math.min(maxL, x));
      const leftPx = clamped;
      const rightPx = rect.width - clamped - cssPx('--gutter',10);
      setLeftRightPx(leftPx, rightPx);
      positionHandle();
    });
    window.addEventListener('mouseup', () => {
      if (dragL){ dragL=false; document.body.style.userSelect=''; }
    });
  }

  let dragR = false;
  if (handle) {
    handle.addEventListener('mousedown', e => {
      dragR = true;
      e.preventDefault();
      document.body.style.userSelect='none';
      document.body.classList.add('dragging-right');
    });
    window.addEventListener('mousemove', e => {
      if (!dragR) return;
      const r = wrap.getBoundingClientRect();
      let x = e.clientX - r.left;
      x = clampTablesW(x);
      setVarPx('--tables-w', x);
      positionHandle();
    });
    window.addEventListener('mouseup', () => {
      if (dragR){
        dragR=false;
        document.body.style.userSelect='';
        document.body.classList.remove('dragging-right');
      }
    });
  }

  window.addEventListener('load', () => { initTablesWidthToContent(); });
  window.addEventListener('resize', () => { positionHandle(); });

  const modal = document.getElementById('zoom-modal');
  const modalImg = document.getElementById('zoom-image');
  document.querySelectorAll('img[data-zoom=\"1\"]').forEach(img => {
    img.addEventListener('click', () => {
      if (!modal || !modalImg) return;
      modalImg.src = img.src;
      modal.classList.add('show');
    });
  });
  if (modal) {
    modal.addEventListener('click', e => { if (e.target === modal || e.target.id === 'zoom-image') modal.classList.remove('show'); });
    window.addEventListener('keydown', e => { if (e.key === 'Escape') modal.classList.remove('show'); });
  }

  document.querySelectorAll('table.sortable').forEach(function(table){
    const ths = table.tHead ? table.tHead.rows[0].cells : [];
    if (!ths.length) return;
    let sorts = [];
    function sortTable(){
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      rows.sort((a,b)=>{
        for (const [idx,dir] of sorts){
          const av = a.cells[idx].textContent.trim();
          const bv = b.cells[idx].textContent.trim();
          const an = parseFloat(av.replace('%',''));
          const bn = parseFloat(bv.replace('%',''));
          const isNum = !Number.isNaN(an) && !Number.isNaN(bn);
          if (isNum && an !== bn) return dir * (an - bn);
          if (!isNum && av !== bv) return dir * (av > bv ? 1 : -1);
        }
        return 0;
      });
      rows.forEach(r => tbody.appendChild(r));
    }
    Array.from(ths).forEach((th, idx) => {
      th.style.cursor = 'pointer';
      th.addEventListener('click', e => {
        const dir = e.shiftKey ? -1 : 1;
        if (!e.shiftKey) sorts = [];
        const existingIndex = sorts.findIndex(([i]) => i === idx);
        if (existingIndex >= 0) sorts.splice(existingIndex, 1);
        sorts.push([idx, dir]);
        sortTable();
      });
    });
  });

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
        print(f"Prediction dashboard written to: {self.html_path}")

    def render(self) -> str:
        """Return the path to the generated HTML dashboard."""
        return self.html_path
