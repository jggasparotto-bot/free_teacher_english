#!/bin/sh
# Renderiza toda a arte da marca: sh render.sh  (LIB = biblioteca Lemo-Opuscar)
set -e
HERE=$(cd "$(dirname "$0")" && pwd); LIB=${LIB:-/home/user/lemomo-ai/lemo-opuscar}; OUT=${OUT:-$HERE/../_render}
mkdir -p "$OUT"; cd "$LIB"
while read page w h; do
  [ -z "$page" ] && continue
  node core/render/still.mjs "$HERE" 0 --size ${w}x${h} --q "page=$page&w=$w&h=$h" --out "$OUT" --prefix "${page}_" >/dev/null
  echo "$page ${w}x${h}"
done <<LIST
avatar 800 800
mark 600 600
banner 2560 1440
pl_at 1920 1080
pl_nt 1920 1080
pl_dormir 1920 1080
post_ola 1080 1350
post_como 1080 1350
post_ep01 1080 1350
colorir 1080 1350
colorir_a4 1240 1754
story_novo 1080 1920
reel_ep01 1080 1920
short_bg 1080 1920
hl_episodios 1080 1920
hl_colorir 1080 1920
hl_versiculos 1080 1920
hl_sobre 1080 1920
hl_novidades 1080 1920
LIST
