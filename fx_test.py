"""
Is there a 'good' forex strategy? Test the most documented ones on 7 majors.
Data: Yahoo Finance daily FX, 2000 -> today. Monthly rebalance.
"""
import json, time, urllib.request, statistics, math, random
import datetime as dt

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X",
         "USDCAD=X", "NZDUSD=X"]
CACHE = "fx_daily.json"


def fetch(sym, p1, p2):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?period1={p1}&period2={p2}&interval=1d")
    for a in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if a == 4:
                raise
            time.sleep(1.5)


def load():
    import os
    if os.path.exists(CACHE):
        with open(CACHE) as f:
            return {k: (v[0], v[1]) for k, v in json.load(f).items()}
    p1 = int(dt.datetime(2000, 1, 1).timestamp())
    p2 = int(time.time())
    out = {}
    for s in PAIRS:
        d = fetch(s, p1, p2)["chart"]["result"][0]
        ts = d["timestamp"]
        cl = d["indicators"]["quote"][0]["close"]
        rows = [(t, c) for t, c in zip(ts, cl) if c]
        out[s] = ([r[0] for r in rows], [r[1] for r in rows])
        print(f"  {s}: {len(rows)} days  {dt.datetime.fromtimestamp(rows[0][0], dt.timezone.utc):%Y-%m-%d}"
              f" -> {dt.datetime.fromtimestamp(rows[-1][0], dt.timezone.utc):%Y-%m-%d}")
    with open(CACHE, "w") as f:
        json.dump(out, f)
    return out


data = load()

# month-end close per pair
def monthly(ts, cl):
    m = {}
    for t, c in zip(ts, cl):
        d = dt.datetime.fromtimestamp(t, dt.timezone.utc)
        m[(d.year, d.month)] = c
    return m


series = {s: monthly(*data[s]) for s in PAIRS}
months = sorted(set().union(*[set(v) for v in series.values()]))
months = [m for m in months if all(m in series[s] for s in PAIRS)]
print(f"\ncommon months: {len(months)}  {months[0]} -> {months[-1]}")


def rets(s, months):
    px = [series[s][m] for m in months]
    return [px[i + 1] / px[i] - 1 for i in range(len(px) - 1)]


R = {s: rets(s, months) for s in PAIRS}
T = len(months) - 1


def stats(pr, label):
    n = len(pr)
    mu = statistics.mean(pr)
    sd = statistics.pstdev(pr)
    eq = 1.0
    curve = []
    for x in pr:
        eq *= (1 + x)
        curve.append(eq)
    peak, mdd = 0, 0
    for v in curve:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1)
    cagr = eq ** (12 / n) - 1
    sharpe = mu / sd * math.sqrt(12) if sd else 0
    hit = sum(1 for x in pr if x > 0) / n
    worst = min(pr)
    print(f"  {label:<42} CAGR {cagr:>6.2%}  vol {sd*math.sqrt(12):>5.2%}  "
          f"Sharpe {sharpe:>5.2f}  maxDD {mdd:>7.1%}  month-win {hit:>5.1%}")
    return {"cagr": cagr, "sharpe": sharpe, "mdd": mdd, "hit": hit, "eq": eq}


def tsmom(lookback, cost_bps=2.0):
    """long if past `lookback` months up, short if down; monthly rebalance"""
    pr = []
    prev = {s: 0 for s in PAIRS}
    for i in range(T):
        if i < lookback:
            continue
        port = 0.0
        for s in PAIRS:
            p0 = series[s][months[i - lookback]]
            p1 = series[s][months[i]]
            pos = 1 if p1 > p0 else -1
            port += pos * R[s][i]
            port -= cost_bps / 1e4 * abs(pos - prev[s])
            prev[s] = pos
        pr.append(port / len(PAIRS))
    return pr


print("\n=== 1. time-series momentum (long/short, 7 majors, eq. weight) ===")
for lb in (1, 3, 6, 12):
    stats(tsmom(lb), f"TSMOM {lb}m lookback", )

print("\n=== 2. cost sensitivity (12m TSMOM) ===")
for c in (0, 2, 5, 10, 20):
    stats(tsmom(12, c), f"12m TSMOM, {c} bps per unit turnover")

print("\n=== 3. control: random signals, same turnover (100 runs) ===")
random.seed(1)
sharpes = []
for _ in range(100):
    pr = []
    for i in range(12, T):
        port = 0.0
        for s in PAIRS:
            port += random.choice((1, -1)) * R[s][i]
        pr.append(port / len(PAIRS))
    m = statistics.mean(pr)
    sd = statistics.pstdev(pr)
    sharpes.append(m / sd * math.sqrt(12))
sharpes.sort()
print(f"  random-signal Sharpe: median {sharpes[50]:+.2f}, "
      f"5-95pct {sharpes[5]:+.2f} to {sharpes[95]:+.2f}, "
      f"best {sharpes[-1]:+.2f}")

print("\n=== 4. buy & hold each pair (no timing) ===")
for s in PAIRS:
    stats(R[s], f"B&H {s[:-2]}")
avg = [statistics.mean(R[s][i] for s in PAIRS) for i in range(T)]
stats(avg, "B&H equal-weight basket")

print("\n=== 5. 12m TSMOM year by year ===")
pr = tsmom(12)
start = 12
cur = None
acc = []
for i, x in enumerate(pr):
    y = months[i + start][0]
    if y != cur and acc:
        print(f"  {cur}: {math.prod(1 + a for a in acc) - 1:>+7.2%}", end="")
        cur = y
        acc = []
        if (y - months[start][0]) % 4 == 0:
            print()
    cur = y
    acc.append(x)
print(f"  {cur}: {math.prod(1 + a for a in acc) - 1:>+7.2%}")

print(f"\n  12m TSMOM: {len(pr)} months, "
      f"final equity x{math.prod(1 + a for a in pr):.2f}")
