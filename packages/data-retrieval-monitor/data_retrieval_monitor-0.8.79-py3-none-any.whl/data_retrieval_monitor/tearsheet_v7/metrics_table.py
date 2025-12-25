# metrics_table.py
# Thin aggregator: melt/cache once; call modular functions from metrics.py; concat → single pivot.

from __future__ import annotations

import math
import inspect
import importlib.util
import types
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, Union, Iterable, List, Callable, Dict, Tuple

import polars as pl

# Import modular metric functions
from metrics import (
    # base metrics
    comp, cagr, sharpe, sortino, vol_ann, exposure, avg_win, avg_loss, payoff,
    best_day, worst_day, skew, kurtosis, win_rate, calmar,
    # drawdown core & numerics
    dd_episodes, ulcer, max_drawdown,
    # episode filters & leaf metrics
    filter_episodes, avg_drawdown_from_ep, longest_dd_days_from_ep, avg_dd_days_from_ep,
    # drawdown dates (strings)
    max_dd_date, max_dd_start, max_dd_end,
    # extremes
    best_month, worst_month, best_year, worst_year,
    # tails
    VaR_5, CVaR_5, omega_0,
    # period slices
    mtd, last_3m, last_6m, ytd, last_1y, ann_3y, ann_5y, ann_10y, ann_alltime,
)


# =========================
# Utilities
# =========================
def _as_lazy(x: Union[pl.DataFrame, pl.LazyFrame]) -> pl.LazyFrame:
    return x.lazy() if isinstance(x, pl.DataFrame) else x


def _schema(lf: pl.LazyFrame) -> Tuple[List[str], List[pl.DataType]]:
    sch = lf.collect_schema()
    return sch.names(), sch.dtypes()


def _ensure_datetime_ns(lf: pl.LazyFrame, date_col: str = "date") -> pl.LazyFrame:
    # Ensure datetime type and cast to ns (robust for .dt ops)
    return lf.with_columns(pl.col(date_col).cast(pl.Datetime).dt.cast_time_unit("ns"))


def _to_long_num(df: pl.LazyFrame | pl.DataFrame, cols: List[str]) -> pl.LazyFrame:
    # returns LONG: ["name","metric","value(Float64)"]
    if isinstance(df, pl.DataFrame):
        df = df.lazy()
    cols = [c for c in cols if c != "name"]
    if not cols:
        return df.select(pl.lit(None).alias("value")).filter(pl.lit(False))
    return (
        df.melt(id_vars="name", value_vars=cols, variable_name="metric", value_name="value")
          .with_columns(pl.col("value").cast(pl.Float64))
    )


def _to_long_str(df: pl.LazyFrame | pl.DataFrame, cols: List[str]) -> pl.LazyFrame:
    # returns LONG: ["name","metric","value(Utf8)"]
    if isinstance(df, pl.DataFrame):
        df = df.lazy()
    cols = [c for c in cols if c != "name"]
    if not cols:
        return df.select(pl.lit(None).alias("value")).filter(pl.lit(False))
    df2 = df.with_columns([pl.col(c).cast(pl.Utf8) for c in cols])
    return df2.melt(id_vars="name", value_vars=cols, variable_name="metric", value_name="value")


# =========================
# Tiny custom-metric registry (numeric only)
# =========================
Expr1 = Callable[[pl.Expr], pl.Expr]            # lambda r: ...
Expr2 = Callable[[pl.Expr, pl.Expr], pl.Expr]   # lambda r, b: ...

class SimpleRegistry:
    """Register easy numeric metrics as Polars Expr lambdas."""
    def __init__(self) -> None:
        self.num1: List[tuple[str, Expr1]] = []  # (name, fn(r))
        self.num2: List[tuple[str, Expr2]] = []  # (name, fn(r,b))

    def register(self, fn: Callable[..., pl.Expr], *, name: Optional[str] = None) -> "SimpleRegistry":
        try:
            ar = fn.__code__.co_argcount
        except Exception:
            ar = 1
        nm = name or getattr(fn, "__name__", None) or f"metric_{len(self.num1)+len(self.num2)}"
        if ar == 1:
            self.num1.append((nm, fn))     # type: ignore[arg-type]
        elif ar == 2:
            self.num2.append((nm, fn))     # type: ignore[arg-type]
        else:
            raise ValueError("Custom metric must be unary (r) or binary (r, b).")
        return self

    def register_map(self, m: Dict[str, Callable[..., pl.Expr]]) -> "SimpleRegistry":
        for k, v in m.items():
            self.register(v, name=k)
        return self

    def empty(self) -> bool:
        return not (self.num1 or self.num2)


# ============================================================
# AGGREGATOR (thin): melt/cache; run builders; concat -> ONE pivot
# ============================================================
def metrics_polars(
    returns: Union[pl.DataFrame, pl.LazyFrame],
    benchmark: Optional[Union[pl.DataFrame, pl.LazyFrame]] = None,
    *,
    rf: float = 0.0,
    periods_per_year: int = 252,
    dd_batch: int = 512,
    mode: str = "full",  # compatibility (unused)
    return_long: bool = False,
    builders_num: Optional[Iterable[Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]]] = None,
    builders_str: Optional[Iterable[Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]]] = None,
    registry: Optional[SimpleRegistry] = None,
    builders_module: Optional[Union[str, types.ModuleType]] = None,
) -> pl.DataFrame:
    """
    Build the FULL metrics table by concatenating LONG frames from builders, then pivoting once.
    Returns a WIDE DataFrame with a 'metric' column and one col per strategy/benchmark.
    """
    # 0) wide -> lazy + ns date
    R = _ensure_datetime_ns(_as_lazy(returns))
    if isinstance(returns, pl.DataFrame):
        ret_cols = [c for c in returns.columns if c != "date"]
    else:
        ret_cols = [c for c in _schema(R)[0] if c != "date"]

    # 1) optional benchmark appended as first column
    B_series: Optional[pl.LazyFrame] = None
    bcol: Optional[str] = None
    if benchmark is not None:
        B = _ensure_datetime_ns(_as_lazy(benchmark))
        bn, _ = _schema(B)
        bnames = [c for c in bn if c != "date"]
        if len(bnames) != 1:
            raise ValueError(f"Benchmark must have exactly one non-'date' column; found {bnames}")
        bcol = bnames[0]
        B_series = B.select(pl.col("date"), pl.col(bcol).alias("b"))
        R = R.join(B.select(["date", pl.col(bcol).alias(bcol)]), on="date", how="left")
        # ensure benchmark is first in ret_cols
        ret_cols = [bcol] + [c for c in ret_cols if c != bcol]

    # 2) melt once & cache
    Rc = (
        R.melt(id_vars=["date"], value_vars=ret_cols, variable_name="name", value_name="r")
         .with_columns([
             (pl.col("r") - rf).alias("r") if rf else pl.col("r"),
             pl.col("name").cast(pl.Categorical()),
         ])
         .cache()
    )
    last_date = Rc.select(pl.max("date").alias("last")).collect()["last"][0]

    # 3) ctx for builders
    ctx = {
        "ppy": periods_per_year,
        "rf": rf,
        "dd_batch": dd_batch,
        "last_date": last_date,
        "ret_cols": ret_cols,
    }

    # 4) run builders -> LONG parts
    num_parts: List[pl.LazyFrame] = []
    str_parts: List[pl.LazyFrame] = []

    # Decide builder packs (include registry ONCE via build_default_builders)
    if builders_module is not None:
        try:
            auto_num, auto_str = discover_builders_from_module(builders_module, dd_batch=dd_batch)
        except Exception:
            auto_num, auto_str = [], []
        builders_num = list(auto_num)
        builders_str = list(auto_str)
        if registry is not None and not registry.empty():
            builders_num.append(expr_long_block(registry))
    elif builders_num is None and builders_str is None:
        if registry is not None:
            builders_num, builders_str = build_default_builders(registry=registry, dd_batch=dd_batch)
        else:
            builders_num, builders_str = _DEFAULT_NUM, _DEFAULT_STR

    # numeric builders
    if builders_num:
        for build in builders_num:
            num_parts.append(build(Rc, B_series, ctx))

    # IMPORTANT: do NOT auto-append the registry block here;
    # if you pass custom builders explicitly, include expr_long_block(registry) yourself.

    # string builders
    if builders_str:
        for build in builders_str:
            str_parts.append(build(Rc, B_series, ctx))

    if not num_parts and not str_parts:
        return pl.DataFrame({"metric": []})

    # 5) pivot numeric once (dedup metric/name before pivot)
    wide_parts: List[pl.DataFrame] = []
    if num_parts:
        long_num = pl.concat(num_parts).with_columns(pl.col("name").cast(pl.Utf8))
        long_num = long_num.group_by(["metric", "name"]).agg(pl.col("value").first().alias("value"))
        wide_num = long_num.collect().pivot(values="value", index="metric", on="name")
        # cast numeric to Utf8 to allow diagonal concat with string block
        wide_num = wide_num.with_columns([pl.col(c).cast(pl.Utf8) for c in wide_num.columns if c != "metric"])
        wide_parts.append(wide_num)

    # 6) pivot string once (dedup too)
    if str_parts:
        long_str = pl.concat(str_parts).with_columns(pl.col("name").cast(pl.Utf8))
        long_str = long_str.group_by(["metric", "name"]).agg(pl.col("value").first().alias("value"))
        wide_str = long_str.collect().pivot(values="value", index="metric", on="name")
        wide_parts.append(wide_str)

    if not wide_parts:
        return pl.DataFrame({"metric": []})

    # 7) assemble diagonally (row-union), benchmark first if present
    wide = pl.concat(wide_parts, how="diagonal")

    if bcol and bcol in wide.columns:
        wide = wide.select(["metric", bcol] + [c for c in wide.columns if c not in ("metric", bcol)])

    if return_long:
        return (
            wide.melt(id_vars="metric", variable_name="name", value_name="value")
                .filter(pl.col("name") != "metric")
                .select(["name","metric","value"])
                .sort(["metric","name"])
        ).collect()

    return wide.sort("metric")


# ============================================================
# BUILDERS (assemble LONG frames from standalone functions)
# ============================================================

def base_long() -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """Risk/Return base metrics composed from standalone functions."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        parts: List[pl.LazyFrame] = []
        parts.append(_to_long_num(comp(Rc, ctx), ["comp"]))
        parts.append(_to_long_num(cagr(Rc, ctx), ["cagr"]))
        parts.append(_to_long_num(sharpe(Rc, ctx), ["sharpe"]))
        parts.append(_to_long_num(sortino(Rc, ctx), ["sortino"]))
        parts.append(_to_long_num(vol_ann(Rc, ctx), ["vol_ann"]))
        parts.append(_to_long_num(exposure(Rc, ctx), ["exposure"]))
        parts.append(_to_long_num(avg_win(Rc, ctx), ["avg_win"]))
        parts.append(_to_long_num(avg_loss(Rc, ctx), ["avg_loss"]))
        parts.append(_to_long_num(payoff(Rc, ctx), ["payoff"]))
        parts.append(_to_long_num(best_day(Rc, ctx), ["best_day"]))
        parts.append(_to_long_num(worst_day(Rc, ctx), ["worst_day"]))
        parts.append(_to_long_num(skew(Rc, ctx), ["skew"]))
        parts.append(_to_long_num(kurtosis(Rc, ctx), ["kurtosis"]))
        parts.append(_to_long_num(win_rate(Rc, ctx), ["win_rate"]))
        return pl.concat(parts) if parts else Rc.select(pl.lit(None).alias("value")).filter(pl.lit(False))
    return _block


def drawdowns_num_long(
    dd_batch: Optional[int] = None,
    *,
    avg_dd_mode: str = "mean",      # "mean" or "topK"
    topk: int = 10,                 # used when avg_dd_mode == "topK"
    min_len: int = 0,               # episode length threshold
    len_unit: str = "periods",      # "days" | "periods"
    min_depth: float = 0.0,         # require |min_dd| >= min_depth
) -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """Numeric DD metrics from standalone functions (thin orchestrator)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        names_list: List[str] = ctx["ret_cols"]
        batch = dd_batch or ctx["dd_batch"]
        out_parts: List[pl.LazyFrame] = []
        for i in range(0, len(names_list), max(1, batch)):
            chunk = names_list[i:i + batch]
            sub = Rc.filter(pl.col("name").is_in(chunk))
            names = sub.select("name").unique()

            parts = [
                _to_long_num(max_drawdown(sub, ctx), ["max_drawdown"]),
                _to_long_num(ulcer(sub, ctx), ["ulcer"]),
            ]

            ep  = dd_episodes(sub, ctx)
            epf = filter_episodes(ep, min_len=min_len, len_unit=len_unit, min_depth=min_depth)

            avg_dd = names.join(
                avg_drawdown_from_ep(epf, mode=avg_dd_mode, topk=topk), on="name", how="left"
            ).select(["name", "avg_drawdown"])

            longest = names.join(
                longest_dd_days_from_ep(epf), on="name", how="left"
            ).with_columns(pl.col("longest_dd_days").fill_null(0.0).cast(pl.Float64)) \
             .select(["name", "longest_dd_days"])

            avg_days = names.join(
                avg_dd_days_from_ep(epf), on="name", how="left"
            ).with_columns(pl.col("avg_dd_days").fill_null(0.0).cast(pl.Float64)) \
             .select(["name", "avg_dd_days"])

            parts.extend([
                _to_long_num(avg_dd,   ["avg_drawdown"]),
                _to_long_num(longest,  ["longest_dd_days"]),
                _to_long_num(avg_days, ["avg_dd_days"]),
            ])

            out_parts.append(pl.concat(parts))
        return pl.concat(out_parts) if out_parts else Rc.select(pl.lit(None).alias("value")).filter(pl.lit(False))
    return _block


def drawdown_dates_long(dd_batch: Optional[int] = None) -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """String DD labels (dates of valley, start, end)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        names_list: List[str] = ctx["ret_cols"]
        batch = dd_batch or ctx["dd_batch"]
        out_parts: List[pl.LazyFrame] = []
        for i in range(0, len(names_list), max(1, batch)):
            chunk = names_list[i:i + batch]
            sub = Rc.filter(pl.col("name").is_in(chunk))
            parts = [
                _to_long_str(max_dd_date(sub, ctx), ["max_dd_date"]),
                _to_long_str(max_dd_start(sub, ctx), ["max_dd_start"]),
                _to_long_str(max_dd_end(sub, ctx), ["max_dd_end"]),
            ]
            out_parts.append(pl.concat(parts))
        return pl.concat(out_parts) if out_parts else Rc.select(pl.lit(None).alias("value")).filter(pl.lit(False))
    return _block


def calmar_long() -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """Calmar (numeric)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        return _to_long_num(calmar(Rc, ctx), ["calmar"])
    return _block


def extremes_long() -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """Best/worst month & year (numeric)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        parts = [
            _to_long_num(best_month(Rc, ctx), ["best_month"]),
            _to_long_num(worst_month(Rc, ctx), ["worst_month"]),
            _to_long_num(best_year(Rc, ctx), ["best_year"]),
            _to_long_num(worst_year(Rc, ctx), ["worst_year"]),
        ]
        return pl.concat(parts)
    return _block


def tails_long() -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """VaR_5, CVaR_5, Omega_0 (numeric)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        parts = [
            _to_long_num(VaR_5(Rc, ctx), ["VaR_5"]),
            _to_long_num(CVaR_5(Rc, ctx), ["CVaR_5"]),
            _to_long_num(omega_0(Rc, ctx), ["omega_0"]),
        ]
        return pl.concat(parts)
    return _block


def period_slices_long() -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """MTD, 3m, 6m, YTD, 1y, 3y_ann, 5y_ann, 10y_ann, alltime_ann (numeric)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        parts = [
            _to_long_num(mtd(Rc, ctx), ["mtd"]),
            _to_long_num(last_3m(Rc, ctx), ["3m"]),
            _to_long_num(last_6m(Rc, ctx), ["6m"]),
            _to_long_num(ytd(Rc, ctx), ["ytd"]),
            _to_long_num(last_1y(Rc, ctx), ["1y"]),
            _to_long_num(ann_3y(Rc, ctx), ["3y_ann"]),
            _to_long_num(ann_5y(Rc, ctx), ["5y_ann"]),
            _to_long_num(ann_10y(Rc, ctx), ["10y_ann"]),
            _to_long_num(ann_alltime(Rc, ctx), ["alltime_ann"]),
        ]
        return pl.concat(parts)
    return _block


# =========================
# Registry → LONG (numeric only)
# =========================
def expr_long_block(registry: SimpleRegistry) -> Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]:
    """Compile registered lambdas into one unary and one binary agg, then LONG-ify (numeric only)."""
    def _block(Rc: pl.LazyFrame, B: Optional[pl.LazyFrame], ctx: dict) -> pl.LazyFrame:
        parts: List[pl.LazyFrame] = []
        returns = pl.col("r")
        if registry.num1:
            wide1 = Rc.group_by("name").agg([fn(returns).alias(nm) for nm, fn in registry.num1])
            parts.append(_to_long_num(wide1, [c for c in wide1.collect_schema().names() if c != "name"]))
        if registry.num2 and B is not None:
            Rcb = Rc.join(B, on="date", how="inner")
            wide2 = Rcb.group_by("name").agg([fn(returns, pl.col("b")).alias(nm) for nm, fn in registry.num2])
            parts.append(_to_long_num(wide2, [c for c in wide2.collect_schema().names() if c != "name"]))
        return pl.concat(parts) if parts else Rc.select(pl.lit(None).alias("value")).filter(pl.lit(False))
    return _block


# =========================
# Default builders pack
# =========================
def build_default_builders(
    *, registry: Optional[SimpleRegistry] = None, dd_batch: int = 512
) -> tuple[list, list]:
    """Return (builders_num, builders_str)."""
    builders_num = [
        base_long(),
        drawdowns_num_long(dd_batch),
        calmar_long(),
        extremes_long(),
        tails_long(),
        period_slices_long(),
    ]
    if registry and not registry.empty():
        builders_num.append(expr_long_block(registry))

    builders_str = [
        drawdown_dates_long(dd_batch),  # DD dates split to preserve numeric schema
    ]
    return builders_num, builders_str


# --- module-level defaults the dashboard will use
_DEFAULT_NUM, _DEFAULT_STR = build_default_builders(dd_batch=512)


def set_default_builders(
    *,
    builders_num: Optional[Iterable[Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]]] = None,
    builders_str: Optional[Iterable[Callable[[pl.LazyFrame, Optional[pl.LazyFrame], dict], pl.LazyFrame]]] = None,
    registry: Optional[SimpleRegistry] = None,
    dd_batch: int = 512,
) -> None:
    """
    Configure the default builders used by metrics_polars() when none are passed explicitly.
    Call this once in your app before creating the dashboard.
    """
    global _DEFAULT_NUM, _DEFAULT_STR
    if registry is not None and (builders_num is None and builders_str is None):
        _DEFAULT_NUM, _DEFAULT_STR = build_default_builders(registry=registry, dd_batch=dd_batch)
        return
    _DEFAULT_NUM = list(builders_num) if builders_num is not None else _DEFAULT_NUM
    _DEFAULT_STR = list(builders_str) if builders_str is not None else _DEFAULT_STR


# =========================
# Builder auto-discovery
# =========================
def _load_module_from_path(path: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("_metrics_builders_module", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import module from path: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def discover_builders_from_module(
    module_or_path: Union[str, types.ModuleType], *, dd_batch: int = 512
) -> tuple[list, list]:
    """
    Discover builder factories in a module and return (numeric_builders, string_builders).
    Convention: functions named '*_long' that take no required args (or only optional 'dd_batch')
    are considered builder factories. We categorize as string-producing if the name contains
    'date' or 'label'; otherwise numeric. Functions like 'expr_long_block' (requiring registry)
    are skipped during discovery.
    """
    if isinstance(module_or_path, str):
        mod = _load_module_from_path(module_or_path)
    else:
        mod = module_or_path

    funcs = [
        (name, obj)
        for name, obj in inspect.getmembers(mod, inspect.isfunction)
        if obj.__module__ == mod.__name__ and name.endswith("_long")
    ]

    num_builders: list = []
    str_builders: list = []

    for name, fn in funcs:
        if name == "expr_long_block":
            continue
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())
        can_call = True
        kwargs = {}
        if params:
            # if any required param, skip
            if any(p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in params):
                can_call = False
            if any(p.name == "dd_batch" for p in params):
                kwargs["dd_batch"] = dd_batch
        if not can_call:
            continue
        try:
            builder = fn(**kwargs)
        except Exception:
            continue
        is_str = ("date" in name) or ("label" in name)
        if is_str:
            str_builders.append(builder)
        else:
            num_builders.append(builder)

    return num_builders, str_builders