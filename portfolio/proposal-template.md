# Proposal template (Upwork)

Copy-paste ready. Replace `[brackets]`. Keep it under ~180 words — buyers skim.

---

## The template

> Hi [First name] — **[one sentence that proves you read the post, quoting their
> problem, not their job title]**.
>
> I've built exactly this shape of thing: **[one line of proof + link to your
> portfolio item]**. For your case the tricky part is likely **[the specific risk
> you spotted — e.g. "their page loads data with JavaScript, so a simple request
> returns nothing" / "their API pages at 50 records, so a 90k-row pull needs
> offset handling"]**, not the obvious part.
>
> How I'd do it:
> 1. **[Step 1 — data source + access check]** (~[time])
> 2. **[Step 2 — build, with validation + retries]**
> 3. **[Step 3 — schedule, alerting, short README, handover]**
>
> Two questions so I don't guess:
> - **[Question about access/keys]**
> - **[Question about what "wrong" looks like — what should trigger an alert]**
>
> Fixed price **$[X]**, **[N] days**, including **[revisions / 7-day fix support]**.
> Happy to send a 90-second screen recording of a similar job running first if
> that helps.
>
> [Your name]

---

## Variants for the first line

The first line decides whether the rest is read. Never open with "I am a Python
developer with X years of experience".

| Job type | Opening line |
|---|---|
| Fix my broken script | "Your script dies at the pagination step — that's almost always a silent `200` with an empty body, not a real error." |
| API → Google Sheet | "You don't need a dashboard, you need 40 rows in a sheet every morning, and an alert when they don't arrive." |
| Scraper | "Before quoting: does this site render prices in the HTML, or does it fetch them with JavaScript? That single answer changes the whole approach." |
| Monitoring / alerts | "The hard part isn't the alert, it's not being woken up by false ones at 3am." |
| "AI automation" | "Everyone can generate the workflow. The part that's missing is what happens when it returns nothing for two days." |

---

## Rules that actually matter

1. **One post, one proposal.** Tailored beats volume. 5 good proposals a day
   outperforms 50 copy-pastes.
2. **Quote their words.** If they wrote "runs every morning", use "every morning".
3. **Name the risk before they do.** This is the only thing that separates a real
   engineer from a template.
4. **Never claim work you haven't done.** "I haven't done this exact source — the
   closest thing is X, and I'd verify it in 30 minutes before committing to a price"
   is stronger than a bluff, and it protects your reviews.
5. **Always give a price and a time.** "Depends on scope" gets ignored.
6. **Two questions maximum.** More feels like an interview, not an offer.
7. **Attach proof.** A 60–90 second screen recording of a similar job running is
   worth more than three paragraphs.

---

## Short version (for small, clear jobs under ~$100)

> Hi [name] — [one line proving you read it].
>
> I can do this: **$[X]**, **[N] days**, delivered as a script with a `.env` for
> your keys, a schedule, and a 1-page README. Similar work: [link].
>
> One question: **[the single thing you must know before starting]**.
>
> [Your name]

---

## Follow-up (send after 3 days, once, politely)

> Hi [name] — following up in case the project is still open. I've since built a
> similar job ([one line about it]), so the estimate in my proposal still stands,
> and I can start [day]. If you've already hired someone, no problem — good luck
> with it.
