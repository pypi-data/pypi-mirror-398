# scores/modules.py
from __future__ import annotations
from typing import Dict, Optional, Callable
import numpy as np
import polars as pl

from .base import ScoreBase, ScoreContext


# ---------- helpers ----------

def _per_period_rf(rf_ann: float, periods_per_year: int) -> float:
    return float(rf_ann) / float(periods_per_year)


def _cumulative_return(series: pl.Series) -> pl.Series:
    # compound path: prod(1+r) - 1  (Polars cumulative)
    return (1.0 + series).cum_prod() - 1.0


def _max_drawdown(series: pl.Series) -> float:
    # equity curve and dd using cum_prod / cum_max
    curve = (1.0 + series).cum_prod()
    running_max = curve.cum_max()
    dd = (curve / running_max) - 1.0
    return float(dd.min())


def _downside_std(series: pl.Series) -> float:
    neg = series.filter(series < 0.0)
    if neg.len() == 0:
        return 0.0
    return float(neg.std(ddof=1))


def _vol(series: pl.Series, periods_per_year: int) -> float:
    s = float(series.std(ddof=1))
    return s * np.sqrt(periods_per_year)


def _cagr(series: pl.Series, periods_per_year: int) -> float:
    n = series.len()
    if n == 0:
        return np.nan
    total = float((1.0 + series).cum_prod().tail(1)[0])
    years = n / float(periods_per_year)
    if years <= 0:
        return np.nan
    return total ** (1.0 / years) - 1.0


def _info_ratio(ret: pl.Series, bench: pl.Series, periods_per_year: int) -> float:
    active = (ret - bench).drop_nulls()
    mu = float(active.mean())
    sd = float(active.std(ddof=1))
    if sd == 0 or np.isnan(sd):
        return np.nan
    return (mu * periods_per_year) / (sd * np.sqrt(periods_per_year))


def _beta_alpha(ret: pl.Series, bench: pl.Series, rf_per: float, periods_per_year: int) -> tuple[float, float]:
    # excess returns per period
    ex_r = ret - rf_per
    ex_b = bench - rf_per
    cov = float(ex_r.cov(ex_b))
    var_b = float(ex_b.var())
    beta = np.nan if var_b == 0 else cov / var_b
    # alpha (annualized)
    mu_r = float(ex_r.mean()) * periods_per_year
    mu_b = float(ex_b.mean()) * periods_per_year
    alpha = mu_r - beta * mu_b
    return beta, alpha


def _var(series: pl.Series, level: float = 0.05) -> float:
    # historical VaR (negative for loss)
    return float(series.quantile(level))


def _cvar(series: pl.Series, level: float = 0.05) -> float:
    q = _var(series, level)
    tail = series.filter(series <= q)
    if tail.len() == 0:
        return float(q)
    return float(tail.mean())


# ---------- Score classes (Polars) ----------

class PLSharpe(ScoreBase):
    name = "Sharpe"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        rf_per = _per_period_rf(ctx.rf, ctx.periods_per_year)
        df = self._get_returns(ctx, start, end)
        out = {}
        for col in [c for c in df.columns if c != ctx.date_col]:
            s = df[col]
            mu = float(s.mean()) - rf_per
            sd = float(s.std(ddof=1))
            out[col] = np.nan if sd == 0 or np.isnan(sd) else (mu * ctx.periods_per_year) / (sd * np.sqrt(ctx.periods_per_year))
        # benchmark too if present
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            s = bm["Benchmark"]
            mu = float(s.mean()) - rf_per
            sd = float(s.std(ddof=1))
            out["Benchmark"] = np.nan if sd == 0 or np.isnan(sd) else (mu * ctx.periods_per_year) / (sd * np.sqrt(ctx.periods_per_year))
        return out


class PLSortino(ScoreBase):
    name = "Sortino"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        rf_per = _per_period_rf(ctx.rf, ctx.periods_per_year)
        df = self._get_returns(ctx, start, end)
        out = {}
        for col in [c for c in df.columns if c != ctx.date_col]:
            s = df[col]
            mu = float(s.mean()) - rf_per
            dstd = _downside_std(s)
            out[col] = np.nan if dstd == 0 or np.isnan(dstd) else (mu * ctx.periods_per_year) / (dstd * np.sqrt(ctx.periods_per_year))
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            s = bm["Benchmark"]
            mu = float(s.mean()) - rf_per
            dstd = _downside_std(s)
            out["Benchmark"] = np.nan if dstd == 0 or np.isnan(dstd) else (mu * ctx.periods_per_year) / (dstd * np.sqrt(ctx.periods_per_year))
        return out


class PLCAGR(ScoreBase):
    name = "CAGR"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {col: _cagr(df[col], ctx.periods_per_year) for col in df.columns if col != ctx.date_col}
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            out["Benchmark"] = _cagr(bm["Benchmark"], ctx.periods_per_year)
        return out


class PLMaxDD(ScoreBase):
    name = "Max Drawdown"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {col: _max_drawdown(df[col]) for col in df.columns if col != ctx.date_col}
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            out["Benchmark"] = _max_drawdown(bm["Benchmark"])
        return out


class PLVolatility(ScoreBase):
    name = "Volatility (ann.)"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {col: _vol(df[col], ctx.periods_per_year) for col in df.columns if col != ctx.date_col}
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            out["Benchmark"] = _vol(bm["Benchmark"], ctx.periods_per_year)
        return out


class PLCalmar(ScoreBase):
    name = "Calmar"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {}
        for col in [c for c in df.columns if c != ctx.date_col]:
            cagr = _cagr(df[col], ctx.periods_per_year)
            mdd = _max_drawdown(df[col])
            out[col] = np.nan if mdd == 0 else cagr / abs(mdd)
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            cagr = _cagr(bm["Benchmark"], ctx.periods_per_year)
            mdd = _max_drawdown(bm["Benchmark"])
            out["Benchmark"] = np.nan if mdd == 0 else cagr / abs(mdd)
        return out


class PLInformationRatio(ScoreBase):
    name = "Information Ratio"
    required_inputs = ("returns", "benchmark")

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        bm = self._get_benchmark(ctx, start, end)
        if bm is None:
            # no benchmark -> NaNs
            return {col: np.nan for col in df.columns if col != ctx.date_col}
        out = {}
        for col in [c for c in df.columns if c != ctx.date_col]:
            j = df.select([ctx.date_col, col]).join(bm, on=ctx.date_col, how="inner")
            out[col] = _info_ratio(j[col], j["Benchmark"], ctx.periods_per_year)
        out["Benchmark"] = np.nan  # IR vs itself undefined
        return out


class PLBetaAlpha(ScoreBase):
    name = "Beta/Alpha"
    required_inputs = ("returns", "benchmark")

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        rf_per = _per_period_rf(ctx.rf, ctx.periods_per_year)
        df = self._get_returns(ctx, start, end)
        bm = self._get_benchmark(ctx, start, end)
        if bm is None:
            return {col: np.nan for col in df.columns if c != ctx.date_col}
        out = {}
        for col in [c for c in df.columns if c != ctx.date_col]:
            j = df.select([ctx.date_col, col]).join(bm, on=ctx.date_col, how="inner")
            beta, alpha = _beta_alpha(j[col], j["Benchmark"], rf_per, ctx.periods_per_year)
            out[col] = beta
        out["Benchmark"] = 1.0
        return out


class PLVaR(ScoreBase):
    name = "VaR (5%)"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {col: _var(df[col], 0.05) for col in df.columns if col != ctx.date_col}
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            out["Benchmark"] = _var(bm["Benchmark"], 0.05)
        return out


class PLCVaR(ScoreBase):
    name = "CVaR (5%)"
    required_inputs = ("returns",)

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {col: _cvar(df[col], 0.05) for col in df.columns if col != ctx.date_col}
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            out["Benchmark"] = _cvar(bm["Benchmark"], 0.05)
        return out


class PLCustomScore(ScoreBase):
    """User-supplied callable: pl.Series -> float (per column) + benchmark."""
    required_inputs = ("returns",)

    def __init__(self, fn: Callable[[pl.Series], float], label: str = "Custom Score"):
        self.fn = fn
        self.name = label

    def compute(self, ctx: ScoreContext, start=None, end=None) -> Dict[str, float]:
        df = self._get_returns(ctx, start, end)
        out = {}
        for col in [c for c in df.columns if c != ctx.date_col]:
            try:
                out[col] = float(self.fn(df[col]))
            except Exception:
                out[col] = np.nan
        bm = self._get_benchmark(ctx, start, end)
        if bm is not None:
            try:
                out["Benchmark"] = float(self.fn(bm["Benchmark"]))
            except Exception:
                out["Benchmark"] = np.nan
        return out


# a deterministic "random" demo score
def random_polars_score(_: pl.Series) -> float:
    rs = np.random.RandomState(42)
    return float(rs.rand())