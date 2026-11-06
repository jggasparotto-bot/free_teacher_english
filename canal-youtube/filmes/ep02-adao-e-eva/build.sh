#!/bin/sh
# Reconstrói o filme do zero: sh build.sh   (LIB = pasta da biblioteca Lemo-Opuscar com `setup.sh deps voice music` já feito)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-/home/user/lemomo-ai/lemo-opuscar}; export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "defina LIB com a pasta da biblioteca Lemo-Opuscar"; exit 1; }
PY="$LIB/.venv/bin/python"
cd "$LIB"
$PY core/tts/tts.py "$HERE/lines.json" "$HERE/voices"                     # 1. narração (Kokoro pf_dora, pt-BR) — Ep. 02
node core/render/events.mjs "$HERE"                                       # 2. linha do tempo → events.json
$PY "$HERE/music/score.py"                                                # 3. trilha original → music/stems
$PY "$HERE/mix.py"                                                        # 4. foley + voz + trilha → mix.wav
python3 "$HERE/tools_subs.py" && $PY core/render/srt.py "$HERE/subs.json" "$HERE/adao-e-eva.srt"   # 5. legendas
node core/render/video.mjs "$HERE" --fps 24 --workers 4 --out "$HERE/out/video.mp4"               # 6. quadro a quadro
sh "$HERE/master.sh" "$HERE/out/video.mp4" "$HERE/mix.wav" "$HERE/adao-e-eva.mp4"                  # 7. −14 LUFS + mux
