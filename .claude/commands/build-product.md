---
description: Build a product from its spec through the build → critique → revise loop, then finalise it
argument-hint: <PB-ID or product name> [--rounds 2] [--build-only|--critique-only]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill
---

Run the product build loop for: **$ARGUMENTS**

You are the orchestrator. You do not build and you do not critique — you run the
two agents, check the gates between them, and report to the owner. Load the
`product-build-loop` skill first and follow its round protocol exactly.

## Steps

1. **Resolve the product.** Find its spec in `Product Plans/specs/`. If the
   argument is ambiguous or no spec matches, list what exists and stop.
   If no argument was given, use the build queue order in the product plan's
   "Handoff to the Design/Build agent" and take the first unbuilt product.

2. **Preflight.**
   ```bash
   python3 .claude/skills/printable-pdf/scripts/fetch_fonts.py --dir Products/_assets/fonts --check
   ```
   Fix fonts before anything else; a build on missing fonts silently falls back
   to system faces.

3. **Round 1 — build.** Launch `product-builder` with the spec path, the brand
   kit path and the product folder. Wait for it.

4. **Gate check, yourself.** Confirm `dist/` holds every file the spec lists,
   `BUILD-LOG.md` exists, and `qa/*.json` contains real gate output. If the
   builder claimed a pass the JSON does not support, send it back before the
   critic wastes a pass on it.

5. **Round 1 — critique.** Launch `product-critic` on the same product. It
   re-runs the gates itself; that duplication is deliberate.

6. **Round 2 — revise, then verify.** Send the builder the critique path to work
   BLOCKERs then MAJORs; then the critic to re-check its own findings.

7. **Round 3** only if a BLOCKER survives. Three rounds is the hard limit —
   anything unresolved goes to the owner instead of another round.

8. **Finalise.** When no BLOCKER or MAJOR remains, have the builder run
   `pdf-protect` (last, after all QA) and write `SIGNOFF.md`.

## Report to the owner

- the product, its files, page counts and sizes
- the gate table with real numbers
- the critic's dimension scores and final verdict
- every finding that was rejected or deferred, and why
- **what still needs a human**: print it and write on it, check it in greyscale,
  tap every link in GoodNotes and Notability
- open owner questions that block the listing — including the brand name, which
  remains an assumption until confirmed

Never report a number you have not seen in a gate output, and never describe a
page you have not opened.
