---
name: product-build-loop
description: The build → critique → revise → release → deliver workflow for digital products, with the hallucination controls that make it trustworthy — single source of truth, deterministic gates, evidence-bound findings, round limits, a script-run release gate, a signed-off release record and a verified Google Drive delivery. Use when running or orchestrating the product-builder and product-critic agents.
---

# The build loop

Two agents, one artefact, a fixed number of rounds, then a gate nobody can talk
past, and a delivery that is verified or not done:

```
product-planner spec ──▶ product-builder ──▶ product-critic ──▶ product-builder
   (already done)          builds PDFs         finds defects       fixes them
                                  ▲                                    │
                                  └──────── round 2, then 3 ───────────┘
                                                                       ▼
                     release_check.py ──▶ pdf-protect ──▶ SIGNOFF.md ──▶ upload to Drive (verified)
                     (fails → BLOCKERs                                  └▶ Drive links appended to SIGNOFF.md
                      for the next round)
```

The orchestrator (the main session, via `/build-product`) runs the agents and every
release and upload script. It does not build or critique itself, and it never
relays a claim it has not seen the evidence for. Run every command from the
repository root with `PY=.venv/bin/python`.

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
7. **Open questions stay open.** The owner's undecided items (support contact,
   practitioner pricing, Notion tiers, free-tier structure, guarantee) are marked
   `[Assumption]` or left as visible placeholders wherever they appear. Neither
   agent may resolve one by guessing.
8. **Round limit.** Three rounds maximum. What is unresolved after round 3 goes to
   the owner in `SIGNOFF.md` under "Unresolved". A loop that cannot converge is
   information, not a reason to keep spinning.
9. **Disagreement is recorded, not argued.** If the builder believes a finding is
   wrong, it writes REJECTED with a reason and evidence. The critic may restate it
   once, then it goes to the owner.
10. **Nothing physical is claimed.** Paper feel, pen bleed, real-device
    annotation and print-shop output cannot be verified here. Both agents list
    them as "needs a human check", every round, and **no agent may tick an owner
    check** in `SIGNOFF.md`.
11. **The release gate is a script.** `scripts/release_check.py` checks what
    shipped past the critic in v1 and fails on any one of these:
    - dead or placeholder URLs
    - products that are not live in `catalogue.md`
    - formats claimed but not shipped
    - SKUs in filenames
    - moved page cross-references or mismatched version stamps
    - a fake tablet edition
    - an undeclared interaction mode
    - missing page renders
    - open BLOCKER/MAJOR findings
    - a critic who did not open every page

    No agent's judgement overrides it.
12. **Delivered means verified.** Nothing uploads before the release gate passes,
    protection has run and `SIGNOFF.md` exists. `upload_to_drive.py` checks the
    files against Drive by hash, and `SIGNOFF.md`'s Drive links are copied from the
    upload record, never typed. A failed upload is reported verbatim and the build
    is not complete.

## Round protocol

**Round 1 — build.** `product-builder` reads the spec, the voice rules and the brand
kit, writes the HTML, renders every edition, runs all gates, fixes what the gates
catch, and writes `BUILD-LOG.md` (decisions, assumptions, gate output, what it could
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

**Release.** When no BLOCKER and no MAJOR remain (or the owner has accepted
them), the orchestrator runs `release_check.py`. If it fails, its failures are the
next round's BLOCKERs — within the same three-round limit. When it passes, the
builder runs `pdf-protect` last (unless the spec says `**Protection:** none`) and
builds the practitioner package if the spec sells one. Then it writes `SIGNOFF.md`,
and the orchestrator delivers it (see "Delivery").

## What each round writes

```
Products/PB-0XX <Name>/
  BUILD-LOG.md            decisions, assumptions, gate output, open questions, OWNER-ACCEPTED lines
  build/new-copy.md       every sentence not from the spec, with its reason and voice rule
  critique/round-N.md     findings, buyer-complaint checks, scores, Pages opened, verdict
  qa/verify-*.json        machine gate output, per edition, per round
  qa/pages/<edition>/     the builder's page PNGs + manifest
  qa/critic-pages/<edition>/  the critic's page PNGs + manifest
  qa/release-check*.json  the release gate (release, listing, signoff modes)
  qa/drive-*.json         upload records (the only source of Drive links)
  SIGNOFF.md              gates table, scores, what a human must still check, Drive links
```

## SIGNOFF.md must contain

- every gate, its command, and its final result — including `release_check.py`
- the nine dimension scores with one line each
- every finding raised, and its outcome (fixed / rejected / deferred / accepted)
- the release file list with sizes, and the protection applied to each (or
  "none — free lead magnet" when the spec says so)
- open owner questions blocking the listing
- **`## Owner checks (not verifiable here, agents may not tick)`**, unticked:
  - `- [ ] Print it on paper`
  - `- [ ] Write on it with a pen`
  - `- [ ] Test the tablet PDF in GoodNotes`
  - `- [ ] Test the tablet PDF in Notability`
- **`## Drive links`** as the **last** section, written only by
  `scripts/append_drive_links.py` from the verified upload records

## Delivery

```bash
$PY scripts/release_check.py "$D" --signoff                      # owner checks present and unticked
$PY scripts/upload_to_drive.py --product "$D" --stage build      # deliverables/ + qa/, verified by hash
$PY scripts/append_drive_links.py "$D"                           # links from qa/drive-build.json
$PY scripts/upload_to_drive.py --product "$D" --stage signoff    # SIGNOFF.md with its links
$PY scripts/release_check.py "$D" --signoff --require-drive-links
```

Drive layout: `Northing Studio/<PB-ID>_<Product-Name>/`
- `deliverables/` — the A4, Letter and tablet PDFs, README and licences
- `listing/`
- `pinterest/`
- `qa/` — SIGNOFF.md, page PNGs and check outputs

Research goes to `Northing Studio/research/`.

## Orchestrator checklist

- [ ] `scripts/setup.sh --check` passes (exit 2 = Drive not configured: say so up front)
- [ ] the spec exists, names its product ID, and has Interaction, Font set, Protection, Practitioner licence and Cross-references
- [ ] `research/buyer-complaints.md` exists
- [ ] `fetch_fonts.py --check --check-system` passes before the build starts
- [ ] builder ran; `BUILD-LOG.md` exists and its gate output is pasted, not summarised
- [ ] critic ran the gates itself, rendered every edition, and listed every page under Pages opened
- [ ] every BLOCKER is closed with re-run evidence
- [ ] `release_check.py` passed before protection
- [ ] `pdf-protect` ran last, after all QA (or the spec says none)
- [ ] `SIGNOFF.md` lists the owner checks, unticked
- [ ] the upload verified, and the Drive links in `SIGNOFF.md` came from the upload record
- [ ] the owner is told, plainly, what is still an assumption and what they must check by hand
