#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v8.py

Fixes v7 bug: meta type codes were returned as a 1-char STRING (,",\"n\"") because we used `string ...`.
Now we fetch the meta type code as a CHAR ATOM directly (e.g. "n"), and convert via .py().

Assumptions (matches your data example):
- trades.exchangeTime and quotes.exchangeTime are both timespan-of-day (type "n") OR both time-of-day (type "t").
- We slice, filter, and aj directly on exchangeTime (or a derived exN for time type).

Debug-friendly:
- Prints every q query before execution and prints the result.
- Trades slice and quotes slice are separate queries per slice.
- Join/classify is separate query.

Example:
  python trade_quote_classify_sliced_v8.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --slice 0 --show-trades 5 --show-quotes 5 --show-result 20 --diag
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


def atom_py(x):
    """Convert a PyKX atom / scalar to a Python scalar safely."""
    return x.py() if hasattr(x, "py") else x


Q_META = r"""
(`metaTrades`metaQuotes)!(meta trades; meta quotes)
"""

# IMPORTANT: do NOT wrap in `string` (that turns a char atom into a 1-char string list: ,"n")
Q_TYPES = r"""
(`tTC`qTC)!(
  first exec t from meta trades where c=`exchangeTime;
  first exec t from meta quotes where c=`exchangeTime
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
t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType
   from trades
   where date=d, RIC=ric, not null exchangeTime,
         exchangeTime>=s, exchangeTime<e;

if[0=count t; :([])];

q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
   from quotes
   where date=d, RIC=ric, not null exchangeTime,
         exchangeTime>=sLb, exchangeTime<e;

t: `RIC`exchangeTime xasc t;
q: `RIC`exchangeTime`captureTime xasc update mid:(bid+ask)%2f from q;

r: aj[`RIC`exchangeTime; t; q];

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

t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
          exN:(z0+exchangeTime)
   from trades
   where date=d, RIC=ric, not null exchangeTime,
         (z0+exchangeTime)>=s, (z0+exchangeTime)<e;

if[0=count t; :([])];

q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
          exN:(z0+exchangeTime)
   from quotes
   where date=d, RIC=ric, not null exchangeTime,
         (z0+exchangeTime)>=sLb, (z0+exchangeTime)<e;

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
    # types is a dict-like table with two entries
    tTC = atom_py(types["tTC"][0])
    qTC = atom_py(types["qTC"][0])

    # ensure Python strings like 'n'
    tTC = str(tTC)
    qTC = str(qTC)

    print(f"Detected exchangeTime types: trades={tTC!r} quotes={qTC!r}")

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
        print("ERROR: This script expects both exchangeTime types to match (both 'n' or both 't').")
        print("Your types:", tTC, qTC)
        return

    n_slices_atom = run_q(compass, "N_SLICES", render(N_SLICES, DATE=d, RIC=ric, CHUNK=chunk))
    n_slices = int(atom_py(n_slices_atom))

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

        tc_atom = run_q(compass, f"TRADES_COUNT i={i}", render(TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        tc_i = int(atom_py(tc_atom))

        if args.show_trades > 0 and tc_i > 0:
            run_q(
                compass,
                f"TRADES_SAMPLE i={i}",
                render(TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades),
            )

        qc_atom = run_q(compass, f"QUOTES_COUNT i={i}", render(QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        qc_i = int(atom_py(qc_atom))

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
