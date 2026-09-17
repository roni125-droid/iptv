#!/usr/bin/env python3
"""Pripni vsak kanal na najboljso razlicico pretoka.

Zakaj:
    Naslov v seznamu obicajno kaze na glavni manifest HLS, v katerem je vec
    razlicic iste slike. Predvajalnik zacne pri najslabsi, da slika stece
    hitro, nato izmeri hitrost povezave in sele cez nekaj sekund preklopi na
    boljso. Zato je slika ob preklopu kanala megleno, cez priblizno deset
    sekund pa se sama zbistri.

    Ta skripta prebere glavni manifest, poisce razlicico z najvisjo
    locljivostjo in naslov v seznamu zamenja z njo. Predvajalnik potem nima
    kaj izbirati in zacne takoj pri najboljsi sliki.

Cena:
    Prilagajanje odpade. Na sibki povezavi predvajalnik ne bo vec znizal
    kakovosti, ampak bo slika zastajala. Ce se to zgodi, uporabite izvirni
    seznam.

Uporaba:
    python3 tools/kakovost.py exyu.m3u --out exyu-hd.m3u
    python3 tools/kakovost.py ex-yu.m3u si.m3u hr.m3u ba.m3u rs.m3u --na-mestu
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

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
STREAM_INF = re.compile(r"#EXT-X-STREAM-INF:(.*)", re.I)
RESOLUTION = re.compile(r"RESOLUTION=(\d+)x(\d+)", re.I)
BANDWIDTH = re.compile(r"BANDWIDTH=(\d+)", re.I)


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


def best_variant(url: str, timeout: float) -> tuple[str | None, str]:
    """Vrni (naslov najboljse razlicice ali None, pojasnilo)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final = resp.geturl()
            body = resp.read(65536).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return None, f"zavrnjeno, HTTP {exc.code}"
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            return None, "neveljavno TLS potrdilo"
        if isinstance(reason, ssl.SSLError):
            return None, f"napaka TLS: {reason.reason or reason}"
        if isinstance(reason, TimeoutError):
            return None, "streznik se ne odziva"
        return None, f"ni povezave: {reason}"
    except TimeoutError:
        return None, "streznik se ne odziva"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

    if "#EXT-X-STREAM-INF" not in body:
        return None, "OK|kanal dela, ima eno samo kakovost, spreminjati ni kaj"

    lines = body.splitlines()
    best, best_key, count = None, (-1, -1), 0
    for i, line in enumerate(lines):
        m = STREAM_INF.match(line.strip())
        if not m:
            continue
        target = next(
            (l.strip() for l in lines[i + 1:] if l.strip() and not l.startswith("#")),
            None,
        )
        if not target:
            continue
        count += 1
        res = RESOLUTION.search(m.group(1))
        band = BANDWIDTH.search(m.group(1))
        key = (int(res.group(2)) if res else 0, int(band.group(1)) if band else 0)
        if key > best_key:
            best_key, best = key, urllib.parse.urljoin(final, target)

    if best is None:
        return None, "OK|kanal dela, razlicic ni bilo mogoce prebrati"
    height, band = best_key
    opis = f"{height}p" if height else f"{band // 1000} kbit/s"
    return best, f"izbrana najboljsa od {count}, {opis}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", help="izhodna datoteka, samo pri eni vhodni")
    ap.add_argument("--na-mestu", action="store_true", help="prepisi vhodne datoteke")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if args.out and len(args.files) > 1:
        print("--out gre samo z eno vhodno datoteko", file=sys.stderr)
        return 2
    if not args.out and not args.na_mestu:
        print("izberite --out ali --na-mestu", file=sys.stderr)
        return 2

    for path in args.files:
        header, entries = parse(path)
        with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
            results = list(
                pool.map(lambda e: best_variant(e[1], args.timeout), entries)
            )

        out, changed, ok, bad = list(header), 0, 0, 0
        print(f"\n== {path}")
        for (block, url), (new_url, info) in zip(entries, results):
            name = name_of(block)
            if new_url and new_url != url:
                changed += 1
                print(f"  PRIPETO   {name:<34} {info}")
                out.extend([block, new_url])
            elif info.startswith("OK|"):
                ok += 1
                print(f"  V REDU    {name:<34} {info[3:]}")
                out.extend([block, url])
            else:
                bad += 1
                print(f"  NAPAKA    {name:<34} {info}")
                out.extend([block, url])

        target = args.out or path
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n")
        print()
        print(f"  pripetih na boljso sliko : {changed}")
        print(f"  ze v redu, brez spremembe: {ok}")
        print(f"  se ni odzvalo            : {bad}")
        print(f"  skupaj kanalov           : {len(entries)}")
        print(f"  -> zapisano v {target}")
        print()
        print("  Pozor: NAPAKA tu pomeni samo, da se streznik ta trenutek s")
        print("  tega racunalnika ni odzval. Kanali z oznako [ni 24/7] so")
        print("  lahko preprosto zunaj programa, protivirusni program pa zna")
        print("  blokirati posamezne streznike. Vsi ti kanali ostanejo v")
        print("  seznamu z izvirnim naslovom in niso izgubljeni.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
