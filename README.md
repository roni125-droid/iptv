# EX YU IPTV — Slovenija, Hrvaška, BiH, Srbija

Seznam **brezplačnih, javno oddajanih** televizijskih programov iz Slovenije,
Hrvaške, Bosne in Hercegovine ter Srbije v formatu M3U.

| Datoteka | Vsebina |
| --- | --- |
| `ex-yu.m3u` | vse štiri države skupaj, razvrščeno po skupinah |
| `si.m3u` | Slovenija |
| `hr.m3u` | Hrvaška |
| `ba.m3u` | Bosna in Hercegovina |
| `rs.m3u` | Srbija |

## Uporaba

V predvajalnik (VLC, Kodi, IPTV Smarters, Tivimate, TV aplikacije) prilepite
neposredno povezavo do surove datoteke:

```
https://raw.githubusercontent.com/roni125-droid/iptv/claude/playlist-ex-yu-iptv-m2u6ya/ex-yu.m3u
```

Ko vejo združite v `main`, je naslov krajši:
`https://raw.githubusercontent.com/roni125-droid/iptv/main/ex-yu.m3u`

V VLC: `Medij → Odpri omrežni tok` in prilepite zgornji naslov. Lokalno
datoteko odprete z `Medij → Odpri datoteko`.

## Kaj je vključeno in kaj ne

Vključeni so samo programi, ki jih izdajatelj (ali njegov uradni CDN) oddaja
javno in brez naročnine. Samodejno so izločeni:

- naslovi na golih IP naslovih brez domene,
- zapisi, ki zahtevajo ponarejen `User-Agent`,
- znani preprodajalski panelji in prepakiran operaterski multicast (`/play/`, `/udp/`),
- puščeni dostopni ključi in testni računi operaterjev,
- plačljivi in tuji programi (HBO, Arena Sport, Nat Geo, Viasat in podobno).

Zato v seznamu **ni** programov kot RTV SLO, HRT, RTS ali Nova TV. Njihovi
prosto dostopni pretoki so geografsko zaklenjeni oziroma na voljo le prek
uradnih aplikacij, vse drugo, kar kroži po spletu, pa so nepooblaščeni
re-streami, ki jih tu namenoma ne objavljam.

## Vzdrževanje

IPTV povezave same po sebi niso trajne. Da seznam ostane uporaben tudi čez
več mesecev, ga vzdržujeta dve skripti in en GitHub Actions posel:

```bash
python3 tools/build.py --out .                       # znova zgradi seznam
python3 tools/check.py ex-yu.m3u si.m3u hr.m3u ba.m3u rs.m3u   # samo poročilo
python3 tools/check.py ex-yu.m3u --prune             # odstrani mrtve povezave
```

`tools/build.py` vsakič znova prebere javno bazo
[iptv-org](https://github.com/iptv-org/iptv), tako da samodejno pobere tudi
nove in spremenjene naslove. `tools/check.py` vsako povezavo dejansko odpre in
zahteva veljaven HLS/DASH odgovor.

Delovni proces `.github/workflows/osvezi-playlisto.yml` oboje zažene vsak
ponedeljek in spremembe sam objavi. Časovnik v GitHubu teče samo na privzeti
veji, zato vejo s tem seznamom nastavite za privzeto ali posel poženite ročno
prek gumba *Run workflow*.

## Viri podatkov

Naslovi pretokov in logotipi izvirajo iz javnih zbirk
[iptv-org/iptv](https://github.com/iptv-org/iptv) in
[iptv-org/database](https://github.com/iptv-org/database), objavljenih pod
licenco MIT oziroma javno domeno.
