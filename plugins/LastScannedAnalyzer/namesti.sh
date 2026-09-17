#!/bin/sh
# Namestitev plugina LastScanned Analyzer na risiver Enigma2.
#
# Na racunalniku:
#     scp -r LastScannedAnalyzer root@<naslov-risiverja>:/tmp/
#     ssh root@<naslov-risiverja> "sh /tmp/LastScannedAnalyzer/namesti.sh"
#
# Ali pa datoteke prenesite z USB kljuckom in skripto pozenite na risiverju.

CILJ=/usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer
IZVOR=$(dirname "$0")

echo "Namescam v $CILJ"
mkdir -p "$CILJ" || exit 1

for datoteka in __init__.py plugin.py lamedb.py bouquets.py picon.py \
                skin.py update.py preizkus.py plugin.png version.json; do
    if [ -f "$IZVOR/$datoteka" ]; then
        cp "$IZVOR/$datoteka" "$CILJ/" || exit 1
    fi
done

# Stare prevedene datoteke znajo prekriti novo kodo.
rm -f "$CILJ"/*.pyc "$CILJ"/*.pyo
rm -rf "$CILJ/__pycache__"

echo "Namesceno. Enigmo je treba znova zagnati:"
echo "    init 4 && sleep 3 && init 3"
echo "ali prek menija: Standby / Restart -> GUI restart."
