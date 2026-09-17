# -*- coding: utf-8 -*-
"""LastScanned Analyzer - pregled kanalov iz zadnjega skeniranja.

Kaj resi:
    Po skeniranju risiver najde na stotine kanalov, a v seznamu kanalov jih
    ni mogoce lociti od starih. Plugin prebere bazo kanalov (lamedb), jih
    primerja z buketi in s stanjem od zadnjic ter z oznako [NEW] pokaze
    tiste, ki so novi ali se niso razvrsceni v noben buket.

Gumbi:
    RDECI    izhod
    ZELENI   oznaci / odznaci kanal ([ * ])
    RUMENI   pokazi samo [NEW] kanale, se enkrat pa spet vse
    MODRI    prenesi oznacene (ali vse nove) v buket, tudi v nov buket
    MENU     Scan Channels / Check for Updates
    INFO     picon, satelit, frekvenca, polarizacija, hitrost simbolov
    OK       enako kot zeleni gumb

Po prenosu plugin sam poklice reloadBouquets, zato risiverja ni treba
ponovno zaganjati.
"""

import os
import json
import time

from enigma import eListboxPythonMultiContent, gFont, eDVBDB, \
    RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.LoadPixmap import LoadPixmap

from . import bouquets
from . import lamedb
from . import picon as piconi
from . import skin as videz
from . import update as posodobitve

RAZLICICA = "1.0"

MAPA_PLUGINA = os.path.dirname(os.path.abspath(__file__))
STANJE = "/etc/enigma2/lastscanned_analyzer.json"

NASLOV = "LastScanned Analyzer"


# --- shranjeno stanje ------------------------------------------------------

def preberi_stanje():
    try:
        with open(STANJE, "r") as fh:
            return json.load(fh)
    except Exception:
        return {}


def zapisi_stanje(sklici):
    try:
        with open(STANJE, "w") as fh:
            json.dump({"refs": sorted(sklici), "cas": time.time(),
                       "razlicica": RAZLICICA}, fh)
    except Exception:
        pass


# --- analiza ---------------------------------------------------------------

def analiziraj(kanali, sklici_v_buketih, prejsnji_sklici):
    """Oznaci, kateri kanali so novi, in jih razvrsti.

    Nov je kanal, ki po skeniranju ni pristal v nobenem buketu, ali kanal,
    ki ga ob zadnjem zagonu plugina v bazi se ni bilo. Prvi pogoj ujame
    obicajno skeniranje, drugi pa kanal, ki ga je Enigma sama dodala v
    buket, a je vseeno nov.

    Ob prvem zagonu prejsnjih sklicev ni. Takrat velja samo prvi pogoj,
    sicer bi bili novi cisto vsi kanali v bazi.
    """
    prvi_zagon = not prejsnji_sklici
    for kanal in kanali:
        sklic = bouquets.normaliziraj(kanal.ref)
        nerazvrscen = sklic not in sklici_v_buketih
        nov_po_skeniranju = (not prvi_zagon) and sklic not in prejsnji_sklici
        kanal.nov = nerazvrscen or nov_po_skeniranju
        kanal.oznacen = False
    # Novi gredo na vrh, sicer bi jih iskali sredi tisocih starih.
    kanali.sort(key=lambda k: (not k.nov, k.ime.lower()))
    return kanali


# --- seznam ----------------------------------------------------------------

class SeznamKanalov(MenuList):
    """Vrstica kanala: oznaka, ime, ponudnik, locljivost, [NEW]."""

    def __init__(self):
        MenuList.__init__(self, [], True, eListboxPythonMultiContent)
        self.l.setFont(0, gFont("Regular", videz.PISAVA_VELIKA))
        self.l.setFont(1, gFont("Regular", videz.PISAVA_MALA))
        self.l.setItemHeight(videz.VISINA_VRSTICE)

    def _vrstica(self, kanal):
        barva_imena = videz.BARVA_NOVO if kanal.nov else videz.BARVA_BESEDILA
        if kanal.oznacen:
            barva_imena = videz.BARVA_OZNACENO
        visina = videz.VISINA_VRSTICE
        levo = RT_HALIGN_LEFT | RT_VALIGN_CENTER
        desno = RT_HALIGN_RIGHT | RT_VALIGN_CENTER
        return [
            kanal,
            MultiContentEntryText(
                pos=(videz.S_OZNAKA[0], 0), size=(videz.S_OZNAKA[1], visina),
                font=0, flags=levo, text="[ * ]" if kanal.oznacen else "",
                color=videz.BARVA_OZNACENO, color_sel=videz.BARVA_OZNACENO),
            MultiContentEntryText(
                pos=(videz.S_IME[0], 0), size=(videz.S_IME[1], visina),
                font=0, flags=levo, text=kanal.ime,
                color=barva_imena, color_sel=videz.BARVA_IZBRANO),
            MultiContentEntryText(
                pos=(videz.S_PONUDNIK[0], 0),
                size=(videz.S_PONUDNIK[1], visina), font=1, flags=levo,
                text=kanal.ponudnik, color=videz.BARVA_BLEDA,
                color_sel=videz.BARVA_BLEDA),
            MultiContentEntryText(
                pos=(videz.S_LOCLJIVOST[0], 0),
                size=(videz.S_LOCLJIVOST[1], visina), font=1, flags=levo,
                text=kanal.locljivost, color=videz.BARVA_BLEDA,
                color_sel=videz.BARVA_BLEDA),
            MultiContentEntryText(
                pos=(videz.S_NOVO[0], 0), size=(videz.S_NOVO[1], visina),
                font=1, flags=desno, text="[NEW]" if kanal.nov else "",
                color=videz.BARVA_NOVO, color_sel=videz.BARVA_NOVO),
        ]

    def postavi(self, kanali):
        self.list = [self._vrstica(k) for k in kanali]
        self.l.setList(self.list)

    def osvezi_vrstico(self, kazalo, kanal):
        """Prerisi eno vrstico, da seznam ob oznacevanju ne poskoci."""
        if 0 <= kazalo < len(self.list):
            self.list[kazalo] = self._vrstica(kanal)
            self.l.invalidateEntry(kazalo)

    def trenutni(self):
        izbrano = self.getCurrent()
        return izbrano[0] if izbrano else None

    def kazalo(self):
        """Katera vrstica je izbrana. Starejse slike imajo drugo ime."""
        for ime in ("getSelectionIndex", "getSelectedIndex"):
            metoda = getattr(self, ime, None)
            if metoda:
                return metoda()
        return 0


# --- okno INFO -------------------------------------------------------------

class OknoInfo(Screen):
    skin = videz.INFO

    def __init__(self, session, kanal):
        Screen.__init__(self, session)
        self.kanal = kanal
        self.setTitle("Channel info")
        self["naslov"] = Label(kanal.ime)
        self["povzetek"] = Label("")
        self["oznake"] = Label("")
        self["vrednosti"] = Label("")
        self["picon"] = Pixmap()
        self["key_red"] = Label("Close")
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {"ok": self.close, "cancel": self.close, "red": self.close}, -1)
        self.onLayoutFinish.append(self.napolni)

    # Kratek povzetek gre ob picon, podrobnosti v dva stolpca. Pisava na
    # risiverju ni enakosirinska, zato stolpcev ne poravnavamo s presledki.
    POVZETEK = ("Provider", "Type", "Resolution")

    def napolni(self):
        povzetek, oznake, vrednosti = [], [], []
        for oznaka, vrednost in self.kanal.vrstice():
            if oznaka == "Name":
                continue
            if oznaka in self.POVZETEK:
                povzetek.append("%s: %s" % (oznaka, vrednost))
            else:
                oznake.append(oznaka)
                vrednosti.append(str(vrednost))
        povzetek.append("State: %s" % ("[NEW]" if self.kanal.nov
                                       else "already in a bouquet"))
        self["povzetek"].setText("\n".join(povzetek))
        self["oznake"].setText("\n".join(oznake))
        self["vrednosti"].setText("\n".join(vrednosti))

        pot = piconi.najdi(self.kanal.ref, self.kanal.ime)
        if pot:
            slika = LoadPixmap(pot)
            if slika:
                try:
                    self["picon"].instance.setScale(1)
                except Exception:
                    pass
                self["picon"].instance.setPixmap(slika)


# --- glavno okno -----------------------------------------------------------

class LastScannedAnalyzer(Screen):
    skin = videz.GLAVNI

    def __init__(self, session):
        Screen.__init__(self, session)
        self.setTitle(NASLOV)
        self.vsi = []
        self.prikazani = []
        self.samo_novi = False
        self.napaka = ""

        self["naslov"] = Label(NASLOV)
        self["stanje"] = Label("")
        self["g_ime"] = Label("CHANNEL")
        self["g_ponudnik"] = Label("PROVIDER")
        self["g_locljivost"] = Label("RESOLUTION")
        self["g_stanje"] = Label("STATE")
        self["podrobno"] = Label("")
        self["seznam"] = SeznamKanalov()
        self["key_red"] = Label("Exit")
        self["key_green"] = Label("Mark")
        self["key_yellow"] = Label("Only NEW")
        self["key_blue"] = Label("Copy to bouquet")

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "MenuActions",
             "EPGSelectActions", "InfobarEPGActions", "DirectionActions"],
            {
                "ok": self.oznaci,
                "cancel": self.close,
                "red": self.close,
                "green": self.oznaci,
                "yellow": self.preklopi_filter,
                "blue": self.v_buket,
                "menu": self.meni,
                "info": self.podrobnosti,
                "showEventInfo": self.podrobnosti,
                "up": self.gor,
                "down": self.dol,
                "left": self.stran_gor,
                "right": self.stran_dol,
            }, -1)

        self.onLayoutFinish.append(self.nalozi)

    # --- branje in analiza ---
    def nalozi(self, ohrani_kazalo=False):
        kazalo = self["seznam"].kazalo() if ohrani_kazalo else 0
        self.vsi = lamedb.preberi()
        self.napaka = "" if self.vsi else (
            "Could not read the channel database (%s)."
            % (lamedb.pot_baze() or "/etc/enigma2/lamedb"))
        prejsnji = set(preberi_stanje().get("refs", []))
        analiziraj(self.vsi, bouquets.sklici_v_buketih(), prejsnji)
        if not prejsnji:
            zapisi_stanje([bouquets.normaliziraj(k.ref) for k in self.vsi])
        self.osvezi(kazalo)

    def osvezi(self, kazalo=0):
        self.prikazani = [k for k in self.vsi if k.nov] if self.samo_novi \
            else list(self.vsi)
        self["seznam"].postavi(self.prikazani)
        if self.prikazani:
            self["seznam"].moveToIndex(min(kazalo, len(self.prikazani) - 1))
        self.osvezi_stanje()

    def osvezi_stanje(self):
        novih = sum(1 for k in self.vsi if k.nov)
        oznacenih = sum(1 for k in self.vsi if k.oznacen)
        self["stanje"].setText(
            "Total: %d    NEW: %d    Marked: %d    Filter: %s"
            % (len(self.vsi), novih, oznacenih,
               "NEW only" if self.samo_novi else "all"))
        kanal = self["seznam"].trenutni()
        if not kanal:
            self["podrobno"].setText(self.napaka)
            return
        tp = kanal.transponder
        self["podrobno"].setText(
            "%s   %s" % (kanal.ref,
                         tp.satelit() if tp else "no transponder data"))

    # --- premikanje ---
    def gor(self):
        self["seznam"].up()
        self.osvezi_stanje()

    def dol(self):
        self["seznam"].down()
        self.osvezi_stanje()

    def stran_gor(self):
        self["seznam"].pageUp()
        self.osvezi_stanje()

    def stran_dol(self):
        self["seznam"].pageDown()
        self.osvezi_stanje()

    # --- zeleni gumb ---
    def oznaci(self):
        kanal = self["seznam"].trenutni()
        if not kanal:
            return
        kanal.oznacen = not kanal.oznacen
        kazalo = self["seznam"].kazalo()
        self["seznam"].osvezi_vrstico(kazalo, kanal)
        self["seznam"].down()
        self.osvezi_stanje()

    # --- rumeni gumb ---
    def preklopi_filter(self):
        self.samo_novi = not self.samo_novi
        self["key_yellow"].setText("Show all" if self.samo_novi
                                   else "Only NEW")
        self.osvezi()

    # --- INFO ---
    def podrobnosti(self):
        kanal = self["seznam"].trenutni()
        if kanal:
            self.session.open(OknoInfo, kanal)

    # --- MENU ---
    def meni(self):
        self.session.openWithCallback(
            self._meni_izbran, ChoiceBox, title="Options",
            list=[("Scan Channels", "scan"),
                  ("Check for Updates", "update"),
                  ("Mark all NEW channels", "mark"),
                  ("Clear all marks", "clear"),
                  ("Forget saved state (rebuild [NEW])", "reset")])

    def _meni_izbran(self, izbira):
        if not izbira:
            return
        {"scan": self.skeniraj, "update": self.posodobi,
         "mark": self.oznaci_vse, "clear": self.pocisti_oznake,
         "reset": self.pozabi_stanje}[izbira[1]]()

    def oznaci_vse(self):
        for kanal in self.prikazani:
            if kanal.nov:
                kanal.oznacen = True
        self.osvezi(self["seznam"].kazalo())

    def pocisti_oznake(self):
        for kanal in self.vsi:
            kanal.oznacen = False
        self.osvezi(self["seznam"].kazalo())

    def pozabi_stanje(self):
        try:
            os.remove(STANJE)
        except OSError:
            pass
        self.nalozi()

    def skeniraj(self):
        """Odpri skeniranje Enigme. Ime zaslona se med slikami razlikuje."""
        for modul, razred in (("Screens.ScanSetup", "ScanSetup"),
                              ("Screens.ScanSetup", "ScanSimple")):
            try:
                zaslon = getattr(__import__(modul, fromlist=[razred]), razred)
                self.session.openWithCallback(self._po_skeniranju, zaslon)
                return
            except Exception:
                continue
        self.session.open(
            MessageBox, "Could not open the scan screen. Start the scan"
            " from the receiver menu.", MessageBox.TYPE_ERROR, timeout=8)

    def _po_skeniranju(self, *args):
        self.nalozi()

    def posodobi(self):
        stanje, podatki = posodobitve.poglej(RAZLICICA)
        if stanje == "ni-vira":
            self.session.open(
                MessageBox, "No update source is set. Write the address of"
                " version.json into VIR in update.py.",
                MessageBox.TYPE_INFO, timeout=8)
            return
        if stanje == "napaka":
            self.session.open(
                MessageBox, "Update check failed:\n%s"
                % podatki, MessageBox.TYPE_ERROR, timeout=8)
            return
        if stanje == "enako":
            self.session.open(
                MessageBox, "You already have the latest version (%s)."
                % RAZLICICA, MessageBox.TYPE_INFO, timeout=6)
            return
        self.nova_razlicica = podatki
        self.session.openWithCallback(
            self._potrjena_posodobitev, MessageBox,
            "Version %s is available (you have %s).\n\n%s\n\nInstall it now?"
            % (podatki.get("version"), RAZLICICA,
               podatki.get("changes", "")), MessageBox.TYPE_YESNO)

    def _potrjena_posodobitev(self, potrjeno):
        if not potrjeno:
            return
        uspeh, opis = posodobitve.namesti(self.nova_razlicica, MAPA_PLUGINA)
        self.session.open(
            MessageBox,
            ("Update installed (%s).\nRestart Enigma2 to run the new"
             " version." % opis) if uspeh
            else "Installation failed:\n%s" % opis,
            MessageBox.TYPE_INFO if uspeh else MessageBox.TYPE_ERROR)

    # --- MODRI gumb: prenos v buket ---
    def _za_prenos(self):
        oznaceni = [k for k in self.vsi if k.oznacen]
        return oznaceni if oznaceni else [k for k in self.vsi if k.nov]

    def v_buket(self):
        izbrani = self._za_prenos()
        if not izbrani:
            self.session.open(
                MessageBox, "Nothing to copy. Mark channels with the"
                " GREEN button, or scan for new ones.", MessageBox.TYPE_INFO,
                timeout=6)
            return
        self.za_prenos = izbrani
        seznam = [("%s  (%s)" % (b.ime, b.vrsta), b)
                  for b in bouquets.seznam()]
        seznam.append(("+ Create New Bouquet", "nov"))
        self.session.openWithCallback(
            self._buket_izbran, ChoiceBox,
            title="Copy %d channel(s) to:" % len(izbrani), list=seznam)

    def _buket_izbran(self, izbira):
        if not izbira:
            return
        cilj = izbira[1]
        if cilj == "nov":
            self.session.openWithCallback(
                self._ime_vpisano, VirtualKeyBoard, title="New bouquet name",
                text="")
            return
        self._prenesi(cilj)

    def _ime_vpisano(self, ime):
        if not ime:
            return
        vrsta = "radio" if all(k.radio for k in self.za_prenos) else "tv"
        try:
            buket = bouquets.ustvari(ime, vrsta)
        except (IOError, OSError) as napaka:
            self.session.open(
                MessageBox, "Could not create the bouquet:\n%s" % napaka,
                MessageBox.TYPE_ERROR)
            return
        self._prenesi(buket)

    def _prenesi(self, buket):
        try:
            dodanih, podvojenih = bouquets.dodaj(buket, self.za_prenos)
        except (IOError, OSError) as napaka:
            self.session.open(
                MessageBox, "Could not write to the bouquet:\n%s" % napaka,
                MessageBox.TYPE_ERROR)
            return

        # Enigma prebere bukete takoj, zato risiverja ni treba zagnati znova.
        try:
            eDVBDB.getInstance().reloadBouquets()
        except Exception:
            pass

        # Preneseni kanali od zdaj niso vec novi.
        preneseni = set(bouquets.normaliziraj(k.ref) for k in self.za_prenos)
        znani = set(preberi_stanje().get("refs", []))
        zapisi_stanje(znani | preneseni |
                      set(bouquets.normaliziraj(k.ref) for k in self.vsi))

        for kanal in self.vsi:
            if bouquets.normaliziraj(kanal.ref) in preneseni:
                kanal.nov = False
                kanal.oznacen = False

        sporocilo = "Copied %d channel(s) to \"%s\"." % (dodanih,
                                                             buket.ime)
        if podvojenih:
            sporocilo += "\n%d were already in that bouquet." % podvojenih
        self.session.open(MessageBox, sporocilo, MessageBox.TYPE_INFO,
                          timeout=6)
        self.osvezi(self["seznam"].kazalo())


# --- vstopna tocka ---------------------------------------------------------

def odpri(session, **kwargs):
    session.open(LastScannedAnalyzer)


def Plugins(**kwargs):
    opis = "Review channels from the last scan, copy them to bouquets"
    return [
        PluginDescriptor(name=NASLOV, description=opis,
                         where=PluginDescriptor.WHERE_PLUGINMENU,
                         icon="plugin.png", fnc=odpri),
        PluginDescriptor(name=NASLOV, description=opis,
                         where=PluginDescriptor.WHERE_EXTENSIONSMENU,
                         fnc=odpri),
    ]
