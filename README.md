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

Ta naslov deluje samo, dokler je repozitorij javen. Ko ga zaprete po korakih
v razdelku [Zaščita repozitorija](#zaščita-repozitorija), sezname na bokse
prenesete lokalno.

V VLC: `Medij → Odpri omrežni tok` in prilepite zgornji naslov. Lokalno
datoteko odprete z `Medij → Odpri datoteko`.

## Namestitev na Android TV box

Na vsakem od boxov ponovite iste korake. Isti naslov lahko uporabljajo vse tri
naprave hkrati, saj gre za navadne javne pretoke brez naročnine in brez
omejitve števila naprav.

**TiViMate** (priporočeno, ker si zapomni vrstni red kanalov):
1. `Settings → Playlists → Add playlist → Enter URL`.
2. Prilepite zgornji naslov in potrdite.
3. Če kateri kanal ne steče, v `Settings → Playlists → <ime> → User agent`
   nastavite brskalniški User-Agent.

**IPTV Smarters ali OTT Navigator**: izberite vpis prek naslova M3U
(`Load Your Playlist → M3U URL`), EPG pustite prazen.

**VLC za Android**: `Nova mreža → Vnesite naslov`.

### Kaj na Android TV najpogosteje ponagaja

| Težava | Kaj se zgodi | Rešitev |
| --- | --- | --- |
| Nešifriran HTTP | Android 9 in novejši ga privzeto blokira | v predvajalniku vklopite dovoljenje za `cleartext`, sicer ta kanal preskočite |
| Neveljavno TLS potrdilo | ExoPlayer povezavo zavrne brez sporočila | kanal odprite v VLC, ki je manj strog |
| Privzeti User-Agent | strežnik vrne napako 403 | nastavite brskalniški User-Agent |
| H.265/HEVC | zvok teče, slike ni | na starejšem boxu izberite drug kanal |

Katera od teh težav velja za vaše omrežje, pove diagnostika:

```bash
python3 tools/check.py ex-yu.m3u --android --devices 3
```

Skripto poženite na računalniku v istem domačem omrežju kot boxi. Zastavica
`--devices 3` odpre tri hkratne povezave do vsakega pretoka in tako preveri
prav vaš primer s tremi napravami naenkrat.

## Zaščita repozitorija

Repozitorij je ob nastanku **javen**, kar pomeni, da je seznam viden vsakomur.
Spodnji koraki ga zaprejo. Nastavitev vidnosti lahko spremeni samo lastnik
računa, zato jih morate opraviti ročno.

### 1. Repozitorij nastavite na zasebnega

1. Odprite `https://github.com/roni125-droid/iptv/settings`.
2. Čisto na dnu, v razdelku **Danger Zone**, kliknite `Change visibility`.
3. Izberite `Make private`, vpišite ime repozitorija in potrdite.

Takoj zatem javni naslov `raw.githubusercontent.com` neha delovati za vse, tudi
za vaše bokse. Kako jih ohranite pri življenju, piše v točki 3.

### 2. Pospravite še nepotrebne funkcije

V razdelku **Features**, ki je na isti strani nekoliko višje, tik nad
razdelkom Pull Requests, izklopite `Issues`, `Wikis` in `Projects`. Ta
repozitorij jih ne potrebuje.

Možnosti `Allow forking` na zasebnem repozitoriju ni. GitHub jo skrije, ker
zasebnega repozitorija v osebnem računu nihče od zunaj ne more forkati. Če je
ne najdete, je to znak, da je repozitorij res zaprt.

Samodejno tedensko osveževanje po tem še vedno deluje, saj GitHub Actions teče
tudi na zasebnih repozitorijih.

### 3. Sezname prenesite na bokse lokalno

Javnega naslova ni več, zato gre seznam na bokse prek USB ključka.

**Prek brskalnika, brez orodij:**

1. Odprite `https://github.com/roni125-droid/iptv` in kliknite `ex-yu.m3u`.
2. Desno zgoraj kliknite `Download raw file` in datoteko shranite na USB ključek.
3. Ključek priklopite na box.

**Če imate repozitorij kloniran in nameščen Python:**

```bash
python3 tools/build.py --out .        # osveži seznam
./tools/za-bokse.sh /media/usb        # pripravi datoteke za prenos
```

Na boksu nato v predvajalniku izberite lokalno datoteko namesto naslova URL.
V TiViMate je to `Settings → Playlists → Add playlist → Open file`. Ob vsaki
osvežitvi postopek ponovite, v praksi zadošča enkrat na mesec ali dva.

### Česa noben od teh korakov ne naredi

Datoteke, ki jo predvajalnik lahko odpre, ni mogoče zakleniti. Kdor ima naslov
ali kopijo, ima seznam, in nobena nastavitev v GitHubu tega ne spremeni.
Zasebnost torej pomeni nadzor nad tem, komu naslov pride v roke, ne pa tehnične
ključavnice.

Vredno je vedeti tudi, da v seznamu ni ničesar izključnega. Naslovi pretokov so
že javno objavljeni v bazi iptv-org, programi pa se oddajajo brezplačno. Ni
naročnine, gesla in ne omejitve naprav, zato z morebitnim deljenjem ne izgubite
dostopa in se vam nič ne porabi. Vaše je le izbiranje in orodje okrog njega,
kar je zapisano v [NOTICE.md](NOTICE.md).

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
python3 tools/build.py --out .                        # znova zgradi seznam
python3 tools/check.py ex-yu.m3u                      # samo poročilo
python3 tools/check.py ex-yu.m3u --android --devices 3  # diagnostika za bokse
python3 tools/check.py ex-yu.m3u --prune              # odstrani mrtve povezave
```

`tools/build.py` vsakič znova prebere javno bazo
[iptv-org](https://github.com/iptv-org/iptv), tako da samodejno pobere tudi
nove in spremenjene naslove. `tools/check.py` vsako povezavo dejansko odpre in
zahteva veljaven HLS/DASH odgovor.

Delovni proces `.github/workflows/osvezi-playlisto.yml` oboje zažene vsak
ponedeljek in spremembe sam objavi. Veja `claude/playlist-ex-yu-iptv-m2u6ya` je
že nastavljena kot privzeta, zato časovnik teče brez dodatnega posega. Predčasno
ga zaženete z gumbom *Run workflow* v zavihku *Actions*.

## Viri podatkov

Naslovi pretokov in logotipi izvirajo iz javnih zbirk
[iptv-org/iptv](https://github.com/iptv-org/iptv) in
[iptv-org/database](https://github.com/iptv-org/database), objavljenih pod
licenco MIT oziroma javno domeno.
