#!/bin/sh
# Renderiza as versões traduzidas dos episódios: sh render_i18n.sh "ep01-a-criacao:a-criacao ep02-adao-e-eva:adao-e-eva" "en es"
# Para cada episódio e idioma: quadros (?lang=xx) → master −14 LUFS → arquivo web (~5,3 Mbps, < 100 MB) → <nome>_<xx>.mp4
set -e
HERE=$(cd "$(dirname "$0")" && pwd); LIB=${LIB:-/home/user/lemomo-ai/lemo-opuscar}; TMP=${TMP:-/tmp}
for pair in $1; do
  ep=${pair%%:*}; name=${pair#*:}; P="$HERE/$ep"
  for l in $2; do
    [ -f "$P/${name}_$l.mp4" ] && { echo "já existe: ${name}_$l.mp4"; continue; }
    echo "== $ep $l: quadros ($(date +%H:%M))"
    (cd "$LIB" && node core/render/video.mjs "$P" --fps 24 --workers 4 --q "lang=$l" --out "$P/out/video_$l.mp4" | grep -E "done|rror" || true)
    echo "== $ep $l: master ($(date +%H:%M))"
    sh "$P/master.sh" "$P/out/video_$l.mp4" "$P/mix_$l.wav" "$TMP/${name}_${l}_alta.mp4"
    (cd "$TMP" && ffmpeg -hide_banner -loglevel error -y -i "${name}_${l}_alta.mp4" -vf hqdn3d=1.2:1.2:3:3 -c:v libx264 -preset slow -b:v 5300k -pass 1 -passlogfile "p_${name}_$l" -an -f mp4 /dev/null \
      && ffmpeg -hide_banner -loglevel error -y -i "${name}_${l}_alta.mp4" -vf hqdn3d=1.2:1.2:3:3 -c:v libx264 -preset slow -b:v 5300k -maxrate 8000k -bufsize 11000k -pass 2 -passlogfile "p_${name}_$l" -pix_fmt yuv420p -c:a copy -movflags +faststart "$P/${name}_$l.mp4")
    rm -f "$P/out/video_$l.mp4"
    echo "== pronto: ${name}_$l.mp4 $(du -h "$P/${name}_$l.mp4" | cut -f1) ($(date +%H:%M))"
  done
done
echo FIM
