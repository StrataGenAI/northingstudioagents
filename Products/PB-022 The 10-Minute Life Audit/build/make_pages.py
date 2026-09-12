#!/usr/bin/env python3
"""Compose a4.html, letter.html and tablet.html for PB-022.

Why a generator rather than three hand-typed files: every prompt, label and
sentence the buyer reads is defined ONCE, in COPY below, straight from
`Product Plans/specs/PB-022 The 10-Minute Life Audit.md`. Three hand-kept copies
of the same paragraph is exactly how a paraphrase creeps into one edition and
not the others. The layouts are still genuinely per-edition: page 2's scoring
row and page 3's wheel are built differently for A4 and for the shorter Letter
and tablet sheets (see `row()` and `SHEETS`).

Run:  python3 build/make_pages.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wheel as wheel_mod                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# COPY — every string below is verbatim from the build spec. Do not improve it.
# Additions that are not in the spec are marked ADDED and justified, one bullet
# each, in build/new-copy.md.
# ---------------------------------------------------------------------------
BRAND = "Northing Studio"          # [Assumption] pending owner confirmation
TITLE = "The 10-Minute Life Audit"

COPY = {
    "p1_kicker": "NORTHING STUDIO · FREE AUDIT",
    "p1_title": TITLE,
    "p1_accent": "A clear picture, then one small move.",
    "p1_body": ("Eight areas. One score each. Ten minutes. You’ll end up with a "
                "number, a picture, and one thing to do this week — which is more "
                "than most of us start the month with."),
    "p1_howto_label": "How to score",          # ADDED - see new-copy.md
    "p1_howto": ("Score each area 0–10 for <strong>how it is right now</strong>, not "
                 "how it should be and not how it was last year. First instinct. "
                 "Don’t average your whole life into a 7."),
    "p1_box": ("This is a structured self-reflection tool. It is not a diagnosis, an "
               "assessment or therapy. If something here worries you, talk to someone "
               "qualified — that is a strong move, not a weak one."),
    # ADDED. "print + tablet" added in round 2: the package ships a tablet
    # edition with 6 working internal links, and the strip is the one line in
    # the product that tells the buyer what they got. Every figure is measured
    # from the built files.
    "p1_spec_strip": ("4 pages · 8 areas · 10 minutes · A4 + Letter · "
                      "print + tablet · undated"),

    "p2_kicker": "STEP ONE · SCORE",
    "p2_title": "Where things actually are",
    "p2_why": "Why that number?",
    "p2_footnote": ("Money here is about how you <em>feel</em> about your money, not "
                    "advice about it. This is not financial advice."),

    "p3_kicker": "STEP TWO · SEE IT",
    "p3_title": "Your wheel",
    "p3_instruction": ("Mark each score on its spoke, then join the marks. Shade it in "
                       "if you like. The shape matters more than the numbers — "
                       "you’re looking for the dents."),
    "p3_f1": "Lowest area:",
    "p3_f2": "Highest area:",
    "p3_f3": "The one that surprised me:",
    "p3_closing": "A dented wheel is normal. A dent you’ve named is workable.",

    "p4_kicker": "STEP THREE · MOVE",
    "p4_title": "One small move",
    "p4_body": ("Take your lowest area — or the one that surprised you, which is "
                "often the real answer. Don’t fix it. Just make one move this week."),
    "p4_panel_kicker": "IF YOU WANT MORE",
    "p4_sell": ("This audit gives you the picture. <strong>The Balance Audit</strong> "
                "gives you the rest of the method: guided questions for all eight areas "
                "so the scores are honest, a gap map, three standing rules, a 30-day "
                "plan, and twelve monthly re-scores so you can watch the shape change."),
    "p4_limit": ("This free audit is complete as it is — the paid one goes deeper, "
                 "it doesn’t unlock this."),
}

# The eight areas and their clarifying lines, verbatim from the spec's page 2 row.
AREAS = [
    ("Health", "Energy, sleep, movement, how your body feels day to day.", False),
    ("Work", "What you spend your working hours on, and whether it’s going somewhere.", False),
    ("Money", "How settled you feel about what comes in and goes out.", True),
    ("People", "The relationships you’d miss if they went quiet.", False),
    ("Home", "The space you live in, and whether it rests you or drains you.", False),
    ("Growth", "Learning, skill, the sense of getting better at something.", False),
    ("Play", "Fun that isn’t productive. Rest that isn’t recovery from work.", False),
    ("Direction", "Whether your days point somewhere you chose.", False),
]

# The five fields on page 4: (lead-in sentence or None, label, ruled lines).
# The spec allows 1-2 lines each. Two lines each, the top of that range: at one
# line per field the column stranded ~38 mm dead bands between questions, and one
# short rule is not enough room to answer "one move I'll make this week".
#
# The last entry is the spec's "Re-score in 30 days. Date to re-score:" split at
# its own full stop into the instruction and the label it introduces. The words
# are untouched; only the typesetting changes. Set as one string it rendered as
# RE-SCORE IN 30 DAYS. DATE TO RE-SCORE: - a two-sentence instruction in
# letter-spaced uppercase mono, which brand-kit.md reserves for "a number, a code
# or a label", and which shouts at the foot of the calmest page in the kit.
MOVES = [
    (None, "The area I’m picking:", 2),
    (None, "One move I’ll make this week:", 2),
    (None, "When, exactly:", 2),
    (None, "How I’ll know I did it:", 2),
    ("Re-score in 30 days.", "Date to re-score:", 2),
]

# ---------------------------------------------------------------------------
# Devices — our own drawings, inline SVG, no fills, 1.25 pt strokes.
# ---------------------------------------------------------------------------
COMPASS_COVER = """<svg class="device device--cover" viewBox="0 0 120 120" aria-hidden="true">
      <circle cx="60" cy="60" r="46" fill="none" stroke="var(--primary)" stroke-width="1.4"/>
      <circle cx="60" cy="60" r="34" fill="none" stroke="var(--stone)" stroke-width="1"/>
      <path d="M60 8 L60 20 M60 100 L60 112 M8 60 L20 60 M100 60 L112 60"
            stroke="var(--primary)" stroke-width="1.4" stroke-linecap="round"/>
      <path d="M60 26 L74 60 L60 94 L46 60 Z" fill="none"
            stroke="var(--primary)" stroke-width="1.4" stroke-linejoin="round"/>
      <circle cx="60" cy="26" r="4" fill="var(--accent)"/>
    </svg>"""

COMPASS_MINI = """<svg class="compass-mini" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9.2" fill="none" stroke="var(--primary)" stroke-width="1.25"/>
      <path d="M12 5 L15 12 L12 19 L9 12 Z" fill="none" stroke="var(--primary)"
            stroke-width="1.25" stroke-linejoin="round"/>
    </svg>"""


def scale_strip():
    """The 0-10 strip: eleven rings, each big enough to circle with a real pen."""
    return ('<span class="scale">'
            + "".join(f"<i>{n}</i>" for n in range(11))
            + "</span>")


def row(name, note, footnote, edition):
    """One scoring row.

    A4 has the sheet height to stack the "why" rule under the full width of the
    row. Letter and tablet are ~18 mm shorter, so they use their extra width and
    tuck the "why" rule under the area name, beside the scale strip.
    """
    fn = f'<span class="fn">{DAGGER}</span>' if footnote else ""
    why = ('<div class="arow-why"><span class="label">' + COPY["p2_why"]
           + '</span><span class="rule"></span></div>')
    ident = (f'<div class="arow-id"><p class="arow-name">{name}{fn}</p>'
             f'<p class="arow-note">{note}</p>')
    if edition == "a4":
        return (f'<div class="arow">'
                f'<div class="arow-top">{ident}</div>{scale_strip()}</div>'
                f'{why}</div>')
    return (f'<div class="arow"><div class="arow-top">{ident}{why}</div>'
            f'{scale_strip()}</div></div>')


# Page-to-page navigation, digital editions only. The wording matches the
# spec's "Links (digital)" column. Held as constants because a backslash escape
# is not allowed inside an f-string expression before Python 3.12.
# (label, destination page). Rendered as real <a href="#pN"> anchors so the
# tablet PDF carries actual link annotations - a <span> looks identical on
# screen and produces nothing a reader can tap.
NAV = {
    1: [("→ p. 2", 2)],
    2: [("← p. 1", 1), ("→ p. 3", 3)],
    3: [("← p. 2", 2), ("→ p. 4", 4)],
    4: [("← p. 3", 3)],
}
DAGGER = "†"


def runfoot(page_no, nav, digital):
    if digital:
        links = " · ".join(
            f'<a class="navlink" href="#p{dest}">{label}</a>' for label, dest in nav)
        nav_html = f'<span class="foot-r">{links}</span>'
    else:
        nav_html = '<span class="foot-r"></span>'
    return (f'<div class="runfoot"><span class="foot-l">{COMPASS_MINI}</span>'
            f'<span class="foot-c">{page_no}/4</span>{nav_html}</div>')


def runhead():
    return f'<div class="runhead"><span>{BRAND}</span><span>{TITLE}</span></div>'


def anchor(page_no, digital):
    return f' id="p{page_no}"' if digital else ""


# ---------------------------------------------------------------------------
def page1(edition, digital):
    return f"""
<section class="page page--cover"{anchor(1, digital)}>
 <div class="sheet">
  <p class="kicker">{COPY['p1_kicker']}</p>
  <h1>{COPY['p1_title']}</h1>
  <p class="accent-line">{COPY['p1_accent']}</p>
  <p class="lede">{COPY['p1_body']}</p>
  <p class="kicker howto">{COPY['p1_howto_label']}</p>
  <p class="lede">{COPY['p1_howto']}</p>

  <div class="fill wheel-wrap">
    {COMPASS_COVER}
  </div>

  <div class="box tint mb-4">
    <p class="mb-0">{COPY['p1_box']}</p>
  </div>
  <p class="spec-strip mb-4">{COPY['p1_spec_strip']}</p>
  {runfoot(1, NAV[1], digital)}
 </div>
</section>"""


def page2(edition, digital):
    rows = "\n    ".join(row(n, d, f, edition) for n, d, f in AREAS)
    return f"""
<section class="page"{anchor(2, digital)}>
 <div class="sheet">
  {runhead()}
  <p class="kicker">{COPY['p2_kicker']}</p>
  <h2>{COPY['p2_title']}</h2>

  <div class="areas">
    {rows}
  </div>

  <p class="footnote"><span class="fn">†</span> {COPY['p2_footnote']}</p>
  {runfoot(2, NAV[2], digital)}
 </div>
</section>"""


def page3(edition, digital):
    fields = "\n    ".join(
        f'<div class="field"><span class="label">{dot}{label}</span>'
        f'<span class="rule"></span></div>'
        for label, dot in (
            (COPY["p3_f1"], '<span class="brass-dot"></span>'),
            (COPY["p3_f2"], ""),
            (COPY["p3_f3"], ""),
        ))
    return f"""
<section class="page"{anchor(3, digital)}>
 <div class="sheet">
  {runhead()}
  <p class="kicker">{COPY['p3_kicker']}</p>
  <h2>{COPY['p3_title']}</h2>

  <div class="fill wheel-wrap">
    {wheel_mod.build(False)}
  </div>
  <p class="instruction">{COPY['p3_instruction']}</p>

  <div class="wheel-fields">
    {fields}
  </div>
  <p class="closing">{COPY['p3_closing']}</p>
  {runfoot(3, NAV[3], digital)}
 </div>
</section>"""


def movefield(lead, label, n):
    """One page-4 answer field.

    `lead` is an instruction sentence that introduces the label rather than being
    part of it. It is set on its own line in sans sentence case, above the mono
    label, so an instruction never renders as a letter-spaced uppercase shout.
    """
    lines = '<span class="lines">' + "<i></i>" * n + "</span>"
    if lead:
        return (f'<div class="field field--instr">'
                f'<span class="lead-in">{lead}</span>'
                f'<span class="label">{label}</span>{lines}</div>')
    return f'<div class="field"><span class="label">{label}</span>{lines}</div>'


def page4(edition, digital):
    """Intro band (action block beside the stone panel), then full-width fields.

    Round 1 stacked the fields inside the left column and stretched the panel to
    match, which is what produced the 173.3 mm void inside the panel. Neither
    element is stretched now: the band is as tall as the taller of its two
    columns, and the writing space takes the rest of the sheet at full width.
    """
    fields = "\n      ".join(movefield(lead, label, n) for lead, label, n in MOVES)
    return f"""
<section class="page"{anchor(4, digital)}>
 <div class="sheet">
  {runhead()}
  <div class="move-grid">
    <div class="move-intro">
      <p class="kicker">{COPY['p4_kicker']}</p>
      <h2>{COPY['p4_title']}</h2>
      <p class="mb-0">{COPY['p4_body']}</p>
    </div>

    <aside class="panel panel--stone tint">
      <p class="kicker">{COPY['p4_panel_kicker']}</p>
      <p class="sell">{COPY['p4_sell']}</p>
      <p class="limit">{COPY['p4_limit']}</p>
    </aside>
  </div>

  <hr class="rule-accent">
  <div class="move-fields">
      {fields}
  </div>

  <p class="disclaimer-foot">{COPY['p1_box']}</p>
  {runfoot(4, NAV[4], digital)}
 </div>
</section>"""


SHEETS = {
    # edition -> (body class, note)
    "a4": "size-a4 print-build ink-light",
    "letter": "size-letter print-build ink-light",
    "tablet": "size-tablet ink-light",
}


def document(edition):
    digital = edition == "tablet"
    pages = "\n".join(fn(edition, digital) for fn in (page1, page2, page3, page4))
    return f"""<meta charset="utf-8">
<title>{TITLE} — {BRAND} — {edition.upper()}</title>
<link rel="stylesheet" href="../../_assets/fonts/fonts.css">
<link rel="stylesheet" href="../../_assets/product-base.css">
<link rel="stylesheet" href="product.css">
<!--
  PB-022 The 10-Minute Life Audit — {edition} edition.
  Generated by build/make_pages.py. Copy is verbatim from
  "Product Plans/specs/PB-022 The 10-Minute Life Audit.md"; additions are
  listed in build/new-copy.md.

  The device on page 3 is our own eight-area balance wheel (build/wheel.py).
  It is not the four-circle ikigai Venn, and the trademarked phrase for it
  appears nowhere in this product.
-->

<body class="{SHEETS[edition]}">
{pages}
</body>
"""


if __name__ == "__main__":
    for ed in ("a4", "letter", "tablet"):
        path = os.path.join(HERE, f"{ed}.html")
        open(path, "w", encoding="utf-8").write(document(ed))
        print(f"wrote {path} ({os.path.getsize(path):,} bytes)")
