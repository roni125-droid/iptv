# -*- coding: utf-8 -*-
"""Preizkus plugina brez risiverja.

Enigme na racunalniku ni, zato tu podtaknemo nekaj praznih modulov z istimi
imeni. Vse, kar ni risalnik zaslona - branje lamedb, iskanje novih kanalov,
pisanje buketov - se s tem da preveriti na navadnem racunalniku, preden
datoteke prenesemo na boks.

    python3 preizkus.py
"""

import os
import shutil
import sys
import tempfile
import types

MAPA = os.path.dirname(os.path.abspath(__file__))


# --- nadomestki za module Enigme ------------------------------------------

def _podtakni():
    def modul(ime, **vsebina):
        m = types.ModuleType(ime)
        for kljuc, vrednost in vsebina.items():
            setattr(m, kljuc, vrednost)
        sys.modules[ime] = m
        return m

    class Prazno(object):
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, ime):
            return Prazno()

        def __call__(self, *args, **kwargs):
            return Prazno()

    class Vsebina(object):
        """Nadomestek za eListboxPythonMultiContent."""

        def __init__(self):
            self.vrstice = []

        def setFont(self, *args):
            pass

        def setItemHeight(self, *args):
            pass

        def setList(self, vrstice):
            self.vrstice = vrstice

        def invalidateEntry(self, kazalo):
            pass

    class SeznamOsnova(object):
        def __init__(self, seznam, *args, **kwargs):
            self.list = seznam
            self.l = Vsebina()

        def getCurrent(self):
            return self.list[0] if self.list else None

        def getSelectionIndex(self):
            return 0

        def moveToIndex(self, kazalo):
            pass

    modul("enigma", eListboxPythonMultiContent=Vsebina, gFont=Prazno,
          eDVBDB=Prazno(), RT_HALIGN_LEFT=1, RT_HALIGN_RIGHT=2,
          RT_VALIGN_CENTER=4)

    for ime in ("Components", "Screens", "Plugins", "Tools"):
        modul(ime)
    modul("Components.ActionMap", ActionMap=Prazno)
    modul("Components.Label", Label=Prazno)
    modul("Components.MenuList", MenuList=SeznamOsnova)
    modul("Components.MultiContent",
          MultiContentEntryText=lambda **kwargs: ("besedilo", kwargs))
    modul("Components.Pixmap", Pixmap=Prazno)
    modul("Plugins.Plugin", PluginDescriptor=Prazno)
    modul("Screens.ChoiceBox", ChoiceBox=Prazno)
    modul("Screens.MessageBox", MessageBox=Prazno)
    modul("Screens.Screen", Screen=Prazno)
    modul("Screens.VirtualKeyBoard", VirtualKeyBoard=Prazno)
    modul("Tools.LoadPixmap", LoadPixmap=Prazno)


# --- pripomocki ------------------------------------------------------------

PREVERJENIH = [0, 0]


def trdi(pogoj, opis):
    PREVERJENIH[0] += 1
    if pogoj:
        print("  ok    %s" % opis)
    else:
        PREVERJENIH[1] += 1
        print("  PADLO %s" % opis)


LAMEDB = """eDVB services /4/
transponders
00820000:0441:0001
\ts 11914000:27500000:0:2:130:2:0:1:2:0:0
/
00c00000:07d0:0085
\ts 12245000:27500000:1:3:3592:2:0:0:1:0:0
/
end
services
0085:00820000:0441:0001:25:0
Prvi HD
p:Provajder A,c:0100a,f:40
0086:00820000:0441:0001:1:0
Drugi SD
p:Provajder A,c:0100a
00a1:00c00000:07d0:0085:2:0
Radio Ena
p:Provajder B
end
sat feeds
end
"""

BUKET = """#NAME Moji programi
#SERVICE 1:0:19:85:441:1:820000:0:0:0:
#DESCRIPTION Prvi HD
"""

KAZALO = ('#NAME Bouquets (TV)\n#SERVICE 1:7:1:0:0:0:0:0:0:0:'
          'FROM BOUQUET "userbouquet.moji.tv" ORDER BY bouquet\n')


def pripravi(mapa):
    with open(os.path.join(mapa, "lamedb"), "w") as fh:
        fh.write(LAMEDB)
    with open(os.path.join(mapa, "bouquets.tv"), "w") as fh:
        fh.write(KAZALO)
    with open(os.path.join(mapa, "userbouquet.moji.tv"), "w") as fh:
        fh.write(BUKET)


# --- preizkusi -------------------------------------------------------------

def main():
    _podtakni()
    sys.path.insert(0, os.path.dirname(MAPA))
    paket = os.path.basename(MAPA)
    lamedb = __import__("%s.lamedb" % paket, fromlist=["lamedb"])
    bouquets = __import__("%s.bouquets" % paket, fromlist=["bouquets"])
    plugin = __import__("%s.plugin" % paket, fromlist=["plugin"])

    mapa = tempfile.mkdtemp(prefix="lsa-preizkus-")
    try:
        pripravi(mapa)

        print("\nbranje baze kanalov")
        kanali = lamedb.preberi(os.path.join(mapa, "lamedb"))
        trdi(len(kanali) == 3, "prebrani so trije kanali")
        po_imenu = dict((k.ime, k) for k in kanali)
        prvi = po_imenu.get("Prvi HD")
        trdi(prvi is not None and prvi.ref == "1:0:19:85:441:1:820000:0:0:0:",
             "sklic kanala je v obliki, ki jo pisejo buketi")
        trdi(prvi is not None and prvi.locljivost == "H.264 HD",
             "vrsta storitve 25 je prepoznana kot H.264 HD")
        trdi(prvi is not None and prvi.transponder.polarizacija == "H",
             "polarizacija je prebrana s transponderja")
        trdi(prvi is not None and "13.0 E" in prvi.transponder.satelit(),
             "orbitalni polozaj je 13.0 E")
        radio = po_imenu.get("Radio Ena")
        trdi(radio is not None and radio.radio, "radio je prepoznan kot radio")
        trdi(radio is not None and "0.8 W" in radio.transponder.satelit(),
             "zahodni polozaj 3592 je 0.8 W")

        print("\niskanje novih kanalov")
        v_buketih = bouquets.sklici_v_buketih(mapa)
        trdi(len(v_buketih) == 1, "v buketu je en kanal")
        plugin.analiziraj(kanali, v_buketih, set())
        novi = [k.ime for k in kanali if k.nov]
        trdi("Prvi HD" not in novi, "kanal iz buketa ni nov")
        trdi(sorted(novi) == ["Drugi SD", "Radio Ena"],
             "nerazvrscena kanala sta oznacena kot [NEW]")
        trdi(kanali[0].nov, "novi so na vrhu seznama")

        print("\nkanal, ki se je pojavil sele po zadnjem zagonu")
        znani = set(bouquets.normaliziraj(k.ref) for k in kanali
                    if k.ime != "Drugi SD")
        plugin.analiziraj(kanali, v_buketih | set(
            bouquets.normaliziraj(k.ref) for k in kanali), znani)
        novi = [k.ime for k in kanali if k.nov]
        trdi(novi == ["Drugi SD"],
             "kanal v buketu je nov, ce ga prej ni bilo v bazi")

        print("\nprenos v obstojeci buket")
        plugin.analiziraj(kanali, v_buketih, set())
        buket = bouquets.seznam(mapa)[0]
        trdi(buket.ime == "Moji programi", "ime buketa je prebrano iz #NAME")
        izbrani = [k for k in kanali if k.nov]
        dodanih, podvojenih = bouquets.dodaj(buket, izbrani, mapa)
        trdi((dodanih, podvojenih) == (2, 0), "dodana sta dva kanala")
        dodanih, podvojenih = bouquets.dodaj(buket, izbrani, mapa)
        trdi((dodanih, podvojenih) == (0, 2),
             "ponovni prenos istih kanalov ne podvaja vrstic")
        trdi(os.path.exists(os.path.join(mapa, "userbouquet.moji.tv.lsa-bak")),
             "pred spremembo nastane varnostna kopija buketa")
        po_prenosu = bouquets.sklici_v_buketih(mapa)
        trdi(len(po_prenosu) == 3, "v buketu so zdaj vsi trije kanali")
        plugin.analiziraj(kanali, po_prenosu, set())
        trdi(not any(k.nov for k in kanali),
             "po prenosu ni vec nobenega [NEW]")

        print("\nustvarjanje novega buketa")
        nov = bouquets.ustvari("Moj novi buket", "tv", mapa)
        trdi(nov.datoteka == "userbouquet.mojnovibuket.tv",
             "ime datoteke je izpeljano iz imena buketa")
        kazalo = open(os.path.join(mapa, "bouquets.tv")).read()
        trdi(nov.datoteka in kazalo, "nov buket je vpisan v kazalo")
        trdi(len(bouquets.seznam(mapa)) == 2, "buketa sta zdaj dva")
        bouquets.dodaj(nov, kanali[:1], mapa)
        vsebina = open(os.path.join(mapa, nov.datoteka)).read()
        trdi(vsebina.startswith("#NAME Moj novi buket"),
             "nov buket ima ime v prvi vrstici")
        trdi("#SERVICE " in vsebina, "kanal je zapisan v nov buket")
        podvojen = bouquets.ustvari("Moj novi buket", "tv", mapa)
        trdi(podvojen.datoteka == "userbouquet.mojnovibuket_2.tv",
             "enako ime ne prepise obstojecega buketa")

        print("\nizris vrstice v seznamu")
        seznam = plugin.SeznamKanalov()
        kanali[0].oznacen = True
        vrstica = seznam._vrstica(kanali[0])
        trdi(vrstica[0] is kanali[0], "vrstica nosi svoj kanal")
        besedila = [d[1].get("text") for d in vrstica[1:]]
        trdi("[ * ]" in besedila, "oznacen kanal dobi zvezdico")
        kanali[0].oznacen = False
        kanali[0].nov = True
        besedila = [d[1].get("text") for d in seznam._vrstica(kanali[0])[1:]]
        trdi("[NEW]" in besedila, "nov kanal dobi oznako [NEW]")

        print("\nzapis stanja")
        plugin.STANJE = os.path.join(mapa, "stanje.json")
        plugin.zapisi_stanje(["1:0:19:85:441:1:820000:0:0:0:"])
        trdi(plugin.preberi_stanje().get("refs") ==
             ["1:0:19:85:441:1:820000:0:0:0:"], "stanje se zapise in prebere")

        print("\nzapis lamedb5")
        pot5 = os.path.join(mapa, "lamedb5")
        with open(pot5, "w") as fh:
            fh.write('eDVB services /5/\n'
                     't:00820000:0441:0001,s 11914000:27500000:0:2:130:2\n'
                     's:0085:00820000:0441:0001:25:0,"Prvi HD",'
                     '"p:Provajder A,c:0100a"\n')
        kanali5 = lamedb.preberi(pot5)
        trdi(len(kanali5) == 1 and kanali5[0].ime == "Prvi HD",
             "novejsi zapis lamedb5 se prebere enako")
        trdi(kanali5[0].ref == "1:0:19:85:441:1:820000:0:0:0:",
             "sklic iz lamedb5 je enak kot iz lamedb")
    finally:
        shutil.rmtree(mapa, ignore_errors=True)

    print("\npreverjenih %d, padlo %d" % (PREVERJENIH[0], PREVERJENIH[1]))
    return 1 if PREVERJENIH[1] else 0


if __name__ == "__main__":
    sys.exit(main())
