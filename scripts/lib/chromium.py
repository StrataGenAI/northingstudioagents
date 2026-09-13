"""Headless Chrome / Chromium for every render in the pipeline.

One place decides how the browser is found and driven, so a product PDF, a
listing image, a contact sheet and a research report are all rendered the same
way on the same machine.

The machine is a Linux server with no display:
  --headless=new            the only headless mode current Chrome ships
  --no-sandbox              the setuid sandbox needs privileges a service user lacks
  --disable-dev-shm-usage   /dev/shm is tiny on servers and VMs; Chrome crashes
                            mid-render when it fills, so shared memory goes to /tmp

The browser is looked up in this order: $CHROME_BIN, google-chrome-stable,
google-chrome, chromium, chromium-browser. scripts/setup.sh installs
google-chrome-stable.
"""
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time

CANDIDATES = ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser")
FLAGS = ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
         "--no-first-run", "--hide-scrollbars", "--allow-file-access-from-files")


def find():
    env = os.environ.get("CHROME_BIN")
    if env:
        if os.path.isfile(env) and os.access(env, os.X_OK):
            return env
        sys.exit(f"FAIL: CHROME_BIN={env} is not an executable file.")
    for name in CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    sys.exit("FAIL: no Chrome or Chromium found (tried $CHROME_BIN, "
             + ", ".join(CANDIDATES) + "). Run scripts/setup.sh.")


def version():
    r = subprocess.run([find(), "--version"], capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


def uri(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def pdf_complete(path):
    """Has Chrome finished writing this PDF?

    Byte count alone cannot tell a finished write from a stalled one, and on a
    loaded machine writes stall for seconds at a time. A finished PDF ends with
    %%EOF, so ask the file itself. Shipping a half-written render is worse than
    waiting: it produces a valid-looking file that every later gate measures.
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            fh.seek(max(0, size - 64))
            return b"%%EOF" in fh.read()
    except OSError:
        return False


def image_complete(path):
    """A finished PNG ends with the IEND chunk; a JPEG with FFD9."""
    try:
        size = os.path.getsize(path)
        if size < 100:
            return False
        with open(path, "rb") as fh:
            fh.seek(max(0, size - 12))
            tail = fh.read()
        return b"IEND" in tail or tail.endswith(b"\xff\xd9")
    except OSError:
        return False


def _stop(p):
    """Stop Chrome and every helper process it started."""
    if p.poll() is not None:
        return
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()


def _render(target_args, out, complete, budget, min_wait, what):
    """Run Chrome until `out` exists, has stopped growing and passes `complete`.

    Chrome in --headless=new regularly writes its output and then never exits, so
    waiting on the process is not an option: wait for the file to settle, then
    stop Chrome ourselves. stderr goes to a file, not a pipe - on a server Chrome
    logs D-Bus noise constantly, and a full pipe would block it mid-render.
    """
    exe = find()
    if os.path.exists(out):
        os.remove(out)
    with tempfile.TemporaryDirectory(prefix="chrome-profile-", ignore_cleanup_errors=True) as profile:
        errlog = os.path.join(profile, "stderr.log")
        cmd = [exe, *FLAGS, f"--virtual-time-budget={budget}",
               f"--user-data-dir={profile}", *target_args]
        with open(errlog, "wb") as errfh:
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=errfh,
                                 start_new_session=True)
            # Generous on purpose: a render that takes five seconds on an idle
            # machine has taken minutes on a loaded one. The completeness test is
            # what normally ends the wait; the deadline only stops a hang.
            deadline = time.time() + max(min_wait, budget / 1000.0 + 60)
            size, stable = -1, 0
            try:
                while time.time() < deadline:
                    if p.poll() is not None:
                        break
                    if os.path.exists(out):
                        s = os.path.getsize(out)
                        stable = stable + 1 if (s == size and s > 0) else 0
                        size = s
                        if stable >= 3 and complete(out):
                            break
                    time.sleep(0.5)
            finally:
                _stop(p)
        err = open(errlog, "rb").read().decode("utf-8", "replace")
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        sys.exit(f"FAIL: Chrome produced no {what}.\n{err[-1500:]}")
    if not complete(out):
        sys.exit(f"FAIL: Chrome's {what} is incomplete - the write stalled or was cut off. "
                 f"Do not measure it; render again.\n{err[-1500:]}")


def print_pdf(html, out, budget=15000):
    """Print an HTML file to PDF. The page size comes from the HTML's own @page rule."""
    _render(["--no-pdf-header-footer", f"--print-to-pdf={out}", uri(html)],
            out, pdf_complete, budget, 600.0, "PDF")


def screenshot(html, out, width, height, budget=15000):
    """Screenshot an HTML file at exactly width x height CSS px, device scale 1."""
    _render(["--force-device-scale-factor=1", f"--window-size={width},{height}",
             f"--screenshot={out}", uri(html)],
            out, image_complete, budget, 300.0, "image")
