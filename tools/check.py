#!/usr/bin/env python3
"""Preveri, ali povezave v playlisti se delujejo, in po zelji odstrani mrtve.

Uporaba:
    python3 tools/check.py ex-yu.m3u                # samo porocilo
    python3 tools/check.py ex-yu.m3u --prune        # odstrani mrtve zapise
    python3 tools/check.py *.m3u --prune --timeout 20

Kanal velja za zivega, ce streznik vrne HTTP 2xx in telo odgovora izgleda kot
HLS manifest (#EXTM3U) ali kot MPEG-TS/DASH vsebina.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import sys
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
OK_TYPES = ("mpegurl", "video/", "mp2t")


def parse(path: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Vrni (glava, [(extinf_blok, url), ...])."""
    lines = open(path, encoding="utf-8").read().splitlines()
    header, entries, block = [], [], []
    for line in lines:
        if line.startswith("#EXTM3U"):
            header.append(line)
        elif line.startswith("#"):
            block.append(line)
        elif line.strip():
            entries.append(("\n".join(block), line.strip()))
            block = []
    return header or ["#EXTM3U"], entries


def probe(url: str, timeout: float) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            body = resp.read(512)
            if resp.status >= 300:
                return False, f"HTTP {resp.status}"
            if body.startswith(b"#EXTM3U"):
                return True, f"HTTP {resp.status}"          # HLS manifest
            if body[:1] == b"\x47":
                return True, f"HTTP {resp.status}"          # surov MPEG-TS
            if b"<MPD" in body[:512]:
                return True, f"HTTP {resp.status}"          # DASH manifest
            if any(t in ctype for t in OK_TYPES):
                return True, f"HTTP {resp.status}"
            return False, f"nepricakovan odgovor ({ctype or 'brez tipa'})"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, type(exc).__name__ + (f": {exc}" if str(exc) else "")


def name_of(block: str) -> str:
    for line in block.splitlines():
        if line.startswith("#EXTINF") and "," in line:
            return line.split(",", 1)[1]
    return "?"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--prune", action="store_true", help="prepisi brez mrtvih")
    args = ap.parse_args()

    dead_total = 0
    for path in args.files:
        header, entries = parse(path)
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            results = list(
                pool.map(lambda e: probe(e[1], args.timeout), entries)
            )

        alive = []
        print(f"\n== {path}")
        for (block, url), (ok, info) in zip(entries, results):
            status = "OK  " if ok else "MRTEV"
            if ok:
                alive.append((block, url))
            else:
                dead_total += 1
            print(f"  {status:<6} {name_of(block):<32} {info}")

        print(f"  -> zivih {len(alive)}/{len(entries)}")
        if args.prune and len(alive) != len(entries):
            out = list(header)
            for block, url in alive:
                out.append(block)
                out.append(url)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(out) + "\n")
            print(f"  -> zapisano brez {len(entries) - len(alive)} mrtvih zapisov")

    return 1 if dead_total and not args.prune else 0


if __name__ == "__main__":
    sys.exit(main())
