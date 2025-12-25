#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v6.py

This version is designed to stop the recurring q errors:
- QError: type
- QError: nyi
- QError: long

Main fixes vs prior versions:
1) Uses meta `t` values as SYMBOLS (e.g. `p, `n), not strings ("p").
   Comparing a symbol to a string causes "type".
2) Avoids "p"$... / "n"$... casts (string-parsing casts), which can trigger "nyi".
3) Avoids long$ casting for slice bounds; does slice math directly on timestamps/timespans.

Core idea:
- Build a normalized timestamp join key `ts` for both trades and quotes.
- For time-of-day types (n/t/u/v): ts = d0 + (0D + exchangeTime)
- For timestamp type (p):        ts = exchangeTime
- For datetime type (z):         ts = epoch + (0D + 1000000 * long$ exchangeTime)  (ms->ns)

Debug:
- Prints EVERY q query before execution and prints the result.
- Trades slice and Quotes slice are fetched in SEPARATE queries.
- Join/classify is its own query.
- You can run a single slice with --slice.

Example:
  python trade_quote_classify_sliced_v6.py --host HOST --port 1234 --region ldn \
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


# -------------------------
# q snippets / templates
# -------------------------

Q_META = r"""
(`metaTrades`metaQuotes)!(meta trades; meta quotes)
"""

Q_TYPE_INFO = r"""
d:__DATE__;
ric:__RIC__;

tTC:first exec t from meta trades where c=`exchangeTime;
qTC:first exec t from meta quotes where c=`exchangeTime;

tCap:first exec t from meta trades where c=`captureTime;
qCap:first exec t from meta quotes where c=`captureTime;

t1: 1#select exchangeTime,captureTime,price from trades where date=d, RIC=ric, not null exchangeTime;
q1: 1#select exchangeTime,captureTime,bid,ask from quotes where date=d, RIC=ric, not null exchangeTime;

(`tTC`qTC`tCap`qCap`tExSample`qExSample)!(
  tTC; qTC; tCap; qCap;
  $[0=count t1; ::; first t1`exchangeTime];
  $[0=count q1; ::; first q1`exchangeTime]
)
"""

Q_N_SLICES = r"""
d:__DATE__;
ric:__RIC__;
chunk:0D + __CHUNK__;   / force timespan
/ trade exchangeTime type symbol from meta (e.g. `n, `p)
tTC:first exec t from meta trades where c=`exchangeTime;

epoch:2000.01.01D00:00:00.000000000;
d0: d + 0D00:00:00.000000000;

/ normalize to timestamp (vectorized)
mkTS:{[et;tc]
  $[tc=`p; et;
    tc in `n`t`u`v; d0 + (0D00:00:00.000000000 + et);
    tc=`z; epoch + (0D00:00:00.000000000 + 1000000 * long$ et);
    `badType]
};

b: select tmin:min ts, tmax:max ts
   from update ts: mkTS[exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

$[null b`tmin; 0; 1 + (b`tmax - b`tmin) div chunk]
"""

Q_SLICE_PREFIX = r"""
d:__DATE__;
ric:__RIC__;
chunk:0D + __CHUNK__;         / force timespan
lb:   0D + __LOOKBACK__;      / force timespan
i:__I__;

tTC:first exec t from meta trades where c=`exchangeTime;
qTC:first exec t from meta quotes where c=`exchangeTime;

epoch:2000.01.01D00:00:00.000000000;
d0: d + 0D00:00:00.000000000;

/ normalize exchangeTime -> timestamp
mkTS:{[et;tc]
  $[tc=`p; et;
    tc in `n`t`u`v; d0 + (0D00:00:00.000000000 + et);
    tc=`z; epoch + (0D00:00:00.000000000 + 1000000 * long$ et);
    `badType]
};

b: select tmin:min ts, tmax:max ts
   from update ts: mkTS[exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

/ if no trades, callers will return empty/0
tmin:b`tmin;
tmax:b`tmax;

n: $[null tmin; 0; 1 + (tmax - tmin) div chunk];

/ slice bounds in timestamp space (half-open [sTS,eTS))
eps:0D00:00:00.000000001;

sTS: $[n=0; 0Np; tmin + chunk * i];
eTS: $[n=0; 0Np;
       i=n-1; tmax + eps;
       tmin + chunk * (i+1)];

sLbTS: sTS - lb;

/ timespan-of-day bounds for filtering time-of-day quote types (n/t/u/v)
sSp: sLbTS - d0;
eSp: eTS   - d0;
"""

Q_SLICE_DIAG = Q_SLICE_PREFIX + r"""
if[n=0; :(`error`msg)!(`noTrades;"no trades for (date,RIC)")];

(`tTC`qTC`tmin`tmax`n`sTS`eTS`sLbTS`sSp`eSp)!(
  tTC; qTC; tmin; tmax; n; sTS; eTS; sLbTS; sSp; eSp
)
"""

Q_TRADES_COUNT = Q_SLICE_PREFIX + r"""
if[n=0; :0];
exec count i
from trades
where date=d, RIC=ric, not null exchangeTime,
      mkTS[exchangeTime;tTC] >= sTS,
      mkTS[exchangeTime;tTC] <  eTS
"""

Q_TRADES_SAMPLE = Q_SLICE_PREFIX + r"""
if[n=0; :([])];

t: update ts: mkTS[exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

__N__#t where ts>=sTS, ts<eTS
"""

Q_QUOTES_COUNT = Q_SLICE_PREFIX + r"""
if[n=0; :0];

qCount:0;

if[qTC=`p;
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                exchangeTime>=sLbTS, exchangeTime<eTS;
];

if[qTC in `n`t`u`v;
  / compare in timespan-of-day space
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                (0D00:00:00.000000000 + exchangeTime) >= sSp,
                (0D00:00:00.000000000 + exchangeTime) <  eSp;
];

if[qTC=`z;
  / convert datetime->timestamp per row for filtering (only if needed)
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                (epoch + (0D00:00:00.000000000 + 1000000 * long$ exchangeTime)) >= sLbTS,
                (epoch + (0D00:00:00.000000000 + 1000000 * long$ exchangeTime)) <  eTS;
];

qCount
"""

Q_QUOTES_SAMPLE = Q_SLICE_PREFIX + r"""
if[n=0; :([])];

q: ();

if[qTC=`p;
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: exchangeTime
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sLbTS, exchangeTime<eTS;
];

if[qTC in `n`t`u`v;
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: d0 + (0D00:00:00.000000000 + exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           (0D00:00:00.000000000 + exchangeTime) >= sSp,
           (0D00:00:00.000000000 + exchangeTime) <  eSp;
];

if[qTC=`z;
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: epoch + (0D00:00:00.000000000 + 1000000 * long$ exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           ts>=sLbTS, ts<eTS;
];

__N__#`ts xasc q
"""

Q_JOIN_CLASSIFY = Q_SLICE_PREFIX + r"""
if[n=0; :([])];

/ trades slice (trade-sized)
t: update ts: mkTS[exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

t: t where ts>=sTS, ts<eTS;
if[0=count t; :([])];

/ quotes slice
q: ();

if[qTC=`p;
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: exchangeTime
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sLbTS, exchangeTime<eTS;
];

if[qTC in `n`t`u`v;
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: d0 + (0D00:00:00.000000000 + exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           (0D00:00:00.000000000 + exchangeTime) >= sSp,
           (0D00:00:00.000000000 + exchangeTime) <  eSp;
];

if[qTC=`z;
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: epoch + (0D00:00:00.000000000 + 1000000 * long$ exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           ts>=sLbTS, ts<eTS;
];

/ sort for aj; captureTime breaks ties at same ts
t: `RIC`ts xasc t;
q: `RIC`ts`captureTime xasc update mid:(bid+ask)%2f from q;

r: aj[`RIC`ts; t; q];

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

    ap.add_argument("--chunk", default="0D00:10:00.000000000", help="q timespan or time literal")
    ap.add_argument("--lookback", default="0D00:05:00.000000000", help="q timespan or time literal")

    ap.add_argument("--max-slices", type=int, default=3, help="-1 for all slices")
    ap.add_argument("--slice", type=int, default=None, help="Run only a specific slice index")

    ap.add_argument("--show-trades", type=int, default=5)
    ap.add_argument("--show-quotes", type=int, default=5)
    ap.add_argument("--show-result", type=int, default=10)

    ap.add_argument("--diag", action="store_true", help="Print meta/type diagnostics and slice bounds.")
    args = ap.parse_args()

    d = q_date_literal(args.date)
    ric = q_symbol_literal(args.ric)
    chunk = args.chunk.strip()
    lb = args.lookback.strip()

    compass = Compass(host=args.host, port=args.port, region=args.region)

    if args.diag:
        run_q(compass, "META", Q_META)
        run_q(compass, "TYPE_INFO", render(Q_TYPE_INFO, DATE=d, RIC=ric))

    n_slices_atom = run_q(compass, "N_SLICES", render(Q_N_SLICES, DATE=d, RIC=ric, CHUNK=chunk))
    n_slices = int(n_slices_atom)

    if n_slices <= 0:
        print("No trades found for (date,RIC).")
        return

    if args.slice is not None:
        indices = [args.slice]
    else:
        to_run = n_slices if args.max_slices == -1 else min(n_slices, args.max_slices)
        indices = list(range(to_run))

    print(f"\nProcessing slice indices: {indices} (n_slices={n_slices})")

    for i in indices:
        if args.diag:
            run_q(compass, f"SLICE_DIAG i={i}", render(Q_SLICE_DIAG, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))

        tc = run_q(compass, f"TRADES_COUNT i={i}", render(Q_TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        tc_i = int(tc)

        if args.show_trades > 0 and tc_i > 0:
            run_q(
                compass,
                f"TRADES_SAMPLE i={i}",
                render(Q_TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades),
            )

        qc = run_q(compass, f"QUOTES_COUNT i={i}", render(Q_QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i))
        qc_i = int(qc)

        if args.show_quotes > 0 and qc_i > 0:
            run_q(
                compass,
                f"QUOTES_SAMPLE i={i}",
                render(Q_QUOTES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_quotes),
            )

        if args.show_result > 0 and tc_i > 0:
            run_q(
                compass,
                f"JOIN_CLASSIFY i={i}",
                render(Q_JOIN_CLASSIFY, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_result),
            )


if __name__ == "__main__":
    main()
