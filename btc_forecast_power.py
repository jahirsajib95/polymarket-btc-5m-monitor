"""
What can 4.87 years of BTC data actually tell us about the FUTURE direction?
Builds daily candles from the 5m cache and measures:
  1. where we are now (price, ATH, drawdown, trend)
  2. unconditional forward-return distribution by horizon
  3. how many INDEPENDENT observations those distributions rest on
  4. whether the usual predictors (drawdown, 200d MA, momentum) work
"""
import json, math, statistics
import datetime as dt

UTC = dt.timezone.utc
with open("btcusdt_5m.json") as f:
    rows = json.load(f)
rows.sort(key=lambda r: r[0])

days = {}
order = []
for r in rows:
    d = dt.datetime.fromtimestamp(int(r[0]) / 1000, UTC).date()
    o, h, l, c = float(r[1]), float(r[2]), float(r[3]), float(r[4])
    if d not in days:
        days[d] = [o, h, l, c]
        order.append(d)
    else:
        x = days[d]
        x[1] = max(x[1], h)
        x[2] = min(x[2], l)
        x[3] = c

D = [days[d] for d in order]
dates = order
close = [x[3] for x in D]
n = len(close)
print(f"daily candles: {n}   {dates[0]} -> {dates[-1]}   ({n/365.25:.2f} years)")
px = close[-1]
ath = max(x[1] for x in D)
print(f"last close ${px:,.0f}   sample high (intraday) ${ath:,.0f}   "
      f"drawdown from it {(px/ath-1)*100:+.1f}%")
print(f"total return over sample {(close[-1]/close[0]-1)*100:+.1f}%   "
      f"CAGR {((close[-1]/close[0])**(365.25/n)-1)*100:+.1f}%")

# realised vol / drawdown profile
rets = [close[i+1]/close[i]-1 for i in range(n-1)]
dvol = statistics.pstdev(rets)*math.sqrt(365)
peak, mdd = 0, 0
for c in close:
    peak = max(peak, c)
    mdd = min(mdd, c/peak-1)
print(f"annualised vol {dvol:.1%}   max drawdown in sample {mdd:.1%}")
sm = [sum(close[i-200:i])/200 for i in range(200, n+1)]
print(f"200d SMA ${sm[-1]:,.0f}   price is {(px/sm[-1]-1)*100:+.1f}% vs it"
      f"   ({(px > sm[-1]) and 'ABOVE' or 'BELOW'})")
up_days = sum(1 for r in rets if r > 0)
print(f"up days {up_days}/{len(rets)} = {up_days/len(rets):.2%}\n")

# ---------- 2. forward returns ----------
print("=" * 74)
print("1. FORWARD RETURNS: what happened after every day in the sample")
print("=" * 74)
print(" horizon |  n_days | P(up)  | median |   5th pct |  95th pct | effective_n")
for h, name in ((1, "1 day"), (7, "1 week"), (30, "1 month"), (90, "3 months"),
                (180, "6 months"), (365, "1 year")):
    fwd = [close[i+h]/close[i]-1 for i in range(n-h)]
    ups = sum(1 for x in fwd if x > 0)
    fwd_s = sorted(fwd)
    eff = n/h
    print(f" {name:<8} | {len(fwd):>6} | {ups/len(fwd):5.1%} | {statistics.median(fwd):+6.1%} "
          f"| {fwd_s[len(fwd)//20]:+8.1%} | {fwd_s[19*len(fwd)//20]:+8.1%} | {eff:>10.1f}")

print("\n The last column is the one that matters: overlapping windows are NOT")
print(" independent samples. At a 1-year horizon these 4.87 years contain")
print(" ~4.87 independent observations. Any 'cycle' is fitted to ~4 points.\n")

# ---------- 3. statistical power on the drift ----------
print("=" * 74)
print("2. HOW WELL DO WE EVEN KNOW THE DRIFT? (calendar years)")
print("=" * 74)
by_year = {}
for i in range(1, n):
    y = dates[i].year
    by_year.setdefault(y, [close[i-1], close[i]])[1] = close[i]
yrs = []
for y in sorted(by_year):
    o, c = by_year[y]
    r = c/o-1
    yrs.append(r)
    print(f"  {y}: {r:+7.1%}" + ("   (partial)" if y == dates[-1].year else ""))
mu = statistics.mean(yrs)
sd = statistics.pstdev(yrs)
se = sd/math.sqrt(len(yrs))
geo = math.prod(1 + y for y in yrs) ** (1 / len(yrs)) - 1
print(f"\n  arithmetic mean {mu:+.1%}  vs  geometric (what you actually earn) {geo:+.1%}")
print(f"  sd {sd:.1%}, n={len(yrs)}")
print(f"  95% CI on the 'expected' annual return: {mu-1.96*se:+.1%} to {mu+1.96*se:+.1%}")
print(f"  a 1-sigma band around next year's return is roughly {mu-sd:+.0%} to {mu+sd:+.0%}")

# ---------- 4. do the classic predictors work? ----------
print("\n" + "=" * 74)
print("3. DO THE USUAL PREDICTORS ACTUALLY PREDICT? (30-day forward)")
print("=" * 74)


def bucket_report(name, buckets, h=30):
    print(f"\n  {name}  ->  forward {h}d")
    for label, idxs in buckets:
        f = [close[i+h]/close[i]-1 for i in idxs if i+h < n]
        if len(f) < 20:
            print(f"    {label:<22} n={len(f):<5} (too few)")
            continue
        ups = sum(1 for x in f if x > 0)
        print(f"    {label:<22} n={len(f):<5} P(up)={ups/len(f):5.1%}  "
              f"median={statistics.median(f):+6.1%}  mean={statistics.mean(f):+6.1%}")


peak_series = []
p = 0
for c in close:
    p = max(p, c)
    peak_series.append(p)
dd = [close[i]/peak_series[i]-1 for i in range(n)]
bucket_report("drawdown from ATH", [
    ("at/near ATH (>-5%)", [i for i in range(n) if dd[i] > -0.05]),
    ("-5% to -15%", [i for i in range(n) if -0.15 < dd[i] <= -0.05]),
    ("-15% to -30%", [i for i in range(n) if -0.30 < dd[i] <= -0.15]),
    ("worse than -30%", [i for i in range(n) if dd[i] <= -0.30]),
])

sma200 = [None]*200 + [sum(close[i-200:i])/200 for i in range(200, n)]
bucket_report("trend vs 200d SMA", [
    ("price ABOVE 200d", [i for i in range(200, n) if close[i] > sma200[i]]),
    ("price BELOW 200d", [i for i in range(200, n) if close[i] < sma200[i]]),
])

mom30 = [None]*30 + [close[i]/close[i-30]-1 for i in range(30, n)]
bucket_report("past 30d momentum", [
    ("up > +10%", [i for i in range(30, n) if mom30[i] > 0.10]),
    ("-10% to +10%", [i for i in range(30, n) if -0.10 <= mom30[i] <= 0.10]),
    ("down < -10%", [i for i in range(30, n) if mom30[i] < -0.10]),
])

print("\n" + "=" * 74)
print("4. THE CURRENT STATE, FOR CONTEXT ONLY (not a forecast)")
print("=" * 74)
i = n-1
print(f"  price ${px:,.0f}   drawdown from ATH(close) {dd[i]:+.1%}   "
      f"vs 200d SMA {px/sma200[i]-1:+.1%}   30d momentum {mom30[i]:+.1%}")
last = [close[i-h] for h in (1, 7, 30, 90)]
print(f"  1d {(px/last[0]-1)*100:+.1f}%   1w {(px/last[1]-1)*100:+.1f}%   "
      f"1m {(px/last[2]-1)*100:+.1f}%   3m {(px/last[3]-1)*100:+.1f}%")
print(f"\n  distribution of the next 30 days, straight from the sample:")
fwd = [close[j+30]/close[j]-1 for j in range(n-30)]
fwd_s = sorted(fwd)
for q in (5, 25, 50, 75, 95):
    print(f"    {q:>2}th pct: {fwd_s[len(fwd)*q//100]:+7.1%}")
