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

**IPTV Extreme:**

1. V stranskem meniju izberite dodajanje seznama in vpišite naslov ali
   izberite lokalno datoteko `ex-yu.m3u`.
2. Če kateri kanal vrne napako 403, v nastavitvah poiščite `User Agent` in
   vpišite brskalniškega. Strežnik takrat misli, da gleda navaden računalnik.
3. Če se kanal ne odpre, v nastavitvah predvajalnika zamenjajte dekoder.
   IPTV Extreme jih ima več in vsak prenese nekoliko drugačne pretoke.

**TiViMate:** `Settings → Playlists → Add playlist`, nato naslov ali datoteka.

**VLC za Android:** `Nova mreža → Vnesite naslov`.

### Skupine in oznake

Seznam je razdeljen na dve vrsti skupin. Najprej so skupine z imenom države,
v katerih so programi, ki oddajajo ves dan. Za njimi so skupine z dodatkom
`- obcasni`, kjer so postaje, ki oddajajo le del dneva ali so geografsko
zaklenjene.

| Skupina | Stalnih | Občasnih |
| --- | --- | --- |
| Slovenija | 3 | 1 |
| Hrvaška | 8 | 6 |
| Bosna in Hercegovina | 5 | 5 |
| Srbija | 9 | 10 |

V oglatem oklepaju za imenom kanala so tri vrste podatkov:

| Oznaka | Pomen |
| --- | --- |
| `[720p]` | ločljivost izvora, kot jo oddaja postaja |
| `[ni 24/7]` | postaja ne oddaja ves dan |
| `[geo]` | pretok je omejen na domačo državo |
| `[potrdilo]` | postaji je poteklo TLS potrdilo, TiViMate jo zavrne, VLC vpraša |

Ločljivost je vredno pogledati, preden se čudite mehki sliki. Marsikatera
lokalna postaja oddaja v 288p ali 480p in to je pri njej normalno, ne okvara.
Najnižje v seznamu so TV Pirot pri 240p ter Kanal 6 in TNT Kids pri 288p.

## Popravljanje seznama

`tools/popravi.py` v enem prehodu popravi, kar se popraviti da:

- kanale, ki jih strežnik dokončno zavrača z 404 ali 403, odstrani,
- kadar se potrdilo glasi na drugo ime, prebere pravo ime iz potrdila in
  naslov popravi nanj, nato pa povezavo preveri v celoti,
- kadar je potrdilo poteklo, poskusi isto sliko prek HTTP, tudi na običajnih
  vratih Wowza 1935 in 8086,
- kanale z več različicami pripne na najboljšo sliko.

```bash
python3 tools/popravi.py ex-yu.m3u --out ex-yu-ok.m3u
```

Na Windows isto naredi dvoklik na `tools/popravi.bat`. Kanal, ki se ta trenutek
ne odziva, ostane v seznamu z izvirnim naslovom, ker je postaja lahko preprosto
zunaj programa.

Pri občasnih postajah je napaka ob odprtju pričakovana in ne pomeni mrtve
povezave. Lokalne televizije pogosto oddajajo šele popoldne in zvečer, zato
isti kanal poskusite ob drugi uri dneva, preden ga odpišete.

### Megleno ob preklopu kanala

Ob preklopu je slika nekaj sekund megleno, nato se sama zbistri. To ni okvara
in ni odvisno od predvajalnika.

Naslov v seznamu kaže na glavni manifest HLS, v katerem je več različic iste
slike. Predvajalnik namenoma začne pri najslabši, da slika stece takoj, nato
izmeri hitrost povezave in šele čez kakih deset sekund preklopi na najboljšo.
To čakanje vidite kot meglo.

Odpravite ga tako, da kanale vnaprej pripnete na najboljšo različico.

Na Windows brez ukazne vrstice: datoteke `exyu.m3u`, `tools/kakovost.py` in
`tools/naredi-hd.bat` dajte v isto mapo in dvokliknite `naredi-hd.bat`. Sam
poišče Python in naredi `exyu-hd.m3u`. Enako dela `preveri.bat`, ki požene
preverjanje kanalov.

Ročno:

```bash
python3 tools/kakovost.py exyu.m3u --out exyu-hd.m3u
```

Pozor, te ukaze vpišete v ukazni poziv, ne v okno Pythona. Če vidite `>>>`,
ste v Pythonu in ukazi tam ne delujejo.

Skripta odpre vsak glavni manifest, poišče različico z najvišjo ločljivostjo
in naslov zamenja z njo. Predvajalnik potem nima česa izbirati in začne takoj
pri najboljši sliki. Zaženite jo doma, ker mora do strežnikov postaj.

Cena tega je, da prilagajanje odpade. Na šibki povezavi predvajalnik ne bo več
sam znižal kakovosti, ampak bo slika zastajala. V tem primeru se vrnite na
izvirni seznam, ki ostane nedotaknjen.

### Če seznam preizkušate na računalniku

Protivirusni programi radi blokirajo strežnike, na katerih tečejo majhne
postaje, ker jih ne poznajo. ESET v takem primeru javi `Naslov je blokiran` in
pokaže naslov IP, predvajalnik pa samo reče, da vira ne more odpreti. To je
blokada na vašem računalniku in ne stanje pretoka. Na boksu iste blokade ni.

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

## Filmi in serije

V seznamu je en pravi filmski program, hrvaški **Klasik**, ki vrti starejše
filme. Brezplačnih živih kanalov s filmi in domačimi nadaljevankami v regiji
tako rekoč ni, ker so te pravice plačljive in jih imajo CineStar, Pickbox,
Pink Film in podobni.

Zakonita in brezplačna pot do domačih filmov in nadaljevank so lastne
platforme javnih televizij. Te niso seznami M3U, ampak aplikacije oziroma
spletne strani, ki jih na boks namestite posebej:

| Platforma | Država | Kaj ponuja |
| --- | --- | --- |
| RTS Planeta | Srbija | velik arhiv domačih serij in filmov, brezplačna registracija |
| HRTi | Hrvaška | hrvaške serije in filmi, del vsebine le znotraj Hrvaške |
| RTV SLO 365 | Slovenija | slovenske nadaljevanke in filmi |
| BHRT in FTV | BiH | oddaje in del arhiva prek spletnega predvajalnika |

Javne televizije imajo tudi uradne kanale na YouTubu, kjer so cele
nadaljevanke in filmi objavljeni zakonito.

## Kaj je vključeno in kaj ne

Vključeni so samo programi, ki jih izdajatelj (ali njegov uradni CDN) oddaja
javno in brez naročnine. Samodejno so izločeni:

- goli naslovi IP, na katerih visi več tujih programov hkrati, kar je znak
  preprodajalskega panela, medtem ko lasten strežnik male postaje ostane,
- zapisi, ki zahtevajo ponarejen `User-Agent`,
- znani preprodajalski panelji in prepakiran operaterski multicast (`/play/`, `/udp/`),
- puščeni dostopni ključi in testni računi operaterjev,
- plačljivi in tuji programi, na primer HBO, Arena Sport, Nat Geo in Viasat,
- strežniki, ki namesto pretoka vrnejo vrinjeno oglasno skripto.

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
python3 tools/kakovost.py ex-yu.m3u --out ex-yu-hd.m3u  # pripni na najboljso sliko
```

`tools/build.py` vsakič znova prebere javno bazo
[iptv-org](https://github.com/iptv-org/iptv), tako da samodejno pobere tudi
nove in spremenjene naslove. `tools/check.py` vsako povezavo dejansko odpre in
zahteva veljaven HLS/DASH odgovor.

Delovni proces `.github/workflows/osvezi-playlisto.yml` oboje zažene vsak
ponedeljek in spremembe sam objavi. Veja `claude/playlist-ex-yu-iptv-m2u6ya` je
že nastavljena kot privzeta, zato časovnik teče brez dodatnega posega. Predčasno
ga zaženete z gumbom *Run workflow* v zavihku *Actions*.

## Plugin za Enigma2

V mapi [`plugins/LastScannedAnalyzer`](plugins/LastScannedAnalyzer) je
ločeno orodje, ki s to playlisto nima opravka: plugin za satelitske
sprejemnike Enigma2. Po skeniranju pokaže, kateri kanali so novi, in jih z
modrim gumbom prenese v buket, tudi v na novo ustvarjenega.

Navodila po korakih, od prenosa datotek do prve uporabe, so v
[NAVODILA.md](plugins/LastScannedAnalyzer/NAVODILA.md), tehnični opis pa v
[README](plugins/LastScannedAnalyzer/README.md) plugina.

## Viri podatkov

Naslovi pretokov in logotipi izvirajo iz javnih zbirk
[iptv-org/iptv](https://github.com/iptv-org/iptv) in
[iptv-org/database](https://github.com/iptv-org/database), objavljenih pod
licenco MIT oziroma javno domeno.
