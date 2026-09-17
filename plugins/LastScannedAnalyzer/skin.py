# -*- coding: utf-8 -*-
"""Temni videz HD (1280x720), ki se sam prilagodi velikosti zaslona.

Videz je zapisan tu in ne v temi risiverja, da je plugin videti enako na
vsakem boksu. Barve so izbrane za gledanje s kavca: temna podlaga, svetlo
besedilo, poudarki samo tam, kjer nekaj pomenijo.

Risan je za 1280x720. Ce vmesnik risiverja tece v 1920x1080, ob zagonu vse
mere in pisave pomnozimo s faktorjem, sicer bi okno sedelo v kotu zaslona.
"""

import re

# --- barve -----------------------------------------------------------------

OZADJE = "#101418"
PAS = "#161b22"
CRTA = "#2b3240"
BESEDILO = "#e6edf3"
BLEDO = "#8a94a3"
IZBRANO = "#22303f"

# barve v seznamu (stevila, ker jih tako rabi MultiContentEntryText)
BARVA_BESEDILA = 0xD8DEE9
BARVA_BLEDA = 0x8A94A3
BARVA_NOVO = 0x7EE081
BARVA_OZNACENO = 0xFFD166
BARVA_KODIRAN = 0xE07A5F
BARVA_IZBRANO = 0xFFFFFF

# --- mere pri 1280x720 -----------------------------------------------------

_VISINA_VRSTICE = 44
_S_OZNAKA = (8, 62)          # [ * ]
_S_IME = (78, 540)
_S_PONUDNIK = (628, 250)
_S_LOCLJIVOST = (888, 120)
_S_KODIRAN = (1016, 56)      # CA = kodiran, prazno = prost
_S_NOVO = (1080, 120)
_PISAVA_VELIKA = 24
_PISAVA_MALA = 20
_ZAMIK_SEZNAMA = 20          # x, kjer se zacne seznam


# --- sestavljanje XML ------------------------------------------------------

_GUMB = (
    '<eLabel position="%d,664" size="10,40" backgroundColor="%s" />'
    '<widget name="%s" position="%d,664" size="256,40" font="Regular;22"'
    ' foregroundColor="' + BESEDILO + '" backgroundColor="' + OZADJE + '"'
    ' transparent="1" valign="center" />'
)

_GLAVA = (
    '<widget name="g_%s" position="%d,84" size="%d,28" font="Regular;19"'
    ' foregroundColor="' + BLEDO + '" backgroundColor="' + OZADJE + '"'
    ' transparent="1" valign="center" halign="%s" />'
)


def _gumbi():
    barve = (("#b0292f", "key_red", 24), ("#2e7d32", "key_green", 336),
             ("#b8860b", "key_yellow", 648), ("#1d5f9e", "key_blue", 960))
    return "".join(_GUMB % (x, barva, ime, x + 18) for barva, ime, x in barve)


def _glave():
    """Naslovi stolpcev stojijo tocno nad stolpci v seznamu."""
    stolpci = (("ime", _S_IME, "left"), ("ponudnik", _S_PONUDNIK, "left"),
               ("locljivost", _S_LOCLJIVOST, "left"),
               ("kodiran", _S_KODIRAN, "left"),
               ("stanje", _S_NOVO, "right"))
    return "".join(_GLAVA % (ime, x + _ZAMIK_SEZNAMA, sirina, poravnava)
                   for ime, (x, sirina), poravnava in stolpci)


_GLAVNI = """
<screen name="LastScannedAnalyzer" position="0,0" size="1280,720"
        title="LastScanned Analyzer" flags="wfNoBorder"
        backgroundColor="{ozadje}">
  <eLabel position="0,0" size="1280,76" backgroundColor="{pas}" />
  <widget name="naslov" position="24,12" size="640,44" font="Regular;32"
          foregroundColor="{besedilo}" backgroundColor="{pas}"
          transparent="1" valign="center" />
  <widget name="stanje" position="672,12" size="584,44" font="Regular;22"
          halign="right" foregroundColor="{bledo}" backgroundColor="{pas}"
          transparent="1" valign="center" />
  <eLabel position="0,76" size="1280,2" backgroundColor="{crta}" />
  {glave}
  <widget name="seznam" position="20,116" size="1240,492"
          scrollbarMode="showOnDemand" backgroundColor="{ozadje}"
          foregroundColor="{besedilo}" backgroundColorSelected="{izbrano}"
          foregroundColorSelected="#ffffff" transparent="0" />
  <eLabel position="0,616" size="1280,2" backgroundColor="{crta}" />
  <widget name="podrobno" position="24,624" size="1232,30" font="Regular;20"
          foregroundColor="{bledo}" backgroundColor="{ozadje}"
          transparent="1" valign="center" />
  {gumbi}
</screen>
""".format(ozadje=OZADJE, pas=PAS, crta=CRTA, besedilo=BESEDILO, bledo=BLEDO,
           izbrano=IZBRANO, gumbi=_gumbi(), glave=_glave())

_INFO = """
<screen name="LastScannedInfo" position="center,center" size="920,600"
        title="Channel info" backgroundColor="{ozadje}">
  <eLabel position="0,0" size="920,72" backgroundColor="{pas}" />
  <widget name="naslov" position="24,12" size="872,48" font="Regular;30"
          foregroundColor="{besedilo}" backgroundColor="{pas}"
          transparent="1" valign="center" />
  <eLabel position="24,96" size="232,144" backgroundColor="{pas}" />
  <widget name="picon" position="30,102" size="220,132" alphatest="blend" />
  <widget name="povzetek" position="284,100" size="612,136" font="Regular;23"
          foregroundColor="{bledo}" backgroundColor="{ozadje}"
          transparent="1" />
  <eLabel position="24,258" size="872,2" backgroundColor="{crta}" />
  <widget name="oznake" position="24,274" size="240,250" font="Regular;23"
          foregroundColor="{bledo}" backgroundColor="{ozadje}"
          transparent="1" />
  <widget name="vrednosti" position="280,274" size="616,250" font="Regular;23"
          foregroundColor="{besedilo}" backgroundColor="{ozadje}"
          transparent="1" />
  <eLabel position="24,546" size="10,36" backgroundColor="#b0292f" />
  <widget name="key_red" position="42,546" size="400,36" font="Regular;22"
          foregroundColor="{besedilo}" backgroundColor="{ozadje}"
          transparent="1" valign="center" />
</screen>
""".format(ozadje=OZADJE, pas=PAS, crta=CRTA, besedilo=BESEDILO, bledo=BLEDO)


# --- prilagoditev velikosti zaslona ---------------------------------------

def zaznaj_faktor():
    """Kolikokrat vecji je zaslon od 1280x720. Zunaj Enigme je to 1."""
    try:
        from enigma import getDesktop
        zaslon = getDesktop(0).size()
        faktor = min(zaslon.width() / 1280.0, zaslon.height() / 720.0)
        return faktor if faktor > 0 else 1.0
    except Exception:
        return 1.0


FAKTOR = zaznaj_faktor()

_MERE_RE = re.compile(r'(position|size)="(-?\d+),(-?\d+)"')
_PISAVA_RE = re.compile(r'font="([^";]+);(\d+)"')


def p(vrednost):
    """Mera, pomnozena s faktorjem zaslona."""
    return int(round(vrednost * FAKTOR))


def _prilagodi(xml):
    if abs(FAKTOR - 1.0) < 0.01:
        return xml
    xml = _MERE_RE.sub(
        lambda m: '%s="%d,%d"' % (m.group(1), p(int(m.group(2))),
                                  p(int(m.group(3)))), xml)
    return _PISAVA_RE.sub(
        lambda m: 'font="%s;%d"' % (m.group(1), p(int(m.group(2)))), xml)


GLAVNI = _prilagodi(_GLAVNI)
INFO = _prilagodi(_INFO)

# Mere, ki jih plugin.py rabi pri risanju vrstic seznama.
VISINA_VRSTICE = p(_VISINA_VRSTICE)
S_OZNAKA = (p(_S_OZNAKA[0]), p(_S_OZNAKA[1]))
S_IME = (p(_S_IME[0]), p(_S_IME[1]))
S_PONUDNIK = (p(_S_PONUDNIK[0]), p(_S_PONUDNIK[1]))
S_LOCLJIVOST = (p(_S_LOCLJIVOST[0]), p(_S_LOCLJIVOST[1]))
S_KODIRAN = (p(_S_KODIRAN[0]), p(_S_KODIRAN[1]))
S_NOVO = (p(_S_NOVO[0]), p(_S_NOVO[1]))
PISAVA_VELIKA = p(_PISAVA_VELIKA)
PISAVA_MALA = p(_PISAVA_MALA)
