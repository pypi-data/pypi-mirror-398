# prediction_metrics.py
from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt


# -------------------------
# Helpers
# -------------------------
def _as_lazy(x: pl.DataFrame | pl.LazyFrame) -> pl.LazyFrame:
    return x.lazy() if isinstance(x, pl.DataFrame) else x

def _ensure_datetime_ns(lf: pl.LazyFrame, date_col: str = "date") -> pl.LazyFrame:
    return lf.with_columns(pl.col(date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))

def _sign_expr(e: pl.Expr) -> pl.Expr:
    # Polars lacks pl.sign; implement via when/otherwise
    return (
        pl.when(e > 0).then(pl.lit(1))
         .when(e < 0).then(pl.lit(-1))
         .otherwise(pl.lit(0))
         .cast(pl.Int8)
    )

def _names_from_schema(lf: pl.LazyFrame, date_col: str = "date") -> List[str]:
    sch = lf.collect_schema()
    return [c for c in sch.names() if c != date_col]


# -------------------------
# Core XY builder per factor/lag/horizon
# -------------------------
def _xy_for_factor(
    preds_lf: pl.LazyFrame,
    target_lf: pl.LazyFrame,
    *,
    factor: str,
    lag: int,
    horizon: int,
    date_col: str = "date",
) -> pl.LazyFrame:
    P = preds_lf.select([pl.col(date_col), pl.col(factor).alias("_px")])
    T = target_lf.select([pl.col(date_col), pl.col(factor).alias("_ty0")])
    base = P.join(T, on=date_col, how="inner").sort(date_col)

    # X_t-k
    x = base.with_columns(pl.col("_px").shift(lag).alias("_x"))

    # y-bar over horizons (mean of next 1..H)
    shifts = [pl.col("_ty0").shift(-k) for k in range(1, max(1, horizon) + 1)]
    y = x.with_columns(pl.mean_horizontal(shifts).alias("_y"))

    return y.select([pl.col(date_col), pl.col("_x"), pl.col("_y")]).drop_nulls()


# -------------------------
# Cell statistics (fixed)
# -------------------------
def _cell_stats(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Returns a single-row LazyFrame:
      ["ic","t","mae","sign","n"]
    Robust to zero-variance and small-sample cases.
    """
    x = pl.col("_x").cast(pl.Float64)
    y = pl.col("_y").cast(pl.Float64)

    base = lf.select([
        pl.count().alias("n"),
        x.mean().alias("_mx"),
        y.mean().alias("_my"),
        (x * y).mean().alias("_mxy"),
        x.std(ddof=1).alias("_sx"),
        y.std(ddof=1).alias("_sy"),
        (x - y).abs().mean().alias("mae"),
        ((_prediction_metrics__sign(x) == _prediction_metrics__sign(y)).cast(pl.Float64).mean()).alias("sign"),
    ])

    # correlation via moments, guarded for sx<=0 or sy<=0 or n<3
    ic_expr = pl.when(
        (pl.col("n") >= 3) & (pl.col("_sx") > 0) & (pl.col("_sy") > 0)
    ).then(
        (pl.col("_mxy") - pl.col("_mx") * pl.col("_my")) / (pl.col("_sx") * pl.col("_sy"))
    ).otherwise(
        pl.lit(0.0)
    ).alias("ic")

    t_expr = pl.when(
        (pl.col("n") >= 3) & (pl.col("ic").abs() < 0.999999)  # avoid inf
    ).then(
        pl.col("ic") * (pl.col("n") - 2).cast(pl.Float64).sqrt() / (1.0 - pl.col("ic") ** 2).sqrt()
    ).otherwise(
        pl.lit(0.0)
    ).alias("t")

    return base.with_columns([ic_expr]).with_columns([t_expr]).select(["ic", "t", "mae", "sign", "n"])


# helper: sign without relying on pl.sign
def _prediction_metrics__sign(e: pl.Expr) -> pl.Expr:
    return (
        pl.when(e > 0).then(1)
         .when(e < 0).then(-1)
         .otherwise(0)
         .cast(pl.Int8)
    )
# -------------------------
# Grid compute
# -------------------------
def ic_grid_long(
    preds_lf: pl.LazyFrame | pl.DataFrame,
    target_lf: pl.LazyFrame | pl.DataFrame,
    *,
    factors: Optional[Iterable[str]] = None,
    lags: Optional[Iterable[int]] = None,
    horizons: Optional[Iterable[int]] = None,
    date_col: str = "date",
) -> Dict[str, pl.DataFrame]:
    P = _ensure_datetime_ns(_as_lazy(preds_lf), date_col)
    T = _ensure_datetime_ns(_as_lazy(target_lf), date_col)

    fact_list = list(factors) if factors is not None else sorted(
        set(_names_from_schema(P, date_col)) & set(_names_from_schema(T, date_col))
    )
    lag_list = list(lags) if lags is not None else [0]
    hor_list = list(horizons) if horizons is not None else [1]

    out: Dict[str, pl.DataFrame] = {}
    for f in fact_list:
        cells: List[pl.LazyFrame] = []
        for L in lag_list:
            for H in hor_list:
                xy = _xy_for_factor(P, T, factor=f, lag=int(L), horizon=int(H), date_col=date_col)
                cell = (
                    _cell_stats(xy)
                    .with_columns([
                        pl.lit(int(L)).alias("lag"),
                        pl.lit(int(H)).alias("horizon"),
                    ])
                    .select(["lag", "horizon", "ic", "t", "mae", "sign", "n"])
                )
                cells.append(cell)
        out[f] = (pl.concat(cells).collect() if cells
                  else pl.DataFrame({"lag": [], "horizon": [], "ic": [], "t": [], "mae": [], "sign": [], "n": []}))
    return out


# -------------------------
# Summary metrics (uses a preferred lag/horizon for MAE/MSE/Sign/N)
# -------------------------
def prediction_summary_metrics(
    preds_lf: pl.LazyFrame | pl.DataFrame,
    target_lf: pl.LazyFrame | pl.DataFrame,
    *,
    factors: Optional[Iterable[str]] = None,
    lags: Optional[Iterable[int]] = None,
    horizons: Optional[Iterable[int]] = None,
    lag: Optional[int] = None,        # preferred single lag (fallback 0)
    horizon: Optional[int] = None,    # preferred single horizon (fallback 1)
    date_col: str = "date",
) -> pd.DataFrame:
    # defaults for preferred cell
    if lags is None:
        lags = [int(lag)] if lag is not None else [0]
    if horizons is None:
        horizons = [int(horizon)] if horizon is not None else [1]

    grids = ic_grid_long(preds_lf, target_lf, factors=factors, lags=lags, horizons=horizons, date_col=date_col)

    cols = list(grids.keys())
    metrics_idx = ["IC", "t-stat", "R²", "MAE", "MSE", "Sign Acc.", "N", "IR (grid)"]
    out = pd.DataFrame(index=metrics_idx, columns=cols, dtype=float)

    def _pick_cell(df: pl.DataFrame) -> Tuple[float, float, float, float, float]:
        if df.is_empty():
            return (np.nan, np.nan, np.nan, np.nan, np.nan)
        prefer = df.filter((pl.col("lag") == lags[0]) & (pl.col("horizon") == horizons[0]))
        row = (prefer if not prefer.is_empty() else df.head(1)).to_dict(as_series=False)
        ic = float(row["ic"][0]) if row["ic"] else np.nan
        t  = float(row["t"][0]) if row["t"] else np.nan
        mae= float(row["mae"][0]) if row["mae"] else np.nan
        n  = float(row["n"][0]) if row["n"] else np.nan
        sign_val = float(row["sign"][0]) if row["sign"] else np.nan
        return ic, t, mae, n, sign_val

    P = _ensure_datetime_ns(_as_lazy(preds_lf), date_col)
    T = _ensure_datetime_ns(_as_lazy(target_lf), date_col)

    for f, df in grids.items():
        if df.is_empty():
            continue

        # IR over the whole grid of IC
        ics = df["ic"].to_numpy()
        mu = np.nanmean(ics) if ics.size else np.nan
        sd = np.nanstd(ics, ddof=1) if np.isfinite(ics).any() and ics.size > 1 else np.nan
        ir_grid = mu / sd if (sd and np.isfinite(sd) and sd > 0) else np.nan

        # Preferred single-cell stats
        ic, t, mae, n, sign_val = _pick_cell(df)

        # R^2 and MSE from preferred (lag, horizon)
        xy = _xy_for_factor(P, T, factor=f, lag=int(lags[0]), horizon=int(horizons[0]), date_col=date_col)
        stat = xy.select([
            ((pl.col("_x") - pl.col("_y")) ** 2).mean().alias("mse"),
            (pl.col("_x") * pl.col("_y")).mean().alias("mxy"),
            pl.col("_x").mean().alias("mx"),
            pl.col("_y").mean().alias("my"),
            (pl.col("_x") ** 2).mean().alias("mxx"),
            (pl.col("_y") ** 2).mean().alias("myy"),
        ]).collect()

        if stat.height:
            mse = float(stat["mse"][0])
            mxy, mx, my, mxx, myy = [float(stat[c][0]) for c in ("mxy","mx","my","mxx","myy")]
            cov = mxy - mx*my
            vx = mxx - mx*mx
            vy = myy - my*my
            r2 = (cov*cov) / (vx*vy) if (vx>0 and vy>0) else np.nan
        else:
            mse = np.nan
            r2 = np.nan

        out.loc["IC", f] = ic
        out.loc["t-stat", f] = t
        out.loc["R²", f] = r2
        out.loc["MAE", f] = mae
        out.loc["MSE", f] = mse
        out.loc["Sign Acc.", f] = sign_val
        out.loc["N", f] = n
        out.loc["IR (grid)", f] = ir_grid

    return out


# -------------------------
# Heatmap (PNG)
# -------------------------
def ic_heatmap_png(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    title: str = "IC Heatmap",
    out_dir: str = "figures",
    fname: str = "ic_heatmap.png",
    annotate: bool = True,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    cmap: str = "RdBu_r",
) -> Optional[str]:
    if isinstance(df, pl.LazyFrame):
        df = df.collect()
    if df.is_empty():
        return None

    # ensure required columns exist
    if not {"lag", "horizon"}.issubset(set(df.columns)):
        raise ValueError("ic_heatmap_png expects columns: 'lag', 'horizon' and one value column")

    # coerce dtypes before pivot (avoid category/utf8 surprises)
    val_cols = [c for c in df.columns if c not in {"lag", "horizon"}]
    if len(val_cols) != 1:
        raise ValueError(f"Expected exactly one value column; got {val_cols}")
    val_col = val_cols[0]

    df = df.with_columns([
        pl.col("lag").cast(pl.Int64),
        pl.col("horizon").cast(pl.Int64),
        pl.col(val_col).cast(pl.Float64),
    ])

    # canonical orderings as **ints**
    lags = sorted(df.select("lag")["lag"].unique().to_list())
    horizons = sorted(df.select("horizon")["horizon"].unique().to_list())

    # explicit aggregate (should be one value per (lag,horizon) anyway)
    wide = (
        df.pivot(index="horizon", columns="lag", values=val_col, aggregate_function="first")
          .sort("horizon")
    )

    # to pandas, normalize axis dtypes to **int**, then reindex with canonical orders
    pdf = wide.to_pandas()
    # Polars includes 'horizon' as a column after pivot
    pdf = pdf.set_index("horizon")
    try:
        pdf.index = pdf.index.astype(int)
    except Exception:
        pass
    try:
        pdf.columns = [int(c) for c in pdf.columns]
    except Exception:
        pass

    pdf = pdf.reindex(index=horizons, columns=lags)

    data = pdf.to_numpy(dtype=float)

    # If everything is NaN, show a zero matrix so the plot isn’t visually empty;
    # annotations still skip NaNs, so you’ll see “0.00” only if you prefer to fill later.
    if not np.isfinite(data).any():
        data = np.zeros_like(data, dtype=float)

    if vmin is None or vmax is None:
        m = np.nanmax(np.abs(data)) if np.isfinite(data).any() else 1.0
        vmin, vmax = -m, m

    h, w = data.shape
    fig_w = max(4.0, 0.6 * max(1, w) + 2.4)
    fig_h = max(3.2, 0.6 * max(1, h) + 2.0)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(data, origin="upper", aspect="auto", vmin=vmin, vmax=vmax, cmap=cmap)
    ax.set_xticks(range(w), lags)
    ax.set_yticks(range(h), horizons)
    ax.set_xlabel("Lag")
    ax.set_ylabel("Horizon")
    ax.set_title(title)

    if annotate:
        for i in range(h):
            for j in range(w):
                v = data[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel(val_col, rotation=270, labelpad=12)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, fname)
    fig.savefig(out_path, dpi=144, bbox_inches="tight")
    plt.close(fig)
    return out_path
