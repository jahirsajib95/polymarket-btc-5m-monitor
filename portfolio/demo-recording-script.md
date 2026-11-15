# 60-second demo recording — shot-by-shot script

Everything below is tested on the real tool. Target length **55–60 s**.
Record once badly to test; then record for real.

---

## Before you hit record (5 minutes)

| Check | Why |
|---|---|
| Terminal font **20–22pt**, dark theme | must be readable on a phone |
| Close Slack / mail / notifications | one popup ruins the take |
| Short clean prompt (`btc $`) | looks deliberate |
| Run all four commands once | confirms they work on *your* machine |
| Profile tab open in the browser | so you can paste the link when done |
| No music, no intro, no logo sting | buyers skip anything that smells like an ad |

**If your spoken English is not confident, record it silent with captions.** It
converts almost as well and cannot embarrass you.

---

## The four commands (tested, in this order)

```bash
# 1 — the tool proves itself offline: no network, no keys
python pm_monitor.py --selftest | head -13

# 2 — live: streak + real order book
python pm_monitor.py --once

# 3 — the pricing / refusal block (fires every time, see note below)
python pm_monitor.py --once --streak 1 | sed -n '/TRIGGER *fade/,$p'

# 4 — the 91k-row analysis
python pm_streak_test.py | head -5
```

### Why `--streak 1` in step 3

A real 7-streak happens about twice a day, so you cannot wait for one on camera.
`--streak 1` makes the trigger fire on every window, so the take is always the same
length. Say so if anyone asks — it is a demo flag, not a different result.

**One thing you cannot control:** the verdict line reads either `EDGE` or
`NO EDGE` depending on where the price happens to be. The narration below is worded
so it is true either way. **Never promise "it will say no" before you press record.**

---

## The script, line by line

| Time | Do this | Say this |
|---|---|---|
| **0:00–0:06** | Terminal open, cursor blinking. Do nothing. | "I make data pipelines that don't quietly break. Three things, sixty seconds." |
| **0:06–0:17** | Paste **command 1**, Enter. Wait for `11/11 passed`. | "First — it tests itself offline. Eleven checks, no network, no API keys. If this fails, the tool is broken, not the API." |
| **0:17–0:32** | Clear, paste **command 2**, Enter. Move the pointer to the BID/ASK table. | "Now live. It watches Bitcoin's five-minute candles, finds a streak, then pulls the real order book from Polymarket — bid, ask, depth, and the taker fee." |
| **0:32–0:46** | Clear, paste **command 3**, Enter. | "Then it prices the trade: the fee, the breakeven hit rate, and the edge I measured, side by side. When breakeven is higher, it prints NO EDGE and tells you to walk away." |
| **0:46–0:55** | Clear, paste **command 4**, Enter. | "I also crawled ninety-one thousand settled markets to check whether the rule was even true. It wasn't." |
| **0:55–1:00** | Stop moving. | "If your pipeline has to survive contact with reality — message me. Link below." |

**Speaking words: 105.** At a normal pace, with pauses while commands run, that is
55–58 seconds.

---

## If the verdict on screen says NO EDGE

Great — you got the better take. At 0:32, instead of the last sentence, point at the
line and say:

> "…and there it is. The price is wrong, so it refuses the trade. Most tools only
> know how to say yes."

Still true, still 15 seconds, and it is the strongest moment in the video.

---

## Timing guardrails

- **Over 65 s?** Cut "and the taker fee" from beat 3. Never cut the breakeven/edge line.
- **Under 45 s?** You are rushing. Add one beat of silence after each command finishes.
- **Let the command finish before speaking over the result.** Silence while the
  terminal works reads as confidence.

---

## Things you must NOT say

| Never say | Why |
|---|---|
| "profitable", "win rate", "returns" | invites the one objection you cannot answer |
| "AI-powered" | makes the buyer think "then I'll just use AI" |
| "guaranteed", "100% accurate" | one review ends the account |
| "this will make you money" | the tool itself may print `NO EDGE` on camera |
| "I have 5 years of experience" | the video is the proof; claims invite doubt |

---

## After recording

1. Upload to Loom or YouTube **unlisted**. Title: `API pipeline + live monitor — 60s demo`.
2. Put the link in **three** places: the gig description, the portfolio item, and
   line 2 of every proposal.
3. Keep it under 100 MB so it plays inline on Upwork.

---

## Fallback: if the network fails mid-recording

Not a disaster — it is a selling point if you narrate it. The monitor prints the
reason and keeps running instead of dying:

```
 ! candles unavailable - URLError: timed out
```

Say: *"That's the failure mode working as designed — it tells you what broke instead
of dying silently. That is exactly why people hire me."* Then re-record.
