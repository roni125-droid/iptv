#!/usr/bin/env python3
"""Zgradi EX-YU IPTV playlisto (SI, HR, BA, RS) iz javne baze iptv-org.

Vir podatkov:
  - https://github.com/iptv-org/iptv       (streams/*.m3u)
  - https://github.com/iptv-org/database   (data/channels.csv, logos.csv)

Skripta obdrzi samo kanale, ki jih izdajatelj (ali njegov uradni CDN) javno
oddaja brez narocnine, in zavrze ocitne nepooblascene re-streame.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import OrderedDict

IPTV_RAW = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams"
DB_RAW = "https://raw.githubusercontent.com/iptv-org/database/master/data"

# Izvorne datoteke, ki jih preberemo (hu.m3u zaradi Pannon RTV iz Vojvodine).
SOURCE_FILES = ["si.m3u", "hr.m3u", "ba.m3u", "rs.m3u", "hu.m3u"]

COUNTRIES = OrderedDict(
    [
        ("si", "Slovenija"),
        ("hr", "Hrvaška"),
        ("ba", "Bosna in Hercegovina"),
        ("rs", "Srbija"),
    ]
)

# --- filtri za nepooblascene / nestabilne vire -----------------------------

# Gostitelji, ki preprodajajo placljive programe ali so pusceni operaterski
# vhodi (test racuni, multicast prehodi, OTT platforme za narocnike).
HOST_DENYLIST = (
    "dstv.cx",
    "dstvmultimedia.com",
    "nghk.ai",
    "isp.bg",
    "xploretv.si",
    "antik.sk",
    "vipottbpkstream.vip.hr",
    "nexttv.ht.hr",
    "united.cloud",
    "webtvstream.bhtelecom.ba",
    "cutuk.net",
    "mirtv.club",      # vraca vrinjeno oglasno skripto namesto pretoka
)

# Poti, znacilne za pirat panele in za prepakiran ISP multicast.
# Pozor: zahtevamo koncno posevnico, sicer vzorec ujame tudi "/playlist.m3u8".
PATH_DENY_RE = re.compile(r"/(play|udp)/", re.I)

# Placljive oz. tuje blagovne znamke, ki ne sodijo v seznam FTA kanalov.
NAME_DENY_RE = re.compile(
    r"\b(hbo|cinemax|cinestar|sport ?klub|arena ?sport|nova ?sport|eurosport|"
    r"national geographic|nat geo|nickelodeon|disney|discovery|history|h2|"
    r"viasat|star (channel|crime|life|movies)|sci ?fi|fox|mtv|pickbox|"
    r"kitchen tv|food network|cbs|amc|axn|tv1000)\b",
    re.I,
)

TVG_ID_RE = re.compile(r'tvg-id="([^"]*)"')


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ex-yu-iptv-build"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def read_source(name: str, cache: str | None) -> str:
    if cache:
        path = os.path.join(cache, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
    return fetch(f"{IPTV_RAW}/{name}")


def read_csv(name: str, cache: str | None) -> list[dict]:
    text = None
    if cache:
        path = os.path.join(cache, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
    if text is None:
        text = fetch(f"{DB_RAW}/{name}")
    return list(csv.DictReader(io.StringIO(text)))


def host_of(url: str) -> str:
    m = re.match(r"[a-z]+://([^/:]+)", url, re.I)
    return m.group(1).lower() if m else ""


def is_bare_ip(host: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host))


def own_server(title: str, url: str) -> bool:
    """Ali pot v naslovu nosi ime same postaje?

    Mala postaja pogosto oddaja s svojega streznika brez domene. Ce se ime
    kanala pojavi v poti, gre skoraj zagotovo za njen lasten streznik in ne
    za preprodajalca, ki na isti naslov obesi tuje programe.
    """
    path = re.sub(r"[^a-z0-9]", "", urllib.parse.urlparse(url).path.lower())
    if not path:
        return False
    name = clean_name(title).lower()
    tokens = [t for t in re.split(r"[^a-z0-9]+", name) if len(t) >= 4]
    tokens.append(re.sub(r"[^a-z0-9]", "", name))
    return any(t and t in path for t in tokens)


def parse_entries(text: str):
    """Vrni (tvg_id, prikazno_ime, url, ima_user_agent) za vsak zapis."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            attrs, _, title = line.partition(",")
            tvg = TVG_ID_RE.search(attrs)
            ua = False
            j = i + 1
            while j < len(lines) and lines[j].startswith("#"):
                if "http-user-agent" in lines[j]:
                    ua = True
                j += 1
            if j < len(lines) and lines[j].strip():
                yield (tvg.group(1) if tvg else "", title.strip(), lines[j].strip(), ua)
            i = j
        i += 1


def keep(tvg_id: str, title: str, url: str, ua: bool,
         ip_channels: int = 99) -> bool:
    if not url.lower().startswith(("http://", "https://")):
        return False          # mmsh:// in rtsp:// sodobni predvajalniki ne marajo
    if ua:
        return False          # ponarejen User-Agent = obhod zascite vira
    host = host_of(url)
    if is_bare_ip(host) and not (ip_channels == 1 and own_server(title, url)):
        return False          # gol IP z vec programi je preprodajalski panel
    if any(bad in host for bad in HOST_DENYLIST):
        return False
    if PATH_DENY_RE.search(url):
        return False
    if re.search(r"[?&](p|u|admin|token|password)=", url, re.I):
        return False          # pusceni dostopni kljuci
    if NAME_DENY_RE.search(title):
        return False
    return True


def country_of(tvg_id: str, source: str) -> str | None:
    m = re.search(r"\.([a-z]{2})@", tvg_id)
    code = m.group(1) if m else source[:2]
    return code if code in COUNTRIES else None


def quality_rank(title: str, url: str) -> tuple:
    res = re.search(r"\((\d{3,4})p\)", title)
    return (
        0 if url.startswith("https://") else 1,
        -(int(res.group(1)) if res else 0),
        1 if "[Not 24/7]" in title or "[Geo-blocked]" in title else 0,
    )


def clean_name(title: str) -> str:
    title = re.sub(r"\s*\((\d{3,4})p\)", "", title)
    title = re.sub(r"\s*\[(Not 24/7|Geo-blocked)\]", "", title)
    return title.strip()


def flags(title: str) -> str:
    """Oznake, ki jih je nujno videti v imenu kanala na zaslonu."""
    out = []
    if "[Geo-blocked]" in title:
        out.append("geo")
    if "[Not 24/7]" in title:
        out.append("ni 24/7")
    return ", ".join(out)


def build(cache: str | None, outdir: str) -> dict:
    channels = {c["id"]: c for c in read_csv("channels.csv", cache)}
    logos: dict[str, str] = {}
    for row in read_csv("logos.csv", cache):
        logos.setdefault(row["channel"], row["url"])

    # Najprej preberi vse vire in prestej kanale na posameznem golem IP-ju.
    sources: dict[str, str] = {}
    ip_count: dict[str, set] = {}
    for src in SOURCE_FILES:
        try:
            sources[src] = read_source(src, cache)
        except Exception as exc:  # pragma: no cover
            print(f"opozorilo: {src} ni na voljo ({exc})", file=sys.stderr)
            continue
        for tvg_id, title, url, _ in parse_entries(sources[src]):
            host = host_of(url)
            if is_bare_ip(host):
                ip_count.setdefault(host, set()).add(tvg_id or title)

    best: dict[str, tuple] = {}
    for src in SOURCE_FILES:
        text = sources.get(src)
        if text is None:
            continue
        for tvg_id, title, url, ua in parse_entries(text):
            country = country_of(tvg_id, src)
            n = len(ip_count.get(host_of(url), {None}))
            if country is None or not keep(tvg_id, title, url, ua, n):
                continue
            key = tvg_id or f"{country}:{clean_name(title).lower()}"
            cand = (quality_rank(title, url), country, tvg_id, title, url)
            if key not in best or cand[0] < best[key][0]:
                best[key] = cand

    per_country: dict[str, list] = {c: [] for c in COUNTRIES}
    for _, (rank, country, tvg_id, title, url) in sorted(best.items()):
        chan = channels.get(tvg_id.split("@")[0], {})
        name = chan.get("name") or clean_name(title)
        per_country[country].append(
            {
                "id": tvg_id,
                "name": name,
                "logo": logos.get(tvg_id.split("@")[0], ""),
                "url": url,
                "note": flags(title),
            }
        )
    for country in per_country:
        per_country[country].sort(key=lambda e: e["name"].lower())

    def render(entry: dict, group: str) -> list[str]:
        name = entry["name"]
        if entry["note"]:
            name += f' [{entry["note"]}]'
        return [
            f'#EXTINF:-1 tvg-id="{entry["id"]}" tvg-logo="{entry["logo"]}" '
            f'group-title="{group}",{name}',
            entry["url"],
        ]

    os.makedirs(outdir, exist_ok=True)
    total = 0

    # Stalni programi gredo v svojo skupino pred obcasne. V TiViMate se
    # skupine berejo po vrsti, zato so zgoraj tisti, ki vedno delajo, spodaj
    # pa postaje, ki oddajajo le del dneva ali so geografsko zaklenjene.
    always = ["#EXTM3U"]
    sometimes: list[str] = []
    for code, label in COUNTRIES.items():
        rows = per_country[code]
        total += len(rows)
        single = ["#EXTM3U"]
        for entry in rows:
            group = label if not entry["note"] else f"{label} - obcasni"
            single += render(entry, group)
            (sometimes if entry["note"] else always).extend(render(entry, group))
        with open(os.path.join(outdir, f"{code}.m3u"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(single) + "\n")
    with open(os.path.join(outdir, "ex-yu.m3u"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(always + sometimes) + "\n")

    print(f"zapisano: {total} kanalov v {outdir}")
    for code, label in COUNTRIES.items():
        rows = per_country[code]
        stalni = sum(1 for e in rows if not e["note"])
        print(f"  {label:<24} {len(rows):>3}  od tega stalnih {stalni}")
    return per_country


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", help="mapa z lokalnimi kopijami virov (offline)")
    ap.add_argument("--out", default=".", help="izhodna mapa (privzeto trenutna)")
    args = ap.parse_args()
    build(args.cache, args.out)


if __name__ == "__main__":
    main()
