# example_run_pl.py
from __future__ import annotations
import numpy as np
import pandas as pd
import polars as pl

from scores.base import ScoreCollection
from scores.metrics import Sharpe, Sortino, VolatilityAnn, CAGR, MaxDrawdown, CustomScore
from scores.validation import qs_full_metrics_table, write_deltas_polars_vs_pandas
from dashboard import QuantStatsDashboard, DashboardManifest

# ----------------- dummy data (pandas first, then cast to polars) -----------------
np.random.seed(42)
dates = pd.bdate_range("2020-01-01", periods=1000)

# --- ONE STRATEGY (uncomment more to test multi-strategy)
# sr1 = pd.Series(np.random.normal(0.0010, 0.020, len(dates)), index=dates, name="Strategy1")
sr2 = pd.Series(np.random.normal(0.0008, 0.018, len(dates)), index=dates, name="Strategy2")
sr3 = pd.Series(np.random.normal(0.0012, 0.022, len(dates)), index=dates, name="Strategy3")

# df = pd.concat([ sr2,sr3], axis=1)
df = sr2.to_frame()  # 1-column DataFrame is fine

bench = pd.Series(np.random.normal(0.0005, 0.015, len(dates)), index=dates, name="Benchmark")

# Time-varying RF example (or use scalar like 0.02)
rf_series_pd = pd.Series(0.02 / 252.0, index=dates, name="RF")
rf_scalar = 0.02

# ----------------- Polars score computation (independent of dashboard) ------------
# Ensure we pass a DataFrame even for one strategy
pl_df = pl.from_pandas(df)

scores = ScoreCollection([
    Sharpe(), Sortino(), VolatilityAnn(), CAGR(), MaxDrawdown(), CustomScore()
])

# Build a Polars rf input (either scalar or Series aligned by length)
# If you prefer scalar RF, just pass rf_scalar instead of rf_pl below.
rf_pl = pl.Series("RF", rf_series_pd.to_numpy())

polars_results = scores.compute_for_frame(
    pl_df,
    rf=rf_pl,            # or rf=rf_scalar
    periods_per_year=252
)

# ----------------- Validation against QS pandas full metrics (delta CSV) ----------
qs_full = qs_full_metrics_table(df, bench, periods_per_year=252)
qs_full.to_csv("output/comprehensive_reports/metrics_qs_full.csv")
print("[validation] wrote QS full metrics: output/comprehensive_reports/metrics_qs_full.csv")

_ = write_deltas_polars_vs_pandas(
    polars_scores=polars_results,
    qs_full=qs_full,
    out_csv_path="output/comprehensive_reports/validation_deltas_polars_vs_pandas.csv"
)

# ----------------- Manifest (choose canonical keys/rows/cols exactly) -------------
manifest = DashboardManifest(
    figures=[
        "snapshot","earnings","returns","log_returns","yearly_returns",
        "daily_returns","rolling_beta","rolling_volatility",
        "rolling_sharpe","rolling_sortino","drawdowns_periods",
        "drawdown","monthly_heatmap","histogram","distribution",
    ],
    metric_rows=[],  # canonical keys (case-insensitive, no spaces), e.g. ["startperiod","endperiod","sharpe"]
    tables=["metrics","eoy","drawdown_details"],
    # metric_cols=["Strategy1"]  # uncomment to filter columns
)

# ----------------- Build dashboard (plots/tables in pandas; rf handled inside) ----
QuantStatsDashboard(
    returns_df=df,
    benchmark=bench,
    rf=rf_series_pd,  # could be float or a series (pd/pl)
    title="Strategy Tearsheet",
    output_dir="output/comprehensive_reports",
    manifest=manifest,
    periods_per_year=252,
)