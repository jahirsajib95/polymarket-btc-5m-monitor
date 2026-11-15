"""
Download every resolved BTC 5m Up/Down market from Polymarket (Gamma API).
These outcomes ARE the official Chainlink-TWAP settlement, so this is the
sequence the '7-candle' claim must be tested on.

Deep offsets return HTTP 422, so walk the series day by day with end_date_*.
"""
import json, os, sys, time, urllib.request, urllib.error
import datetime as dt
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (research)", "Accept": "application/json"}
G = "https://gamma-api.polymarket.com"
SERIES = 10684
OUT = "pm_btc5m.json"
PAGE = 100


def get(url, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (406, 429, 500, 502, 503, 504):
                time.sleep(0.5 * (t + 1))
                continue
            return None          # 422 on empty page etc.
        except Exception:
            if t == tries - 1:
                return None
            time.sleep(0.5 * (t + 1))
    return None


def page(d0, d1, off):
    u = (f"{G}/events/pagination?series_id={SERIES}&limit={PAGE}&offset={off}"
         f"&end_date_min={d0}&end_date_max={d1}")
    r = get(u)
    if not isinstance(r, dict):
        return []
    return r.get("data") or []


def parse(ev):
    slug = ev.get("slug") or ""
    if not slug.startswith("btc-updown-5m-"):
        return None
    try:
        ts = int(slug.rsplit("-", 1)[1])
    except ValueError:
        return None
    ms = ev.get("markets") or []
    if not ms:
        return None
    m = ms[0]
    op = m.get("outcomePrices")
    if isinstance(op, str):
        try:
            op = json.loads(op)
        except Exception:
            return None
    if not op or len(op) < 2:
        return None
    try:
        up, dn = float(op[0]), float(op[1])
    except (TypeError, ValueError):
        return None
    if up > 0.99 and dn < 0.01:
        return ts, "U"
    if dn > 0.99 and up < 0.01:
        return ts, "D"
    return None


# series span
head = get(f"{G}/events?series_id={SERIES}&limit=1&order=endDate&ascending=true") or []
tail = get(f"{G}/events?series_id={SERIES}&limit=1&order=endDate&ascending=false") or []
if not head or not tail:
    sys.exit("cannot read series bounds")
oldest = int(head[0]["slug"].rsplit("-", 1)[1])
newest = int(tail[0]["slug"].rsplit("-", 1)[1])
d_start = dt.datetime.fromtimestamp(oldest, dt.timezone.utc).date() - dt.timedelta(days=2)
d_end = dt.datetime.fromtimestamp(newest, dt.timezone.utc).date() + dt.timedelta(days=1)
print(f"series {oldest} -> {newest}; days {d_start} .. {d_end}")

days = []
d = d_start
while d <= d_end:
    n = d + dt.timedelta(days=1)
    days.append((f"{d}T00:00:00Z", f"{n}T00:00:00Z"))
    d = n

tasks = [(a, b, off) for (a, b) in days for off in (0, PAGE, 2 * PAGE, 3 * PAGE)]
print(f"{len(days)} days -> {len(tasks)} page requests, 8 threads")

have = {}
if os.path.exists(OUT):
    with open(OUT) as f:
        have = {int(k): v for k, v in json.load(f).items()}
    print(f"cache had {len(have)}")

done = 0
t0 = time.time()
fails = 0


def work(t):
    return page(*t)


with ThreadPoolExecutor(max_workers=8) as ex:
    for res in ex.map(work, tasks):
        if not res:
            fails += 1
        for ev in res:
            p = parse(ev)
            if p:
                have[p[0]] = p[1]
        done += 1
        if done % 200 == 0:
            print(f"  {done}/{len(tasks)} pages, {len(have)} windows, "
                  f"{time.time()-t0:.0f}s", flush=True)

with open(OUT, "w") as f:
    json.dump({str(k): v for k, v in sorted(have.items())}, f)

ks = sorted(have)
gaps = sum(1 for a, b in zip(ks, ks[1:]) if b - a != 300)
print(f"DONE {len(have)} windows in {time.time()-t0:.0f}s  empty-pages={fails}")
print(f"contiguous: {len(ks)-1-gaps}/{len(ks)-1} gaps={gaps}")
print(f"up={sum(1 for v in have.values() if v=='U')} "
      f"down={sum(1 for v in have.values() if v=='D')}")
print(f"range {dt.datetime.fromtimestamp(ks[0], dt.timezone.utc):%Y-%m-%d %H:%M}"
      f" -> {dt.datetime.fromtimestamp(ks[-1], dt.timezone.utc):%Y-%m-%d %H:%M}")
