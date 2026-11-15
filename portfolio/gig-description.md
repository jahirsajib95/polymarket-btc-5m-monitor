# Gig description (Fiverr / Upwork Project Catalog)

Copy-paste ready. Replace `[bracketed]` items only.

---

## Title (pick one, under 80 characters)

1. `I will build a reliable Python data pipeline from any API to Google Sheets`
2. `I will build a monitoring bot with alerts for prices, stock or leads`
3. `I will fix and maintain your broken Python automation script`

> Fiverr tip: title #1 or #3 converts best. "Automation" and "fix" are what buyers
> actually type; "AI agent" is crowded.

## Category

Programming & Tech → Scripting & Automation (Fiverr) / Data Processing (Upwork)

## Search tags

`python`, `api integration`, `data pipeline`, `web scraping`, `automation`,
`monitoring`, `google sheets`, `telegram bot`, `cron`, `webhook`

---

## Description

**Your script worked. Then it silently stopped, and nobody noticed for two weeks.**

That is the actual problem most businesses have — not "I need code", but "I need
this to keep working, and to tell me when it doesn't".

I build small, dependable data pipelines and monitors:

- pull data from an API or page on a schedule
- clean it, validate it, remove duplicates
- write it where you actually look: Google Sheets, a database, a report
- alert you (Telegram / Slack / email) when something is wrong or missing
- and stay maintainable — documented, with error handling, not a black box

**Recent work:** a monitor for Polymarket's 5-minute crypto markets. I crawled
**91,036 settled records** from an API with no bulk export (handling rate limits,
an undocumented HTTP 422, and duplicate/unsettled rows to reach 99.98% continuity),
then built a live monitor showing real order-book prices, fees and breakeven levels.
Delivered as one file, standard library only, no API keys, with an offline test suite.

### What you get

- Working script, with your credentials kept in a `.env` file — never in the code
- Scheduled run set up (cron / scheduler) so it runs without you
- Alerting when a run fails or data is missing
- A short README: how to run it, how to change it, what breaks it
- 7 days of bug-fix support after delivery

### What I need from you

1. Where the data comes from (URL / API / account access)
2. Where the result should go (Sheet, email, database, file)
3. How often it should run
4. What "wrong" looks like — so I can alert on it

### Honest notes

- I will tell you if your idea needs something you have to pay a third party for
  (paid API, proxy, hosting) — before you buy the gig.
- I do not do "guaranteed profit" trading bots, fake reviews, or anything that
  scrapes personal data or breaks a site's terms.

---

## Packages — care first, code included

Buying a script is cheap and usually a mistake. What actually costs you money is the
week it silently stops. So these are priced as **outcomes with a care period**, not
as lines of code.

| | **RESCUE + CARE** | **BUILD + CARE** | **MANAGED** |
|---|---|---|---|
| **Price** | **$150** one-time | **$280** one-time | **$420 / month** |
| Best when | something already broke | you need it built from scratch | you want it off your desk |
| Scope | 1 automation | 1 pipeline, up to 3 sources | up to 6 pipelines |
| Care period included | **14 days** | **30 days** | ongoing |
| Response time | 2 business days | 1 business day | 4 business hours |
| Error handling | fix + dead-man alert | retries, logging, Telegram/email alerts | + uptime dashboard, monthly report |
| Documentation | fix summary | README + handover notes | runbook + quarterly audit |
| Delivery | 2–3 days | 5–7 days | starts within 2 days |

**Why the entry tier is $150 and not $60.** A $60 script is a commodity — an AI
writes the same file for free, and it breaks in week three with nobody watching. The
$150 tier is *diagnosis + fix + a working alert*, which is a different product.

### Extras

| Add-on | Price |
|---|---|
| Extra data source | +$40 |
| Extra output format (Sheet + PDF + DB) | +$30 |
| Extra pipeline under Managed | +$70 / month |
| Rush (under 48h) | +30% |
| Build only, no care period | from $120 — not recommended |

### After the care period

Most clients continue rather than go back to guessing:

- **Care Plan — $180/month**: up to 3 pipelines, monitoring, small changes, fixes.
- **Managed — $420/month**: up to 6 pipelines, 4-business-hour response, monthly
  report and a quarterly audit of whether the numbers still mean anything.

---

## FAQ

**My source has no API. Can you still do it?**
Usually. Options in order of reliability: official API → public data feed → browser
automation. I will tell you which one your site allows and how fragile each is.

**Will it break when the site changes?**
Any scraper can. That is why Standard and Premium include an alert when a run
returns nothing or the layout changes — you find out in minutes, not weeks.

**Can you just fix my existing script?**
Yes, that is the most common request. Send the file and the error and I will quote
based on what is actually wrong rather than guessing.

**Do you offer ongoing maintenance?**
Yes, that is the main product: **$180/month** for up to 3 pipelines (monitoring,
small changes, fixes) or **$420/month** for up to 6 with a 4-hour response time.

**Is my data safe?**
Credentials stay in a `.env` file on your machine/server, never in the code or in
messages. I do not keep copies after handover unless you ask me to maintain it.

---

## Buyer requirements (the form Fiverr sends)

1. Data source — URL, API docs, or which account/site
2. Where the output should go
3. How often it should run
4. Do you already have API keys, and can you share them securely?
5. What should happen when something fails?
