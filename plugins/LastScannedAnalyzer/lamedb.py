# -*- coding: utf-8 -*-
"""Branje baze kanalov Enigma2 (lamedb in lamedb5).

Zakaj sploh beremo datoteko in ne vprasamo sistema:
    eServiceCenter zna povedati ime kanala, podatkov o transponderju pa za
    kanal, ki ta hip ne igra, ne da. Frekvenca, polarizacija in hitrost
    simbolov so zapisane samo v lamedb, zato jo preberemo sami.

Podprta sta oba zapisa:
    lamedb  (glava "eDVB services /4/") - tri vrstice na kanal,
    lamedb5 (glava "eDVB services /5/") - ena vrstica na kanal.

Modul je namenoma brez uvozov iz enigme, da ga je mogoce pognati in
preizkusiti tudi na navadnem racunalniku:

    python3 lamedb.py /pot/do/lamedb
"""

import os
import sys

PRIVZETA_MAPA = "/etc/enigma2"

# --- slovarji za berljiv izpis --------------------------------------------

POLARIZACIJA = {0: "H", 1: "V", 2: "CL", 3: "CR"}

FEC = {
    0: "Auto", 1: "1/2", 2: "2/3", 3: "3/4", 4: "5/6", 5: "7/8", 6: "8/9",
    7: "3/5", 8: "4/5", 9: "9/10", 15: "None",
}

SISTEM = {0: "DVB-S", 1: "DVB-S2"}

MODULACIJA = {0: "Auto", 1: "QPSK", 2: "8PSK", 3: "QAM16", 4: "16APSK",
              5: "32APSK"}

# Vrsta storitve pove tudi, kaksno sliko pricakujemo. Stevilke so iz
# standarda DVB, dodatki nad 0x80 pa iz prakse Enigme.
VRSTA = {
    1: ("TV", "SD (MPEG2)"),
    2: ("Radio", "-"),
    3: ("Teletext", "-"),
    4: ("NVOD", "-"),
    10: ("Radio", "-"),
    12: ("Data", "-"),
    17: ("TV", "MPEG4 SD"),
    22: ("TV", "H.264 SD"),
    25: ("TV", "H.264 HD"),
    26: ("TV", "HEVC SD"),
    27: ("TV", "HEVC HD"),
    31: ("TV", "HEVC UHD (4K)"),
    134: ("TV", "UHD"),
    139: ("TV", "UHD"),
    195: ("Data", "-"),
}


def opis_vrste(stype):
    return VRSTA.get(stype, ("TV" if stype < 128 else "Data", "?"))


def orbita_besedilo(pos):
    """3592 -> "0.8 W", 192 -> "19.2 E"."""
    try:
        pos = int(pos)
    except (TypeError, ValueError):
        return "?"
    if pos > 1800:
        return "%.1f W" % ((3600 - pos) / 10.0)
    return "%.1f E" % (pos / 10.0)


# --- transponder -----------------------------------------------------------

class Transponder(object):
    """Parametri prenosa, s katerega je kanal prisel."""

    def __init__(self, vrsta, polja):
        self.vrsta = vrsta          # "s" satelit, "c" kabel, "t" antena
        self.polja = polja

    def _p(self, i, privzeto=0):
        try:
            return int(self.polja[i])
        except (IndexError, ValueError, TypeError):
            return privzeto

    # --- posamezne vrednosti ---
    @property
    def frekvenca(self):
        return self._p(0)

    @property
    def hitrost_simbolov(self):
        return self._p(1)

    @property
    def orbita(self):
        return self._p(4) if self.vrsta == "s" else None

    @property
    def polarizacija(self):
        return POLARIZACIJA.get(self._p(2), "?") if self.vrsta == "s" else "-"

    def satelit(self):
        """Ime satelita. Ce Enigma tece, vprasamo njo, sicer stopinje."""
        if self.vrsta != "s":
            return {"c": "Kabel (DVB-C)", "t": "Antena (DVB-T)"}.get(
                self.vrsta, "?")
        stopinje = orbita_besedilo(self.orbita)
        try:
            from Components.NimManager import nimmanager
            ime = nimmanager.getSatDescription(self.orbita)
            if ime:
                return "%s (%s)" % (ime, stopinje)
        except Exception:
            pass
        return stopinje

    def vrstice(self):
        """Pari (oznaka, vrednost) za prikaz v oknu INFO."""
        if self.vrsta == "s":
            return [
                ("Satellite", self.satelit()),
                ("Frequency", "%d MHz" % (self.frekvenca // 1000)),
                ("Polarization", self.polarizacija),
                ("Symbol rate", "%d" % (self.hitrost_simbolov // 1000)),
                ("FEC", FEC.get(self._p(3), "?")),
                ("System", "%s / %s" % (SISTEM.get(self._p(7), "DVB-S"),
                                        MODULACIJA.get(self._p(8), "Auto"))),
            ]
        if self.vrsta == "c":
            return [
                ("Source", "Cable (DVB-C)"),
                ("Frequency", "%d kHz" % self.frekvenca),
                ("Symbol rate", "%d" % (self.hitrost_simbolov // 1000)),
                ("Modulation", MODULACIJA.get(self._p(3), "Auto")),
            ]
        return [
            ("Source", "Terrestrial (DVB-T)"),
            ("Frequency", "%d kHz" % self.frekvenca),
        ]




def razclleni_transponder(besedilo):
    """Iz vrstice "s 11914000:27500000:0:..." naredi Transponder."""
    besedilo = (besedilo or "").strip()
    if not besedilo:
        return None
    vrsta, _, ostanek = besedilo.partition(" ")
    vrsta = vrsta.strip().lower()
    if vrsta not in ("s", "c", "t"):
        return None
    return Transponder(vrsta, ostanek.strip().split(":"))


# --- kanal -----------------------------------------------------------------

class Kanal(object):
    """En kanal iz baze, skupaj s transponderjem, s katerega je prisel."""

    def __init__(self, sid, ns, tsid, onid, stype, ime, ponudnik, transponder):
        self.sid = sid
        self.ns = ns
        self.tsid = tsid
        self.onid = onid
        self.stype = stype
        self.ime = ime or "(brez imena)"
        self.ponudnik = ponudnik or ""
        self.transponder = transponder
        self.nov = False            # nastavi analiza v plugin.py
        self.oznacen = False        # zeleni gumb

    @property
    def ref(self):
        """Sklic v obliki, kot ga pisejo buketi Enigme."""
        return "1:0:%X:%X:%X:%X:%X:0:0:0:" % (
            self.stype, self.sid, self.tsid, self.onid, self.ns)

    @property
    def radio(self):
        return opis_vrste(self.stype)[0] == "Radio"

    @property
    def locljivost(self):
        return opis_vrste(self.stype)[1]

    def vrstice(self):
        """Pari (oznaka, vrednost) za okno INFO."""
        podatki = [("Name", self.ime),
                   ("Provider", self.ponudnik or "(neznan)")]
        if self.transponder:
            podatki += self.transponder.vrstice()
        podatki += [
            ("Resolution", self.locljivost),
            ("Type", opis_vrste(self.stype)[0]),
            ("Service ref", self.ref),
        ]
        return podatki


def _kljuc(ns, tsid, onid):
    """Enoten kljuc, ne glede na vodilne nicle in velikost crk."""
    try:
        return (int(ns, 16), int(tsid, 16), int(onid, 16))
    except (ValueError, TypeError):
        return None


def _ponudnik(zastavice):
    for del_ in (zastavice or "").split(","):
        del_ = del_.strip()
        if del_.startswith("p:"):
            return del_[2:]
    return ""


# --- zapis /4/ -------------------------------------------------------------

def _preberi_v4(vrstice):
    transponderji = {}
    kanali = []
    i, n = 0, len(vrstice)

    while i < n and vrstice[i].strip() != "transponders":
        i += 1
    i += 1
    while i < n:
        glava = vrstice[i].strip()
        i += 1
        if glava == "end":
            break
        if not glava or glava == "/":
            continue
        polja = glava.split(":")
        kljuc = _kljuc(*polja[:3]) if len(polja) >= 3 else None
        parametri = vrstice[i].strip() if i < n else ""
        i += 1
        while i < n and vrstice[i].strip() != "/":
            i += 1
        i += 1
        tp = razclleni_transponder(parametri)
        if kljuc and tp:
            transponderji[kljuc] = tp

    while i < n and vrstice[i].strip() != "services":
        i += 1
    i += 1
    while i < n:
        glava = vrstice[i].strip()
        i += 1
        if glava == "end":
            break
        if not glava:
            continue
        ime = vrstice[i].strip() if i < n else ""
        i += 1
        zastavice = vrstice[i].strip() if i < n else ""
        i += 1
        polja = glava.split(":")
        if len(polja) < 5:
            continue
        try:
            sid = int(polja[0], 16)
            ns = int(polja[1], 16)
            tsid = int(polja[2], 16)
            onid = int(polja[3], 16)
            stype = int(polja[4])
        except ValueError:
            continue
        kanali.append(Kanal(sid, ns, tsid, onid, stype, ime,
                            _ponudnik(zastavice),
                            transponderji.get((ns, tsid, onid))))
    return kanali


# --- zapis /5/ -------------------------------------------------------------

def _navedki(besedilo):
    """Vrni vse odseke med narekovaji."""
    izid, trenutni, znotraj = [], [], False
    for znak in besedilo:
        if znak == '"':
            if znotraj:
                izid.append("".join(trenutni))
                trenutni = []
            znotraj = not znotraj
        elif znotraj:
            trenutni.append(znak)
    return izid


def _preberi_v5(vrstice):
    transponderji = {}
    kanali = []
    surovi = []

    for vrstica in vrstice:
        vrstica = vrstica.strip()
        if vrstica.startswith("t:"):
            glava, _, ostanek = vrstica.partition(",")
            polja = glava.split(":")
            if len(polja) < 4:
                continue
            kljuc = _kljuc(polja[1], polja[2], polja[3])
            tp = razclleni_transponder(ostanek)
            if kljuc and tp:
                transponderji[kljuc] = tp
        elif vrstica.startswith("s:"):
            glava, _, ostanek = vrstica.partition(",")
            polja = glava.split(":")
            if len(polja) < 6:
                continue
            try:
                sid = int(polja[1], 16)
                ns = int(polja[2], 16)
                tsid = int(polja[3], 16)
                onid = int(polja[4], 16)
                stype = int(polja[5])
            except ValueError:
                continue
            deli = _navedki(ostanek)
            ime = deli[0] if deli else ""
            zastavice = deli[1] if len(deli) > 1 else ""
            surovi.append((sid, ns, tsid, onid, stype, ime, zastavice))

    for sid, ns, tsid, onid, stype, ime, zastavice in surovi:
        kanali.append(Kanal(sid, ns, tsid, onid, stype, ime,
                            _ponudnik(zastavice),
                            transponderji.get((ns, tsid, onid))))
    return kanali


# --- javni vstop -----------------------------------------------------------

def pot_baze(mapa=PRIVZETA_MAPA):
    """Vrni pot do baze, ki v tej sliki obstaja."""
    for ime in ("lamedb", "lamedb5"):
        pot = os.path.join(mapa, ime)
        if os.path.exists(pot):
            return pot
    return None


def preberi(pot=None, mapa=PRIVZETA_MAPA):
    """Vrni seznam kanalov iz baze. Ob napaki vrne prazen seznam."""
    pot = pot or pot_baze(mapa)
    if not pot or not os.path.exists(pot):
        return []
    try:
        with open(pot, "r", errors="replace") as fh:
            vsebina = fh.read()
    except TypeError:                      # Python 2 nima errors=
        with open(pot, "r") as fh:
            vsebina = fh.read()
    except (IOError, OSError):
        return []

    vrstice = vsebina.splitlines()
    if not vrstice:
        return []
    glava = vrstice[0].strip()
    if "/5/" in glava or any(v.startswith("s:") for v in vrstice[:20]):
        return _preberi_v5(vrstice)
    return _preberi_v4(vrstice)


def cas_spremembe(pot=None, mapa=PRIVZETA_MAPA):
    pot = pot or pot_baze(mapa)
    try:
        return os.path.getmtime(pot)
    except (OSError, TypeError):
        return 0


if __name__ == "__main__":
    izbrana = sys.argv[1] if len(sys.argv) > 1 else None
    vsi = preberi(izbrana)
    print("kanalov: %d" % len(vsi))
    for kanal in vsi[:10]:
        tp = kanal.transponder
        print("  %-28s %-16s %s" % (
            kanal.ime[:28], kanal.ponudnik[:16],
            ("%s %s %s" % (tp.satelit(), tp.frekvenca // 1000,
                           tp.polarizacija)) if tp else "brez transponderja"))
        print("      %s" % kanal.ref)
