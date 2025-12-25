# tutorial_multi_tab_code_demo.py
# -*- coding: utf-8 -*-
"""
Multi-tab dashboard demo.

This script shows how to assemble several dashboard HTML files into a single
tabbed UI using `multi_dashboard.TabbedDashboard`.  It builds three tabs:

    1. Standard backtest tearsheet
    2. Prediction dashboard
    3. Customised backtest dashboard (with bespoke figure/table/metric blocks)

The output index.html lives in `output/multi_tab_demo/index.html`.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Dict

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

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
from information_dashboard import InformationTearsheet, InformationManifest
from tearsheet_suite import Tearsheet

# ---------------------------------------------------------------------------
# Shared custom builders (reuse logic from customisation tutorial)
# ---------------------------------------------------------------------------

def monthly_heatmap_tiles(returns_lf: pl.LazyFrame, dashboard: BacktestTearsheet):
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
        ax.set_xticklabels(pivot.columns, fontsize=9)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index.astype(int), fontsize=9)
        ax.set_title(f"{col} Monthly Returns (%)", fontsize=12)
        fig.tight_layout()
        fig_path = dashboard.save_custom_figure(fig, prefix=f"multi_heatmap_{col.lower()}")
        if fig_path:
            tiles.append((f"{col} Monthly Heatmap", fig_path))
    return tiles


def residual_quartiles(residual_lf, dashboard):
    df = residual_lf.collect().to_pandas()
    if df.empty:
        return ""
    qt = df.quantile([0.25, 0.5, 0.75]).round(3)
    qt.index.name = "Quantile"
    return qt.reset_index().to_html(border=0, escape=False, index=False)


def build_active_block(_, dashboard):
    pdf = dashboard.returns_excess_lf.collect().to_pandas()
    if pdf.empty:
        return pd.DataFrame()
    cols = [c for c in pdf.columns if c != "date"]
    data = {col: [pdf[col].mean() * 10000, pdf[col].std() * 10000] for col in cols}
    if dashboard.benchmark_excess_lf is not None:
        bench_pdf = dashboard.benchmark_excess_lf.collect().to_pandas()
        bench_cols = [c for c in bench_pdf.columns if c != "date"]
        if bench_cols:
            ser = bench_pdf[bench_cols[0]].dropna()
            data["Benchmark"] = [ser.mean() * 10000, ser.std() * 10000]
    block = pd.DataFrame(data).reindex(columns=["Benchmark"] + cols, fill_value=np.nan)
    block.index = ["Return Mean (bp)", "Return Std (bp)"]
    return block


def replace_risk_block(_, dashboard):
    block = dashboard.metrics_df_raw.loc[
        ["Cumulative Return", "CAGR﹪", "Sharpe"]
    ].apply(pd.to_numeric, errors="coerce")
    block.loc["Sharpe (adj)"] = block.loc["Sharpe"] * 0.8
    return block


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

def run_multi_tab_demo(output_dir: str = "output/multi_tab_demo") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    backtest_bundle = make_backtest_bundle()
    prediction_bundle = make_prediction_bundle()

    # Standard dashboards (backtest + prediction)
    standard_backtest = BacktestTearsheet(
        returns_df=backtest_bundle.tracking_pnl,
        benchmark=backtest_bundle.benchmark,
        title="Standard Backtest",
        output_dir=os.path.join(output_dir, "tab_backtest"),
    )

    pred_manifest = InformationManifest()
    standard_prediction = InformationTearsheet(
        preds_lf=prediction_bundle.preds_lf,
        target_lf=prediction_bundle.target_lf,
        title="Prediction Diagnostics",
        output_dir=os.path.join(output_dir, "tab_prediction"),
        manifest=pred_manifest,
    )

    # Customised backtest dashboard reused from earlier example
    alt_returns = backtest_bundle.tracking_pnl.with_columns(
        (pl.col(c) * 0.5).alias(c)
        for c in backtest_bundle.tracking_pnl.collect_schema().names()
        if c != "date"
    )
    custom_manifest = BacktestManifest(
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
    custom_data = SimpleNamespace(
        tracking_pnl=backtest_bundle.tracking_pnl,
        benchmark=backtest_bundle.benchmark,
        active_tracking_pnl=backtest_bundle.active_tracking_pnl,
        returns=backtest_bundle.tracking_pnl,
        alt_returns=alt_returns,
        residuals=prediction_bundle.residuals_lf if hasattr(prediction_bundle, "residuals_lf") else None,
    )
    custom_backtest = BacktestTearsheet(
        manifest=custom_manifest,
        title="Customised Backtest",
        output_dir=os.path.join(output_dir, "tab_custom_backtest"),
        data_source=custom_data,
    )

    tabs_output = Tearsheet(
        standard_backtest,
        standard_prediction,
        custom_backtest,
        title="Multi Tab Dashboard Demo",
        tab_titles=["Backtest", "Prediction", "Custom Backtest"],
        tab_output_dir=output_dir,
    ).render()

    return tabs_output.get("index")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    index_path = run_multi_tab_demo()
    print("Tabbed dashboard created:", index_path)
