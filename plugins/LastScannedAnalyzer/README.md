# LastScanned Analyzer

Plugin za Enigma2, ki po skeniranju pokaže, **kateri kanali so novi**, in jih
z enim pritiskom prenese v buket. Temen vmesnik HD (1280x720), berljiv s
kavča.

Po skeniranju risiver najde na stotine kanalov, v seznamu kanalov pa jih ni
mogoče ločiti od starih. Ta plugin prebere bazo kanalov (`lamedb`), jo
primerja z buketi in s stanjem od zadnjič ter novince označi z `[NEW]`.

> Če plugina na Enigmo še niste nameščali, so navodila po korakih, od
> prenosa datotek do prve uporabe, v [NAVODILA.md](NAVODILA.md).

## Namestitev

S paketom, ki ga razume `opkg`:

```bash
scp enigma2-plugin-extensions-lastscannedanalyzer_1.0_all.ipk root@<naslov>:/tmp/
ssh root@<naslov> "opkg install /tmp/enigma2-plugin-extensions-lastscannedanalyzer_1.0_all.ipk"
```

Tako je plugin zaveden med nameščeno programsko opremo in ga odstranite z
`opkg remove enigma2-plugin-extensions-lastscannedanalyzer`. Paket po
spremembi kode zgradite znova z `python3 naredi-ipk.py` (potrebuje samo
Python, `--preveri` ga po gradnji še razpakira in izpiše vsebino).

Če ste plugin kdaj kopirali ročno, ostanke počisti drugi paket,
`...-cistilec_1.0_all.ipk`. Ob namestitvi pogleda, ali je plugin zaveden v
`opkg`: če je, pobriše samo prevedene datoteke, ostanke starejših različic
in kopije na napačnih mestih, sicer pa celotno mapo, ker je vsa skupaj
ostanek ročne namestitve. Pravilno nameščenega plugina torej ne odnese s
seboj. Podrobneje v
[NAVODILA.md](NAVODILA.md#čiščenje-starih-datotek).

Brez paketa, s kopiranjem datotek:

```bash
scp -r plugins/LastScannedAnalyzer root@<naslov-risiverja>:/tmp/
ssh root@<naslov-risiverja> "sh /tmp/LastScannedAnalyzer/namesti.sh"
```

Brez SSH: mapo `LastScannedAnalyzer` prekopirajte na USB ključek, ga
priklopite na risiver in prek datotečnega upravitelja vsebino prenesite v
`/usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer`.

Po namestitvi je potreben ponovni zagon vmesnika (`GUI restart`). Plugin je
nato v `Meni → Vtičniki` in v meniju razširitev.

## Gumbi

| Gumb | Kaj naredi |
| --- | --- |
| **RDEČI** | izhod |
| **ZELENI** | označi ali odznači kanal, oznaka je `[ * ]` |
| **RUMENI** | prikaže samo `[NEW]` kanale, ponovni pritisk spet vse |
| **MODRI** | prenese označene (ali vse nove) v buket |
| **MENU** | `Scan Channels`, `Check for Updates` in tri bližnjice |
| **INFO** | picon in podatki o transponderju |
| **OK** | enako kot zeleni gumb |

Zeleni gumb po označitvi sam skoči na naslednjo vrstico, zato gre označevanje
hitro. V meniju sta tudi `Mark all NEW channels` in `Clear all marks`.

## Kaj pomeni `[NEW]`

Kanal je nov, če velja **karkoli** od tega:

1. po skeniranju **ni pristal v nobenem buketu** — to je običajen primer,
2. ob zadnjem zagonu plugina **ga v bazi še ni bilo** — to ujame kanal, ki ga
   je Enigma sama dodala v buket, pa je vseeno nov.

Ob prvem zagonu velja samo prvo pravilo. Drugače bi bili novi čisto vsi
kanali v bazi, kar ne bi povedalo ničesar.

Stanje se shrani v `/etc/enigma2/lastscanned_analyzer.json`. Zapiše se ob
prvem zagonu in po vsakem prenosu v buket, ne pa ob vsakem odprtju — tako
oznake `[NEW]` ne izginejo, če plugin med delom zaprete in znova odprete.
Če želite začeti od začetka, v meniju izberite
`Forget saved state (rebuild [NEW])`.

## Prenos v buket

Modri gumb prenese označene kanale, in če ni označen nobeden, vse z oznako
`[NEW]`. Nato izberete obstoječi buket ali `+ Create New Bouquet`, kjer ime
vpišete kar na zaslonu.

- Kanal, ki je v buketu že notri, se ne podvoji.
- Pred prvo spremembo nastane varnostna kopija `<datoteka>.lsa-bak`.
- Nov buket dobi ime datoteke iz vpisanega imena
  (`Moji programi` → `userbouquet.mojiprogrami.tv`). Če takšna datoteka že
  obstaja, se doda številka, obstoječi buket se ne prepiše.
- Če so vsi izbrani kanali radijski, nastane buket `.radio`, sicer `.tv`.
- Zapisuje se prek začasne datoteke, zato buket tudi ob izpadu električnega
  toka ne ostane napol zapisan.

Po prenosu plugin sam pokliče `reloadBouquets`, zato risiverja **ni treba**
znova zagnati. Spremembe so vidne takoj.

Baze kanalov `lamedb` plugin nikoli ne spreminja — samo bere jo.

## Okno INFO

Pokaže picon in podatke, po katerih se vidi, od kod kanal prihaja:

| Podatek | Primer |
| --- | --- |
| Satellite | `Hotbird 13.0E (13.0 E)` |
| Frequency | `11914 MHz` |
| Polarization | `H` |
| Symbol rate | `27500` |
| FEC | `2/3` |
| System | `DVB-S2 / 8PSK` |
| Resolution | `H.264 HD` |
| Service ref | `1:0:19:85:441:1:820000:0:0:0:` |

Ime satelita pove Enigma sama (`nimmanager`), zato je takšno, kot ga imate
nastavljeno. Če ga ni, so izpisane stopinje. Pri kabelskih in antenskih
kanalih so prikazani ustrezni parametri.

Picon se išče po standardnih mapah (`/usr/share/enigma2/picon`, `/picon`,
`/media/*/picon`), najprej po imenu sklica, nato po imenu kanala. Če picona
ni, ostane prostor prazen in vse drugo deluje naprej.

## Posodobitve

`MENU → Check for Updates` prenese datoteko `version.json` z naslova, ki ga
vpišete v `update.py` (spremenljivka `VIR`), in primerja različico s to, ki
teče. Datoteka izgleda takole:

```json
{
  "version": "1.1",
  "url": "https://primer.si/lastscanned-1.1.tar.gz",
  "changes": "Kaj je novega"
}
```

Arhiv `tar.gz` mora vsebovati mapo `LastScannedAnalyzer` z datotekami
plugina. Nič se ne namesti samo od sebe — plugin prej vpraša, ali naj
posodobitev namesti.

`VIR` je ob dostavi prazen, ker repozitorij ni nujno javno dosegljiv. Dokler
je prazen, gumb to samo pove in ne javlja napake. Ko boste imeli naslov,
vpišite ga v `update.py`.

## Preizkus brez risiverja

Kodo je mogoče preveriti kar na računalniku, preden jo prenesete na boks:

```bash
python3 plugins/LastScannedAnalyzer/preizkus.py
```

Skripta podtakne prazne module namesto Enigme, na začasni kopiji `lamedb` in
buketov pa preveri branje baze, iskanje novih kanalov, pisanje in ustvarjanje
buketov ter izris vrstic. Konča z izpisom, koliko preverb je padlo.

## Kaj plugin podpira

- `lamedb` (zapis `/4/`) in `lamedb5` (zapis `/5/`),
- satelitske, kabelske in antenske kanale,
- Python 3 in Python 2 (starejše slike),
- TV in radijske kanale,
- vmesnik v ločljivosti 1280x720 in 1920x1080.

Videz je risan za 1280x720. Ob zagonu plugin prebere velikost zaslona in vse
mere ter pisave po potrebi pomnoži, zato na vmesniku 1920x1080 ni stisnjen v
kot, ampak zapolni zaslon. Ker nosi svoj videz, je videti enako ne glede na
nameščeno temo risiverja.
