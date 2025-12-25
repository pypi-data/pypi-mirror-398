#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v3.py

Goal: Debug-friendly slicing with separate trades/quotes queries AND server-side asof join classification.
- No pandas.
- Avoids common q "type" errors by computing slice bounds in LONG nanoseconds, then casting back to timespan ("n"$).

Run:
  python trade_quote_classify_sliced_v3.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --max-slices 5 --show-trades 5 --show-quotes 5 --show-result 5
"""

from __future__ import annotations

import argparse
from goldmansachs.compass_pykx import Compass


def q_date_literal(s: str) -> str:
    s = s.strip()
    return s.replace("-", ".") if "-" in s else s


def q_symbol_literal(s: str) -> str:
    s = s.strip()
    return s if s.startswith("`") else f"`{s}"


def run_query(compass: Compass, q: str):
    try:
        return compass.run_query_sync(q)
    except Exception:
        print("\nFAILED q:\n" + "-" * 80)
        print(q)
        print("-" * 80)
        raise


def q_bounds_and_ns_vars(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    """
    Defines: tminN,tmaxN,chunkN,lbN,n,sN,eN,s,e,sLb,e (timespans)
    Uses half-open slice [s,e) with a +1ns on last slice.
    Clamps sLb at 0D00:00:00 if lookback pushes negative.
    """
    return f"""
    d:{d};
    ric:{ric};
    chunk:{chunk};
    lb:{lb};
    i:{i};

    b: select tmin:min exchangeTime, tmax:max exchangeTime
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    / if no trades, return 0 (caller will handle)
    if[null b`tmin; :`noTrades];

    tminN: long$ b`tmin;
    tmaxN: long$ b`tmax;
    chunkN: long$ chunk;
    lbN:    long$ lb;

    n: 1 + (tmaxN - tminN) div chunkN;

    sN: tminN + chunkN * i;
    eN: $[i=n-1; tmaxN + 1; tminN + chunkN * (i+1)];  / +1ns on last slice

    s: "n"$sN;
    e: "n"$eN;

    sLbN: sN - lbN;
    if[sLbN < 0; sLbN: 0];
    sLb: "n"$sLbN;
    """


def q_n_slices(d: str, ric: str, chunk: str) -> str:
    return f"""
    d:{d}; ric:{ric}; chunk:{chunk};

    b: select tmin:min exchangeTime, tmax:max exchangeTime
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    $[null b`tmin; 0; 1 + (long$b`tmax - long$b`tmin) div long$chunk]
    """


def q_diag_types(d: str, ric: str) -> str:
    # Pull one row from each table to check types
    return f"""
    d:{d}; ric:{ric};
    t1: 1#select date,RIC,exchangeTime,captureTime,price from trades where date=d, RIC=ric, not null exchangeTime;
    q1: 1#select date,RIC,exchangeTime,captureTime,bid,ask from quotes where date=d, RIC=ric, not null exchangeTime;

    ([] table:`trades`quotes;
        exchangeTimeType:(type first t1`exchangeTime; type first q1`exchangeTime);
        RICType:(type first t1`RIC; type first q1`RIC);
        dateType:(type first t1`date; type first q1`date);
        captureTimeType:(type first t1`captureTime; type first q1`captureTime);
        priceType:(type first t1`price; 0N);
        bidType:(0N; type first q1`bid);
        askType:(0N; type first q1`ask)
    )
    """


def q_trades_count(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return q_bounds_and_ns_vars(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :0];  / never happens; kept for safety
    exec count i
    from trades
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s, exchangeTime<e
    """


def q_trades_sample(d: str, ric: str, chunk: str, lb: str, i: int, nrows: int) -> str:
    return q_bounds_and_ns_vars(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];
    {nrows}#select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid
    from trades
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s, exchangeTime<e
    """


def q_quotes_count(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return q_bounds_and_ns_vars(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :0];
    exec count i
    from quotes
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=sLb, exchangeTime<e
    """


def q_quotes_sample(d: str, ric: str, chunk: str, lb: str, i: int, nrows: int) -> str:
    return q_bounds_and_ns_vars(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];
    {nrows}#select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
    from quotes
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=sLb, exchangeTime<e
    """


def q_join_classify_sample(d: str, ric: str, chunk: str, lb: str, i: int, nrows: int) -> str:
    return q_bounds_and_ns_vars(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];

    t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType
       from trades
       where date=d, RIC=ric, not null exchangeTime,
             exchangeTime>=s, exchangeTime<e;

    / If no trades in this slice, return empty result quickly
    if[0=count t; :0#update mid:0n, side:`symbol$() from t];

    q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
       from quotes
       where date=d, RIC=ric, not null exchangeTime,
             exchangeTime>=sLb, exchangeTime<e;

    / Sort for aj; captureTime breaks ties at same exchangeTime
    t: `RIC`exchangeTime xasc t;
    q: `RIC`exchangeTime`captureTime xasc update mid:(bid+ask)%2f from q;

    r: aj[`RIC`exchangeTime; t; q];

    {nrows}#select date,primaryRIC,RIC,exchangeTime,price,size,mid,
            side:$[ null mid; `unknown;
                   price>mid; `buy;
                   price<mid; `sell;
                   `mid ],
            MIC,cond,eutradetype,trade_xid,mmt_class,aucType
    from r
    """


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")
    ap.add_argument("--date", required=True, help="YYYY.MM.DD or YYYY-MM-DD")
    ap.add_argument("--ric", required=True, help="e.g. NVLH.PA")
    ap.add_argument("--chunk", default="0D00:10:00.000000000", help="q timespan literal")
    ap.add_argument("--lookback", default="0D00:05:00.000000000", help="q timespan literal")
    ap.add_argument("--max-slices", type=int, default=5, help="How many slices to process (-1 for all).")
    ap.add_argument("--show-trades", type=int, default=5, help="Print first N trades per slice (0 disables).")
    ap.add_argument("--show-quotes", type=int, default=5, help="Print first N quotes per slice (0 disables).")
    ap.add_argument("--show-result", type=int, default=5, help="Print first N joined rows per slice (0 disables).")
    ap.add_argument("--diag", action="store_true", help="Print type diagnostics for key columns.")
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric = q_symbol_literal(args.ric)
    chunk = args.chunk.strip()
    lb = args.lookback.strip()

    compass = Compass(host=args.host, port=args.port, region=args.region)

    if args.diag:
        print("Diagnostics (types):")
        print(run_query(compass, q_diag_types(d, ric)))
        print("-" * 80)

    ns = run_query(compass, q_n_slices(d, ric, chunk))
    n_slices = int(ns)

    if n_slices <= 0:
        print("No trades found for given (date,RIC).")
        return

    to_run = n_slices if args.max_slices == -1 else min(n_slices, args.max_slices)

    print(f"date={d} ric={ric} chunk={chunk} lookback={lb}")
    print(f"n_slices={n_slices}, processing={to_run}")
    print("-" * 80)

    for i in range(to_run):
        print(f"[slice {i}]")

        tc = run_query(compass, q_trades_count(d, ric, chunk, lb, i))
        tc_i = int(tc)
        print("  trades count:", tc_i)

        if args.show_trades > 0 and tc_i > 0:
            ts = run_query(compass, q_trades_sample(d, ric, chunk, lb, i, args.show_trades))
            print("  trades sample:")
            print(ts)

        qc = run_query(compass, q_quotes_count(d, ric, chunk, lb, i))
        qc_i = int(qc)
        print("  quotes count:", qc_i)

        if args.show_quotes > 0 and qc_i > 0:
            qs = run_query(compass, q_quotes_sample(d, ric, chunk, lb, i, args.show_quotes))
            print("  quotes sample:")
            print(qs)

        if args.show_result > 0:
            jr = run_query(compass, q_join_classify_sample(d, ric, chunk, lb, i, args.show_result))
            print(f"  result sample (top {args.show_result}):")
            print(jr)

        print("-" * 80)


if __name__ == "__main__":
    main()
