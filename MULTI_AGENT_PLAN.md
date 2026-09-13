# MULTI_AGENT_PLAN — Northing Studio pipeline: headless Linux, Drive delivery, new gates

> Plan mode only lets me write to this plan file, so the **first step after approval is to copy
> it verbatim to `/home/ubuntu/northingstudio/MULTI_AGENT_PLAN.md`**. I won't touch any agent file,
> script or product until you approve.

## Context

The pipeline was built on macOS. Here it runs on a headless Ubuntu 26.04 x86_64 server with
passwordless sudo, and you're working remotely, so every file you need has to reach you through
Google Drive. The current v1 builds let several defects past the critic: placeholder URLs,
upsells to products that don't exist, SKU strings in filenames, and no copy of any file off the
machine. This plan:

- ports rendering, rasterising and font checks to headless Linux
- adds Drive delivery that fails hard on errors
- settles the brand structure
- adds a release gate aimed at the defects that got past the critic
- makes the tablet edition a real edition
- adds a niche-scout agent upstream and an outcomes feedback loop
- ties the critic's rubric to real buyer complaints
- makes listing images and Pinterest pins explicit outputs you review

**Unchanged:** the 3-round build↔critique loop, the rule that numbers come from scripts, and
`spec_coverage.py`.

### Decisions you made (2026-09-13)
| Question | Decision |
|---|---|
| Bash in agents | **Allowed.** Agents get Read, Write, Edit, Bash, and WebSearch/WebFetch where needed. Grep, Glob, TodoWrite and Skill are removed. |
| Drive auth | **rclone with an OAuth token** made on your laptop. Personal Gmail rules out a service account (no storage quota). |
| File prefix | **Keep `NorthingStudio_`** (what's on disk today). This overrides item 12's "keep QuietCompass_". |
| catalogue.md | **Live listings only.** An upsell to anything without a live URL fails. |

---

## Conflicts between your brief and the repo

1. **Tool list vs Bash.** Every agent except the planner has to run scripts. Settled: Bash is
   added. `Task` is not added to any agent: subagents can't spawn subagents, and only the
   slash commands launch agents (the tool is called `Agent` in Claude Code 2.1.270).
   `Skill` goes too; skills still load through each agent's `skills:` frontmatter. I can't
   confirm your note that Grep and Glob get stripped, but removing them costs nothing.
2. **File prefix.** `rename_brand.py` already swapped QuietCompass→NorthingStudio (144
   occurrences), and `brand-kit.md` records that "Quiet Compass" was dropped because it was
   unavailable on Etsy. Settled: keep `NorthingStudio_`. Using "Quiet Compass" as the line name
   in listing titles is still exposed to that Etsy conflict. **This is your risk to accept.**
3. **The brand kit contradicts itself.** Its screening table says a Northing Studio conflict was
   "found, and knowingly accepted", but its v2 changelog says "remains unscreened". The plan's
   Q1 still asks whether the brand is Northing Studio. I'll record your decision (NORTHING
   STUDIO = shop) and delete the stale `[Assumption]` flags. The screening contradiction goes
   into `brands/SHOP.md` as an open owner note.
4. **"The Balance Audit / The Compass System don't exist."** Both are specced (PB-003, PB-002)
   but not built or listed. With "live only", the free products' next-step copy now fails
   `release_check`. The fix is a **spec change to product copy**, which is the planner's or your
   job; I won't rewrite it myself. PB-006 and PB-022 stay blocked until their specs drop those
   lines. They return in v1.1 once the paid products are live.
5. **The Focus Audit hasn't been built.** PB-001 exists only as a spec. `voice.md` will draw on
   the PB-001 spec copy plus the built PB-022 (and PB-006) copy. The "Day 5 collects 6/8/10/12"
   check (item 18) is written generically and proven on PB-022; it applies to PB-001 when that is
   built. In the spec, Day 5 is pp. 13–14, with the pull-forward markers on p. 13.
6. **`quietcompass.example` history.** It survives only in PB-006's build log and QA JSON, but
   the **current** PB-006 dist still ships `northingstudio.example` (footer plus a link) and
   `hello@northingstudio.example`. PB-022's README ships `<SUPPORT CONTACT - owner to insert…>`.
   `release_check` will fail both. You need to supply a real support contact.
7. **Neither existing product can be released.** PB-006's round 1 was FIX with 6 MAJORs; PB-022's
   was FIX with 3 MAJORs. Round 2 never ran, and there is no `SIGNOFF.md`. Once the port lands,
   both continue at round 2 and nothing uploads until they pass.
8. **Tablet editions exist but are zoomed print layouts.** Both are 1620×2160 px (3:4, not A4), so
   an "identical to A4" check alone would pass them. PB-022's tablet is its print layout at
   28 mm margins ×2.041, about 13% blank per side. The new no-print-margin check will **fail
   both current tablet editions**, which is what you asked for, and means rework.
9. **Fillable.** No product has form fields, and Chrome's print-to-PDF can't create them, so every
   current product is annotate-only. The spec field and the gate go in now. Actually *producing*
   fillable PDFs would need a new pypdf step that adds AcroForm fields. **Out of scope unless you
   ask.** `release_check` fails any product declared "fillable" that has no fields.
10. **There's no licence generator.** Licences are hand-written into each README; the PDFs carry
    no licence text (checked). So the practitioner variant is just a different `LICENCE.txt` and
    README section, not a second set of PDFs. I'll draft plain-English licence text; **have it
    reviewed before you sell it.** Practitioner pricing isn't in the plan, so it stays an
    `[Assumption]` for you to set. It keeps the "not a clinical tool" framing, which matters more
    once the buyer is a therapist.
11. **Buyer complaints need Etsy.** Gumroad exposes only star percentages, no review text
    (`gumroad.py` confirmed). Low-star review text comes from Etsy: archive JSON-LD samples
    (thin), or the Etsy Open API (needs a key, optional manual step M4). The research files stay
    gitignored (third-party text); they go to your private Drive only.
12. **Critic depends on research.** `research/` and `Research Reports/` don't exist on this
    machine. Since the rubric has to come from real complaints, `/build-product` preflight
    **fails while `research/buyer-complaints.md` is missing**. So the researcher has to run
    before any critique round.
13. **Upload ordering (items 9/10 vs 27).** "Upload last" happens per stage. Build stage: the
    deliverables and QA upload after SIGNOFF. Listing stage: the slot brief uploads for your
    review, then listing and pins upload after their gates pass. SIGNOFF links are written after
    upload, and SIGNOFF is then re-uploaded and re-verified.
14. **Drive links are private by default.** A "shareable link" that works for anyone would make
    paid files public. `upload_to_drive.py` returns owner-only `drive.google.com` links; `--public`
    (anyone with the link) is opt-in per call.
15. **Chromium.** Ubuntu's `chromium` is snap-only (apt has no candidate). Snap's private `/tmp`
    and home confinement break the temp-profile and output-path handling. I'll install
    **Google Chrome stable from Google's signed apt repo** (a Chromium build, same flags,
    updated by apt), overridable with `CHROME_BIN`.
16. **The frontend-design skill.** It exists only as an official plugin in
    `~/.claude/plugins/…`, and the builder is told to *ignore its taste brief*. **Remove the
    reference** and move the three rigour rules it was used for (one idea per page, no generic
    layout, three type sizes maximum) into `printable-pdf/SKILL.md`.
17. **Getting your inputs onto the server.** You're remote. CSV exports go in Drive
    `Northing Studio/research/input/` (a new subfolder), and `setup`/`niche-scout` pull them into
    `data/research-input/`. You edit `OUTCOMES.md` on GitHub's web editor; commands `git pull`
    before reading it.
18. **Etsy URLs from a datacenter IP** usually return 403 (bot wall). In `release_check`, an
    etsy.com URL counts as verified only through the Etsy API with `ETSY_API_KEY`. Without the
    key it **fails as unverifiable**, never passes silently.

---

## One-time manual steps for you (exact)

**M1 — Get the Drive token (about 10 minutes; any laptop with a browser).**
1. Install rclone on your laptop: https://rclone.org/downloads/.
2. Open a terminal on this server from a browser: AWS Console → EC2 → this instance → **Connect**
   → *EC2 Instance Connect* or *Session Manager*. That gives an interactive TTY, which Claude
   Code's `!` prompt doesn't.
3. On the server, run `rclone config --config ~/.config/northing/rclone.conf` and answer:
   - `n` (new remote), name **`northing`**, storage **`drive`**
   - client_id and client_secret: blank (rclone's built-in client; a personal "Testing" OAuth
     app would expire the token every 7 days)
   - scope **`drive`** (full access). *Corrected during implementation:* `drive.file` only sees files rclone
     created itself, so it could never read the CSVs you upload by hand to `research/input/`.
   - root_folder_id: blank; service_account_file: blank
   - advanced config `n`; "Use web browser to automatically authenticate?" → **`n`**
4. rclone prints `rclone authorize "drive" "<code>"`. Run that on your **laptop**, log in as the
   Drive owner, and paste the token it prints back into the server prompt. Then answer "Shared
   Drive?" `n` → `y` to keep.
5. Still in that server terminal:
   `echo 'export GDRIVE_CREDENTIALS=$HOME/.config/northing/rclone.conf' >> ~/.bashrc && chmod 600 ~/.config/northing/rclone.conf`
6. Let the pipeline create the "Northing Studio" folder on its first upload. If you create it by
   hand first, create exactly one: two folders with the same name get merged by `rclone dedupe`.
   **Never paste the token into this chat**, or it ends up in the transcript.

**M2 — Support contact.** Give me the real support email or URL for READMEs and listings.
**M3 — Practitioner licence price** (Gumroad tier / Etsy listing), plus a legal review of the
licence text.
**M4 (optional) — Etsy Open API key** from https://www.etsy.com/developers (app approval takes days).
It enables Etsy review text and Etsy URL verification. Set `ETSY_API_KEY` in `~/.bashrc` from the
same browser terminal.
**M5 — First CSV exports** for niche-scout (columns below), uploaded to Drive
`Northing Studio/research/input/` once M1 exists.
**M6 — Owner checks** after download: print, write on it, and test in GoodNotes and Notability.
No agent may tick these.

---

## Implementation, in order (each phase is verified before the next)

### Phase 1 — Headless environment (A1–A5)

**Shared helpers (new):** `scripts/lib/chromium.py` and `scripts/lib/raster.py`. Skill scripts
add the repo root to `sys.path`; they already assume the repo root as cwd.

- **`chromium.py`**
  - Finds the browser in order: `$CHROME_BIN`, then `google-chrome-stable`, `google-chrome`,
    `chromium`, `chromium-browser`. It fails loudly if none is found.
  - Always passes `--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu
    --no-first-run --hide-scrollbars`, plus a temp `--user-data-dir`.
  - `print_pdf()` moves over the existing Popen, `%%EOF` and stable-size polling from
    `build_pdf.py:99-120` unchanged.
  - `screenshot()` moves over the IEND/FFD9 polling from `render_artboard.py`.
- **`raster.py`**
  - Wraps poppler's `pdftoppm`: `page_png(pdf, page, width|px_per_mm, grey)` and
    `page_grey_matrix()` (parses PGM, replacing the hand-rolled BMP parse).
  - Pillow provides `image_size`, `resize` and `to_jpeg`, replacing `sips`.
  - **Raises if `pdftoppm` is missing.** Nothing returns `None`.

**Script ports** (Chrome lookup and `sips` calls replaced by the helpers):

| Script | Change |
|---|---|
| `printable-pdf/scripts/build_pdf.py` | Chrome via helper. Page-box `normalise()` kept as is. |
| `printable-pdf/scripts/render_pages.py` | `pdftoppm`. **Required** output `qa/pages/<edition>/<stem>-pNN.png` (+ `-grey`), plus `manifest.json` (page count, dpi, sha256 per PNG). Exits 1 if PNG count ≠ PDF page count. |
| `printable-pdf/scripts/verify_pdf.py` | `page_bitmap` uses `raster.py` at the same `PX_PER_MM = 320/297`. **A raster failure is a FAIL** (today lines 63-64 and 397-398 skip silently). `--no-raster` only allowed with `--allow-no-raster` and recorded in the JSON. |
| `pdf-report/scripts/md_to_pdf.py` | Adds the missing `which` fallback, timeout, `%%EOF` wait and `--no-sandbox` via helper. Pillow replaces `sips`. |
| `listing-images/scripts/render_artboard.py` | Helper. Pillow for `dimensions()` (on Linux it returns 0×0 today, so every render fails) and `--jpg`. |
| `listing-image-audit/scripts/contact_sheet.py`, `palette.py` | Helper / Pillow. |

**Font substitution check (A2)**
- `fetch_fonts.py`: records each face's **PostScript name** in `manifest.json`, parsed from the
  WOFF `name` table (stdlib zlib + struct). It also installs the brand faces into
  `~/.local/share/fonts/<line>/` and runs `fc-cache`.
- `verify_pdf.py`: new required `--fonts <line>/fonts/manifest.json`.
  - It strips the `ABCDEF+` subset prefix and **FAILS on any font not in the manifest**, which
    catches DejaVu, Liberation or whatever fontconfig substituted.
  - Reports can pass `--any-font`; product builds may not.
- **Where the font set is named:** a new spec field `Font set: brands/quiet-compass/fonts`.
  Specs don't name fonts today; the brand kit does.
- **Why system fonts too:** `fonts-dejavu-core` is installed as a base, because Chrome needs *a*
  system font for its UI. The manifest check is what stops it reaching a product.

**Python.** `python3` is externally managed (PEP 668), so `setup.sh` builds `.venv/`
(gitignored) with `pypdf markdown requests Pillow`. Every doc and agent command changes
`python3 …` to `.venv/bin/python …`.

**`scripts/setup.sh` (A4).** Idempotent: every step checks before it acts; `set -euo pipefail`;
safe to re-run.
1. apt: `poppler-utils fontconfig fonts-dejavu-core curl ca-certificates python3-venv gnupg`.
2. Google Chrome: keyring in `/etc/apt/keyrings/google-chrome.gpg`, a `signed-by` source list,
   then `google-chrome-stable`.
3. rclone: the official `.deb` from downloads.rclone.org, checked against `SHA256SUMS`, only if
   missing or older than 1.65 (apt's 1.60 is too old).
4. `.venv` plus pip packages; then `fetch_fonts.py --check` and system font install;
   `fc-list | grep` for each family.
5. **Self-test:** render `Products/_smoke`, then `verify_pdf` (fonts plus raster), then
   `render_pages` (PNG count).
6. Drive: if `GDRIVE_CREDENTIALS` is set, `rclone lsd northing:` plus a write/read/delete probe.
   If it isn't set, print M1 and **exit 2** ("installed, Drive not configured").
7. Print a PASS/FAIL table.

**Also in Phase 1:** remove `frontend-design` from `product-builder.md:5,26` and fold its rules
into `printable-pdf/SKILL.md`. Rewrite the Requirements and "Platform facts" sections of
`README.md` for Linux. Update `pdf-report`, `listing-images` and `listing-image-audit` SKILL.md,
which still say macOS/`sips`.

**Risk:** poppler anti-aliasing differs from `sips`, so ink and gap percentages will shift slightly.
Phase 1 re-measures `_smoke`, PB-006 and PB-022 and records the before/after numbers in their
BUILD-LOGs. Thresholds stay the same unless a difference beyond ±0.3 pp shows up; if it does,
I'll report it to you rather than silently retune.

### Phase 2 — Brand structure, voice, catalogue, outcomes (C12–13, D15, G24)

```
brands/
  SHOP.md                     NORTHING STUDIO: shop identity, support contact (M2), licensor, owner notes
  licences/personal.md        licence templates (shop-level; the shop is the licensor)
  licences/practitioner.md
  quiet-compass/
    brand-kit.md              moved from Product Plans/brand-kit.md (changelog entry added)
    voice.md                  NEW, locked ground truth
    fonts/                    moved from Products/_assets/fonts (HTML links updated → rebuild)
    artboard.css              moved from Products/_assets
catalogue.md                  live products only: id · line · name · platform · url · price · formats · interaction
OUTCOMES.md                   product · line · niche · date_listed · platform · views_14d · favourites_14d · sales_14d · views_30d · favourites_30d · sales_30d · notes
```
- **Rename cleanup:** `Products/_assets/product-base.css` stays (page system, not brand). Stale
  "Quiet Compass is [Assumption]" lines go (builder.md:138, PB-006 `product.css:5`). Dist
  filenames stay `NorthingStudio_…`, and builder.md:47 is corrected to match.
- **`voice.md`:**
  - **Sentence rhythm:** short declaratives, one idea each, and a concrete number over an
    adjective.
  - **Anti-motivational stance:** "not an app, nothing here reminds you".
  - **Evidence over encouragement:** "a bad week is data".
  - **Banned words:** mirrors `banned.json`.
  - **Worked examples:** 10 on-voice lines quoted from PB-001, PB-006 and PB-022, each paired with
    a rewritten off-voice version and the rule it breaks.
- **Enforcing `voice.md`:**
  - `banned.json` gets a `voice` category of measurable violations: exclamation marks, "you
    deserve", "journey", "unlock", "level up", urgency.
  - `banned_terms.py` (not frozen) runs it on `new-copy.md` and all copy.
  - A consistency test fails if a banned word in `voice.md` is missing from `banned.json`.
  - Anything not measurable is judged by the critic under Copywriting and cited to a `voice.md`
    rule.
- **Who reads `voice.md`:** the planner, builder and listing-creator. The builder's rule becomes
  "a new sentence in `new-copy.md` must cite the voice rule it satisfies".
- **`OUTCOMES.md`:** Gumroad has no favourites, so that column reads `n/a`. With no rows, agents
  must say "no outcome data yet". They never estimate.

### Phase 3 — Release gate, tablet, interaction, licences (D14–18, E19–20, I29)

**`scripts/release_check.py`** runs after the critic's final round and before `pdf-protect`.
It runs again in `--listing` mode after listing and pins are made. It writes
`qa/release-check.json` and exits 1 on any failure.

| # | Check (per edition, never once per product) |
|---|---|
| 14 | Every URL resolves. URLs come from PDF link annotations, **bare domains and emails in extracted text**, README and listing copy. HEAD then GET, 3 retries, 2xx/3xx pass. `.example/.test/.invalid`, placeholders like `<…>` and unresolvable `mailto:` domains fail. etsy.com needs API verification (conflict 18). |
| 15 | Every product name or URL referenced in copy must match a `catalogue.md` row. Names are matched against all spec titles from the plan, so "The Balance Audit" is recognised as a product reference. |
| 16 | Every format named on the cover (page 1 text), in README and in `listing.json` (`--listing`) must match a shipped file of that size. Checked per format: "Letter" needs a Letter-sized PDF, not just any PDF. |
| 17 | No `PB-\d{3}` / `BN-\d{2}` in any customer-facing filename (dist, listing images, pins), or in PDF `/Title` metadata. |
| 18 | Cross-refs. The new spec section `## Cross-references` has `ref text → target page → target heading` (its table avoids the `\| # \|` header, so `spec_coverage.py` ignores it). For each edition, the page containing the ref text is found and the target page number checked for the heading. All "page N"/"p. N" strings in the text must be declared. Version/date stamps (`v\d+\.\d+ · YYYY-MM`) must match across all three PDFs and README. |
| 19 | Tablet: aspect ≠ A4's 1:1.414 (not just different mm), page size = tablet preset, MediaBox = CropBox = TrimBox, largest blank side margin ≤ 8% of width (raster-measured, per-spec override allowed), and every "from page N" / "page N" ref on a tablet page has a GoTo link resolving to page N. |
| 20 | Spec field `Interaction: fillable \| annotate-only` is required. README and `listing.json` must state the same. "fillable" requires AcroForm fields; "annotate-only" requires none. |
| — | Critic status: parses the latest `critique/round-N.md` header. Zero open BLOCKER/MAJOR, or each one marked accepted by you in `BUILD-LOG`. |

The JSON also stores **sha256 of every dist file**. The upload re-hashes and refuses if anything
changed after the check, which also confirms `pdf-protect` ran (every PDF must be encrypted).

**Licences** (`scripts/make_licence.py --tier personal|practitioner --product PB-0XX`)
- Renders `brands/licences/*.md` into `dist/licences/LICENCE.txt` and the README licence
  section.
- Practitioner output goes to `dist-practitioner/`: same protected PDFs, practitioner licence.
  It uploads to `deliverables/practitioner/`.
- The price is an `[Assumption]` until you set it (M3).

**Spec template** (`product-brief-format/SKILL.md`) gets three new required fields: `Font set`,
`Interaction`, and `## Cross-references`.

### Phase 4 — Drive delivery (B6–11)

**`scripts/upload_to_drive.py <local_dir> <drive_path> [--json out] [--public]`**
- Sets `RCLONE_CONFIG=$GDRIVE_CREDENTIALS`.
- **Refuses** if the variable is unset, the file is missing or inside the repo, or its permissions
  aren't 600.
- **Upload sequence, run in order:**
  1. `rclone sync` (replace, never duplicate; stale remote files removed).
  2. `rclone dedupe --dedupe-mode newest` as a safety net.
  3. `rclone check --one-way --download=false` (md5) **must report 0 differences**.
  4. `rclone lsjson -R` gives the file IDs, which become owner-only
     `https://drive.google.com/file/d/<id>/view` links. `--public` → `rclone link`.
  5. Writes the links JSON.
- **Any non-zero step exits 1** with rclone's stderr, and the build is not complete.

**`--product PB-0XX` mode**
- Refuses unless `qa/release-check.json` passes, dist hashes match it, every PDF is encrypted,
  and `SIGNOFF.md` exists (item 9).
- Stages into `Products/<PB>/.upload/` (gitignored):
  - `deliverables/`: dist/ plus practitioner/
  - `listing/`: `listing.json`, listing copy md, `slot-brief.md`, images, instruction PDF
  - `pinterest/`: pins plus `pins.json`
  - `qa/`: SIGNOFF.md, `pages/**`, `*.json`, `critique/*.md`
- Syncs the staged folders to `Northing Studio/<PB-ID>_<Product-Name>/…`. The Drive folder name
  uses the PB-ID because it's internal; the SKU check covers the files inside.
- **Never uploads unless its gate passed.** `--stage build` uploads deliverables and qa;
  `--stage listing` uploads listing and pinterest.
- `--research` syncs `research/` reports and `buyer-complaints.md` to `Northing Studio/research/`.
- `--pull-inputs` copies `research/input/` down to `data/research-input/`.

**SIGNOFF (items 10/11)**
1. SIGNOFF is written.
2. Upload runs, then `append_drive_links.py` adds a final `## Drive links` section from the
   upload JSON only.
3. SIGNOFF is re-uploaded and verified.

It also contains `## Owner checks (not verifiable here, agents may not tick)` with unticked
`[ ]` boxes: print it, write on it with a pen, test the tablet PDF in GoodNotes, test it in
Notability. `release_check --signoff` fails if an agent ticked any of them.

**`.gitignore`** gains: `.venv/`, `.upload/`, `data/research-input/`, `*.rclone.conf`,
`rclone.conf`, `*service-account*.json`, `*credentials*.json`, `.env`.

### Phase 5 — Agents, commands, research, listing (F21–23, H25, I26–28)

**Tool lists** (frontmatter):

| Agent | Tools |
|---|---|
| niche-scout (NEW) | Read, Write, Edit, Bash, WebSearch, WebFetch |
| digital-product-researcher | Read, Write, Edit, Bash, WebSearch, WebFetch |
| product-planner | Read, Write, Edit, Bash, WebSearch, WebFetch |
| product-builder | Read, Write, Edit, Bash |
| product-critic | Read, Write, Bash, WebSearch |
| listing-creator | Read, Write, Edit, Bash, WebSearch |
| pinterest-creator (NEW) | Read, Write, Edit, Bash |

Every body that assumed Grep/Glob is changed to use `ls`/`find` through Bash, or given exact paths.

**niche-scout** (`.claude/agents/niche-scout.md`, runs above the researcher, command `/scout-niche`)
- **Reads `OUTCOMES.md` first.**
- `scripts/niche_metrics.py` validates the CSVs and computes every number. It **exits 1 on a
  missing file, a missing column or a blank required cell**, and never substitutes defaults.
  An `export_date` older than 45 days is a warning.
- `data/research-input/keywords.csv` columns: `niche, keyword, platform, monthly_searches,
  competing_listings, avg_price_usd, source_tool, export_date`
- `data/research-input/competitors.csv` columns: `niche, platform, listing_url, shop, title,
  price_usd, review_count, rating_avg, est_monthly_sales, is_digital, source_tool, export_date`.
  `est_monthly_sales` may be blank; `review_count` stands in as transaction evidence.
- **Metrics per niche:**
  - **Competition density:** searches ÷ live listings.
  - **Price ceiling:** kill unless at least 3 digital listings at ≥ $10 show sales or reviews.
  - **Incumbent moat:** median review count of the top 10.
- **Judgement dimensions, each citing its rule:**
  - **Family depth:** free lead piece, 2 paid singles, a $50 bundle, named concretely.
  - **Brand fit:** against `voice.md` and `brand-kit.md`; Quiet Compass or a new Northing line.
  - **Claim risk:** therapy, medical, financial or legal adjacency, checked against the
    `banned.json` unsafe_claims.
- **Output:** `research/niche-shortlist-YYYY-MM-DD.md`, a ranked top 3 with scores and a rejected
  table with **one kill reason each**. It is not a corpus. Uploaded via `--research`.

**digital-product-researcher**
- Remove the Gumroad-only banner and the `ETSY_ENABLED` guard (`etsy.py:459-460`). Etsy and
  Gumroad both run again.
- Pick one report path (`Research Reports/YYYY-MM-DD Digital Product Research Report.md`); today
  there are three.
- Takes the chosen niche from the shortlist.
- **New output `research/buyer-complaints.md`:**
  - 1–3★ reviews of comparable products, grouped into themes `BC-01…`.
  - Each theme has: its dimension (one of the 9), review count (n ≥ 3 or marked *weak*), up to 3
    quotes of ≤ 25 words with source URL, star rating and date, and a **checkable test** (e.g.
    "BC-04 · Print & production · lines too narrow to write on · test: writing bands ≥ 7.5 mm,
    measured").

**product-critic + `product-qa/SKILL.md`**
- The 9 dimensions stay.
- Each dimension's rubric becomes the list of `BC-xx` tests mapped to it, plus the existing
  measured gates. Generic heuristics only apply where no complaint covers them, and are labelled
  "judgement, not evidence".
- Every score cites which BC tests passed or failed.
- The critic renders **all three editions** to `qa/critic-pages/<edition>/`; only A4 is rendered
  today.
- `critique/round-N.md` must contain a `## Pages opened` table listing every PNG. The orchestrator
  and `release_check` compare it with the render manifests, so a missing page fails the round.

**listing-creator**
- **Phase A — slot brief** (`Listing/slot-brief.md`):
  - Slot 1 hero: formats, page count, "undated", all from dist facts.
  - Slot 2: an interior decision page.
  - Slot 3: the charter/output page.
  - Slots 4–10: the rest. Minimum 8 slots; a slot is N/A only with a reason.
  - Every slot names its **exact source**: edition PDF plus page number plus PNG path.
- `scripts/check_slot_brief.py` verifies each source page exists in dist and that slot 1's claims
  match the shipped files.
- The brief uploads to Drive `listing/`, and the command **stops**.
- **Phase B** only runs after you approve in the session. The orchestrator writes
  `Listing/slot-brief.APPROVED` holding the brief's sha256; images are refused if the brief
  changed after approval.
- The slot tables in `listing-images/SKILL.md` and `product-brief-format/SKILL.md` (which
  disagree today) are replaced by this order.

**pinterest-creator** (new agent plus `pinterest-pins` skill, runs after brief approval)
- Makes 5 pins at 1000×1500, built only from real rendered pages (new `.art--pin` in
  `artboard.css`, rendered via `render_artboard.py`).
- Writes `pins.json` with a title, description, alt text and a destination URL (which must be a
  `catalogue.md` live URL) for each pin.
- `scripts/check_pins.py` checks size, count = 5, a real source page for each, banned/voice terms,
  and character limits (title ≤ 100, description ≤ 500; I'll re-check Pinterest's current limits
  when implementing). Pin URLs go through `release_check --listing`.

**Commands**

| Command | Status | Flow |
|---|---|---|
| `/scout-niche` | NEW | `git pull` → `upload --pull-inputs` → niche-scout → upload `--research` |
| `/research` | NEW | researcher → upload `--research` |
| `/build-product` | edited | **Preflight:** `setup.sh --check`, `buyer-complaints.md` exists, `.venv`. **Build:** the unchanged ≤ 3-round loop. **Release:** `release_check` → `pdf-protect` → SIGNOFF → `upload --stage build` → append links → re-upload SIGNOFF. **Report:** Drive links from the JSON only. |
| `/list-product` | NEW | listing copy + slot brief → upload brief → **STOP** for approval → images + pins (parallel agents) → `check_listing` + `check_pins` + `release_check --listing` → `upload --stage listing` → append links. |

`check_listing.py` (not frozen) gets per-format page-count checks: each claimed format must match
its own file and page count.

### Phase 6 — Docs
Rewrite `README.md`: Linux requirements, `setup.sh`, the full chain from niche-scout to Drive,
manual steps M1–M6, and the Drive layout. Update the tables and diagram in
`product-build-loop/SKILL.md` for release_check and upload, leaving the round protocol text
unchanged.

---

## Verification

1. **Setup.** `scripts/setup.sh` twice; the second run makes no changes. Exits 0, or 2 only
   because Drive isn't configured. Then `google-chrome-stable --version`, `pdftoppm -v`,
   `rclone version`, `fc-list | grep -E "Fraunces|Source Sans 3|IBM Plex Mono"`.
2. **Smoke test.**
   - `build_pdf.py` on `Products/_smoke`, then `verify_pdf.py --fonts …` passes, with a report
     showing the tablet page at 428.6×571.5 mm.
   - Negative test: temporarily point the HTML at a missing `fonts.css`. verify must FAIL naming
     the DejaVu substitute.
   - Negative test: `PATH` without `pdftoppm`. `render_pages` and `verify_pdf` must exit 1.
3. **Release gate negative tests** on scratch copies, each expected to FAIL with the right
   message:
   - PB-006 dist (`northingstudio.example`)
   - PB-022 (Balance Audit upsell, placeholder support contact)
   - a dist file renamed to `PB-022_x.pdf`
   - a tablet PDF replaced by the A4 file
   - a cross-ref edited to the wrong page
   - a spec missing `Interaction`
4. **Drive** (after M1).
   - `upload_to_drive.py` on a scratch folder to `Northing Studio/_selftest`, run **twice**:
     `rclone lsjson` shows one copy of each file, and `check` reports 0 differences.
   - Negative test: a bad `GDRIVE_CREDENTIALS` exits 1 with the rclone error.
   - `--product PB-022` before release: refused.
5. **Agents.** Spawn each agent with a probe ("list your tools and your preloaded skills; do
   nothing else"). This confirms the frontmatter took effect in 2.1.270 and that no Grep/Glob
   is left.
6. **Niche-scout.** With `data/research-input/` empty it must fail naming the missing file. With a
   two-niche sample CSV it must produce 3-or-fewer ranked niches, each with a kill reason, and
   numbers matching `niche_metrics.py` output.
7. **End to end.** `/build-product PB-022` continues at round 2 once research exists. Expected
   result: **release_check FAILS** (upsell, support contact, tablet margins) and nothing uploads.
   That's correct until the spec changes in conflicts 4 and 6 are made.

---

## Implementation notes (2026-09-13)

What changed from the approved plan while building it, and why:

1. **pypdf is pinned at 6.16.1** (`scripts/requirements.txt`). pypdf 6.16.2 and later extract letter-spaced text as
   single letters, which falsely trips the split-text gate and would break `spec_coverage.py` and the release check's
   text matching. Bisected version by version on the shipped PB-022 file.
2. **Google Chrome installs from Google's own .deb** rather than a hand-written `signed-by` source. The .deb adds
   Google's signed apt repository itself; a second source line conflicts with it.
3. **Drive scope is full `drive`, not `drive.file`** (M1 corrected above). `drive.file` cannot see the CSVs you
   upload by hand to `research/input/`.
4. **New spec fields:** `**Protection:**` (a free lead magnet may declare `none`; the existing pdf-protect rule keeps
   freebies unprotected, and the upload gate honours it) and `**Practitioner licence:** yes | no`. Both are added to
   PB-006 and PB-022 alongside `Interaction`, `Font set` and `## Cross-references`. The five unbuilt specs still need
   them from the planner; `/build-product` stops until they are there.
5. **Cross-references have an Editions column**, so tablet-only navigation ("p. 3" chevrons) is not demanded of the
   paper editions.
6. **Pins may carry `pending-own-listing`** as their destination until the product's own listing is live; any other
   non-live destination fails.
7. **`check_pins.py`** lives in the new `pinterest-pins` skill; the other release scripts are in `scripts/`.
8. **niche-scout's density and moat thresholds** are starting values marked `[Assumption]`, to recalibrate once
   `OUTCOMES.md` has rows. The $10+ price-ceiling kill is exact.
9. **Ink drift (Mac `sips` → Linux poppler)** is up to ±0.75 pp on PB-006/PB-022, beyond the ±0.3 pp the plan
   mentioned. Nothing changes pass/fail (all pages ≤4.2% against an 8% limit), so thresholds were not retuned;
   the numbers are appended to both BUILD-LOGs.
10. **The link checker uses a plain tool user agent** (`NorthingStudio-release-check/1.0`). Some sites stall
    browser-looking agents from datacenter IPs.
11. **The working copy was deleted from the server at about 01:53 UTC on 2026-09-13**, cause unknown (no command in
    this session removed it). Everything was rebuilt from the session record into a fresh clone. Nothing is
    committed or pushed; that stays the owner's call.
