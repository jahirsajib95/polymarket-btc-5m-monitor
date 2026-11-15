import json, time, urllib.request, statistics

# --- 1. how "thin" are 5m candles (colour can flip on a few dollars) ---
with open("btcusdt_5m.json") as f:
    rows = json.load(f)
rows = [r for r in rows if r[1]]
moves = [abs(r[4] - r[1]) for r in rows]
pct = sorted(abs(r[4] / r[1] - 1) * 100 for r in rows)
n = len(pct)
print(f"5m candles: {n}")
print(f"median |close-open|: ${statistics.median(moves):.2f}  ({statistics.median(pct):.3f}%)")
for th in (1, 5, 10, 20, 50):
    c = sum(1 for m in moves if m < th)
    print(f"  |close-open| < ${th}: {c} = {c/n:.1%} of candles")
print(f"  10th pct |move| ${sorted(moves)[n//10]:.2f}, 90th ${sorted(moves)[9*n//10]:.2f}")

# --- 2. live Polymarket 5m BTC market rules ---
s = int(time.time()) // 300 * 300
for slug in (f"btc-updown-5m-{s}", f"btc-updown-5m-{s-300}"):
    try:
        req = urllib.request.Request(
            f"https://gamma-api.polymarket.com/events?slug={slug}",
            headers={"User-Agent": "research/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        if not d:
            print(f"\n[{slug}] not found")
            continue
        e = d[0]
        print(f"\n[{slug}] {e.get('title')}")
        print(f"  closed={e.get('closed')}  volume={e.get('volume')}  liquidity={e.get('liquidity')}")
        m = (e.get("markets") or [{}])[0]
        print(f"  question: {m.get('question')}")
        print(f"  outcomes={m.get('outcomes')} prices={m.get('outcomePrices')}")
        print(f"  endDate={m.get('endDate')}")
        desc = (m.get("description") or "").replace("\n", " ")
        print(f"  rules: {desc[:700]}")
    except Exception as ex:
        print(f"\n[{slug}] error: {ex}")
