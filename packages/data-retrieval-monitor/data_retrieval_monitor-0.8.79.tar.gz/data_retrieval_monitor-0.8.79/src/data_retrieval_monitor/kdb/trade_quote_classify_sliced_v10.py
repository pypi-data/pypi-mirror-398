#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v10.py

Purpose: eliminate recurring q 'type' errors for timespan exchangeTime (type 'n') by:
- Normalizing chunk and lookback to TIMESPAN even if user passes time-of-day (type 't')
- Keeping everything in timespan space (no timestamps, no long casts, no string casts)

Given your confirmed types:
  trades.exchangeTime type = 'n'
  quotes.exchangeTime type = 'n'

This script:
- prints each q query before running it
- runs separate queries per slice:
  1) PARAM_DIAG
  2) N_SLICES
  3) SLICE_DIAG (optional)
  4) TRADES_COUNT + TRADES_SAMPLE
  5) QUOTES_COUNT + QUOTES_SAMPLE
  6) JOIN_CLASSIFY (aj + mid + buy/sell/mid)

No pandas.
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


def to_py_scalar(x):
    return x.py() if hasattr(x, "py") else x


def norm_typecode(v) -> str:
    v = to_py_scalar(v)
    if isinstance(v, (bytes, bytearray)):
        v = v.decode("utf-8", errors="ignore")
    v = str(v)
    return v[0] if v else v


Q_META = r"""
(`metaTrades`metaQuotes)!(meta trades; meta quotes)
"""

Q_TYPES = r"""
(`tTC`qTC)!(
  first exec t from meta trades where c=`exchangeTime;
  first exec t from meta quotes where c=`exchangeTime
)
"""

# normalize chunk/lb to timespan:
# - if chunk0/lb0 are time-of-day (type 19h), add to timespan zero to coerce
# - else keep as-is
Q_PARAM_DIAG = r"""
d:__DATE__; ric:__RIC__;
chunk0:__CHUNK__;
lb0:__LOOKBACK__;
z0:0D00:00:00.000000000;

chunk: $[abs type chunk0=19h; z0+chunk0; chunk0];
lb:    $[abs type lb0=19h;    z0+lb0;    lb0];

(`chunk0`lb0`chunk`lb`typeChunk0`typeLb0`typeChunk`typeLb`exTypeTrades`exTypeQuotes)!(
  chunk0; lb0; chunk; lb;
  abs type chunk0; abs type lb0; abs type chunk; abs type lb;
  abs type first exec exchangeTime from trades where date=d, RIC=ric, not null exchangeTime;
  abs type first exec exchangeTime from quotes where date=d, RIC=ric, not null exchangeTime
)
"""

Q_N_SLICES = r"""
d:__DATE__;
ric:__RIC__;
chunk0:__CHUNK__;
z0:0D00:00:00.000000000;
chunk: $[abs type chunk0=19h; z0+chunk0; chunk0];

b: select tmin:min exchangeTime, tmax:max exchangeTime
   from trades
   where date=d, RIC=ric, not null exchangeTime;

$[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk]
"""

Q_SLICE_PREFIX = r"""
d:__DATE__;
ric:__RIC__;
chunk0:__CHUNK__;
lb0:__LOOKBACK__;
z0:0D00:00:00.000000000;
chunk: $[abs type chunk0=19h; z0+chunk0; chunk0];
lb:    $[abs type lb0=19h;    z0+lb0;    lb0];

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

Q_SLICE_DIAG = Q_SLICE_PREFIX + r"""
(`s`sLb`e`n`typeS`typeSLb`typeE`typeChunk`typeLb)!(
  s; sLb; e; n;
  abs type s; abs type sLb; abs type e;
  abs type chunk; abs type lb
)
"""

Q_TRADES_COUNT = Q_SLICE_PREFIX + r"""
exec count i
from trades
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=s, exchangeTime<e
"""

Q_TRADES_SAMPLE = Q_SLICE_PREFIX + r"""
__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid
from trades
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=s, exchangeTime<e
"""

Q_QUOTES_COUNT = Q_SLICE_PREFIX + r"""
exec count i
from quotes
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=sLb, exchangeTime<e
"""

Q_QUOTES_SAMPLE = Q_SLICE_PREFIX + r"""
__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo
from quotes
where date=d, RIC=ric, not null exchangeTime,
      exchangeTime>=sLb, exchangeTime<e
"""

Q_JOIN_CLASSIFY = Q_SLICE_PREFIX + r"""
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

/ join_asof
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", required=True, type=int)
    ap.add_argument("--region", default="ldn")

    ap.add_argument("--date", required=True)
    ap.add_argument("--ric", required=True)

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

    # types check (still useful)
    types = run_q(compass, "TYPES", Q_TYPES)
    tTC = norm_typecode(types["tTC"][0])
    qTC = norm_typecode(types["qTC"][0])
    print(f"Detected exchangeTime types: trades={tTC!r} quotes={qTC!r}")

    # parameter diag (this is where type errors usually come from)
    run_q(compass, "PARAM_DIAG", render(Q_PARAM_DIAG, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb))

    if not (tTC == "n" and qTC == "n"):
        print("ERROR: v10 expects timespan exchangeTime ('n') on both tables. You have:", tTC, qTC)
        return

    n_slices_atom = run_q(compass, "N_SLICES", render(Q_N_SLICES, DATE=d, RIC=ric, CHUNK=chunk))
    n_slices = int(to_py_scalar(n_slices_atom))
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
            run_q(compass, f"SLICE_DIAG i={i}",
                  render(Q_SLICE_DIAG, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))

        tc_atom = run_q(compass, f"TRADES_COUNT i={i}",
                        render(Q_TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        tc = int(to_py_scalar(tc_atom))

        if args.show_trades > 0 and tc > 0:
            run_q(compass, f"TRADES_SAMPLE i={i}",
                  render(Q_TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades))

        qc_atom = run_q(compass, f"QUOTES_COUNT i={i}",
                        render(Q_QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        qc = int(to_py_scalar(qc_atom))

        if args.show_quotes > 0 and qc > 0:
            run_q(compass, f"QUOTES_SAMPLE i={i}",
                  render(Q_QUOTES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_quotes))

        if args.show_result > 0 and tc > 0:
            run_q(compass, f"JOIN_CLASSIFY i={i}",
                  render(Q_JOIN_CLASSIFY, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_result))


if __name__ == "__main__":
    main()
