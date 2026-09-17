# -*- coding: utf-8 -*-
"""Branje in pisanje buketov Enigma2.

Buketi so navadne besedilne datoteke v /etc/enigma2:

    bouquets.tv              kazalo, katere bukete naj Enigma pokaze
    userbouquet.<ime>.tv     posamezen buket s sklici na kanale

Modul je brez uvozov iz enigme, da ga je mogoce preizkusiti tudi na
racunalniku. Ponovno branje (reloadBouquets) sprozi plugin.py.
"""

import os
import re

PRIVZETA_MAPA = "/etc/enigma2"

KAZALO = {"tv": "bouquets.tv", "radio": "bouquets.radio"}
VRSTICA_KAZALA = ('#SERVICE 1:7:%d:0:0:0:0:0:0:0:FROM BOUQUET "%s"'
                  ' ORDER BY bouquet')
SKLIC_RE = re.compile(r'FROM BOUQUET "([^"]+)"')


class Buket(object):
    def __init__(self, datoteka, ime, vrsta):
        self.datoteka = datoteka        # userbouquet.moj.tv
        self.ime = ime                  # ime, kot ga vidi gledalec
        self.vrsta = vrsta              # "tv" ali "radio"

    def __repr__(self):
        return "<Buket %s (%s)>" % (self.ime, self.datoteka)


def normaliziraj(ref):
    """Sklic v enotno obliko, da primerjava ne pade zaradi vodilnih nicel."""
    polja = (ref or "").strip().split(":")
    if len(polja) < 10:
        return (ref or "").strip().upper()
    izid = polja[:2]
    for polje in polja[2:10]:
        try:
            izid.append("%X" % int(polje, 16))
        except ValueError:
            izid.append(polje.upper())
    return ":".join(izid)


def _preberi(pot):
    try:
        with open(pot, "r") as fh:
            return fh.read().splitlines()
    except (IOError, OSError):
        return []


def _zapisi(pot, vrstice):
    """Zapisi prek zacasne datoteke, da ob prekinitvi buket ne ostane pol."""
    zacasna = pot + ".lsa-tmp"
    with open(zacasna, "w") as fh:
        fh.write("\n".join(vrstice).rstrip("\n") + "\n")
    os.rename(zacasna, pot)


def varnostna_kopija(pot):
    """Enkratna kopija datoteke, preden jo prvic spremenimo."""
    kopija = pot + ".lsa-bak"
    if os.path.exists(pot) and not os.path.exists(kopija):
        try:
            with open(pot, "r") as vir, open(kopija, "w") as cilj:
                cilj.write(vir.read())
        except (IOError, OSError):
            pass


def ime_buketa(pot):
    for vrstica in _preberi(pot):
        if vrstica.startswith("#NAME"):
            return vrstica[5:].strip()
    return os.path.basename(pot)


def seznam(mapa=PRIVZETA_MAPA, vrste=("tv", "radio")):
    """Vsi uporabniski buketi, v vrstnem redu iz kazala."""
    najdeni = []
    for vrsta in vrste:
        kazalo = os.path.join(mapa, KAZALO[vrsta])
        for vrstica in _preberi(kazalo):
            zadetek = SKLIC_RE.search(vrstica)
            if not zadetek:
                continue
            datoteka = zadetek.group(1)
            pot = os.path.join(mapa, datoteka)
            if os.path.exists(pot):
                najdeni.append(Buket(datoteka, ime_buketa(pot), vrsta))
    return najdeni


def sklici_v_buketih(mapa=PRIVZETA_MAPA):
    """Mnozica vseh sklicev, ki so ze v kateremkoli buketu.

    Kanal, ki ga tu ni, je po skeniranju ostal nerazvrscen - to je tisto,
    kar nas zanima kot [NEW].
    """
    izid = set()
    for buket in seznam(mapa):
        for vrstica in _preberi(os.path.join(mapa, buket.datoteka)):
            if vrstica.startswith("#SERVICE "):
                izid.add(normaliziraj(vrstica[9:]))
    return izid


def _prosto_ime(mapa, osnova, koncnica):
    ime = "userbouquet.%s.%s" % (osnova, koncnica)
    stevec = 1
    while os.path.exists(os.path.join(mapa, ime)):
        stevec += 1
        ime = "userbouquet.%s_%d.%s" % (osnova, stevec, koncnica)
    return ime


def ustvari(ime, vrsta="tv", mapa=PRIVZETA_MAPA):
    """Naredi nov buket in ga vpisi v kazalo. Vrne Buket."""
    ime = (ime or "").strip() or "New bouquet"
    osnova = re.sub(r"[^a-z0-9]+", "", ime.lower()) or "novi"
    datoteka = _prosto_ime(mapa, osnova, vrsta)

    _zapisi(os.path.join(mapa, datoteka), ["#NAME %s" % ime])

    kazalo = os.path.join(mapa, KAZALO[vrsta])
    varnostna_kopija(kazalo)
    vrstice = _preberi(kazalo)
    if not vrstice:
        vrstice = ["#NAME Bouquets (%s)" % vrsta.upper()]
    vrstice.append(VRSTICA_KAZALA % (1 if vrsta == "tv" else 2, datoteka))
    _zapisi(kazalo, vrstice)
    return Buket(datoteka, ime, vrsta)


def dodaj(buket, kanali, mapa=PRIVZETA_MAPA):
    """Pripni kanale v buket. Vrne (dodanih, ze_bilo_notri)."""
    pot = os.path.join(mapa, buket.datoteka)
    varnostna_kopija(pot)
    vrstice = _preberi(pot)
    if not vrstice:
        vrstice = ["#NAME %s" % buket.ime]

    ze_notri = set()
    for vrstica in vrstice:
        if vrstica.startswith("#SERVICE "):
            ze_notri.add(normaliziraj(vrstica[9:]))

    dodanih, podvojenih = 0, 0
    for kanal in kanali:
        if normaliziraj(kanal.ref) in ze_notri:
            podvojenih += 1
            continue
        vrstice.append("#SERVICE %s" % kanal.ref)
        vrstice.append("#DESCRIPTION %s" % kanal.ime)
        ze_notri.add(normaliziraj(kanal.ref))
        dodanih += 1

    if dodanih:
        _zapisi(pot, vrstice)
    return dodanih, podvojenih
