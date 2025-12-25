#!/usr/bin/env python3
"""
asof_join_debug_compass.py

Simple as-of join between trades and quotes for one (date, RIC), compute mid and classify side.

DEBUG-FIRST:
- Runs small checkpoint queries separately and prints each query + its result.
- No lookback/window logic.
- Normalizes RIC on both tables: RICsym:(`$string RIC)
- Uses derived join key ex:(0D00:00:00 + exchangeTime) to avoid hidden time/timespan mismatches.

Usage:
  python asof_join_debug_compass.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA --sample 5 --join-sample 20 --trade-cap 0
"""

from __future__ import annotations

import argparse
from goldmansachs.compass_pykx import Compass


def q_date_literal(s: str) -> str:
    s = s.strip()
    return s.replace("-", ".") if "-" in s else s


def run_q(compass: Compass, name: str, q: str):
    print(f"\n[{name}] q:\n" + "-" * 120)
    print(q.strip())
    print("-" * 120)
    try:
        out = compass.run_query_sync(q)
    except Exception as e:
        print(f"[{name}] FAILED: {e}")
        raise
    print(f"[{name}] result:\n{out}\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")
    ap.add_argument("--date", required=True, help="YYYY.MM.DD or YYYY-MM-DD")
    ap.add_argument("--ric", required=True, help="e.g. NVLH.PA")
    ap.add_argument("--sample", type=int, default=5, help="rows to show in small samples")
    ap.add_argument("--join-sample", type=int, default=20, help="rows to show from joined output")
    ap.add_argument("--trade-cap", type=int, default=0,
                    help="if >0, cap trades used for join to first N after sorting (debug speed)")
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric_str = args.ric.strip().replace('"', '\\"')  # safe inside q string

    compass = Compass(host=args.host, port=args.port, region=args.region)

    # STEP 0: meta + sample types
    q0 = f"""
    d:{d};
    ric:`$"{ric_str}";

    tMeta: select c,t from meta trades where c in `RIC`exchangeTime`captureTime`price;
    qMeta: select c,t from meta quotes where c in `RIC`exchangeTime`captureTime`bid`ask;

    tSamp: 1#select RIC,exchangeTime,captureTime,price
           from trades
           where date=d, (`$string RIC)=ric, not null exchangeTime;

    qSamp: 1#select RIC,exchangeTime,captureTime,bid,ask
           from quotes
           where date=d, (`$string RIC)=ric, not null exchangeTime;

    types:(`tRIC`tEX`qRIC`qEX`texKey`qexKey)!(
      $[0=count tSamp;0h;abs type first tSamp`RIC];
      $[0=count tSamp;0h;abs type first tSamp`exchangeTime];
      $[0=count qSamp;0h;abs type first qSamp`RIC];
      $[0=count qSamp;0h;abs type first qSamp`exchangeTime];
      $[0=count tSamp;0h;abs type (0D00:00:00.000000000 + first tSamp`exchangeTime)];
      $[0=count qSamp;0h;abs type (0D00:00:00.000000000 + first qSamp`exchangeTime)]
    );

    (`tMeta`qMeta`tSamp`qSamp`types)!(tMeta;qMeta;tSamp;qSamp;types)
    """
    run_q(compass, "STEP0_META_AND_TYPES", q0)

    # STEP 1: tiny filtered samples
    n = args.sample
    q1 = f"""
    d:{d};
    ric:`$"{ric_str}";
    z0:0D00:00:00.000000000;

    tS: {n}#select date,primaryRIC,
                  RICsym:(`$string RIC),
                  exchangeTime,captureTime,price,size,trade_xid,
                  ex:(z0+exchangeTime)
         from trades
         where date=d, (`$string RIC)=ric, not null exchangeTime;

    qS: {n}#select date,primaryRIC,
                  RICsym:(`$string RIC),
                  exchangeTime,captureTime,bid,ask,seqNo,
                  ex:(z0+exchangeTime)
         from quotes
         where date=d, (`$string RIC)=ric, not null exchangeTime;

    (`tSample`qSample)!(tS;qS)
    """
    run_q(compass, "STEP1_TINY_SAMPLES", q1)

    # STEP 2: counts
    q2 = f"""
    d:{d};
    ric:`$"{ric_str}";

    tCount: exec count i from trades where date=d, (`$string RIC)=ric, not null exchangeTime;
    qCount: exec count i from quotes where date=d, (`$string RIC)=ric, not null exchangeTime;

    (`trades`quotes)!(tCount;qCount)
    """
    run_q(compass, "STEP2_COUNTS", q2)

    # STEP 3: join (return only counts + small heads)
    trade_cap = int(args.trade_cap)
    cap_stmt = "" if trade_cap <= 0 else f"t: {trade_cap}#t;"

    q3 = f"""
    d:{d};
    ric:`$"{ric_str}";
    z0:0D00:00:00.000000000;

    t: select date,primaryRIC,
              RIC:(`$string RIC),
              exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
              ex:(z0+exchangeTime)
       from trades
       where date=d, (`$string RIC)=ric, not null exchangeTime;

    q: select RIC:(`$string RIC),
              exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
              ex:(z0+exchangeTime)
       from quotes
       where date=d, (`$string RIC)=ric, not null exchangeTime;

    t: `RIC`ex xasc t;
    {cap_stmt}
    q: `RIC`ex`captureTime xasc update mid:(bid+ask)%2f from q;

    r: aj[`RIC`ex; t; q];

    r: update side:$[
              null mid; `unknown;
              price>mid; `buy;
              price<mid; `sell;
              `mid
         ] from r;

    (`tN`qN`rN`thead`qhead`rhead)!(
      count t; count q; count r;
      {n}#t;
      {n}#q;
      {args.join_sample}#select date,primaryRIC,RIC,exchangeTime,price,size,mid,side,trade_xid from r
    )
    """
    run_q(compass, "STEP3_JOIN_COUNTS_AND_HEADS", q3)


if __name__ == "__main__":
    main()
