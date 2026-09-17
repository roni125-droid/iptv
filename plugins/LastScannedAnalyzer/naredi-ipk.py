#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zgradi paket .ipk za namestitev z opkg.

Uporaba:
    python3 naredi-ipk.py                 # paket nastane v tej mapi
    python3 naredi-ipk.py --out /tmp      # paket nastane drugje
    python3 naredi-ipk.py --preveri       # paket zgradi in ga razpakira nazaj

Zakaj lastna skripta in ne opkg-build:
    Paket .ipk je arhiv "ar" s tremi clanicami: debian-binary, control.tar.gz
    in data.tar.gz. Vse troje zna narediti Python sam, zato skripta tece na
    vsakem racunalniku s Pythonom, tudi na Windows, brez binutils in brez
    orodij OpenEmbedded.

Paket je ponovljiv: dvakratna gradnja iz istih datotek da bajt za bajtom
enak paket, ker so casi in lastniki v arhivu nastavljeni na stalno vrednost.
"""

from __future__ import annotations

import argparse
import gzip
import io
import os
import re
import sys
import tarfile

MAPA = os.path.dirname(os.path.abspath(__file__))

PAKET = "enigma2-plugin-extensions-lastscannedanalyzer"
ARHITEKTURA = "all"          # cista koda Python, neodvisna od procesorja
VZDRZEVALEC = "roni125-droid"
CILJ = "/usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer"

# Datoteke, ki gredo na risiver. Dokumentacija ostane v repozitoriju.
VSEBINA = (
    "__init__.py", "plugin.py", "lamedb.py", "bouquets.py", "picon.py",
    "skin.py", "update.py", "preizkus.py", "plugin.png", "version.json",
)

OPIS = """Pregled kanalov iz zadnjega skeniranja.
 Po skeniranju pokaze, kateri kanali so novi ali se niso v nobenem buketu,
 in jih z modrim gumbom prenese v izbrani ali na novo ustvarjeni buket.
 Pokaze tudi picon in podatke o transponderju."""

POSTINST = """#!/bin/sh
# Stare prevedene datoteke znajo prekriti novo kodo.
rm -f %(cilj)s/*.pyc %(cilj)s/*.pyo
rm -rf %(cilj)s/__pycache__
echo ""
echo "LastScanned Analyzer je namescen."
echo "Za zagon ponovno zazenite vmesnik:  init 4 && sleep 3 && init 3"
echo "ali prek menija: Standby / Restart -> Restart GUI."
echo ""
exit 0
""" % {"cilj": CILJ}

POSTRM = """#!/bin/sh
# Prevedenih datotek opkg ne vodi, zato mapa brez tega ostane za nami.
rm -f %(cilj)s/*.pyc %(cilj)s/*.pyo
rm -rf %(cilj)s/__pycache__
rmdir %(cilj)s 2>/dev/null
echo "LastScanned Analyzer je odstranjen. Shranjeno stanje ostaja v"
echo "/etc/enigma2/lastscanned_analyzer.json, brisete ga rocno."
exit 0
""" % {"cilj": CILJ}

CAS = 0                      # stalen cas, da je paket ponovljiv


# --- razlicica -------------------------------------------------------------

def razlicica():
    """Razlicico vzamemo iz plugin.py, da paket in plugin ne razideta."""
    besedilo = open(os.path.join(MAPA, "plugin.py"), encoding="utf-8").read()
    zadetek = re.search(r'^RAZLICICA = "([^"]+)"', besedilo, re.M)
    if not zadetek:
        print("napaka: v plugin.py ni vrstice RAZLICICA", file=sys.stderr)
        sys.exit(1)
    return zadetek.group(1)


def preveri_version_json(oznaka):
    pot = os.path.join(MAPA, "version.json")
    try:
        import json
        with open(pot, encoding="utf-8") as fh:
            tam = str(json.load(fh).get("version", ""))
    except Exception:
        return
    if tam and tam != oznaka:
        print("opozorilo: version.json pravi %s, plugin.py pa %s"
              % (tam, oznaka))


# --- sestavljanje arhivov --------------------------------------------------

def _clan(ime, podatki, nacin):
    info = tarfile.TarInfo(ime)
    info.size = len(podatki)
    info.mtime = CAS
    info.mode = nacin
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    return info, io.BytesIO(podatki)


def _tar_gz(datoteke):
    """datoteke: seznam (ime v arhivu, vsebina, nacin) -> stisnjen tar."""
    surovi = io.BytesIO()
    with tarfile.open(fileobj=surovi, mode="w", format=tarfile.GNU_FORMAT) as t:
        mape = set()
        for ime, _, _ in datoteke:
            mapa = os.path.dirname(ime)
            while mapa and mapa not in ("./", ".") and mapa not in mape:
                mape.add(mapa)
                mapa = os.path.dirname(mapa)
        for mapa in sorted(mape):
            info = tarfile.TarInfo(mapa)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            info.mtime = CAS
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            t.addfile(info)
        for ime, vsebina, nacin in datoteke:
            info, tok = _clan(ime, vsebina, nacin)
            t.addfile(info, tok)
    stisnjen = io.BytesIO()
    with gzip.GzipFile(fileobj=stisnjen, mode="wb", mtime=CAS) as g:
        g.write(surovi.getvalue())
    return stisnjen.getvalue()


def _ar(clani):
    """clani: seznam (ime, podatki) -> arhiv ar, kot ga pricakuje opkg."""
    izid = [b"!<arch>\n"]
    for ime, podatki in clani:
        glava = "%-16s%-12d%-6d%-6d%-8o%-10d`\n" % (
            ime, CAS, 0, 0, 0o100644, len(podatki))
        izid.append(glava.encode("ascii"))
        izid.append(podatki)
        if len(podatki) % 2:
            izid.append(b"\n")          # clanice so poravnane na sodo dolzino
    return b"".join(izid)


def zgradi(izhodna_mapa):
    oznaka = razlicica()
    preveri_version_json(oznaka)

    # data.tar.gz - datoteke, kot lezijo na risiverju
    podatki = []
    for ime in VSEBINA:
        pot = os.path.join(MAPA, ime)
        if not os.path.exists(pot):
            print("napaka: manjka %s" % ime, file=sys.stderr)
            sys.exit(1)
        with open(pot, "rb") as fh:
            podatki.append(("." + CILJ + "/" + ime, fh.read(), 0o644))
    data = _tar_gz(podatki)

    # control.tar.gz - opis paketa in skripti ob namestitvi
    nadzor = (
        "Package: %s\n"
        "Version: %s\n"
        "Architecture: %s\n"
        "Maintainer: %s\n"
        "Section: multimedia\n"
        "Priority: optional\n"
        "Installed-Size: %d\n"
        "Description: %s\n"
    ) % (PAKET, oznaka, ARHITEKTURA, VZDRZEVALEC,
         sum(len(v) for _, v, _ in podatki), OPIS)
    control = _tar_gz([
        ("./control", nadzor.encode("utf-8"), 0o644),
        ("./postinst", POSTINST.encode("utf-8"), 0o755),
        ("./postrm", POSTRM.encode("utf-8"), 0o755),
    ])

    paket = _ar([
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control),
        ("data.tar.gz", data),
    ])

    ime = "%s_%s_%s.ipk" % (PAKET, oznaka, ARHITEKTURA)
    pot = os.path.join(izhodna_mapa, ime)
    with open(pot, "wb") as fh:
        fh.write(paket)
    print("zgrajeno: %s (%d bajtov, %d datotek)"
          % (pot, len(paket), len(podatki)))
    return pot


# --- preverjanje -----------------------------------------------------------

def razberi_ar(pot):
    """Razpakiraj arhiv ar nazaj, da vidimo, kaj je v paketu res koncalo."""
    with open(pot, "rb") as fh:
        vsebina = fh.read()
    if not vsebina.startswith(b"!<arch>\n"):
        raise ValueError("to ni arhiv ar")
    kazalo = 8
    clani = []
    while kazalo + 60 <= len(vsebina):
        glava = vsebina[kazalo:kazalo + 60]
        if glava[58:60] != b"`\n":
            raise ValueError("pokvarjena glava clanice")
        ime = glava[0:16].decode("ascii").strip().rstrip("/")
        velikost = int(glava[48:58].decode("ascii").strip())
        zacetek = kazalo + 60
        clani.append((ime, vsebina[zacetek:zacetek + velikost]))
        kazalo = zacetek + velikost + (velikost % 2)
    return clani


def preveri(pot):
    clani = razberi_ar(pot)
    imena = [ime for ime, _ in clani]
    print("\nclanice arhiva: %s" % ", ".join(imena))
    if imena != ["debian-binary", "control.tar.gz", "data.tar.gz"]:
        print("NAPAKA: napacne ali napacno razvrscene clanice")
        return 1

    napake = 0
    for ime, podatki in clani:
        if ime == "debian-binary":
            if podatki != b"2.0\n":
                print("NAPAKA: debian-binary ni 2.0"); napake += 1
            continue
        with tarfile.open(fileobj=io.BytesIO(podatki), mode="r:gz") as t:
            print("\n%s:" % ime)
            for clan in t.getmembers():
                if clan.isdir():
                    continue
                print("  %-58s %5d B  %o" % (clan.name, clan.size, clan.mode))
            if ime == "control.tar.gz":
                nadzor = t.extractfile("./control").read().decode("utf-8")
                print("\n--- control ---\n%s" % nadzor.rstrip())
                for polje in ("Package:", "Version:", "Architecture:"):
                    if polje not in nadzor:
                        print("NAPAKA: v control manjka %s" % polje)
                        napake += 1
                for skript in ("./postinst", "./postrm"):
                    if t.getmember(skript).mode & 0o111 == 0:
                        print("NAPAKA: %s ni izvrsljiv" % skript)
                        napake += 1
            else:
                poti = [c.name for c in t.getmembers() if c.isfile()]
                manjka = [i for i in VSEBINA
                          if ("." + CILJ + "/" + i) not in poti]
                if manjka:
                    print("NAPAKA: v paketu manjka %s" % ", ".join(manjka))
                    napake += 1

    print("\n%s" % ("preverjanje je uspelo" if not napake
                    else "napak: %d" % napake))
    return 1 if napake else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=MAPA, help="kam naj zapisem paket")
    ap.add_argument("--preveri", action="store_true",
                    help="paket po gradnji razpakiraj in izpisi vsebino")
    args = ap.parse_args()

    pot = zgradi(args.out)
    return preveri(pot) if args.preveri else 0


if __name__ == "__main__":
    sys.exit(main())
