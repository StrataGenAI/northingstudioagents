#!/usr/bin/env python3
"""End SIGNOFF.md with the Drive links, taken only from the verified upload records.

  append_drive_links.py "Products/PB-022 The 10-Minute Life Audit"

Reads qa/drive-build.json (required) and qa/drive-listing.json (once the listing
stage has uploaded). Any earlier '## Drive links' section is replaced, and a fresh
one becomes the last section of SIGNOFF.md. A link that is not in an upload record
cannot appear here, so nobody can write in a link to a file that never uploaded.

Next: upload_to_drive.py --product "<product>" --stage signoff
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LIST_FILES = ("deliverables", "listing", "pinterest")   # qa/ is linked as a folder only


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pdir = os.path.abspath(sys.argv[1])
    signoff = os.path.join(pdir, "SIGNOFF.md")
    if not os.path.exists(signoff):
        sys.exit("FAIL: SIGNOFF.md is missing")
    records = []
    for stage in ("build", "listing"):
        path = os.path.join(pdir, "qa", f"drive-{stage}.json")
        if os.path.exists(path):
            records.append(json.load(open(path, encoding="utf-8")))
        elif stage == "build":
            sys.exit("FAIL: qa/drive-build.json is missing - the build has not been uploaded and verified")

    lines = ["## Drive links", "",
             "Uploaded with `scripts/upload_to_drive.py` and verified by hash (rclone check: 0 differences). "
             "Links open for the Drive owner only, unless a record says it was shared publicly.", ""]
    for rec in records:
        lines.append(f"Drive folder: `{rec['drive_folder']}/` (stage {rec['stage']}, {rec['uploaded_at']})")
        lines.append("")
        for key, res in rec["results"].items():
            lines.append(f"**{key}/** · [open folder]({res['folder']['url']}) · {len(res['files'])} file(s)"
                         + (" · shared publicly" if res.get("public") else ""))
            if key in LIST_FILES:
                lines += [f"- [{f['path']}]({f['url']})" for f in res["files"]]
            else:
                lines += [f"- [{f['path']}]({f['url']})" for f in res["files"] if f["path"] == "SIGNOFF.md"]
            lines.append("")

    text = open(signoff, encoding="utf-8").read()
    text = re.sub(r"\n##\s+Drive links\b.*\Z", "", text, flags=re.S).rstrip()
    open(signoff, "w", encoding="utf-8").write(text + "\n\n" + "\n".join(lines).rstrip() + "\n")
    print(f"SIGNOFF.md now ends with the Drive links from {len(records)} upload record(s).")
    print(f'Next: upload_to_drive.py --product "{os.path.relpath(pdir, ROOT)}" --stage signoff')
    return 0


if __name__ == "__main__":
    sys.exit(main())
