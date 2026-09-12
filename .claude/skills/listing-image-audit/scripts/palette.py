#!/usr/bin/env python3
"""Dominant colours of an image as hex codes with their share of the image.

Dependency-free: macOS `sips` shrinks the image to a small BMP, then a tiny k-means runs in pure Python.

Usage:
  palette.py IMAGE [IMAGE ...] [--k 6]
Output (one line per image):
  01.jpg  #F4EFE8 41%  #A3B18A 22%  #3E3A36 14% ...
"""
import argparse
import os
import struct
import subprocess
import sys
import tempfile


def pixels(path):
    with tempfile.TemporaryDirectory() as td:
        bmp = os.path.join(td, "p.bmp")
        subprocess.run(["sips", "-Z", "96", "-s", "format", "bmp", path, "--out", bmp],
                       check=True, capture_output=True)
        data = open(bmp, "rb").read()
    off = struct.unpack_from("<I", data, 10)[0]
    w, h = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]
    step = bpp // 8
    row = (w * step + 3) & ~3
    out = []
    for y in range(abs(h)):
        base = off + y * row
        for x in range(w):
            i = base + x * step
            b, g, r = data[i], data[i + 1], data[i + 2]
            out.append((r, g, b))
    return out


def kmeans(px, k, iters=12):
    # seed with the most common colours after coarse quantisation, kept apart from each other
    counts = {}
    for p in px:
        q = (p[0] >> 4, p[1] >> 4, p[2] >> 4)
        counts[q] = counts.get(q, 0) + 1
    seeds = []
    for q, _ in sorted(counts.items(), key=lambda kv: -kv[1]):
        c = (q[0] * 16 + 8, q[1] * 16 + 8, q[2] * 16 + 8)
        if all(sum((a - b) ** 2 for a, b in zip(c, s)) > 1600 for s in seeds):
            seeds.append(c)
        if len(seeds) == k:
            break
    cents = seeds
    for _ in range(iters):
        sums = [[0, 0, 0, 0] for _ in cents]
        for p in px:
            j = min(range(len(cents)), key=lambda i: (p[0] - cents[i][0]) ** 2 + (p[1] - cents[i][1]) ** 2 + (p[2] - cents[i][2]) ** 2)
            s = sums[j]; s[0] += p[0]; s[1] += p[1]; s[2] += p[2]; s[3] += 1
        cents = [(s[0] // s[3], s[1] // s[3], s[2] // s[3]) if s[3] else c for s, c in zip(sums, cents)]
    shares = [s[3] / len(px) for s in sums]
    return sorted(zip(cents, shares), key=lambda cs: -cs[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--k", type=int, default=6)
    a = ap.parse_args()
    for path in a.images:
        try:
            pal = kmeans(pixels(path), a.k)
        except Exception as e:  # unreadable/unsupported file
            print(f"{os.path.basename(path)}  ERROR {e}", file=sys.stderr)
            continue
        parts = [f"#{r:02X}{g:02X}{b:02X} {share * 100:.0f}%" for (r, g, b), share in pal if share >= 0.02]
        print(f"{os.path.basename(path)}  " + "  ".join(parts))


if __name__ == "__main__":
    main()
