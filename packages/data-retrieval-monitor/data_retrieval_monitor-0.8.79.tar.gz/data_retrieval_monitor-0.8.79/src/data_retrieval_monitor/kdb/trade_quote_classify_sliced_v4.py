#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v4.py

This version fixes the recurring q "type" error by NORMALIZING exchangeTime to a TIMESTAMP key (ts)
for BOTH trades and quotes, then doing slicing, filtering, sorting, and aj on that timestamp key.

It also runs in DEBUG MODE:
- prints every q query BEFORE executing it,
- trades and quotes are queried in SEPARATE calls per slice (count + optional sample),
- join/classification is a separate call per slice,
- no pandas is used.

Why this should eliminate 'type':
- All time comparisons are done on timestamp ts (type p),
  regardless of whether exchangeTime is stored as timespan (n), timestamp (p), or time (t).
- We only compare like-with-like (timestamp with timestamp, timespan with timespan, etc.).

USAGE:
  python trade_quote_classify_sliced_v4.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --max-slices 5 --show-trades 5 --show-quotes 5 --show-result 5 --diag
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


def run_q(compass: Compass, name: str, q: str):
    print(f"\n[{name}] q:\n" + "-" * 80)
    print(q.strip())
    print("-" * 80)
    out = compass.run_query_sync(q)
    print(f"[{name}] result:\n{out}\n")
    return out


def q_meta() -> str:
    # meta is fast; returns schema + types
    return "(`metaTrades`metaQuotes)!(meta trades; meta quotes)"


def q_type_diag(d: str, ric: str) -> str:
    return f"""
    d:{d}; ric:{ric};

    / Grab one row from each table to inspect types (first non-null exchangeTime)
    t1: 1#select date,RIC,exchangeTime,captureTime,price
        from trades
        where date=d, RIC=ric, not null exchangeTime;

    q1: 1#select date,RIC,exchangeTime,captureTime,bid,ask
        from quotes
        where date=d, RIC=ric, not null exchangeTime;

    / Type codes (abs to ignore atom vs list sign)
    tET: $[0=count t1; 0h; abs type first t1`exchangeTime];
    qET: $[0=count q1; 0h; abs type first q1`exchangeTime];

    (`tET`qET`tExSample`qExSample`tCapType`qCapType`tPriceType`qBidType`qAskType)!(
      tET;
      qET;
      $[0=count t1; ::; first t1`exchangeTime];
      $[0=count q1; ::; first q1`exchangeTime];
      $[0=count t1; ::; abs type first t1`captureTime];
      $[0=count q1; ::; abs type first q1`captureTime];
      $[0=count t1; ::; abs type first t1`price];
      $[0=count q1; ::; abs type first q1`bid];
      $[0=count q1; ::; abs type first q1`ask]
    )
    """


def q_n_slices(d: str, ric: str, chunk: str) -> str:
    """
    Compute #slices using normalized trade timestamp ts.
    """
    return f"""
    d:{d}; ric:{ric}; chunk:{chunk};

    / detect trade exchangeTime type
    tET: abs type first exec exchangeTime from trades where date=d, RIC=ric, not null exchangeTime;

    / normalize to timestamp
    mkTS:{[d;et;t]
      $[t=12h; et;                    / timestamp
        t=16h; d + et;                / timespan -> timestamp
        t=19h; timestamp$ (d + et);   / time -> datetime -> timestamp
        t=15h; timestamp$ et;         / datetime -> timestamp
        0Np]
    };

    b: select tmin:min ts, tmax:max ts
       from update ts: mkTS[d;exchangeTime;tET]
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    $[null b`tmin; 0; 1 + (long$b`tmax - long$b`tmin) div long$chunk]
    """


def q_slice_prefix(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    """
    Builds:
      tET,qET, mkTS
      b(tmin,tmax), n
      sTS,eTS,sLbTS (timestamps)
    """
    return f"""
    d:{d};
    ric:{ric};
    chunk:{chunk};
    lb:{lb};
    i:{i};

    / detect exchangeTime types (abs type code)
    tET: abs type first exec exchangeTime from trades where date=d, RIC=ric, not null exchangeTime;
    qET: abs type first exec exchangeTime from quotes where date=d, RIC=ric, not null exchangeTime;

    / normalize to timestamp
    mkTS:{[d;et;t]
      $[t=12h; et;                    / timestamp
        t=16h; d + et;                / timespan -> timestamp
        t=19h; timestamp$ (d + et);   / time -> datetime -> timestamp
        t=15h; timestamp$ et;         / datetime -> timestamp
        0Np]
    };

    b: select tmin:min ts, tmax:max ts
       from update ts: mkTS[d;exchangeTime;tET]
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    if[null b`tmin; :`noTrades];

    tminN: long$b`tmin;
    tmaxN: long$b`tmax;
    chunkN: long$chunk;
    lbN: long$lb;

    n: 1 + (tmaxN - tminN) div chunkN;

    sN: tminN + chunkN * i;
    eN: $[i=n-1; tmaxN + 1; tminN + chunkN * (i+1)];

    sTS: "p"$sN;
    eTS: "p"$eN;
    sLbTS:"p"$(sN - lbN);
    """


def q_trades_count(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return q_slice_prefix(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :0];
    / count trades in this slice using normalized ts
    exec count i
    from trades
    where date=d, RIC=ric, not null exchangeTime,
          mkTS[d;exchangeTime;tET] >= sTS,
          mkTS[d;exchangeTime;tET] <  eTS
    """


def q_trades_sample(d: str, ric: str, chunk: str, lb: str, i: int, nrows: int) -> str:
    return q_slice_prefix(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];
    t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid,
              ts: mkTS[d;exchangeTime;tET]
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    {nrows}#t where ts>=sTS, ts<eTS
    """


def q_quotes_count(d: str, ric: str, chunk: str, lb: str, i: int) -> str:
    return q_slice_prefix(d, ric, chunk, lb, i) + """
    if[`noTrades~::; :0];

    qCount:0;

    / Filter in the NATIVE exchangeTime type for quotes (to avoid type errors and reduce scan):
    if[qET=12h;
      qCount: exec count i
              from quotes
              where date=d, RIC=ric, not null exchangeTime,
                    exchangeTime>=sLbTS, exchangeTime<eTS;
    ];

    if[qET=16h;
      sSp: sLbTS - d; eSp: eTS - d;   / convert bounds to timespan-of-day
      qCount: exec count i
              from quotes
              where date=d, RIC=ric, not null exchangeTime,
                    exchangeTime>=sSp, exchangeTime<eSp;
    ];

    if[qET=19h;
      sTm: time$ sLbTS; eTm: time$ eTS;
      qCount: exec count i
              from quotes
              where date=d, RIC=ric, not null exchangeTime,
                    exchangeTime>=sTm, exchangeTime<eTm;
    ];

    if[qET=15h;
      qCount: exec count i
              from quotes
              where date=d, RIC=ric, not null exchangeTime,
                    timestamp$ exchangeTime>=sLbTS, timestamp$ exchangeTime<eTS;
    ];

    qCount
    """


def q_quotes_sample(d: str, ric: str, chunk: str, lb: str, i: int, nrows: int) -> str:
    return q_slice_prefix(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :([])];

    q: ();
    / select window using native exchangeTime type, then attach normalized ts for later join
    if[qET=12h;
      q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: exchangeTime
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               exchangeTime>=sLbTS, exchangeTime<eTS;
    ];

    if[qET=16h;
      sSp: sLbTS - d; eSp: eTS - d;
      q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: d + exchangeTime
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               exchangeTime>=sSp, exchangeTime<eSp;
    ];

    if[qET=19h;
      sTm: time$ sLbTS; eTm: time$ eTS;
      q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: timestamp$ (d + exchangeTime)
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               exchangeTime>=sTm, exchangeTime<eTm;
    ];

    if[qET=15h;
      q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: timestamp$ exchangeTime
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               ts>=sLbTS, ts<eTS;
    ];

    {nrows}#`ts xasc q
    """


def q_join_classify_sample(d: str, ric: str, chunk: str, lb: str, i: int, nrows: int) -> str:
    """
    Returns a dictionary with:
      diag: types + bounds + counts
      res : top N joined rows with mid + side
    """
    return q_slice_prefix(d, ric, chunk, lb, i) + f"""
    if[`noTrades~::; :(`diag`res)!((`error`msg)!(`noTrades;"no trades for (date,RIC)");([]))];

    / --- trades subset with normalized ts ---
    t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
              ts: mkTS[d;exchangeTime;tET]
       from trades
       where date=d, RIC=ric, not null exchangeTime;

    t: t where ts>=sTS, ts<eTS;

    / --- quotes subset using native exchangeTime type + normalized ts ---
    q: ();

    if[qET=12h;
      q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: exchangeTime
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               exchangeTime>=sLbTS, exchangeTime<eTS;
    ];

    if[qET=16h;
      sSp: sLbTS - d; eSp: eTS - d;
      q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: d + exchangeTime
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               exchangeTime>=sSp, exchangeTime<eSp;
    ];

    if[qET=19h;
      sTm: time$ sLbTS; eTm: time$ eTS;
      q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: timestamp$ (d + exchangeTime)
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               exchangeTime>=sTm, exchangeTime<eTm;
    ];

    if[qET=15h;
      q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
                ts: timestamp$ exchangeTime
         from quotes
         where date=d, RIC=ric, not null exchangeTime,
               ts>=sLbTS, ts<eTS;
    ];

    / --- sort for aj; captureTime breaks ties at same ts ---
    t: `RIC`ts xasc t;
    q: `RIC`ts`captureTime xasc update mid:(bid+ask)%2f from q;

    / --- asof join (quote.ts <= trade.ts, closest) ---
    r: aj[`RIC`ts; t; q];

    res: {nrows}#select date,primaryRIC,RIC,exchangeTime,price,size,
                     mid,
                     side:$[ null mid; `unknown;
                            price>mid; `buy;
                            price<mid; `sell;
                            `mid ],
                     trade_xid
          from r;

    diag:(`tET`qET`sTS`eTS`sLbTS`tCount`qCount)!(
      tET; qET; sTS; eTS; sLbTS; count t; count q
    );

    (`diag`res)!(diag; res)
    """


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")
    ap.add_argument("--date", required=True)
    ap.add_argument("--ric", required=True)
    ap.add_argument("--chunk", default="0D00:10:00.000000000")
    ap.add_argument("--lookback", default="0D00:05:00.000000000")
    ap.add_argument("--max-slices", type=int, default=5, help="-1 for all slices")
    ap.add_argument("--show-trades", type=int, default=5)
    ap.add_argument("--show-quotes", type=int, default=5)
    ap.add_argument("--show-result", type=int, default=5)
    ap.add_argument("--diag", action="store_true")
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric = q_symbol_literal(args.ric)
    chunk = args.chunk.strip()
    lb = args.lookback.strip()

    compass = Compass(host=args.host, port=args.port, region=args.region)

    if args.diag:
        run_q(compass, "META", q_meta())
        run_q(compass, "TYPE_DIAG", q_type_diag(d, ric))

    ns = run_q(compass, "N_SLICES", q_n_slices(d, ric, chunk))
    n_slices = int(ns)

    if n_slices <= 0:
        print("No trades found for (date,RIC).")
        return

    to_run = n_slices if args.max_slices == -1 else min(n_slices, args.max_slices)
    print(f"\nWill process {to_run}/{n_slices} slice(s).")

    for i in range(to_run):
        # Trades count
        tc = run_q(compass, f"TRADES_COUNT slice={i}", q_trades_count(d, ric, chunk, lb, i))
        tc_i = int(tc)

        if args.show_trades > 0 and tc_i > 0:
            run_q(compass, f"TRADES_SAMPLE slice={i}", q_trades_sample(d, ric, chunk, lb, i, args.show_trades))

        # Quotes count
        qc = run_q(compass, f"QUOTES_COUNT slice={i}", q_quotes_count(d, ric, chunk, lb, i))
        qc_i = int(qc)

        if args.show_quotes > 0 and qc_i > 0:
            run_q(compass, f"QUOTES_SAMPLE slice={i}", q_quotes_sample(d, ric, chunk, lb, i, args.show_quotes))

        # Join + classify sample
        if args.show_result > 0:
            run_q(compass, f"JOIN_CLASSIFY slice={i}", q_join_classify_sample(d, ric, chunk, lb, i, args.show_result))


if __name__ == "__main__":
    main()
