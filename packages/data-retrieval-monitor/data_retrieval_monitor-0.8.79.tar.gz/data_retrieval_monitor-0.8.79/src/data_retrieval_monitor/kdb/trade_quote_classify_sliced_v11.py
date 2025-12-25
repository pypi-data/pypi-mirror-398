#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v11.py

KDB/Q-only (timespan) implementation that avoids nyi/type/long:
- CONFIRMED: trades.exchangeTime and quotes.exchangeTime are timespan-of-day (type `n).
- Therefore we DO NOT do any type conversions inside q.
- We validate/normalize --chunk and --lookback in Python into canonical q timespan literals.

Debug behavior:
- Prints each q query before execution and prints the result.
- Runs separate queries per slice:
  1) TYPES (from meta)
  2) PARAM_TYPES (types of chunk/lookback literals + tmin/tmax types)
  3) N_SLICES
  4) SLICE_DIAG (optional)
  5) TRADES_COUNT + TRADES_SAMPLE
  6) QUOTES_COUNT + QUOTES_SAMPLE
  7) JOIN_CLASSIFY (aj + mid + buy/sell/mid)

No pandas.
"""

from __future__ import annotations

import argparse
import re
from goldmansachs.compass_pykx import Compass

_TS_RE = re.compile(
    r"^\s*(?P<d>\d+)D(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})(?:\.(?P<ns>\d{1,9}))?\s*$"
)

def q_date_literal(s: str) -> str:
    s = s.strip()
    return s.replace("-", ".") if "-" in s else s

def q_symbol_literal(s: str) -> str:
    s = s.strip()
    return s if s.startswith("`") else f"`{s}"

def normalize_q_timespan_literal(s: str) -> str:
    """
    Normalize to q timespan literal: <D>D<HH>:<MM>:<SS>.<NNNNNNNNN>
    Raises ValueError if not parseable.
    """
    m = _TS_RE.match(s)
    if not m:
        raise ValueError(f"Invalid timespan literal: {s!r}. Expected like 0D00:05:00.000000000")
    d = int(m.group("d"))
    h = int(m.group("h"))
    mi = int(m.group("m"))
    sec = int(m.group("s"))
    ns = (m.group("ns") or "0")
    ns = (ns + "0" * 9)[:9]
    return f"{d}D{h:02d}:{mi:02d}:{sec:02d}.{ns}"

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

Q_TYPES = r"""
(`tTC`qTC)!(
  first exec t from meta trades where c=`exchangeTime;
  first exec t from meta quotes where c=`exchangeTime
)
"""

Q_PARAM_TYPES = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;

b: select tmin:min exchangeTime, tmax:max exchangeTime
   from trades
   where date=d, RIC=ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;

(`typeChunk`typeLb`typeTmin`typeTmax`chunk`lb`tmin`tmax)!(
  abs type chunk;
  abs type lb;
  abs type tmin;
  abs type tmax;
  chunk; lb; tmin; tmax
)
"""

Q_N_SLICES = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;

b: select tmin:min exchangeTime, tmax:max exchangeTime
   from trades
   where date=d, RIC=ric, not null exchangeTime;

$[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk]
"""

Q_SLICE_PREFIX = r"""
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

Q_SLICE_DIAG = Q_SLICE_PREFIX + r"""
(`s`sLb`e`n`typeS`typeSLb`typeE)!(
  s; sLb; e; n;
  abs type s; abs type sLb; abs type e
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

    chunk = normalize_q_timespan_literal(args.chunk)
    lb = normalize_q_timespan_literal(args.lookback)

    compass = Compass(host=args.host, port=args.port, region=args.region)

    types = run_q(compass, "TYPES", Q_TYPES)
    tTC = norm_typecode(types["tTC"][0])
    qTC = norm_typecode(types["qTC"][0])
    print(f"Detected exchangeTime types: trades={tTC!r} quotes={qTC!r}")

    if not (tTC == "n" and qTC == "n"):
        print("ERROR: v11 is for timespan exchangeTime (type 'n') on BOTH tables.")
        print("Your types:", tTC, qTC)
        return

    run_q(compass, "PARAM_TYPES", render(Q_PARAM_TYPES, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb))

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
            run_q(compass, f"SLICE_DIAG i={i}", render(Q_SLICE_DIAG, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))

        tc_atom = run_q(compass, f"TRADES_COUNT i={i}", render(Q_TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        tc = int(to_py_scalar(tc_atom))

        if args.show_trades > 0 and tc > 0:
            run_q(compass, f"TRADES_SAMPLE i={i}", render(Q_TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades))

        qc_atom = run_q(compass, f"QUOTES_COUNT i={i}", render(Q_QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        qc = int(to_py_scalar(qc_atom))

        if args.show_quotes > 0 and qc > 0:
            run_q(compass, f"QUOTES_SAMPLE i={i}", render(Q_QUOTES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_quotes))

        if args.show_result > 0 and tc > 0:
            run_q(compass, f"JOIN_CLASSIFY i={i}", render(Q_JOIN_CLASSIFY, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_result))

if __name__ == "__main__":
    main()
