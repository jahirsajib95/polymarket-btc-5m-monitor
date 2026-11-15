"""
Test the '7 candles then reversal within 4-5' claim on POLYMARKET's own
resolved outcomes (Chainlink TWAP), not on Binance candle colours.

Also measures: how often does the Binance candle colour even agree with the
official settlement? That is the size of the mismatch we warned about.
"""
import json
import datetime as dt

from common import maximal_runs, segments, wilson

OUT = "pm_btc5m.json"
BIN = "btcusdt_5m.json"


def load_pm():
    with open(OUT) as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def load_bin():
    """Optional input: only used for the chart-vs-settlement comparison."""
    try:
        with open(BIN) as f:
            rows = json.load(f)
    except FileNotFoundError:
        print(f"note: {BIN} not found - skipping the chart-vs-settlement section.")
        print("      run streak_report.py once to download it.\n")
        return {}
    d = {}
    for r in rows:
        ot = int(r[0]) // 1000
        op, cl = float(r[1]), float(r[4])
        d[ot] = "U" if cl >= op else "D"
    return d


def test(lab, label, L0=7):
    """lab: list of 'U'/'D' (contiguous). Print the #8/#9 analysis."""
    rs = maximal_runs(lab)
    ev = [(c, L, s) for c, L, s in rs if L >= L0 and s + 8 < len(lab)]
    N = len(ev)
    if not N:
        print(f"  {label}: no events")
        return None
    a = [1 if lab[s + L0] != c else 0 for c, L, s in ev]
    b = [1 if lab[s + L0 + 1] != c else 0 for c, L, s in ev]
    bw = sum(1 for x, y in zip(a, b) if x and y)
    ow = sum(1 for x, y in zip(a, b) if x != y)
    bl = N - bw - ow
    fail4 = sum(1 for c, L, s in ev if L - L0 >= 4)
    fail5 = sum(1 for c, L, s in ev if L - L0 >= 5)
    lo8, hi8 = wilson(sum(a), N)
    lo9, hi9 = wilson(sum(b), N)
    print(f"  {label}")
    print(f"    candles={len(lab)}  runs>={L0}: {N}  longest run={max(L for _, L, _ in rs)}")
    print(f"    #8 win  {sum(a)/N:6.2%}  (95% CI {lo8:.2%}-{hi8:.2%})   n={N}")
    print(f"    #9 win  {sum(b)/N:6.2%}  (95% CI {lo9:.2%}-{hi9:.2%})")
    print(f"    both win {bw/N:5.2%} | exactly one {ow/N:5.2%} | both lose {bl/N:5.2%}")
    print(f"    no opposite within 4: {fail4}/{N} = {fail4/N:.2%}"
          f"   within 5: {fail5}/{N} = {fail5/N:.2%}")
    return {"N": N, "a": sum(a), "b": sum(b), "bw": bw, "fail4": fail4, "fail5": fail5}


pm = load_pm()
bin_ = load_bin()
ks = sorted(pm)
print(f"Polymarket resolved windows: {len(ks)}")
print(f"  {dt.datetime.fromtimestamp(ks[0], dt.timezone.utc):%Y-%m-%d %H:%M}"
      f" -> {dt.datetime.fromtimestamp(ks[-1], dt.timezone.utc):%Y-%m-%d %H:%M} UTC")
seg = segments(ks)
print(f"  contiguous segments: {len(seg)}  "
      f"(longest {max(len(s) for s in seg)} windows = {max(len(s) for s in seg)/288:.1f} days)")

# ---------------- agreement: Polymarket vs Binance colour -----------------
both = [t for t in ks if t in bin_]
if both:
    agree = sum(1 for t in both if pm[t] == bin_[t])
    lo, hi = wilson(agree, len(both))
    print(f"\nAgreement PM settlement vs Binance candle colour: {agree}/{len(both)} = "
          f"{agree/len(both):.2%} (95% CI {lo:.2%}-{hi:.2%})")
    print(f"  -> they disagree on {len(both)-agree} windows, "
          f"{1-agree/len(both):.2%} of the time")
    print(f"  PM up-share {sum(1 for v in pm.values() if v=='U')/len(pm):.2%} | "
          f"Binance up-share {sum(1 for v in bin_.values() if v=='U')/len(bin_):.2%}")
else:
    print("\nAgreement check skipped - no Binance cache to compare against.")

# agreement by month
print("\n  by month (agreement):")
bym = {}
for t in both:
    m = dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m")
    d = bym.setdefault(m, [0, 0])
    d[0] += 1
    d[1] += pm[t] == bin_[t]
for m in sorted(bym):
    n, k2 = bym[m]
    print(f"    {m}: {k2/n:6.2%}  (n={n})")

# ---------------- the streak test ----------------------------------------
print("\n" + "=" * 70)
print("7-STREAK TEST")
print("=" * 70)

print("\n[1] on POLYMARKET final outcomes (the settlements that matter)")
# build contiguous label lists across all segments
pm_lab_all = []
for s in seg:
    pm_lab_all.extend(pm[t] for t in s)
res_pm = test(pm_lab_all, "ALL Polymarket windows", 7)

print("\n[2] same windows, using BINANCE candle colours")
bin_lab_all = []
for s in seg:
    for t in s:
        if t in bin_:
            bin_lab_all.append(bin_[t])
res_bin = test(bin_lab_all, "Binance colour on the same windows", 7)

print("\n[3] by settlement regime (PM)")
SINGLE_END = int(dt.datetime(2026, 8, 7, tzinfo=dt.timezone.utc).timestamp())
TWAP30_END = int(dt.datetime(2026, 8, 14, tzinfo=dt.timezone.utc).timestamp())
for name, lo_t, hi_t in (("single print (<2026-08-07)", 0, SINGLE_END),
                         ("30s TWAP (08-07..08-14)", SINGLE_END, TWAP30_END),
                         ("60s TWAP (>=2026-08-14)", TWAP30_END, 10**12)):
    lab = []
    for s in seg:
        for t in s:
            if lo_t <= t < hi_t:
                lab.append(pm[t])
    if len(lab) > 1000:
        print()
        test(lab, name, 7)

# ---------------- fee-adjusted price reality -----------------------------
print("\n" + "=" * 70)
print("what the numbers mean at the ask")
print("=" * 70)
if res_pm:
    for p in (0.50, 0.51, 0.52, 0.53):
        fee = 0.07 * p * (1 - p)
        be = p + fee
        print(f"  fill {p:.2f} -> breakeven hit rate {be:.2%}  "
              f"| PM #8 = {res_pm['a']/res_pm['N']:.2%}  "
              f"({'EDGE' if res_pm['a']/res_pm['N'] > be else 'NO EDGE'})")
