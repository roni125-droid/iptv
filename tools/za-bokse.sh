#!/bin/sh
# Pripravi sezname za prenos na Android TV bokse prek USB kljucka.
#
# Uporaba:
#   ./tools/za-bokse.sh /media/usb
#   ./tools/za-bokse.sh                 # privzeto v mapo ./za-bokse
#
# Na boksu nato v predvajalniku izberite lokalno datoteko namesto naslova URL.
# Tako seznam ni nikjer javno dosegljiv.

set -eu

cilj="${1:-za-bokse}"
vir="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$cilj"

for f in ex-yu.m3u si.m3u hr.m3u ba.m3u rs.m3u; do
    if [ -f "$vir/$f" ]; then
        cp "$vir/$f" "$cilj/$f"
        kanalov=$(grep -c '^#EXTINF' "$cilj/$f" || true)
        printf '%-12s %3s kanalov\n' "$f" "$kanalov"
    else
        printf '%-12s manjka, najprej pozenite tools/build.py\n' "$f"
    fi
done

cat > "$cilj/BERI-ME.txt" <<'TXT'
Sezname odprite v predvajalniku na boksu kot LOKALNO datoteko.

TiViMate:       Settings -> Playlists -> Add playlist -> Open file
IPTV Smarters:  Load Your Playlist -> M3U File
VLC:            Brskaj -> Notranji pomnilnik

Datoteko ex-yu.m3u vsebuje vse stiri drzave skupaj.
Ostale so locene po drzavah.
TXT

printf '\nPripravljeno v: %s\n' "$cilj"
printf 'Kopirajte mapo na USB kljucek in jo prenesite na vsak boks.\n'
