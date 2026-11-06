#!/bin/sh
# Shorts/Reels verticais (1080×1920) a partir dos episódios: sh make_shorts.sh <idioma: pt|en|es>
# Ep. 01: "Haja luz!" (19,4 s → 60,0 s) · Ep. 02: "O coração" (69,6 s → 91,6 s)
set -e
M=$(cd "$(dirname "$0")" && pwd); F="$M/../filmes"; l=$1
suf=$([ "$l" = pt ] && echo "" || echo "_$l"); bgs=$([ "$l" = pt ] && echo "" || echo "_$l")
out=$([ "$l" = pt ] && echo "$M" || echo "$M/$l")
cut() {  # vídeo início duração fundo saída
  [ -f "$1" ] || { echo "falta $1"; return 0; }
  ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$4" -ss "$2" -t "$3" -i "$1" -filter_complex \
    "[1:v]scale=1080:608,fade=in:st=0:d=0.4,fade=out:st=$(echo "$3 - 0.5" | bc):d=0.5[v];[0:v][v]overlay=0:656:shortest=1,format=yuv420p[o];[1:a]afade=in:st=0:d=0.3,afade=out:st=$(echo "$3 - 0.8" | bc):d=0.8[a]" \
    -map "[o]" -map "[a]" -c:v libx264 -preset slow -crf 23 -r 24 -c:a aac -b:a 160k -t "$3" -movflags +faststart "$5"
  echo "ok $5"
}
BG="$M/_render"; [ "$l" = pt ] || BG="$M/_render/i18n"
cut "$F/ep01-a-criacao/a-criacao$suf.mp4" 19.4 40.6 "$BG/short_bg${bgs}_0.jpg" "$out/short-reels-ep01-haja-luz$suf.mp4"
cut "$F/ep02-adao-e-eva/adao-e-eva$suf.mp4" 69.6 22.0 "$BG/short_bg2${bgs}_0.jpg" "$out/short-reels-ep02-o-coracao$suf.mp4"
