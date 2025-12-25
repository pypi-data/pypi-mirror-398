from __future__ import annotations

"""Utility helpers for producing wrapped dashboards (backtest + prediction)."""

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

from backtest_dashboard import (
    CustomFigureSpec as BTCustomFigure,
    CustomTableSpec as BTCustomTable,
    BacktestManifest,
    BacktestTearsheet,
)
from information_dashboard import (
    CustomFigureSpec as PRCustomFigure,
    CustomTableSpec as PRCustomTable,
    InformationTearsheet,
    InformationManifest,
)
from tearsheet_suite import TearsheetSuite, Tearsheet


@dataclass
class BacktestData:
    tracking_pnl: pl.LazyFrame
    benchmark: pl.LazyFrame
    active_tracking_pnl: pl.LazyFrame


@dataclass
class PredictionData:
    preds_lf: pl.LazyFrame
    target_lf: pl.LazyFrame
    residuals_lf: pl.LazyFrame


# -----------------------------------------------------------------------------
# Synthetic demo generators
# -----------------------------------------------------------------------------
def make_backtest_bundle(n: int = 500, seed: int = 42) -> BacktestData:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")

    bench = rng.normal(0.0002, 0.01, size=n)
    strat = bench + rng.normal(0.0003, 0.008, size=n)

    tracking = pl.from_pandas(pd.DataFrame({"date": dates, "Strategy": strat})).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    benchmark = pl.from_pandas(pd.DataFrame({"date": dates, "Benchmark": bench})).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    active = pl.from_pandas(pd.DataFrame({"date": dates, "Active": strat - bench})).with_columns(pl.col("date").cast(pl.Datetime)).lazy()

    return BacktestData(tracking_pnl=tracking, benchmark=benchmark, active_tracking_pnl=active)


def make_prediction_bundle(
    n: int = 500,
    seed: int = 7,
    factors: List[str] = ("Value", "Momentum"),
) -> PredictionData:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")

    preds_dict: Dict[str, Any] = {"date": dates}
    target_dict: Dict[str, Any] = {"date": dates}
    residual_dict: Dict[str, Any] = {"date": dates}

    for i, factor in enumerate(factors):
        baseline = rng.normal(0, 1.0 + 0.2 * i, size=n).cumsum()
        pred = baseline + rng.normal(0, 0.4 + 0.1 * i, size=n)
        target = 0.003 * pred + rng.normal(0, 0.01 + 0.003 * i, size=n)

        preds_dict[factor] = pred
        target_dict[factor] = target
        residual_dict[factor] = target - pred

    preds = pl.from_pandas(pd.DataFrame(preds_dict)).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    targets = pl.from_pandas(pd.DataFrame(target_dict)).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
    residuals = pl.from_pandas(pd.DataFrame(residual_dict)).with_columns(pl.col("date").cast(pl.Datetime)).lazy()

    return PredictionData(preds_lf=preds, target_lf=targets, residuals_lf=residuals)


# -----------------------------------------------------------------------------
# Helpers for coercing user-provided bundles
# -----------------------------------------------------------------------------
def _ensure_lazy(frame: Any) -> pl.LazyFrame:
    if isinstance(frame, pl.LazyFrame):
        return frame
    if isinstance(frame, pl.DataFrame):
        return frame.lazy()
    if isinstance(frame, pd.DataFrame):
        return pl.from_pandas(frame).lazy()
    raise TypeError("Expected Polars LazyFrame/DataFrame or pandas DataFrame.")


def _coerce_backtest_bundle(bundle: Any) -> BacktestData:
    if isinstance(bundle, BacktestData):
        return bundle

    if isinstance(bundle, dict):
        tracking = bundle.get("tracking_pnl")
        benchmark = bundle.get("benchmark")
        active = bundle.get("active_tracking_pnl")
    else:
        tracking = getattr(bundle, "tracking_pnl", None)
        benchmark = getattr(bundle, "benchmark", None)
        active = getattr(bundle, "active_tracking_pnl", None)

    if tracking is None or benchmark is None:
        raise ValueError("backtest bundle requires 'tracking_pnl' and 'benchmark'.")

    tracking_lazy = _ensure_lazy(tracking)
    benchmark_lazy = _ensure_lazy(benchmark)

    if active is None:
        tracking_pd = tracking_lazy.collect().to_pandas()
        benchmark_pd = benchmark_lazy.collect().to_pandas()
        bench_cols = [c for c in benchmark_pd.columns if c != "date"]
        if not bench_cols:
            raise ValueError("benchmark must contain at least one non-date column.")
        bench_series = benchmark_pd[bench_cols[0]]
        active_dict = {"date": tracking_pd["date"]}
        for col in tracking_pd.columns:
            if col == "date":
                continue
            active_dict[f"{col} Active"] = tracking_pd[col] - bench_series
        active_lazy = pl.from_pandas(pd.DataFrame(active_dict)).lazy()
    else:
        active_lazy = _ensure_lazy(active)

    return BacktestData(
        tracking_pnl=tracking_lazy,
        benchmark=benchmark_lazy,
        active_tracking_pnl=active_lazy,
    )


def _coerce_prediction_bundle(bundle: Any) -> PredictionData:
    if isinstance(bundle, PredictionData):
        return bundle

    if isinstance(bundle, dict):
        preds = bundle.get("preds_lf")
        target = bundle.get("target_lf")
        residuals = bundle.get("residuals_lf")
    else:
        preds = getattr(bundle, "preds_lf", None)
        target = getattr(bundle, "target_lf", None)
        residuals = getattr(bundle, "residuals_lf", None)

    if preds is None or target is None:
        raise ValueError("prediction bundle requires 'preds_lf' and 'target_lf'.")

    preds_lazy = _ensure_lazy(preds)
    target_lazy = _ensure_lazy(target)

    if residuals is None:
        preds_pd = preds_lazy.collect().to_pandas()
        target_pd = target_lazy.collect().to_pandas()
        residual_pd = target_pd.copy()
        for col in residual_pd.columns:
            if col == "date":
                continue
            residual_pd[col] = residual_pd[col] - preds_pd[col]
        residual_lazy = pl.from_pandas(residual_pd).lazy()
    else:
        residual_lazy = _ensure_lazy(residuals)

    return PredictionData(preds_lf=preds_lazy, target_lf=target_lazy, residuals_lf=residual_lazy)


# -----------------------------------------------------------------------------
# Default custom builders
# -----------------------------------------------------------------------------
def _active_cumulative(active_lf: pl.LazyFrame, *_):
    df = active_lf.collect().to_pandas().set_index("date")
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 2.4))
    df.iloc[:, 0].cumsum().plot(ax=ax, lw=1.4, color="#2E7D32")
    ax.set_title("Cumulative Active Return")
    ax.set_ylabel("Active Return")
    ax.grid(alpha=0.25)
    return {"label": "Active", "figure": fig, "prefix": "active"}


def _active_summary(active_lf: pl.LazyFrame, *_):
    df = active_lf.collect().to_pandas()
    if df.empty:
        return ""
    series = df.iloc[:, 1] if df.columns[0] == "date" else df.iloc[:, 0]
    stats = series.agg(["mean", "std", "median"]).to_frame(name="Active")
    stats = stats.mul(10000).round(2)
    stats = stats.reset_index().rename(columns={"index": "Metric"})
    return stats.to_html(border=0, escape=False, index=False)


def _residual_histograms(residual_lf: pl.LazyFrame, *_):
    df = residual_lf.collect().to_pandas().set_index("date")
    if df.empty:
        return None
    tiles = []
    for col in df.columns:
        fig, ax = plt.subplots(figsize=(4.2, 2.4))
        ax.hist(df[col].dropna(), bins=40, color="#3949AB", alpha=0.75)
        ax.set_title(f"Residual Distribution — {col}")
        ax.axvline(df[col].mean(), color="#F44336", lw=1.0, linestyle="--")
        ax.set_xlabel("Residual")
        ax.set_ylabel("Frequency")
        ax.grid(alpha=0.2)
        tiles.append({"label": col, "figure": fig, "prefix": f"resid_{col.lower()}", "column": col})
    return tiles


def _residual_summary(residual_lf: pl.LazyFrame, *_):
    df = residual_lf.collect().to_pandas()
    if df.empty:
        return ""
    summary = pd.DataFrame(
        {
            "Mean": df.mean(),
            "Std Dev": df.std(),
            "Skew": df.skew(),
            "Kurtosis": df.kurtosis(),
        }
    ).round(3)
    summary = summary.reset_index().rename(columns={"index": "Factor"})
    return summary.to_html(border=0, escape=False, index=False)


# -----------------------------------------------------------------------------
# Class-based interface
# -----------------------------------------------------------------------------
class WrappedDashboardSuite:
    """
    Class-based orchestrator that replaces the legacy ``build_dashboards`` helper.

    Instantiate with your backtest/prediction bundles and optional configuration,
    then call :meth:`render` to generate the dashboards and an index tab.
    """

    def __init__(
        self,
        *,
        backtest_bundle: BacktestData | dict | object,
        prediction_bundle: PredictionData | dict | object,
        backtest_figures: Optional[List[str]] = None,
        backtest_tables: Optional[List[str]] = None,
        custom_backtest_figures: Optional[List[Callable]] = None,
        custom_backtest_tables: Optional[List[Callable]] = None,
        custom_prediction_figures: Optional[List[Callable]] = None,
        custom_prediction_tables: Optional[List[Callable]] = None,
        output_dir: str = "output/demo_wrapped",
        backtest_title: str = "Strategy Backtest",
        prediction_title: str = "Prediction Diagnostics",
        suite_title: str = "Wrapped Dashboards",
        backtest_tab_title: str = "Backtest",
        prediction_tab_title: str = "Prediction",
        prediction_lags: Optional[List[int]] = None,
        prediction_horizons: Optional[List[int]] = None,
        prediction_summary_lag: Optional[int] = None,
        prediction_summary_horizon: Optional[int] = None,
    ) -> None:
        self.backtest_data = _coerce_backtest_bundle(backtest_bundle)
        self.prediction_data = _coerce_prediction_bundle(prediction_bundle)

        self.backtest_figures = backtest_figures or ["returns", "drawdown"]
        self.backtest_tables = backtest_tables or ["metrics", "monthly"]
        self.custom_backtest_figures = custom_backtest_figures
        self.custom_backtest_tables = custom_backtest_tables
        self.custom_prediction_figures = custom_prediction_figures
        self.custom_prediction_tables = custom_prediction_tables

        self.output_dir = output_dir
        self.backtest_output_dir = os.path.join(self.output_dir, "backtest")
        self.prediction_output_dir = os.path.join(self.output_dir, "prediction")

        self.backtest_title = backtest_title
        self.prediction_title = prediction_title
        self.suite_title = suite_title
        self.backtest_tab_title = backtest_tab_title
        self.prediction_tab_title = prediction_tab_title

        self.prediction_lags = prediction_lags or [0, 1, 5, 10]
        self.prediction_horizons = prediction_horizons or [1, 5, 20]
        self.prediction_summary_lag = prediction_summary_lag or 1
        self.prediction_summary_horizon = prediction_summary_horizon or 5

        self.backtest_tearsheet: Optional[BacktestTearsheet] = None
        self.prediction_tearsheet: Optional[InformationTearsheet] = None
        self._outputs: Optional[Dict[str, str]] = None

    # ------------------------------------------------------------------
    # Manifest builders
    # ------------------------------------------------------------------
    def _build_backtest_manifest(self) -> BacktestManifest:
        return BacktestManifest(
            figures=self.backtest_figures,
            tables=self.backtest_tables,
            data_overrides={
                "returns": "tracking_pnl",
                "benchmark": "benchmark",
                "active_tracking_pnl": "active_tracking_pnl",
            },
            custom_figures=self._resolve_backtest_custom_figures(),
            custom_tables=self._resolve_backtest_custom_tables(),
        )

    def _build_prediction_manifest(self) -> InformationManifest:
        factors = [c for c in self.prediction_data.preds_lf.collect_schema().names() if c != "date"]
        return InformationManifest(
            factors=factors,
            lags=self.prediction_lags,
            horizons=self.prediction_horizons,
            summary_lag=self.prediction_summary_lag,
            summary_horizon=self.prediction_summary_horizon,
            data_overrides={
                "preds": "preds_lf",
                "target": "target_lf",
                "residuals": "residuals_lf",
            },
            custom_figures=self._resolve_prediction_custom_figures(),
            custom_tables=self._resolve_prediction_custom_tables(),
        )

    # ------------------------------------------------------------------
    # Custom figure/table helpers
    # ------------------------------------------------------------------
    def _resolve_backtest_custom_figures(self) -> List[BTCustomFigure]:
        if not self.custom_backtest_figures:
            return [
                BTCustomFigure(
                    key="active_cumulative",
                    data_key="active_tracking_pnl",
                    builder=_active_cumulative,
                    title="Active Contribution",
                    output_prefix="active",
                )
            ]
        specs: List[BTCustomFigure] = []
        for idx, entry in enumerate(self.custom_backtest_figures):
            if isinstance(entry, BTCustomFigure):
                specs.append(entry)
                continue
            name = getattr(entry, "__name__", f"custom_backtest_fig_{idx}")
            specs.append(
                BTCustomFigure(
                    key=name,
                    data_key="returns",
                    builder=entry,
                    title=name.replace("_", " ").title(),
                )
            )
        return specs

    def _resolve_backtest_custom_tables(self) -> List[BTCustomTable]:
        if not self.custom_backtest_tables:
            return [
                BTCustomTable(
                    key="active_summary",
                    data_key="active_tracking_pnl",
                    builder=_active_summary,
                    title="Active Summary (bp)",
                    controlled=True,
                )
            ]
        specs: List[BTCustomTable] = []
        for idx, entry in enumerate(self.custom_backtest_tables):
            if isinstance(entry, BTCustomTable):
                specs.append(entry)
                continue
            name = getattr(entry, "__name__", f"custom_backtest_table_{idx}")
            specs.append(
                BTCustomTable(
                    key=name,
                    data_key="active_tracking_pnl",
                    builder=entry,
                    title=name.replace("_", " ").title(),
                )
            )
        return specs

    def _resolve_prediction_custom_figures(self) -> List[PRCustomFigure]:
        if not self.custom_prediction_figures:
            return [
                PRCustomFigure(
                    key="residual_histograms",
                    data_key="residuals",
                    builder=_residual_histograms,
                    title="Residual Diagnostics",
                    output_prefix="resid",
                )
            ]
        specs: List[PRCustomFigure] = []
        for idx, entry in enumerate(self.custom_prediction_figures):
            if isinstance(entry, PRCustomFigure):
                specs.append(entry)
                continue
            name = getattr(entry, "__name__", f"custom_prediction_fig_{idx}")
            specs.append(
                PRCustomFigure(
                    key=name,
                    data_key="residuals",
                    builder=entry,
                    title=name.replace("_", " ").title(),
                )
            )
        return specs

    def _resolve_prediction_custom_tables(self) -> List[PRCustomTable]:
        if not self.custom_prediction_tables:
            return [
                PRCustomTable(
                    key="residual_summary",
                    data_key="residuals",
                    builder=_residual_summary,
                    title="Residual Summary",
                    controlled=True,
                )
            ]
        specs: List[PRCustomTable] = []
        for idx, entry in enumerate(self.custom_prediction_tables):
            if isinstance(entry, PRCustomTable):
                specs.append(entry)
                continue
            name = getattr(entry, "__name__", f"custom_prediction_table_{idx}")
            specs.append(
                PRCustomTable(
                    key=name,
                    data_key="residuals",
                    builder=entry,
                    title=name.replace("_", " ").title(),
                )
            )
        return specs

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _create_backtest_tearsheet(self) -> BacktestTearsheet:
        return BacktestTearsheet(
            returns_df=None,
            benchmark=None,
            rf=0.0,
            manifest=self._build_backtest_manifest(),
            title=self.backtest_title,
            output_dir=self.backtest_output_dir,
            data_source=self.backtest_data,
        )

    def _create_prediction_tearsheet(self) -> InformationTearsheet:
        return InformationTearsheet(
            preds_lf=None,
            target_lf=None,
            manifest=self._build_prediction_manifest(),
            title=self.prediction_title,
            output_dir=self.prediction_output_dir,
            data_source=self.prediction_data,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(self) -> Dict[str, str]:
        os.makedirs(self.output_dir, exist_ok=True)

        self.backtest_tearsheet = self._create_backtest_tearsheet()
        self.prediction_tearsheet = self._create_prediction_tearsheet()

        suite_outputs = Tearsheet(
            tearsheets=[self.backtest_tearsheet, self.prediction_tearsheet],
            title=self.suite_title,
            tab_output_dir=self.output_dir,
            tab_titles=[self.backtest_tab_title, self.prediction_tab_title],
            create_tabbed=True,
        ).render()

        index_path = suite_outputs.get("index")

        self._outputs = {
            "backtest": self.backtest_tearsheet.html_path,
            "prediction": self.prediction_tearsheet.html_path,
        }
        self._outputs["index"] = index_path or self.backtest_tearsheet.html_path
        return self._outputs

    @property
    def outputs(self) -> Optional[Dict[str, str]]:
        """Return cached outputs if :meth:`render` has already been called."""
        return self._outputs
