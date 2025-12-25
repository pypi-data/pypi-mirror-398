# polars_plots.py
from __future__ import annotations
from typing import Optional, Dict
import numpy as np
import matplotlib.pyplot as plt
import polars as pl


def plot_cumulative_returns(
    returns_pl: pl.DataFrame,
    *,
    benchmark_pl: Optional[pl.DataFrame] = None,
    date_col: str = "date",
    title: str = "Cumulative Returns",
    figsize=(8, 5),
):
    plt.figure(figsize=figsize)
    x = returns_pl[date_col].to_numpy()
    for col in [c for c in returns_pl.columns if c != date_col]:
        curve = (1.0 + returns_pl[col]).cum_prod() - 1.0
        plt.plot(x, curve.to_numpy(), label=col)
    if benchmark_pl is not None and "Benchmark" in benchmark_pl.columns:
        x2 = benchmark_pl[date_col].to_numpy()
        curve_b = (1.0 + benchmark_pl["Benchmark"]).cum_prod() - 1.0
        plt.plot(x2, curve_b.to_numpy(), label="Benchmark", linestyle="--")
    plt.title(title)
    plt.ylabel("Cumulative Return")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()


def plot_log_returns(
    returns_pl: pl.DataFrame,
    *,
    benchmark_pl: Optional[pl.DataFrame] = None,
    date_col: str = "date",
    title: str = "Log Returns",
    figsize=(8, 4),
):
    plt.figure(figsize=figsize)
    x = returns_pl[date_col].to_numpy()
    for col in [c for c in returns_pl.columns if c != date_col]:
        curve = (1.0 + returns_pl[col]).cum_prod().log()
        plt.plot(x, curve.to_numpy(), label=col)
    if benchmark_pl is not None and "Benchmark" in benchmark_pl.columns:
        x2 = benchmark_pl[date_col].to_numpy()
        curve = (1.0 + benchmark_pl["Benchmark"]).cum_prod().log()
        plt.plot(x2, curve.to_numpy(), label="Benchmark", linestyle="--")
    plt.title(title)
    plt.ylabel("log(Equity)")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()


def plot_yearly_returns(
    returns_pl: pl.DataFrame,
    *,
    benchmark_pl: Optional[pl.DataFrame] = None,
    date_col: str = "date",
    title: str = "Yearly Returns",
    figsize=(8, 4),
):
    # group by year: prod(1+r)-1
    df = returns_pl.with_columns(pl.col(date_col).dt.year().alias("_year"))
    cols = [c for c in df.columns if c not in (date_col, "_year")]

    yr_dict: Dict[str, pl.DataFrame] = {}
    for col in cols:
        yr = df.group_by("_year").agg(((1.0 + pl.col(col)).product() - 1.0).alias(col)).sort("_year")
        yr_dict[col] = yr

    yb = None
    if benchmark_pl is not None and "Benchmark" in benchmark_pl.columns:
        dfb = benchmark_pl.with_columns(pl.col(date_col).dt.year().alias("_year"))
        yb = dfb.group_by("_year").agg(((1.0 + pl.col("Benchmark")).product() - 1.0).alias("Benchmark")).sort("_year")

    years = sorted(set().union(*[set(yr["_year"].to_list()) for yr in yr_dict.values()]) | (set(yb["_year"].to_list()) if yb is not None else set()))
    idx_map = {y: i for i, y in enumerate(years)}
    n_series = len(yr_dict) + (1 if yb is not None else 0)
    width = 0.8 / max(1, n_series)

    plt.figure(figsize=figsize)
    for k, col in enumerate(yr_dict.keys()):
        yr = yr_dict[col]
        xs = [idx_map[y] + k * width for y in yr["_year"].to_list()]
        plt.bar(xs, yr[col].to_numpy(), width=width, label=col)
    if yb is not None:
        k = len(yr_dict)
        xs = [idx_map[y] + k * width for y in yb["_year"].to_list()]
        plt.bar(xs, yb["Benchmark"].to_numpy(), width=width, label="Benchmark", alpha=0.7)

    plt.xticks([idx_map[y] + 0.4 for y in years], years, rotation=0)
    plt.title(title)
    plt.ylabel("Return")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()


def plot_distribution(
    returns_pl: pl.DataFrame,
    *,
    benchmark_pl: Optional[pl.DataFrame] = None,
    date_col: str = "date",
    title: str = "Distribution of Returns",
    bins: int = 50,
    figsize=(8, 4),
):
    plt.figure(figsize=figsize)
    # overlay histograms
    for col in [c for c in returns_pl.columns if c != date_col]:
        plt.hist(returns_pl[col].to_numpy(), bins=bins, alpha=0.5, label=col, density=True)
    if benchmark_pl is not None and "Benchmark" in benchmark_pl.columns:
        plt.hist(benchmark_pl["Benchmark"].to_numpy(), bins=bins, alpha=0.7, label="Benchmark", density=True, histtype="step", linewidth=1.75)
    plt.title(title)
    plt.xlabel("Return")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()


def plot_daily_returns(
    returns_pl: pl.DataFrame,
    *,
    date_col: str = "date",
    title: str = "Daily Returns",
    figsize=(8, 3),
):
    plt.figure(figsize=figsize)
    x = returns_pl[date_col].to_numpy()
    for col in [c for c in returns_pl.columns if c != date_col]:
        plt.plot(x, returns_pl[col].to_numpy(), label=col, linewidth=0.7)
    plt.title(title)
    plt.ylabel("Return")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()


def plot_rolling_volatility(
    returns_pl: pl.DataFrame,
    *,
    window: int = 21,
    periods_per_year: int = 252,
    benchmark_pl: Optional[pl.DataFrame] = None,
    date_col: str = "date",
    title: str = "Rolling Volatility (ann.)",
    figsize=(8, 3),
):
    plt.figure(figsize=figsize)
    x = returns_pl[date_col].to_numpy()
    for col in [c for c in returns_pl.columns if c != date_col]:
        rv = (
            returns_pl.select(
                pl.col(col).rolling_std(window_size=window, ddof=1) * np.sqrt(periods_per_year)
            )[col]
        ).to_numpy()
        plt.plot(x, rv, label=col, linewidth=0.9)
    if benchmark_pl is not None and "Benchmark" in benchmark_pl.columns:
        x2 = benchmark_pl[date_col].to_numpy()
        rvb = (
            benchmark_pl.select(
                pl.col("Benchmark").rolling_std(window_size=window, ddof=1) * np.sqrt(periods_per_year)
            )["Benchmark"]
        ).to_numpy()
        plt.plot(x2, rvb, label="Benchmark", linestyle="--", linewidth=0.9)
    # NOTE: No horizontal 0-line (removed by request)
    plt.title(title)
    plt.ylabel("Ann. Volatility")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()


def plot_underwater(
    returns_pl: pl.DataFrame,
    *,
    date_col: str = "date",
    title: str = "Underwater (Drawdown)",
    figsize=(8, 3),
):
    plt.figure(figsize=figsize)
    x = returns_pl[date_col].to_numpy()
    for col in [c for c in returns_pl.columns if c != date_col]:
        curve = (1.0 + returns_pl[col]).cum_prod()
        dd = (curve / curve.cum_max()) - 1.0
        plt.fill_between(x, dd.to_numpy(), 0.0, alpha=0.25, label=col, step="pre")
    plt.title(title)
    plt.ylabel("Drawdown")
    plt.legend()
    plt.tight_layout()
    return plt.gcf()