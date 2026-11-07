#!/bin/sh
# Fila de renderização dos episódios: lê fila.txt (linhas "pasta:nome"; a linha FIM encerra).
# Espera a fila das versões traduzidas terminar; renderiza cada episódio cujo mix.wav já exista.
HERE=$(cd "$(dirname "$0")" && pwd); LIB=${LIB:-/home/user/lemomo-ai/lemo-opuscar}; TMP=${TMP:-/tmp}
while pgrep -f render_i18n.sh >/dev/null; do sleep 60; done
while true; do
  next=""; fim=0
  while read -r ln; do
    [ "$ln" = FIM ] && { fim=1; continue; }
    [ -z "$ln" ] && continue
    ep=${ln%%:*}; name=${ln#*:}
    [ -f "$HERE/$ep/$name.mp4" ] && continue
    [ -f "$HERE/$ep/mix.wav" ] && [ -f "$HERE/$ep/pronto" ] && { next=$ln; break; }
  done < "$HERE/fila.txt"
  if [ -z "$next" ]; then [ $fim = 1 ] && ! grep -v FIM "$HERE/fila.txt" | while read -r l; do [ -f "$HERE/${l%%:*}/${l#*:}.mp4" ] || echo x; done | grep -q x && { echo "FIM DA FILA $(date +%H:%M)"; exit 0; }; sleep 60; continue; fi
  ep=${next%%:*}; name=${next#*:}; P="$HERE/$ep"
  echo "== $ep: quadros ($(date +%H:%M))"
  (cd "$LIB" && node core/render/events.mjs "$P" >/dev/null 2>&1; node "$HERE/chunk.mjs" "$P" --fps 24 --workers 4 --out "$P/out/video.mp4" 2>&1 | grep -E "done|rror|falhou")
  echo "== $ep: master ($(date +%H:%M))"
  sh "$HERE/ep01-a-criacao/master.sh" "$P/out/video.mp4" "$P/mix.wav" "$TMP/${name}_alta.mp4"
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/${name}_alta.mp4"); BR=$(python3 -c "print(min(5300, int(94*8388.608/$D - 220)))")   # cabe em < 100 MB
  (cd "$TMP" && ffmpeg -hide_banner -loglevel error -y -i "${name}_alta.mp4" -vf hqdn3d=1.2:1.2:3:3 -c:v libx264 -preset slow -b:v ${BR}k -pass 1 -passlogfile "q_$name" -an -f mp4 /dev/null \
    && ffmpeg -hide_banner -loglevel error -y -i "${name}_alta.mp4" -vf hqdn3d=1.2:1.2:3:3 -c:v libx264 -preset slow -b:v ${BR}k -maxrate 8000k -bufsize 11000k -pass 2 -passlogfile "q_$name" -pix_fmt yuv420p -c:a copy -movflags +faststart "$P/$name.mp4")
  rm -f "$P/out/video.mp4" "$TMP/${name}_alta.mp4"
  echo "== pronto: $name.mp4 $(du -h "$P/$name.mp4" | cut -f1) ($(date +%H:%M))"
done
