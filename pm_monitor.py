"""
Polymarket BTC 5-minute streak monitor.

Watches BTC 5m candles, detects a run of N same-colour candles (default 7), and
shows the LIVE order book of the Polymarket "Bitcoin Up or Down" window you would
actually trade - real bid/ask, the taker fee, and the breakeven hit rate.

    python pm_monitor.py               # live view, refresh every 5s
    python pm_monitor.py --once        # one snapshot
    python pm_monitor.py --once --json # machine-readable
    python pm_monitor.py --selftest    # no network: verify logic + render
    python pm_monitor.py --source pm   # build the streak from official settlements

No API keys, no dependencies, read-only: it never places an order.

Data sources (all public):
  candles : Binance klines
  windows : Gamma API  events?slug=btc-updown-5m-<unix>
  book    : CLOB API   /book?token_id=<token>
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
BINANCE = "https://api.binance.com/api/v3/klines"
UA = {"User-Agent": "Mozilla/5.0 (pm-monitor)", "Accept": "application/json"}

WINDOW = 300              # 5 minutes
FEE_RATE = 0.07           # Polymarket crypto taker fee: C * 0.07 * p * (1-p)
SHARES = 100              # reference size for fee / breakeven

# Measured on 91,036 settled windows (see pm_streak_test.py).
EDGE_POOLED = (0.538, 0.542)   # all regimes, n=642 seven-runs
EDGE_CURRENT = 0.5126          # 60s-TWAP regime only, n=199, +/-7%
TWAP_SINCE = "2026-08-14"


class FetchError(Exception):
    """Network/API failure with a short, printable reason."""


# --------------------------------------------------------------------- http
def http_json(url, tries=3, timeout=15):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as exc:                      # noqa: BLE001 - any transport error
            last = exc
            if attempt < tries - 1:
                time.sleep(0.4 * (attempt + 1))
    raise FetchError(f"{type(last).__name__}: {last}")


def try_json(url, **kw):
    """Never raises: returns (data, error_string)."""
    try:
        return http_json(url, **kw), None
    except FetchError as exc:
        return None, str(exc)


# --------------------------------------------------------------------- data
def binance_candles(count):
    """Last `count` candles (the newest may still be forming)."""
    raw = http_json(f"{BINANCE}?symbol=BTCUSDT&interval=5m&limit={count}")
    out = []
    for k in raw:
        o, c = float(k[1]), float(k[4])
        out.append({"t": int(k[0]) // 1000, "open": o, "close": c,
                    "colour": "U" if c >= o else "D"})
    return out


_MARKET_CACHE = {}


def window_meta(ts):
    """Gamma metadata for one window, cached per window (only on success)."""
    if ts in _MARKET_CACHE:
        return _MARKET_CACHE[ts]
    data, _err = try_json(f"{GAMMA}/events?slug=btc-updown-5m-{ts}", tries=2)
    if not data:
        return None
    m = (data[0].get("markets") or [{}])[0]
    toks = m.get("clobTokenIds")
    toks = json.loads(toks) if isinstance(toks, str) else (toks or [])
    meta = {
        "question": m.get("question") or data[0].get("title") or "?",
        "volume": float(m.get("volume") or 0),
        "liquidity": float(m.get("liquidity") or 0),
        "tokens": list(toks),
    }
    _MARKET_CACHE[ts] = meta
    return meta


def order_book(token):
    """Best bid/ask plus depth. Never raises."""
    data, err = try_json(f"{CLOB}/book?token_id={token}")
    if data is None:
        return {"bid": None, "ask": None, "err": err}
    bids = [(float(x["price"]), float(x["size"])) for x in (data.get("bids") or []) if x.get("size")]
    asks = [(float(x["price"]), float(x["size"])) for x in (data.get("asks") or []) if x.get("size")]
    best_bid = max(bids, key=lambda x: x[0]) if bids else None
    best_ask = min(asks, key=lambda x: x[0]) if asks else None
    return {"bid": best_bid, "ask": best_ask, "n_bid": len(bids), "n_ask": len(asks),
            "err": None}


def official_colours(start_ts, count):
    """Settled Polymarket outcomes for `count` windows ending at start_ts."""
    out = []
    for i in range(count):
        ts = start_ts - i * WINDOW
        data, _err = try_json(f"{GAMMA}/events?slug=btc-updown-5m-{ts}", tries=2)
        if not data:
            continue
        prices = (data[0].get("markets") or [{}])[0].get("outcomePrices")
        prices = json.loads(prices) if isinstance(prices, str) else prices
        if not prices or len(prices) < 2:
            continue
        up, down = float(prices[0]), float(prices[1])
        if up > 0.99:
            out.append((ts, "U"))
        elif down > 0.99:
            out.append((ts, "D"))
    return sorted(out)


# ------------------------------------------------------------ pure logic
def streak_length(colours):
    """How many of the same colour at the tail of the list."""
    if not colours:
        return 0
    k = 1
    while k < len(colours) and colours[-1 - k] == colours[-1]:
        k += 1
    return k


def quote(level, shares=SHARES):
    """Turn an ask level into fee / cost / breakeven. Pure."""
    price = level[0]
    fee = shares * FEE_RATE * price * (1 - price)
    cost = shares * price + fee
    return {"price": price, "size": level[1], "fee": fee, "cost": cost,
            "breakeven": cost / shares, "payout": float(shares)}


def verdict(breakeven):
    """Compare a breakeven hit rate against the measured edge. Pure."""
    if breakeven <= EDGE_POOLED[0]:
        return "EDGE (pooled data)"
    if breakeven <= EDGE_POOLED[1]:
        return "MARGINAL"
    return "NO EDGE at this price"


# ------------------------------------------------------------------- state
def build_state(streak_len=7, source="binance"):
    """Collect everything the view needs. Never raises."""
    now = int(time.time())
    window = now // WINDOW * WINDOW
    st = {"now": now, "window_start": window, "seconds_left": WINDOW - (now - window),
          "source": source, "streak_len": streak_len, "errors": [],
          "colours": [], "last_close": None, "market": None, "quotes": {},
          "trigger": None}

    if source == "pm":
        pairs = official_colours(window - WINDOW, streak_len + 4)
        st["colours"] = [c for _ts, c in pairs]
    else:
        try:
            candles = binance_candles(streak_len + 5)
        except FetchError as exc:
            st["errors"].append(f"candles unavailable - {exc}")
        else:
            closed = [c for c in candles if c["t"] + WINDOW <= now]
            st["colours"] = [c["colour"] for c in closed]
            if closed:
                st["last_close"] = closed[-1]["close"]

    st["streak"] = streak_length(st["colours"])
    st["triggered"] = st["streak"] >= streak_len

    meta = window_meta(window)
    if not meta:
        st["errors"].append("market not created yet for this window")
        return st
    st["market"] = {k: meta[k] for k in ("question", "volume", "liquidity")}

    for side, token in zip(("Up", "Down"), meta["tokens"][:2]):
        bk = order_book(token)
        entry = {"bid": None, "ask": None, "err": bk["err"]}
        if bk["bid"]:
            entry["bid"] = bk["bid"][0]
            entry["bid_size"] = bk["bid"][1]
        if bk["ask"]:
            entry["ask"] = bk["ask"][0]
            entry["ask_size"] = bk["ask"][1]
            q = quote(bk["ask"])
            entry.update({"fee": q["fee"], "cost": q["cost"],
                          "breakeven": q["breakeven"]})
        if bk["bid"] and bk["ask"]:
            entry["mid"] = (bk["bid"][0] + bk["ask"][0]) / 2
            entry["spread"] = bk["ask"][0] - bk["bid"][0]
        st["quotes"][side] = entry

    if st["triggered"] and st["colours"]:
        fade = "Down" if st["colours"][-1] == "U" else "Up"
        q = st["quotes"].get(fade) or {}
        if q.get("ask") is not None:
            st["trigger"] = {"fade": fade, "ask": q["ask"], "cost": q["cost"],
                             "breakeven": q["breakeven"],
                             "verdict": verdict(q["breakeven"])}
        else:
            st["trigger"] = {"fade": fade, "unavailable": True}
    return st


# ------------------------------------------------------------------ render
def clock(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%H:%M")


def render(st):
    rule = "=" * 68
    lines = [rule,
             f" Polymarket  ·  BTC 5m Up/Down monitor      "
             f"{dt.datetime.fromtimestamp(st['now'], dt.timezone.utc):%Y-%m-%d %H:%M:%S} UTC",
             f" window {clock(st['window_start'])}-{clock(st['window_start'] + WINDOW)} UTC"
             f"   ·   source: {'official settlements' if st['source'] == 'pm' else 'Binance candles'}",
             rule]

    colour = {"U": "GREEN / UP", "D": "RED / DOWN"}.get(
        st["colours"][-1] if st["colours"] else "", "unknown")
    close = f"   close ${st['last_close']:,.2f}" if st["last_close"] else ""
    mark = f"   << TRIGGER {st['streak_len']} >>" if st["triggered"] else ""
    lines += [f" candle      {colour}{close}",
              f" streak      {st['streak']} in a row{mark}",
              f" last 8      {' '.join(st['colours'][-8:]) or '-'}",
              f" window      {st['window_start']}  ·  {st['seconds_left']}s left"]

    if st["market"]:
        lines += ["",
                  f" market      {st['market']['question']}",
                  f" volume      ${st['market']['volume']:,.0f}"
                  f"   liquidity ${st['market']['liquidity']:,.0f}",
                  "",
                  "               BID      ASK    SPREAD     MID   FEE/100   BREAKEVEN"]
        for side in ("Up", "Down"):
            q = st["quotes"].get(side) or {}
            if q.get("bid") is None or q.get("ask") is None:
                why = q.get("err") or "book empty (orders pulled near close?)"
                lines.append(f"   {side:<5}      -        -      -        -      -          ({why})")
                continue
            lines.append(f"   {side:<5}    {q['bid']:6.3f}   {q['ask']:6.3f}   {q['spread']:5.3f}"
                         f"   {q['mid']:5.3f}   ${q['fee']:5.2f}     {q['breakeven']:6.2%}")

    if st["trigger"]:
        t = st["trigger"]
        lines.append("")
        if t.get("unavailable"):
            lines.append(f" TRIGGER     fade the streak -> '{t['fade']}', but no ask is quoted")
        else:
            lines += [f" TRIGGER     fade the streak: buy '{t['fade']}' at {t['ask']:.3f}",
                      f" {SHARES} shares cost ${t['cost']:.2f} · pays ${SHARES:.0f} · "
                      f"breakeven {t['breakeven']:.2%}",
                      f" measured edge {EDGE_POOLED[0]:.1%}-{EDGE_POOLED[1]:.1%}  ->  {t['verdict']}",
                      f" caveat: under the 60s-TWAP rule (since {TWAP_SINCE}) the edge is",
                      f"         {EDGE_CURRENT:.1%} +/-7% (n=199) - unproven at this price."]

    if st["errors"]:
        lines.append("")
        for e in st["errors"]:
            lines.append(f" ! {e}")

    lines.append("")
    lines.append(" note: Binance colour matched ~86% of settlements since the 60s-TWAP rule;")
    lines.append("       use --source pm to build the streak from the official outcomes.")
    return "\n".join(lines)


def as_json(st):
    clean = json.loads(json.dumps(st, default=str))
    for q in clean["quotes"].values():
        for k in ("fee", "cost", "breakeven", "mid", "spread"):
            if isinstance(q.get(k), float):
                q[k] = round(q[k], 6)
    return json.dumps(clean, indent=2)


# ---------------------------------------------------------------- selftest
def selftest():
    checks = []

    def ok(name, cond):
        checks.append((name, bool(cond)))

    ok("streak_length 3 ups", streak_length(list("UDUUU")) == 3)
    ok("streak_length single", streak_length(list("UD")) == 1)
    ok("streak_length empty", streak_length([]) == 0)
    q = quote((0.50, 500))
    ok("fee at 50c = 1.75", abs(q["fee"] - 1.75) < 1e-9)
    ok("breakeven at 50c = 51.75%", abs(q["breakeven"] - 0.5175) < 1e-9)
    q2 = quote((0.53, 500))
    ok("breakeven at 53c = 54.74%", abs(q2["breakeven"] - 0.547437) < 1e-6)
    ok("verdict edge at 50c", verdict(q["breakeven"]).startswith("EDGE"))
    ok("verdict no edge at 55c", verdict(quote((0.55, 1))["breakeven"]).startswith("NO EDGE"))

    fake = {"now": 1794749600, "window_start": 1794749400, "seconds_left": 184,
            "source": "binance", "streak_len": 7, "errors": [], "streak": 7,
            "triggered": True, "last_close": 65684.01,
            "colours": list("DUUUUUUU"),
            "market": {"question": "Bitcoin Up or Down - demo", "volume": 20400.0,
                       "liquidity": 18639.0},
            "quotes": {"Up": {"bid": 0.51, "ask": 0.52, "spread": 0.01, "mid": 0.515,
                              "fee": 1.7472, "cost": 53.7472, "breakeven": 0.537472,
                              "err": None},
                       "Down": {"bid": 0.47, "ask": 0.48, "spread": 0.01, "mid": 0.475,
                                "fee": 1.747, "cost": 49.747, "breakeven": 0.49747,
                                "err": None}},
            "trigger": {"fade": "Down", "ask": 0.48, "cost": 49.747,
                        "breakeven": 0.49747, "verdict": "EDGE (pooled data)"}}
    text = render(fake)
    ok("render has trigger block", "TRIGGER     fade the streak" in text)
    ok("render picks the Down ask", "buy 'Down' at 0.480" in text)
    ok("json serialises", json.loads(as_json(fake))["streak"] == 7)

    width = max(len(n) for n, _ in checks)
    for name, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<{width}}")
    bad = sum(1 for _n, p in checks if not p)
    print(f"\n  {len(checks) - bad}/{len(checks)} passed")
    print("\n  sample render (canned data, no network):\n")
    print(render(fake))
    return 1 if bad else 0


# -------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="Polymarket BTC 5m streak monitor")
    ap.add_argument("--once", action="store_true", help="print one snapshot and exit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true", help="offline logic + render check")
    ap.add_argument("--streak", type=int, default=7,
                    help="candles in a row (default 7; 1 = always fires, for demos)")
    ap.add_argument("--source", choices=("binance", "pm"), default="binance",
                    help="build the streak from Binance candles or official settlements")
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between refreshes")
    args = ap.parse_args(argv)

    if args.streak < 1:
        print("--streak must be >= 1", file=sys.stderr)
        return 2
    if args.selftest:
        return selftest()

    tty = sys.stdout.isatty()
    try:
        while True:
            state = build_state(args.streak, args.source)
            if not args.once and tty:
                sys.stdout.write("\033[2J\033[H")
            print(as_json(state) if args.json else render(state), flush=True)
            if args.once:
                return 1 if state["errors"] else 0
            time.sleep(max(args.interval, 1.0))
    except KeyboardInterrupt:
        print("\nstopped.", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
