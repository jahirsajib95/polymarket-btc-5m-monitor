# Data Pipeline & Monitoring Engineer

**I make external data reliable: fetch it, verify it, alert on it, and keep it running.**

Most "it works on my machine" scripts die quietly three weeks later. My work is the
opposite: pipelines with retries, validation and alerts, plus the measurements that
show whether the data can actually be trusted.

---

## See it without running anything

**A real live snapshot** — captured mid-window, unedited. Note that one side is
already at 93c: five minutes is a very short time, and the price knows it before
you do.

```
====================================================================
 Polymarket  ·  BTC 5m Up/Down monitor      2026-11-15 16:28:37 UTC
 window 16:25-16:30 UTC   ·   source: Binance candles
====================================================================
 candle      RED / DOWN   close $64,421.21
 streak      3 in a row
 last 8      U U D D U D D D
 window      1794759900  ·  83s left

 market      Bitcoin Up or Down - November 15, 11:25AM-11:30AM ET
 volume      $2   liquidity $14,790

               BID      ASK    SPREAD     MID   FEE/100   BREAKEVEN
   Up        0.930    0.940   0.010   0.935   $ 0.39     94.39%
   Down      0.060    0.070   0.010   0.065   $ 0.46      7.46%
```

**And the same tool refusing a trade.** This is the part worth reading:

```
 TRIGGER     fade the streak: buy 'Up' at 0.950
 100 shares cost $95.33 · pays $100 · breakeven 95.33%
 measured edge 53.8%-54.2%  ->  NO EDGE at this price
 caveat: under the 60s-TWAP rule (since 2026-08-14) the edge is
         51.3% +/-7% (n=199) - unproven at this price.
```

Most tools are built to say yes. This one calculates the taker fee, the breakeven
hit rate and the measured edge — and says **no** when the price is wrong. That is
the same discipline your data pipeline needs.

**The 91k-row analysis, in five lines of output:**

```
Polymarket resolved windows: 91036
  2025-12-18 04:25 -> 2026-11-15 13:25 UTC
  contiguous segments: 19  (longest 17994 windows = 62.5 days)

Agreement PM settlement vs Binance candle colour: 85251/91025 = 93.66% (95% CI 93.50%-93.81%)
  -> they disagree on 5774 windows, 6.34% of the time
```

**Self-test, offline, no network and no API keys:**

```
  [PASS] fee at 50c = 1.75
  [PASS] breakeven at 50c = 51.75%
  [PASS] render picks the Down ask
  [PASS] json serialises

  11/11 passed
```

---

## Featured project — Polymarket BTC 5-minute market monitor

**The problem.** Polymarket publishes a new 5-minute "Bitcoin Up or Down" market
every 5 minutes (288 a day, ~$12.8M daily volume). Traders watch a price chart and
assume the chart tells them what the market will settle at. It often does not.

**What I built (two parts).**

1. **A settlement-history crawler** (`fetch_pm_history.py`) — pulled **91,036
   resolved markets** (2025-12-18 → 2026-11-15) from a public API with no bulk
   export endpoint.
2. **A live monitor** (`pm_monitor.py`) — detects a run of N same-colour candles and
   shows the **live order book** of the exact market you would trade: real bid/ask,
   depth, the taker fee, and the breakeven hit rate.

**The engineering that mattered.**

| Problem | What I did |
|---|---|
| No bulk export; deep offsets returned an undocumented **HTTP 422** | Reverse-engineered the API, re-partitioned the crawl into date windows, kept offsets shallow |
| 1.5s per page sequentially (~50 min) | Threaded crawl, 8 workers with backoff → **91k records in 255s** |
| Rate limits / 406 / 429 under load | Retry with exponential backoff, per-request isolation, continue-on-error |
| Duplicate and unsettled records | Dedupe by key, drop unresolved, **99.98% contiguous** sequence |
| Silent breakage | Pure functions separated from I/O; offline self-test; explicit exit codes |

**The analysis (this is the part clients actually pay for).**

Rather than assume the popular "7 candles in a row must reverse" rule was true, I
measured it on the **official settlements**, not a chart:

| | Chart (Binance) | **Official settlement (Chainlink TWAP)** |
|---|---|---|
| 7-in-a-row events | 610 | **642** |
| Next candle reverses | 56.4% | **54.1%** (95% CI 50.2–57.9) |
| No reversal within 4 candles | 5.3% | **6.1%** |
| No reversal within 5 candles | 2.5% | **3.4%** |

And the finding a client can act on: **since a settlement-rule change on
2026-08-14, the chart colour matched only 86.2% of settlements** (down from ~97%).
Anyone trading off the chart was working from a series that disagreed with the real
one roughly **one window in seven**.

**Delivered as:** single-file tools, standard library only, no API keys, read-only,
with an offline test suite (11/11 checks) and a README a non-technical buyer can follow.

---

## What I do for clients

| Service | Typical deliverable |
|---|---|
| **API → Sheet / DB pipeline** | Scheduled job that pulls, cleans and writes data; dedupe and validation included |
| **Monitoring + alerting** | Telegram / Slack / email alerts on price, stock, leads, errors — with "is it alive?" checks |
| **Reconciliation** | Report showing whether two systems agree, with the exact rows that don't |
| **Rescue a broken automation** | Diagnose why an existing script/workflow stopped, fix it, add error handling |
| **Verification / audit** | Test whether a claimed result, backtest or dashboard is actually supported by the data |

---

## Stack

`Python` (stdlib-heavy, no bloat) · `REST APIs` · pagination & rate limits · webhooks ·
`Google Sheets` · `SQLite` · `cron` / scheduled jobs · `n8n` / `Make` / `Zapier` ·
logging & alerting · statistics (intervals, backtests, significance)

---

## How I work

1. **Discovery** — 15 minutes of questions about the process, not the technology.
2. **Written scope** — what is included, what is not, what "done" means.
3. **Build + demo** — you see it running before final delivery.
4. **Handover** — code, docs, and how to keep it running. Or I maintain it monthly.

**Honest limits.** I do not sell predictions or "win rates". If the data does not
support a claim, my report will say so — that is the point of hiring someone to check.

---

*Contact: [your name] · [Upwork / Fiverr profile link] · [email]*
