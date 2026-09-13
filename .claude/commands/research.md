---
description: Research a shortlisted niche on Etsy and Gumroad — competitor report plus the buyer-complaints evidence the critic scores against — and deliver both to Google Drive
argument-hint: [niche from the latest shortlist]
allowed-tools: Read, Write, Edit, Bash, Agent
---

Research: **$ARGUMENTS** (default: the rank-1 niche in the newest
`research/niche-shortlist-*.md`). Run every command from the repository root with
`PY=.venv/bin/python`.

1. **Resolve the niche.** Read the newest shortlist. If there is none, stop and
   send the owner to `/scout-niche`. If the argument names a niche that is not on
   it, say so and ask before researching an unscored niche.
2. **Launch `digital-product-researcher`** with the niche and the shortlist path.
   Wait for it.
3. **Check its output yourself:**
   - `Research Reports/<today> Digital Product Research Report.md` and `.pdf` exist,
     and the PDF has pages
   - `research/buyer-complaints.md` exists and has at least one `## BC-` theme,
     each with a dimension, a review count and a test

   If `buyer-complaints.md` is missing or has no testable themes, the build loop
   cannot score products. Send it back once, then report to the owner.
4. **Deliver:**
   ```bash
   $PY scripts/upload_to_drive.py --research
   ```
   If it fails, paste the error and say the research is not delivered.

## Report to the owner

- the report's page count
- the number of complaint themes and how many are weak
- the top findings and the top 5 product ideas
- coverage gaps
- the Drive links, copied from `research/drive-research.json`
- next step: plan products with the `product-planner` agent
