#!/usr/bin/env python3
"""Upload to Google Drive with rclone: idempotent, verified, and never silent.

Credentials: an rclone config file at the path in $GDRIVE_CREDENTIALS. It must sit
outside the repository, have mode 600, and hold a remote named "northing"
(MULTI_AGENT_PLAN.md, step M1). Everything lands under the Drive folder
"Northing Studio/".

  upload_to_drive.py LOCAL_DIR DRIVE_PATH [--json out.json] [--public]
  upload_to_drive.py --product "Products/PB-022 The 10-Minute Life Audit" --stage build
  upload_to_drive.py --product "Products/PB-022 ..." --stage brief|listing|signoff
  upload_to_drive.py --research        # reports, buyer complaints, niche shortlists -> research/
  upload_to_drive.py --pull-inputs     # research/input/*.csv on Drive -> data/research-input/
  upload_to_drive.py --selftest        # credentials, then a write/read/delete probe

Every upload runs the same steps:
1. rclone sync (or copy). Re-running replaces files; it never duplicates them.
2. dedupe
3. rclone check against md5 hashes. It must report 0 differences.
4. list the Drive IDs
5. build the links

If any step fails, the script exits 1 with rclone's own error. A build whose upload
was not verified is not complete.

Links are owner-only drive.google.com URLs. --public turns on "anyone with the
link" for each file; never use it for paid files.

Product stages and what each one needs before it will upload:
  build     Uploads dist/ -> deliverables/, dist-practitioner/ -> deliverables/practitioner/,
            and SIGNOFF.md, qa/pages/, qa/*.json and critique/ -> qa/.
            Needs: qa/release-check.json passed (no open BLOCKER or MAJOR), the
            deliverables still match what that check measured, every PDF is
            protected (unless the spec says "**Protection:** none"), and SIGNOFF.md
            passes release_check --signoff.
  brief     Copies Listing/slot-brief.md -> listing/ for the owner to review.
  listing   Uploads the listing copy, images and instructions -> listing/, and
            Pinterest/ -> pinterest/.
            Needs: everything the build stage needs, plus release_check --listing,
            check_listing.py and check_pins.py all passed.
  signoff   Uploads SIGNOFF.md -> qa/ again, after append_drive_links.py has added
            the links. Needs: release_check --signoff --require-drive-links passed.
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lib import inventory, shop  # noqa: E402

REMOTE = os.environ.get("GDRIVE_REMOTE", "northing")
TOP = "Northing Studio"


def die(msg):
    print(f"\nFAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------ rclone
def credentials():
    path = os.environ.get("GDRIVE_CREDENTIALS")
    if not path:
        die("GDRIVE_CREDENTIALS is not set - Drive is not configured (MULTI_AGENT_PLAN.md, step M1)")
    path = os.path.realpath(os.path.expanduser(path))
    if not os.path.isfile(path):
        die(f"GDRIVE_CREDENTIALS points at {path}, which does not exist")
    if os.path.commonpath([path, ROOT]) == ROOT:
        die("the Drive credentials are inside the repository - move them out so they can never be committed")
    mode = stat.S_IMODE(os.stat(path).st_mode)
    if mode & 0o077:
        die(f"{path} can be read by other users (mode {mode:o}) - run: chmod 600 {path}")
    return path


def rclone(args, creds, input_text=None, check=True):
    exe = shutil.which("rclone")
    if not exe:
        die("rclone is not installed - run scripts/setup.sh")
    r = subprocess.run([exe, *args], env=dict(os.environ, RCLONE_CONFIG=creds),
                       capture_output=True, text=True, input=input_text)
    if check and r.returncode != 0:
        die(f"rclone {args[0]} failed (exit {r.returncode}):\n{(r.stderr or r.stdout).strip()[-2500:]}")
    return r


def remote(path=""):
    path = path.strip("/")
    return f"{REMOTE}:{TOP}" + (f"/{path}" if path else "")


def local_files(folder):
    return sorted(os.path.relpath(os.path.join(base, f), folder)
                  for base, _, files in os.walk(folder) for f in files)


def folder_id(drive_path, creds):
    parent, name = os.path.split(drive_path.strip("/"))
    target = remote(parent) if name else f"{REMOTE}:"
    name = name or TOP
    items = json.loads(rclone(["lsjson", "--dirs-only", target], creds).stdout or "[]")
    for item in items:
        if item.get("Name") == name and item.get("ID"):
            return item["ID"]
    die(f"uploaded, but Drive returned no folder ID for {target}/{name}")


def upload(local, drive_path, creds, mode="sync", public=False):
    """Upload a folder, verify it by hash, and return its links."""
    files = local_files(local) if os.path.isdir(local) else []
    if not files:
        die(f"nothing to upload in {os.path.relpath(local, ROOT)}")
    dest = remote(drive_path)
    print(f"  {mode:<4} {os.path.relpath(local, ROOT)}  ->  {dest}  ({len(files)} file(s))")
    rclone([mode, local, dest, "--checksum"], creds)
    rclone(["dedupe", "--dedupe-mode", "newest", dest], creds)
    check = rclone(["check", local, dest, "--one-way"], creds, check=False)
    if check.returncode != 0:
        die(f"the upload to {dest} did not verify - rclone check found differences:\n"
            f"{(check.stderr or check.stdout).strip()[-2500:]}")
    listed = {item["Path"]: item for item in
              json.loads(rclone(["lsjson", "-R", "--files-only", "--hash", dest], creds).stdout or "[]")}
    missing = [f for f in files if f not in listed]
    if missing:
        die(f"verified by hash, yet Drive does not list: {', '.join(missing[:10])}")
    out_files = []
    for rel in files:
        item = listed[rel]
        if not item.get("ID"):
            die(f"Drive returned no file ID for {rel}")
        url = f"https://drive.google.com/file/d/{item['ID']}/view"
        if public:
            url = rclone(["link", f"{dest}/{rel}"], creds).stdout.strip()
        out_files.append({"path": rel, "id": item["ID"], "url": url, "bytes": item.get("Size"),
                          "md5": (item.get("Hashes") or {}).get("md5")})
    fid = folder_id(drive_path, creds)
    return {"local": os.path.relpath(local, ROOT), "remote": dest,
            "folder": {"id": fid, "url": f"https://drive.google.com/drive/folders/{fid}"},
            "files": out_files, "public": public, "verified": "rclone check: 0 differences",
            "uploaded_at": now()}


# ------------------------------------------------------------------ product stages
def product_folder(pdir):
    pb_id = shop.product_id(pdir)
    _, name = shop.spec_identity(shop.find_spec(pb_id))
    return pb_id, name, f"{pb_id}_{re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-')}"


def passed(path, label):
    if not os.path.exists(path):
        die(f"{label} has not run ({os.path.relpath(path, ROOT)} is missing) - nothing uploads")
    data = json.load(open(path, encoding="utf-8"))
    ok = data["pass"] if "pass" in data else not data.get("fails")
    if not ok:
        fails = data.get("fails") or []
        die(f"{label} did not pass - nothing uploads:\n  " + "\n  ".join(str(f) for f in fails[:15]))
    return data


def gate_build(pdir):
    report = passed(os.path.join(pdir, "qa", "release-check.json"), "release_check.py")
    if report.get("mode") != "release":
        die("qa/release-check.json is not a default-mode release check")
    now_inv = inventory.inventory(os.path.join(pdir, "dist"))
    changes = inventory.content_changes(report.get("dist_inventory", {}), now_inv)
    if changes:
        die("the deliverables changed after the release check - re-run it:\n  " + "\n  ".join(changes))
    unprotected = [rel for rel, rec in now_inv.items() if rel.lower().endswith(".pdf") and not rec["encrypted"]]
    spec_text = open(shop.find_spec(shop.product_id(pdir)), encoding="utf-8").read()
    protection = (shop.spec_field(spec_text, "Protection") or "").lower()
    if unprotected and not protection.startswith("none"):
        die(f"not protected: {', '.join(unprotected)} - run pdf-protect before uploading "
            f"(only a spec declaring '**Protection:** none' ships unprotected, e.g. a free lead magnet)")
    if not os.path.exists(os.path.join(pdir, "SIGNOFF.md")):
        die("SIGNOFF.md is missing - it is written before the upload")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "release_check.py"), pdir, "--signoff",
                        "--json", os.path.join(pdir, "qa", "release-check-signoff.json")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        die("SIGNOFF.md does not pass release_check --signoff:\n" + r.stdout[-2000:])


def copy_into(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def stage_product(pdir, stage, creds, public):
    pb_id, name, folder = product_folder(pdir)
    staging = os.path.join(pdir, ".upload", stage)
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging)
    results = {}
    print(f"{pb_id} {name}: {stage} stage -> Drive '{TOP}/{folder}/'")

    if stage == "build":
        gate_build(pdir)
        copy_into(os.path.join(pdir, "dist"), os.path.join(staging, "deliverables"))
        copy_into(os.path.join(pdir, "dist-practitioner"), os.path.join(staging, "deliverables", "practitioner"))
        qa = os.path.join(staging, "qa")
        copy_into(os.path.join(pdir, "SIGNOFF.md"), os.path.join(qa, "SIGNOFF.md"))
        copy_into(os.path.join(pdir, "qa", "pages"), os.path.join(qa, "pages"))
        for j in glob.glob(os.path.join(glob.escape(pdir), "qa", "*.json")):
            copy_into(j, os.path.join(qa, os.path.basename(j)))
        copy_into(os.path.join(pdir, "critique"), os.path.join(qa, "critique"))
        results["deliverables"] = upload(os.path.join(staging, "deliverables"), f"{folder}/deliverables", creds,
                                         public=public)
        results["qa"] = upload(qa, f"{folder}/qa", creds, public=public)

    elif stage == "brief":
        brief = os.path.join(pdir, "Listing", "slot-brief.md")
        if not os.path.exists(brief):
            die("Listing/slot-brief.md is missing")
        copy_into(brief, os.path.join(staging, "slot-brief.md"))
        results["listing"] = upload(staging, f"{folder}/listing", creds, mode="copy", public=public)

    elif stage == "listing":
        gate_build(pdir)
        passed(os.path.join(pdir, "qa", "release-check-listing.json"), "release_check.py --listing")
        passed(os.path.join(pdir, "Listing", "qa", "listing.json"), "check_listing.py")
        passed(os.path.join(pdir, "Pinterest", "qa", "pins-check.json"), "check_pins.py")
        ldir = os.path.join(pdir, "Listing")
        listing = os.path.join(staging, "listing")
        for f in sorted(os.listdir(ldir)):
            if f.lower().endswith((".json", ".md", ".pdf")):
                copy_into(os.path.join(ldir, f), os.path.join(listing, f))
        copy_into(os.path.join(ldir, "images"), os.path.join(listing, "images"))
        pins = os.path.join(staging, "pinterest")
        pdir_pins = os.path.join(pdir, "Pinterest")
        for f in sorted(os.listdir(pdir_pins)):
            if f not in ("qa", "build"):
                copy_into(os.path.join(pdir_pins, f), os.path.join(pins, f))
        results["listing"] = upload(listing, f"{folder}/listing", creds, public=public)
        results["pinterest"] = upload(pins, f"{folder}/pinterest", creds, public=public)

    elif stage == "signoff":
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "release_check.py"), pdir, "--signoff",
                            "--require-drive-links",
                            "--json", os.path.join(pdir, "qa", "release-check-signoff.json")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            die("SIGNOFF.md does not end with verified Drive links:\n" + r.stdout[-2000:])
        copy_into(os.path.join(pdir, "SIGNOFF.md"), os.path.join(staging, "SIGNOFF.md"))
        results["qa"] = upload(staging, f"{folder}/qa", creds, mode="copy", public=public)

    record = {"product": os.path.relpath(pdir, ROOT), "pb_id": pb_id, "stage": stage,
              "drive_folder": f"{TOP}/{folder}", "results": results, "uploaded_at": now()}
    return record, os.path.join(pdir, "qa", f"drive-{stage}.json")


# ------------------------------------------------------------------ research, inputs, selftest
def stage_research(creds, public):
    staging = os.path.join(ROOT, ".upload", "research")
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging)
    for f in glob.glob(os.path.join(ROOT, "Research Reports", "*")):
        if f.lower().endswith((".md", ".pdf")):
            copy_into(f, os.path.join(staging, "reports", os.path.basename(f)))
    for pattern in ("buyer-complaints.md", "niche-shortlist-*.md", "niche-metrics-*.json"):
        for f in glob.glob(os.path.join(ROOT, "research", pattern)):
            copy_into(f, os.path.join(staging, os.path.basename(f)))
    # copy, not sync: research/input/ on Drive is the owner's upload area and must survive
    results = {"research": upload(staging, "research", creds, mode="copy", public=public)}
    return ({"stage": "research", "results": results, "uploaded_at": now()},
            os.path.join(ROOT, "research", "drive-research.json"))


def pull_inputs(creds):
    dirs = json.loads(rclone(["lsjson", "--dirs-only", remote("research")], creds, check=False).stdout or "[]")
    if not any(d.get("Name") == "input" for d in dirs):
        die(f"Drive has no '{TOP}/research/input/' folder. Upload keywords.csv and competitors.csv "
            f"there (MULTI_AGENT_PLAN.md, step M5), then run this again.")
    dest = os.path.join(ROOT, "data", "research-input")
    os.makedirs(dest, exist_ok=True)
    rclone(["copy", remote("research/input"), dest, "--checksum"], creds)
    check = rclone(["check", remote("research/input"), dest, "--one-way"], creds, check=False)
    if check.returncode != 0:
        die(f"the download did not verify:\n{(check.stderr or check.stdout).strip()[-2000:]}")
    for f in local_files(dest):
        print(f"  pulled data/research-input/{f}")
    print("PASS - research inputs pulled and verified by hash.")


def selftest():
    creds = credentials()
    rclone(["lsd", f"{REMOTE}:"], creds)
    probe = f"probe-{socket.gethostname()}-{int(time.time())}.txt"
    content = f"Northing Studio Drive self-test {now()}\n"
    target = remote(f"_selftest/{probe}")
    rclone(["rcat", target], creds, input_text=content)
    got = rclone(["cat", target], creds).stdout
    rclone(["deletefile", target], creds)
    rclone(["rmdir", remote("_selftest")], creds, check=False)
    if got != content:
        die("wrote a probe file to Drive but read back something different")
    print(f"Drive OK - remote '{REMOTE}:', write/read/delete verified under '{TOP}/_selftest'")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("local_dir", nargs="?")
    ap.add_argument("drive_path", nargs="?", help=f"path under '{TOP}/'")
    ap.add_argument("--product")
    ap.add_argument("--stage", choices=["build", "brief", "listing", "signoff"])
    ap.add_argument("--research", action="store_true")
    ap.add_argument("--pull-inputs", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--public", action="store_true", help="anyone-with-the-link sharing (never for paid files)")
    ap.add_argument("--json")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0
    creds = credentials()
    if a.pull_inputs:
        pull_inputs(creds)
        return 0
    if a.product:
        if not a.stage:
            die("--product needs --stage build|brief|listing|signoff")
        pdir = os.path.abspath(a.product)
        if not os.path.isdir(pdir):
            die(f"no such product folder: {a.product}")
        record, default_out = stage_product(pdir, a.stage, creds, a.public)
    elif a.research:
        record, default_out = stage_research(creds, a.public)
    else:
        if not (a.local_dir and a.drive_path):
            die("give LOCAL_DIR and DRIVE_PATH, or use --product/--research/--pull-inputs/--selftest")
        local = os.path.realpath(a.local_dir)
        if os.path.commonpath([local, os.path.join(ROOT, "Products")]) == os.path.join(ROOT, "Products"):
            die("product files upload with --product and --stage, so the release gate applies")
        record = {"stage": "folder", "results": {"folder": upload(local, a.drive_path, creds, public=a.public)},
                  "uploaded_at": now()}
        default_out = None

    out = a.json or default_out
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(record, open(out, "w", encoding="utf-8"), indent=2)
    for key, res in record["results"].items():
        print(f"\n  {key}/  {res['folder']['url']}")
        for f in res["files"][:40]:
            print(f"    {f['path']}  {f['url']}")
        if len(res["files"]) > 40:
            print(f"    ... and {len(res['files']) - 40} more (see the JSON record)")
    if out:
        print(f"\n  wrote {os.path.relpath(out, ROOT)}")
    print("\nPASS - uploaded and verified (rclone check: 0 differences).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
