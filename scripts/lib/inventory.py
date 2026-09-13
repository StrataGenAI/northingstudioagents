"""A content fingerprint of a deliverables folder.

release_check.py records it when the build passes; upload_to_drive.py takes it
again just before uploading and refuses if the content moved in between.
pdf-protect legitimately rewrites every PDF (encryption changes every byte), so a
PDF is compared by what a buyer gets - page count, page size and the text of every
page - while every other file is compared byte for byte.
"""
import hashlib
import os


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_fingerprint(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    encrypted = r.is_encrypted
    if encrypted:
        r.decrypt("")
    mb = r.pages[0].mediabox
    return {
        "encrypted": encrypted,
        "pages": len(r.pages),
        "size_pt": [round(float(mb.width), 2), round(float(mb.height), 2)],
        "page_text_sha256": [hashlib.sha256((p.extract_text() or "").encode("utf-8")).hexdigest()
                             for p in r.pages],
    }


def inventory(folder):
    out = {}
    for base, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            rec = {"sha256": sha256(path), "bytes": os.path.getsize(path)}
            if name.lower().endswith(".pdf"):
                rec.update(pdf_fingerprint(path))
            out[os.path.relpath(path, folder)] = rec
    return out


def content_changes(before, after):
    """What changed that a buyer would notice. Encryption alone is not a change."""
    diffs = []
    for rel in sorted(set(before) | set(after)):
        b, a = before.get(rel), after.get(rel)
        if b is None:
            diffs.append(f"{rel}: added after the release check")
        elif a is None:
            diffs.append(f"{rel}: removed after the release check")
        elif "pages" in b:
            if (b["pages"] != a.get("pages") or b["size_pt"] != a.get("size_pt")
                    or b["page_text_sha256"] != a.get("page_text_sha256")):
                diffs.append(f"{rel}: PDF content changed after the release check")
        elif b["sha256"] != a["sha256"]:
            diffs.append(f"{rel}: changed after the release check")
    return diffs
