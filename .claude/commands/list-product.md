---
description: Prepare a built product's Etsy/Gumroad listing and Pinterest pins — slot brief for owner approval first, then images, pins, gates and Drive delivery
argument-hint: <PB-ID or product name> [approve]
allowed-tools: Read, Write, Edit, Bash, Agent
---

Prepare the listing and pins for: **$ARGUMENTS**

You are the orchestrator. The owner reviews the image plan **before** any image is
made, and they are not at this machine. So this command runs in two halves with a
stop in between. Run every command from the repository root with
`PY=.venv/bin/python`; let `D` be the product folder.

## First half — the brief (no `approve` argument)

1. **Preconditions.** The product must be delivered:
   - `qa/drive-build.json` exists
   - `$PY scripts/release_check.py "$D" --signoff --require-drive-links` passes

   If either fails, stop and send the owner to `/build-product` first.
2. **Launch `listing-creator` in phase "brief".** It writes `Listing/listing.json`
   and `Listing/slot-brief.md` and runs `check_slot_brief.py` and `check_listing.py`.
3. **Check it yourself:**
   ```bash
   $PY scripts/check_slot_brief.py "$D"
   ```
   Failures go back to the agent once; if they still fail, report them to the owner.
4. **Deliver the brief for review:**
   ```bash
   $PY scripts/upload_to_drive.py --product "$D" --stage brief
   ```
5. **Stop.** Tell the owner:
   - the Drive link to `listing/slot-brief.md`, copied from `qa/drive-brief.json`
   - the slot table (slot · role · source page)
   - "reply `/list-product <PB-ID> approve` to approve, or tell me what to change"

   Do not continue in this turn.

## Second half — after the owner approves (`approve` argument)

Only an explicit approval from the owner in this session counts. A change request
means back to the first half with the changes.

1. **Record the approval** (it hashes the brief; any later edit voids it):
   ```bash
   $PY scripts/check_slot_brief.py "$D" --approve
   ```
2. **Launch `listing-creator` in phase "images" and `pinterest-creator` together.**
   Wait for both.
3. **Gates. Stop at the first failure.** A failing gate goes back to its agent once;
   if it still fails, it goes to the owner.
   ```bash
   $PY .claude/skills/listing-copy/scripts/check_listing.py "$D/Listing/listing.json" --dist "$D/dist" \
       --json "$D/Listing/qa/listing.json"
   $PY .claude/skills/pinterest-pins/scripts/check_pins.py "$D"
   $PY scripts/release_check.py "$D" --listing
   ```
4. **Deliver:**
   ```bash
   $PY scripts/upload_to_drive.py --product "$D" --stage listing
   $PY scripts/append_drive_links.py "$D"
   $PY scripts/upload_to_drive.py --product "$D" --stage signoff
   $PY scripts/release_check.py "$D" --signoff --require-drive-links
   ```
   If an upload fails, paste the error verbatim and say the listing is **not delivered**.

## Report to the owner

- the Etsy title (with character count), tags, price and launch price
- the images built and the five pins, with their source pages
- gate results with real numbers
- **Drive links** for `listing/` and `pinterest/`, copied from `qa/drive-listing.json` only
- **what the owner does next, by hand:**
  - publish the listing on Etsy and Gumroad from the instruction PDF
  - add the live URL to `catalogue.md`
  - set the pins' destination links and pin them
  - add the product's row to `OUTCOMES.md`, then its 14- and 30-day numbers later
- every `[Assumption]` and blocked item
