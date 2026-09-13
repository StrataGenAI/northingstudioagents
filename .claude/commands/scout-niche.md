---
description: Score candidate niches from the owner's exported keyword/competitor CSVs and deliver a ranked shortlist of 3 with kill reasons to Google Drive
argument-hint: (no arguments)
allowed-tools: Read, Write, Edit, Bash, Agent
---

Scout niches for the next product line. Run every command from the repository root
with `PY=.venv/bin/python`.

1. **Current outcomes.** `git pull --ff-only`. The owner edits `OUTCOMES.md` on
   GitHub, and niche-scout reads it first. If the pull fails, say so and continue
   with the local copy, naming its last commit date.
2. **Pull the owner's exports from Drive:**
   ```bash
   $PY scripts/upload_to_drive.py --pull-inputs
   ```
   If it fails, stop and tell the owner exactly what the error says. The expected
   files and columns are in `scripts/templates/`, and step M5 of
   `MULTI_AGENT_PLAN.md` covers the upload. Never continue with old or guessed
   inputs.
3. **Launch `niche-scout`.** Wait for it.
   - If it reports that `niche_metrics.py` failed, relay the error and stop.
   - Otherwise confirm `research/niche-shortlist-<today>.md` exists, ranks at most
     three niches, and gives every rejection one kill reason.
4. **Deliver:**
   ```bash
   $PY scripts/upload_to_drive.py --research
   ```
   If it fails, paste the error and say the shortlist is not delivered.

## Report to the owner

- the three niches, their totals and the line each belongs to
- the rejected niches with their kill reasons
- input warnings (stale exports, data gaps)
- whether `OUTCOMES.md` had data
- the Drive link to the shortlist, copied from `research/drive-research.json`
- next step: `/research <niche>`
