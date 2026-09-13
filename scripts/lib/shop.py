"""Shop-level facts the release scripts share: brands/SHOP.md, catalogue.md and the specs.

Nothing here guesses. A missing file or an unreadable field ends the run with the
reason, because every script that asks for a fact is about to put it in front of
a customer.
"""
import glob
import os
import re
import sys
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SPEC_TITLE = re.compile(r"^#\s+Build spec\s+[—–-]\s+((?:PB|BN)-\d{2,3})\s+(.+?)\s+\(v\d+\)\s*$", re.M)


def norm(s):
    """Fold quotes, dashes, spacing and case so PDF text, Markdown and JSON compare fairly."""
    s = unicodedata.normalize("NFKC", s or "")
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
          .replace("—", "-").replace("–", "-").replace(" ", " "))
    return re.sub(r"\s+", " ", s).strip().lower()


def shop_facts():
    """The key: value block in brands/SHOP.md. Empty values mean 'not decided'."""
    path = os.path.join(ROOT, "brands", "SHOP.md")
    if not os.path.exists(path):
        sys.exit("FAIL: brands/SHOP.md is missing")
    m = re.search(r"```\n(.*?)```", open(path, encoding="utf-8").read(), re.S)
    if not m:
        sys.exit("FAIL: brands/SHOP.md has no fenced block of shop facts")
    facts = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            facts[key.strip()] = value.strip()
    return facts


def load_catalogue():
    """Rows of catalogue.md's table, as dicts keyed by the header. Only live products."""
    path = os.path.join(ROOT, "catalogue.md")
    if not os.path.exists(path):
        sys.exit("FAIL: catalogue.md is missing")
    header, rows = None, []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            if cells and cells[0].lower() == "id":
                header = [c.lower() for c in cells]
            continue
        if re.fullmatch(r"\|[\s:|-]+\|", s):
            continue
        if any(cells):
            rows.append(dict(zip(header, cells)))
    if header is None:
        sys.exit("FAIL: catalogue.md has no table with an 'id' column")
    return rows


def product_id(product_dir):
    name = os.path.basename(os.path.normpath(product_dir))
    m = re.search(r"\b(PB-\d{3}|BN-\d{2,3})\b", name)
    if not m:
        sys.exit(f"FAIL: cannot read a PB-/BN- id from the folder name {name!r}")
    return m.group(1)


def find_spec(pb_id):
    hits = sorted(glob.glob(os.path.join(ROOT, "Product Plans", "specs", f"{glob.escape(pb_id)} *.md")))
    if len(hits) != 1:
        sys.exit(f"FAIL: expected exactly one spec for {pb_id} in Product Plans/specs/, found {len(hits)}")
    return hits[0]


def spec_identity(spec_path):
    m = SPEC_TITLE.search(open(spec_path, encoding="utf-8").read())
    if not m:
        sys.exit(f"FAIL: {spec_path} has no '# Build spec — PB-0XX <Name> (vN)' title")
    return m.group(1), m.group(2).strip()


def known_products():
    """Every product name the studio has planned: {name: id}.

    Taken from the spec titles and from the product plans' tables (an ID cell
    followed by a name cell starting with "The"), so a customer file that names a
    planned-but-unreleased product is recognised as naming a product.
    """
    names = {}
    for path in glob.glob(os.path.join(ROOT, "Product Plans", "specs", "*.md")):
        m = SPEC_TITLE.search(open(path, encoding="utf-8").read())
        if m:
            names[m.group(2).strip()] = m.group(1)
    for path in glob.glob(os.path.join(ROOT, "Product Plans", "*Product Plan.md")):
        for line in open(path, encoding="utf-8"):
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
            for i, cell in enumerate(cells[:-1]):
                if re.fullmatch(r"(?:PB|BN)-\d{2,3}", cell):
                    name = re.sub(r"\s*\(.*?\)\s*$", "", cells[i + 1]).strip().strip("*").strip()
                    if name.lower().startswith("the ") and 5 < len(name) < 60:
                        names.setdefault(name, cell)
    return names


def spec_field(spec_text, name):
    """The value of a '**Name:** value' line in a build spec, or None if absent."""
    m = re.search(r"^\s*(?:[-*]\s*)?\**%s:?\**:?\s*(.+?)\s*$" % re.escape(name), spec_text, re.M | re.I)
    return m.group(1).strip("`* ") if m else None
