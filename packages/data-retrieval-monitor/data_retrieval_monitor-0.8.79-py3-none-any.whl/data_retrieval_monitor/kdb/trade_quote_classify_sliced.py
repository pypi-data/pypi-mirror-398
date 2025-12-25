#!/usr/bin/env python3
"""
Sliced (chunked) trade/quote asof join + mid + buy/sell/mid classification using Compass (PyKX remote q).

Key properties:
- Trades and quotes are pulled in SEPARATE queries per slice (for debugging).
- Classification is done server-side in q (no pandas).
- Output per slice is trade-sized (left asof join).
"""

from __future__ import annotations

import argparse
from typing import List, Tuple

from goldmansachs.compass_pykx import Compass


def _q_date(s: str) -> str:
    """Accept 'YYYY.MM.DD' or 'YYYY-MM-DD' and return q date literal 'YYYY.MM.DD'."""
    s = s.strip()
    if "-" in s:
        s = s.replace("-", ".")
    return s


def _q_symbol(s: str) -> str:
    """Return q symbol literal with leading backtick."""
    s = s.strip()
    if s.startswith("`"):
        return s
    return f"`{s}"


def run_query(compass: Compass, q: str):
    """Run a q string via Compass."""
    return compass.run_query_sync(q)


def build_windows(compass: Compass, d: str, ric_q: str, chunk_q: str) -> List[Tuple[int, str, str]]:
    """
    Return list of (i, sStr, eStr) windows covering all trades for (date, RIC),
    using half-open intervals [s,e) and a +1ns eps on the final end.
    """
    q = f"""
    d:{d}; ric:{ric_q};
    chunk:{chunk_q};
    eps:0D00:00:00.000000001;

    b: select tmin:min exchangeTime, tmax:max exchangeTime
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    if[null b`tmin; :([] i:(); sStr:(); eStr:())];

    tmin:b`tmin; tmax:b`tmax;

    n: 1 + (tmax - tmin) div chunk;
    sL: tmin + chunk * til n;
    eL: (1 _ sL), enlist (tmax + eps);

    ([] i:til n; sStr:string sL; eStr:string eL)
    """
    w = run_query(compass, q)
    if len(w) == 0:
        return []
    # Convert to plain Python list of tuples for easy looping
    # (PyKX table supports column access; values are PyKX atoms)
    out = []
    for idx in range(len(w)):
        i = int(w["i"][idx])
        sStr = str(w["sStr"][idx])
        eStr = str(w["eStr"][idx])
        out.append((i, sStr, eStr))
    return out


def trades_count_q(d: str, ric_q: str, sStr: str, eStr: str) -> str:
    return f"""
    d:{d}; ric:{ric_q}; s:{sStr}; e:{eStr};
    select n:count i
    from trades
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s, exchangeTime<e
    """


def trades_sample_q(d: str, ric_q: str, sStr: str, eStr: str, n: int) -> str:
    # Keep a compact sample for debugging
    return f"""
    d:{d}; ric:{ric_q}; s:{sStr}; e:{eStr};
    {n}#select date,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid
    from trades
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s, exchangeTime<e
    """


def quotes_count_q(d: str, ric_q: str, sStr: str, eStr: str, lb_q: str) -> str:
    return f"""
    d:{d}; ric:{ric_q}; s:{sStr}; e:{eStr}; lb:{lb_q};
    select n:count i
    from quotes
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s-lb, exchangeTime<e
    """


def quotes_sample_q(d: str, ric_q: str, sStr: str, eStr: str, lb_q: str, n: int) -> str:
    return f"""
    d:{d}; ric:{ric_q}; s:{sStr}; e:{eStr}; lb:{lb_q};
    {n}#select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
    from quotes
    where date=d, RIC=ric, not null exchangeTime,
          exchangeTime>=s-lb, exchangeTime<e
    """


def join_classify_q(d: str, ric_q: str, sStr: str, eStr: str, lb_q: str) -> str:
    """
    As-of join: last quote at or before each trade exchangeTime (closest earlier).
    Tie-breaker: captureTime, since q is sorted by exchangeTime,captureTime.
    Output: trade rows with mid + side classification.
    """
    return f"""
    d:{d}; ric:{ric_q}; s:{sStr}; e:{eStr}; lb:{lb_q};

    / trades in [s,e)
    t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType
       from trades
       where date=d, RIC=ric, not null exchangeTime,
             exchangeTime>=s, exchangeTime<e;

    / quotes in [s-lb,e)
    q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
       from quotes
       where date=d, RIC=ric, not null exchangeTime,
             exchangeTime>=s-lb, exchangeTime<e;

    / required sort for aj; captureTime breaks ties at same exchangeTime
    t: `RIC`exchangeTime xasc t;
    q: `RIC`exchangeTime`captureTime xasc update mid:(bid+ask)%2f from q;

    r: aj[`RIC`exchangeTime; t; q];

    / classify; return ONLY trade rows
    select date,primaryRIC,RIC,exchangeTime,price,size,mid,
           side:$[ null mid; `unknown;
                  price>mid; `buy;
                  price<mid; `sell;
                  `mid ],
           MIC,cond,eutradetype,trade_xid,mmt_class,aucType
    from r
    """


def main() -> None:
    ap = argparse.ArgumentParser(description="Sliced trade/quote asof join + buy/sell/mid classification (Compass/PyKX).")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")
    ap.add_argument("--date", required=True, help="q date, e.g. 2025.10.22 or 2025-10-22")
    ap.add_argument("--ric", required=True, help="RIC, e.g. NVLH.PA")
    ap.add_argument("--chunk", default="0D00:10:00.000000000", help="q timespan, e.g. 0D00:10:00.000000000")
    ap.add_argument("--lookback", default="0D00:05:00.000000000", help="q timespan, e.g. 0D00:05:00.000000000")
    ap.add_argument("--max-slices", type=int, default=5, help="How many slices to process (debug). Use -1 for all.")
    ap.add_argument("--show-trades", type=int, default=5, help="Print first N trades per slice (0 disables).")
    ap.add_argument("--show-quotes", type=int, default=5, help="Print first N quotes per slice (0 disables).")
    ap.add_argument("--show-result", type=int, default=5, help="Print first N joined rows per slice (0 disables).")
    args = ap.parse_args()

    d = _q_date(args.date)
    ric_q = _q_symbol(args.ric)
    chunk_q = args.chunk
    lb_q = args.lookback

    compass = Compass(host=args.host, port=args.port, region=args.region)

    windows = build_windows(compass, d, ric_q, chunk_q)
    if not windows:
        print("No trades found for given (date,RIC). Nothing to do.")
        return

    if args.max_slices == -1:
        work = windows
    else:
        work = windows[: args.max_slices]

    print(f"Found {len(windows)} slice(s); processing {len(work)} slice(s).")
    print(f"date={d} ric={ric_q} chunk={chunk_q} lookback={lb_q}")
    print("-" * 80)

    for i, sStr, eStr in work:
        print(f"[slice {i}] s={sStr} e={eStr}")

        # --- trades slice: count then sample ---
        tc = run_query(compass, trades_count_q(d, ric_q, sStr, eStr))
        print("  trades count:", tc)

        if args.show_trades > 0:
            ts = run_query(compass, trades_sample_q(d, ric_q, sStr, eStr, args.show_trades))
            print("  trades sample:")
            print(ts)

        # --- quotes slice: count then sample ---
        qc = run_query(compass, quotes_count_q(d, ric_q, sStr, eStr, lb_q))
        print("  quotes count:", qc)

        if args.show_quotes > 0:
            qs = run_query(compass, quotes_sample_q(d, ric_q, sStr, eStr, lb_q, args.show_quotes))
            print("  quotes sample:")
            print(qs)

        # --- join + classify (trade-sized output) ---
        jr = run_query(compass, join_classify_q(d, ric_q, sStr, eStr, lb_q))
        print("  joined rows:", len(jr))

        if args.show_result > 0 and len(jr) > 0:
            # request a small head on the server to avoid large transfer
            head = run_query(compass, f"{args.show_result}#({join_classify_q(d, ric_q, sStr, eStr, lb_q)})")
            print("  result sample:")
            print(head)

        print("-" * 80)


if __name__ == "__main__":
    main()
