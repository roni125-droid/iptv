#!/usr/bin/env python3
"""Preveri playlisto in jo oceni za predvajanje na Android TV boxih.

Uporaba:
    python3 tools/check.py ex-yu.m3u                    # osnovno porocilo
    python3 tools/check.py ex-yu.m3u --android          # diagnostika za Android TV
    python3 tools/check.py ex-yu.m3u --android --devices 3   # test treh hkratnih naprav
    python3 tools/check.py ex-yu.m3u --prune            # odstrani mrtve zapise

Skripto zazenite v istem domacem omrezju, kjer stojijo boxi. Rezultat velja
za tisto omrezje, saj so mnogi pretoki geografsko ali operatersko omejeni.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

# Privzeta glava, ki jo poslje vecina predvajalnikov na Android TV.
UA_EXOPLAYER = "ExoPlayerLib/2.19.1 (Linux; Android 12) ExoPlayerLib/2.19.1"
UA_BROWSER = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
OK_TYPES = ("mpegurl", "video/", "mp2t")

LAX_SSL = ssl.create_default_context()
LAX_SSL.check_hostname = False
LAX_SSL.verify_mode = ssl.CERT_NONE


class Probe:
    """Izid enega poskusa odpiranja povezave."""

    def __init__(self, ok: bool, info: str, body: bytes = b"", final: str = ""):
        self.ok = ok
        self.info = info
        self.body = body
        self.final = final


def open_url(url: str, timeout: float, ua: str = UA_BROWSER, verify: bool = True,
             read: int = 2048, headers: dict | None = None) -> Probe:
    hdrs = {"User-Agent": ua}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    ctx = None if verify else LAX_SSL
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read(read)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if resp.status >= 300:
                return Probe(False, f"HTTP {resp.status}")
            if (
                body.startswith(b"#EXTM3U")
                or body[:1] == b"\x47"
                or b"<MPD" in body[:512]
                or any(t in ctype for t in OK_TYPES)
            ):
                return Probe(True, f"HTTP {resp.status}", body, resp.geturl())
            return Probe(False, f"nepricakovan odgovor ({ctype or 'brez tipa'})")
    except urllib.error.HTTPError as exc:
        return Probe(False, f"HTTP {exc.code}")
    except ssl.SSLCertVerificationError as exc:
        return Probe(False, f"neveljavno TLS potrdilo: {exc.verify_message}")
    except Exception as exc:
        return Probe(False, type(exc).__name__ + (f": {exc}" if str(exc) else ""))


# --- razclenjevanje playliste ---------------------------------------------

def parse(path: str) -> tuple[list[str], list[tuple[str, str]]]:
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


def name_of(block: str) -> str:
    for line in block.splitlines():
        if line.startswith("#EXTINF") and "," in line:
            return line.split(",", 1)[1]
    return "?"


# --- diagnostika za Android TV --------------------------------------------

def first_segment(url: str, body: bytes, timeout: float) -> str | None:
    """Iz HLS manifesta poisci naslov prvega odseka (po potrebi cez varianto)."""
    text = body.decode("utf-8", "replace")
    variants = [l.strip() for l in text.splitlines()
                if l.strip() and not l.startswith("#")]
    if not variants:
        return None
    target = urllib.parse.urljoin(url, variants[0])
    if "#EXT-X-STREAM-INF" in text:          # master -> se en korak globlje
        inner = open_url(target, timeout, read=4096)
        if not inner.ok:
            return None
        media = [l.strip() for l in inner.body.decode("utf-8", "replace").splitlines()
                 if l.strip() and not l.startswith("#")]
        if not media:
            return None
        return urllib.parse.urljoin(target, media[0])
    return target


def concurrent_test(seg_url: str, devices: int, timeout: float) -> tuple[int, int]:
    """Odpri vec hkratnih povezav do istega odseka, kot bi to naredili boxi."""
    def one(_):
        p = open_url(seg_url, timeout, ua=UA_EXOPLAYER, read=256,
                     headers={"Range": "bytes=0-255"})
        return p.ok

    with concurrent.futures.ThreadPoolExecutor(devices) as pool:
        results = list(pool.map(one, range(devices)))
    return sum(results), devices


def android_report(url: str, timeout: float, devices: int) -> tuple[bool, list[str]]:
    """Vrni (deluje, [opozorila]) z vidika Android TV predvajalnika."""
    warn: list[str] = []
    parsed = urllib.parse.urlparse(url)

    if parsed.scheme == "http":
        warn.append("nesifriran HTTP, Android 9+ ga privzeto blokira")
    if parsed.port and parsed.port not in (80, 443):
        warn.append(f"nestandardna vrata {parsed.port}, nekatera omrezja jih zaprejo")

    # 1. tocno tako, kot bi poskusil box
    p = open_url(url, timeout, ua=UA_EXOPLAYER)
    if not p.ok and parsed.scheme == "https":
        # ali je kriv samo TLS?
        lax = open_url(url, timeout, ua=UA_EXOPLAYER, verify=False)
        if lax.ok:
            warn.append("neveljavno TLS potrdilo, ExoPlayer bo povezavo zavrnil")
            p = lax
    if not p.ok:
        # ali je kriv User-Agent?
        alt = open_url(url, timeout, ua=UA_BROWSER)
        if alt.ok:
            warn.append("streznik zavraca privzeti User-Agent, nastavite brskalniskega")
            p = alt
    if not p.ok:
        return False, [p.info]

    text = p.body.decode("utf-8", "replace")
    if re.search(r"#EXT-X-(SESSION-)?KEY:METHOD=(?!NONE)", text):
        warn.append("pretok je sifriran, brez podpore za kljuce ne bo slike")
    if re.search(r'CODECS="[^"]*(hvc1|hev1)', text):
        warn.append("H.265/HEVC, starejsi boxi ga ne dekodirajo")
    if p.final and p.final.startswith("http://") and parsed.scheme == "https":
        warn.append("preusmeritev s HTTPS na HTTP")

    if devices > 1:
        seg = first_segment(p.final or url, p.body, timeout)
        if seg:
            ok_count, total = concurrent_test(seg, devices, timeout)
            if ok_count < total:
                warn.append(f"hkrati je steklo le {ok_count} od {total} povezav")

    return True, warn


# --- glavni tok ------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--prune", action="store_true", help="prepisi brez mrtvih")
    ap.add_argument("--android", action="store_true",
                    help="dodatna diagnostika za Android TV")
    ap.add_argument("--devices", type=int, default=1,
                    help="koliko hkratnih naprav naj preizkusim (npr. 3)")
    args = ap.parse_args()

    dead_total = 0
    for path in args.files:
        header, entries = parse(path)

        def work(entry):
            _, url = entry
            if args.android:
                return android_report(url, args.timeout, args.devices)
            p = open_url(url, args.timeout)
            return p.ok, ([] if p.ok else [p.info])

        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            results = list(pool.map(work, entries))

        alive, flagged = [], 0
        print(f"\n== {path}")
        for (block, url), (ok, notes) in zip(entries, results):
            name = name_of(block)
            if ok:
                alive.append((block, url))
                if notes:
                    flagged += 1
                    print(f"  OPOZORILO  {name}")
                    for note in notes:
                        print(f"             - {note}")
                else:
                    print(f"  OK         {name}")
            else:
                dead_total += 1
                print(f"  MRTEV      {name:<32} {notes[0] if notes else ''}")

        print(f"  -> zivih {len(alive)}/{len(entries)}, z opozorili {flagged}")
        if args.prune and len(alive) != len(entries):
            out = list(header)
            for block, url in alive:
                out.extend([block, url])
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(out) + "\n")
            print(f"  -> odstranjenih {len(entries) - len(alive)} mrtvih zapisov")

    return 1 if dead_total and not args.prune else 0


if __name__ == "__main__":
    sys.exit(main())
