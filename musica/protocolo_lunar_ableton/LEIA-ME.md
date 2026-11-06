# Protocolo Lunar: pacote para Ableton Live

- **Andamento:** 144 BPM · **Compasso:** 4/4 · **Tom:** Ré frígio (D phrygian)
- **Duração:** 8:00 (288 compassos), mais 3 s de cauda
- **Formato dos stems:** FLAC 24-bit, 44,1 kHz, estéreo. Todos começam em 0:00 e terminam juntos.

## Conteúdo

```
Stems/                         15 camadas de áudio, com reverb e delay já aplicados
MIDI/                          as notas de cada camada melódica e a bateria
Protocolo Lunar - Master.flac  a mixagem final, para referência
arrangement.json               onde começa cada seção
```

### Stems
| Arquivo | O que tem |
|---|---|
| 01 Kick | Bumbo (inclui os kicks abafados da intro e do breakdown) |
| 02 Bass | Baixo rolante (padrão off-beat de semicolcheias) |
| 03 Hats | Hi-hat aberto no contratempo |
| 04 Shakers | Shaker em semicolcheias, com swing |
| 05 Ride | Ride no contratempo |
| 06 Claps & Snares | Palmas nos tempos 2 e 4, e os snare rolls dos builds |
| 07 Toms & Metal | Viradas de tom e as batidas metálicas "de máquina" |
| 08 Acid | Riff acid 303 |
| 09 Growl | Stabs FM rosnados |
| 10 Lead | Gancho FM dos drops e a melodia lenta do breakdown |
| 11 Pad & Drone | Pads do breakdown e o drone grave em Ré |
| 12 Machine | Arpejo de máquina (bitcrush) e os bipes de "dados" |
| 13 FX | Risers, crashes, swirls, zaps e sinos |
| 14 Atmosphere | Vento e grilos |
| 15 Vocals | Vozes robóticas e sussurradas |

Os stems estão **6 dB abaixo** da mixagem final, para não distorcerem quando somados. Com todos os faders em 0 dB, a soma corresponde à mixagem antes do limiter. Para chegar ao volume do master, coloque um Limiter (ou um Glue Compressor seguido de Limiter) no Master.

### MIDI
`Bass`, `Acid`, `Growl`, `Lead Hook`, `Lead Slow`, `Machine Arp`, `Pad`, `Drone` e `Drums`.

- `Drums.mid` usa o mapa General MIDI, que casa com os pads de um Drum Rack:
  Kick = C1 (36), Snare = D1 (38), Clap = D#1 (39), Shaker = F#1 (42), Tom grave = A1 (45),
  Open Hat = A#1 (46), Tom médio = B1 (47), Tom agudo = C2 (48), Ride = D#2 (51), Metal = G#2 (56).
- Use os MIDIs para trocar qualquer timbre por um synth seu (Operator, Wavetable, Serum…) mantendo as mesmas notas.

## Como montar no Ableton

1. Crie um Live Set novo e mude o andamento para **144 BPM** antes de importar.
2. **Desligue o Auto-Warp**: Preferências → Record/Warp/Launch → desmarque **Auto-Warp Long Samples**. Assim o Live não tenta adivinhar o andamento dos stems.
3. Na **Arrangement View**, selecione todos os arquivos da pasta `Stems` no navegador (ou no Finder/Explorer) e arraste-os juntos para o início do compasso 1. Segure **Ctrl** (Windows) ou **Cmd** (Mac) ao soltar, para que cada arquivo vá para uma faixa separada.
4. Confira se todos os clipes começam exatamente em **1.1.1**. Os stems já estão em 144 BPM, então ficam alinhados com o grid sem warp.
5. (Opcional) Arraste os arquivos da pasta `MIDI` para faixas MIDI, também no compasso 1, e coloque um instrumento em cada uma. Mute o stem de áudio correspondente se quiser substituir o som.
6. Salve o set (**File → Save Live Set As…**) e use **File → Collect All and Save** para copiar os stems para dentro do projeto.

## Mapa das seções (para marcadores/locators)

| Compasso | Tempo | Seção |
|---|---|---|
| 1 | 0:00 | Intro |
| 33 | 0:53 | Build 1 |
| 49 | 1:20 | Groove 1 |
| 81 | 2:13 | Mid-break |
| 89 | 2:26 | Groove 2 (a máquina assume) |
| 121 | 3:20 | Breakdown |
| 145 | 4:00 | Build 2 |
| 153 | 4:13 | Drop |
| 201 | 5:33 | Machine break (as "ordens") |
| 209 | 5:46 | Drop 2 |
| 249 | 6:53 | Outro (para mixar) |

## Recriar ou alterar

Tudo é gerado pelo script `protocolo_lunar.py`. Ele precisa de Python 3 com `numpy`, `scipy`, `soundfile`, `mido`, além de `espeak-ng` e `ffmpeg` instalados. Rode:

```
python3 protocolo_lunar.py
```
