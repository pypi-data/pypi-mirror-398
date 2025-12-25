#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v7.py

This version is intentionally SIMPLE and compatible:
- Assumes exchangeTime is intraday (timespan `n or time `t) for BOTH trades and quotes,
  which matches your example: 0D05:30:01.381...
- Does NOT use any timestamp casts, long casts, or string->time casts that can cause:
    QError: nyi / type / long
- Trades slice, quotes slice, and join/classify are run in SEPARATE queries per slice.
- Prints EVERY q query before running it + prints the result, so you can pinpoint errors.

If meta shows trades.exchangeTime and quotes.exchangeTime are not `n or `t, the script prints
the types and exits (so you can adjust safely).

USAGE:
  python trade_quote_classify_sliced_v7.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --slice 0 --show-trades 5 --show-quotes 5 --show-result 20 --diag

Run first 3 slices:
  python trade_quote_classify_sliced_v7.py ... --max-slices 3
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


def render(template: str, **kw) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace(f"__{k}__", str(v))
    return out


def run_q(compass: Compass, name: str, q: str):
    print(f"\n[{name}] q:\n" + "-" * 110)
    print(q.strip())
    print("-" * 110)
    try:
        out = compass.run_query_sync(q)
    except Exception as e:
        print(f"[{name}] FAILED: {e}")
        raise
    print(f"[{name}] result:\n{out}\n")
    return out


Q_META = r"""
(`metaTrades`metaQuotes)!(meta trades; meta quotes)
"""

Q_TYPES = r"""
(`tTC`qTC)!(
  string first exec t from meta trades where c=`exchangeTime;
  string first exec t from meta quotes where c=`exchangeTime
)
"""

Q_N_SLICES_N = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;

b: select tmin:min exchangeTime, tmax:max exchangeTime
   from trades
   where date=d, RIC=ric, not null exchangeTime;

$[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk]
"""

Q_N_SLICES_T = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
z0:0D00:00:00.000000000;

b: select tmin:min (z0+exchangeTime), tmax:max (z0+exchangeTime)
   from trades
   where date=d, RIC=ric, not null exchangeTime;

$[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk]
"""

Q_SLICE_PREFIX_N = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;

b: select tmin:min exchangeTime, tmax:max exchangeTime
   from trades
   where date=d, RIC=ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :`noTrades];
if[i<0 or i>=n; '("slice i out of range, i=",string i," n=",string n)];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
sLb: s - lb;
"""

Q_SLICE_PREFIX_T = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min (z0+exchangeTime), tmax:max (z0+exchangeTime)
   from trades
   where date=d, RIC=ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :`noTrades];
if[i<0 or i>=n; '("slice i out of range, i=",string i," n=",string n)];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
sLb: s - lb;
"""

Q_SLICE_DIAG_N = Q_SLICE_PREFIX_N + r"""
(`s`sLb`e`n)! (s; sLb; e; n)
"""

Q_SLICE_DIAG_T = Q_SLICE_PREFIX_T + r"""
(`s`sLb`e`n)! (s; sLb; e; n)
"""

Q_TRADES_COUNT_N = Q_SLICE_PREFIX_N + r"""
exec count i
from trades
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=s, exchangeTime<e
"""

Q_TRADES_COUNT_T = Q_SLICE_PREFIX_T + r"""
z0:0D00:00:00.000000000;
exec count i
from trades
where date=d, RIC=ric, not null exchangeTime,
      (z0+exchangeTime)>=s, (z0+exchangeTime)<e
"""

Q_TRADES_SAMPLE_N = Q_SLICE_PREFIX_N + r"""
__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid
from trades
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=s, exchangeTime<e
"""

Q_TRADES_SAMPLE_T = Q_SLICE_PREFIX_T + r"""
z0:0D00:00:00.000000000;
__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid,
          exN:(z0+exchangeTime)
from trades
where date=d, RIC=ric, not null exchangeTime,
      (z0+exchangeTime)>=s, (z0+exchangeTime)<e
"""

Q_QUOTES_COUNT_N = Q_SLICE_PREFIX_N + r"""
exec count i
from quotes
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=sLb, exchangeTime<e
"""

Q_QUOTES_COUNT_T = Q_SLICE_PREFIX_T + r"""
z0:0D00:00:00.000000000;
exec count i
from quotes
where date=d, RIC=ric, not null exchangeTime,
      (z0+exchangeTime)>=sLb, (z0+exchangeTime)<e
"""

Q_QUOTES_SAMPLE_N = Q_SLICE_PREFIX_N + r"""
__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
from quotes
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=sLb, exchangeTime<e
"""

Q_QUOTES_SAMPLE_T = Q_SLICE_PREFIX_T + r"""
z0:0D00:00:00.000000000;
__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
          exN:(z0+exchangeTime)
from quotes
where date=d, RIC=ric, not null exchangeTime,
      (z0+exchangeTime)>=sLb, (z0+exchangeTime)<e
"""

Q_JOIN_CLASSIFY_N = Q_SLICE_PREFIX_N + r"""
/ slice trades
t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType
   from trades
   where date=d, RIC=ric, not null exchangeTime,
         exchangeTime>=s, exchangeTime<e;

if[0=count t; :([])];

/ slice quotes (+lookback)
q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
   from quotes
   where date=d, RIC=ric, not null exchangeTime,
         exchangeTime>=sLb, exchangeTime<e;

/ sort for aj
t: `RIC`exchangeTime xasc t;
q: `RIC`exchangeTime`captureTime xasc update mid:(bid+ask)%2f from q;

/ asof join (quote.exchangeTime <= trade.exchangeTime, closest)
r: aj[`RIC`exchangeTime; t; q];

/ classify
__N__#select date,primaryRIC,RIC,exchangeTime,price,size,mid,
       side:$[ null mid; `unknown;
              price>mid; `buy;
              price<mid; `sell;
              `mid ],
       trade_xid
from r
"""

Q_JOIN_CLASSIFY_T = Q_SLICE_PREFIX_T + r"""
z0:0D00:00:00.000000000;

/ slice trades, with join key exN
t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
          exN:(z0+exchangeTime)
   from trades
   where date=d, RIC=ric, not null exchangeTime,
         (z0+exchangeTime)>=s, (z0+exchangeTime)<e;

if[0=count t; :([])];

/ slice quotes (+lookback), with join key exN
q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
          exN:(z0+exchangeTime)
   from quotes
   where date=d, RIC=ric, not null exchangeTime,
         (z0+exchangeTime)>=sLb, (z0+exchangeTime)<e;

/ sort for aj on exN
t: `RIC`exN xasc t;
q: `RIC`exN`captureTime xasc update mid:(bid+ask)%2f from q;

r: aj[`RIC`exN; t; q];

__N__#select date,primaryRIC,RIC,exchangeTime,price,size,mid,
       side:$[ null mid; `unknown;
              price>mid; `buy;
              price<mid; `sell;
              `mid ],
       trade_xid
from r
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")

    ap.add_argument("--date", required=True, help="YYYY.MM.DD or YYYY-MM-DD")
    ap.add_argument("--ric", required=True, help="e.g. NVLH.PA")

    ap.add_argument("--chunk", default="0D00:10:00.000000000")
    ap.add_argument("--lookback", default="0D00:05:00.000000000")

    ap.add_argument("--max-slices", type=int, default=3, help="-1 for all")
    ap.add_argument("--slice", type=int, default=None)

    ap.add_argument("--show-trades", type=int, default=5)
    ap.add_argument("--show-quotes", type=int, default=5)
    ap.add_argument("--show-result", type=int, default=10)

    ap.add_argument("--diag", action="store_true")
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric = q_symbol_literal(args.ric)
    chunk = args.chunk.strip()
    lb = args.lookback.strip()

    compass = Compass(host=args.host, port=args.port, region=args.region)

    if args.diag:
        run_q(compass, "META", Q_META)

    types = run_q(compass, "TYPES", Q_TYPES)
    tTC = str(types["tTC"][0])
    qTC = str(types["qTC"][0])

    print(f"Detected exchangeTime types: trades={tTC} quotes={qTC}")

    # Choose strategy
    if tTC == "n" and qTC == "n":
        N_SLICES = Q_N_SLICES_N
        SLICE_DIAG = Q_SLICE_DIAG_N
        TRADES_COUNT = Q_TRADES_COUNT_N
        TRADES_SAMPLE = Q_TRADES_SAMPLE_N
        QUOTES_COUNT = Q_QUOTES_COUNT_N
        QUOTES_SAMPLE = Q_QUOTES_SAMPLE_N
        JOIN_CLASSIFY = Q_JOIN_CLASSIFY_N
    elif tTC == "t" and qTC == "t":
        N_SLICES = Q_N_SLICES_T
        SLICE_DIAG = Q_SLICE_DIAG_T
        TRADES_COUNT = Q_TRADES_COUNT_T
        TRADES_SAMPLE = Q_TRADES_SAMPLE_T
        QUOTES_COUNT = Q_QUOTES_COUNT_T
        QUOTES_SAMPLE = Q_QUOTES_SAMPLE_T
        JOIN_CLASSIFY = Q_JOIN_CLASSIFY_T
    else:
        # We stop here to avoid more type errors and guessing.
        # You can extend with mixed-type handling once you confirm your types.
        print("ERROR: exchangeTime types are not both `n (timespan) or both `t (time).")
        print("Run with --diag and check META/TYPES output. Then we can add a safe cast branch.")
        return

    n_slices_atom = run_q(compass, "N_SLICES", render(N_SLICES, DATE=d, RIC=ric, CHUNK=chunk))
    n_slices = int(n_slices_atom)

    if n_slices <= 0:
        print("No trades found for (date,RIC).")
        return

    if args.slice is not None:
        indices = [args.slice]
    else:
        to_run = n_slices if args.max_slices == -1 else min(n_slices, args.max_slices)
        indices = list(range(to_run))

    print(f"\nProcessing slices {indices} (n_slices={n_slices})")

    for i in indices:
        if args.diag:
            run_q(compass, f"SLICE_DIAG i={i}", render(SLICE_DIAG, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))

        tc = run_q(compass, f"TRADES_COUNT i={i}", render(TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        tc_i = int(tc)

        if args.show_trades > 0 and tc_i > 0:
            run_q(
                compass,
                f"TRADES_SAMPLE i={i}",
                render(TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades),
            )

        qc = run_q(compass, f"QUOTES_COUNT i={i}", render(QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        qc_i = int(qc)

        if args.show_quotes > 0 and qc_i > 0:
            run_q(
                compass,
                f"QUOTES_SAMPLE i={i}",
                render(QUOTES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_quotes),
            )

        if args.show_result > 0 and tc_i > 0:
            run_q(
                compass,
                f"JOIN_CLASSIFY i={i}",
                render(JOIN_CLASSIFY, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_result),
            )


if __name__ == "__main__":
    main()
