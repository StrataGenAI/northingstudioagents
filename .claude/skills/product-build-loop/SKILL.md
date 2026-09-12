---
name: product-build-loop
description: The build → critique → revise → finalise workflow for digital products, with the hallucination controls that make it trustworthy — single source of truth, deterministic gates, evidence-bound findings, round limits and a signed-off release record. Use when running or orchestrating the product-builder and product-critic agents.
---

# The build loop

Two agents, one artefact, a fixed number of rounds:

```
product-planner spec ──▶ product-builder ──▶ product-critic ──▶ product-builder
   (already done)          builds PDFs         finds defects       fixes them
                                  ▲                                    │
                                  └──────── round 2, then 3 ───────────┘
                                                                       ▼
                                                              SIGNOFF.md + ship
```

The orchestrator (the main session) runs the agents; it does not build or
critique itself, and it never relays a claim it has not seen the evidence for.

## The hallucination controls

These are the point of the whole workflow. Each one removes a chance to make
something up.

1. **Single source of truth.** `Product Plans/specs/PB-0XX *.md` decides what the
   product says. The builder may not improve, paraphrase or "fix" the spec's copy.
   Genuinely new copy goes in `build/new-copy.md` with a one-line reason, and
   `spec_coverage.py` fails the build if any new sentence is unjustified.
2. **Every claim is a measurement.** Page counts, trim, fonts, ink, type size and
   fill come from `verify_pdf.py`; copy coverage from `spec_coverage.py`; banned
   terms from `banned_terms.py`. Neither agent may state these from memory, and
   both paste the actual output into their report.
3. **Look before judging.** Any statement about appearance requires the agent to
   have opened the rendered PNG with Read, in this session.
4. **Evidence-bound findings.** A critic finding without a gate output, a quoted
   string or a named PNG is dropped by the builder — with a note, not silently.
5. **Fix means re-measure.** A finding is only "fixed" when the gate that caught
   it is re-run and its new output is pasted in. No re-run, no fix.
   And a revision is only finished when **every edition is rebuilt**. A builder
   that stops mid-round — a slow render, an interrupted session — leaves one new
   file beside two stale ones, and every gate passes all three because each file
   is internally valid. Pass `--source` to `verify_pdf.py` for each edition's HTML
   and the shared CSS; it fails a PDF older than what it was built from. Equally,
   "Chrome wrote a file" is not "the build finished": a killed run can leave an
   un-normalised page box behind.
6. **Scope is fixed.** The critic does not redesign the product, and the builder
   does not add features. Both route anything beyond the spec to the owner as an
   IDEA.
7. **Open questions stay open.** The owner's undecided items (brand name, Notion
   tiers, free-tier structure, guarantee) are marked `[Assumption]` wherever they
   appear. Neither agent may resolve one by guessing.
8. **Round limit.** Three rounds maximum. What is unresolved after round 3 goes to
   the owner in `SIGNOFF.md` under "Unresolved". A loop that cannot converge is
   information, not a reason to keep spinning.
9. **Disagreement is recorded, not argued.** If the builder believes a finding is
   wrong, it writes REJECTED with a reason and evidence. The critic may restate it
   once, then it goes to the owner.
10. **Nothing physical is claimed.** Paper feel, pen bleed, real-device
    annotation and print-shop output cannot be verified here. Both agents list
    them as "needs a human check", every round.

## Round protocol

**Round 1 — build.** `product-builder` reads the spec and the brand kit, writes
the HTML, renders every edition, runs all gates, fixes what the gates catch, and
writes `build/BUILD-LOG.md` (decisions, assumptions, gate output, what it could
not verify).

**Round 1 — critique.** `product-critic` runs the gates itself (it never trusts
the builder's numbers), opens every rendered page, and writes
`critique/round-1.md`: findings in the standard format, dimension scores, and a
verdict of SHIP / FIX / REBUILD.

**Round 2 — revise.** The builder addresses each finding in order: BLOCKER, then
MAJOR, then MINOR, and answers each one FIXED (with re-run gate output), REJECTED
(with reason) or DEFERRED (with the owner question it depends on). It appends to
the build log; it does not rewrite history.

**Round 2 — verify.** The critic re-checks only the findings it raised, plus a
full gate re-run, and writes `critique/round-2.md`. New defects introduced by the
fixes are fair game; new opinions about untouched pages are not.

**Round 3** happens only if a BLOCKER survives. Same shape.

**Finalise.** When no BLOCKER and no MAJOR remain (or the owner has accepted
them), the builder runs `pdf-protect` last, then writes `SIGNOFF.md`.

## What each round writes

```
Products/PB-0XX <Name>/
  build/BUILD-LOG.md      decisions, assumptions, gate output, open questions
  build/new-copy.md       every sentence not from the spec, with its reason
  critique/round-N.md     findings, scores, verdict
  qa/verify-*.json        machine gate output, per edition, per round
  qa/pages/*.png          what was actually looked at
  SIGNOFF.md              gates table, scores, what a human must still check
```

## SIGNOFF.md must contain

- every gate, its command, and its final result
- the nine dimension scores with one line each
- every finding raised, and its outcome (fixed / rejected / deferred / accepted)
- **what could not be verified here** — printing on paper, writing on it with a
  pen, GoodNotes and Notability on a real device, colour on a real printer
- open owner questions blocking the listing
- the release file list with sizes, and the protection applied to each

## Orchestrator checklist

- [ ] the spec exists and names its product ID
- [ ] `fetch_fonts.py --check` passes before the build starts
- [ ] builder ran; `BUILD-LOG.md` exists and its gate output is pasted, not summarised
- [ ] critic ran the gates itself and opened the PNGs
- [ ] every BLOCKER is closed with re-run evidence
- [ ] `pdf-protect` ran last, after all QA
- [ ] `SIGNOFF.md` lists the human checks that remain
- [ ] the owner is told, plainly, what is still an assumption
