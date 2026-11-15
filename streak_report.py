"""
BTC streak study, v2.

Fix vs v1: a "7 candle event" is the *7th* candle of a run. What happens next is
`run_length - 7` more same-colour candles. If that number >= 4 then no opposite
candle appeared within the next 4 candles -> user's claim fails.

Also: robustness across 5m / 15m / 1h, and fee-adjusted EV.
"""
import json
import os
import time
import urllib.request
import datetime as dt
from collections import Counter

from common import maximal_runs, wilson

BASE = "https://api.binance.com/api/v3/klines"
STEP = {"5m": 300_000, "15m": 900_000, "1h": 3_600_000}
START = int(dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)


def fetch(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "streak-research/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(1.0 + attempt)


def load(tf):
    cache = f"btcusdt_{tf}.json"
    step = STEP[tf]
    if os.path.exists(cache):
        with open(cache) as f:
            rows = json.load(f)
        if time.time() * 1000 - rows[-1][0] < 6 * 3600 * 1000:
            return rows
    now = int(time.time() * 1000)
    cur, rows = START, []
    while cur < now:
        batch = fetch(f"{BASE}?symbol=BTCUSDT&interval={tf}&startTime={cur}&limit=1000")
        if not batch:
            break
        rows.extend(batch)
        cur = int(batch[-1][0]) + step
    out = [[int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])] for r in rows]
    with open(cache, "w") as f:
        json.dump(out, f)
    return out


def p_continue(lab, k):
    same = tot = 0
    for t in range(k, len(lab) - 1):
        if all(lab[t - m] == lab[t] for m in range(k)):
            tot += 1
            same += lab[t + 1] == lab[t]
    return same, tot


def analyse(tf, streak=7):
    rows = load(tf)
    step = STEP[tf]
    seen = {int(r[0]): r for r in rows}
    c = [seen[k] for k in sorted(seen)]
    now = int(time.time() * 1000)
    if c and c[-1][0] + step > now:
        c = c[:-1]
    opens = [x[0] for x in c]
    lab = [1 if x[4] >= x[1] else 0 for x in c]
    n = len(lab)
    rs = maximal_runs(lab)
    ev = [r for r in rs if r[1] >= streak]
    # exclude the final run if it may be truncated by the data edge
    ev = [r for r in ev if r[2] + r[1] < n]
    extra = Counter(r[1] - streak for r in ev)
    print(f"=== {tf} ===  candles={n}  up={sum(lab)/n:.2%}  "
          f"range {dt.datetime.fromtimestamp(opens[0]/1000, dt.timezone.utc):%Y-%m} .. "
          f"{dt.datetime.fromtimestamp(opens[-1]/1000, dt.timezone.utc):%Y-%m}")
    print(f"  runs >= {streak}: {len(ev)}")
    print(f"  longest run: {max(r[1] for r in rs)}")
    row = []
    for w in (1, 3, 4, 5, 6):
        fail = sum(v for k, v in extra.items() if k >= w)
        lo, hi = wilson(fail, len(ev))
        print(f"  no opposite within {w}: {fail}/{len(ev)} = {fail/len(ev):.2%} "
              f"(95% CI {lo:.1%}-{hi:.1%})  -> opposite did appear {1-fail/len(ev):.2%}")
    dist = " ".join(f"{k+1}:{extra.get(k,0)}" for k in range(0, 9))
    print(f"  opposite arrives at candle +1..+9 : {dist}")
    s, t = p_continue(lab, streak)
    lo, hi = wilson(s, t)
    print(f"  P(next candle continues | {streak} in a row) = {s/t:.2%} "
          f"n={t} (95% CI {lo:.2%}-{hi:.2%})   -> P(reversal) = {1-s/t:.2%}")
    print()
    return {"tf": tf, "n": n, "events": len(ev), "extra": extra, "pcont": s / t, "ncont": t}


res = [analyse("5m"), analyse("15m"), analyse("1h")]

print("=== econ: flat bet 'reversal next candle' on Polymarket 5m, price 50c ===")
p = res[0]["pcont"]
p_rev = 1 - p
shares, price = 100, 0.50
fee = shares * 0.07 * price * (1 - price)
stake = shares * price + fee
print(f"  measured P(reversal | 7 in a row) = {p_rev:.2%}")
print(f"  buy {shares} shares @ {price:.2f}: cost ${stake:.2f} (incl ${fee:.2f} fee), "
      f"pays ${shares:.2f} if right")
print(f"  breakeven hit rate = {stake/shares:.2%}")
print(f"  EV per bet = ${p_rev*shares - stake:+.2f}  ({100*(p_rev*shares-stake)/stake:+.2f}% of stake)")
print("  NOTE: needs real 50c fills; a window is priced by the book, not by this study.")

print("\n=== drawdown: if you had to keep betting until the reversal ===")
for tf in ("5m",):
    r = res[0]
    print("  5m distribution of extra same-colour candles after the 7th:")
    for k in sorted(r["extra"]):
        print(f"    +{k}: {r['extra'][k]}")
