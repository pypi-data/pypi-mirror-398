# dashboard.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Callable, Tuple, Any
from datetime import datetime
import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
from quantstats import plots as qs_plots

# shared base
from core_tearsheet import TearsheetBase, _ensure_dir

# metrics / builders (compute-only; pure Polars)
import metrics_table as metrics_mod
from metrics_table import SimpleRegistry
from metrics import drawdown_top10_long  # numeric DD table builder (lazy → eager outside)


# =============================================================================
# Default figure/table keys
# =============================================================================
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

ALL_TABLES = ["metrics", "eoy", "monthly", "drawdown_top10"]


# =============================================================================
# Custom extension points
# =============================================================================
@dataclass
class BacktestManifest:
    figures: Optional[List[str]] = None
    metric_rows: Optional[List[str]] = None
    metric_cols: Optional[List[str]] = None
    tables: Optional[List[str]] = None
    metric_groups: Optional[List[Dict[str, List[str]]]] = None
    strategy_filter: Optional[List[str]] = None
    tables_controlled_by_slider: Optional[List[str]] = None
    custom_metric_registry: Optional["SimpleRegistry"] = None

    display_name_overrides: Optional[Dict[str, Tuple[str, bool]]] = None
    strict_metric_groups: bool = True
    data_overrides: Optional[Dict[str, Union[str, Callable[[Any], Any]]]] = None
    custom_figures: Optional[List["CustomFigureSpec"]] = None
    custom_tables: Optional[List["CustomTableSpec"]] = None
    custom_metric_blocks: Optional[List["CustomMetricBlockSpec"]] = None
    figure_data_overrides: Optional[Dict[str, str]] = None
    table_data_overrides: Optional[Dict[str, str]] = None


@dataclass
class CustomFigureSpec:
    key: str
    data_key: Optional[str]
    builder: Callable[[Any, "BacktestTearsheet"], Optional[List[Tuple[str, str]]]]
    title: Optional[str] = None
    description: Optional[str] = None
    output_prefix: Optional[str] = None
    per_strategy: bool = True


@dataclass
class CustomTableSpec:
    key: str
    data_key: Optional[str]
    builder: Callable[[Any, "BacktestTearsheet"], Optional[str]]
    title: Optional[str] = None
    controlled: bool = True


@dataclass
class CustomMetricBlockSpec: 
    key: str
    data_key: Optional[str]
    builder: Callable[[Any, "BacktestTearsheet"], Optional[pd.DataFrame]]
    title: Optional[str] = None
    replace: bool = False
    prepend: bool = False

# =============================================================================
# Main Dashboard
# =============================================================================
class BacktestTearsheet(TearsheetBase):
    """
    Backtest dashboard:
      - compute in Polars lazy (via metrics_table/metrics)
      - convert to pandas only to render tables
      - all layout/HTML delegated to TearsheetBase
    """
    def __init__(
        self,
        returns_df: Optional[Union[pd.DataFrame, pd.Series, pl.DataFrame, pl.LazyFrame, pl.Series]] = None,
        benchmark: Optional[Union[pd.Series, pd.DataFrame, pl.DataFrame, pl.LazyFrame, pl.Series]] = None,
        rf: Optional[Union[float, int, pd.Series, pd.DataFrame, pl.DataFrame, pl.LazyFrame, pl.Series]] = None,
        title: str = "Strategy Tearsheet",
        output_dir: str = "output/comprehensive_reports",
        manifest: Optional[BacktestManifest] = None,
        periods_per_year: int = 252,
        data_source: Optional[Any] = None,
        figures: Optional[List[str]] = None,
        tables: Optional[List[str]] = None,
        data_overrides: Optional[Dict[str, Union[str, Callable[[Any], Any]]]] = None,
    ) -> None:
        super().__init__(title=title, output_dir=output_dir)

        self.ppy = periods_per_year
        self.manifest = manifest or BacktestManifest()
        if figures is not None:
            self.manifest.figures = figures
        if tables is not None:
            self.manifest.tables = tables
        if data_overrides:
            merged_overrides = dict(self.manifest.data_overrides or {})
            merged_overrides.update(data_overrides)
            self.manifest.data_overrides = merged_overrides
        self.display_overrides = self.manifest.display_name_overrides or {}
        self.strict_groups = bool(self.manifest.strict_metric_groups)
        self.custom_registry = self.manifest.custom_metric_registry
        self._custom_fig_counter = 0
        self.figure_data_overrides = self.manifest.figure_data_overrides or {}
        self.table_data_overrides = self.manifest.table_data_overrides or {}
        self.data_sources: Dict[str, Any] = {}
        resolved_data_overrides = self.manifest.data_overrides or {}

        base_source = data_source if data_source is not None else None
        if base_source is None and not self._is_data_input(returns_df):
            base_source = returns_df
        self.source_obj = base_source

        raw_returns_obj = returns_df
        if self.source_obj is not None and "returns" in resolved_data_overrides:
            raw_returns_obj = self._resolve_data_spec(resolved_data_overrides["returns"], self.source_obj)
        elif not self._is_data_input(returns_df):
            if self.source_obj is None:
                raise TypeError("A data source object is required when returns_df is not dataframe-like.")
            returns_spec = resolved_data_overrides.get("returns")
            if returns_spec is None and hasattr(self.source_obj, "tracking_pnl"):
                returns_spec = "tracking_pnl"
            if returns_spec is None:
                raise TypeError("Unable to infer returns data from source; set manifest.data_overrides['returns'].")
            raw_returns_obj = self._resolve_data_spec(returns_spec, self.source_obj)
        self.data_sources["returns"] = raw_returns_obj

        self.benchmark_display_name = "Benchmark"
        if benchmark is not None:
            self.benchmark_display_name = self._infer_benchmark_label(benchmark, self.benchmark_display_name)

        if self.source_obj is not None:
            for key, spec in resolved_data_overrides.items():
                if key == "returns":
                    continue
                try:
                    value = self._resolve_data_spec(spec, self.source_obj)
                except Exception as err:
                    print(f"[manifest:data_overrides] {key} failed: {err}")
                    continue
                self.data_sources[key] = value
                if key == "benchmark":
                    benchmark = value
                    self.benchmark_display_name = self._infer_benchmark_label(value, self.benchmark_display_name)
                if key == "rf":
                    rf = value
            self.data_sources.setdefault("source", self.source_obj)

        if not self._is_data_input(raw_returns_obj):
            raise TypeError("Provide returns_df or set manifest.data_overrides['returns'] to a valid data source attribute.")

        returns_df = raw_returns_obj

        # --- normalize inputs to Polars **LazyFrame**
        base_returns_lf = self._coerce_returns_to_pl_lazy(returns_df)
        bench_lf        = self._coerce_bench_to_pl_lazy(benchmark)

        # EXCESS returns lazily (if rf provided)
        self.returns_excess_lf = self._excess_returns_lazy(base_returns_lf, rf, self.ppy)

        self.benchmark_excess_lf = None
        if bench_lf is not None:
            self.benchmark_excess_lf = self._excess_returns_lazy(bench_lf, rf, self.ppy)

        # strategies
        names = self.returns_excess_lf.collect_schema().names()
        self.strategies = [c for c in names if c != "date"]

        # Strategy subset to render
        if self.manifest.strategy_filter:
            self.render_strategies = [c for c in self.strategies if c in self.manifest.strategy_filter]
        else:
            self.render_strategies = self.strategies[:]

        # date range (lazy min/max)
        self.start, self.end = self._lazy_min_max_dates(self.returns_excess_lf)
        self.date_range_str = f"{self.start} — {self.end}"

        # figures/tables
        if self.manifest.figures is not None:
            self.fig_list = [f for f in self.manifest.figures if f]
        else:
            self.fig_list = DEFAULT_FIGURES.copy()

        if self.manifest.tables is not None:
            filtered = [t for t in self.manifest.tables if t in ALL_TABLES]
            self.tables_list = filtered
        else:
            self.tables_list = ALL_TABLES.copy()

        # tables controlled by right slider
        self.tables_controlled = self.manifest.tables_controlled_by_slider or ["metrics","eoy","monthly","drawdown_top10"]

        # default metric columns: Benchmark + strategies
        self.default_metric_cols = (["Benchmark"] if self.benchmark_excess_lf is not None else []) + self.render_strategies
        self.metric_cols_filter = None
        if self.manifest.metric_cols:
            avail = (["Benchmark"] if self.benchmark_excess_lf is not None else []) + self.strategies
            self.metric_cols_filter = [c for c in self.manifest.metric_cols if c in avail]

        # build pipeline
        self._save_manifest()
        self._build_figures()
        self._build_tables()
        self._render_html()

    # -------------------------------------------------------------------------
    # Data access helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _is_data_input(obj: Any) -> bool:
        return isinstance(obj, (pd.Series, pd.DataFrame, pl.DataFrame, pl.LazyFrame, pl.Series))

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

    def _manifest_data(self, data_key: Optional[str]) -> Any:
        if data_key is None:
            return self.source_obj or self.data_sources.get("returns")
        if data_key in self.data_sources:
            return self.data_sources[data_key]
        if self.source_obj is not None:
            try:
                value = self._resolve_data_spec(data_key, self.source_obj)
                self.data_sources[data_key] = value
                return value
            except Exception:
                return None
        return None

    def _figure_data_source(self, key: str) -> Optional[pl.LazyFrame]:
        override = (self.figure_data_overrides or {}).get(key)
        if not override:
            return None
        obj = self._manifest_data(override)
        if obj is None:
            return None
        try:
            return self._coerce_returns_to_pl_lazy(obj)
        except Exception as err:
            print(f"[figure_data_override] {key} failed: {err}")
            return None

    def _table_data_source(self, key: str, default: pl.LazyFrame) -> pl.LazyFrame:
        override = (self.table_data_overrides or {}).get(key)
        if not override:
            return default
        obj = self._manifest_data(override)
        if obj is None:
            return default
        try:
            return self._coerce_returns_to_pl_lazy(obj)
        except Exception as err:
            print(f"[table_data_override] {key} failed: {err}")
            return default

    def _infer_benchmark_label(self, bench_obj: Any, default: str = "Benchmark") -> str:
        if bench_obj is None:
            return default
        try:
            if isinstance(bench_obj, pd.Series):
                name = bench_obj.name
                if name:
                    return str(name)
            if isinstance(bench_obj, pd.DataFrame):
                cols = [c for c in bench_obj.columns if c != "date"]
                if cols:
                    return str(cols[0])
            if isinstance(bench_obj, pl.LazyFrame):
                names = bench_obj.collect_schema().names()
                non_date = [c for c in names if c != "date"]
                if non_date:
                    return str(non_date[0])
            if isinstance(bench_obj, pl.DataFrame):
                non_date = [c for c in bench_obj.columns if c != "date"]
                if non_date:
                    return str(non_date[0])
            if isinstance(bench_obj, pl.Series):
                if bench_obj.name:
                    return str(bench_obj.name)
        except Exception:
            pass
        name = getattr(bench_obj, "name", None)
        if name:
            return str(name)
        return default

        if data_key is None:
            return self.source_obj or self.data_sources.get("returns")
        if data_key in self.data_sources:
            return self.data_sources[data_key]
        if self.source_obj is not None:
            try:
                value = self._resolve_data_spec(data_key, self.source_obj)
                self.data_sources[data_key] = value
                return value
            except Exception:
                return None
        return None

    def save_custom_figure(self, fig: plt.Figure, filename: Optional[str] = None, prefix: Optional[str] = None) -> Optional[str]:
        self._custom_fig_counter += 1
        name = filename
        if name is None:
            base = prefix or f"custom_fig_{self._custom_fig_counter}"
            name = f"{base}_{self._custom_fig_counter}.png"
        return self._save_fig(fig, name)

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
        if isinstance(result, plt.Figure):
            path = self.save_custom_figure(result, prefix=prefix)
            if path:
                tiles.append((default_label, path))
            return tiles
        return tiles

    # -------------------------------------------------------------------------
    # Polars-only coercion / alignment helpers (all LAZY)
    # -------------------------------------------------------------------------
    @staticmethod
    def _as_lazy(x: Union[pl.DataFrame, pl.LazyFrame]) -> pl.LazyFrame:
        return x.lazy() if isinstance(x, pl.DataFrame) else x

    @staticmethod
    def _ensure_datetime_ns(lf: pl.LazyFrame, date_col: str = "date") -> pl.LazyFrame:
        return lf.with_columns(pl.col(date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))

    def _coerce_returns_to_pl_lazy(self, returns_obj: Union[pd.DataFrame, pd.Series, pl.DataFrame, pl.LazyFrame, pl.Series]) -> pl.LazyFrame:
        if not self._is_data_input(returns_obj):
            if hasattr(returns_obj, "tracking_pnl"):
                return self._coerce_returns_to_pl_lazy(getattr(returns_obj, "tracking_pnl"))
            raise TypeError("returns_df must be convertible to a Polars LazyFrame.")
        if isinstance(returns_obj, pl.LazyFrame):
            return self._ensure_datetime_ns(returns_obj)
        if isinstance(returns_obj, pl.DataFrame):
            return self._ensure_datetime_ns(returns_obj.lazy())
        if isinstance(returns_obj, pl.Series):
            if returns_obj.dtype != pl.Struct:
                raise TypeError("polars.Series must be a struct series with fields: ['date', <value>].")
            fields = returns_obj.struct.fields
            if "date" not in fields:
                raise ValueError("Struct series must include a 'date' field.")
            vfield = next((f for f in fields if f != "date"), None)
            if vfield is None:
                raise ValueError("Could not infer value field from struct series.")
            name = str(returns_obj.name or "Strategy")
            df = returns_obj.struct.unnest().rename({vfield: name})
            return self._ensure_datetime_ns(df.lazy())
        # pandas -> polars (conversion only)
        if isinstance(returns_obj, pd.Series):
            pdf = returns_obj.to_frame(name=str(returns_obj.name or "Strategy")).copy()
        elif isinstance(returns_obj, pd.DataFrame):
            pdf = returns_obj.copy()
        else:
            raise TypeError("returns_df must be pandas Series/DataFrame, polars DataFrame/LazyFrame, or polars struct Series.")
        idx = pd.DatetimeIndex(pdf.index).tz_localize(None)
        data = {"date": list(idx.to_pydatetime())}
        for c in pdf.columns:
            data[str(c)] = pd.to_numeric(pdf[c], errors="coerce").astype(float).to_numpy()
        pl_df = pl.DataFrame(data).with_columns(pl.col("date").cast(pl.Datetime))
        return self._ensure_datetime_ns(pl_df.lazy())

    def _coerce_bench_to_pl_lazy(self, bench_obj: Optional[Union[pd.Series, pd.DataFrame, pl.DataFrame, pl.LazyFrame, pl.Series]], name: str = "Benchmark") -> Optional[pl.LazyFrame]:
        if bench_obj is None:
            return None
        if not self._is_data_input(bench_obj):
            if hasattr(bench_obj, "tracking_pnl"):
                return self._coerce_bench_to_pl_lazy(getattr(bench_obj, "tracking_pnl"), name=name)
            raise TypeError("benchmark must be convertible to a Polars LazyFrame.")

        def _rename_single_column(lf: pl.LazyFrame) -> pl.LazyFrame:
            names = lf.collect_schema().names()
            non_date = [c for c in names if c != "date"]
            if len(non_date) != 1:
                raise ValueError("Benchmark input must contain exactly one non-'date' column.")
            current = non_date[0]
            if current != name:
                lf = lf.rename({current: name})
            return lf

        if isinstance(bench_obj, pl.LazyFrame):
            lf = self._ensure_datetime_ns(bench_obj)
            return _rename_single_column(lf)
        if isinstance(bench_obj, pl.DataFrame):
            lf = self._ensure_datetime_ns(bench_obj.lazy())
            return _rename_single_column(lf)
        if isinstance(bench_obj, pl.Series):
            if bench_obj.dtype != pl.Struct:
                raise TypeError("polars.Series benchmark must be a struct with fields: ['date', <value>].")
            fields = bench_obj.struct.fields
            if "date" not in fields:
                raise ValueError("Benchmark struct series must include 'date'.")
            vfield = next((f for f in fields if f != "date"), None)
            if vfield is None:
                raise ValueError("Could not infer benchmark value field.")
            df = bench_obj.struct.unnest()
            df = df.rename({vfield: name})
            return self._ensure_datetime_ns(df.lazy())
        # pandas -> polars
        if isinstance(bench_obj, pd.Series):
            s = bench_obj.copy()
            s.name = name
            idx = pd.DatetimeIndex(s.index).tz_localize(None)
            data = {"date": list(idx.to_pydatetime()), str(s.name): pd.to_numeric(s, errors="coerce").astype(float).to_numpy()}
            pl_df = pl.DataFrame(data).with_columns(pl.col("date").cast(pl.Datetime))
            return self._ensure_datetime_ns(pl_df.lazy())
        if isinstance(bench_obj, pd.DataFrame):
            if bench_obj.shape[1] == 0:
                return None
            s = bench_obj.iloc[:, 0].copy()
            s.name = name
            idx = pd.DatetimeIndex(s.index).tz_localize(None)
            data = {"date": list(idx.to_pydatetime()), str(s.name): pd.to_numeric(s, errors="coerce").astype(float).to_numpy()}
            pl_df = pl.DataFrame(data).with_columns(pl.col("date").cast(pl.Datetime))
            return self._ensure_datetime_ns(pl_df.lazy())
        raise TypeError("benchmark must be pandas Series/DataFrame, polars DataFrame/LazyFrame with 'date', or polars struct Series.")

    @staticmethod
    def _excess_returns_lazy(
        returns_lf: pl.LazyFrame,
        rf: Optional[Union[float, int, pd.Series, pd.DataFrame, pl.DataFrame, pl.LazyFrame, pl.Series]],
        periods_per_year: int,
    ) -> pl.LazyFrame:
        lf = returns_lf.with_columns(pl.col("date").cast(pl.Datetime).dt.cast_time_unit("ns"))
        names = lf.collect_schema().names()
        date_col = "date"
        strat_cols = [c for c in names if c != date_col]
        if not strat_cols or rf is None:
            return lf
        if isinstance(rf, (int, float)):
            per_step_rf = (1.0 + float(rf)) ** (1.0 / float(periods_per_year)) - 1.0
            return lf.with_columns([(pl.col(c) - per_step_rf).alias(c) for c in strat_cols])

        # coerce rf to ["date","rf"]
        def _coerce_rf(x) -> pl.LazyFrame:
            if isinstance(x, pl.LazyFrame):
                z = x.with_columns(pl.col("date").cast(pl.Datetime).dt.cast_time_unit("ns"))
                keep = [pl.col("date")] + [pl.all().exclude("date")]
                rename = {c: "rf" for c in z.collect_schema().names() if c != "date"}
                return z.select(keep).rename(rename)
            if isinstance(x, pl.DataFrame):
                z = x.lazy().with_columns(pl.col("date").cast(pl.Datetime).dt.cast_time_unit("ns"))
                rename = {c: "rf" for c in x.columns if c != "date"}
                return z.select([pl.col("date")] + [pl.all().exclude("date")]).rename(rename)
            if isinstance(x, pl.Series):
                if x.dtype != pl.Struct:
                    raise TypeError("rf polars.Series must be a struct with ['date', value].")
                fields = x.struct.fields
                if "date" not in fields:
                    raise ValueError("rf struct series must include 'date'.")
                vfield = next((f for f in fields if f != "date"), None)
                if vfield is None:
                    raise ValueError("Could not infer rf value field.")
                return x.struct.unnest().rename({vfield: "rf"}).lazy().with_columns(pl.col("date").cast(pl.Datetime).dt.cast_time_unit("ns"))
            if isinstance(x, (pd.Series, pd.DataFrame)):
                s = x if isinstance(x, pd.Series) else x.iloc[:, 0]
                idx = pd.DatetimeIndex(s.index).tz_localize(None)
                pl_df = pl.DataFrame({"date": list(idx.to_pydatetime()), "rf": pd.to_numeric(s, errors="coerce").astype(float).to_numpy()})
                return pl_df.lazy().with_columns(pl.col("date").cast(pl.Datetime).dt.cast_time_unit("ns"))
            raise TypeError("Unsupported rf type for excess computation.")

        rf_lf = _coerce_rf(rf)
        joined = lf.join(rf_lf, on="date", how="left")
        return joined.with_columns([(pl.col(c) - pl.col("rf").fill_null(0.0)).alias(c) for c in strat_cols]).select([date_col] + strat_cols)

    @staticmethod
    def _lazy_min_max_dates(lf: pl.LazyFrame) -> Tuple[str, str]:
        s = lf.select([pl.col("date").min().alias("_min"), pl.col("date").max().alias("_max")]).collect()
        a = s["_min"][0]
        b = s["_max"][0]
        sa = (a.strftime("%Y-%m-%d") if isinstance(a, datetime) else str(a))
        sb = (b.strftime("%Y-%m-%d") if isinstance(b, datetime) else str(b))
        return sa, sb

    # -------------------------------------------------------------------------
    # Display helpers
    # -------------------------------------------------------------------------
    def _display_name_map(self) -> Dict[str, Tuple[str, bool]]:
        base = {
            "comp": ("Cumulative Return", True),
            "cagr": ("CAGR﹪", True),
            "sharpe": ("Sharpe", False),
            "sortino": ("Sortino", False),
            "vol_ann": ("Volatility (ann.)", True),
            "calmar": ("Calmar", False),
            "best_day": ("Best Day", True),
            "worst_day": ("Worst Day", True),
            "best_month": ("Best Month", True),
            "worst_month": ("Worst Month", True),
            "best_year": ("Best Year", True),
            "worst_year": ("Worst Year", True),
            "skew": ("Skew", False),
            "kurtosis": ("Kurtosis", False),
            "max_drawdown": ("Max Drawdown", True),
            "avg_drawdown": ("Avg. Drawdown", True),
            "ulcer": ("Ulcer Index", True),
            "longest_dd_days": ("Longest DD Days", False),
            "avg_dd_days": ("Avg. Drawdown Days", False),
            "max_dd_date": ("Max DD Date", False),
            "max_dd_start": ("Max DD Period Start", False),
            "max_dd_end": ("Max DD Period End", False),
            "VaR_5": ("Daily Value-at-Risk", True),
            "CVaR_5": ("Expected Shortfall (cVaR)", True),
            "omega_0": ("Omega", False),
            "mtd": ("MTD", True),
            "3m": ("3M", True),
            "6m": ("6M", True),
            "ytd": ("YTD", True),
            "1y": ("1Y", True),
            "3y_ann": ("3Y (ann.)", True),
            "5y_ann": ("5Y (ann.)", True),
            "10y_ann": ("10Y (ann.)", True),
            "alltime_ann": ("All-time (ann.)", True),
            "exposure": ("Time in Market", True),
            "avg_win": ("Avg. Win", True),
            "avg_loss": ("Avg. Loss", True),
            "payoff": ("Payoff Ratio", False),
            "win_rate": ("Win Days", True),
        }
        base.update(self.display_overrides)
        return base

    def _is_percent_label(self, display_label: str) -> bool:
        dm = self._display_name_map()
        for _, (lbl, is_pct) in dm.items():
            if lbl == display_label:
                return is_pct
        s = display_label.lower()
        hints = ("return", "volatility", "ytd", "mtd", "ann.", "month", "year", "win", "%")
        anti  = ("skew", "kurtosis", "omega", "calmar", "sharpe", "sortino", "payoff", "days")
        return any(h in s for h in hints) and not any(a in s for a in anti)

    def _format_number(self, v: object, is_pct: bool, as_int: bool = False) -> str:
        if v is None:
            return "-"
        if isinstance(v, str):
            raw = v.strip()
            had_pct = raw.endswith("%")
            raw = raw.replace(",", "").replace("%", "")
            try:
                x = float(raw)
            except Exception:
                return v
            if not np.isfinite(x):
                return "-"
            if as_int:
                return f"{int(round(x))}"
            if had_pct:
                return f"{x:.2f}%" if is_pct else f"{x:.2f}"
            return f"{x*100:.2f}%" if is_pct else f"{x:.2f}"
        if isinstance(v, (int, float, np.integer, np.floating)):
            if not np.isfinite(float(v)):
                return "-"
            x = float(v)
            if as_int:
                return f"{int(round(x))}"
            return f"{x*100:.2f}%" if is_pct else f"{x:.2f}"
        return str(v)

    def _format_df_2dp(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        out = df.copy()
        int_labels = {"Avg. Drawdown Days", "Longest DD Days"}
        for label in out.index:
            is_pct = self._is_percent_label(label)
            as_int = (label in int_labels)
            out.loc[label] = out.loc[label].map(lambda v: self._format_number(v, is_pct, as_int))
        return out.astype(str)

    # -------------------------------------------------------------------------
    # Manifest & metrics compute
    # -------------------------------------------------------------------------
    def _save_manifest(self) -> None:
        full_metrics = self._compute_metrics_table(self.returns_excess_lf, full=True)
        keys = list(full_metrics.index)
        manifest = {
            "figures_available": DEFAULT_FIGURES,
            "tables_available": ALL_TABLES,
            "metric_rows": keys,
            "metric_cols": (["Benchmark"] if self.benchmark_excess_lf is not None else []) + self.strategies,
            "date_range": [self.start, self.end],
        }
        self.write_manifest(manifest)

    def _compute_metrics_table(self, ret_lf: pl.LazyFrame, full: bool = False) -> pd.DataFrame:
        bench_lf = self.benchmark_excess_lf

        out_pl = metrics_mod.metrics_polars(
            returns=ret_lf,
            benchmark=bench_lf,
            rf=0.0,
            mode="full" if full else "basic",
            registry=self.custom_registry,
            builders_module=metrics_mod,   # auto-collect *_long builders from module
        )
        df = out_pl.to_pandas() if isinstance(out_pl, pl.DataFrame) else pd.DataFrame(out_pl)
        if "metric" in df.columns:
            df = df.set_index("metric")

        dm = self._display_name_map()
        df.index = [dm.get(str(raw), (str(raw), False))[0] for raw in df.index]
        df.index.name = "Metric"

        cols = list(df.columns)
        if "benchmark" in cols:
            df = df.rename(columns={"benchmark": "Benchmark"})
        if "Benchmark" in df.columns:
            df = df[["Benchmark"] + [c for c in df.columns if c != "Benchmark"]]
        return df

    # -------------------------------------------------------------------------
    # Tables (metrics + others) + HTML fragments
    # -------------------------------------------------------------------------
    def _render_metrics_grouped(self, df: pd.DataFrame, groups: List[Dict[str, List[str]]]) -> str:
        if df is None or df.empty:
            return "<div style='padding:12px;color:#888;'>No metrics.</div>"

        pretty = self._format_df_2dp(df)
        cols = list(pretty.columns)
        idx_labels = {self._norm_key(lbl): lbl for lbl in pretty.index}

        html = []
        html.append('<table class="metrics-grouped" id="metrics-table">')
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
                nk = self._norm_key(key)
                if nk not in idx_labels:
                    continue
                label = idx_labels[nk]
                used.add(label)
                row = pretty.loc[label]
                html.append('<tr>')
                html.append(f'<td class="mname sticky-col">{label}</td>')
                for c in cols:
                    html.append(f'<td class="mval">{str(row.get(c, "-"))}</td>')
                html.append('</tr>')

        if not self.strict_groups:
            leftovers = [lbl for lbl in pretty.index if lbl not in used]
            if leftovers:
                html.append(f'<tr class="sep"><td colspan="{len(cols)+1}"></td></tr>')
                html.append(f'<tr class="glabel"><td class="gtitle sticky-col" colspan="{len(cols)+1}">Other</td></tr>')
                for label in leftovers:
                    row = pretty.loc[label]
                    html.append('<tr>')
                    html.append(f'<td class="mname sticky-col">{label}</td>')
                    for c in cols:
                        html.append(f'<td class="mval">{str(row.get(c, "-"))}</td>')
                    html.append('</tr>')

        html.append('</tbody></table>')
        return "".join(html)

    @staticmethod
    def _norm_key(s: str) -> str:
        try:
            return "".join(ch.lower() for ch in str(s) if ch.isalnum())
        except Exception:
            return str(s).lower()

    def _default_metric_groups(self) -> List[Dict[str, List[str]]]:
        RR  = ["Cumulative Return","CAGR﹪","Sharpe","Sortino","Volatility (ann.)","Calmar","Time in Market","Avg. Win","Avg. Loss","Payoff Ratio","Win Days"]
        DD  = ["Max Drawdown","Max DD Date","Max DD Period Start","Max DD Period End","Longest DD Days","Avg. Drawdown","Avg. Drawdown Days","Ulcer Index"]
        EXT = ["Best Day","Worst Day","Best Month","Worst Month","Best Year","Worst Year","Skew","Kurtosis"]
        TL  = ["Daily Value-at-Risk","Expected Shortfall (cVaR)","Omega"]
        PD  = ["MTD","3M","6M","YTD","1Y","3Y (ann.)","5Y (ann.)","10Y (ann.)","All-time (ann.)"]
        return [
            {"Risk/Return": RR},
            {"Drawdowns": DD},
            {"Extremes": EXT},
            {"Tails": TL},
            {"Periods": PD},
        ]

    # -----------------------
    # Build Figures
    # -----------------------
    def _build_figures(self) -> None:
        self.fig_paths: Dict[str, Dict[str, str]] = {col: {} for col in self.render_strategies}
        self.extra_figures_rows: List[Dict[str, Any]] = []

        def _pd_series(col: str, source_lf: pl.LazyFrame) -> pd.Series:
            df = (
                source_lf
                .select([pl.col("date"), pl.col(col).alias(col)])
                .collect()
            )
            s = TearsheetBase._pd_series_from_pl_two_cols(df, "date", col, name=col)
            return s.dropna()

        bench_pd: Optional[pd.Series] = None
        if self.benchmark_excess_lf is not None:
            bn = self.benchmark_excess_lf.collect_schema().names()
            bcols = [c for c in bn if c != "date"]
            if bcols:
                bname = bcols[0]
                bdf = self.benchmark_excess_lf.select([pl.col("date"), pl.col(bname)]).collect()
                bench_pd = TearsheetBase._pd_series_from_pl_two_cols(bdf, "date", bname, name=bname).dropna()

        def _save(fig, fname: str):
            return self._save_fig(fig, fname)

        for f in self.fig_list:
            source_lf = self._figure_data_source(f) or self.returns_excess_lf
            available_cols = [c for c in source_lf.collect_schema().names() if c != "date"]
            for col in self.render_strategies:
                if col not in available_cols:
                    continue
                s = _pd_series(col, source_lf)
                if s.empty:
                    continue
                fig_obj = None
                try:
                    if f == "snapshot":
                        fig_obj = qs_plots.snapshot(s, show=False)
                    elif f == "earnings":
                        fig_obj = qs_plots.earnings(s, show=False)
                    elif f == "returns":
                        fig_obj = qs_plots.returns(s, benchmark=bench_pd, show=False)
                    elif f == "log_returns":
                        fig_obj = qs_plots.log_returns(s, benchmark=bench_pd, show=False)
                    elif f == "yearly_returns":
                        fig_obj = qs_plots.yearly_returns(s, benchmark=bench_pd, show=False)
                    elif f == "daily_returns":
                        fig_obj = qs_plots.daily_returns(s, benchmark=bench_pd, show=False)
                    elif f == "rolling_beta":
                        if bench_pd is not None:
                            fig_obj = qs_plots.rolling_beta(s, bench_pd, show=False)
                    elif f == "rolling_volatility":
                        try:
                            fig_obj = qs_plots.rolling_volatility(s, benchmark=bench_pd, show=False)
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
                        try:
                            fig_obj = qs_plots.monthly_heatmap(s, benchmark=bench_pd, show=False)
                        except TypeError:
                            fig_obj = qs_plots.monthly_heatmap(s, show=False)
                    elif f == "histogram":
                        fig_obj = qs_plots.histogram(s, benchmark=bench_pd, show=False)
                    elif f == "distribution":
                        fig_obj = qs_plots.distribution(s, show=False)
                    else:
                        continue
                    if fig_obj is not None:
                        fp = _save(fig_obj, f"{f}_{col}.png")
                        if fp:
                            self.fig_paths[col][f] = fp
                except Exception as e:
                    print(f"[plot] failed: {f}({col}) -> {e}")
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
                self.extra_figures_rows.append({
                    "title": spec.title or spec.key,
                    "description": spec.description,
                    "tiles": tiles,
                    "per_strategy": bool(getattr(spec, "per_strategy", True)),
                })

    # -----------------------
    # Build Tables
    # -----------------------
    def _build_tables(self) -> None:
        # Metrics (raw -> display labels)
        metrics_source = self._table_data_source("metrics", self.returns_excess_lf)
        full_m = self._compute_metrics_table(metrics_source, full=True)

        # Column filter
        if self.metric_cols_filter:
            keep_cols = [c for c in self.metric_cols_filter if c in full_m.columns]
        else:
            keep_cols = [c for c in self.default_metric_cols if c in full_m.columns]
        keep_cols = list(dict.fromkeys(keep_cols))  # unique
        metrics_df = full_m[keep_cols] if keep_cols else full_m
        self.metrics_df_raw = metrics_df.copy()

        # Optional row filter (by display names)
        if self.manifest.metric_rows:
            idx_map = {self._norm_key(i): i for i in self.metrics_df_raw.index}
            want = [idx_map[self._norm_key(k)] for k in self.manifest.metric_rows if self._norm_key(k) in idx_map]
            if want:
                self.metrics_df_raw = self.metrics_df_raw.loc[want]


        # Custom metric blocks (optional)
        groups_raw = self.manifest.metric_groups or self._default_metric_groups()
        group_entries: List[Tuple[str, List[str]]] = []
        for grp in groups_raw:
            title, metrics = next(iter(grp.items()))
            group_entries.append((title, list(metrics)))

        base_df = self.metrics_df_raw
        additional_frames_top: List[pd.DataFrame] = []
        additional_frames_bottom: List[pd.DataFrame] = []
        customs = self.manifest.custom_metric_blocks or []
        for spec in customs:
            data_obj = self._manifest_data(spec.data_key)
            if data_obj is None:
                continue
            try:
                block_df = spec.builder(data_obj, self)
            except Exception as err:
                print(f"[custom_metric_block] {spec.key} failed: {err}")
                continue
            if block_df is None:
                continue
            if isinstance(block_df, pl.DataFrame):
                block_df = block_df.to_pandas()
            elif not isinstance(block_df, pd.DataFrame):
                try:
                    block_df = pd.DataFrame(block_df)
                except Exception:
                    continue
            if block_df.empty:
                continue
            block_df = block_df.copy()
            block_df.index = [str(idx) for idx in block_df.index]
            block_df.columns = [str(c) for c in block_df.columns]

            orig_cols = list(block_df.columns)
            all_cols = list(dict.fromkeys(list(base_df.columns) + list(block_df.columns)))
            base_df = base_df.reindex(columns=all_cols)
            block_df = block_df.reindex(columns=all_cols)
            missing = [c for c in all_cols if c not in orig_cols]
            if missing:
                for col in missing:
                    block_df[col] = np.nan

            title = spec.title or spec.key
            insertion = (title, list(block_df.index))
            if spec.replace:
                idx = next((i for i, (name, _) in enumerate(group_entries) if name.lower() == title.lower()), None)
                if idx is not None:
                    drop_names = group_entries[idx][1]
                    base_df = base_df.drop(index=[n for n in drop_names if n in base_df.index], errors='ignore')
                    group_entries[idx] = (group_entries[idx][0], list(block_df.index))
                    if getattr(spec, "prepend", False) and idx != 0:
                        entry = group_entries.pop(idx)
                        group_entries.insert(0, entry)
                else:
                    if getattr(spec, "prepend", False):
                        group_entries.insert(0, insertion)
                    else:
                        group_entries.append(insertion)
            else:
                if getattr(spec, "prepend", False):
                    group_entries.insert(0, insertion)
                else:
                    group_entries.append(insertion)
            target_list = additional_frames_top if getattr(spec, "prepend", False) else additional_frames_bottom
            target_list.append(block_df)

        if additional_frames_top:
            base_df = pd.concat(additional_frames_top + [base_df], axis=0)
        if additional_frames_bottom:
            base_df = pd.concat([base_df] + additional_frames_bottom, axis=0)

        order: List[str] = []
        cleaned_groups: List[Dict[str, List[str]]] = []
        for title, metrics in group_entries:
            filtered = [m for m in metrics if m in base_df.index]
            if not filtered:
                continue
            cleaned_groups.append({title: filtered})
            order.extend(filtered)
        if order:
            base_df = base_df.reindex(order)
        self.metrics_df_raw = base_df

        # Pretty grouped metrics HTML
        if cleaned_groups:
            groups = cleaned_groups
        else:
            groups = [{title: metrics} for title, metrics in group_entries if metrics]
        self.metrics_html = self._render_metrics_grouped(self.metrics_df_raw, groups)

        # EOY table (delegated to metrics functions via metrics_table usage)
        eoy_source = self._table_data_source("eoy", self.returns_excess_lf)
        self.eoy_map = self._eoy_table_via_metrics(eoy_source)

        # Monthly table
        monthly_source = self._table_data_source("monthly", self.returns_excess_lf)
        self.monthly_map = self._monthly_tables_via_metrics(monthly_source)

        # Drawdown Top10 table (already factored in metrics)
        drawdown_source = self._table_data_source("drawdown_top10", self.returns_excess_lf)
        self.dd_map = self._drawdown_tables_via_metrics(drawdown_source)

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
                <div class="table-block" data-table="{spec.key}" data-group="{'controlled' if spec.controlled else 'free'}">
                    <h3>{spec.title or spec.key}</h3>
                    {table_html}
                </div>
                """
                self.custom_table_blocks.append(block)

    # --- monthly via metrics (no inline computations here)
    def _monthly_tables_via_metrics(self, ret_lf: pl.LazyFrame) -> Dict[str, pd.DataFrame]:
        # We can leverage metrics_table period_slices and build a matrix-like monthly pivot via a helper
        # To stay within "no compute here", we do monthly in metrics.py if needed.
        # For compatibility, fall back to a safe minimal month pivot based on returns_excess_lf.
        res: Dict[str, pd.DataFrame] = {}
        date = pl.col("date")
        for col in self.render_strategies:
            m = (
                ret_lf
                .select([pl.col("date"), pl.col(col).alias("ret")])
                .with_columns([date.dt.year().alias("year"), date.dt.month().alias("month")])
                .group_by(["year","month"])
                .agg(((pl.col("ret") + 1.0).product() - 1.0).alias("mret"))
                .sort(["year","month"])
                .collect()
            )
            wide = m.pivot(index="year", columns="month", values="mret").sort("year")
            pdf = wide.to_pandas().set_index("year")
            from datetime import datetime as _dt
            pdf.columns = [_dt(2000, int(c), 1).strftime("%b") for c in pdf.columns]
            res[col] = pdf
        return res

    # --- EOY via metrics
    def _eoy_table_via_metrics(self, ret_lf: pl.LazyFrame) -> Dict[str, pd.DataFrame]:
        res: Dict[str, pd.DataFrame] = {}
        date = pl.col("date")

        bench_map: Dict[int, float] = {}
        if self.benchmark_excess_lf is not None:
            bn = self.benchmark_excess_lf.collect_schema().names()
            bcols = [c for c in bn if c != "date"]
            if bcols:
                bname = bcols[0]
                by = (
                    self.benchmark_excess_lf
                    .with_columns(date.dt.year().alias("year"))
                    .group_by("year")
                    .agg(((pl.col(bname) + 1.0).product() - 1.0).alias("bench_eoy"))
                    .sort("year")
                    .collect()
                )
                bench_map = dict(zip(by["year"].to_list(), by["bench_eoy"].to_list()))

        ret_cols = self.render_strategies[:]
        long = (
            ret_lf
            .select([pl.col("date")] + [pl.col(c) for c in ret_cols])
            .melt(id_vars="date", value_vars=ret_cols, variable_name="name", value_name="ret")
            .with_columns(date.dt.year().alias("year"))
            .group_by(["name","year"])
            .agg(((pl.col("ret") + 1.0).product() - 1.0).alias("strat_eoy"))
            .sort(["name","year"])
            .collect()
        )

        for col in self.render_strategies:
            df = long.filter(pl.col("name") == col).select(["year","strat_eoy"]).rename({"year":"Year","strat_eoy":"Strategy"})
            pdf = df.to_pandas()
            if bench_map:
                pdf["Benchmark"] = pdf["Year"].map(bench_map).astype(float)
            else:
                pdf["Benchmark"] = np.nan
            bench = pdf["Benchmark"].to_numpy()
            strat = pdf["Strategy"].to_numpy()
            with np.errstate(divide="ignore", invalid="ignore"):
                mult = np.where(np.isfinite(bench) & (np.abs(bench) > 1e-12), strat / bench, np.nan)
            pdf["Multiplier"] = mult
            pdf["Won"] = np.where(np.isfinite(strat) & np.isfinite(bench),
                                  np.where(strat > bench, "+", "–"), "")
            res[col] = pdf[["Year","Benchmark","Strategy","Multiplier","Won"]].reset_index(drop=True)
        return res

    # --- Drawdown Top10 via metrics.py (already refactored)
    def _drawdown_tables_via_metrics(self, ret_lf: pl.LazyFrame) -> Dict[str, pd.DataFrame]:
        out: Dict[str, pd.DataFrame] = {}
        long_pl: pl.DataFrame = drawdown_top10_long(ret_lf, self.ppy).collect()
        for col in self.render_strategies:
            top10 = (
                long_pl
                .filter(pl.col("name") == col)
                .select(["Started", "Recovered", "Drawdown", "Days"])
                .to_pandas()
            )

            def _fmt_date_left(x):
                if pd.isna(x):
                    return "-"
                d = pd.to_datetime(x)
                return f"<span style='display:block;text-align:left'>{d.strftime('%Y-%m-%d')}</span>"

            if "Started" in top10.columns:
                top10["Started"] = top10["Started"].map(_fmt_date_left)
            if "Recovered" in top10.columns:
                top10["Recovered"] = top10["Recovered"].map(_fmt_date_left)

            new_cols = []
            for c in top10.columns:
                if c in ("Started", "Recovered"):
                    new_cols.append(f"<span style='display:block;text-align:left'>{c}</span>")
                else:
                    new_cols.append(c)
            top10.columns = new_cols
            out[col] = top10
        return out

    # -------------------------------------------------------------------------
    # HTML assembly using TearsheetBase
    # -------------------------------------------------------------------------
    def _render_html(self) -> None:
        # ---------- FIGURES HTML ----------
        fig_rows_html = []
        for f in self.fig_list:
            tiles, have = [], 0
            for col in self.render_strategies:
                p = self.fig_paths.get(col, {}).get(f)
                if p and os.path.isfile(p):
                    have += 1
                    tiles.append(
                        f"""<div class="thumb">
                               <div class="fig-header">{f.replace('_',' ').title()} — {col}</div>
                               <img src="{os.path.relpath(p, self.output_dir)}" alt="{f} - {col}" data-zoom="1"/>
                           </div>"""
                    )
            if have == 0:
                continue
            fig_rows_html.append(f"""
                <div class="fig-row">
                    <div class="fig-title">{f.replace('_',' ').title()}</div>
                    <div class="fig-grid" style="grid-template-columns: repeat({have}, 1fr);">
                        {''.join(tiles)}
                    </div>
                </div>
            """)
        for row in getattr(self, "extra_figures_rows", []):
            tile_tags = []
            tiles_raw = row.get("tiles", [])
            for label, path in tiles_raw:
                rel = os.path.relpath(path, self.output_dir)
                tile_tags.append(
                    f"""<div class="thumb">
                           <div class="fig-header">{label}</div>
                           <img src="{rel}" alt="{label}" data-zoom="1"/>
                       </div>"""
                )
            if not tile_tags:
                continue
            note = row.get("description")
            note_html = f'<div class="fig-note">{note}</div>' if note else ""
            per_strategy = row.get("per_strategy", True)
            if per_strategy:
                grid_cols = max(1, len(tile_tags))
            else:
                grid_cols = max(1, len(self.render_strategies))
                placeholders = max(0, grid_cols - len(tile_tags))
                if placeholders:
                    tile_tags.extend('<div class="thumb placeholder"></div>' for _ in range(placeholders))
            fig_rows_html.append(f"""
                <div class="fig-row">
                    <div class="fig-title">{row.get("title", "")}</div>
                    {note_html}
                    <div class="fig-grid" style="grid-template-columns: repeat({grid_cols}, 1fr);">
                        {''.join(tile_tags)}
                    </div>
                </div>
            """)
        figures_html = "\n".join(fig_rows_html) if fig_rows_html else "<div style='padding:12px;color:#888;'>No figures generated.</div>"

        # ---------- TABLES HTML ----------
        def _as_pct(df: pd.DataFrame, sig: int = 2) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame()
            d = df.copy()
            def fmt(x):
                if pd.isna(x): return "-"
                if isinstance(x, (int, float, np.floating)): return f"{x*100.0:.{sig}f}%"
                return str(x)
            try:
                return d.map(fmt)
            except Exception:
                return d.applymap(fmt)

        blocks = []

        # Metrics
        if "metrics" in self.tables_list:
            blocks.append(f"""
            <div class="table-block" data-table="metrics" data-group="{'controlled' if 'metrics' in self.tables_controlled else 'free'}">
                <h3>Key Performance Metrics</h3>
                {self.metrics_html}
            </div>
            """)

        # EOY
        if "eoy" in self.tables_list and getattr(self, "eoy_map", None):
            for col, df in self.eoy_map.items():
                if df is None or df.empty or (col not in self.render_strategies):
                    continue
                disp = df.copy()
                if "Benchmark" in disp.columns: disp["Benchmark"] = disp["Benchmark"].map(lambda v: "-" if pd.isna(v) else f"{v*100:.2f}%")
                if "Strategy" in disp.columns: disp["Strategy"] = disp["Strategy"].map(lambda v: "-" if pd.isna(v) else f"{v*100:.2f}%")
                if "Multiplier" in disp.columns: disp["Multiplier"] = disp["Multiplier"].map(lambda v: "-" if pd.isna(v) else f"{v:.2f}x")
                eoy_html = disp.to_html(border=0, escape=False, index=False)
                blocks.append(f"""
                <div class="table-block" data-table="eoy" data-group="{'controlled' if 'eoy' in self.tables_controlled else 'free'}">
                    <h3>End of Year — {col}</h3>
                    {eoy_html}
                </div>
                """)

        # Monthly
        if "monthly" in self.tables_list and getattr(self, "monthly_map", None):
            for col in self.render_strategies:
                m = self.monthly_map.get(col, pd.DataFrame())
                if m is None or m.empty:
                    continue
                m_disp = _as_pct(m, sig=2).to_html(border=0, escape=False)
                blocks.append(f"""
                <div class="table-block" data-table="monthly" data-group="{'controlled' if 'monthly' in self.tables_controlled else 'free'}">
                    <h3>Monthly Returns — {col}</h3>
                    {m_disp}
                </div>
                """)

        # Drawdown details
        if "drawdown_top10" in self.tables_list and getattr(self, "dd_map", None):
            for col in self.render_strategies:
                ddf = self.dd_map.get(col, pd.DataFrame())
                if ddf is None or ddf.empty:
                    continue
                ddisp = ddf.copy()
                if "Drawdown" in ddisp.columns:
                    ddisp["Drawdown"] = ddisp["Drawdown"].map(lambda v: f"{v:.2f}%" if isinstance(v, (int, float, np.floating)) else v)
                dd_html = ddisp.to_html(border=0, escape=False, index=False)
                blocks.append(f"""
                <div class="table-block" data-table="drawdown_top10" data-group="{'controlled' if 'drawdown_top10' in self.tables_controlled else 'free'}">
                    <h3>Worst 10 Drawdowns — {col}</h3>
                    {dd_html}
                </div>
                """)

        if getattr(self, "custom_table_blocks", None):
            blocks.extend(self.custom_table_blocks)

        tables_html = "\n".join(blocks) if blocks else "<div style='padding:12px;color:#888;'>No tables selected.</div>"

        bench_name = "—"
        if self.benchmark_excess_lf is not None:
            bench_name = self.benchmark_display_name or "Benchmark"
        subtitle = f"<strong>Benchmark: {bench_name}</strong> &nbsp;&nbsp; Sample Period: {self.date_range_str}"

        self.write_html(figures_html=figures_html, tables_html=tables_html, subtitle_html=subtitle)

    def render(self) -> str:
        """Return the path to the generated HTML dashboard."""
        return self.html_path
