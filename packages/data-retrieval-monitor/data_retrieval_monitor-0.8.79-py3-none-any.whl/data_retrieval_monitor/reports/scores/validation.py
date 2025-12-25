# scores/validation.py
from __future__ import annotations
import pandas as pd
import numpy as np
import quantstats as qs

def qs_full_metrics_table(
    returns: pd.DataFrame | pd.Series,
    benchmark: pd.Series | None,
    periods_per_year: int = 252
) -> pd.DataFrame:
    """
    Wrapper around qs.reports.metrics that is robust to single-column inputs.
    Prevents KeyError('max drawdown') seen in some versions with 1 strategy.
    """
    r = returns.copy()
    if isinstance(r, pd.DataFrame) and r.shape[1] == 1:
        r = r.squeeze("columns")

    try:
        m = qs.reports.metrics(
            returns=r,
            benchmark=benchmark,
            rf=0.0,
            display=False,
            mode="full",
            compounded=True,
            periods_per_year=periods_per_year,
            prepare_returns=True,  # safer for 1-col cases
        )
    except Exception:
        # very defensive fallback: fill NAs then retry
        r2 = r.fillna(0) if isinstance(r, pd.DataFrame) else r.fillna(0)
        m = qs.reports.metrics(
            returns=r2,
            benchmark=benchmark,
            rf=0.0,
            display=False,
            mode="full",
            compounded=True,
            periods_per_year=periods_per_year,
            prepare_returns=True,
        )
    m.index.name = "Metric"
    return m

def _to_float(x):
    try:
        if isinstance(x, str) and x.endswith("%"):
            return float(x[:-1]) / 100.0
        return float(x)
    except Exception:
        return np.nan

def write_deltas_polars_vs_pandas(
    polars_scores: dict,
    qs_full: pd.DataFrame,
    out_csv_path: str
) -> str:
    """
    Writes (polars - pandas) deltas for overlapping metrics/portfolios.
    """
    if not polars_scores:
        pd.DataFrame().to_csv(out_csv_path, index=True)
        print(f"[validation] wrote empty diff (one side empty): {out_csv_path}")
        return out_csv_path

    P = pd.DataFrame(polars_scores).T
    P.index.name = "Portfolio"

    Q = qs_full.applymap(_to_float).T
    Q.index.name = "Portfolio"

    common_ports = sorted(set(P.index) & set(Q.index))
    if not common_ports:
        pd.DataFrame().to_csv(out_csv_path, index=True)
        print(f"[validation] wrote empty diff (no common portfolios): {out_csv_path}")
        return out_csv_path

    P2 = P.loc[common_ports].copy()
    Q2 = Q.loc[common_ports].copy()

    common_metrics = sorted(set(P2.columns) & set(Q2.columns))
    if not common_metrics:
        pd.DataFrame().to_csv(out_csv_path, index=True)
        print(f"[validation] wrote empty diff (no common metrics): {out_csv_path}")
        return out_csv_path

    P2 = P2[common_metrics].astype(float)
    Q2 = Q2[common_metrics].astype(float)

    delta = P2 - Q2
    delta.to_csv(out_csv_path, index=True)
    print(f"[validation] wrote deltas: {out_csv_path}")
    return out_csv_path