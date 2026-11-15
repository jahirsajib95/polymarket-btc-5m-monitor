"""
Can '80% profit' be had? What high win rate actually costs.
1. The identity: on a binary market, win rate = price you pay, EV = -fee.
2. Real edge (7-streak fade): probability of being in profit vs horizon.
"""
import json, time, random, statistics

with open("btcusdt_5m.json") as f:
    rows = json.load(f)
rows = rows if rows[-1][0] < time.time() * 1000 - 300_000 else rows[:-1]
rows.sort(key=lambda r: r[0])
lab = [1 if r[4] >= r[1] else 0 for r in rows]
n = len(lab)

runs, i = [], 0
while i < n:
    j = i
    while j + 1 < n and lab[j + 1] == lab[i]:
        j += 1
    runs.append((lab[i], j - i + 1, i))
    i = j + 1
ev = [(c, L, s) for c, L, s in runs if L >= 7 and s + 8 < n]
a = [1 if lab[s + 7] != c else 0 for c, L, s in ev]
b = [1 if lab[s + 8] != c else 0 for c, L, s in ev]

print("=" * 66)
print("1. THE HIGH-WIN-RATE TRADE: what '80% win rate' really is")
print("=" * 66)
print("On any binary market, if you buy a side at price p, you win ~p of the")
print("time by construction. The house fee is what you actually pay.\n")
print(" price | win rate | fee/share | EV per $100 staked | breakeven needed")
for p in (0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99):
    fee = 0.07 * p * (1 - p)          # per share, C=1
    cost = p + fee                     # per share
    win = 1 - p - fee
    ev_pct = 100 * (p * win - (1 - p) * cost) / cost
    print(f"  {p:.2f} |  {p*100:5.1f}%  |  {fee*100:5.2f}c   |  {ev_pct:+6.2f}%"
          f"           | {cost*100:5.2f}c")
print("\n  -> '80% win rate' is not a strategy, it is a price tag.")
print("     You can have 80% wins today, and you pay 1.12c/share for it every time.")
print("     100 shares @80c: win +$18.88 (80% of the time), lose -$81.12 (20%)")
print("     EV = 0.8*18.88 - 0.2*81.12 = -$1.12  == exactly the fee, every time.\n")
print("  To beat it you need win rate ABOVE the price. That gap is the only")
print("  thing anyone in this market actually trades.\n")

# ---------------- 2. the real edge, over real horizons ----------------
SH, P = 100, 0.50
def leg(p):
    fee = SH * 0.07 * p * (1 - p)
    cost = SH * p + fee
    return cost, SH - cost

def series(p, both):
    cost, win = leg(p)
    out = []
    for x, y in zip(a, b):
        pl = (win if x else -cost)
        if both:
            pl += (win if y else -cost)
        out.append(pl)
    return out

print("=" * 66)
print("2. THE ONLY REAL EDGE FOUND: 7-streak fade (54% vs 51.75% breakeven)")
print("=" * 66)
EVENTS_PER_YEAR = 590
for label, p, both in (("#8 only @50c", 0.50, False), ("#8 only @52c", 0.52, False),
                       ("#8+#9 @50c", 0.50, True), ("#8+#9 @52c", 0.52, True)):
    s = series(p, both)
    mu = statistics.mean(s)
    sd = statistics.pstdev(s)
    print(f"\n{label}: EV ${mu:+.2f}/event, sd ${sd:.2f}")
    print("  horizon      events   P(profit)   median P&L    5th pct")
    for months, h in (("1 month", 49), ("3 months", 148), ("6 months", 295),
                      ("1 year", 590), ("2 years", 1180), ("5 years", 2950)):
        random.seed(11)
        trials = [sum(random.choices(s, k=h)) for _ in range(20000)]
        trials.sort()
        pp = sum(1 for t in trials if t > 0) / len(trials)
        print(f"  {months:<10} {h:>7}   {pp:>7.1%}     ${trials[10000]:>+9.0f}"
              f"  ${trials[1000]:>+9.0f}")
    # worst drawdown over a year
    random.seed(3)
    dds = []
    for _ in range(3000):
        cum, peak, dd = 0, 0, 0
        for v in random.choices(s, k=590):
            cum += v
            peak = max(peak, cum)
            dd = min(dd, cum - peak)
        dds.append(dd)
    dds.sort()
    print(f"  worst drawdown in 1 year: median ${dds[1500]:.0f}, "
          f"10th pct ${dds[300]:.0f}, 1st pct ${dds[30]:.0f}")

print("\n" + "=" * 66)
print("3. what an '80% win rate' system looks like when it finally breaks")
print("=" * 66)
print("  a 90%-win-rate book selling tails: 9 wins of +$100, 1 loss of -$1,000")
print(f"  9*100 - 1000 = ${9*100-1000:+d}  -> the '99% success' story ends in one trade")
