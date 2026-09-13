---
description: Build a product from its spec through the build → critique → revise loop, pass the release gate, protect it, sign it off and deliver it to Google Drive
argument-hint: <PB-ID or product name> [--rounds 2] [--build-only|--critique-only]
allowed-tools: Read, Write, Edit, Bash, Agent
---

Run the product build loop for: **$ARGUMENTS**

You are the orchestrator. You do not build and you do not critique — you run the
two agents, check the gates between them, deliver the result, and report to the
owner. Read `.claude/skills/product-build-loop/SKILL.md` first and follow its round
protocol exactly. Run every command from the repository root with
`PY=.venv/bin/python`.

The owner is not at this machine. Every file they need reaches them through Google
Drive, and a build whose upload did not verify is **not complete**.

## Steps

1. **Resolve the product.** Find its spec in `Product Plans/specs/`. If the
   argument is ambiguous or no spec matches, list what exists and stop.
   If no argument was given, use the build queue order in the product plan's
   "Handoff to the Design/Build agent" and take the first unbuilt product.

2. **Preflight. Stop on any failure, and say what fixes it.**
   ```bash
   scripts/setup.sh --check --no-selftest     # exit 0 = ready; 2 = ready but Drive not configured; 1 = stop
   $PY .claude/skills/printable-pdf/scripts/fetch_fonts.py --dir brands/quiet-compass/fonts --check --check-system
   test -f research/buyer-complaints.md       # the critic's rubric; without it, run /research first
   ```
   - **Drive not configured (exit 2).** Tell the owner now that the build can run
     but cannot be delivered until step M1 of `MULTI_AGENT_PLAN.md` is done.
   - **Spec fields.** Check the spec declares `**Interaction:**`, `**Font set:**`,
     `**Protection:**`, `**Practitioner licence:**` and a `## Cross-references`
     section. If any is missing, stop and route it to the planner or owner.

3. **Round 1 — build.** Launch `product-builder` with the spec path, the brand
   kit and voice paths, and the product folder. Wait for it.

4. **Gate check, yourself.** Before the critic runs, confirm:
   - `dist/` holds every file the spec lists
   - `BUILD-LOG.md` exists
   - `qa/*.json` contains real gate output
   - `qa/pages/<edition>/` has a manifest for every edition

   If the builder claimed a pass the JSON does not support, send it back before the
   critic wastes a pass on it.

5. **Round 1 — critique.** Launch `product-critic` on the same product. It
   re-runs the gates itself; that duplication is deliberate.

6. **Round 2 — revise, then verify.** Send the builder the critique path to work
   BLOCKERs then MAJORs; then the critic to re-check its own findings.

7. **Round 3** only if a BLOCKER survives. Three rounds is the hard limit —
   anything unresolved goes to the owner instead of another round.

8. **Release gate.** When the latest critique round has no open BLOCKER or MAJOR:
   ```bash
   $PY scripts/release_check.py "Products/PB-0XX <Name>"
   ```
   - **If it fails and a round remains:** its failures become BLOCKERs. The builder
     fixes them and the critic verifies, as one round of the loop.
   - **If it fails after round 3:** stop. Report every failure to the owner.
     Nothing is protected, signed off or uploaded.

9. **Finalise** (only after `release_check.py` passes):
   1. Have the builder protect the PDFs (unless the spec says `**Protection:** none`),
      build the practitioner package if the spec sells one, and write `SIGNOFF.md`,
      ending with the unticked Owner checks.
   2. Then run, in order, stopping at the first failure:
      ```bash
      $PY scripts/release_check.py "$D" --signoff
      $PY scripts/upload_to_drive.py --product "$D" --stage build
      $PY scripts/append_drive_links.py "$D"
      $PY scripts/upload_to_drive.py --product "$D" --stage signoff
      $PY scripts/release_check.py "$D" --signoff --require-drive-links
      ```
   3. **If any upload step fails,** paste its error verbatim into the report. Say
      plainly that the build is **not delivered**, and do not describe it as
      complete.

## Report to the owner

- the product, its files, page counts and sizes
- the gate table with real numbers, including `release_check.py`
- the critic's dimension scores and final verdict, and the buyer-complaint checks that failed
- every finding that was rejected or deferred, and why
- **the Drive links**, copied from `qa/drive-build.json` and `qa/drive-signoff.json`
  only — never typed from memory
- **what you must still verify by hand once you download** — these cannot be marked
  done by any agent:
  - print it on paper
  - write on it with a pen
  - test the tablet PDF in GoodNotes
  - test the tablet PDF in Notability
- open owner questions that block the listing (support contact, practitioner
  price, any BLOCKED FOR RELEASE copy)
- next step: `/list-product <PB-ID>`

Never report a number you have not seen in a gate output, never describe a page
you have not opened, and never report an upload that has no verified JSON record.
