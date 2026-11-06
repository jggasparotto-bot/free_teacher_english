#!/bin/sh
# Narra vários episódios em sequência: sh narrar_lote.sh  (edite a lista abaixo)
cd "$(dirname "$0")/.."
PY=/home/user/lemomo-ai/lemo-opuscar/.venv/bin/python
while pgrep -f "story_build.py roteiros/07" >/dev/null; do sleep 20; done
for spec in "08-mar-vermelho|ep08-mar-vermelho|As Muralhas de Jericó" "09-muralhas-de-jerico|ep09-jerico|Sansão, o Homem Mais Forte" "10-sansao|ep10-sansao|Davi e o Gigante Golias"; do
  r=${spec%%|*}; rest=${spec#*|}; e=${rest%%|*}; n=${rest#*|}
  [ -f filmes/$e/story.json ] && continue
  $PY filmes/story_build.py roteiros/$r.md filmes/$e "$n" 2>&1 | tail -1
done
echo FIM
