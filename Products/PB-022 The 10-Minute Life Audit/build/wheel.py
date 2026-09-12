#!/usr/bin/env python3
"""Generate the eight-area wheel master as inline SVG.

One unit in the viewBox == 1 mm when the SVG is rendered 164 mm wide, so the
outer ring is exactly 120 mm across (r = 60). PB-003 and PB-002 reuse this file
by scaling the rendered width; the geometry never changes.

This is NOT the four-circle ikigai Venn. The live US trademark covering this
kind of diagram (brand-kit.md, conflict-screen table) is banned outright: it
appears in no product file, file name, label, header or alt text. Ours is
"the eight-area wheel", or "the balance wheel diagram".
"""
import math

C = 82.0          # centre x and y
R = 60.0          # outer ring radius -> 120 mm across
RINGS = [12.0, 24.0, 36.0, 48.0, 60.0]        # scores 2/4/6/8/10
ODD_R = [6.0, 18.0, 30.0, 42.0, 54.0]         # tick marks at 1/3/5/7/9
TICK = 1.3        # half-length of an odd-score tick
VB = 164.0

# How far inside its own ring a scale number sits. 2.2 mm puts the number 2.2 mm
# from the ring it labels and 3.8 mm from the odd-score tick below it, so which
# one it belongs to is never in doubt.
NUM_INSET = 2.2

AREAS = ["Health", "Work", "Money", "People", "Home", "Growth", "Play", "Direction"]

# stroke widths, converted from points to mm (1 pt = 0.352778 mm)
PT = 0.352778
W_SPOKE = round(1.25 * PT, 3)     # 0.441 - diagram stroke, primary
W_HAIR = round(0.5 * PT, 3)       # 0.176 - hairline, stone

# label radius and text anchor per spoke index (N, NE, E, SE, S, SW, W, NW)
LABELS = [
    (66.0, "middle", 0.0),
    (64.0, "start", 1.2),
    (62.0, "start", 1.5),
    (64.0, "start", 1.2),
    (66.0, "middle", 3.2),
    (64.0, "end", 1.2),
    (62.0, "end", 1.5),
    (64.0, "end", 1.2),
]


def polar(r, deg):
    a = math.radians(deg)
    return C + r * math.cos(a), C + r * math.sin(a)


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def build(standalone):
    o = []
    if standalone:
        o.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(VB)} {f(VB)}" '
            f'width="164mm" height="164mm" role="img" '
            f'aria-label="Eight-area balance wheel: eight labelled spokes and five rings">'
        )
        o.append(
            "<style>\n"
            "  /* Single-sourced from brand-kit.md. Inline copies inherit these\n"
            "     from product-base.css instead of redeclaring them. */\n"
            "  :root { --ink:#1F2A36; --primary:#3E6B89; --accent:#D9A441;\n"
            "          --stone:#E4DCD0; --paper:#FBF8F3;\n"
            "          --sans:'Source Sans 3',sans-serif; --mono:'IBM Plex Mono',monospace; }\n"
            "</style>"
        )
    else:
        o.append(
            f'<svg class="wheel" viewBox="0 0 {f(VB)} {f(VB)}" role="img" '
            f'aria-label="Eight-area balance wheel: eight labelled spokes and five rings">'
        )

    # ---- rings (5 hairline stone, scores 2/4/6/8/10)
    o.append("  <!-- five rings: scores 2, 4, 6, 8, 10 -->")
    o.append(f'  <g fill="none" stroke="var(--stone)" stroke-width="{f(W_HAIR)}">')
    for r in RINGS:
        o.append(f'    <circle cx="{f(C)}" cy="{f(C)}" r="{f(r)}"/>')
    o.append("  </g>")

    # ---- odd-score ticks, so every integer 0-10 is findable with a pen
    o.append("  <!-- ticks at scores 1, 3, 5, 7, 9 -->")
    o.append(f'  <g stroke="var(--stone)" stroke-width="{f(W_HAIR)}" stroke-linecap="round">')
    for i in range(8):
        deg = -90 + 45 * i
        a = math.radians(deg)
        px, py = -math.sin(a), math.cos(a)      # unit perpendicular to the spoke
        for r in ODD_R:
            x, y = polar(r, deg)
            o.append(
                f'    <line x1="{f(x - TICK * px)}" y1="{f(y - TICK * py)}" '
                f'x2="{f(x + TICK * px)}" y2="{f(y + TICK * py)}"/>'
            )
    o.append("  </g>")

    # ---- the eight spokes
    o.append("  <!-- eight spokes -->")
    o.append(
        f'  <g stroke="var(--primary)" stroke-width="{f(W_SPOKE)}" stroke-linecap="round">'
    )
    for i in range(8):
        x, y = polar(R, -90 + 45 * i)
        o.append(f'    <line x1="{f(C)}" y1="{f(C)}" x2="{f(x)}" y2="{f(y)}"/>')
    o.append("  </g>")
    o.append(
        f'  <circle cx="{f(C)}" cy="{f(C)}" r="1.1" fill="var(--primary)"/>'
    )

    # ---- scale numbers, one column in EVERY wedge
    #
    # Round 1 numbered a single wedge (between the N and NE spokes). That made
    # seven of the eight spokes unmarkable without carrying a ring position
    # across a 120 mm circle by eye - the one task this page exists to support.
    # Every wedge now carries its own 2/4/6/8/10, so each spoke has a full scale
    # 22.5 degrees away on both sides instead of one scale up to 180 degrees away.
    #
    # The numbers sit just INSIDE the ring they label rather than on top of it.
    # Round 1 cut the ring with a paper-coloured backing rect; repeating that in
    # eight wedges would have broken the score-2 ring in eight places out of a
    # 75 mm circumference and left it barely readable. Set inside the ring, the
    # five rings stay unbroken circles - which also helps them survive greyscale.
    o.append("  <!-- scale numbers: a column per wedge, so no score is carried"
             " across the circle -->")
    # SVG font-size is in USER UNITS, and one user unit is 1 mm here - so a point
    # size must be converted or the label renders ~2.8x too big and overflows the
    # viewBox. 8.5 pt -> 3.0 units.
    o.append(f'  <g font-family="var(--mono)" font-size="{f(8.5 * PT)}"'
             ' fill="var(--primary)" text-anchor="middle">')
    for k in range(8):
        deg = -67.5 + 45 * k                  # the bisector of each wedge
        for r, lab in zip(RINGS, ["2", "4", "6", "8", "10"]):
            x, y = polar(r - NUM_INSET, deg)
            o.append(f'    <text x="{f(x)}" y="{f(y + 1.05)}">{lab}</text>')
    o.append("  </g>")

    # ---- the eight area labels
    o.append("  <!-- area labels, editable text -->")
    # 9.5 pt -> 3.35 user units. The spec asks for Source Sans 3 at 9 pt; 9.5 pt
    # keeps a margin over the 9 pt accessibility floor after rounding.
    o.append(f'  <g font-family="var(--sans)" font-size="{f(9.5 * PT)}" font-weight="600"'
             ' fill="var(--ink)" letter-spacing="0.055em">')
    for i, name in enumerate(AREAS):
        rl, anchor, dy = LABELS[i]
        x, y = polar(rl, -90 + 45 * i)
        o.append(
            f'    <text x="{f(x)}" y="{f(y + dy)}" text-anchor="{anchor}">'
            f"{name.upper()}</text>"
        )
    o.append("  </g>")
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    import sys
    standalone = "--standalone" in sys.argv
    out = build(standalone)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        open(sys.argv[1], "w", encoding="utf-8").write(out + "\n")
        print(f"wrote {sys.argv[1]} ({len(out)} bytes)")
    else:
        print(out)
