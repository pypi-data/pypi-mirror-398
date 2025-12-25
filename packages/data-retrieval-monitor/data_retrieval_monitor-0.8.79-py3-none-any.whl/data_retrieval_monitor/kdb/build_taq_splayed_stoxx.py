#!/usr/bin/env python3
"""
build_taq_splayed_stoxx.py

Goal
----
For each day from yesterday back to 2 years ago (daily), compute TAQ (trades + asof quotes mid)
ONLY for primaryRICs that are in the STOXX universe for that date:

  universe: .eqexec.idxCmp[date; `.STOXX]

Universe table columns: date, index, RIC, weight
We treat universe.RIC as the "allowed set" and filter trades on trades.primaryRIC.
Then we do:
  trades (SI) as-of join with quotes on (`primaryRIC, exchangeTime)
  mid = 0.5*(bid+ask)
  side = buy/sell/mid based on price vs mid

Performance / Efficiency
------------------------
- We do ONE TAQ query PER DATE (not per RIC). This avoids 100s of repeated scans.
- Inside that query, we:
  * get universe for that date
  * filter trades to universe RICs
  * filter quotes only to RICs that actually traded (further reduces quote scan)
  * sort both sides before aj (required)
  * optional: drop quotes after last trade time (safe, reduces rows)

Output
------
Saves splayed tables locally using PyKX, one per (date, primaryRIC):

  <out_root>/<YYYY.MM.DD>/<PRIMARY_RIC>/taq_single_ric/

After saving each splayed table, it reloads it and verifies row counts.

No pandas. Prints progress and timings for every step.

Usage (default: yesterday -> 2 years back):
  python build_taq_splayed_stoxx.py --host HOST --port 1234 --region ldn --out ./taq_out --skip-existing

Test one day, limit to first 10 RICs with trades:
  python build_taq_splayed_stoxx.py --host HOST --port 1234 --region ldn --out ./taq_out \
    --start-date 2025.11.12 --end-date 2025.11.12 --max-rics-per-day 10 --print-rics

/ taq_stoxx_day.q
/ Lightweight q functions for STOXX universe TAQ
/ Assumes tables: trades, quotes
/ Assumes universe function: .eqexec.idxCmp[date;`.STOXX]

/ Return STOXX universe for date d (raw)
stoxxUniverse:{[d] .eqexec.idxCmp[d;`.STOXX] };

/ Return list of RICs (as symbols) for date d
stoxxRics:{[d]
  u: stoxxUniverse[d];
  exec distinct RIC from u where not null RIC
};

/ Build TAQ for one day for STOXX constituents (SI trades only)
/ Returns a table with joined quotes, mid, side, and universe columns (index, weight)
taqStoxxDay:{[d]
  / universe -> align name to primaryRIC for joining
  u: stoxxUniverse[d];
  u: select date, primaryRIC:RIC, index, weight from u where not null RIC;
  uRics: exec distinct primaryRIC from u;

  / trades filtered to universe
  t: select date, primaryRIC, RIC, exchangeTime, captureTime, price, size, MIC, cond, eutradetype, trade_xid, mmt_class, aucType
     from trades
     where date=d, eutradetype=`SI, primaryRIC in uRics, not null exchangeTime;
  t: distinct t;
  t: `primaryRIC`exchangeTime xasc t;

  / if no trades, return empty table
  if[0=count t; :0#t];

  tradedRics: exec distinct primaryRIC from t;
  tmax: max t`exchangeTime;

  / quotes only for traded rics + quality filters + drop after last trade time
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

  / attach universe columns (index, weight)
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
# Small helpers
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
    return ":" + p  # q file symbol uses leading :


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
    kx.q('{[p;t] (`$p) set t}', qdir, tbl)
    save_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    loaded = kx.q('{[p] get (`$p)}', qdir)
    load_s = time.perf_counter() - t1

    loaded_rows = kx_count(loaded)

    del loaded
    gc.collect()

    return saved_rows, loaded_rows, save_s, load_s


# -----------------------------
# q builders
# -----------------------------
def q_universe_rics(date_q: str) -> str:
    """
    Returns a small table with distinct RIC for STOXX universe on date d.
    """
    return f"""
d:{date_q};
u: .eqexec.idxCmp[d;`.STOXX];
select distinct RIC from u where not null RIC
""".strip()


def q_taq_stoxx_day(date_q: str) -> str:
    """
    ONE query per date:
    - universe -> universeRics
    - trades filtered by primaryRIC in universe, eutradetype=`SI
    - quotes filtered by traded rics only + quality filters
    - aj join on (`primaryRIC, exchangeTime)
    - side classification
    - (optional) attach index + weight from universe via left join
    """
    return f"""
d:{date_q};

/ 1) STOXX universe for this date
u: .eqexec.idxCmp[d;`.STOXX];
u: select date, primaryRIC:RIC, index, weight from u where not null RIC;

/ rics in universe
uRics: exec distinct primaryRIC from u;

/ 2) Trades (SI) restricted to universe rics
trades_raw: select date, primaryRIC, RIC, exchangeTime, captureTime, price, size, MIC, cond, eutradetype, trade_xid, mmt_class, aucType
            from trades
            where date=d, eutradetype=`SI,
                  primaryRIC in uRics,
                  not null exchangeTime;
trades_raw: distinct trades_raw;
trades_raw: `primaryRIC`exchangeTime xasc trades_raw;

/ If no trades, return empty table (fast)
if[0=count trades_raw; :0#trades_raw];

/ 3) Quotes restricted to ONLY rics that traded (even lighter than universe list)
tradedRics: exec distinct primaryRIC from trades_raw;

/ Optional: drop quotes AFTER last trade time (safe)
tmax: max trades_raw`exchangeTime;

quotes_raw: select primaryRIC, exchangeTime, captureTime, bid, bidSize, ask, askSize, MIC, seqNo,
                   mid:0.5*(bid+ask)
            from quotes
            where date=d,
                  primaryRIC in tradedRics,
                  RIC=primaryRIC,
                  not null exchangeTime,
                  exchangeTime<=tmax,
                  not null bid, not null ask,
                  bid>0, ask>0;
quotes_raw: `primaryRIC`exchangeTime`captureTime xasc quotes_raw;

/ 4) As-of join + classify
taq: aj[`primaryRIC`exchangeTime; trades_raw; quotes_raw];
taq: update side:$[price>mid; `buy; price<mid; `sell; `mid] from taq;

/ 5) Attach universe columns (index, weight) by (date, primaryRIC)
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
    ap.add_argument("--max-days", type=int, default=0, help="If >0, limit number of days (debug)")

    ap.add_argument("--max-rics-per-day", type=int, default=0, help="If >0, limit number of RICs SAVED per day (debug)")
    ap.add_argument("--print-rics", action="store_true", help="Print all universe RICs (can be long)")

    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing output dirs")
    ap.add_argument("--skip-existing", action="store_true", help="Skip saving if output dir exists and non-empty")

    ap.add_argument("--continue-on-day-error", action="store_true", help="If a day fails, continue to next day")
    ap.add_argument("--continue-on-ric-error", action="store_true", help="If a ric save fails, continue to next ric")

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
    print(f"Date range: {start_date} .. {end_date} (processing {total_days} day(s), descending)")

    compass = Compass(host=args.host, port=args.port, region=args.region)

    overall_t0 = time.perf_counter()

    for day_idx, d in enumerate(iter_dates_desc(end_date, total_days), start=1):
        date_q = yyyy_mm_dd_to_qdate(d)
        print("\n" + "=" * 100)
        print(f"[DAY {day_idx}/{total_days}] date={date_q}")
        day_t0 = time.perf_counter()

        # Step A: universe rics (for printing / visibility)
        try:
            u_tbl, t_u = run_query(compass, q_universe_rics(date_q), label=f"UNIVERSE {date_q}")
            universe_rics = extract_symbol_list(u_tbl, "RIC")
            print(f"  Universe: {len(universe_rics)} RICs (took {fmt_s(t_u)})")
            if args.print_rics:
                print("  Universe RICs:", universe_rics)
            else:
                print("  Universe preview:", universe_rics[:20])
        except Exception:
            if args.continue_on_day_error:
                print("  Universe query failed; continuing to next day.")
                continue
            raise

        if len(universe_rics) == 0:
            print("  No universe constituents; skipping day.")
            continue

        # Step B: TAQ for the whole day (one query)
        try:
            taq_day, t_taq = run_query(compass, q_taq_stoxx_day(date_q), label=f"TAQ_DAY {date_q}")
        except Exception:
            if args.continue_on_day_error:
                print("  TAQ day query failed; continuing to next day.")
                continue
            raise

        rows_day = kx_count(taq_day)
        print(f"  TAQ day rows: {rows_day} (query took {fmt_s(t_taq)})")

        if rows_day == 0:
            print("  No trades for universe constituents; skipping day.")
            del taq_day
            gc.collect()
            continue

        # Step C: group by primaryRIC once (fast split)
        t0 = time.perf_counter()
        grouped = kx.q('`primaryRIC xgroup x', taq_day)
        t_group = time.perf_counter() - t0

        traded_keys = kx.q('key x', grouped)
        traded_rics = [s.decode("utf-8") if isinstance(s, (bytes, bytearray)) else str(s) for s in traded_keys.py()]
        print(f"  Traded RICs: {len(traded_rics)} (grouping took {fmt_s(t_group)})")
        print("  Traded preview:", traded_rics[:20])

        # Optionally limit number of rics saved per day (debug)
        if args.max_rics_per_day and args.max_rics_per_day > 0:
            traded_rics = traded_rics[: args.max_rics_per_day]
            print(f"  Limiting saves to first {len(traded_rics)} traded RICs due to --max-rics-per-day")

        # Step D: save each RIC table to splayed and verify
        for i, ric in enumerate(traded_rics, start=1):
            ric_t0 = time.perf_counter()
            ric_dir = sanitize_dir_name(ric)
            out_dir = os.path.join(out_root, date_q, ric_dir, "taq_single_ric")

            if args.skip_existing and os.path.isdir(out_dir) and os.listdir(out_dir):
                print(f"    [{i:04d}/{len(traded_rics):04d}] {ric}: SKIP existing")
                continue

            try:
                # pull grouped table for this ric without rescanning (dictionary lookup)
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

            ric_elapsed = time.perf_counter() - ric_t0
            print(f"      done {ric} in {fmt_s(ric_elapsed)}")

        # Cleanup day objects
        del grouped
        del taq_day
        gc.collect()

        day_elapsed = time.perf_counter() - day_t0
        print(f"[DAY DONE] {date_q} took {fmt_s(day_elapsed)}")

    overall_elapsed = time.perf_counter() - overall_t0
    print("\n" + "=" * 100)
    print(f"ALL DONE in {fmt_s(overall_elapsed)}")


if __name__ == "__main__":
    main()

