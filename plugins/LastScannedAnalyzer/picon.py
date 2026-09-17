# -*- coding: utf-8 -*-
"""Iskanje logotipa kanala (picon).

Enigma picone poimenuje po sklicu kanala, kjer dvopicja zamenjajo podcrtaji:

    1:0:19:2B5E:441:1:C00000:0:0:0:  ->  1_0_19_2B5E_441_1_C00000_0_0_0.png

Nekatere zbirke piconov so poimenovane po imenu kanala, zato poskusimo se to.
"""

import os
import re

POTI = (
    "/usr/share/enigma2/picon/",
    "/picon/",
    "/media/hdd/picon/",
    "/media/usb/picon/",
    "/media/sdcard/picon/",
    "/media/mmc/picon/",
    "/media/cf/picon/",
    "/media/net/picon/",
    "/usr/share/enigma2/piconlcd/",
)


def ime_iz_sklica(ref):
    polja = (ref or "").split(":")[:10]
    if len(polja) < 10:
        return ""
    return "_".join(polja) + ".png"


def ime_iz_imena(ime):
    ocisceno = (ime or "").lower().replace("&", "and").replace("+", "plus")
    ocisceno = re.sub(r"[^a-z0-9]", "", ocisceno)
    return (ocisceno + ".png") if ocisceno else ""


def najdi(ref, ime=""):
    """Vrni pot do picona ali prazen niz."""
    kandidati = [k for k in (ime_iz_sklica(ref), ime_iz_imena(ime)) if k]
    for mapa in POTI:
        if not os.path.isdir(mapa):
            continue
        for kandidat in kandidati:
            pot = os.path.join(mapa, kandidat)
            if os.path.exists(pot):
                return pot
    return ""
