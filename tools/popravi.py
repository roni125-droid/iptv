#!/usr/bin/env python3
"""Popravi seznam: odstrani mrtve, obidi pokvarjena potrdila, pripni kakovost.

Skripta gre cez vsak kanal in naredi troje:

1. Kanale, ki jih streznik dokoncno zavrne (HTTP 404 ali 403), odstrani.
   Tam naslov ne obstaja vec in cakanje nima smisla.

2. Kanale, ki padejo zaradi poteklega ali napacnega TLS potrdila, poskusi
   odpreti prek navadnega HTTP. Vecina teh strojev strezhe isto sliko na
   obeh vratih, le potrdila jim je poteklo. Tak kanal potem dela tudi v
   predvajalnikih, ki so pri potrdilih strogi.

3. Kanale z vec razlicicami slike pripne na najboljso, da ob preklopu ni
   vec megle.

Kanal, ki se ta trenutek ne odziva, ostane v seznamu z izvirnim naslovom.
Postaja je lahko preprosto zunaj programa.

Uporaba:
    python3 tools/popravi.py exyu.m3u --out exyu-ok.m3u
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import socket
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

DROP = "odstrani"
KEEP = "obdrzi"


class Result:
    def __init__(self, action: str, url: str, note: str):
        self.action = action
        self.url = url
        self.note = note


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


def fetch(url: str, timeout: float):
    """Vrni (telo, koncni_naslov, napaka). Napaka je None ob uspehu."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(65536), resp.geturl(), None
    except urllib.error.HTTPError as exc:
        return None, None, ("http", exc.code, f"streznik zavraca, HTTP {exc.code}")
    except urllib.error.URLError as exc:
        r = exc.reason
        if isinstance(r, ssl.SSLCertVerificationError):
            return None, None, ("tls", 0, f"TLS potrdilo: {r.verify_message}")
        if isinstance(r, ssl.SSLError):
            return None, None, ("tls", 0, f"napaka TLS: {r.reason or r}")
        if isinstance(r, TimeoutError):
            return None, None, ("mreza", 0, "streznik se ne odziva")
        return None, None, ("mreza", 0, f"ni povezave: {r}")
    except TimeoutError:
        return None, None, ("mreza", 0, "streznik se ne odziva")
    except Exception as exc:
        return None, None, ("drugo", 0, f"{type(exc).__name__}: {exc}")


def best_variant(body: bytes, base: str) -> tuple[str | None, str]:
    text = body.decode("utf-8", "replace")
    if "#EXT-X-STREAM-INF" not in text:
        return None, ""
    lines = text.splitlines()
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
            best_key, best = key, urllib.parse.urljoin(base, target)
    if best is None or count < 2:
        return (best, f"pripeto na najboljso od {count}") if best else (None, "")
    height, band = best_key
    opis = f"{height}p" if height else f"{band // 1000} kbit/s"
    return best, f"pripeto na najboljso od {count}, {opis}"


def http_candidates(url: str) -> list[str]:
    """Naslovi prek HTTP, ki jih je vredno poskusiti, ko potrdilo odpove.

    Najprej ista vrata, nato brez njih. Streznik Wowza namrec sifrirano
    slika strezhe na vratih 4443, nesifrirano pa na privzetih.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() != "https":
        return []
    bare = parts.hostname or ""
    out = [urllib.parse.urlunsplit(("http",) + tuple(parts)[1:])]
    if parts.port:
        out.append(
            urllib.parse.urlunsplit(("http", bare, parts.path, parts.query, ""))
        )
    # Wowza strezhe sifrirano na 443 ali 4443, nesifrirano pa na 1935 ali 8086.
    if (parts.port or 443) in (443, 4443):
        for port in (1935, 8086):
            out.append(
                urllib.parse.urlunsplit(
                    ("http", f"{bare}:{port}", parts.path, parts.query, "")
                )
            )
    return out


def cert_hostname(url: str, timeout: float) -> str | None:
    """Ime, na katero se glasi potrdilo streznika.

    Kadar postaja oddaja s svojega naslova IP, je potrdilo veljavno, le
    glasi se na domeno. Preverjanje verige zato opravimo, preverjanje imena
    pa zacasno izpustimo, samo da iz potrdila preberemo pravo ime. Nato se
    povezemo nanj s polnim preverjanjem.
    """
    parts = urllib.parse.urlsplit(url)
    host, port = parts.hostname, parts.port or 443
    if not host:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False          # ime preverimo sami, veriga ostane
    try:
        with socket.create_connection((host, port), timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as tls:
                cert = tls.getpeercert() or {}
    except Exception:
        return None
    names = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
    for entry in cert.get("subject", ()):
        for k, v in entry:
            if k == "commonName" and v not in names:
                names.append(v)
    for name in names:
        if name and not name.startswith("*") and name != host:
            return name
    return None


def repair(url: str, timeout: float) -> Result:
    body, final, err = fetch(url, timeout)

    if err and err[0] == "tls" and "mismatch" in err[2].lower():
        # Potrdilo je veljavno, le glasi se na drugo ime. Poskusimo nanj.
        name = cert_hostname(url, timeout)
        if name:
            parts = urllib.parse.urlsplit(url)
            netloc = f"{name}:{parts.port}" if parts.port else name
            fixed = urllib.parse.urlunsplit(
                ("https", netloc, parts.path, parts.query, "")
            )
            body2, final2, err2 = fetch(fixed, timeout)
            if err2 is None:
                note = f"naslov popravljen na pravo ime streznika, {name}"
                new, extra = best_variant(body2, final2 or fixed)
                return Result(
                    KEEP, new or fixed, f"{note}; {extra}" if extra else note
                )

    if err and err[0] == "tls":
        # Potrdilo je pokvarjeno. Ista slika je pogosto na voljo prek HTTP.
        for plain in http_candidates(url):
            body2, final2, err2 = fetch(plain, timeout)
            if err2 is None:
                note = "preklopljeno na HTTP, potrdilo postaje je pokvarjeno"
                new, extra = best_variant(body2, final2 or plain)
                return Result(
                    KEEP, new or plain, f"{note}; {extra}" if extra else note
                )
        return Result(KEEP, url, f"ostaja, {err[2]}")

    if err and err[0] == "http" and err[1] in (403, 404, 410):
        return Result(DROP, url, err[2])

    if err:
        return Result(KEEP, url, f"ostaja, {err[2]}")

    new, extra = best_variant(body, final or url)
    if new:
        return Result(KEEP, new, extra)
    return Result(KEEP, url, "dela, ena sama kakovost")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    header, entries = parse(args.file)
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(lambda e: repair(e[1], args.timeout), entries))

    out = list(header)
    dropped, fixed, pinned, kept = [], 0, 0, 0
    print(f"\n== {args.file}")
    for (block, url), r in zip(entries, results):
        name = name_of(block)
        if r.action == DROP:
            dropped.append(name)
            print(f"  ODSTRANJEN  {name:<34} {r.note}")
            continue
        out.extend([block, r.url])
        kept += 1
        if "preklopljeno" in r.note or "popravljen" in r.note:
            fixed += 1
            print(f"  POPRAVLJEN  {name:<34} {r.note}")
        elif "pripeto" in r.note:
            pinned += 1
            print(f"  PRIPET      {name:<34} {r.note}")
        else:
            print(f"  ohranjen    {name:<34} {r.note}")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")

    print()
    print(f"  odstranjenih (404 ali 403) : {len(dropped)}")
    print(f"  popravljenih naslovov      : {fixed}")
    print(f"  pripetih na boljso sliko   : {pinned}")
    print(f"  kanalov v novem seznamu    : {kept}")
    print(f"  -> zapisano v {args.out}")
    if dropped:
        print("\n  Odstranjeni: " + ", ".join(dropped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
