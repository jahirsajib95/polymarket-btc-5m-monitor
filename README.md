# Polymarket BTC 5-Minute Streak Monitor

A read-only monitor for Polymarket's **"Bitcoin Up or Down"** 5-minute markets.

It detects a run of N same-colour BTC 5m candles (default: 7) and then shows the
**live order book of the window you would actually trade** — real bid/ask, depth,
the taker fee, and the breakeven hit rate. The point is not to predict anything;
it is to show whether a streak means anything *at the price you can actually get*.

No API keys. No dependencies. Single file. **It never places an order.**

---

## Why this exists

A widely repeated claim is that after 7 same-colour candles an opposite candle
*must* arrive within the next 4–5. It is false, and the price is where it dies.
Measured on **91,036 settled Polymarket windows** (2025-12-18 → 2026-11-15, from
`pm_streak_test.py`, outcomes taken from Chainlink TWAP settlement — not from a
chart):

| | Binance candles | **Polymarket settlements** |
|---|---|---|
| 7-in-a-row events | 610 | **642** |
| next candle reverses | 56.39% | **54.05%** (95% CI 50.18–57.87) |
| **no reversal within 4 candles** | 5.25% | **6.07%** |
| **no reversal within 5 candles** | 2.46% | **3.43%** |
| longest run | 15 | 15 |

Two findings shape what this tool says:

1. **The "must reverse" rule fails ~1 time in 17** — and roughly twice as often on
   real settlements as on a chart.
2. **Your chart and the settlement disagree more than you think.** Since the
   60-second TWAP rule (2026-08-14) the Binance candle colour matched only
   **86.2%** of settlements (Oct 2026). Before that rule it was ~97%.

So the monitor prints both numbers it needs to be honest: the breakeven price and
the measured edge, plus the caveat that under the current rule the edge is
**51.3% ± 7% (n=199)** — i.e. unproven.

---

## See it work with no network at all

```bash
python pm_monitor.py --selftest
```

Runs the pure logic (streak counting, fee/breakeven maths, verdict, JSON) against
known values and renders a canned snapshot. Exit code 0 = all checks pass.

---

## Run it

```bash
python pm_monitor.py                # live view, refreshes every 5s
python pm_monitor.py --once         # one snapshot
python pm_monitor.py --once --json  # machine-readable
```

Requirements: Python 3.9+, standard library only.

This is the renderer's real output, produced by `--selftest` from canned data
(no network needed) — a triggered window, exactly as you would see it live:

```
====================================================================
 Polymarket  ·  BTC 5m Up/Down monitor      2026-11-15 13:33:20 UTC
 window 13:30-13:35 UTC   ·   source: Binance candles
====================================================================
 candle      GREEN / UP   close $65,684.01
 streak      7 in a row   << TRIGGER 7 >>
 last 8      D U U U U U U U
 window      1794749400  ·  184s left

 market      Bitcoin Up or Down - demo
 volume      $20,400   liquidity $18,639

               BID      ASK    SPREAD     MID   FEE/100   BREAKEVEN
   Up        0.510    0.520   0.010   0.515   $ 1.75     53.75%
   Down      0.470    0.480   0.010   0.475   $ 1.75     49.75%

 TRIGGER     fade the streak: buy 'Down' at 0.480
 100 shares cost $49.75 · pays $100 · breakeven 49.75%
 measured edge 53.8%-54.2%  ->  EDGE (pooled data)
 caveat: under the 60s-TWAP rule (since 2026-08-14) the edge is
         51.3% +/-7% (n=199) - unproven at this price.

 note: Binance colour matched ~86% of settlements since the 60s-TWAP rule;
       use --source pm to build the streak from the official outcomes.
```

The same conditions minutes later, at an ask of 0.500, would print
`breakeven 51.75%` and `NO EDGE at this price` — the price decides, not the streak.

---

## Options

| Flag | Default | Meaning |
|---|---|---|
| `--once` | off | print one snapshot and exit |
| `--json` | off | machine-readable state instead of the view |
| `--selftest` | off | offline logic + render checks |
| `--streak N` | 7 | candles in a row that count as a trigger |
| `--source binance\|pm` | binance | build the streak from charts, or from official settlements |
| `--interval S` | 5 | refresh seconds in live mode |

---

## Reliability

- **Never crashes on a bad response.** Every network call retries with backoff and
  returns an error string instead of raising; the view prints the reason
  (e.g. `candles unavailable - URLError: timed out`) and keeps running.
- **Per-window metadata cache** — the market lookup runs once per 5-minute window,
  not once per refresh, so a 5s loop does not hammer the API.
- **Empty books are explained**, not hidden: Polymarket pulls resting orders in the
  last seconds of a window, so the view says so instead of showing `-`.
- **Exit codes:** `0` ok, `1` snapshot completed with errors (`--once`), `2` bad flag.
- **Graceful stop** on Ctrl-C, no traceback.

---

## Limitations

- Public, undocumented endpoints (Gamma, CLOB, Binance). They can change.
- Read-only: no fills, no slippage, no 150 ms taker delay modelling.
- `--source pm` costs one request per window (slow at high refresh rates).
- The edge shown is a *measurement from history*, not a forecast, and not advice.

---

## Files

| File | What it does |
|---|---|
| `pm_monitor.py` | **the monitor** — live streak + real bid/ask |
| `pm_streak_test.py` | the 91k-window test behind every number quoted above |
| `fetch_pm_history.py` | downloads the settled-window history (`pm_btc5m.json`) |
| `common.py` | shared helpers (Wilson CI, run detection, segments) |
| `streak_report.py` | BTC candle statistics across 5m / 15m / 1h |
| `bet_8_9.py` | per-event P&L for betting candle #8 / #9 |
| `eighty_percent.py` | what a high win rate actually costs |
| `btc_forecast_power.py` | how little 4.87 years says about direction |
| `fx_test.py`, `fx_test2.py`, `fx_1000_plan.py` | the FX momentum / sizing work |
| `extra_checks.py` | candle thinness + live market rules check |

Data files (`btcusdt_*.json`, `pm_btc5m.json`, `fx_daily.json`) are caches; scripts
re-download when stale.
