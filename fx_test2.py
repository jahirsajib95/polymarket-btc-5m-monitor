"""Fairer versions of the two classic FX factor strategies, same cached data."""
import json, math, statistics
import datetime as dt

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X",
         "USDCAD=X", "NZDUSD=X"]
with open("fx_daily.json") as f:
    data = {k: (v[0], v[1]) for k, v in json.load(f).items()}


def monthly(ts, cl):
    m = {}
    for t, c in zip(ts, cl):
        d = dt.datetime.fromtimestamp(t, dt.timezone.utc)
        m[(d.year, d.month)] = c
    return m


series = {s: monthly(*data[s]) for s in PAIRS}
months = sorted(set().union(*[set(v) for v in series.values()]))
months = [m for m in months if all(m in series[s] for s in PAIRS)]
T = len(months) - 1
R = {s: [series[s][months[i + 1]] / series[s][months[i]] - 1 for i in range(T)]
     for s in PAIRS}


def stats(pr, label):
    n = len(pr)
    mu, sd = statistics.mean(pr), statistics.pstdev(pr)
    eq = math.prod(1 + x for x in pr)
    peak = eqc = 1.0
    mdd = 0
    for x in pr:
        eqc *= (1 + x)
        peak = max(peak, eqc)
        mdd = min(mdd, eqc / peak - 1)
    print(f"  {label:<40} CAGR {eq**(12/n)-1:>7.2%}  vol {sd*math.sqrt(12):>5.2%}  "
          f"Sharpe {mu/sd*math.sqrt(12):>5.2f}  maxDD {mdd:>7.1%}  "
          f"month-win {sum(1 for x in pr if x>0)/n:>5.1%}")


def vol_target(pr, target=0.10):
    """scale the whole series to a 10% vol target (informational only)"""
    sd = statistics.pstdev(pr) * math.sqrt(12)
    k = target / sd if sd else 1
    return [x * k for x in pr]


# --- A. vol-scaled TSMOM (position ~ 1/sigma per pair) ---
def tsmom_vol(lookback=12, cost_bps=2.0):
    # realised vol per pair from monthly returns
    vol = {s: statistics.pstdev(R[s][:12]) if T > 12 else 0.01 for s in PAIRS}
    pr, prev = [], {s: 0.0 for s in PAIRS}
    for i in range(lookback, T):
        port = 0.0
        for s in PAIRS:
            v = statistics.pstdev(R[s][max(0, i - 12):i]) or 0.01
            pos = (1 if series[s][months[i]] > series[s][months[i - lookback]] else -1)
            w = min(0.03 / v, 3.0) / len(PAIRS) * len(PAIRS) / 7
            pos = pos * min(0.03 / v, 3.0)
            port += pos * R[s][i]
            port -= cost_bps / 1e4 * abs(pos - prev[s])
            prev[s] = pos
        pr.append(port / len(PAIRS))
    return pr


# --- B. cross-sectional momentum: long top-3, short bottom-3 ---
def csmom(lookback=12, cost_bps=2.0, k=3):
    pr, prev = [], {s: 0.0 for s in PAIRS}
    for i in range(lookback, T):
        sc = {s: series[s][months[i]] / series[s][months[i - lookback]] - 1 for s in PAIRS}
        order = sorted(PAIRS, key=lambda s: sc[s])
        pos = {s: 0.0 for s in PAIRS}
        for s in order[:k]:
            pos[s] = -1 / k
        for s in order[-k:]:
            pos[s] = 1 / k
        port = 0.0
        for s in PAIRS:
            port += pos[s] * R[s][i]
            port -= cost_bps / 1e4 * abs(pos[s] - prev[s])
            prev[s] = pos[s]
        pr.append(port)
    return pr


# --- C. 1-month cross-sectional reversal ---
def csmom_rev(lookback=1, cost_bps=2.0, k=3):
    return csmom(lookback, cost_bps, k)


print("=== vol-scaled / cross-sectional versions (2006-2026, 234 months) ===")
for lb in (3, 6, 12):
    stats(vol_target(tsmom_vol(lb)), f"TSMOM vol-scaled {lb}m")
for lb, nm in ((12, "12m"), (6, "6m"), (3, "3m")):
    stats(vol_target(csmom(lb)), f"CSMOM long/short top3 {nm}")
stats(vol_target(csmom_rev(1)), "CS 1m reversal (top3/bottom3)")

print("\n=== cost sensitivity of the best variant ===")
best = csmom(12)
for c in (0, 2, 5, 10, 20, 40):
    stats(vol_target(csmom(12, c)), f"CSMOM 12m @ {c} bps turnover")

print("\n=== reference: 10% vol target means these are the SAME Sharpe ===")
print("  a Sharpe 0.5 strategy at 10% vol = ~5% a year, with ~15-20% drawdowns.")
