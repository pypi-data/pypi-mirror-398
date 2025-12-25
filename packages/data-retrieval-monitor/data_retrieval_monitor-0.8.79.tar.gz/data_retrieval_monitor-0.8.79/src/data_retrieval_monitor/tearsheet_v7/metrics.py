# metrics.py
from __future__ import annotations

import math
from datetime import datetime
from typing import List, Optional

import polars as pl
from dateutil.relativedelta import relativedelta


# ============================================================================
# Column resolution helpers (avoid hard-coded names like "r"/"name"/"date")
# ============================================================================

_PREFERRED_DATE = "date"
_PREFERRED_NAME = "name"
_PREFERRED_RET  = "r"   # what metrics_table.melt() uses today
_EPS = 1e-12


def _schema(lf: pl.LazyFrame):
    sch = lf.collect_schema()
    return sch.names(), sch.dtypes()


def _schema_names(lf: pl.LazyFrame) -> List[str]:
    return _schema(lf)[0]


def _date_col_name(lf: pl.LazyFrame) -> str:
    names, dtypes = _schema(lf)
    if _PREFERRED_DATE in names:
        return _PREFERRED_DATE
    for i, c in enumerate(names):
        if dtypes[i] in (pl.Datetime, pl.Date):
            return c
    return names[0]


def _name_col_name(lf: pl.LazyFrame) -> str:
    names, dtypes = _schema(lf)
    if _PREFERRED_NAME in names:
        return _PREFERRED_NAME
    dcol = _date_col_name(lf)
    for i, c in enumerate(names):
        if c == dcol:
            continue
        if dtypes[i] in (pl.Categorical, pl.Utf8):
            return c
    return names[1] if len(names) > 1 else names[0]


def _ret_col_name(lf: pl.LazyFrame, ctx: Optional[dict] = None) -> str:
    if ctx is not None and isinstance(ctx.get("ret_col"), str):
        return ctx["ret_col"]
    names = _schema_names(lf)
    if _PREFERRED_RET in names:
        return _PREFERRED_RET
    dcol = _date_col_name(lf)
    ncol = _name_col_name(lf)
    cands = [c for c in names if c not in (dcol, ncol)]
    return cands[0] if cands else names[-1]


# ============================================================================
# Standalone metric functions (each returns LazyFrame ["name", "<metric>"])
# ============================================================================

# ---------- Base metrics ----------
def comp(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(((1.0 + r).product() - 1.0).alias("comp")).select([name_col, "comp"])


def _n(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    return Rc.group_by(name_col).agg(pl.count().alias("_n")).select([name_col, "_n"])


def _mu(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.mean().alias("_mu")).select([name_col, "_mu"])


def _sd(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.std(ddof=1).alias("_sd")).select([name_col, "_sd"])


def _lpsd(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg((r.clip(upper_bound=0.0) ** 2).mean().sqrt().alias("_lpsd")).select([name_col, "_lpsd"])


def _nz(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg((r != 0).sum().alias("_nz")).select([name_col, "_nz"])


def avg_win(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.filter(r > 0).mean().alias("avg_win")).select([name_col, "avg_win"])


def avg_loss(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.filter(r < 0).mean().alias("avg_loss")).select([name_col, "avg_loss"])


def best_day(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.max().alias("best_day")).select([name_col, "best_day"])


def worst_day(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.min().alias("worst_day")).select([name_col, "worst_day"])


def skew(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.skew().alias("skew")).select([name_col, "skew"])


def kurtosis(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.kurtosis().alias("kurtosis")).select([name_col, "kurtosis"])


def win_rate(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(((r > 0).sum() / pl.count()).alias("win_rate")).select([name_col, "win_rate"])


def cagr(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    ppy = ctx["ppy"]
    return (
        comp(Rc, ctx)
        .join(_n(Rc, ctx), on=name_col, how="inner")
        .with_columns(((1.0 + pl.col("comp")) ** (pl.lit(ppy) / pl.col("_n")) - 1.0).alias("cagr"))
        .select([name_col, "cagr"])
    )


def sharpe(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    ppy = ctx["ppy"]
    return (
        _mu(Rc, ctx)
        .join(_sd(Rc, ctx), on=name_col, how="inner")
        .with_columns(
            pl.when(pl.col("_sd") == 0)
             .then(pl.lit(float("nan")))
             .otherwise(pl.col("_mu") / pl.col("_sd") * math.sqrt(ppy))
             .alias("sharpe")
        )
        .select([name_col, "sharpe"])
    )


def sortino(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    ppy = ctx["ppy"]
    return (
        _mu(Rc, ctx)
        .join(_lpsd(Rc, ctx), on=name_col, how="inner")
        .with_columns(
            pl.when(pl.col("_lpsd") == 0)
             .then(pl.lit(float("nan")))
             .otherwise(pl.col("_mu") / pl.col("_lpsd") * math.sqrt(ppy))
             .alias("sortino")
        )
        .select([name_col, "sortino"])
    )


def vol_ann(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    ppy = ctx["ppy"]
    return _sd(Rc, ctx).with_columns((pl.col("_sd") * math.sqrt(ppy)).alias("vol_ann")).select([name_col, "vol_ann"])


def exposure(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    return (
        _nz(Rc, ctx)
        .join(_n(Rc, ctx), on=name_col, how="inner")
        .with_columns((pl.col("_nz") / pl.col("_n")).alias("exposure"))
        .select([name_col, "exposure"])
    )


def payoff(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    return (
        avg_win(Rc, ctx)
        .join(avg_loss(Rc, ctx), on=name_col, how="inner")
        .with_columns((pl.col("avg_win") / (-pl.col("avg_loss"))).alias("payoff"))
        .select([name_col, "payoff"])
    )


def calmar(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    return (
        cagr(Rc, ctx)
        .join(max_drawdown(Rc, ctx), on=name_col, how="inner")
        .with_columns(
            pl.when(pl.col("max_drawdown") <= 0)
             .then(pl.lit(float("nan")))
             .otherwise(pl.col("cagr") / pl.col("max_drawdown"))
             .alias("calmar")
        )
        .select([name_col, "calmar"])
    )


# ---------- Drawdown series & helpers ----------
def eq(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))

    base = Rc.sort([name_col, date_col])
    return base.with_columns(((1.0 + r).cum_prod().over(name_col)).alias("eq")).select([name_col, date_col, "eq"])


def peak(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    E = eq(Rc, ctx)
    return E.with_columns(pl.col("eq").cum_max().over(name_col).alias("peak")).select([name_col, date_col, "eq", "peak"])


def dd(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    base = Rc.sort([name_col, date_col])
    return (
        base.with_columns(((1.0 + r).cum_prod().over(name_col)).alias("eq"))
            .with_columns(pl.col("eq").cum_max().over(name_col).alias("peak"))
            .with_columns(((pl.col("eq") / pl.col("peak")) - 1.0).clip(upper_bound=0.0).alias("dd"))
            .select([name_col, date_col, "dd"])
    )


def ulcer(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    D = dd(Rc, ctx)
    ddv = pl.col("dd")
    return D.group_by(name_col).agg(((ddv ** 2).mean()).sqrt().alias("ulcer")).select([name_col, "ulcer"])


def max_drawdown(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    D = dd(Rc, ctx)
    ddv = pl.col("dd")
    return D.group_by(name_col).agg((-ddv.min()).alias("max_drawdown")).select([name_col, "max_drawdown"])


def dd_episodes(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    """
    One row per drawdown episode:
    ['name','grp','start','end','min_dd','periods','days']
    """
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)

    D = dd(Rc, ctx)
    seq = (
        D.with_columns((pl.col("dd") < 0).alias("_in"))
         .with_columns(
             pl.when(pl.col("_in") & (~pl.col("_in").shift(1).over(name_col).fill_null(False)))
               .then(1).otherwise(0).cast(pl.Int64).alias("_start")
         )
         .with_columns(pl.col("_start").cum_sum().over(name_col).alias("grp"))
         .filter(pl.col("_in"))
    )
    ep = seq.group_by([name_col, "grp"]).agg([
        pl.first(date_col).alias("start"),
        pl.last(date_col).alias("end"),
        pl.min("dd").alias("min_dd"),
        pl.count().alias("periods"),
    ])
    # calendar days (robust when start==end)
    ppy = ctx.get("ppy", 252)
    seconds = (pl.col("end") - pl.col("start")).dt.total_seconds().abs()
    days = seconds.truediv(86_400.0)
    min_span = pl.lit(1.0 / float(ppy))
    return ep.with_columns(
        pl.when(days > 0.0).then(days).otherwise(min_span).alias("days")
    )


# ---------- Episode filtering + leaf metrics ----------
def filter_episodes(
    ep: pl.LazyFrame,
    *,
    min_len: int = 0,
    len_unit: str = "days",   # "days" | "periods"
    min_depth: float = 0.0,   # require |min_dd| >= min_depth
) -> pl.LazyFrame:
    out = ep.filter(-pl.col("min_dd") >= float(min_depth))
    if min_len and min_len > 0:
        if str(len_unit).lower() == "periods":
            out = out.filter(pl.col("periods") >= int(min_len))
        else:
            out = out.filter(pl.col("days") >= float(min_len))
    return out


def avg_drawdown_from_ep(ep: pl.LazyFrame, *, mode: str = "mean", topk: int = 10) -> pl.LazyFrame:
    """
    From filtered episodes, compute avg drawdown per name.
    mode="mean" uses mean over all episodes; mode="topK" uses mean of K worst.
    Returns: ['name','avg_drawdown']
    """
    name_col = _name_col_name(ep)

    if mode.lower() == "topk":
        # Most negative first per name, then take top-K using a portable rank:
        ep_sorted = ep.sort([name_col, "min_dd"])
        ep_ranked = (
            ep_sorted
            .with_columns(pl.lit(1).alias("_one"))
            .with_columns(pl.col("_one").cum_sum().over(name_col).alias("_rn"))
        )
        ep_topk = ep_ranked.filter(pl.col("_rn") <= int(topk))
        return (
            ep_topk.group_by(name_col)
                   .agg((-pl.col("min_dd").mean()).alias("avg_drawdown"))
                   .select([name_col, "avg_drawdown"])
        )

    return (
        ep.group_by(name_col)
          .agg((-pl.col("min_dd").mean()).alias("avg_drawdown"))
          .select([name_col, "avg_drawdown"])
    )


def longest_dd_days_from_ep(ep: pl.LazyFrame) -> pl.LazyFrame:
    name_col = _name_col_name(ep)
    return (
        ep.group_by(name_col)
          .agg(pl.col("days").max().cast(pl.Float64).alias("longest_dd_days"))
          .select([name_col, "longest_dd_days"])
    )


def avg_dd_days_from_ep(ep: pl.LazyFrame) -> pl.LazyFrame:
    name_col = _name_col_name(ep)
    return (
        ep.group_by(name_col)
          .agg(pl.col("days").mean().cast(pl.Float64).alias("avg_dd_days"))
          .select([name_col, "avg_dd_days"])
    )


# ---------- Drawdown dates (strings) ----------
def _valley(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)

    D = dd(Rc, ctx).sort([name_col, date_col])
    return D.group_by(name_col).agg([
        pl.col("dd").min().alias("_min_dd"),
        pl.col(date_col).sort_by(pl.col("dd")).first().alias("valley"),
    ])


def _zeros(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)

    D = dd(Rc, ctx)
    return (
        D.with_columns((pl.col("dd") >= -_EPS).alias("_at_zero"))
         .filter(pl.col("_at_zero"))
         .select([name_col, pl.col(date_col).alias("zero_date")])
         .sort([name_col, "zero_date"])
    )


def max_dd_date(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    return _valley(Rc, ctx).select([name_col, pl.col("valley").dt.strftime("%Y-%m-%d").alias("max_dd_date")])


def max_dd_start(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)

    v = _valley(Rc, ctx).with_columns(pl.col("valley").alias("join_key")).sort([name_col, "join_key"])
    z = _zeros(Rc, ctx).with_columns(pl.col("zero_date").alias("join_key")).sort([name_col, "join_key"])
    j = v.join_asof(z, on="join_key", by=name_col, strategy="backward")
    return j.select([name_col, pl.col("zero_date").dt.strftime("%Y-%m-%d").alias("max_dd_start")])


def max_dd_end(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)

    v = _valley(Rc, ctx).with_columns(pl.col("valley").alias("join_key")).sort([name_col, "join_key"])
    z = _zeros(Rc, ctx).with_columns(pl.col("zero_date").alias("join_key")).sort([name_col, "join_key"])
    j = v.join_asof(z, on="join_key", by=name_col, strategy="forward")
    return j.select([name_col, pl.col("zero_date").dt.strftime("%Y-%m-%d").alias("max_dd_end")])


# ---------- Extremes ----------
def best_month(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    date = pl.col(date_col)
    mon = (
        Rc.with_columns([date.dt.year().alias("_y"), date.dt.month().alias("_m")])
          .group_by([name_col, "_y", "_m"])
          .agg(((1.0 + r).product() - 1.0).alias("rm"))
    )
    return mon.group_by(name_col).agg(pl.col("rm").max().alias("best_month")).select([name_col, "best_month"])


def worst_month(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    date = pl.col(date_col)
    mon = (
        Rc.with_columns([date.dt.year().alias("_y"), date.dt.month().alias("_m")])
          .group_by([name_col, "_y", "_m"])
          .agg(((1.0 + r).product() - 1.0).alias("rm"))
    )
    return mon.group_by(name_col).agg(pl.col("rm").min().alias("worst_month")).select([name_col, "worst_month"])


def best_year(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    date = pl.col(date_col)
    yr = (
        Rc.with_columns(date.dt.year().alias("_y"))
          .group_by([name_col, "_y"])
          .agg(((1.0 + r).product() - 1.0).alias("ry"))
    )
    return yr.group_by(name_col).agg(pl.col("ry").max().alias("best_year")).select([name_col, "best_year"])


def worst_year(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    date = pl.col(date_col)
    yr = (
        Rc.with_columns(date.dt.year().alias("_y"))
          .group_by([name_col, "_y"])
          .agg(((1.0 + r).product() - 1.0).alias("ry"))
    )
    return yr.group_by(name_col).agg(pl.col("ry").min().alias("worst_year")).select([name_col, "worst_year"])


# ---------- Tails ----------
def VaR_5(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return Rc.group_by(name_col).agg(r.quantile(0.05, "nearest").alias("VaR_5")).select([name_col, "VaR_5"])


def CVaR_5(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    var5 = VaR_5(Rc, ctx)
    return (
        Rc.join(var5, on=name_col, how="inner")
          .filter(r <= pl.col("VaR_5"))
          .group_by(name_col)
          .agg(r.mean().alias("CVaR_5"))
          .select([name_col, "CVaR_5"])
    )


def omega_0(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return (
        Rc.group_by(name_col).agg(
            (r.clip(lower_bound=0.0).sum() / (-r.clip(upper_bound=0.0).sum())).alias("omega_0")
        ).select([name_col, "omega_0"])
    )


# ---------- Period slices ----------
def mtd(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    last_date: datetime = ctx["last_date"]
    date = pl.col(date_col)
    return (
        Rc.with_columns([date.dt.year().alias("_y"), date.dt.month().alias("_m")])
          .filter((pl.col("_y") == last_date.year) & (pl.col("_m") == last_date.month))
          .group_by(name_col)
          .agg(((1.0 + r).product() - 1.0).alias("mtd"))
          .select([name_col, "mtd"])
    )


def _since(Rc: pl.LazyFrame, ctx: dict, start: datetime, out: str) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    r = pl.col(_ret_col_name(Rc, ctx))
    return (
        Rc.filter(pl.col(date_col) >= pl.lit(start))
          .group_by(name_col)
          .agg(((1.0 + r).product() - 1.0).alias(out))
          .select([name_col, out])
    )


def _cagr_since(Rc: pl.LazyFrame, ctx: dict, start: datetime, out: str) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    date_col = _date_col_name(Rc)
    ppy = ctx["ppy"]
    r = pl.col(_ret_col_name(Rc, ctx))

    sub = Rc.filter(pl.col(date_col) >= pl.lit(start)).group_by(name_col).agg([
        ((1.0 + r).product() - 1.0).alias("_comp"),
        pl.count().alias("_n"),
    ])
    return sub.with_columns(((1.0 + pl.col("_comp")) ** (pl.lit(ppy) / pl.col("_n")) - 1.0).alias(out)).select([name_col, out])


def last_3m(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    return _since(Rc, ctx, ctx["last_date"] - relativedelta(months=3), "3m")


def last_6m(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    return _since(Rc, ctx, ctx["last_date"] - relativedelta(months=6), "6m")


def ytd(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    ld: datetime = ctx["last_date"]
    return _since(Rc, ctx, datetime(ld.year, 1, 1), "ytd")


def last_1y(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    return _since(Rc, ctx, ctx["last_date"] - relativedelta(years=1), "1y")


def ann_3y(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    return _cagr_since(Rc, ctx, ctx["last_date"] - relativedelta(years=3), "3y_ann")


def ann_5y(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    return _cagr_since(Rc, ctx, ctx["last_date"] - relativedelta(years=5), "5y_ann")


def ann_10y(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    return _cagr_since(Rc, ctx, ctx["last_date"] - relativedelta(years=10), "10y_ann")


def ann_alltime(Rc: pl.LazyFrame, ctx: dict) -> pl.LazyFrame:
    name_col = _name_col_name(Rc)
    ppy = ctx["ppy"]
    r = pl.col(_ret_col_name(Rc, ctx))
    sub = Rc.group_by(name_col).agg([
        ((1.0 + r).product() - 1.0).alias("_comp"),
        pl.count().alias("_n"),
    ])
    return sub.with_columns(((1.0 + pl.col("_comp")) ** (pl.lit(ppy) / pl.col("_n")) - 1.0).alias("alltime_ann")).select([name_col, "alltime_ann"])


# ============================================================================
# Table-oriented long producers (pure Polars Lazy; no pandas)
# ============================================================================

def _melt_wide_returns(
    returns_lf: pl.LazyFrame,
    *,
    value_name: str = _PREFERRED_RET,
    name_name: str = _PREFERRED_NAME,
    date_name: Optional[str] = None,
) -> pl.LazyFrame:
    """Wide [date, s1, s2, ...] -> long Rc [date, name, <value_name>] (lazy)."""
    names = _schema_names(returns_lf)
    dcol = date_name or (_PREFERRED_DATE if _PREFERRED_DATE in names else _date_col_name(returns_lf))
    strat_cols = [c for c in names if c != dcol]
    return (
        returns_lf
        .with_columns(pl.col(dcol).cast(pl.Datetime).dt.cast_time_unit("ns"))
        .melt(id_vars=[dcol], value_vars=strat_cols, variable_name=name_name, value_name=value_name)
        .with_columns(pl.col(name_name).cast(pl.Categorical()))
    )


def yearly_returns_long(
    returns_lf: pl.LazyFrame,
    benchmark_lf: Optional[pl.LazyFrame] = None,
) -> pl.LazyFrame:
    """
    Produce long EOY table for all strategies (and optional benchmark).
    Output columns: ["name","Year","Benchmark","Strategy","Multiplier","Won"]
    """
    dcol = _date_col_name(returns_lf)
    Rc = _melt_wide_returns(returns_lf, value_name=_PREFERRED_RET, name_name=_PREFERRED_NAME, date_name=dcol)
    name_col = _name_col_name(Rc)
    rcol = _ret_col_name(Rc, {"ret_col": _PREFERRED_RET})
    date = pl.col(dcol)

    # strategy yearly compounded returns
    strat = (
        Rc.with_columns(date.dt.year().alias("Year"))
          .group_by([name_col, "Year"])
          .agg(((1.0 + pl.col(rcol)).product() - 1.0).alias("Strategy"))
    )

    # benchmark yearly
    bench = None
    if benchmark_lf is not None:
        bn = _schema_names(benchmark_lf)
        bd = _date_col_name(benchmark_lf)
        bcols = [c for c in bn if c != bd]
        if len(bcols) == 1:
            bcol = bcols[0]
            bench = (
                benchmark_lf
                .with_columns(pl.col(bd).cast(pl.Datetime).dt.cast_time_unit("ns"))
                .with_columns(pl.col(bd).dt.year().alias("Year"))
                .group_by("Year")
                .agg(((1.0 + pl.col(bcol)).product() - 1.0).alias("Benchmark"))
            )

    if bench is not None:
        joined = strat.join(bench, on="Year", how="left")
        joined = joined.with_columns([
            pl.when(pl.col("Benchmark").is_not_null() & ((pl.col("Benchmark")).abs() > _EPS))
              .then(pl.col("Strategy") / pl.col("Benchmark"))
              .otherwise(pl.lit(float("nan")))
              .alias("Multiplier"),
            pl.when(pl.col("Benchmark").is_not_null() & pl.col("Strategy").is_not_null())
              .then(pl.when(pl.col("Strategy") > pl.col("Benchmark")).then(pl.lit("+")).otherwise(pl.lit("–")))
              .otherwise(pl.lit(""))
              .alias("Won"),
        ])
        out = joined.select([name_col, "Year", "Benchmark", "Strategy", "Multiplier", "Won"]).sort([name_col, "Year"])
    else:
        out = strat.with_columns([
            pl.lit(float("nan")).alias("Benchmark"),
            pl.lit(float("nan")).alias("Multiplier"),
            pl.lit("").alias("Won"),
        ]).select([name_col, "Year", "Benchmark", "Strategy", "Multiplier", "Won"]).sort([name_col, "Year"])

    return out.rename({name_col: "name"})


def monthly_returns_long(returns_lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Produce long monthly returns for all strategies.
    Output columns: ["name","year","month","mret"]
    """
    dcol = _date_col_name(returns_lf)
    Rc = _melt_wide_returns(returns_lf, value_name=_PREFERRED_RET, name_name=_PREFERRED_NAME, date_name=dcol)
    name_col = _name_col_name(Rc)
    rcol = _ret_col_name(Rc, {"ret_col": _PREFERRED_RET})
    date = pl.col(dcol)

    out = (
        Rc.with_columns([date.dt.year().alias("year"), date.dt.month().alias("month")])
          .group_by([name_col, "year", "month"])
          .agg(((1.0 + pl.col(rcol)).product() - 1.0).alias("mret"))
          .select([name_col, "year", "month", "mret"])
          .sort([name_col, "year", "month"])
    )
    return out.rename({name_col: "name"})


def drawdown_top10_long(returns_lf: pl.LazyFrame, ppy: int = 252) -> pl.LazyFrame:
    """
    Worst 10 drawdowns per strategy (long).
    Output columns: ["name","Started","Recovered","Drawdown","Days"]
    - Drawdown is already in percent units (e.g., -32.45)
    """
    dcol = _date_col_name(returns_lf)
    Rc = _melt_wide_returns(returns_lf, value_name=_PREFERRED_RET, name_name=_PREFERRED_NAME, date_name=dcol)
    name_col = _name_col_name(Rc)
    rcol = _ret_col_name(Rc, {"ret_col": _PREFERRED_RET})

    returns = pl.col(rcol)
    base = Rc.sort([name_col, dcol])

    seq = (
        base
        .with_columns(((1.0 + returns).cum_prod().over(name_col)).alias("equity"))
        .with_columns(pl.col("equity").cum_max().over(name_col).alias("peak"))
        .with_columns((pl.col("equity") / pl.col("peak") - 1.0).alias("dd"))
        .with_columns((pl.col("dd") < -_EPS).alias("_in"))
        .with_columns(
            pl.when(pl.col("_in") & (~pl.col("_in").shift(1).over(name_col).fill_null(False)))
              .then(1).otherwise(0).cast(pl.Int64).alias("_start")
        )
        .with_columns(pl.col("_start").cum_sum().over(name_col).alias("grp"))
    )

    dd_only = seq.filter(pl.col("_in"))

    blocks = (
        dd_only
        .group_by([name_col, "grp"])
        .agg([
            pl.col(dcol).first().alias("Started"),
            pl.col(dcol).last().alias("EndBlock"),
            pl.col(dcol).sort_by(pl.col("dd")).first().alias("Trough"),
            pl.col("dd").min().alias("_min_dd"),
            (
                (pl.col(dcol).last().cast(pl.Date) - pl.col(dcol).first().cast(pl.Date))
                .dt.total_days()
                .add(1)
            ).alias("Days"),
            pl.count().alias("_steps"),
        ])
    )

    zeros = (
        seq.filter(pl.col("dd") >= -_EPS)
           .select([pl.col(name_col), pl.col(dcol).alias("join_key"), pl.col(dcol).alias("Recovered")])
           .sort([name_col, "join_key"])
    )

    joined = (
        blocks.sort([name_col, "EndBlock"])
              .join_asof(zeros, left_on="EndBlock", right_on="join_key", by=name_col, strategy="forward")
              .with_columns((pl.col("_min_dd") * 100.0).alias("Drawdown"))
              .select([pl.col(name_col), pl.col("Started"), pl.col("Recovered"), pl.col("Drawdown"), pl.col("Days"), pl.col("_min_dd"), pl.col("Trough")])
    )

    # rank per strategy using 1-based cumulative sum of ones in the sorted order
    ranked = (
        joined
        .sort([name_col, "_min_dd", "Days", "Trough"], descending=[False, True, False, False])
        .with_columns(pl.lit(1).alias("_one"))
        .with_columns(pl.col("_one").cum_sum().over(name_col).alias("_rn"))
        .filter(pl.col("_rn") <= 10)
        .select([
            pl.col(name_col).alias("name"),
            pl.col("Started"),
            pl.col("Recovered"),
            pl.col("Drawdown"),
            pl.col("Days"),
        ])
    )
    return ranked

# --- in metrics.py ---

from typing import Sequence

def yearly_returns_long_wide(
    returns_lf: pl.LazyFrame,
    *,
    ret_cols: Sequence[str] | None = None,
    date_col: str = "date",
    out_col: str = "year_ret",
) -> pl.LazyFrame:
    """
    Compute per-strategy End-Of-Year returns as a LONG lazy frame:
    ['name','year', out_col]. All computation is here (not in tables).
    """
    # decide which strategy columns to use
    names = returns_lf.collect_schema().names()
    if ret_cols is None:
        ret_cols = [c for c in names if c != date_col]
    if not ret_cols:
        # empty long frame with the right schema
        return pl.LazyFrame({"name": [], "year": [], out_col: []}, schema={"name": pl.Utf8, "year": pl.Int32, out_col: pl.Float64})

    long = (
        returns_lf
        .select([pl.col(date_col)] + [pl.col(c) for c in ret_cols])
        .melt(id_vars=date_col, value_vars=list(ret_cols), variable_name="name", value_name="_ret")
    )
    return (
        long.with_columns(pl.col(date_col).dt.year().alias("year"))
            .group_by(["name", "year"])
            .agg(((pl.col("_ret") + 1.0).product() - 1.0).alias(out_col))
            .select(["name", "year", out_col])
    )


def monthly_returns_long_wide(
    returns_lf: pl.LazyFrame,
    *,
    ret_cols: Sequence[str] | None = None,
    date_col: str = "date",
    out_col: str = "mret",
) -> pl.LazyFrame:
    """
    Compute per-strategy monthly returns as a LONG lazy frame:
    ['name','year','month', out_col]. All computation is here.
    """
    names = returns_lf.collect_schema().names()
    if ret_cols is None:
        ret_cols = [c for c in names if c != date_col]
    if not ret_cols:
        return pl.LazyFrame(
            {"name": [], "year": [], "month": [], out_col: []},
            schema={"name": pl.Utf8, "year": pl.Int32, "month": pl.Int32, out_col: pl.Float64},
        )

    long = (
        returns_lf
        .select([pl.col(date_col)] + [pl.col(c) for c in ret_cols])
        .melt(id_vars=date_col, value_vars=list(ret_cols), variable_name="name", value_name="_ret")
    )
    d = pl.col(date_col)
    return (
        long.with_columns([d.dt.year().alias("year"), d.dt.month().alias("month")])
            .group_by(["name", "year", "month"])
            .agg(((pl.col("_ret") + 1.0).product() - 1.0).alias(out_col))
            .select(["name", "year", "month", out_col])
    )


def single_series_yearly_returns(
    lf: pl.LazyFrame,
    *,
    series_col: str,
    date_col: str = "date",
    out_col: str = "eoy",
) -> pl.LazyFrame:
    """
    Compute yearly returns for a single series column (e.g., benchmark).
    Returns LONG lazy frame: ['year', out_col].
    """
    return (
        lf.with_columns(pl.col(date_col).dt.year().alias("year"))
          .group_by("year")
          .agg(((pl.col(series_col) + 1.0).product() - 1.0).alias(out_col))
          .select(["year", out_col])
          .sort("year")
    )