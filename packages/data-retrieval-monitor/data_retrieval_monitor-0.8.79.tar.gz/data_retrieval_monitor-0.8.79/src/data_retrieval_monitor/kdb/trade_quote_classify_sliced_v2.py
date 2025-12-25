#!/usr/bin/env python3
"""
Sliced trade/quote debugging + asof join classification (server-side q), using Compass.

Design goals:
- NEVER use pandas.
- Trades and quotes are fetched in separate queries per slice (count + optional sample).
- Join + mid + buy/sell/mid classification is done in q per slice.
- Avoid passing timespans as Python objects (prevents type mismatches). Slice bounds are computed in q.

Usage example:
  python trade_quote_classify_sliced_v2.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --max-slices 5 --show-trades 5 --show-quotes 5 --show-result 5
"""

from __future__ import annotations

import argparse
from typing import Optional

from goldmansachs.compass_pykx import Compass


def q_date_literal(s: str) -> str:
    """Accept 'YYYY.MM.DD' or 'YYYY-MM-DD' and return q date literal 'YYYY.MM.DD'."""
    s = s.strip()
    if "-" in s:
        s = s.replace("-", ".")
    return s


def q_symbol_literal(s: str) -> str:
    """Return q symbol literal with leading backtick."""
    s = s.strip()
    return s if s.startswith("`") else f"`{s}"


def run_query(compass: Compass, q: str):
    """Run q via Compass; on failure print the query to aid debugging."""
    try:
        return compass.run_query_sync(q)
    except Exception as e:
        print("\nERROR while running q:\n" + "-" * 80)
        print(q)
        print("-" * 80)
        raise


def get_n_slices(compass: Compass, d: str, ric: str, chunk: str) -> int:
    q = f"""
    d:{d}; ric:{ric};
    chunk:{chunk};

    b: select tmin:min exchangeTime, tmax:max exchangeTime
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    n: $[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk];
    n
    """
    out = run_query(compass, q)
    # out is a scalar (PyKX atom), int(...) works
    return int(out)


def slice_vars_prefix(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    # Compute s,e (timespans) inside q to avoid type conversion issues.
    return f"""
    d:{d}; ric:{ric};
    chunk:{chunk};
    lb:{lb};
    eps:0D00:00:00.000000001;
    i:{i};

    b: select tmin:min exchangeTime, tmax:max exchangeTime
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    if[null b`tmin; :`noTrades];

    tmin:b`tmin; tmax:b`tmax;
    n: 1 + (tmax - tmin) div chunk;

    / bounds for slice i (half-open [s,e))
    s: tmin + chunk * i;
    e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
    """


def trades_count_query(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return slice_vars_prefix(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :0];
    exec count i from trades
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s, exchangeTime<e
    """


def trades_sample_query(d: str, ric: str, chunk: str, lb: str, i: int, n: int) -> str:
    return slice_vars_prefix(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];
    {n}#select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid
    from trades
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s, exchangeTime<e
    """


def quotes_count_query(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return slice_vars_prefix(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :0];
    exec count i from quotes
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s-lb, exchangeTime<e
    """


def quotes_sample_query(d: str, ric: str, chunk: str, lb: str, i: int, n: int) -> str:
    return slice_vars_prefix(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];
    {n}#select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
    from quotes
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s-lb, exchangeTime<e
    """


def join_classify_query(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return slice_vars_prefix(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :([])];

    t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType
       from trades
       where date=d, RIC=ric, not null exchangeTime,
             exchangeTime>=s, exchangeTime<e;

    q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
       from quotes
       where date=d, RIC=ric, not null exchangeTime,
             exchangeTime>=s-lb, exchangeTime<e;

    / required sort for aj; captureTime breaks ties at same exchangeTime
    t: `RIC`exchangeTime xasc t;
    q: `RIC`exchangeTime`captureTime xasc update mid:(bid+ask)%2f from q;

    r: aj[`RIC`exchangeTime; t; q];

    select date,primaryRIC,RIC,exchangeTime,price,size,mid,
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
    ap.add_argument("--show-result", type=int, default=5, help="Print first N result rows per slice (0 disables).")
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric = q_symbol_literal(args.ric)
    chunk = args.chunk.strip()
    lb = args.lookback.strip()

    compass = Compass(host=args.host, port=args.port, region=args.region)

    n_slices = get_n_slices(compass, d, ric, chunk)
    if n_slices <= 0:
        print("No trades found for given (date,RIC).")
        return

    to_run = n_slices if args.max_slices == -1 else min(n_slices, args.max_slices)
    print(f"date={d} ric={ric} chunk={chunk} lookback={lb}")
    print(f"n_slices={n_slices}, processing={to_run}")
    print("-" * 80)

    for i in range(to_run):
        print(f"[slice {i}]")

        tc = run_query(compass, trades_count_query(d, ric, chunk, lb, i))
        print("  trades count:", int(tc) if tc is not None else tc)

        if args.show_trades > 0 and int(tc) > 0:
            ts = run_query(compass, trades_sample_query(d, ric, chunk, lb, i, args.show_trades))
            print("  trades sample:")
            print(ts)

        qc = run_query(compass, quotes_count_query(d, ric, chunk, lb, i))
        print("  quotes count:", int(qc) if qc is not None else qc)

        if args.show_quotes > 0 and int(qc) > 0:
            qs = run_query(compass, quotes_sample_query(d, ric, chunk, lb, i, args.show_quotes))
            print("  quotes sample:")
            print(qs)

        jr = run_query(compass, join_classify_query(d, ric, chunk, lb, i))
        print("  joined rows:", len(jr))

        if args.show_result > 0 and len(jr) > 0:
            head = run_query(compass, f"{args.show_result}#({join_classify_query(d, ric, chunk, lb, i)})")
            print("  result sample:")
            print(head)

        print("-" * 80)


if __name__ == "__main__":
    main()
