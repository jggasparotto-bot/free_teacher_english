#!/bin/sh
# Masterização com ffmpeg 6.x (o mux.sh da biblioteca pede ffmpeg 7+): loudnorm em duas passadas → −14 LUFS, pico real −1,5 dB; junta com o vídeo.
# Uso: sh master.sh out/video.mp4 mix.wav a-criacao.mp4
set -e
V=$1; A=$2; OUT=$3; TMP=$(mktemp -d)
J=$(ffmpeg -hide_banner -nostats -i "$A" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | sed -n "s/.*\"$1\" : \"\([^\"]*\)\".*/\1/p"; }
ffmpeg -hide_banner -loglevel error -y -i "$A" -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -c:a pcm_s16le "$TMP/norm.wav"
ffmpeg -hide_banner -loglevel error -y -i "$V" -i "$TMP/norm.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf ${CRF:-22} -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
rm -rf "$TMP"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tr -s ' '
