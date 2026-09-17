# Navodila po korakih

Za nekoga, ki plugina na Enigmo še ni nameščal. Če vam je kaj od tega že
domače, poglavje preprosto preskočite.

- [Kaj plugin sploh dela](#kaj-plugin-sploh-dela)
- [Kam se namesti](#kam-se-namesti)
- [1. korak: datoteke na računalnik](#1-korak-datoteke-na-računalnik)
- [2. korak: namestitev](#2-korak-namestitev)
  - [Pot A: z USB ključkom](#pot-a-z-usb-ključkom-brez-računalniških-orodij)
  - [Pot B: prek omrežja (WinSCP)](#pot-b-prek-omrežja-winscp-windows)
  - [Pot C: prek omrežja (ukazna vrstica)](#pot-c-prek-omrežja-ukazna-vrstica)
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

1. Odprite `https://github.com/roni125-droid/iptv`.
2. Zeleni gumb **Code** → **Download ZIP**.
3. ZIP razpakirajte. Znotraj poiščite mapo
   `plugins/LastScannedAnalyzer` — ta mapa je tisto, kar potrebujete.

Če imate repozitorij kloniran, je mapa že pri vas in tega koraka ni.

Potrebovali boste tudi **naslov IP sprejemnika**. Na sprejemniku:
`Meni → Nastavitve → Sistem → Omrežje` (ali `Meni → Informacije → Omrežje`).
Zapišite si ga, videti je kot `192.168.1.25`.

## 2. korak: namestitev

Izberite eno od treh poti. Pot A ne potrebuje nobenega programa, pot B je
najpreprostejša na Windows, pot C je najhitrejša, če vam ukazna vrstica ni
tuja.

### Pot A: z USB ključkom (brez računalniških orodij)

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

### Pot B: prek omrežja (WinSCP, Windows)

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

### Pot C: prek omrežja (ukazna vrstica)

Na Linuxu, macOS ali v Windows PowerShellu, v mapi, kjer je
`plugins/LastScannedAnalyzer`:

```bash
scp -r plugins/LastScannedAnalyzer root@192.168.1.25:/tmp/
ssh root@192.168.1.25 "sh /tmp/LastScannedAnalyzer/namesti.sh"
```

Naslov `192.168.1.25` zamenjajte s svojim. Skripta `namesti.sh` datoteke
prekopira na pravo mesto, pobriše morebitne stare prevedene datoteke in na
koncu izpiše, kako zagnati vmesnik na novo.

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
   Total: 1243    NEW: 38    Marked: 0    Filter: all
   ```

   Novi kanali so zeleni, z oznako `[NEW]` na desni, in so **na vrhu
   seznama**.

4. **Pritisnite RUMENI gumb.** Stari kanali izginejo, ostanejo samo novi.
   Ponovni pritisk spet pokaže vse.

5. **Označite, kar hočete obdržati.** Z **ZELENIM** gumbom, oznaka je
   `[ * ]`. Kazalec se po označitvi sam premakne navzdol, zato gre hitro.
   Če hočete vse nove naenkrat: **MENU** → `Mark all NEW channels`.

   Če ne označite ničesar, modri gumb vzame **vse** kanale z oznako
   `[NEW]`.

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
| MENU | skeniranje, posodobitve, označi vse / počisti oznake |
| INFO | podatki o kanalu in transponderju |
| OK | enako kot zeleni gumb |
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
   je Enigma sama dodala v buket, pa je vseeno nov.

Ob prvem zagonu velja samo prvo pravilo. Drugače bi bili novi čisto vsi
kanali v bazi, kar ne bi povedalo ničesar.

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
| Gumb INFO ne naredi nič | Nekatere slike tipko INFO vežejo drugače. Vse drugo deluje; za označevanje uporabite OK ali zeleni gumb. |
| Buket je pokvarjen | Prek SSH vrnite kopijo: `cp /etc/enigma2/userbouquet.moj.tv.lsa-bak /etc/enigma2/userbouquet.moj.tv`, nato ponovni zagon vmesnika. |
| `Check for Updates` javi, da vir ni nastavljen | Tako je prav. V `update.py` spremenljivka `VIR` je prazna, dokler vanjo ne vpišete naslova do `version.json`. |

Če se plugin sesuje, je razlog zapisan v dnevniku sprejemnika, običajno v
`/home/root/logs` ali prek `journalctl -n 200`. Tisti izpis je tisto, kar
je vredno pokazati naprej.

## Kako ga odstranim

Prek SSH:

```bash
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer
rm -f /etc/enigma2/lastscanned_analyzer.json
init 4 && sleep 3 && init 3
```

Buketi, ki ste jih z njim naredili, ostanejo. Plugin jih ne odnese s
seboj, saj so navadne datoteke Enigme.
