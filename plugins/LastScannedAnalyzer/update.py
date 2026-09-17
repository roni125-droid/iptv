# -*- coding: utf-8 -*-
"""Rocno preverjanje posodobitev (gumb MENU -> Check for Updates).

Na naslovu VIR pricakujemo majhno datoteko JSON:

    {
      "version": "1.1",
      "url": "https://primer.si/lastscanned-1.1.tar.gz",
      "changes": "Kaj je novega"
    }

Arhiv tar.gz mora vsebovati mapo LastScannedAnalyzer z datotekami plugina.
Nic se ne namesti samo od sebe - plugin.py prej vprasa uporabnika.
"""

import json
import os
import shutil
import tarfile
import tempfile

try:                                   # Python 3
    from urllib.request import urlopen, Request
except ImportError:                    # Python 2 na starejsih slikah
    from urllib2 import urlopen, Request

# Naslov, kjer stoji version.json. Dokler je prazen, gumb "Check for
# Updates" samo pove, da vir ni nastavljen, in ne javlja napake.
VIR = ""

CAKANJE = 15


def _prenesi(naslov, cakanje=CAKANJE):
    zahteva = Request(naslov, headers={"User-Agent": "LastScannedAnalyzer"})
    odgovor = urlopen(zahteva, timeout=cakanje)
    try:
        return odgovor.read()
    finally:
        odgovor.close()


def _stevilke(razlicica):
    deli = []
    for del_ in str(razlicica).split("."):
        try:
            deli.append(int(del_))
        except ValueError:
            deli.append(0)
    return tuple(deli)


def novejsa(tam, tu):
    return _stevilke(tam) > _stevilke(tu)


def poglej(trenutna, vir=VIR):
    """Vrni (stanje, podatki).

    Stanje je "novo", "enako", "ni-vira" ali "napaka".
    """
    if not vir:
        return "ni-vira", ""
    try:
        podatki = json.loads(_prenesi(vir).decode("utf-8", "replace"))
    except Exception as napaka:
        return "napaka", str(napaka)
    tam = str(podatki.get("version", "")).strip()
    if not tam:
        return "napaka", "odgovor brez polja version"
    if novejsa(tam, trenutna):
        return "novo", podatki
    return "enako", podatki


def namesti(podatki, mapa_plugina):
    """Prenesi arhiv in ga razpakiraj cez mapo plugina. Vrne (uspeh, opis)."""
    naslov = podatki.get("url")
    if not naslov:
        return False, "odgovor nima polja url"
    zacasna = tempfile.mkdtemp(prefix="lsa-")
    arhiv = os.path.join(zacasna, "posodobitev.tar.gz")
    try:
        with open(arhiv, "wb") as fh:
            fh.write(_prenesi(naslov, cakanje=60))
        with tarfile.open(arhiv, "r:gz") as tar:
            clani = [c for c in tar.getmembers()
                     if not c.name.startswith(("/", ".."))
                     and ".." not in c.name]
            tar.extractall(zacasna, members=clani)
        izvor = os.path.join(zacasna, "LastScannedAnalyzer")
        if not os.path.isdir(izvor):
            izvor = zacasna
        prepisanih = 0
        for ime in os.listdir(izvor):
            if not ime.endswith(".py") and ime != "version.json":
                continue
            shutil.copy(os.path.join(izvor, ime),
                        os.path.join(mapa_plugina, ime))
            prepisanih += 1
        if not prepisanih:
            return False, "v arhivu ni datotek plugina"
        return True, "posodobljenih datotek: %d" % prepisanih
    except Exception as napaka:
        return False, str(napaka)
    finally:
        shutil.rmtree(zacasna, ignore_errors=True)
