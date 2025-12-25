#!/usr/bin/env python3
"""
trade_quote_classify_sliced_v5.py

Robust, debug-first slicing for:
- separate TRADES slice query
- separate QUOTES slice query
- ASOF JOIN + MID + BUY/SELL/MID classification

Fixes the recurring q "type" error by:
1) Detecting exchangeTime storage type from `meta` (no scanning)
2) Normalizing both trades and quotes to a timestamp key `ts` for join
3) Filtering quotes using *native exchangeTime type* (fast & type-safe), then attaching `ts`

No pandas.

It prints EVERY q query before running it, plus the result, so you can see exactly
which step fails if there is any issue.

Example:
  python trade_quote_classify_sliced_v5.py --host HOST --port 1234 --region ldn \
    --date 2025.10.22 --ric NVLH.PA \
    --chunk 0D00:10:00.000000000 --lookback 0D00:05:00.000000000 \
    --max-slices 3 --show-trades 5 --show-quotes 5 --show-result 5 --diag

Run one specific slice:
  python trade_quote_classify_sliced_v5.py ... --slice 12 --show-result 50
"""

from __future__ import annotations

import argparse
from goldmansachs.compass_pykx import Compass


# ----------------------------
# Helpers for q literals
# ----------------------------
def q_date_literal(s: str) -> str:
    """Accept YYYY.MM.DD or YYYY-MM-DD -> q date literal YYYY.MM.DD"""
    s = s.strip()
    return s.replace("-", ".") if "-" in s else s


def q_symbol_literal(s: str) -> str:
    """Return q symbol literal with leading backtick."""
    s = s.strip()
    return s if s.startswith("`") else f"`{s}"


def render(template: str, **kw) -> str:
    """Simple placeholder replace: __KEY__ -> value (string)."""
    out = template
    for k, v in kw.items():
        out = out.replace(f"__{k}__", str(v))
    return out


def run_q(compass: Compass, name: str, q: str):
    print(f"\n[{name}] q:\n" + "-" * 100)
    print(q.strip())
    print("-" * 100)
    try:
        out = compass.run_query_sync(q)
    except Exception as e:
        print(f"[{name}] FAILED with exception: {e}\n")
        raise
    print(f"[{name}] result:\n{out}\n")
    return out


# ----------------------------
# q templates
# ----------------------------
Q_META = r"""
(`metaTrades`metaQuotes)!(meta trades; meta quotes)
"""

Q_TYPE_INFO = r"""
d:__DATE__;
ric:__RIC__;

/ exchangeTime storage type from meta (single char: "p","n","t","z",...)
tTC:first exec t from meta trades where c=`exchangeTime;
qTC:first exec t from meta quotes where c=`exchangeTime;

/ show also captureTime types (sometimes helpful)
tCapTC:first exec t from meta trades where c=`captureTime;
qCapTC:first exec t from meta quotes where c=`captureTime;

/ show price/bid/ask types
tPriceTC:first exec t from meta trades where c=`price;
qBidTC:first exec t from meta quotes where c=`bid;
qAskTC:first exec t from meta quotes where c=`ask;

/ sample values (first row)
t1: 1#select exchangeTime,captureTime,price from trades where date=d, RIC=ric, not null exchangeTime;
q1: 1#select exchangeTime,captureTime,bid,ask from quotes where date=d, RIC=ric, not null exchangeTime;

(`tTC`qTC`tCapTC`qCapTC`tPriceTC`qBidTC`qAskTC`tExSample`qExSample)!(
  tTC; qTC; tCapTC; qCapTC; tPriceTC; qBidTC; qAskTC;
  $[0=count t1; ::; first t1`exchangeTime];
  $[0=count q1; ::; first q1`exchangeTime]
)
"""

Q_N_SLICES = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;

/ exchangeTime type char from meta
tTC:first exec t from meta trades where c=`exchangeTime;

/ normalize exchangeTime -> timestamp
mkTS:{[d;et;tc]
  $[tc="p"; et;
    tc="n"; timestamp$ (d + et);
    tc="t"; timestamp$ (d + et);
    tc="u"; timestamp$ (d + time$et);   / minute -> time -> ts
    tc="v"; timestamp$ (d + time$et);   / second -> time -> ts
    tc="z"; timestamp$ et;              / datetime -> ts
    `type]
};

b: select tmin:min ts, tmax:max ts
   from update ts: mkTS[d;exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

$[null b`tmin; 0; 1 + (long$b`tmax - long$b`tmin) div long$chunk]
"""

Q_SLICE_PREFIX = r"""
d:__DATE__;
ric:__RIC__;
chunk:__CHUNK__;
lb:__LOOKBACK__;
i:__I__;

tTC:first exec t from meta trades where c=`exchangeTime;
qTC:first exec t from meta quotes where c=`exchangeTime;

mkTS:{[d;et;tc]
  $[tc="p"; et;
    tc="n"; timestamp$ (d + et);
    tc="t"; timestamp$ (d + et);
    tc="u"; timestamp$ (d + time$et);
    tc="v"; timestamp$ (d + time$et);
    tc="z"; timestamp$ et;
    `type]
};

b: select tmin:min ts, tmax:max ts
   from update ts: mkTS[d;exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

if[null b`tmin; :`noTrades];

tminN: long$b`tmin;
tmaxN: long$b`tmax;
chunkN: long$chunk;
lbN:    long$lb;

n: 1 + (tmaxN - tminN) div chunkN;

if[i<0 or i>=n; '("slice i out of range, i=",string i," n=",string n)];

sN: tminN + chunkN * i;
eN: $[i=n-1; tmaxN + 1; tminN + chunkN * (i+1)];

sTS:"p"$sN;
eTS:"p"$eN;
sLbTS:"p"$(sN - lbN);

/ For timespan bounds when quotes.exchangeTime is timespan-of-day (n)
d0: timestamp$ d;
sSp: sLbTS - d0;
eSp: eTS - d0;

/ For time bounds when quotes.exchangeTime is time-of-day (t)
sTm: time$ sLbTS;
eTm: time$ eTS;
"""

Q_TRADES_COUNT = Q_SLICE_PREFIX + r"""
if[`noTrades~::; :0];
exec count i
from trades
where date=d, RIC=ric, not null exchangeTime,
      mkTS[d;exchangeTime;tTC] >= sTS,
      mkTS[d;exchangeTime;tTC] <  eTS
"""

Q_TRADES_SAMPLE = Q_SLICE_PREFIX + r"""
if[`noTrades~::; :([])];

t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
          ts: mkTS[d;exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

__N__#t where ts>=sTS, ts<eTS
"""

Q_QUOTES_COUNT = Q_SLICE_PREFIX + r"""
if[`noTrades~::; :0];

qCount:0;

if[qTC="p";
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                exchangeTime>=sLbTS, exchangeTime<eTS;
];

if[qTC="n";
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                exchangeTime>=sSp, exchangeTime<eSp;
];

if[qTC="t" or qTC="u" or qTC="v";
  / treat minute/second like time for filtering
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                exchangeTime>=sTm, exchangeTime<eTm;
];

if[qTC="z";
  qCount: exec count i from quotes
          where date=d, RIC=ric, not null exchangeTime,
                timestamp$ exchangeTime>=sLbTS, timestamp$ exchangeTime<eTS;
];

qCount
"""

Q_QUOTES_SAMPLE = Q_SLICE_PREFIX + r"""
if[`noTrades~::; :([])];

q: ();

if[qTC="p";
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: exchangeTime
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sLbTS, exchangeTime<eTS;
];

if[qTC="n";
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: timestamp$ (d + exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sSp, exchangeTime<eSp;
];

if[qTC="t" or qTC="u" or qTC="v";
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: timestamp$ (d + time$ exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sTm, exchangeTime<eTm;
];

if[qTC="z";
  q: select date,primaryRIC,RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: timestamp$ exchangeTime
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           ts>=sLbTS, ts<eTS;
];

__N__#`ts xasc q
"""

Q_JOIN_CLASSIFY = Q_SLICE_PREFIX + r"""
if[`noTrades~::; :([])];

/ trades slice
t: select date,primaryRIC,RIC,exchangeTime,captureTime,price,size,MIC,cond,eutradetype,trade_xid,mmt_class,aucType,
          ts: mkTS[d;exchangeTime;tTC]
   from trades
   where date=d, RIC=ric, not null exchangeTime;

t: t where ts>=sTS, ts<eTS;

if[0=count t; :([])];

/ quotes slice (native filtering), then compute mid
q: ();

if[qTC="p";
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: exchangeTime
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sLbTS, exchangeTime<eTS;
];

if[qTC="n";
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: timestamp$ (d + exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sSp, exchangeTime<eSp;
];

if[qTC="t" or qTC="u" or qTC="v";
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: timestamp$ (d + time$ exchangeTime)
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           exchangeTime>=sTm, exchangeTime<eTm;
];

if[qTC="z";
  q: select RIC,exchangeTime,captureTime,bid,bidSize,ask,askSize,MIC,seqNo,
            ts: timestamp$ exchangeTime
     from quotes
     where date=d, RIC=ric, not null exchangeTime,
           ts>=sLbTS, ts<eTS;
];

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
    ap.add_argument("--chunk", default="0D00:10:00.000000000", help="q timespan literal")
    ap.add_argument("--lookback", default="0D00:05:00.000000000", help="q timespan literal")
    ap.add_argument("--max-slices", type=int, default=3, help="-1 for all slices")
    ap.add_argument("--slice", type=int, default=None, help="Run only a specific slice index")
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

    print(f"\nProcessing slices: {indices} (n_slices={n_slices})")

    for i in indices:
        # TRADES COUNT
        tc = run_q(
            compass,
            f"TRADES_COUNT slice={i}",
            render(Q_TRADES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i),
        )
        tc_i = int(tc)

        # TRADES SAMPLE
        if args.show_trades > 0 and tc_i > 0:
            run_q(
                compass,
                f"TRADES_SAMPLE slice={i}",
                render(Q_TRADES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_trades),
            )

        # QUOTES COUNT
        qc = run_q(
            compass,
            f"QUOTES_COUNT slice={i}",
            render(Q_QUOTES_COUNT, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i),
        )
        qc_i = int(qc)

        # QUOTES SAMPLE
        if args.show_quotes > 0 and qc_i > 0:
            run_q(
                compass,
                f"QUOTES_SAMPLE slice={i}",
                render(Q_QUOTES_SAMPLE, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_quotes),
            )

        # JOIN + CLASSIFY SAMPLE
        if args.show_result > 0 and tc_i > 0:
            run_q(
                compass,
                f"JOIN_CLASSIFY slice={i}",
                render(Q_JOIN_CLASSIFY, DATE=d, RIC=ric, CHUNK=chunk, LOOKBACK=lb, I=i, N=args.show_result),
            )


if __name__ == "__main__":
    main()
