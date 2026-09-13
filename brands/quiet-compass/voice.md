# Voice — Quiet Compass (locked)

**Status: locked ground truth, 2026-09-13.** Changes require an owner decision, recorded
in the changelog at the bottom.

**Sources:**
- The exact copy of **The Focus Audit** (`Product Plans/specs/PB-001 The Focus Audit.md`)
- The exact copy of **The 10-Minute Life Audit** (`Product Plans/specs/PB-022 The 10-Minute Life Audit.md` and its build)
- The voice table in `brand-kit.md`

**Who reads it:** `product-planner`, `product-builder`, `listing-creator`,
`pinterest-creator` and `product-critic`.

**What it covers:** every string a customer can see:
- product pages, README and licence text
- listing copy, image text, and pin titles and descriptions

## How it is enforced

- **Measurable rules run automatically.** They live in
  `.claude/skills/product-qa/assets/banned.json`. The `banned_terms`, `unsafe_claims`
  and `voice` groups **block a release**; `hype` warns. `banned_terms.py` runs them on
  every product PDF, `build/new-copy.md`, README, listing copy and pin copy.
- **This file and `banned.json` must agree.** `scripts/check_voice_sync.py` fails if
  any word listed under "Banned words" below is missing from `banned.json`.
- **Everything else is judged.** The critic reviews it under Copywriting, and every
  such finding cites a rule number from this file (V1–V11).
- **The builder may not write a sentence that breaks a rule.** Each new sentence in
  `build/new-copy.md` names the rule it satisfies, e.g. `(V1, V5)`. A sentence that
  cannot name one is not written.

## 1. The stance

Quiet Compass is paper and PDF. **It is not an app. Nothing here reminds you.** It
sends no notifications, keeps no streaks, tracks nothing, and does not cheer you on.
The pages hold the structure; the buyer does the thinking. We ask for evidence of
what actually happened, not encouragement about what might.

## 2. Rules

**V1 · Short declarative sentences.** One idea per sentence. Second person, present
tense. Most sentences stay under 15 words. A longer sentence has to be carrying a
concrete list.
> "Eight areas. One score each. Ten minutes." — PB-022 p.1
> "Do one day at a time. Twenty minutes, not two hours." — PB-001 p.2

**V2 · A number instead of an adjective.** State the size of the ask as a count or a
time, never as "quick", "easy" or "powerful".
> "Seven days, twenty minutes" — PB-001 p.2 · "Three, not thirteen" — PB-001 p.13

**V3 · Evidence, not encouragement.** Ask for what actually happened. Never praise
the reader, predict success or promise a feeling.
> "Log yesterday, not a typical day — typical days don't exist." — PB-001 p.5
> "07:10 · 40 min · Phone in bed · ✗ — I'd have said 10 minutes. It was 40." — PB-001 p.5

**V4 · Anti-motivational.** No cheerleading, no "you've got this", no identity talk
("best self", "level up"), no transformation. Treat a setback as normal and as data.
> "It will slip. That's not the sprint failing, that's a normal month." — PB-001 p.18
> "A dented wheel is normal. A dent you've named is workable." — PB-022 p.3

**V5 · Not an app.** Never promise reminders, streaks, tracking, notifications,
automation, or that the product does the work for the reader.
> "This isn't a productivity system. It's an audit — you're gathering evidence for one week, then making one decision with it." — PB-001 p.2
> "This is paper and PDF. You do the thinking; the pages hold the structure." — brand kit

**V6 · Kind but firm.** Give direct instructions without shaming. Name the
uncomfortable thing plainly, and allow the reader not to act on it yet.
> "You don't have to act on it this week — just stop pretending you don't see it." — PB-001 p.16
> "Don't fix it. Just make one move this week." — PB-022 p.4

**V7 · Honest limits.** Say what the product does not do. A free product is complete
as it stands. A cross-sell names only products that are live in `catalogue.md`, and
says what that product adds.
> "This free audit is complete as it is — the paid one goes deeper, it doesn't unlock this." — PB-022 p.4

**V8 · Specific over general.** Ask for the concrete instance, not the category.
> "Be specific. 'Email' is not an answer; 'clearing inbox before lunch' is." — PB-001 p.2
> "Score each area 0–10 for how it is right now, not how it should be and not how it was last year." — PB-022 p.1

**V9 · Not clinical, not advice.** A structured self-reflection tool. Never diagnose,
treat or advise. When something is beyond the page, point to a qualified person.
> "If something here worries you, talk to someone qualified — that is a strong move, not a weak one." — PB-022 p.1

**V10 · Name our own mechanisms.** "The Vital Few", "the Floor", "the eight-area
wheel", "the Focus Charter". Never borrow another method's name (see Banned words).

**V11 · Calm punctuation.** No exclamation marks, no emoji, no sentences in capitals.
Mono kickers are labels, not sentences. No stacks of rhetorical questions.

## 3. Banned words

Each item below exists as a `term` in `banned.json`, and `check_voice_sync.py` checks
that. Trademarks and borrowed method names block a release:

- `Wheel of Life`
- `Getting Things Done`
- `GTD`
- `PARA`
- `Building a Second Brain`
- `Second Brain`
- `12 Week Year`
- `Bullet Journal`
- `BuJo`
- `Atomic Habits`
- `That Girl`
- `75 Hard`
- `WOOP`
- `Mandalart`
- `Solo Leveling`
- `Eisenhower Matrix`
- `Life Compass`
- `1% Studio`

Voice violations also block a release:

- `exclamation mark`
- `you deserve`
- `you've got this`
- `best self`
- `level up`
- `journey`
- `hustle`
- `motivation`
- `reminders`
- `streaks`
- `notifications`
- `this app`
- `does the work for you`

`motivation`, `reminders`, `streaks` and `notifications` are banned as **promises or
cheering**: "stay motivated", "daily reminders", "build your streak", "push
notifications". Naming them in order to question them is on voice. PB-004's
"Streaks are fiction. Restarts are the skill." and a quoted belief like "I do the
thing when I'm motivated" are both fine. `this app` and `does the work for you` are
allowed only when negated ("not an app"), which is the stance in §1. Unsafe-claim
patterns (treatment, diagnosis, advice, invented statistics, weight, guarantees) and
hype warnings (transformation, fake urgency, "unlock", "effortless") are defined in
`banned.json` and are not repeated here.

## 4. On-voice and off-voice, worked

The left column is our real copy. The right column is the same idea written the way
we never write it.

| # | On voice (source) | Off voice | Breaks |
|---|---|---|---|
| 1 | "Eight areas. One score each. Ten minutes." (PB-022 p.1) | "Discover the full picture of your life in just a few amazing minutes!" | V1, V2, V11 |
| 2 | "Score each area 0–10 for how it is right now, not how it should be and not how it was last year." (PB-022 p.1) | "Rate how fulfilled you feel on the journey to your best self." | V3, V4, V8 |
| 3 | "First instinct. Don't average your whole life into a 7." (PB-022 p.1) | "Take your time and reflect deeply on every part of your life." | V1, V8 |
| 4 | "A dented wheel is normal. A dent you've named is workable." (PB-022 p.3) | "Don't worry, you've got this! Every area can be amazing." | V4, V11 |
| 5 | "Don't fix it. Just make one move this week." (PB-022 p.4) | "Now crush your lowest area and level up your whole life." | V4, V6 |
| 6 | "This free audit is complete as it is — the paid one goes deeper, it doesn't unlock this." (PB-022 p.4) | "Unlock your full results with the premium version!" | V7, V11 |
| 7 | "This isn't a productivity system. It's an audit — you're gathering evidence for one week, then making one decision with it." (PB-001 p.2) | "The ultimate productivity system that keeps you motivated all week." | V3, V5 |
| 8 | "Log yesterday, not a typical day — typical days don't exist." (PB-001 p.5) | "Track your time every day and build an unbreakable streak." | V3, V5 |
| 9 | "07:10 · 40 min · Phone in bed · ✗ — I'd have said 10 minutes. It was 40." (PB-001 p.5) | "Be more mindful of your screen time and make better choices." | V3, V8 |
| 10 | "It will slip. That's not the sprint failing, that's a normal month." (PB-001 p.18) | "Most people quit here. No excuses — stay motivated." | V4, V6 |
| 11 | "Be specific. 'Email' is not an answer; 'clearing inbox before lunch' is." (PB-001 p.2) | "Think about the things that take up your time." | V8 |
| 12 | "If something here worries you, talk to someone qualified — that is a strong move, not a weak one." (PB-022 p.1) | "Find out if you're burnt out, and heal your stress for good." | V9 |

## 5. Fixed wording

- **Audit and reflection products:** "A structured self-reflection tool. Not therapy,
  diagnosis or financial advice." It appears on the listing, on the Start here page,
  and in the footer of any scoring page.
- **Money products:** "Educational only — not financial advice."
- **Practitioner licence:** keeps the self-reflection wording. Use inside a
  professional relationship does not make the pages a clinical or assessment tool.

## Changelog

- **v1 · 2026-09-13** — Locked. Extracted from the PB-001 and PB-022 copy and the
  brand kit's voice table, as the owner requested in `MULTI_AGENT_PLAN.md` item 13.
