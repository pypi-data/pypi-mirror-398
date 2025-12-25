# tutorial_customisation_code_demo.py
# -*- coding: utf-8 -*-
"""
Comprehensive code-based tutorial for extending the backtest dashboard.

Features demonstrated:
    • Custom monthly heatmap figures (QuantStats-style) via CustomFigureSpec
    • Custom residual quantile tables via CustomTableSpec
    • Appending and replacing blocks in the Key Performance Metrics table
      with CustomMetricBlockSpec
    • Per-figure and per-table data overrides using figure_data_overrides /
      table_data_overrides
    • End-to-end generation of customised backtest and prediction dashboards

This script mirrors the notebook workflow but keeps everything in a single,
well-documented Python module so it can be versioned, tested, or invoked from
other automation.
"""

from __future__ import annotations

import os
import calendar
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

from wrapped_helper import (
    make_backtest_bundle,
    make_prediction_bundle,
)
from backtest_dashboard import (
    BacktestManifest,
    CustomFigureSpec,
    CustomTableSpec,
    CustomMetricBlockSpec,
    BacktestTearsheet,
)
from information_dashboard import (
    InformationManifest,
    CustomTableSpec as PRCustomTableSpec,
    InformationTearsheet,
)
from tearsheet_suite import Tearsheet

# -----------------------------------------------------------------------------
# Custom builders
# -----------------------------------------------------------------------------

def monthly_heatmap_tiles(returns_lf: pl.LazyFrame, dashboard: BacktestTearsheet):
    """Generate QuantStats-style monthly heatmaps for each return column."""
    df = returns_lf.collect().to_pandas()
    if df.empty:
        return []

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

    tiles = []
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            continue

        monthly = series.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        if monthly.empty:
            continue

        pivot = (
            monthly.to_frame("ret")
            .assign(Year=lambda x: x.index.year, Month=lambda x: x.index.month)
            .pivot(index="Year", columns="Month", values="ret")
            * 100.0
        )

        fig, ax = plt.subplots(figsize=(6, 3))
        data = pivot.to_numpy()
        if np.isfinite(data).any():
            vmin = float(np.nanmin(data))
            vmax = float(np.nanmax(data))
            clim = max(abs(vmin), abs(vmax)) or 1.0
            vmin, vmax = -clim, clim
        else:
            vmin, vmax = -5.0, 5.0

        im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=vmin, vmax=vmax)
        for (i, j), val in np.ndenumerate(data):
            if np.isnan(val):
                continue
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=8, color="black")

        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([calendar.month_abbr[m] for m in pivot.columns], fontsize=9)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index.astype(int), fontsize=9)
        ax.set_title(f"{col} Monthly Returns (%)", fontsize=12)
        ax.set_xlabel("Month")
        ax.set_ylabel("Year")
        fig.tight_layout()

        fig_path = dashboard.save_custom_figure(fig, prefix=f"monthly_heatmap_{col.lower()}")
        if fig_path:
            tiles.append((f"{col} Monthly Heatmap", fig_path))
    return tiles


def residual_quartiles(residual_lf: pl.LazyFrame, dashboard: InformationTearsheet) -> str:
    """Render residual quartiles (25/50/75th percentile) as an HTML table."""
    df = residual_lf.collect().to_pandas()
    if df.empty:
        return ""
    quartiles = df.quantile([0.25, 0.5, 0.75]).round(3)
    quartiles.index.name = "Quantile"
    return quartiles.reset_index().to_html(border=0, escape=False, index=False)


def build_active_block(_, dashboard: BacktestTearsheet) -> pd.DataFrame:
    """Append a block summarising mean / std of returns (bp)."""
    base_pdf = dashboard.returns_excess_lf.collect().to_pandas()
    if base_pdf.empty:
        return pd.DataFrame()

    base_cols = [c for c in base_pdf.columns if c != "date"]
    summary: Dict[str, List[float]] = {}

    if dashboard.benchmark_excess_lf is not None:
        bench_pdf = dashboard.benchmark_excess_lf.collect().to_pandas()
        bench_cols = [c for c in bench_pdf.columns if c != "date"]
        if bench_cols:
            bench_series = bench_pdf[bench_cols[0]].dropna()
            summary["Benchmark"] = [
                bench_series.mean() * 10000,
                bench_series.std() * 10000,
            ]

    for col in base_cols:
        ser = base_pdf[col].dropna()
        summary[col] = [ser.mean() * 10000, ser.std() * 10000]

    block = pd.DataFrame(summary, index=["Return Mean (bp)", "Return Std (bp)"])
    return block


def replace_risk_block(_, dashboard: BacktestTearsheet) -> pd.DataFrame:
    """Replace the built-in Risk/Return section with an adjusted copy."""
    block = dashboard.metrics_df_raw.loc[
        ["Cumulative Return", "CAGR﹪", "Sharpe"]
    ].apply(pd.to_numeric, errors="coerce")
    block.loc["Sharpe (adj)"] = block.loc["Sharpe"] * 0.8
    return block


# -----------------------------------------------------------------------------
# Tutorial runner
# -----------------------------------------------------------------------------

def run_customisation_demo(output_dir: str = "output/tutorial_customisation_suite_v2") -> Dict[str, str]:
    """End-to-end example demonstrating the customisation hooks."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    backtest_bundle = make_backtest_bundle()
    prediction_bundle = make_prediction_bundle()

    # Alternative returns used for override demonstrations
    returns_schema = backtest_bundle.tracking_pnl.collect_schema().names()
    alt_returns = backtest_bundle.tracking_pnl.with_columns(
        (pl.col(c) * 0.5).alias(c) for c in returns_schema if c != "date"
    )

    custom_data_source = SimpleNamespace(
        tracking_pnl=backtest_bundle.tracking_pnl,
        benchmark=backtest_bundle.benchmark,
        active_tracking_pnl=backtest_bundle.active_tracking_pnl,
        returns=backtest_bundle.tracking_pnl,
        alt_returns=alt_returns,
        residuals=prediction_bundle.residuals_lf if hasattr(prediction_bundle, "residuals_lf") else None,
    )

    manifest = BacktestManifest(
        figures=["returns", "drawdown"],
        tables=["metrics", "monthly"],
        data_overrides={
            "returns": "tracking_pnl",
            "benchmark": "benchmark",
            "active_tracking_pnl": "active_tracking_pnl",
            "residuals": "residuals",
        },
        figure_data_overrides={"rolling_volatility": "alt_returns"},
        table_data_overrides={"monthly": "alt_returns"},
        custom_figures=[
            CustomFigureSpec(
                key="monthly_heatmap",
                title="Monthly Heatmaps",
                data_key="returns",
                builder=monthly_heatmap_tiles,
            )
        ],
        custom_tables=[
            CustomTableSpec(
                key="residual_quartiles",
                title="Residual Quartiles",
                data_key="residuals",
                builder=residual_quartiles,
            )
        ],
        custom_metric_blocks=[
            CustomMetricBlockSpec(
                key="Active Summary",
                title="Active Summary (bp)",
                data_key=None,
                builder=build_active_block,
            ),
            CustomMetricBlockSpec(
                key="Risk/Return",
                title="Risk/Return",
                data_key=None,
                builder=replace_risk_block,
                replace=True,
            ),
        ],
    )

    custom_dash = BacktestTearsheet(
        manifest=manifest,
        title="Customised Backtest Dashboard",
        output_dir=os.path.join(output_dir, "backtest"),
        data_source=custom_data_source,
    )

    combined_backtest = BacktestTearsheet(
        manifest=BacktestManifest(
            figures=["returns", "drawdown"],
            tables=["metrics"],
            data_overrides={
                "returns": "tracking_pnl",
                "benchmark": "benchmark",
                "active_tracking_pnl": "active_tracking_pnl",
            },
            custom_figures=[
                CustomFigureSpec(
                    key="monthly_heatmap",
                    title="Monthly Heatmaps",
                    data_key="tracking_pnl",
                    builder=monthly_heatmap_tiles,
                )
            ],
        ),
        title="Combined Backtest",
        output_dir=os.path.join(output_dir, "combined", "backtest"),
        data_source=backtest_bundle,
    )

    combined_prediction = InformationTearsheet(
        manifest=InformationManifest(
            factors=[c for c in prediction_bundle.preds_lf.collect_schema().names() if c != "date"],
            lags=[0, 1, 5, 10],
            horizons=[1, 5, 20],
            summary_lag=1,
            summary_horizon=5,
            custom_tables=[
                PRCustomTableSpec(
                    key="residual_quartiles",
                    title="Residual Quartiles",
                    data_key="residuals_lf",
                    builder=residual_quartiles,
                )
            ],
        ),
        figures=["IC", "sign"],
        tables=["pred_metrics"],
        data_overrides={
            "preds": "preds_lf",
            "target": "target_lf",
            "residuals": "residuals_lf",
        },
        title="Combined Prediction",
        output_dir=os.path.join(output_dir, "combined", "prediction"),
        data_source=prediction_bundle,
    )

    combined_paths = Tearsheet(
        combined_backtest,
        combined_prediction,
        title="Customisation Combo",
        tab_output_dir=os.path.join(output_dir, "combined"),
    ).render()

    result = {
        "custom_backtest_html": custom_dash.html_path,
        "combined_index_html": combined_paths.get("index"),
    }
    return result


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    outputs = run_customisation_demo()
    print("Custom dashboard paths:")
    for label, path in outputs.items():
        print(f"  {label}: {path}")
