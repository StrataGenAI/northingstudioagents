---
name: pdf-report
description: Turn a Markdown report into a polished, print-ready A4 PDF (cover page, table of contents, page numbers, styled tables, callout boxes, image galleries, hex colour swatches) using headless Chrome on the Linux server. Use whenever a report, brief, plan or instruction document must be delivered as PDF.
---

# PDF report

Write the report in Markdown, then convert it:

All finished research reports live in the project's **`Research Reports/`** folder, named `YYYY-MM-DD <Report name>.md` and `.pdf`. Plans live in `Product Plans/`; listing instructions in each product's `Listing/`.

```bash
PY=.venv/bin/python
$PY .claude/skills/pdf-report/scripts/md_to_pdf.py "Research Reports/2026-09-12 Digital Product Research Report.md" \
  --subtitle "Etsy & Gumroad competitor, design & product-opportunity research" \
  --author "Northing Studio research"
# -> "Research Reports/2026-09-12 Digital Product Research Report.pdf"  (prints page count + size)
```

**Requirements.** The headless Linux setup from `scripts/setup.sh`:
- **Chrome:** Google Chrome, driven by `scripts/lib/chromium.py`, which waits for `%%EOF` and never hangs on a stalled render.
- **Python:** `.venv` with `markdown`, `pypdf` and `Pillow`. Pillow downscales large images.

**Options:**

| Option | Effect |
|---|---|
| `-o out.pdf` | output path |
| `--title` | by default the first `# H1`, which moves to the cover page |
| `--subtitle`, `--author`, `--date` | cover text |
| `--no-cover`, `--no-toc` | drop the cover page or table of contents |
| `--css extra.css` | brand overrides |
| `--max-image 1400` | larger local images are downscaled into a temp-folder cache, so the report folder stays clean |
| `--keep-html` | keeps `*.print.html` for debugging |

## Markdown conventions

| Write this | You get |
|---|---|
| First line `# Report title` | cover page title |
| `# Section` (each H1 after the first) | starts a new page with a sage underline |
| `## Sub-section` / `### ...` | listed in the table of contents (H2 and H3) |
| `> [!IDEA] text` · `[!INSIGHT]` · `[!OPPORTUNITY]` · `[!WARNING]` · `[!NOTE]` · `[!TIP]` | coloured callout box |
| A paragraph with several images `![](a.jpg) ![](b.jpg) ![](c.jpg)` | 3-column image gallery |
| One image on its own line `![Caption](a.jpg)` | a figure, with the alt text as its caption |
| `` `#A3B18A` `` | colour swatch plus the hex code |
| `<!-- pagebreak -->` | forced page break |
| Standard tables | striped tables with a repeating header row; rows don't split across pages |
| GitHub-style lists (`-`, `1.`), including inside `>` callouts | the script adds the blank line before a list and re-indents 2–3-space nested items to 4 spaces. List markers must be a number or bullet: write `- p. 4–5: …`, not `4–5. …` |

Image paths are relative to the Markdown file, e.g. `assets/etsy/<seller>/<listing>/01.jpg` from inside `research/`. For contact sheets, use the `_sheet.png` files made by the `listing-image-audit` skill.

## Layout tips for research reports
- Keep tables to 6 columns or fewer on A4 portrait. Split wider tables, or move the long text into bullets under the table.
- Put the 3–6 most telling images in each seller profile as a gallery. Link the rest of the asset folder instead of embedding everything.
- Start every major section with an `[!INSIGHT]` callout of 1–3 sentences, so a reader skimming the PDF gets the key point.
- Use `[!IDEA]` / `[!OPPORTUNITY]` for product ideas, so they stand out.

## Verify before handing off
1. **Size.** The script prints the page count and file size. A 20-seller report with galleries is typically 40–120 pages and under 50 MB; if it's much bigger, lower `--max-image`.
2. **Text.**
   ```bash
   $PY -c "import pypdf;r=pypdf.PdfReader('X.pdf');print(r.pages[2].extract_text()[:800])"
   ```
3. **Look.** Rasterise a few pages, including the cover, and `Read` the PNGs:
   ```bash
   $PY .claude/skills/printable-pdf/scripts/render_pages.py X.pdf --out /tmp/report-check --pages 1,2,5 --width 1200
   ```
4. **Missing images.** The script prints `warning: image not found` for each one. Fix the paths and re-run.
