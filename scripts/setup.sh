#!/usr/bin/env bash
# setup.sh - install and verify everything the Northing Studio pipeline needs on a
# headless Linux server (Ubuntu/Debian): Google Chrome for rendering, poppler for
# rasterising pages, rclone for Google Drive, the brand fonts, and a Python venv
# with pypdf, markdown, requests and Pillow.
#
# Idempotent: every step looks before it acts, so a re-run changes nothing that is
# already right. Safe to run as often as you like.
#
#   scripts/setup.sh                  install what is missing, then verify everything
#   scripts/setup.sh --check          verify only, install nothing (build preflight)
#   scripts/setup.sh --no-selftest    skip the render self-test
#
# Exit: 0 everything verified · 1 something failed · 2 installed and verified, but
# Google Drive is not configured yet (MULTI_AGENT_PLAN.md, step M1).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
SK="$ROOT/.claude/skills"
CHECK=0
SELFTEST=1
for arg in "$@"; do
  case "$arg" in
    --check) CHECK=1 ;;
    --no-selftest) SELFTEST=0 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 1 ;;
  esac
done

APT_PACKAGES=(poppler-utils fontconfig fonts-dejavu-core curl ca-certificates python3-venv gnupg)
RCLONE_MIN="1.65.0"

ROWS=()
FAILED=0
DRIVE_MISSING=0
ok()   { ROWS+=("PASS  $*"); printf '  ok    %s\n' "$*"; }
bad()  { ROWS+=("FAIL  $*"); printf '  FAIL  %s\n' "$*" >&2; FAILED=1; }
note() { ROWS+=("----  $*"); printf '  --    %s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
may_install() { [ "$CHECK" -eq 0 ]; }

SUDO=""
[ "$(id -u)" -eq 0 ] || SUDO="sudo -n"

have_pkg() { dpkg-query -W -f='${db:Status-Abbrev}' "$1" 2>/dev/null | grep -q '^ii'; }
version_ge() { [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" = "$2" ]; }
APT_UPDATED=0
apt_update_once() {
  [ "$APT_UPDATED" -eq 1 ] && return 0
  $SUDO apt-get update -qq >/dev/null && APT_UPDATED=1
}
apt_install() { $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@" >/dev/null; }

# ---------------------------------------------------------------- packages
step "System packages"
missing=()
for p in "${APT_PACKAGES[@]}"; do have_pkg "$p" || missing+=("$p"); done
if [ ${#missing[@]} -gt 0 ] && may_install; then
  printf '  installing %s\n' "${missing[*]}"
  if ! { apt_update_once && apt_install "${missing[@]}"; }; then
    bad "apt-get install ${missing[*]} failed"
  fi
fi
for p in "${APT_PACKAGES[@]}"; do
  if have_pkg "$p"; then ok "apt: $p"; else bad "apt: $p is not installed"; fi
done

# ---------------------------------------------------------------- browser
step "Headless Chrome"
chrome_bin() {
  if [ -n "${CHROME_BIN:-}" ]; then printf '%s' "$CHROME_BIN"; return 0; fi
  for c in google-chrome-stable google-chrome chromium chromium-browser; do
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return 0; fi
  done
  return 1
}
CHROME="$(chrome_bin || true)"
if [ -z "$CHROME" ] && may_install; then
  arch="$(dpkg --print-architecture)"
  if [ "$arch" = "amd64" ]; then
    # Ubuntu's chromium is snap-only; snap's private /tmp breaks Chrome's temp
    # profile and output paths. Google's .deb also adds Google's signed apt repo,
    # so apt keeps it updated.
    printf '  installing google-chrome-stable\n'
    tmp="$(mktemp -d)"
    if curl -fsSL --retry 3 -o "$tmp/google-chrome-stable_current_amd64.deb" \
         https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
       && apt_update_once && apt_install "$tmp/google-chrome-stable_current_amd64.deb"; then
      CHROME="$(chrome_bin || true)"
    else
      bad "Google Chrome download or install failed"
    fi
    rm -rf "$tmp"
  else
    bad "Google Chrome ships no $arch build - install Chromium and set CHROME_BIN"
  fi
fi
if [ -n "$CHROME" ] && cver="$("$CHROME" --version 2>/dev/null)"; then
  ok "browser: $cver ($CHROME)"
  profile="$(mktemp -d)"
  dom="$(timeout 90 "$CHROME" --headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu \
           --no-first-run --user-data-dir="$profile" --dump-dom \
           'data:text/html,<p>northing-probe</p>' 2>/dev/null || true)"
  rm -rf "$profile"
  if grep -q northing-probe <<<"$dom"; then ok "browser: headless render works"
  else bad "browser: headless probe rendered nothing"; fi
else
  bad "browser: no Chrome/Chromium found"
fi

# ---------------------------------------------------------------- rclone
step "rclone (Google Drive client)"
rclone_ver() { rclone version 2>/dev/null | sed -n '1s/^rclone v\([0-9.]*\).*/\1/p'; }
rv="$(rclone_ver || true)"
if { [ -z "$rv" ] || ! version_ge "$rv" "$RCLONE_MIN"; } && may_install; then
  arch="$(dpkg --print-architecture)"
  tag="$(curl -fsSL --retry 3 https://downloads.rclone.org/version.txt | sed -n 's/^rclone \(v[0-9.]*\).*/\1/p' || true)"
  deb="rclone-${tag}-linux-${arch}.deb"
  printf '  installing rclone %s\n' "${tag:-?}"
  tmp="$(mktemp -d)"
  if [ -n "$tag" ] \
     && curl -fsSL --retry 3 -o "$tmp/$deb" "https://downloads.rclone.org/${tag}/${deb}" \
     && curl -fsSL --retry 3 -o "$tmp/SHA256SUMS" "https://downloads.rclone.org/${tag}/SHA256SUMS" \
     && (cd "$tmp" && grep -E "  ${deb}\$" SHA256SUMS | sha256sum -c --status -) \
     && apt_install "$tmp/$deb"; then
    rv="$(rclone_ver || true)"
  else
    bad "rclone download, checksum or install failed"
  fi
  rm -rf "$tmp"
fi
if [ -n "$rv" ] && version_ge "$rv" "$RCLONE_MIN"; then ok "rclone $rv"
else bad "rclone ${rv:-missing} (need >= $RCLONE_MIN)"; fi

# ---------------------------------------------------------------- python
step "Python venv (.venv)"
if [ ! -x "$PY" ] && may_install; then
  printf '  creating %s\n' "$VENV"
  /usr/bin/python3 -m venv "$VENV" || bad "python3 -m venv failed"
fi
REQS="$ROOT/scripts/requirements.txt"
# Exact pins, not "any version": the gates are calibrated against these extractors.
pins_ok() {
  "$PY" - "$REQS" <<'PYEOF'
import re, sys
from importlib import metadata
bad = 0
for line in open(sys.argv[1]):
    m = re.match(r"^\s*([A-Za-z0-9_.-]+)==([^\s#]+)", line)
    if not m:
        continue
    name, want = m.groups()
    try:
        got = metadata.version(name)
    except metadata.PackageNotFoundError:
        got = None
    print(f"{name} {got or 'missing'}" + ("" if got == want else f" (pinned {want})"))
    bad += got != want
sys.exit(1 if bad else 0)
PYEOF
}
if [ -x "$PY" ]; then
  if ! pins_ok >/dev/null 2>&1 && may_install; then
    printf '  installing pinned packages from scripts/requirements.txt\n'
    "$PY" -m pip install -q --disable-pip-version-check -r "$REQS" || bad "pip install -r scripts/requirements.txt failed"
  fi
  if out="$(pins_ok 2>&1)"; then
    while IFS= read -r line; do ok "python: $line"; done <<<"$out"
  else
    bad "python: .venv does not match scripts/requirements.txt"
    printf '%s\n' "$out" >&2
  fi
else
  bad "python: no venv at $VENV"
fi

# ---------------------------------------------------------------- fonts
step "Brand fonts"
FONT_DIRS=()
while IFS= read -r m; do FONT_DIRS+=("$(dirname "$m")"); done \
  < <(find "$ROOT/brands" "$ROOT/Products/_assets" -path '*/fonts/manifest.json' 2>/dev/null | sort)
FETCH="$SK/printable-pdf/scripts/fetch_fonts.py"
if [ ${#FONT_DIRS[@]} -eq 0 ]; then
  bad "fonts: no fonts/manifest.json under brands/ or Products/_assets/"
elif [ ! -x "$PY" ]; then
  bad "fonts: cannot check without the venv"
else
  for d in "${FONT_DIRS[@]}"; do
    rel="${d#"$ROOT"/}"
    if may_install; then
      # Records PostScript names in the manifest (downloads only what is missing),
      # then installs the faces for fontconfig.
      "$PY" "$FETCH" --dir "$d" >/dev/null || bad "fonts: fetch_fonts.py --dir $rel failed"
      "$PY" "$FETCH" --dir "$d" --install-system >/dev/null || bad "fonts: system install from $rel failed"
    fi
    if out="$("$PY" "$FETCH" --dir "$d" --check --check-system 2>&1)"; then
      ok "fonts: $rel - $(tail -n1 <<<"$out")"
    else
      bad "fonts: $rel"
      printf '%s\n' "$out" >&2
    fi
  done
fi

# ---------------------------------------------------------------- self-test
if [ "$SELFTEST" -eq 1 ]; then
  step "Render self-test (Products/_smoke, output to a temp dir)"
  if [ -x "$PY" ] && [ -n "$CHROME" ]; then
    tmp="$(mktemp -d)"
    for ed in a4 tablet; do
      html="$ROOT/Products/_smoke/build/smoke-$ed.html"
      css="$(sed -n 's/.*href="\([^"]*fonts\.css\)".*/\1/p' "$html" | head -n1)"
      manifest="$(realpath -m "$(dirname "$html")/$(dirname "$css")")/manifest.json"
      pdf="$tmp/smoke-$ed.pdf"
      if "$PY" "$SK/printable-pdf/scripts/build_pdf.py" "$html" -o "$pdf" --size "$ed" >"$tmp/$ed-build.log" 2>&1 \
         && "$PY" "$SK/printable-pdf/scripts/verify_pdf.py" "$pdf" --size "$ed" --fonts "$manifest" \
              --json "$tmp/$ed-verify.json" >"$tmp/$ed-verify.log" 2>&1 \
         && "$PY" "$SK/printable-pdf/scripts/render_pages.py" "$pdf" --out "$tmp/$ed-pages" >"$tmp/$ed-pages.log" 2>&1; then
        ok "self-test $ed: built, verified (brand fonts + raster gates), $(find "$tmp/$ed-pages" -name '*.png' | wc -l) page PNG(s)"
      else
        bad "self-test $ed failed:"
        tail -n 25 "$tmp/$ed"-*.log >&2
      fi
    done
    rm -rf "$tmp"
  else
    bad "self-test: needs the venv and a browser"
  fi
fi

# ---------------------------------------------------------------- drive
step "Google Drive"
if [ -z "${GDRIVE_CREDENTIALS:-}" ]; then
  note "GDRIVE_CREDENTIALS is not set - Drive is not configured (MULTI_AGENT_PLAN.md, step M1)"
  DRIVE_MISSING=1
elif [ ! -f "$ROOT/scripts/upload_to_drive.py" ]; then
  bad "drive: scripts/upload_to_drive.py is missing"
elif out="$("$PY" "$ROOT/scripts/upload_to_drive.py" --selftest 2>&1)"; then
  ok "drive: $(tail -n1 <<<"$out")"
else
  bad "drive: self-test failed"
  printf '%s\n' "$out" >&2
fi

# ---------------------------------------------------------------- summary
printf '\n== Summary\n'
printf '  %s\n' "${ROWS[@]}"
if [ "$FAILED" -ne 0 ]; then
  printf '\nFAIL - fix the rows above, then re-run scripts/setup.sh\n'
  exit 1
fi
if [ "$DRIVE_MISSING" -ne 0 ]; then
  printf '\nINSTALLED - everything verified except Google Drive (exit 2). See MULTI_AGENT_PLAN.md, step M1.\n'
  exit 2
fi
printf '\nPASS - everything installed and verified.\n'
