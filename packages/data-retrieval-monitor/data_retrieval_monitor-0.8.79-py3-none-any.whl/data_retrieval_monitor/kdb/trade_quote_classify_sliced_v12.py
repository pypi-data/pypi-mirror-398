#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v12.py

Robust and DEBUG-FIRST for your exact case:
- trades.exchangeTime type = timespan (q type `n)
- quotes.exchangeTime type = timespan (q type `n)

This version eliminates recurring q "type" errors by:
1) NEVER comparing symbols to strings: always normalize RIC to symbol via `$string RIC
2) Using a derived intraday timespan key `ex: 0D00:00:00.000000000 + exchangeTime`
   (safe for both timespan and time; for your case it stays timespan)
3) Normalizing chunk/lookback *in Python* into canonical q timespan literals (DHH:MM:SS.NNNNNNNNN)

Debug:
- Prints every q query before running it.
- Runs step-by-step per slice:
  A) DIAG_TYPES  (column types + sample)
  B) BOUNDS      (tmin/tmax, n slices)
  C) SLICE_VARS  (s/e/sLb + types)
  D) TRADES_SLICE_COUNT / SAMPLE
  E) QUOTES_SLICE_COUNT / SAMPLE
  F) JOIN_CLASSIFY_SAMPLE

No pandas.

Usage:
  python trade_quote_classify_sliced_v12.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --slice 0 --show-trades 5 --show-quotes 5 --show-result 20
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
    Accepts shorter fractional seconds; pads/truncates to 9.
    """
    m = _TS_RE.match(s)
    if not m:
        raise ValueError(f"Invalid timespan literal: {s!r}. Use like 0D00:05:00.000000000")
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


Q_DIAG_TYPES = r"""
d:__DATE__;
ric:__RIC__;
z0:0D00:00:00.000000000;

/ meta types
tRICt:first exec t from meta trades where c=`RIC;
qRICt:first exec t from meta quotes where c=`RIC;
tEXt:first exec t from meta trades where c=`exchangeTime;
qEXt:first exec t from meta quotes where c=`exchangeTime;

/ sample rows
t1: 1#select RIC,exchangeTime,captureTime,price from trades
    where date=d, `$string RIC = ric, not null exchangeTime;

q1: 1#select RIC,exchangeTime,captureTime,bid,ask from quotes
    where date=d, `$string RIC = ric, not null exchangeTime;

(`meta_t_RIC`meta_q_RIC`meta_t_ex`meta_q_ex
 `sample_t_RIC_type`sample_q_RIC_type`sample_t_ex_type`sample_q_ex_type
 `sample_t_ex_as_ex_type`sample_q_ex_as_ex_type
 `sample_t_ex`sample_q_ex)!(
  tRICt; qRICt; tEXt; qEXt;
  $[0=count t1; 0h; abs type first t1`RIC];
  $[0=count q1; 0h; abs type first q1`RIC];
  $[0=count t1; 0h; abs type first t1`exchangeTime];
  $[0=count q1; 0h; abs type first q1`exchangeTime];
  $[0=count t1; 0h; abs type (z0 + first t1`exchangeTime)];
  $[0=count q1; 0h; abs type (z0 + first q1`exchangeTime)];
  $[0=count t1; ::; first t1`exchangeTime];
  $[0=count q1; ::; first q1`exchangeTime]
)
"""

Q_BOUNDS = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

n: $[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk];

(`tmin`tmax`n`typeTmin`typeTmax`typeChunk)!(
  b`tmin; b`tmax; n;
  $[null b`tmin; 0h; abs type b`tmin];
  $[null b`tmax; 0h; abs type b`tmax];
  abs type chunk
)
"""

Q_SLICE_VARS = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :(`error`msg)!(`noTrades;"no trades for (date,RIC)")];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
sLb: s - lb;

(`s`sLb`e`n`typeS`typeSLb`typeE`typeLb)!(
  s; sLb; e; n;
  abs type s; abs type sLb; abs type e; abs type lb
)
"""

Q_TRADES_COUNT = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :0];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];

exec count i
from trades
where date=d, `$string RIC = ric, not null exchangeTime,
      (z0 + exchangeTime) >= s,
      (z0 + exchangeTime) <  e
"""

Q_TRADES_SAMPLE = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :([])];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];

__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,trade_xid,
          ex:(z0 + exchangeTime),
          RICsym:(`$string RIC)
from trades
where date=d, `$string RIC = ric, not null exchangeTime,
      (z0 + exchangeTime) >= s,
      (z0 + exchangeTime) <  e
"""

Q_QUOTES_COUNT = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :0];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
sLb: s - lb;

exec count i
from quotes
where date=d, `$string RIC = ric, not null exchangeTime,
      (z0 + exchangeTime) >= sLb,
      (z0 + exchangeTime) <  e
"""

Q_QUOTES_SAMPLE = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :([])];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
sLb: s - lb;

__N__#select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
          ex:(z0 + exchangeTime),
          RICsym:(`$string RIC)
from quotes
where date=d, `$string RIC = ric, not null exchangeTime,
      (z0 + exchangeTime) >= sLb,
      (z0 + exchangeTime) <  e
"""

Q_JOIN_CLASSIFY = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;
eps:0D00:00:00.000000001;
z0:0D00:00:00.000000000;

b: select tmin:min ex, tmax:max ex
   from update ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime;

tmin:b`tmin; tmax:b`tmax;
n:$[null tmin; 0; 1 + (tmax - tmin) div chunk];
if[n=0; :([])];

s: tmin + chunk * i;
e: $[i=n-1; tmax + eps; tmin + chunk * (i+1)];
sLb: s - lb;

/ trades slice: normalize RIC to symbol and compute ex join key
t: select date,primaryRIC,RIC:(`$string RIC),exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
          ex:(z0 + exchangeTime)
   from trades
   where date=d, `$string RIC = ric, not null exchangeTime,
         (z0 + exchangeTime) >= s,
         (z0 + exchangeTime) <  e;

if[0=count t; :([])];

/ quotes slice (+lookback): normalize RIC and compute ex join key
q: select RIC:(`$string RIC),exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
          ex:(z0 + exchangeTime)
   from quotes
   where date=d, `$string RIC = ric, not null exchangeTime,
         (z0 + exchangeTime) >= sLb,
         (z0 + exchangeTime) <  e;

/ sort for aj on (RIC,ex), tie-break by captureTime on quote side
t: `RIC`ex xasc t;
q: `RIC`ex`captureTime xasc update mid:(bid+ask)%2f from q;

r: aj[`RIC`ex; t; q];

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
    ap.add_argument("--slice", type=int, default=0)
    ap.add_argument("--show-trades", type=int, default=5)
    ap.add_argument("--show-quotes", type=int, default=5)
    ap.add_argument("--show-result", type=int, default=20)
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric = q_symbol_literal(args.ric)

    chunk = normalize_q_timespan_literal(args.chunk)
    lb = normalize_q_timespan_literal(args.lookback)

    compass = Compass(host=args.host, port=args.port, region=args.region)

    # A) types & samples
    run_q(compass, "DIAG_TYPES", render(Q_DIAG_TYPES, DATE=d, RIC=ric))

    # B) bounds
    run_q(compass, "BOUNDS", render(Q_BOUNDS, DATE=d, RIC=ric, CHUNK=chunk))

    i = args.slice

    # C) slice vars
    run_q(compass, f"SLICE_VARS i={i}", render(Q_SLICE_VARS, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))

    # D) trades slice
    run_q(compass, f"TRADES_COUNT i={i}", render(Q_TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
    if args.show_trades > 0:
        run_q(compass, f"TRADES_SAMPLE i={i}", render(Q_TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades))

    # E) quotes slice
    run_q(compass, f"QUOTES_COUNT i={i}", render(Q_QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
    if args.show_quotes > 0:
        run_q(compass, f"QUOTES_SAMPLE i={i}", render(Q_QUOTES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_quotes))

    # F) join/classify
    if args.show_result > 0:
        run_q(compass, f"JOIN_CLASSIFY_SAMPLE i={i}", render(Q_JOIN_CLASSIFY, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_result))


if __name__ == "__main__":
    main()
