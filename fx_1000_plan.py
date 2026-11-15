"""
$1,000 forex account: cost + sizing decide survival, not signal.
Section 3 models trades in R units (1R = the money risked), with fat-tailed
slippage taken straight from EURUSD's measured excess kurtosis.
"""
import json, math, random, statistics

with open("fx_daily.json") as f:
    data = {k: (v[0], v[1]) for k, v in json.load(f).items()}
ts, cl = data["EURUSD=X"]
rets = [cl[i + 1] / cl[i] - 1 for i in range(len(cl) - 1) if cl[i] and cl[i + 1]]
sd = statistics.pstdev(rets)
mu = statistics.mean(rets)
kurt = sum((r - mu) ** 4 for r in rets) / len(rets) / sd ** 4
print(f"EURUSD: n={len(rets)} days  sd={sd:.3%}  ann vol={sd*math.sqrt(252):.1%}  "
      f"excess kurtosis {kurt - 3:+.1f}  worst day {min(rets):+.2%}")

EQ0 = 1000.0
PIP = 0.0001

# ---------------------------------------------------------------- 1. sizing
print("\n" + "=" * 78)
print("1. SIZING A $1,000 ACCOUNT  (standard lot = $10/pip, 0.01 lot = $0.10/pip)")
print("=" * 78)
print("  risk%   risk$  |  stop 15p   stop 30p   stop 60p   (lots)")
for rp in (0.25, 0.5, 1.0, 2.0):
    risk = EQ0 * rp / 100
    cells = "".join(f"{risk / (s * 10):>9.3f}   " for s in (15, 30, 60))
    print(f"  {rp:>4.2f}%  ${risk:>5.0f}  |{cells}")
print("\n  -> 0.5-1% risk means 0.01-0.03 lots on a 30-pip stop. Brokers allow it,")
print("     so lot-size minimums are NOT what kills small accounts. Cost is.")

# ---------------------------------------------------------------- 2. cost
print("\n" + "=" * 78)
print("2. THE COST WALL  (1% risk, 30-pip stop -> notional $3,333; 1 pip = $0.33)")
print("=" * 78)
notional = EQ0 * 0.01 / (30 * PIP)
pipcost = notional * PIP
comm = notional * 0.000035 * 2
print(f"  notional ${notional:,.0f}   spread cost/trade ${pipcost:.2f}   "
      f"commission/trade ${comm:.2f}   total ${pipcost+comm:.2f}")
print("\n  trades/day  trades/yr | cost/yr    as % of account")
for tpd in (0.2, 1, 2, 3, 5, 10):
    n = tpd * 252
    c = n * (pipcost + comm)
    print(f"  {tpd:>10.1f}  {n:>9.0f} | ${c:>8.0f}      {c/EQ0:>7.1%}")
print("\n  -> 3 trades/day burns ~43% of the account each year in friction alone.")
print("     2 trades/day burns ~29%. Weekly trading burns ~3%.")
print("     THIS is why frequency, not skill, decides most retail outcomes.")
be = 31 / 60
print(f"\n  breakeven win rate (30p stop / 30p target, 1p spread): {be:.2%}")

# ---------------------------------------------------------------- 3. survival
print("\n" + "=" * 78)
print("3. SURVIVAL  (1R = money risked; 2% of trades take a 2.5R tail loss)")
print("=" * 78)


def sim(risk_pct, p=0.50, tail=0.02, tailR=2.5, trades=250, years=3,
        paths=20000, seed=7):
    random.seed(seed)
    f = risk_pct / 100
    d20 = d50 = gone = 0
    dds, finals = [], []
    for _ in range(paths):
        eq, peak, mdd = EQ0, EQ0, 0.0
        dead = False
        for _ in range(trades * years):
            if random.random() < tail:
                eq -= eq * f * tailR
            elif random.random() < p:
                eq += eq * f
            else:
                eq -= eq * f
            if eq <= EQ0 * 0.02:
                dead = True
                eq = max(eq, 0)
                break
            peak = max(peak, eq)
            mdd = min(mdd, eq / peak - 1)
        dds.append(mdd)
        finals.append(eq)
        d20 += mdd <= -0.20
        d50 += mdd <= -0.50
        gone += dead
    dds.sort()
    finals.sort()
    return (d20 / paths, d50 / paths, gone / paths, dds[paths // 2],
            finals[paths // 2], finals[int(paths * 0.05)])


def ev_per_trade(p, tail=0.02, tailR=2.5):
    """must match the sim: the tail branch REPLACES a normal trade"""
    return (1 - tail) * (2 * p - 1) - tail * tailR


for p, lbl in ((0.50, "no edge  (p=50%)"), (0.53, "real edge (p=53%)")):
    gross = 2 * p - 1
    net = ev_per_trade(p)
    print(f"\n  {lbl}: gross edge {gross:+.3f}R/trade, after 2% x 2.5R tails "
          f"{net:+.4f}R/trade")
    print(f"    over 250 trades/yr at 0.5% risk that is {net*250*0.005:+.1%}/yr expected")
    print("   risk | P(DD>20%) | P(DD>50%) | wiped | med maxDD |  median $3y |  5th pct")
    print("   -----|-----------|-----------|-------|-----------|----------|----------")
    for rp in (0.25, 0.5, 1.0, 2.0, 5.0):
        a, b, c, m, med, p5 = sim(rp, p=p)
        print(f"  {rp:>5.2f}% |  {a:7.1%}  |  {b:7.1%}  | {c:6.1%} |   {m:7.1%}  |"
              f" ${med:>7,.0f} | ${p5:>7,.0f}")

# ---------------------------------------------------------------- 4. streaks
print("\n" + "=" * 78)
print("4. WHAT A NORMAL BAD RUN LOOKS LIKE (50% win rate)")
print("=" * 78)
random.seed(3)
runs, cur, mx = [], 0, 0
for _ in range(20000):
    if random.random() < 0.5:
        cur += 1
        mx = max(mx, cur)
    else:
        runs.append(cur)
        cur = 0
runs.sort()
print(f"  in 20,000 trades: longest losing streak {mx}")
print(f"  streaks >=5: {sum(1 for r in runs if r >= 5)}, "
      f">=8: {sum(1 for r in runs if r >= 8)}, >=10: {sum(1 for r in runs if r >= 10)}")
for k in (5, 8, 10, 15):
    print(f"  {k} losses in a row at 1% risk = {1-0.99**k:5.2%} of equity, "
          f"at 2% = {1-0.98**k:5.2%}, at 5% = {1-0.95**k:5.2%}")
