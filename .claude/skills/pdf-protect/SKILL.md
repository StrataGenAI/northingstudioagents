---
name: pdf-protect
description: Apply copy protection and document metadata to a finished product PDF — blocks copy/paste, editing and page extraction while keeping printing, tablet annotation and screen-reader access working. Use as the last step before a digital product ships, and to check what protection an existing PDF carries.
---

# PDF copy protection

## Say what this is, honestly

PDF permissions are enforced by the **reader**, not by cryptography the buyer
cannot bypass. The file opens without a password, so a determined person with the
right tool can strip the flags in seconds.

What it actually buys us:

- casual copy-paste of our copy into someone else's product stops working
- the file cannot be edited or re-assembled in ordinary tools
- our authorship and intent are recorded in the document itself

**Never** write "copy-proof", "cannot be copied", "DRM protected" or "piracy
proof" in a listing, a README or an image. Claiming uncopyable protection we do
not have is a false statement about the product. If the owner wants stronger
deterrence, the honest options are per-buyer stamping (the buyer's email set into
the footer at purchase time) and watermarked free samples — not stronger claims.

## Use it

```bash
S=.claude/skills/pdf-protect/scripts

# printable editions: print freely, copy nothing
python3 $S/protect_pdf.py "…/dist/QuietCompass_Focus-Audit_A4.pdf" \
  --edition print --title "The Focus Audit" --author "Quiet Compass" \
  --subject "A 7-day focus audit workbook" --owner-pass "$QC_OWNER_PASS"

# tablet edition: same, but annotation and form filling stay on
python3 $S/protect_pdf.py "…/dist/QuietCompass_Focus-Audit_Tablet.pdf" --edition tablet …

# check any PDF
python3 $S/protect_pdf.py "…/dist/…_A4.pdf" --verify-only
```

| Edition | Allowed | Denied |
|---|---|---|
| `print` | printing at full resolution, screen-reader text | copy/extract, editing, annotation, page assembly |
| `tablet` | printing, screen-reader text, **annotation, form filling** | copy/extract, editing, page assembly |

## Rules

1. **Protect last.** Encryption must come after every build and QA step —
   `verify_pdf.py` and `spec_coverage.py` read the PDF, and re-encrypting an
   already-encrypted file fails. Order: build → verify → QA → protect → ship.
2. **Tablet editions must stay annotatable.** The product promises GoodNotes and
   Notability support; `--edition print` on a tablet file breaks that promise.
   Test on a real device before claiming compatibility.
3. **Keep the accessibility path open.** `--deny-accessibility` blocks screen
   readers. Do not use it: it excludes disabled buyers to stop copying that a
   screenshot defeats anyway.
4. **Store the owner password.** Set `QC_OWNER_PASS` in the environment and reuse
   it for the whole catalogue, or the file can never be edited again. If the
   script generates one, save it before the terminal scrollback is gone.
5. **Free lead magnets stay unprotected** unless the owner asks otherwise —
   friction on a free file costs more in shares than it saves in copying.
6. Re-run `--verify-only` after protecting and paste the output into the QA
   record. "Protected" is a claim; the verify output is the evidence.
