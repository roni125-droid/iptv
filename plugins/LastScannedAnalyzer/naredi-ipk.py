#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zgradi paketa .ipk za namestitev z opkg.

Nastaneta dva paketa:

    ..._all.ipk            plugin sam
    ...-cistilec_all.ipk   pocisti ostanke starejsih, rocno prekopiranih
                           namestitev; pravilno namescenega plugina se ne
                           dotakne

Uporaba:
    python3 naredi-ipk.py                 # oba paketa v to mapo
    python3 naredi-ipk.py --kaj plugin    # samo plugin
    python3 naredi-ipk.py --kaj cistilec  # samo cistilec
    python3 naredi-ipk.py --out /tmp      # paketa nastaneta drugje
    python3 naredi-ipk.py --preveri       # po gradnji ju razpakira nazaj

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

CISTILEC = PAKET + "-cistilec"
OPOMBA = "/usr/share/lastscanned-analyzer/cistilec.txt"

CAS = 0                      # stalen cas, da je paket ponovljiv

OPIS_CISTILCA = """Pocisti ostanke starih namestitev LastScanned Analyzerja.
 Rocno prekopiranih datotek opkg ne vodi, zato ostanejo tudi po namestitvi
 paketa. Ta paket jih odstrani: prevedene datoteke, napacno vgnezdene ali
 napacno pisane kopije in ostanke v /tmp. Ce je plugin namescen prek opkg,
 pusti njegove datoteke pri miru."""

# Skript tece ob namestitvi cistilca. Kaj brise, je odvisno od tega, ali je
# plugin namescen prek opkg. Ce je, so njegove datoteke svete in gredo samo
# tuji ostanki; ce ni, je vse v mapi rocna kopija in gre cela.
POSTINST_CISTILCA = """#!/bin/sh
PLUGIN=%(cilj)s
PAKET=%(paket)s
EXT=$(dirname "$PLUGIN")

lastnik=ne
for mapa in /usr/lib/opkg/info /var/lib/opkg/info /usr/lib/ipkg/info; do
    if [ -f "$mapa/$PAKET.list" ]; then
        lastnik=da
    fi
done

stevilo=0
odstrani() {
    if [ -e "$1" ]; then
        rm -rf "$1"
        echo "  odstranjeno: $1"
        stevilo=$((stevilo + 1))
    fi
}

echo ""
echo "LastScanned Analyzer - ciscenje starih datotek"
if [ "$lastnik" = da ]; then
    echo "Plugin je namescen prek opkg, zato se njegovih datotek ne dotikam."
else
    echo "Plugina opkg ne vodi, kar pomeni rocno prekopirane datoteke."
fi
echo ""

# 1. prevedene datoteke, ki znajo prekriti novo kodo
odstrani "$PLUGIN/__pycache__"
for koncnica in pyc pyo; do
    for datoteka in "$PLUGIN"/*.$koncnica; do
        odstrani "$datoteka"
    done
done

# 2. kopije na napacnem mestu ali z napacnim imenom
odstrani "$PLUGIN/LastScannedAnalyzer"
odstrani "$EXT/lastscannedanalyzer"
odstrani "$EXT/LastScanned_Analyzer"
odstrani "$EXT/LastScannedAnalyser"
odstrani "/tmp/LastScannedAnalyzer"

# 3. sama mapa plugina
if [ "$lastnik" = da ]; then
    # Pustimo datoteke tekoce razlicice, vse drugo je ostanek.
    if [ -d "$PLUGIN" ]; then
        for datoteka in "$PLUGIN"/*; do
            [ -e "$datoteka" ] || continue
            case "${datoteka##*/}" in
                %(znane)s) ;;
                *) odstrani "$datoteka" ;;
            esac
        done
    fi
else
    odstrani "$PLUGIN"
fi

echo ""
if [ "$stevilo" = 0 ]; then
    echo "Ni bilo kaj pocistiti, vse je bilo ze v redu."
else
    echo "Pocistil sem $stevilo stvari."
    echo "Ponovno zazenite vmesnik:  init 4 && sleep 3 && init 3"
fi
echo ""
echo "Shranjeno stanje /etc/enigma2/lastscanned_analyzer.json ostaja"
echo "nedotaknjeno, brisete ga rocno, ce ga ne potrebujete vec."
echo ""
exit 0
"""

POSTRM_CISTILCA = """#!/bin/sh
rm -rf %(opomba_mapa)s 2>/dev/null
exit 0
"""


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


def _nadzor(paket, oznaka, opis, velikost):
    return (
        "Package: %s\n"
        "Version: %s\n"
        "Architecture: %s\n"
        "Maintainer: %s\n"
        "Section: multimedia\n"
        "Priority: optional\n"
        "Installed-Size: %d\n"
        "Description: %s\n"
    ) % (paket, oznaka, ARHITEKTURA, VZDRZEVALEC, velikost, opis)


def _zapisi(izhodna_mapa, paket, oznaka, control, data):
    arhiv = _ar([
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control),
        ("data.tar.gz", data),
    ])
    pot = os.path.join(izhodna_mapa,
                       "%s_%s_%s.ipk" % (paket, oznaka, ARHITEKTURA))
    with open(pot, "wb") as fh:
        fh.write(arhiv)
    return pot, len(arhiv)


def zgradi_cistilec(izhodna_mapa):
    """Paket, ki ob namestitvi pocisti ostanke starih namestitev."""
    oznaka = razlicica()
    postinst = POSTINST_CISTILCA % {
        "cilj": CILJ, "paket": PAKET, "znane": "|".join(VSEBINA)}
    postrm = POSTRM_CISTILCA % {"opomba_mapa": os.path.dirname(OPOMBA)}

    opomba = (
        "LastScanned Analyzer - cistilec %s\n\n"
        "Delo je opravil skript postinst ob namestitvi tega paketa.\n"
        "Paket sam ne vsebuje plugina in ga lahko odstranite z\n"
        "    opkg remove %s\n" % (oznaka, CISTILEC)
    ).encode("utf-8")
    data = _tar_gz([("." + OPOMBA, opomba, 0o644)])

    control = _tar_gz([
        ("./control", _nadzor(CISTILEC, oznaka, OPIS_CISTILCA,
                              len(opomba)).encode("utf-8"), 0o644),
        ("./postinst", postinst.encode("utf-8"), 0o755),
        ("./postrm", postrm.encode("utf-8"), 0o755),
    ])

    pot, velikost = _zapisi(izhodna_mapa, CISTILEC, oznaka, control, data)
    print("zgrajeno: %s (%d bajtov, cistilec)" % (pot, velikost))
    return pot


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
    nadzor = _nadzor(PAKET, oznaka, OPIS,
                     sum(len(v) for _, v, _ in podatki))
    control = _tar_gz([
        ("./control", nadzor.encode("utf-8"), 0o644),
        ("./postinst", POSTINST.encode("utf-8"), 0o755),
        ("./postrm", POSTRM.encode("utf-8"), 0o755),
    ])

    pot, velikost = _zapisi(izhodna_mapa, PAKET, oznaka, control, data)
    print("zgrajeno: %s (%d bajtov, %d datotek)"
          % (pot, velikost, len(podatki)))
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


def preveri(pot, plugin=True):
    """Razpakiraj paket nazaj in preveri, da je v njem, kar mora biti."""
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
            elif plugin:
                poti = [c.name for c in t.getmembers() if c.isfile()]
                manjka = [i for i in VSEBINA
                          if ("." + CILJ + "/" + i) not in poti]
                if manjka:
                    print("NAPAKA: v paketu manjka %s" % ", ".join(manjka))
                    napake += 1
            else:
                # Cistilec ne sme prinesti plugina s sabo, saj bi ga pri
                # odstranitvi odnesel s seboj.
                for clan in t.getmembers():
                    if CILJ in clan.name:
                        print("NAPAKA: cistilec nosi datoteko plugina (%s)"
                              % clan.name)
                        napake += 1

    print("\n%s" % ("preverjanje je uspelo" if not napake
                    else "napak: %d" % napake))
    return 1 if napake else 0


def main():
    ap = argparse.ArgumentParser(
        description="Zgradi paketa .ipk (plugin in cistilec).")
    ap.add_argument("--out", default=MAPA, help="kam naj zapisem paketa")
    ap.add_argument("--kaj", choices=("oba", "plugin", "cistilec"),
                    default="oba", help="kateri paket naj zgradim")
    ap.add_argument("--preveri", action="store_true",
                    help="paket po gradnji razpakiraj in izpisi vsebino")
    args = ap.parse_args()

    napake = 0
    if args.kaj in ("oba", "plugin"):
        pot = zgradi(args.out)
        if args.preveri:
            napake += preveri(pot, plugin=True)
    if args.kaj in ("oba", "cistilec"):
        pot = zgradi_cistilec(args.out)
        if args.preveri:
            napake += preveri(pot, plugin=False)
    return 1 if napake else 0


if __name__ == "__main__":
    sys.exit(main())
