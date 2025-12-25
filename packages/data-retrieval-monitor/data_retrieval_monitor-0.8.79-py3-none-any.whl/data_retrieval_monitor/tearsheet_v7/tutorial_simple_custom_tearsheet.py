"""Simple custom tearsheet example (two strategies & two factors)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
from types import SimpleNamespace
from typing import Any

from backtest_dashboard import (
    BacktestManifest,
    CustomFigureSpec,
    CustomTableSpec,
    CustomMetricBlockSpec,
    BacktestTearsheet,
)
from information_dashboard import (
    InformationManifest,
    CustomFigureSpec as PRCustomFigureSpec,
    CustomTableSpec as PRCustomTableSpec,
    InformationTearsheet,
)
from tearsheet_suite import Tearsheet

# ---------------------------------------------------------------------------
# Synthetic data (two strategies, two prediction factors)
# ---------------------------------------------------------------------------

rng = np.random.default_rng(2024)
dates = pd.date_range("2021-01-01", periods=360, freq="B")

alpha = 0.0005 + rng.normal(0, 0.012, len(dates))
beta = 0.0003 + rng.normal(0, 0.010, len(dates))
benchmark = 0.0004 + rng.normal(0, 0.009, len(dates))

returns_df = pd.DataFrame(
    {
        "Strategy Alpha": alpha,
        "Strategy Beta": beta,
    },
    index=dates,
)
returns_df.index.name = "date"

benchmark_series = pd.Series(benchmark, index=dates, name="SPY")

active_df = pd.DataFrame(
    {
        "Strategy Alpha": alpha - benchmark,
        "Strategy Beta": beta - benchmark,
    },
    index=dates,
)
active_df.index.name = "date"

returns_lf = pl.from_pandas(returns_df.reset_index()).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
benchmark_lf = pl.from_pandas(benchmark_series.to_frame().reset_index()).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
active_lf = pl.from_pandas(active_df.reset_index()).with_columns(pl.col("date").cast(pl.Datetime)).lazy()

# prediction bundle
theta1 = rng.normal(0, 1, len(dates))
theta2 = rng.normal(0, 1, len(dates))
factors_pred = pd.DataFrame({
    "date": dates,
    "Value": theta1,
    "Momentum": theta2,
})
factors_target = pd.DataFrame({
    "date": dates,
    "Value": 0.3 * theta1 + rng.normal(0, 0.6, len(dates)),
    "Momentum": 0.4 * theta2 + rng.normal(0, 0.5, len(dates)),
})
preds_lf = pl.from_pandas(factors_pred).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
target_lf = pl.from_pandas(factors_target).with_columns(pl.col("date").cast(pl.Datetime)).lazy()
residuals_df = factors_target.copy()
residuals_df["Value"] = residuals_df["Value"] - factors_pred["Value"]
residuals_df["Momentum"] = residuals_df["Momentum"] - factors_pred["Momentum"]
residuals_lf = pl.from_pandas(residuals_df).with_columns(pl.col("date").cast(pl.Datetime)).lazy()


# ---------------------------------------------------------------------------
# Shared helpers (used below before class definitions)
# ---------------------------------------------------------------------------

def _as_pandas_frame(data) -> pd.DataFrame:
    """Helper that converts Polars LazyFrame/DataFrame or pandas DataFrame to pandas."""
    if hasattr(data, "collect"):
        try:
            return data.collect().to_pandas()
        except Exception:
            pass
    if isinstance(data, pl.DataFrame):
        return data.to_pandas()
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, dict):
        return pd.DataFrame(data)
    raise TypeError("Unsupported data type for custom builder.")


# user-defined inputs demonstrating custom figure/table data sources
factor_exposure_df = pd.DataFrame(
    {
        "Strategy": ["Strategy Alpha", "Strategy Alpha", "Strategy Beta", "Strategy Beta"],
        "Factor": ["Value", "Momentum", "Value", "Momentum"],
        "Exposure": [0.8, -0.2, 0.35, 0.55],
    }
)

risk_budget_df = pd.DataFrame(
    {
        "Bucket": ["Equities", "Rates", "FX", "Commodities"],
        "Contribution %": [42.0, 28.0, 18.0, 12.0],
        "VaR Share %": [38.0, 32.0, 20.0, 10.0],
    }
)

user_metric_block_df = pd.DataFrame(
    {
        "Metric": ["Hit Rate", "Avg Trade", "Active Tilt"],
        "Benchmark": [0.60, 0.12, 40],
        "Strategy Alpha": [0.62, 0.14, 55],
        "Strategy Beta": [0.58, 0.11, 33],
    }
)

alpha_snapshot_df = pd.DataFrame(
    {
        "Metric": ["Alpha IR", "Beta IR", "Hit Rate Δ"],
        "Benchmark": ["0.90", "0.08", "+0.0pp"],
        "Strategy Alpha": ["1.05", "0.12", "+4.2pp"],
        "Strategy Beta": ["0.88", "0.05", "+2.8pp"],
    }
)

diagnostic_sections = {
    "Signal Quality": pd.DataFrame(
        {
            "Metric": ["Average IC", "IR", "Sign Accuracy"],
            "Value": [0.12, 1.02, "57%"],
            "Momentum": [0.18, 1.35, "61%"],
        }
    ),
    "Error Diagnostics": pd.DataFrame(
        {
            "Metric": ["MAE", "MSE", "Hit Ratio"],
            "Value": [0.82, 0.94, "59%"],
            "Momentum": [0.71, 0.88, "63%"],
        }
    ),
}

prediction_kpi_sections = {
    "Forecast Accuracy": pd.DataFrame(
        {
            "Metric": ["MAE", "RMSE", "MAPE"],
            "Value": ["0.82", "1.05", "3.2%"],
            "Momentum": ["0.71", "0.98", "2.8%"],
        }
    ),
    "Stability": pd.DataFrame(
        {
            "Metric": ["Average Lag", "Effective Horizon"],
            "Value": ["2.1", "5"],
            "Momentum": ["1.9", "4"],
        }
    ),
}

prediction_metrics_sections = {}
for section_name, df in prediction_kpi_sections.items():
    prediction_metrics_sections[section_name] = df.copy()

# Append diagnostics sections (custom data)
for diag_title, diag_df in diagnostic_sections.items():
    prediction_metrics_sections[f"Diagnostics — {diag_title}"] = diag_df.copy()

print("Custom figure input (factor_exposure_df):")
print(factor_exposure_df)
print("\nCustom table input (risk_budget_df):")
print(risk_budget_df)
print("\nCustom metric block input (user_metric_block_df):")
print(user_metric_block_df)
print("\nSnapshot metrics for top placement (alpha_snapshot_df):")
print(alpha_snapshot_df)
print("\nPrediction diagnostic sections (dictionary input):")
for section, frame in diagnostic_sections.items():
    print(f"\n[{section}]")
    print(frame)
print("\nPrediction metric sections (dictionary input):")
for section, frame in prediction_metrics_sections.items():
    print(f"\n[{section}]")
    print(frame)

# ---------------------------------------------------------------------------
# Custom builders (figures & tables only)
# ---------------------------------------------------------------------------

def strategy_cumulative_tiles(returns_data, dashboard: BacktestTearsheet):
    """Return one mini cumulative chart per strategy (no built-in figures)."""
    pdf = _as_pandas_frame(returns_data)
    if pdf.empty:
        return []
    if "date" in pdf.columns:
        pdf["date"] = pd.to_datetime(pdf["date"])
        pdf = pdf.set_index("date")
    tiles = []
    for col in pdf.columns:
        series = pdf[col].dropna()
        if series.empty:
            tiles.append((f"{col} cumulative", None))
            continue
        cumulative = (1 + series).cumprod() - 1
        fig, ax = plt.subplots(figsize=(3.2, 2.1))
        ax.plot(cumulative.index, cumulative.values, color="#1f77b4", linewidth=1.4)
        ax.set_title(f"{col} — Cumulative", fontsize=10)
        ax.set_ylabel("Return")
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.2)
        fig.autofmt_xdate(rotation=30)
        fig.tight_layout()
        path = dashboard.save_custom_figure(fig, prefix=f"mini_cum_{col.lower().replace(' ','_')}")
        tiles.append((f"{col} cumulative", path))
    return tiles


def strategy_stats_table(returns_data, dashboard: BacktestTearsheet) -> str:
    """Compact stats table (mean/vol/sharpe) computed directly from returns."""
    pdf = _as_pandas_frame(returns_data)
    if pdf.empty:
        return ""
    if "date" in pdf.columns:
        pdf = pdf.drop(columns=["date"])
    rows = []
    for col in pdf.columns:
        ser = pdf[col].dropna()
        if ser.empty:
            continue
        avg = ser.mean() * 100
        vol = ser.std() * np.sqrt(252) * 100
        sharpe = ser.mean() / ser.std() * np.sqrt(252) if ser.std() != 0 else 0.0
        rows.append(
            {
                "Strategy": col,
                "Avg Daily %": f"{avg:.2f}",
                "Vol (ann. %)": f"{vol:.2f}",
                "Sharpe": f"{sharpe:.2f}",
            }
        )
    if not rows:
        return ""
    table = pd.DataFrame(rows)
    return table.to_html(border=0, index=False, escape=False)


def factor_residual_tiles(residual_data, dashboard: InformationTearsheet):
    """Per-factor residual histogram tiles (replaces built-in heatmaps)."""
    pdf = _as_pandas_frame(residual_data)
    if pdf.empty:
        return []
    if "date" in pdf.columns:
        pdf = pdf.drop(columns=["date"])
    tiles = []
    for factor in dashboard.factors:
        series = pdf.get(factor)
        if series is None or series.dropna().empty:
            tiles.append((factor, None))
            continue
        data = series.dropna()
        fig, ax = plt.subplots(figsize=(3.2, 2.3))
        ax.hist(data, bins=30, color="#9467bd", alpha=0.8, edgecolor="white")
        ax.set_title(f"{factor} residuals", fontsize=10)
        ax.grid(alpha=0.2)
        fig.tight_layout()
        path = dashboard.save_custom_figure(fig, prefix=f"{factor.lower()}_resid_hist")
        tiles.append((f"{factor} residuals", path))
    return tiles




def factor_exposure_summary(exposure_data, dashboard: BacktestTearsheet):
    """
    Aggregate chart showing factor exposure inputs supplied via the manifest.
    Demonstrates `per_strategy=False` usage with custom data.
    """
    pdf = _as_pandas_frame(exposure_data)
    if pdf.empty:
        return []
    pivot = pdf.pivot(index="Factor", columns="Strategy", values="Exposure").fillna(0.0)
    fig, ax = plt.subplots(figsize=(4.0, 2.6))
    pivot.plot(kind="bar", ax=ax)
    ax.axhline(0, color="#555", linewidth=0.8)
    ax.set_ylabel("Exposure")
    ax.set_title("Factor Exposure Snapshot", fontsize=11)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = dashboard.save_custom_figure(fig, prefix="factor_exposure_summary")
    return [("Factor Exposure Snapshot", path)]


def risk_budget_table(risk_data, dashboard: BacktestTearsheet) -> str:
    """Render a user-provided dataframe showing risk contributions."""
    pdf = _as_pandas_frame(risk_data)
    if pdf.empty:
        return ""
    display = pdf.copy()
    for col in display.columns:
        if display[col].dtype.kind in "fc":
            display[col] = display[col].map(lambda v: f"{v:.1f}%")
    return display.to_html(border=0, index=False, escape=False)


def alpha_snapshot_block(snapshot_data, dashboard: BacktestTearsheet) -> pd.DataFrame:
    """Return a dataframe intended for the top of the metrics table."""
    pdf = _as_pandas_frame(snapshot_data)
    if pdf.empty:
        return pd.DataFrame()
    if "Metric" in pdf.columns:
        pdf = pdf.set_index(pdf["Metric"].astype(str))
        pdf = pdf.drop(columns=["Metric"])
    pdf.index = [str(idx) for idx in pdf.index]
    preferred = ["Benchmark"] + [c for c in dashboard.render_strategies if c in pdf.columns]
    # Append anything not already included
    preferred.extend([c for c in pdf.columns if c not in preferred])
    pdf = pdf.reindex(columns=[c for c in preferred if c in pdf.columns])
    return pdf


def custom_metrics_block(data, dashboard: BacktestTearsheet) -> pd.DataFrame:
    """Provide a lightweight KPI block for the metrics table."""
    pdf = _as_pandas_frame(data)
    if pdf.empty:
        return pd.DataFrame()
    if "Metric" in pdf.columns:
        pdf = pdf.set_index(pdf["Metric"].astype(str))
        pdf = pdf.drop(columns=["Metric"])
    pdf.index = [str(idx) for idx in pdf.index]
    return pdf


def prediction_metrics_table(sections_data, dashboard: InformationTearsheet) -> str:
    """Render a grouped metrics layout similar to the backtest metrics table."""
    if not sections_data or not isinstance(sections_data, dict):
        return ""

    sections = []
    column_order: list[str] = []
    for title, block in sections_data.items():
        try:
            df = _as_pandas_frame(block)
        except Exception:
            try:
                df = pd.DataFrame(block)
            except Exception:
                continue
        if df.empty:
            continue
        if "Metric" not in df.columns:
            df = df.reset_index().rename(columns={df.index.name or "index": "Metric"})
        df = df.copy()
        for col in df.columns:
            if col == "Metric":
                continue
            if col not in column_order:
                column_order.append(col)
        sections.append((title, df))

    if not sections or not column_order:
        return ""

    def fmt(val: Any) -> str:
        if isinstance(val, str):
            return val
        if isinstance(val, (int, float, np.floating)):
            return f"{val:.2f}"
        if pd.isna(val):
            return "-"
        return str(val)

    html = [
        '<table class="metrics-grouped" style="width:var(--tables-w);">'
        '<thead><tr><th class="sticky-col">Metric</th>'
    ]
    html.append("".join(f'<th>{col}</th>' for col in column_order))
    html.append('</tr></thead><tbody>')

    first_section = True
    for title, df in sections:
        if not first_section:
            html.append(f'<tr class="sep"><td colspan="{len(column_order)+1}"></td></tr>')
        first_section = False
        html.append(f'<tr class="glabel"><td class="gtitle sticky-col" colspan="{len(column_order)+1}">{title}</td></tr>')
        for _, row in df.iterrows():
            metric = row.get("Metric", "")
            html.append('<tr>')
            html.append(f'<td class="mname sticky-col">{metric}</td>')
            for col in column_order:
                html.append(f'<td class="mval">{fmt(row.get(col))}</td>')
            html.append('</tr>')

    html.append('</tbody></table>')
    return "".join(html)

# ---------------------------------------------------------------------------
# Manifest configuration
# ---------------------------------------------------------------------------

backtest_manifest = BacktestManifest(
    figures=[],  # disable built-in plots
    tables=["metrics"],   # render metrics table only
    data_overrides={
        "returns": "returns",
        "benchmark": "benchmark",
        "active_tracking_pnl": "active_tracking_pnl",
    },
    custom_figures=[
        CustomFigureSpec(
            key="strategy_cumulative",
            data_key="returns",
            builder=strategy_cumulative_tiles,
            title="Mini Cumulative Trends",
        ),
        CustomFigureSpec(
            key="factor_exposure",
            data_key="factor_exposure",
            builder=factor_exposure_summary,
            title="Factor Exposure (Custom Input)",
            per_strategy=False,
        ),
    ],
    custom_metric_blocks=[
        CustomMetricBlockSpec(
            key="alpha_snapshot",
            data_key="alpha_snapshot",
            builder=alpha_snapshot_block,
            title="Alpha Snapshot",
            prepend=True,
        ),
        CustomMetricBlockSpec(
            key="user_kpis",
            data_key="custom_metrics",
            builder=custom_metrics_block,
            title="User KPIs",
            replace=False,
        ),
    ],
    custom_tables=[
        CustomTableSpec(
            key="strategy_stats",
            data_key="returns",
            builder=strategy_stats_table,
            title="Strategy Snapshot",
            controlled=True,
        ),
        CustomTableSpec(
            key="risk_budget",
            data_key="risk_budget",
            builder=risk_budget_table,
            title="Risk Budget Contributions",
            controlled=False,
        ),
    ],
)

prediction_manifest = InformationManifest(
    factors=["Value", "Momentum"],
    include_core_figures=False,
    include_core_tables=False,
    tables_controlled_by_slider=["prediction_metrics_full"],
    data_overrides={"residuals": "residuals"},
    custom_figures=[
        PRCustomFigureSpec(
            key="residual_histograms",
            data_key="residuals",
            builder=factor_residual_tiles,
            title="Residual Distributions",
        )
    ],
    custom_tables=[
        PRCustomTableSpec(
            key="prediction_metrics_full",
            data_key="prediction_metrics_sections",
            builder=prediction_metrics_table,
            title="Key Performance Metrics",
            controlled=True,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Build tearsheets using the new interface
# ---------------------------------------------------------------------------

backtest_ts = BacktestTearsheet(
    returns_df=None,  # supply data via data_source
    benchmark=None,
    manifest=backtest_manifest,
    title="Backtest (Custom Example)",
    output_dir="output/tutorial_simple/backtest",
    data_source=SimpleNamespace(
        active_tracking_pnl=active_lf,
        returns=returns_lf,
        benchmark=benchmark_lf,
        factor_exposure=factor_exposure_df,
        risk_budget=risk_budget_df,
        custom_metrics=user_metric_block_df,
        alpha_snapshot=alpha_snapshot_df,
    ),
)

prediction_ts = InformationTearsheet(
    preds_lf=preds_lf,
    target_lf=target_lf,
    manifest=prediction_manifest,
    title="Prediction (Custom Example)",
    output_dir="output/tutorial_simple/prediction",
    data_source=SimpleNamespace(
        residuals=residuals_lf,
        diagnostic_sections=diagnostic_sections,
        prediction_metrics_sections=prediction_metrics_sections,
    ),
)

suite = Tearsheet(backtest_ts, prediction_ts)
outputs = suite.render()

print("Generated dashboards:")
for name, path in outputs.items():
    print(f"  {name}: {path}")
