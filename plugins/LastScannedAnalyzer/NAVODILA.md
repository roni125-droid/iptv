# Navodila po korakih

Za nekoga, ki plugina na Enigmo še ni nameščal. Če vam je kaj od tega že
domače, poglavje preprosto preskočite.

- [Kaj plugin sploh dela](#kaj-plugin-sploh-dela)
- [Kam se namesti](#kam-se-namesti)
- [1. korak: datoteke na računalnik](#1-korak-datoteke-na-računalnik)
- [2. korak: namestitev](#2-korak-namestitev)
  - [Pot A: paket .ipk](#pot-a-paket-ipk-priporočeno)
  - [Pot B: z USB ključkom](#pot-b-z-usb-ključkom-brez-računalniških-orodij)
  - [Pot C: prek omrežja (WinSCP)](#pot-c-prek-omrežja-winscp-windows)
  - [Pot D: prek omrežja (ukazna vrstica)](#pot-d-prek-omrežja-ukazna-vrstica)
  - [Čiščenje starih datotek](#čiščenje-starih-datotek)
- [3. korak: ponovni zagon vmesnika](#3-korak-ponovni-zagon-vmesnika)
- [4. korak: prva uporaba](#4-korak-prva-uporaba)
- [Kako plugin dela od znotraj](#kako-plugin-dela-od-znotraj)
- [Če gre kaj narobe](#če-gre-kaj-narobe)
- [Kako ga odstranim](#kako-ga-odstranim)

## Kaj plugin sploh dela

Ko sprejemnik poskenirate, se vsi najdeni kanali zapišejo v bazo, ki se
imenuje `lamedb`. V njej so **vsi** kanali, stari in novi, brez oznake,
kdaj so prišli. Kanal je gledljiv šele, ko je v kakem **buketu** (seznamu,
ki ga vidite, ko na daljincu pritisnete OK).

Prav to je nadloga po vsakem skeniranju: v bazi je na primer 1200 kanalov,
40 jih je novih, ročno pa jih iščete enega po enega.

Plugin naredi troje:

1. prebere bazo `lamedb`,
2. pogleda, kateri kanali **niso v nobenem buketu** — to so tisti, ki so
   po skeniranju ostali nerazvrščeni, in dobijo oznako `[NEW]`,
3. tiste, ki jih izberete, zapiše v buket, ki ga izberete ali ustvarite.

Baze `lamedb` pri tem nikoli ne spreminja. Piše samo v bukete, pred prvo
spremembo pa naredi varnostno kopijo.

## Kam se namesti

Na sprejemnik, v mapo:

```
/usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer
```

Ta mapa je na notranjem pomnilniku sprejemnika, ne na disku in ne na USB
ključku. Vse slike Enigme2 (OpenATV, OpenPLi, OpenBH, VTi, Egami …) imajo
prav to pot. Mapo `LastScannedAnalyzer` ustvarite vi, ostale so že tam.

V njej morajo biti te datoteke:

```
__init__.py   plugin.py    lamedb.py     bouquets.py   picon.py
skin.py       update.py    preizkus.py   plugin.png    version.json
```

## 1. korak: datoteke na računalnik

Če boste šli po **poti A** (paket `.ipk`), potrebujete eno samo datoteko in
lahko ta korak preskočite — prenos je opisan tam. Spodnje velja za poti B,
C in D, ki kopirajo posamezne datoteke.

1. Odprite `https://github.com/roni125-droid/iptv`.
2. Zeleni gumb **Code** → **Download ZIP**.
3. ZIP razpakirajte. Znotraj poiščite mapo
   `plugins/LastScannedAnalyzer` — ta mapa je tisto, kar potrebujete.

Če imate repozitorij kloniran, je mapa že pri vas in tega koraka ni.

Potrebovali boste tudi **naslov IP sprejemnika**. Na sprejemniku:
`Meni → Nastavitve → Sistem → Omrežje` (ali `Meni → Informacije → Omrežje`).
Zapišite si ga, videti je kot `192.168.1.25`.

## 2. korak: namestitev

Izberite eno od štirih poti.

| Pot | Kdaj |
| --- | --- |
| **A — paket `.ipk`** | privzeta izbira; sprejemnik si plugin zapomni in ga zna sam odstraniti |
| B — USB ključek | ročno kopiranje, brez računalniških orodij |
| C — WinSCP | ročno kopiranje z Windows |
| D — ukazna vrstica | najhitreje, če vam SSH ni tuj |

Poti B, C in D datoteke samo prekopirajo. Delujejo enako dobro, le da
sprejemnik o njih ne ve ničesar in jih morate pozneje odstraniti ročno.

Če ste plugin po eni od teh poti nameščali že prej, si oglejte še
[Čiščenje starih datotek](#čiščenje-starih-datotek) na koncu tega koraka.

### Pot A: paket .ipk (priporočeno)

`.ipk` je paket, ki ga razume `opkg`, isti nameščalnik, s katerim
sprejemnik nameša vse svoje vtičnike.

1. **Prenesite paket.** V repozitoriju odprite
   `plugins/LastScannedAnalyzer/enigma2-plugin-extensions-lastscannedanalyzer_1.1_all.ipk`
   in kliknite `Download raw file`.

2. **Spravite ga na sprejemnik**, na en od dveh načinov:

   - na USB ključek, ki ga priklopite na sprejemnik (pristane v
     `/media/usb`),
   - ali prek omrežja:
     `scp enigma2-plugin-extensions-lastscannedanalyzer_1.1_all.ipk root@192.168.1.25:/tmp/`

3. **Namestite ga.**

   Prek SSH:

   ```bash
   opkg install /tmp/enigma2-plugin-extensions-lastscannedanalyzer_1.1_all.ipk
   ```

   Brez računalnika, kar na sprejemniku: poiščite postavko za namestitev
   lokalnega paketa. V večini slik je pod
   `Meni → Nastavitve → Programska oprema`, imenuje pa se
   `Namesti lokalno razširitev` oziroma `Install local extension`. Pokaže
   datoteke `.ipk` z `/tmp` in s priklopljenih ključkov; izberite našo in
   potrdite.

4. Nameščalnik izpiše, da je plugin nameščen, in vas opozori na ponovni
   zagon vmesnika. Pojdite na [3. korak](#3-korak-ponovni-zagon-vmesnika).

Kaj ste s tem pridobili: paket je zaveden v seznamu nameščene programske
opreme (`opkg list-installed | grep lastscanned`), odstranite pa ga z enim
ukazom, brez brskanja po mapah:

```bash
opkg remove enigma2-plugin-extensions-lastscannedanalyzer
```

Če kodo spremenite, nov paket zgradite z

```bash
python3 plugins/LastScannedAnalyzer/naredi-ipk.py
```

Skripta potrebuje samo Python, nobenih orodij OpenEmbedded, in vzame
različico kar iz `plugin.py`, da se paket in plugin ne razideta.

### Pot B: z USB ključkom (brez računalniških orodij)

1. Mapo `LastScannedAnalyzer` prekopirajte na USB ključek (formatiran kot
   FAT32).
2. Ključek priklopite na sprejemnik.
3. Na sprejemniku odprite datotečni upravitelj. V OpenATV je to
   `Meni → Vtičniki → File Commander`, v drugih slikah se imenuje podobno
   (`File Manager`, `Filebrowser`). Če ga ni, ga namestite iz seznama
   vtičnikov; v večini slik ta seznam odpre zeleni gumb v `Meni → Vtičniki`.
4. V levem stolpcu poiščite ključek, običajno `/media/usb`, in na njem
   mapo `LastScannedAnalyzer`.
5. V desnem stolpcu se pomaknite v
   `/usr/lib/enigma2/python/Plugins/Extensions`.
6. Mapo označite (v File Commanderju z zelenim gumbom) in izberite
   **Copy** oziroma **Kopiraj**. Datotečni upravitelji se razlikujejo,
   povsod pa gre za isti dve dejanji: označi in kopiraj.
7. Pojdite na [3. korak](#3-korak-ponovni-zagon-vmesnika).

### Pot C: prek omrežja (WinSCP, Windows)

1. Namestite **WinSCP** z naslova `winscp.net`.
2. Zaženite ga in vpišite:

   | Polje | Vrednost |
   | --- | --- |
   | File protocol | `SCP` |
   | Host name | naslov IP sprejemnika, npr. `192.168.1.25` |
   | Port | `22` |
   | User name | `root` |
   | Password | geslo sprejemnika; pri večini slik je prazno |

   Če geslo ni prazno in ga ne veste, ga pri večini slik nastavite na
   sprejemniku pod `Meni → Nastavitve → Sistem → Omrežje`, kjer je postavka
   za geslo uporabnika root.
3. Ob prvi povezavi WinSCP vpraša za potrditev ključa strežnika. Potrdite.
4. V desnem oknu (sprejemnik) se pomaknite v
   `/usr/lib/enigma2/python/Plugins/Extensions`.
5. Iz levega okna (računalnik) povlecite mapo `LastScannedAnalyzer` v
   desno okno.
6. Pojdite na [3. korak](#3-korak-ponovni-zagon-vmesnika).

### Pot D: prek omrežja (ukazna vrstica)

Na Linuxu, macOS ali v Windows PowerShellu, v mapi, kjer je
`plugins/LastScannedAnalyzer`:

```bash
scp -r plugins/LastScannedAnalyzer root@192.168.1.25:/tmp/
ssh root@192.168.1.25 "sh /tmp/LastScannedAnalyzer/namesti.sh"
```

Naslov `192.168.1.25` zamenjajte s svojim. Skripta `namesti.sh` datoteke
prekopira na pravo mesto, pobriše morebitne stare prevedene datoteke in na
koncu izpiše, kako zagnati vmesnik na novo.

### Čiščenje starih datotek

To potrebujete samo, če ste plugin kdaj že kopirali ročno. Takih datotek
`opkg` ne vodi, zato po namestitvi paketa ostanejo ležati naokrog:
prevedene datoteke `.pyc`, mapa `__pycache__`, datoteke starejših različic,
ki jih nova nima več, po nesreči vgnezdene kopije in ostanki v `/tmp`.

Zanje je drugi paket:

```
enigma2-plugin-extensions-lastscannedanalyzer-cistilec_1.1_all.ipk
```

Namestite ga enako kot prvega:

```bash
scp enigma2-plugin-extensions-lastscannedanalyzer-cistilec_1.1_all.ipk root@192.168.1.25:/tmp/
ssh root@192.168.1.25 "opkg install /tmp/enigma2-plugin-extensions-lastscannedanalyzer-cistilec_1.1_all.ipk"
```

Delo opravi takoj ob namestitvi in sproti izpiše, kaj je odstranil:

```
LastScanned Analyzer - ciscenje starih datotek
Plugin je namescen prek opkg, zato se njegovih datotek ne dotikam.

  odstranjeno: .../LastScannedAnalyzer/__pycache__
  odstranjeno: .../LastScannedAnalyzer/plugin.pyc
  odstranjeno: .../LastScannedAnalyzer/stara-datoteka.py
  odstranjeno: /tmp/LastScannedAnalyzer

Pocistil sem 4 stvari.
```

**Kaj pobriše, je odvisno od tega, kako je plugin nameščen.** Paket to
preveri sam, v seznamu nameščene programske opreme:

| Stanje | Kaj naredi |
| --- | --- |
| Plugin je nameščen prek `opkg` | Pusti njegove datoteke pri miru. Odstrani samo prevedene datoteke, ostanke starejših različic in kopije na napačnih mestih. |
| Plugina `opkg` ne vodi (ročna kopija) | Odstrani celotno mapo plugina, ker je vsa skupaj ostanek ročne namestitve. |

Zato je vseeno, v katerem vrstnem redu ga poženete. Najbolj čisto je
takole: najprej čistilec (pobriše staro ročno kopijo), nato paket s
pluginom (namesti novo, o kateri sprejemnik ve).

Čistilec **ni** odstranjevalnik plugina. Pravilno nameščenega plugina se
namenoma ne dotakne; za odstranitev je `opkg remove`, kot piše v
[zadnjem poglavju](#kako-ga-odstranim).

Shranjenega stanja (`/etc/enigma2/lastscanned_analyzer.json`) ne briše, da
oznake `[NEW]` ostanejo take, kot so bile.

Ko konča, ga lahko odstranite, saj je svoje opravil:

```bash
opkg remove enigma2-plugin-extensions-lastscannedanalyzer-cistilec
```

## 3. korak: ponovni zagon vmesnika

Enigma prebere vtičnike samo ob zagonu, zato je po namestitvi potreben
ponovni zagon vmesnika. Sprejemnika ni treba izklapljati iz elektrike.

Na sprejemniku: `Meni → Ugasni / Ponovni zagon → Ponovni zagon vmesnika`
(v angleščini `Standby / Restart → Restart GUI`).

Prek SSH:

```bash
init 4 && sleep 3 && init 3
```

Slika za nekaj sekund ugasne in se vrne. To je normalno.

## 4. korak: prva uporaba

1. **Poskenirajte kanale**, če tega še niste. To naredite po običajni poti
   sprejemnika ali kar iz plugina: odprite ga in pritisnite **MENU** →
   `Scan Channels`.

2. **Odprite plugin**: `Meni → Vtičniki → LastScanned Analyzer`.
   V mnogih slikah je seznam vtičnikov tudi na modrem gumbu med gledanjem
   programa.

3. **Poglejte zgornjo vrstico.** Pove, koliko je vseh kanalov, koliko je
   novih in koliko ste jih označili:

   ```
   Total: 1243   NEW: 38   Free: 211   Marked: 0   Shown: 1243 (all)
   ```

   Novi kanali so zeleni, z oznako `[NEW]` na desni, in so **na vrhu
   seznama**. Kodirani imajo v stolpcu `CA` oranžno oznako.

4. **Pritisnite RUMENI gumb.** Stari kanali izginejo, ostanejo samo novi.
   Ponovni pritisk spet pokaže vse.

   **Pritisnite še tipko 1.** Izginejo kodirani kanali, ki jih brez kartice
   ne morete gledati. Po skeniranju satelita je teh navadno velika večina,
   zato se seznam tu najbolj skrajša. Ponovni pritisk jih spet pokaže.

   Če veste, kaj iščete, **tipka 2** odpre tipkovnico na zaslonu in seznam
   omeji na kanale s to besedo v imenu. Filtri se seštevajo, kaj je
   vklopljeno, pa piše na koncu zgornje vrstice, na primer
   `Shown: 6 (NEW + free + "hrt")`.

5. **Označite, kar hočete obdržati.** Z **ZELENIM** gumbom, oznaka je
   `[ * ]`. Kazalec se po označitvi sam premakne navzdol, zato gre hitro.
   Če hočete vse nove naenkrat: **MENU** → `Mark all NEW channels`.

   Če ne označite ničesar, modri gumb vzame vse kanale z oznako `[NEW]`
   **med tistimi, ki so trenutno na zaslonu**. Filter torej ni past: kdor
   gleda samo proste kanale, ne dobi v buket še kodiranih.

6. **Pritisnite MODRI gumb.** Odpre se seznam vaših buketov, na dnu pa
   `+ Create New Bouquet`.

   - Izberite obstoječi buket, in kanali gredo vanj.
   - Ali izberite `+ Create New Bouquet`, vpišite ime (na primer
     `Novo s 13E`) in potrdite. Buket nastane in kanali gredo vanj.

7. **Izpiše se potrdilo**, na primer `Copied 38 channel(s) to "Novo s 13E".`
   Kanali so uporabni **takoj**, sprejemnika ni treba znova zagnati.

8. **RDEČI gumb** zapre plugin. Pritisnite OK na daljincu in preverite:
   nov buket je v seznamu kanalov.

Če se pri kakem kanalu ne morete odločiti, pritisnite **INFO**. Pokaže
logotip in podatke, od kod kanal prihaja — satelit, frekvenco,
polarizacijo, hitrost simbolov, FEC, sistem in ločljivost.

### Vsi gumbi na enem mestu

| Gumb | Kaj naredi |
| --- | --- |
| RDEČI | izhod |
| ZELENI | označi / odznači kanal (`[ * ]`) |
| RUMENI | samo `[NEW]` ↔ vsi kanali |
| MODRI | prenos v buket |
| MENU | filtri, iskanje, skeniranje, posodobitve, označi vse / počisti |
| INFO | podatki o kanalu in transponderju |
| OK | enako kot zeleni gumb |
| **1** | samo prosti (FTA) kanali ↔ vsi kanali |
| **2** | iskanje po imenu kanala |
| gor / dol | premik po seznamu |
| levo / desno | stran gor / stran dol |

## Kako plugin dela od znotraj

Za tiste, ki jih zanima, kaj se dogaja pod pokrovom.

**Kje bere.** `/etc/enigma2/lamedb` (ali `lamedb5` v novejših slikah). To
je seznam vseh kanalov s podatki o transponderjih. Plugin ga samo bere.

**Kako ve, kaj je novo.** Kanal dobi oznako `[NEW]`, če velja karkoli od
tega:

1. ni v nobenem buketu — to je običajen primer po skeniranju,
2. ob zadnjem zagonu plugina ga v bazi še ni bilo — to ujame kanal, ki ga
   je Enigma sama dodala v buket, pa je vseeno nov,
3. Enigma sama ga je ob skeniranju označila z zastavico `dxNewFound`
   (`f:40` v bazi) — edini znak, ki deluje tudi ob prvem zagonu.

Tretjega pravila plugin ne uporablja slepo. Nekatere slike zastavice nikoli
ne počistijo in jo potem nosi domala vsa baza; če je označenih več kot 80
odstotkov kanalov, jo zanemari in ostane pri prvih dveh pravilih.

Brez tretjega pravila ob prvem zagonu velja samo prvo. Drugače bi bili novi
čisto vsi kanali v bazi, kar ne bi povedalo ničesar.

**Kako ve, kaj je kodirano.** Pri vsakem kanalu bere zapise `C:` s šiframi
CAID. Te se zapišejo ob skeniranju oziroma ob prvem odprtju kanala, zato
oznaka `CA` pomeni zagotovo kodiran, njena odsotnost pa najverjetneje
prost. Kakšen kodiran kanal se zna prikrasti med proste, nasprotno pa se ne
zgodi.

**Kje si zapomni stanje.** V `/etc/enigma2/lastscanned_analyzer.json`.
Zapiše se ob prvem zagonu in po vsakem prenosu v buket, **ne** ob vsakem
odprtju. Zato oznake `[NEW]` ne izginejo, če plugin vmes zaprete.
Če hočete začeti od začetka: **MENU** →
`Forget saved state (rebuild [NEW])`.

Iz istega razloga se splača plugin enkrat odpreti **pred** skeniranjem.
Takrat si zapiše, kaj je v bazi, in po skeniranju pozna razliko tudi pri
kanalih, ki jih je Enigma sama razvrstila v bukete.

**Kam piše.** Samo v `/etc/enigma2/userbouquet.*.tv` (oziroma `.radio`) in
v kazalo `bouquets.tv`. Pred prvo spremembo naredi kopijo z isto pot in
končnico `.lsa-bak`. Piše prek začasne datoteke, zato buket tudi ob izpadu
elektrike ne ostane napol zapisan.

**Zakaj ni treba ponovnega zagona.** Po pisanju pokliče `reloadBouquets`,
kar je isto, kar naredi Enigma sama, ko bukete urejate v njenem meniju.

## Če gre kaj narobe

| Težava | Vzrok in rešitev |
| --- | --- |
| Plugina ni v meniju | Datoteke niso v pravi mapi. Preverite, da pot **ni** `.../Extensions/plugins/LastScannedAnalyzer` ali `.../Extensions/LastScannedAnalyzer/LastScannedAnalyzer`. V mapi mora biti `plugin.py`. |
| Plugina ni niti po pravilnem kopiranju | Niste ponovno zagnali vmesnika. Glejte [3. korak](#3-korak-ponovni-zagon-vmesnika). |
| Po posodobitvi se vede po starem | Ostale so prevedene datoteke. Prek SSH: `rm -f /usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer/*.pyc` in ponovni zagon vmesnika. |
| `Could not read the channel database` | Baza ni na običajnem mestu ali je prazna. Preverite, da datoteka `/etc/enigma2/lamedb` obstaja in da ste že kdaj skenirali. |
| Vsi kanali so `[NEW]` | To je normalno ob prvem zagonu, če noben kanal ni v buketu. Prenesite jih v buket in oznake izginejo. |
| Noben kanal ni `[NEW]`, čeprav ste pravkar skenirali | Enigma je nove kanale sama razvrstila v bukete, plugin pa še ni imel posnetka baze od prej, s katerim bi jih primerjal. Navada, ki to prepreči: plugin enkrat odprite **pred** skeniranjem. Takrat si zapiše stanje baze in po skeniranju zna pokazati razliko. |
| Med prostimi je kakšen kodiran | Šifre kodiranja se zapišejo šele ob skeniranju ali prvem odprtju kanala. Odprite ga enkrat in po naslednjem zagonu plugina bo označen z `CA`. |
| Tipki 1 in 2 ne naredita nič | Nekateri daljinci številk ne pošiljajo v vse zaslone. Isto dobite prek `MENU`, kjer sta postavki `Show only free (FTA) channels` in `Search by name`. |
| Gumb INFO ne naredi nič | Nekatere slike tipko INFO vežejo drugače. Vse drugo deluje; za označevanje uporabite OK ali zeleni gumb. |
| Buket je pokvarjen | Prek SSH vrnite kopijo: `cp /etc/enigma2/userbouquet.moj.tv.lsa-bak /etc/enigma2/userbouquet.moj.tv`, nato ponovni zagon vmesnika. |
| `Check for Updates` javi, da vir ni nastavljen | Tako je prav. V `update.py` spremenljivka `VIR` je prazna, dokler vanjo ne vpišete naslova do `version.json`. |

Če se plugin sesuje, je razlog zapisan v dnevniku sprejemnika, običajno v
`/home/root/logs` ali prek `journalctl -n 200`. Tisti izpis je tisto, kar
je vredno pokazati naprej.

## Kako ga odstranim

Če ste ga namestili **s paketom `.ipk` (pot A)**:

```bash
opkg remove enigma2-plugin-extensions-lastscannedanalyzer
init 4 && sleep 3 && init 3
```

Če ste datoteke **prekopirali ročno (poti B, C, D)**:

```bash
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer
init 4 && sleep 3 && init 3
```

Shranjeno stanje v obeh primerih ostane; če ga ne potrebujete več:

```bash
rm -f /etc/enigma2/lastscanned_analyzer.json
```

Buketi, ki ste jih z njim naredili, ostanejo. Plugin jih ne odnese s
seboj, saj so navadne datoteke Enigme.
