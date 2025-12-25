# scores/metrics.py
from __future__ import annotations
import math
from typing import Optional, Union
import numpy as np
import polars as pl

class Score:
    key: str
    label: str
    def compute(self, series: pl.Series, rf: Optional[Union[float, pl.Series]] = None, periods_per_year: int = 252) -> float:
        raise NotImplementedError

# ---------- helpers ----------
def _cast_f64(s: pl.Series) -> pl.Series:
    if not isinstance(s, pl.Series):
        s = pl.Series(s)
    if s.dtype != pl.Float64:
        s = s.cast(pl.Float64, strict=False)
    return s

def _per_period_rf(rf: Optional[Union[float, pl.Series]], ppy: int, n: int) -> Optional[pl.Series]:
    if rf is None:
        return None
    if isinstance(rf, (int, float)):
        pprf = (1.0 + float(rf)) ** (1.0 / ppy) - 1.0
        return pl.Series("rf", [pprf] * n, dtype=pl.Float64)
    if isinstance(rf, pl.Series):
        rfs = _cast_f64(rf)
        if rfs.len() == n:
            return rfs
        if rfs.len() == 1:
            return pl.Series("rf", [float(rfs.item())] * n, dtype=pl.Float64)
        # fallback: broadcast mean
        return pl.Series("rf", [float(rfs.mean())] * n, dtype=pl.Float64)
    return pl.Series("rf", [0.0] * n, dtype=pl.Float64)

def _excess(series: pl.Series, rf: Optional[Union[float, pl.Series]], ppy: int) -> pl.Series:
    s = _cast_f64(series)
    rfs = _per_period_rf(rf, ppy, s.len())
    return s if rfs is None else (s - rfs)

# ---------- metrics ----------
class Sharpe(Score):
    def __init__(self):
        self.key = "sharpe"; self.label = "Sharpe"
    def compute(self, series: pl.Series, rf=None, periods_per_year: int = 252) -> float:
        r = _excess(series, rf, periods_per_year)
        mu = float(r.mean()) * periods_per_year
        sd = float(r.std()) * math.sqrt(periods_per_year)
        return mu / sd if sd and not math.isclose(sd, 0.0) else float("nan")

class Sortino(Score):
    def __init__(self):
        self.key = "sortino"; self.label = "Sortino"
    def compute(self, series: pl.Series, rf=None, periods_per_year: int = 252) -> float:
        r = _excess(series, rf, periods_per_year)
        downside = r.filter(r < 0.0)
        if downside.len() == 0:
            return float("nan")
        dd = float((downside.pow(2.0).mean()) ** 0.5) * math.sqrt(periods_per_year)  # annualized
        mu = float(r.mean()) * periods_per_year
        return mu / dd if dd and not math.isclose(dd, 0.0) else float("nan")

class VolatilityAnn(Score):
    def __init__(self):
        self.key = "vol_ann"; self.label = "Volatility (ann.)"
    def compute(self, series: pl.Series, rf=None, periods_per_year: int = 252) -> float:
        s = _cast_f64(series)
        return float(s.std()) * math.sqrt(periods_per_year)

class CAGR(Score):
    def __init__(self):
        self.key = "cagr"; self.label = "CAGR"
    def compute(self, series: pl.Series, rf=None, periods_per_year: int = 252) -> float:
        s = _cast_f64(series)
        n = s.len()
        if n == 0:
            return float("nan")
        equity = (1.0 + s).cum_prod()
        endv = float(equity.item(-1))
        years = n / float(periods_per_year)
        if years <= 0.0 or endv <= 0.0:
            return float("nan")
        return endv ** (1.0 / years) - 1.0

class MaxDrawdown(Score):
    def __init__(self):
        self.key = "max_dd"; self.label = "Max Drawdown"
    def compute(self, series: pl.Series, rf=None, periods_per_year: int = 252) -> float:
        s = _cast_f64(series)
        if s.len() == 0:
            return float("nan")
        equity = (1.0 + s).cum_prod()
        peak = equity.cum_max()
        dd = equity / peak - 1.0
        return float(dd.min())

class CustomScore(Score):
    """Example score to demonstrate adding new metrics."""
    def __init__(self):
        self.key = "custom_score"; self.label = "Custom Score"
    def compute(self, series: pl.Series, rf=None, periods_per_year: int = 252) -> float:
        rng = np.random.RandomState(123 + series.len())
        return float(rng.uniform(-1.0, 1.0))