"""
Betting analysis v2: after 7 same-colour 5m candles, bet 'opposite colour' on
candle #8 (index s+7) and candle #9 (index s+8).

fix: the candle after a *maximal* run is opposite by definition, so #8 must be
read at index s+7 (= end of a length-7 run) and #9 at s+8, not s+L, s+L+1.
"""
import json
import time
import datetime as dt
import random

from common import wilson

with open("btcusdt_5m.json") as f:
    rows = json.load(f)
rows = rows if rows[-1][0] < time.time() * 1000 - 300_000 else rows[:-1]
rows.sort(key=lambda r: r[0])
lab = [1 if r[4] >= r[1] else 0 for r in rows]
opens = [r[0] for r in rows]
n = len(lab)

runs, i = [], 0
while i < n:
    j = i
    while j + 1 < n and lab[j + 1] == lab[i]:
        j += 1
    runs.append((lab[i], j - i + 1, i))
    i = j + 1

# event = the moment the 7th consecutive candle closes at index s+6
ev = [(c, L, s) for c, L, s in runs if L >= 7 and s + 8 < n]
N = len(ev)
print(f"candles={n}  7-run events={N}")

# is candle #8 / #9 opposite to the streak colour?
a = [1 if lab[s + 7] != c else 0 for c, L, s in ev]
b = [1 if lab[s + 8] != c else 0 for c, L, s in ev]


def pc(k, tot):
    return f"{k:>4}/{tot} = {k/tot:6.2%}"


print("\n=== win chance per bet (bet 'opposite colour') ===")
for name, arr in (("candle #8", a), ("candle #9", b)):
    lo, hi = wilson(sum(arr), N)
    print(f"  {name}: {pc(sum(arr), N)}   95% CI {lo:.2%}-{hi:.2%}")

print("\n=== both candles together (equal stake on #8 and #9) ===")
bw = sum(1 for x, y in zip(a, b) if x and y)
ow = sum(1 for x, y in zip(a, b) if x != y)
bl = N - bw - ow
print(f"  both win  : {pc(bw, N)}")
print(f"  one win   : {pc(ow, N)}")
print(f"  both lose : {pc(bl, N)}")
lo, hi = wilson(bw, N)
print(f"  'at least one win': {pc(bw+ow, N)}   (95% CI for both-win: {lo:.2%}-{hi:.2%})")

print("\n=== conditional structure ===")
s8 = sum(1 for x in a if not x)
print(f"  P(#9 opposite | #8 same)     : {pc(sum(y for x, y in zip(a, b) if not x), s8)}")
print(f"  P(#9 opposite | #8 opposite) : {pc(sum(y for x, y in zip(a, b) if x), sum(a))}")

random.seed(7)
boots = sorted(sum(random.choices([1 if x and y else 0 for x, y in zip(a, b)], k=N)) / N
               for _ in range(4000))
print(f"  bootstrap 95% CI (both win): {boots[100]:.2%} - {boots[3899]:.2%}")

print("\n=== per year ===")
by = {}
for (c, L, s), x, y in zip(ev, a, b):
    yr = dt.datetime.fromtimestamp(opens[s] / 1000, dt.timezone.utc).year
    d = by.setdefault(yr, [0, 0, 0, 0])
    d[0] += 1
    d[1] += x
    d[2] += y
    d[3] += x and y
for yr in sorted(by):
    t, w1, w2, bb = by[yr]
    print(f"  {yr}: events={t:>4}  #8 win {w1/t:.2%}  #9 win {w2/t:.2%}  both {bb/t:.2%}")

# ---------------- money ----------------
SH = 100
def leg(p):
    fee = SH * 0.07 * p * (1 - p)
    cost = SH * p + fee
    return fee, cost, SH - cost

print("\n=== money: 100 shares per window ===")
for p in (0.50, 0.51, 0.52, 0.53, 0.55):
    fee, cost, win = leg(p)
    print(f"  fill {p:.2f}: fee ${fee:.2f}, stake ${cost:.2f}, win +${win:.2f}, "
          f"lose -${cost:.2f}, breakeven hit rate {cost/SH:.2%}")

for label, p in (("optimistic 50c", 0.50), ("realistic 52c", 0.52), ("thick 55c", 0.55)):
    fee, cost, win = leg(p)
    e8 = sum(win if x else -cost for x in a) / N
    e2 = (bw * 2 * win + ow * (win - cost) + bl * (-2 * cost)) / N
    print(f"\n  [{label}]")
    print(f"    #8 only      : ${e8:+.3f}/event -> ${e8*590:+.0f}/yr at 590 events")
    print(f"    #8 + #9 flat : ${e2:+.3f}/event -> ${e2*590:+.0f}/yr")
    print(f"    P(profit) when betting both = {bw/N:.2%}")

print("\n=== martingale variant: bet #8, if it loses double on #9 ===")
p = 0.50
fee, cost, win = leg(p)
tot = 0.0
# #8 wins -> +win ; #8 loses, #9 wins -> -cost + 2*win ; both lose -> -cost - 2*cost
for x, y in zip(a, b):
    if x:
        tot += win
    elif y:
        tot += -cost + 2 * win
    else:
        tot += -cost - 2 * cost
print(f"  total ${tot:+.2f} over {N} events -> ${tot/N:+.3f}/event -> ${tot/N*590:+.0f}/yr")
print(f"  worst case seen: 2 consecutive losses = ${-(cost+2*cost):.2f} per $50 base")
