# dashboard.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime
import numpy as np
import pandas as pd
import quantstats as qs
from quantstats import stats as qs_stats
from quantstats import plots as qs_plots

import matplotlib.pyplot as plt


# -----------------------
# Helper: filesystem
# -----------------------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# -----------------------
# Risk-free + alignment
# -----------------------
def _align_like(obj: Union[pd.Series, pd.DataFrame, float, int],
                index: pd.DatetimeIndex,
                fill: float = 0.0) -> pd.Series:
    """
    Align rf-like object to index.
    - float/int -> constant Series
    - Series -> reindex fill
    - DataFrame -> first column
    """
    if isinstance(obj, (float, int)):
        return pd.Series(float(obj), index=index, name="rf")
    if isinstance(obj, pd.DataFrame):
        s = obj.iloc[:, 0] if obj.shape[1] > 1 else obj.squeeze("columns")
        s = s.reindex(index).fillna(fill)
        s.name = "rf"
        return s
    if isinstance(obj, pd.Series):
        s = obj.reindex(index).fillna(fill)
        s.name = "rf"
        return s
    return pd.Series(fill, index=index, name="rf")


def _maybe_excess_returns(returns_pd: pd.DataFrame,
                          rf: Optional[Union[float, int, pd.Series, pd.DataFrame]],
                          periods_per_year: int) -> pd.DataFrame:
    """
    Convert returns to excess returns if rf provided.
    float/int -> treated as ANNUAL rf, converted to per-period.
    Series/DataFrame -> assumed per-period and aligned.
    """
    rets = returns_pd.copy()
    try:
        rets.index = rets.index.tz_localize(None)
    except Exception:
        pass

    if rf is None:
        return rets

    if isinstance(rf, (float, int)):
        pprf = (1.0 + float(rf)) ** (1.0 / periods_per_year) - 1.0
        return rets - pprf

    rf_series = _align_like(rf, rets.index, fill=0.0)
    return rets.sub(rf_series, axis=0)


# -----------------------
# Canonical figure & table lists
# -----------------------
DEFAULT_FIGURES = [
    "snapshot",
    "earnings",
    "returns",
    "log_returns",
    "yearly_returns",
    "daily_returns",
    "rolling_beta",
    "rolling_volatility",
    "rolling_sharpe",
    "rolling_sortino",
    "drawdowns_periods",
    "drawdown",
    "monthly_heatmap",
    "histogram",
    "distribution",
]

ALL_TABLES = ["metrics", "eoy", "monthly_returns", "drawdown_details"]


# -----------------------
# Manifest: choose subsets
# -----------------------
@dataclass
class DashboardManifest:
    figures: Optional[List[str]] = None          # subset of DEFAULT_FIGURES
    metric_rows: Optional[List[str]] = None      # canonical row keys (case-insensitive, alnum-only)
    metric_cols: Optional[List[str]] = None      # subset of columns (e.g., ["Strategy1","Benchmark"])
    tables: Optional[List[str]] = None           # subset of ALL_TABLES


# -----------------------
# Main Dashboard
# -----------------------
class QuantStatsDashboard:
    def __init__(
        self,
        returns_df: pd.DataFrame,
        benchmark: Optional[pd.Series] = None,
        rf: Optional[Union[float, int, pd.Series, pd.DataFrame]] = None,
        title: str = "Strategy Tearsheet",
        output_dir: str = "output/comprehensive_reports",
        manifest: Optional[DashboardManifest] = None,
        periods_per_year: int = 252,
    ) -> None:
        self.ppy = periods_per_year
        self.title = title
        self.output_dir = output_dir
        _ensure_dir(self.output_dir)

        # clean inputs
        self.returns_pd = returns_df.copy()
        self.returns_pd.index = pd.DatetimeIndex(self.returns_pd.index).tz_localize(None)
        self.strategies = list(self.returns_pd.columns)

        self.benchmark = benchmark.copy() if benchmark is not None else None
        if self.benchmark is not None:
            self.benchmark.index = pd.DatetimeIndex(self.benchmark.index).tz_localize(None)
            common_idx = self.returns_pd.index.intersection(self.benchmark.index)
            self.returns_pd = self.returns_pd.loc[common_idx]
            self.benchmark = self.benchmark.loc[common_idx]

        # Convert to EXCESS once; then rf=0.0 everywhere (plots + metrics).
        self.returns_excess = _maybe_excess_returns(self.returns_pd, rf, self.ppy)
        self.benchmark_excess = None
        if self.benchmark is not None:
            self.benchmark_excess = _maybe_excess_returns(self.benchmark.to_frame("bench"), rf, self.ppy)["bench"]

        # date range
        self.start = self.returns_excess.index.min().strftime("%Y-%m-%d")
        self.end = self.returns_excess.index.max().strftime("%Y-%m-%d")
        self.date_range_str = f"{self.start} — {self.end}"

        # manifest
        self.fig_list = (manifest.figures if manifest and manifest.figures else DEFAULT_FIGURES)

        # tables subset
        if manifest and manifest.tables:
            self.tables_list = [t for t in manifest.tables if t in ALL_TABLES]
            if not self.tables_list:
                self.tables_list = ALL_TABLES.copy()
        else:
            self.tables_list = ALL_TABLES.copy()

        # metric rows filter (exact by normalized key)
        self.metric_rows_filter = None
        if manifest and manifest.metric_rows:
            self.metric_rows_filter = [self._norm_key(k) for k in manifest.metric_rows]

        # metric columns filter (exact by name, case-insensitive)
        self.metric_cols_filter = None
        if manifest and manifest.metric_cols:
            wanted = set(n.lower() for n in manifest.metric_cols)
            cols = []
            for c in (["Benchmark"] if self.benchmark_excess is not None else []) + self.strategies:
                if c.lower() in wanted:
                    cols.append(c)
            self.metric_cols_filter = cols if cols else None

        # output paths
        self.fig_dir = os.path.join(self.output_dir, "figures")
        _ensure_dir(self.fig_dir)
        self.html_path = os.path.join(self.output_dir, "dashboard.html")
        self.manifest_path = os.path.join(self.output_dir, "available_manifest.json")

        # build
        self._save_manifest()
        self._build_figures()
        self._build_tables()
        self._write_html()

    # -----------------------
    # Normalization helper for metric row keys
    # -----------------------
    @staticmethod
    def _norm_key(s: str) -> str:
        return "".join(ch.lower() for ch in s if ch.isalnum())

    # -----------------------
    # Manifest of available things
    # -----------------------
    def _save_manifest(self) -> None:
        full_metrics = self._compute_metrics_table(full=True)
        keys = list(full_metrics.index)
        manifest = {
            "figures_available": DEFAULT_FIGURES,
            "tables_available": ALL_TABLES,
            "metric_rows": keys,
            "metric_cols": (["Benchmark"] if self.benchmark_excess is not None else []) + self.strategies,
            "date_range": [self.start, self.end],
        }
        import json
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[manifest] wrote: {self.manifest_path}")

    # -----------------------
    # Metrics (QuantStats) on EXCESS returns; rf=0.0 -> consistency
    # -----------------------
    def _compute_metrics_table(self, full: bool = False) -> pd.DataFrame:
        """
        Compute metrics once via QS for the whole object (handles 1 or many columns).
        Using original returns/benchmark with QS's own preparation avoids many '-' cells.
        """
        mode = "full" if full else "basic"

        # Use original cleaned inputs (not the excess series) for QS metrics stability
        ret_in = self.returns_pd.copy()
        bench_in = self.benchmark.copy() if self.benchmark is not None else None

        # QS accepts Series or DataFrame; handle the 1-column edge case explicitly
        if isinstance(ret_in, pd.DataFrame) and ret_in.shape[1] == 1:
            ret_in = ret_in.iloc[:, 0]

        try:
            m = qs.reports.metrics(
                returns=ret_in,
                benchmark=bench_in,
                rf=0.0,                 # rf already handled for plots; QS 'rf' is scalar-only anyway
                display=False,
                mode=mode,
                compounded=True,
                prepare_returns=True,   # <-- let QS prep; reduces 'blank' metrics
                periods_per_year=self.ppy,
            )
        except Exception as e:
            print(f"[metrics] fallback basic metrics due to: {e}")
            # ultra-conservative fallback
            if isinstance(ret_in, pd.Series):
                ret_in = ret_in.to_frame(ret_in.name or "Strategy")
            cols = []
            for c in ret_in.columns:
                s = ret_in[c].dropna()
                ann_ret = (1 + s).prod() ** (self.ppy / max(1, len(s))) - 1 if len(s) else np.nan
                ann_vol = s.std(ddof=0) * np.sqrt(self.ppy) if len(s) else np.nan
                sharpe  = (s.mean() * self.ppy) / ann_vol if ann_vol and ann_vol != 0 else np.nan
                cols.append(pd.Series(
                    {"Start Period": s.index.min(), "End Period": s.index.max(),
                    "CAGR﹪": ann_ret, "Volatility (ann.)": ann_vol, "Sharpe": sharpe},
                    name=c
                ))
            m = pd.concat(cols, axis=1)
            m.index.name = "Metric"
            return m

        # Normalize to DataFrame
        if isinstance(m, pd.Series):
            name = ret_in.name if isinstance(ret_in, pd.Series) else (ret_in.columns[0] if ret_in.shape[1] else "Strategy")
            m = m.to_frame(name=name)

        m.index.name = "Metric"
        return m
    # -----------------------
    # EOY Returns
    # -----------------------
    def _eoy_table(self) -> Dict[str, pd.DataFrame]:
        """
        For each strategy, return a long-form EOY comparison table:
        columns = Year | Benchmark | Strategy | Multiplier | Won

        - Benchmark: EOY return of benchmark for that year (NaN if missing)
        - Strategy : EOY return of the strategy for that year
        - Multiplier: Strategy / Benchmark (NaN if Benchmark is 0 or NaN)
        - Won: "+" if Strategy > Benchmark else "–" (blank if either is NaN)
        """
        out: Dict[str, pd.DataFrame] = {}

        # Build a robust year -> benchmark_return map (if benchmark exists)
        bench_map = {}
        if self.benchmark_excess is not None:
            b = self.benchmark_excess.dropna()
            if not b.empty:
                by = b.resample("YE").apply(lambda r: (1 + r).prod() - 1.0)
                bench_map = {d.year: float(v) for d, v in zip(by.index, by.values)}

        for col in self.strategies:
            s = self.returns_excess[col].dropna()
            if s.empty:
                out[col] = pd.DataFrame(columns=["Year", "Benchmark", "Strategy", "Multiplier", "Won"])
                continue

            # Strategy EOY returns
            sy = s.resample("YE").apply(lambda r: (1 + r).prod() - 1.0)

            # Assemble long-form table
            df = pd.DataFrame({
                "Year": sy.index.year.astype(int),
                "Strategy": sy.values.astype(float),
            })

            # Map benchmark by year (via dict; no positional indexing)
            if bench_map:
                df["Benchmark"] = df["Year"].map(bench_map).astype(float)
            else:
                df["Benchmark"] = np.nan

            # Multiplier = Strategy / Benchmark (guard 0/NaN)
            bench = df["Benchmark"].to_numpy()
            strat = df["Strategy"].to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                mult = np.where(
                    np.isfinite(bench) & (np.abs(bench) > 1e-12),
                    strat / bench,
                    np.nan
                )
            df["Multiplier"] = mult

            # Won = "+" if Strategy > Benchmark (only when both are finite)
            won = np.where(
                np.isfinite(strat) & np.isfinite(bench),
                np.where(strat > bench, "+", "–"),
                ""
            )
            df["Won"] = won

            # Final column order
            df = df[["Year", "Benchmark", "Strategy", "Multiplier", "Won"]].reset_index(drop=True)
            out[col] = df

        return out

    # -----------------------
    # Monthly Returns per strategy (heatmap source)
    # -----------------------
    def _monthly_tables(self) -> Dict[str, pd.DataFrame]:
        res: Dict[str, pd.DataFrame] = {}
        for col in self.strategies:
            ser = self.returns_excess[col].dropna()
            if ser.empty:
                res[col] = pd.DataFrame()
                continue
            g = ser.groupby([ser.index.year, ser.index.month]).apply(lambda r: (1 + r).prod() - 1.0)
            m = g.unstack(fill_value=np.nan)
            # month numbers -> "Jan" ...
            from datetime import datetime as _dt
            m.columns = [_dt(2000, int(c), 1).strftime("%b") for c in m.columns]
            res[col] = m
        return res

    # -----------------------
    # Drawdown details per strategy
    # -----------------------
    def _drawdown_tables(self) -> Dict[str, pd.DataFrame]:
        res: Dict[str, pd.DataFrame] = {}
        for col in self.strategies:
            ser = self.returns_excess[col].dropna()
            if ser.empty:
                res[col] = pd.DataFrame()
                continue
            dd_series = qs_stats.to_drawdown_series(ser)
            dd_info = qs_stats.drawdown_details(dd_series)
            if dd_info.empty:
                res[col] = pd.DataFrame()
                continue
            dd_info = dd_info.sort_values(by="max drawdown", ascending=True).copy()
            dd_info = dd_info[["start", "end", "max drawdown", "days"]].head(10)
            dd_info.columns = ["Started", "Recovered", "Drawdown", "Days"]
            res[col] = dd_info
        return res

    # -----------------------
    # Build figures (per-strategy), save PNGs — use pure QuantStats defaults
    # -----------------------
    def _build_figures(self) -> None:
        self.fig_paths: Dict[str, Dict[str, str]] = {col: {} for col in self.strategies}
        bench = self.benchmark_excess  # may be None

        def _save(fig, fname: str):
            if fig is None:
                return
            p = os.path.join(self.fig_dir, fname)
            fig.savefig(p, dpi=144, bbox_inches="tight")
            try:
                plt.close(fig)
            except Exception:
                pass
            return p

        for col in self.strategies:
            s = self.returns_excess[col].dropna()
            if s.empty:
                continue

            for f in self.fig_list:
                fig_obj = None
                try:
                    if f == "snapshot":
                        fig_obj = qs_plots.snapshot(s, show=False)
                    elif f == "earnings":
                        fig_obj = qs_plots.earnings(s, show=False)
                    elif f == "returns":
                        fig_obj = qs_plots.returns(s, benchmark=bench, show=False)
                    elif f == "log_returns":
                        fig_obj = qs_plots.log_returns(s, benchmark=bench, show=False)
                    elif f == "yearly_returns":
                        fig_obj = qs_plots.yearly_returns(s, benchmark=bench, show=False)
                    elif f == "daily_returns":
                        fig_obj = qs_plots.daily_returns(s, benchmark=bench, show=False)
                    elif f == "rolling_beta":
                        if bench is not None:
                            fig_obj = qs_plots.rolling_beta(s, bench, show=False)
                    elif f == "rolling_volatility":
                        # if your QS supports overlay benchmark volatility, pass it; else omit
                        try:
                            fig_obj = qs_plots.rolling_volatility(s, benchmark=bench, show=False)
                        except TypeError:
                            fig_obj = qs_plots.rolling_volatility(s, show=False)
                    elif f == "rolling_sharpe":
                        fig_obj = qs_plots.rolling_sharpe(s, show=False)
                    elif f == "rolling_sortino":
                        fig_obj = qs_plots.rolling_sortino(s, show=False)
                    elif f == "drawdowns_periods":
                        fig_obj = qs_plots.drawdowns_periods(s, show=False)
                    elif f == "drawdown":
                        fig_obj = qs_plots.drawdown(s, show=False)
                    elif f == "monthly_heatmap":
                        # older QS builds lack some kwargs; keep minimal
                        if bench is not None:
                            try:
                                fig_obj = qs_plots.monthly_heatmap(s, benchmark=bench, show=False)
                            except TypeError:
                                fig_obj = qs_plots.monthly_heatmap(s, show=False)
                        else:
                            fig_obj = qs_plots.monthly_heatmap(s, show=False)
                    elif f == "histogram":
                        fig_obj = qs_plots.histogram(s, benchmark=bench, show=False)
                    elif f == "distribution":
                        # QS distribution() does NOT accept benchmark — generate per series
                        fig_obj = qs_plots.distribution(s, show=False)
                    else:
                        continue

                    if fig_obj is not None:
                        fp = _save(fig_obj, f"{f}_{col}.png")
                        if fp:
                            self.fig_paths[col][f] = fp
                except Exception as e:
                    print(f"[plot] failed: {f}({col}) -> {e}")

    # -----------------------
    # Build tables
    # -----------------------
    def _build_tables(self) -> None:
        # Metrics
        full_m = self._compute_metrics_table(full=True)

        # Filter rows by canonical keys (exact after normalization)
        if self.metric_rows_filter:
            idx_map = {self._norm_key(i): i for i in full_m.index}
            keep_keys = [idx_map[k] for k in self.metric_rows_filter if k in idx_map]
            metrics_df = full_m.loc[keep_keys] if keep_keys else full_m
        else:
            metrics_df = full_m

        # Filter columns if requested
        if self.metric_cols_filter:
            keep_cols = [c for c in self.metric_cols_filter if c in metrics_df.columns]
            if keep_cols:
                metrics_df = metrics_df[keep_cols]

        # Reorder to put Benchmark first if exists
        cols = list(metrics_df.columns)
        if "Benchmark" in cols:
            cols = ["Benchmark"] + [c for c in cols if c != "Benchmark"]
            metrics_df = metrics_df[cols]
        self.metrics_df = metrics_df

        # EOY
        # EOY (now per strategy)
        self.eoy_map = self._eoy_table()  # Dict[strategy -> DataFrame]
        if self.metric_cols_filter:
            wanted = set(c for c in self.metric_cols_filter if c != "Benchmark")
            self.eoy_map = {k: v for k, v in self.eoy_map.items() if k in wanted}

        # Monthly per strategy
        month_map = self._monthly_tables()
        if self.metric_cols_filter:
            wanted = set(c for c in self.metric_cols_filter if c != "Benchmark")
            self.monthly_map = {k: v for k, v in month_map.items() if k in wanted}
        else:
            self.monthly_map = month_map

        # Drawdowns per strategy
        dd_map = self._drawdown_tables()
        if self.metric_cols_filter:
            wanted = set(c for c in self.metric_cols_filter if c != "Benchmark")
            self.dd_map = {k: v for k, v in dd_map.items() if k in wanted}
        else:
            self.dd_map = dd_map

    # -----------------------
    # HTML writer
    # -----------------------
    def _write_html(self) -> None:
        # Initial left/right split scaled by number of strategies (unchanged)
        n_strats = max(1, len(self.strategies))
        base_left = 54.0
        factor = min(n_strats / 3.0, 1.0)  # 1 -> ~1/3, 2 -> ~2/3, 3+ -> full default
        left_pct = round(base_left * factor, 2)
        right_pct = round(100.0 - left_pct, 2)

        css = f"""
    <style>
    :root {{
        --gutter: 10px;
        --left-col: {left_pct}%;
        --right-col: {right_pct}%;

        /* Tables content width, set by JS to widest table (px) */
        --tables-w: 720px;

        /* Right handle (px-from-left inside tables-wrap); set by JS */
        --handle-left: var(--tables-w);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background:#fff; }}
    .page {{ padding: 16px; }}

    .titlebar {{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }}
    .titlebar h1 {{ margin:0; font-size:20px; }}
    .titlebar .sub {{ color:#555; font-size:13px; }}
    .meta {{ margin: 4px 0 16px 0; color:#666; font-size:12px; }}

    .outer-split {{
        display: grid;
        grid-template-columns: var(--left-col) var(--gutter) var(--right-col);
        width: 100%;
        height: calc(100vh - 100px);
        min-height: 540px;
    }}
    .left-pane, .right-pane {{ overflow: auto; }}

    .gutter {{
        background: transparent;
        cursor: col-resize;
        width: var(--gutter);
    }}
    .gutter:hover {{ background: rgba(0,0,0,0.06); }}

    /* Figures */
    .fig-row {{ margin: 6px 8px 18px 2px; }}
    .fig-title {{ font-size:13px; font-weight:600; margin: 4px 6px; color:#333; }}
    .fig-grid {{
        display: grid;
        grid-template-columns: repeat(AUTO_COLS, 1fr);
        gap: 10px;
    }}
    .thumb {{
        border: 1px solid #e4e4e4;
        border-radius: 6px;
        overflow: hidden;
        background:#fff;
    }}
    .thumb img {{ display:block; width:100%; height:auto; cursor: zoom-in; }}

    /* Tables panel w/ sticky right handle */
    .tables-wrap {{
        position: relative;
        height: 100%;
        overflow: hidden; /* we manage width so no h-scroll initially */
    }}
    .tables-content {{
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: var(--tables-w);
        overflow: auto; /* falls back to h-scroll if user shrinks too far */
        padding: 4px 10px 12px 10px;
        background: transparent;
    }}
    .right-handle {{
        position: absolute;
        top: 0; bottom: 0;
        left: var(--handle-left);
        width: 8px;
        cursor: col-resize;
        background: transparent;     /* invisible by default */
        z-index: 5;
        pointer-events: auto;
    }}
    .right-handle:hover {{ background: rgba(0,0,0,0.06); }}

    /* Tables */
    .table-block {{ margin: 8px 4px 18px 4px; }}
    .table-block h3 {{ font-size:14px; margin: 0 0 6px 0; }}
    table {{ border-collapse: collapse; width: 100%; background:#fff; }}
    th, td {{ border: 1px solid #d8d8d8; padding: 6px 8px; font-size: 12px; text-align: right; }}
    th {{ background: #f6f6f6; color:#333; text-align: left; }}
    td:first-child, th:first-child {{ text-align: left; }}

    /* Zoom modal */
    .modal {{
        position: fixed; inset: 0; display:none; align-items: center; justify-content: center;
        background: rgba(0,0,0,0.76); z-index: 1000;
    }}
    .modal img {{
        max-width: 98vw; max-height: 96vh; display:block;
        box-shadow: 0 10px 26px rgba(0,0,0,0.45); border-radius: 10px;
    }}
    .modal.show {{ display:flex; }}
    </style>
    """

        # ---- Figures HTML (unchanged from your latest) ----
        fig_rows_html = []
        for f in self.fig_list:
            tiles, have_count = [], 0
            for col in self.strategies:
                p = self.fig_paths.get(col, {}).get(f)
                if p and os.path.isfile(p):
                    have_count += 1
                    tiles.append(
                        f"""<div class="thumb"><img src="{os.path.relpath(p, self.output_dir)}" alt="{f} - {col}" data-zoom="1"/></div>"""
                    )
            if have_count == 0:
                continue
            row = f"""
            <div class="fig-row">
            <div class="fig-title">{f.replace('_',' ').title()}</div>
            <div class="fig-grid" style="grid-template-columns: repeat({have_count}, 1fr);">
                {''.join(tiles)}
            </div>
            </div>
            """
            fig_rows_html.append(row)
        figures_html = "\n".join(fig_rows_html) if fig_rows_html else "<div style='padding:12px;color:#888;'>No figures generated.</div>"

        # ---- Tables HTML (unchanged structure) ----
        def _as_pct(df: pd.DataFrame, sig: int = 2) -> pd.DataFrame:
            if df is None or df.empty: return pd.DataFrame()
            d = df.copy()
            def fmt(x):
                if pd.isna(x): return "-"
                if isinstance(x, (int, float, np.floating)): return f"{x*100.0:.{sig}f}%"
                return str(x)
            try:    return d.map(fmt)
            except: return d.applymap(fmt)

        blocks = []
        if "metrics" in self.tables_list:
            metrics_html = self.metrics_df.to_html(border=0, escape=False)
            blocks.append(f"""
            <div class="table-block" data-table="normal">
                <h3>Key Performance Metrics</h3>
                {metrics_html}
            </div>
            """)

        if "eoy" in self.tables_list and getattr(self, "eoy_map", None):
            for col in (self.metric_cols_filter or self.strategies):
                if col == "Benchmark": continue
                df = self.eoy_map.get(col)
                if df is None or df.empty: continue
                disp = df.copy()
                for k in ["Benchmark", "Strategy", "Multiplier"]:
                    if k in disp.columns and k != "Multiplier":
                        disp[k] = disp[k].map(lambda v: f"{v*100:.2f}%" if pd.notna(v) else "-")
                    elif k == "Multiplier" and k in disp.columns:
                        disp[k] = disp[k].map(lambda v: f"{v:.2f}x" if pd.notna(v) else "-")
                eoy_html = disp.to_html(border=0, escape=False)
                blocks.append(f"""
                <div class="table-block" data-table="normal">
                    <h3>EOY vs Benchmark — {col}</h3>
                    {eoy_html}
                </div>
                """)

        if "monthly_returns" in self.tables_list and self.monthly_map:
            for col in (self.metric_cols_filter or self.strategies):
                if col == "Benchmark": continue
                m = self.monthly_map.get(col, pd.DataFrame())
                if m is None or m.empty: continue
                m_disp = _as_pct(m, sig=2).to_html(border=0, escape=False)
                blocks.append(f"""
                <div class="table-block" data-table="monthly">
                    <h3>Monthly Returns — {col}</h3>
                    {m_disp}
                </div>
                """)

        if "drawdown_details" in self.tables_list and self.dd_map:
            for col in (self.metric_cols_filter or self.strategies):
                if col == "Benchmark": continue
                ddf = self.dd_map.get(col, pd.DataFrame())
                if ddf is None or ddf.empty: continue
                ddisp = ddf.copy()
                if "Drawdown" in ddisp.columns:
                    ddisp["Drawdown"] = ddisp["Drawdown"].map(
                        lambda v: f"{v:.2f}%" if isinstance(v, (int, float, np.floating)) else v
                    )
                dd_html = ddisp.to_html(border=0, escape=False)
                blocks.append(f"""
                <div class="table-block" data-table="normal">
                    <h3>Worst 10 Drawdowns — {col}</h3>
                    {dd_html}
                </div>
                """)

        tables_html = "\n".join(blocks) if blocks else "<div style='padding:12px;color:#888;'>No tables selected.</div>"

        # ---- JS: align to widest table, clamp handle, persist after drag ----
        js = """
    <script>
    (function(){
    const root    = document.documentElement;
    const outer   = document.querySelector('.outer-split');
    const gutter  = document.getElementById('left-gutter');
    const wrap    = document.getElementById('tables-wrap');
    const content = document.getElementById('tables-content');
    const handle  = document.getElementById('right-handle');

    // ---------- helpers ----------
    function cssPx(name, fallback=0){
        const v = getComputedStyle(root).getPropertyValue(name).trim();
        if (!v) return fallback;
        return v.endsWith('px') ? parseFloat(v) : (parseFloat(v) || fallback);
    }
    function setVarPx(name, px){
        root.style.setProperty(name, px + 'px');
    }
    function setLeftRightPx(leftPx, rightPx){
        const total = leftPx + cssPx('--gutter', 10) + rightPx;
        const leftPct  = (leftPx  / total) * 100;
        const rightPct = (rightPx / total) * 100;
        root.style.setProperty('--left-col',  leftPct  + '%');
        root.style.setProperty('--right-col', rightPct + '%');
    }

    function widestTableWidth(){
        let maxW = 0;
        document.querySelectorAll('#tables-content table').forEach(t => {
        maxW = Math.max(maxW, t.scrollWidth);
        });
        return Math.max(maxW, 420); // minimum sensible width
    }

    function clampTablesW(px){
        const r = wrap.getBoundingClientRect();
        const minW = 420;
        const maxW = Math.max(minW, r.width - 12); // keep handle visible
        return Math.max(minW, Math.min(maxW, px));
    }

    function positionHandleAtTablesW(){
        // keep handle inside wrap always
        const r = wrap.getBoundingClientRect();
        const tablesW = cssPx('--tables-w', 720);
        const left = Math.max(0, Math.min(r.width - 8, tablesW));
        setVarPx('--handle-left', left);
    }

    function initToWidest(){
        const outerRect = outer.getBoundingClientRect();
        const minLeft   = 260; // px
        const gutterW   = cssPx('--gutter', 10);

        // 1) find the true widest table (monthly usually)
        const widest = widestTableWidth();

        // 2) we try to give the right pane enough width to fit 'widest'
        const maxRight = outerRect.width - minLeft - gutterW;
        const targetRight = Math.min(Math.max(360, widest + 12), maxRight);

        // 3) set left/right columns accordingly
        setLeftRightPx(outerRect.width - targetRight - gutterW, targetRight);

        // 4) set tables content width to exactly the widest (but clamp to wrap)
        const desiredTablesW = clampTablesW(widest);
        setVarPx('--tables-w', desiredTablesW);

        // 5) place handle exactly at the right edge of content
        positionHandleAtTablesW();
    }

    // ---------- left splitter (figures|tables) ----------
    let draggingLeft = false;
    gutter.addEventListener('mousedown', (e) => {
        draggingLeft = true; e.preventDefault();
        document.body.style.userSelect = 'none';
    });
    window.addEventListener('mousemove', (e) => {
        if (!draggingLeft) return;
        const rect = outer.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const minL = 260; // px
        const maxL = rect.width - 360; // keep space for tables
        const clamped = Math.max(minL, Math.min(maxL, x));
        const leftPx = clamped;
        const rightPx = rect.width - clamped - cssPx('--gutter', 10);
        setLeftRightPx(leftPx, rightPx);
        // after pane resize, keep handle visible by re-clamping tables-w
        const tw = clampTablesW(cssPx('--tables-w', 720));
        setVarPx('--tables-w', tw);
        positionHandleAtTablesW();
    });
    window.addEventListener('mouseup', () => {
        if (draggingLeft) {
        draggingLeft = false;
        document.body.style.userSelect = '';
        }
    });

    // ---------- right handle drag (controls content width) ----------
    let draggingRight = false;
    handle.addEventListener('mousedown', (e) => {
        draggingRight = true; e.preventDefault();
        document.body.style.userSelect = 'none';
    });
    window.addEventListener('mousemove', (e) => {
        if (!draggingRight) return;
        const r = wrap.getBoundingClientRect();
        let x = e.clientX - r.left;              // desired tables-w
        x = clampTablesW(x);                     // clamp to container
        setVarPx('--tables-w', x);
        positionHandleAtTablesW();               // keep handle aligned
    });
    window.addEventListener('mouseup', () => {
        if (draggingRight) {
        draggingRight = false;
        document.body.style.userSelect = '';
        }
    });

    // ---------- init + keep in sync on resize ----------
    window.addEventListener('load',   initToWidest);
    window.addEventListener('resize', initToWidest);

    // ---------- zoom modal ----------
    const modal = document.getElementById('zoom-modal');
    const modalImg = document.getElementById('zoom-image');
    document.querySelectorAll('img[data-zoom="1"]').forEach(img => {
        img.addEventListener('click', () => {
        modalImg.src = img.src;
        modal.classList.add('show');
        });
    });
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.id === 'zoom-image') modal.classList.remove('show');
    });
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') modal.classList.remove('show');
    });
    })();
    </script>
    """

        tz = datetime.now().astimezone().tzinfo
        generated_str = datetime.now().astimezone().strftime(f"%Y-%m-%d %H:%M:%S {tz}")

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
        <div class="sub">{self.date_range_str}</div>
        </div>
        <div class="meta">Generated on {generated_str}</div>

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