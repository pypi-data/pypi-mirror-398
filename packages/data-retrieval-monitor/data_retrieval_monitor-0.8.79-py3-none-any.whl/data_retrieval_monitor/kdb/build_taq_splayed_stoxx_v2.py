#!/usr/bin/env python3
"""
build_taq_splayed_stoxx_v2.py

Fixes the most common SOURCE of q 'rank' in your flow:
    .eqexec.idxCmp[date; `.STOXX]

If .eqexec.idxCmp is a KEYED TABLE (not a function), calling it with TWO arguments
causes 'rank'. The correct access pattern is ONE argument containing a 2-item key:
    .eqexec.idxCmp[(date; `.STOXX)]

This script makes universe retrieval robust by:
- Detecting the type of .eqexec.idxCmp
- Using:
    * function call    -> .eqexec.idxCmp[d; idx]
    * unkeyed table    -> select from .eqexec.idxCmp where date=d, index=idx
    * keyed table/dict -> .eqexec.idxCmp[(d; idx)]

Everything else is the same:
- For each day (yesterday back 2 years, daily):
  1) universe rics
  2) compute TAQ for that day (ONE query) restricted to universe
  3) split by primaryRIC and save each to splayed using PyKX, reload to verify
- Progress + timings printed at each step.

No pandas.

Usage:
  python build_taq_splayed_stoxx_v2.py --host HOST --port 1234 --region ldn --out ./taq_out --skip-existing

Test:
  python build_taq_splayed_stoxx_v2.py --host HOST --port 1234 --region ldn --out ./taq_out \
    --start-date 2025.11.12 --end-date 2025.11.12 --max-rics-per-day 10 --print-rics

/ taq_stoxx_day_v2.q
/ Lightweight q helpers for STOXX universe TAQ
/ FIX: handle `.eqexec.idxCmp` as function OR table OR keyed table (rank-safe)

/ Get universe for (date d, index idx) without rank error
getIdxCmp:{[d;idx]
  tc:abs type .eqexec.idxCmp;
  :$[
    tc>=100h; .eqexec.idxCmp[d; idx];                                  / function
    tc=98h;  select from .eqexec.idxCmp where date=d, index=idx;       / plain table
    .eqexec.idxCmp[(d; idx)]                                           / keyed table/dict
  ]
};

/ TAQ for one day for STOXX constituents (SI trades only)
taqStoxxDay:{[d; idx]
  u: getIdxCmp[d; idx];
  u: select date, primaryRIC:RIC, index, weight from u where not null RIC;
  uRics: exec distinct primaryRIC from u;

  t: select date, primaryRIC, RIC, exchangeTime, captureTime, price, size, MIC, cond, eutradetype, trade_xid, mmt_class, aucType
     from trades
     where date=d, eutradetype=`SI, primaryRIC in uRics, not null exchangeTime;
  t: distinct t;
  t: `primaryRIC`exchangeTime xasc t;
  if[0=count t; :0#t];

  tradedRics: exec distinct primaryRIC from t;
  tmax: max t`exchangeTime;

  q: select primaryRIC, exchangeTime, captureTime, bid, bidSize, ask, askSize, MIC, seqNo,
            mid:0.5*(bid+ask)
     from quotes
     where date=d,
           primaryRIC in tradedRics,
           RIC=primaryRIC,
           not null exchangeTime,
           exchangeTime<=tmax,
           not null bid, not null ask,
           bid>0, ask>0;
  q: `primaryRIC`exchangeTime`captureTime xasc q;

  taq: aj[`primaryRIC`exchangeTime; t; q];
  taq: update side:$[price>mid; `buy; price<mid; `sell; `mid] from taq;

  uKey: `date`primaryRIC xkey u;
  taq: taq lj uKey;

  taq
};

"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import os
import shutil
import time
from typing import Iterable, List, Tuple

import pykx as kx
from goldmansachs.compass_pykx import Compass


# -----------------------------
# Helpers
# -----------------------------
def fmt_s(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    return f"{seconds:.2f}s"


def yyyy_mm_dd_to_qdate(d: dt.date) -> str:
    return f"{d.year:04d}.{d.month:02d}.{d.day:02d}"


def sanitize_dir_name(s: str) -> str:
    return s.replace("/", "_").replace("\\", "_").replace(" ", "_")


def q_file_symbol_for_dir(dir_path: str) -> str:
    p = os.path.abspath(dir_path).replace("\\", "/")
    if not p.endswith("/"):
        p += "/"
    return ":" + p


def run_query(compass: Compass, q: str, label: str):
    t0 = time.perf_counter()
    try:
        res = compass.run_query_sync(q) if hasattr(compass, "run_query_sync") else compass.run_query(q)
    except Exception as e:
        print(f"\n[{label}] FAILED: {e}")
        print("----- q that failed -----")
        print(q.strip())
        print("-------------------------\n")
        raise
    return res, time.perf_counter() - t0


def kx_count(obj) -> int:
    return int(kx.q("count x", obj).py())


def extract_symbol_list(tbl, col: str) -> List[str]:
    vec = tbl[col]
    pyv = vec.py() if hasattr(vec, "py") else list(vec)
    out: List[str] = []
    for v in pyv:
        if isinstance(v, (bytes, bytearray)):
            out.append(v.decode("utf-8", errors="ignore"))
        else:
            out.append(str(v))
    return out


def save_splayed_and_reload(tbl, out_dir: str, overwrite: bool) -> Tuple[int, int, float, float]:
    if overwrite and os.path.exists(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)

    os.makedirs(out_dir, exist_ok=True)
    qdir = q_file_symbol_for_dir(out_dir)

    saved_rows = kx_count(tbl)

    t0 = time.perf_counter()
    kx.q('{[p;t] (`$p) set t}', qdir, tbl)  # splayed save
    save_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    loaded = kx.q('{[p] get (`$p)}', qdir)
    load_s = time.perf_counter() - t1

    loaded_rows = kx_count(loaded)

    del loaded
    gc.collect()

    return saved_rows, loaded_rows, save_s, load_s


# -----------------------------
# q builders (rank-safe universe)
# -----------------------------
def q_get_universe(date_q: str, idx_symbol: str = ".STOXX") -> str:
    """
    Returns STOXX universe table for date d in a RANK-SAFE way.
    """
    return f"""
d:{date_q};
idx:`{idx_symbol};

/ rank-safe universe retrieval
tc: abs type .eqexec.idxCmp;
u: $[
    tc>=100h; .eqexec.idxCmp[d; idx];                 / function
    tc=98h;  select from .eqexec.idxCmp where date=d, index=idx; / plain table
    .eqexec.idxCmp[(d; idx)]                          / keyed table / dict style
];
u
""".strip()


def q_universe_rics(date_q: str, idx_symbol: str = ".STOXX") -> str:
    """
    Small table: distinct RIC from universe on date.
    """
    return f"""
u: {q_get_universe(date_q, idx_symbol)};
select distinct RIC from u where not null RIC
""".strip()


def q_taq_stoxx_day(date_q: str, idx_symbol: str = ".STOXX") -> str:
    """
    ONE query per date:
    - get universe (rank-safe)
    - filter trades to universe rics (by trades.primaryRIC)
    - filter quotes to traded rics
    - aj join + mid + side
    - attach universe columns (index, weight)
    """
    return f"""
d:{date_q};
idx:`{idx_symbol};

tc: abs type .eqexec.idxCmp;
u: $[
    tc>=100h; .eqexec.idxCmp[d; idx];
    tc=98h;  select from .eqexec.idxCmp where date=d, index=idx;
    .eqexec.idxCmp[(d; idx)]
];

/ align universe column name to primaryRIC for joining
u: select date, primaryRIC:RIC, index, weight from u where not null RIC;
uRics: exec distinct primaryRIC from u;

/ trades (SI) restricted to universe rics
t: select date, primaryRIC, RIC, exchangeTime, captureTime, price, size, MIC, cond, eutradetype, trade_xid, mmt_class, aucType
   from trades
   where date=d, eutradetype=`SI, primaryRIC in uRics, not null exchangeTime;
t: distinct t;
t: `primaryRIC`exchangeTime xasc t;

if[0=count t; :0#t];

/ quotes restricted to traded rics only
tradedRics: exec distinct primaryRIC from t;
tmax: max t`exchangeTime;

q: select primaryRIC, exchangeTime, captureTime, bid, bidSize, ask, askSize, MIC, seqNo,
          mid:0.5*(bid+ask)
   from quotes
   where date=d,
         primaryRIC in tradedRics,
         RIC=primaryRIC,
         not null exchangeTime,
         exchangeTime<=tmax,
         not null bid, not null ask,
         bid>0, ask>0;
q: `primaryRIC`exchangeTime`captureTime xasc q;

/ asof join + classify
taq: aj[`primaryRIC`exchangeTime; t; q];
taq: update side:$[price>mid; `buy; price<mid; `sell; `mid] from taq;

/ attach universe columns
uKey: `date`primaryRIC xkey u;
taq: taq lj uKey;

taq
""".strip()


# -----------------------------
# Date iteration
# -----------------------------
def iter_dates_desc(end_date: dt.date, n_days: int) -> Iterable[dt.date]:
    for i in range(n_days):
        yield end_date - dt.timedelta(days=i)


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")

    ap.add_argument("--out", required=True, help="Output root directory for splayed tables")

    ap.add_argument("--start-date", default=None, help="YYYY-MM-DD or YYYY.MM.DD (optional)")
    ap.add_argument("--end-date", default=None, help="YYYY-MM-DD or YYYY.MM.DD (optional). Default: yesterday")

    ap.add_argument("--years-back", type=int, default=2)
    ap.add_argument("--max-days", type=int, default=0, help="If >0, limit days (debug)")

    ap.add_argument("--max-rics-per-day", type=int, default=0, help="If >0, limit number of RICs saved per day")
    ap.add_argument("--print-rics", action="store_true")

    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")

    ap.add_argument("--continue-on-day-error", action="store_true")
    ap.add_argument("--continue-on-ric-error", action="store_true")

    ap.add_argument("--index-symbol", default=".STOXX", help="Universe index symbol (default .STOXX)")

    args = ap.parse_args()

    out_root = os.path.abspath(args.out)
    os.makedirs(out_root, exist_ok=True)

    # Date range
    if args.end_date:
        end_date = dt.date.fromisoformat(args.end_date.replace(".", "-"))
    else:
        end_date = dt.date.today() - dt.timedelta(days=1)

    if args.start_date:
        start_date = dt.date.fromisoformat(args.start_date.replace(".", "-"))
    else:
        start_date = end_date - dt.timedelta(days=365 * args.years_back)

    if start_date > end_date:
        raise SystemExit(f"start-date {start_date} is after end-date {end_date}")

    total_days = (end_date - start_date).days + 1
    if args.max_days and args.max_days > 0:
        total_days = min(total_days, args.max_days)

    print(f"Output root: {out_root}")
    print(f"Index: {args.index_symbol}")
    print(f"Date range: {start_date} .. {end_date} (processing {total_days} day(s), descending)")

    compass = Compass(host=args.host, port=args.port, region=args.region)

    overall_t0 = time.perf_counter()

    for day_idx, d in enumerate(iter_dates_desc(end_date, total_days), start=1):
        date_q = yyyy_mm_dd_to_qdate(d)
        print("\n" + "=" * 100)
        print(f"[DAY {day_idx}/{total_days}] date={date_q}")
        day_t0 = time.perf_counter()

        # A) Universe RICs
        try:
            u_tbl, t_u = run_query(compass, q_universe_rics(date_q, args.index_symbol), label=f"UNIVERSE_RICS {date_q}")
            universe_rics = extract_symbol_list(u_tbl, "RIC")
            print(f"  Universe: {len(universe_rics)} RICs (took {fmt_s(t_u)})")
            if args.print_rics:
                print("  Universe RICs:", universe_rics)
            else:
                print("  Universe preview:", universe_rics[:20])
        except Exception:
            if args.continue_on_day_error:
                print("  Universe query failed; continuing.")
                continue
            raise

        if len(universe_rics) == 0:
            print("  No universe constituents; skipping day.")
            continue

        # B) TAQ day (ONE query)
        try:
            taq_day, t_taq = run_query(compass, q_taq_stoxx_day(date_q, args.index_symbol), label=f"TAQ_DAY {date_q}")
        except Exception:
            if args.continue_on_day_error:
                print("  TAQ day query failed; continuing.")
                continue
            raise

        rows_day = kx_count(taq_day)
        print(f"  TAQ day rows: {rows_day} (query took {fmt_s(t_taq)})")
        if rows_day == 0:
            del taq_day
            gc.collect()
            print(f"[DAY DONE] {date_q} took {fmt_s(time.perf_counter()-day_t0)} (no trades)")
            continue

        # C) split by primaryRIC (local, fast)
        t0 = time.perf_counter()
        grouped = kx.q('`primaryRIC xgroup x', taq_day)
        t_group = time.perf_counter() - t0

        keys = kx.q('key x', grouped).py()
        traded_rics = [k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else str(k) for k in keys]
        print(f"  Traded RICs: {len(traded_rics)} (grouping took {fmt_s(t_group)})")
        print("  Traded preview:", traded_rics[:20])

        if args.max_rics_per_day and args.max_rics_per_day > 0:
            traded_rics = traded_rics[: args.max_rics_per_day]
            print(f"  Limiting saves to first {len(traded_rics)} traded RICs")

        # D) save each ric
        for i, ric in enumerate(traded_rics, start=1):
            ric_t0 = time.perf_counter()
            out_dir = os.path.join(out_root, date_q, sanitize_dir_name(ric), "taq_single_ric")

            if args.skip_existing and os.path.isdir(out_dir) and os.listdir(out_dir):
                print(f"    [{i:04d}/{len(traded_rics):04d}] {ric}: SKIP existing")
                continue

            try:
                sub = kx.q('{[g;r] g[`$r]}', grouped, ric)
                sub_rows = kx_count(sub)
                print(f"    [{i:04d}/{len(traded_rics):04d}] {ric}: rows={sub_rows} ... ", end="", flush=True)

                saved_rows, loaded_rows, t_save, t_load = save_splayed_and_reload(sub, out_dir, overwrite=args.overwrite)
                ok = (saved_rows == loaded_rows)
                print(f"saved={saved_rows} loaded={loaded_rows} ok={ok} (save {fmt_s(t_save)}, load {fmt_s(t_load)})")

                del sub
                gc.collect()

            except Exception as e:
                print(f"\n      ERROR saving {ric}: {e}")
                if not args.continue_on_ric_error:
                    raise

            print(f"      done {ric} in {fmt_s(time.perf_counter()-ric_t0)}")

        del grouped
        del taq_day
        gc.collect()

        print(f"[DAY DONE] {date_q} took {fmt_s(time.perf_counter()-day_t0)}")

    print("\n" + "=" * 100)
    print(f"ALL DONE in {fmt_s(time.perf_counter()-overall_t0)}")


if __name__ == "__main__":
    main()
