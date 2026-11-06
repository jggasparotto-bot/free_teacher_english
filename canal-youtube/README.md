# 🎨 Bíblia em Traços — Canal de YouTube

Histórias da Bíblia desenhadas para toda a família.

| O quê | Onde |
|---|---|
| 📺 Plano completo do canal (identidade, formatos, calendário, SEO, configuração, crescimento) | [`01-plano-do-canal.md`](01-plano-do-canal.md) |
| 📝 Roteiros das 20 histórias (cenas, narração, lição, Short, título, tags e miniatura) | [`roteiros/`](roteiros/) |
| 🎬 Episódio piloto pronto: **A Criação** (1080p, 2min36, trilha original + legendas) | [`video/ep01/ep01_a_criacao.mp4`](video/ep01/ep01_a_criacao.mp4) |
| 🖼️ Miniatura do piloto (1280×720) | [`video/ep01/miniatura_ep01.png`](video/ep01/miniatura_ep01.png) |
| ⏱️ Tempos das falas para gravar a narração | [`video/ep01/ep01_a_criacao.srt`](video/ep01/ep01_a_criacao.srt) |
| ⚙️ Gerador do vídeo (desenhos, animação e trilha feitos 100% em código) | [`video/gerar_episodio_01.py`](video/gerar_episodio_01.py) |

## Roteiros

| Nº | História | Nº | História |
|---|---|---|---|
| 01 | [A Criação](roteiros/01-a-criacao.md) ✅ vídeo | 11 | [Davi e o Gigante Golias](roteiros/11-davi-e-golias.md) |
| 02 | [Adão e Eva no Jardim do Éden](roteiros/02-adao-e-eva.md) | 12 | [Daniel na Cova dos Leões](roteiros/12-daniel-na-cova-dos-leoes.md) |
| 03 | [Noé e a Grande Arca](roteiros/03-noe-e-a-arca.md) | 13 | [Os Três Amigos na Fornalha](roteiros/13-tres-amigos-na-fornalha.md) |
| 04 | [A Torre de Babel](roteiros/04-torre-de-babel.md) | 14 | [Jonas e o Grande Peixe](roteiros/14-jonas.md) |
| 05 | [Abraão e as Estrelas do Céu](roteiros/05-abraao.md) | 15 | [A Rainha Ester](roteiros/15-rainha-ester.md) |
| 06 | [José e a Túnica Colorida](roteiros/06-jose.md) | 16 | [O Nascimento de Jesus](roteiros/16-nascimento-de-jesus.md) 🎄 |
| 07 | [O Bebê Moisés e a Sarça Ardente](roteiros/07-moises-bebe-e-sarca.md) | 17 | [Jesus Acalma a Tempestade](roteiros/17-jesus-acalma-a-tempestade.md) |
| 08 | [A Travessia do Mar Vermelho](roteiros/08-mar-vermelho.md) | 18 | [A Multiplicação dos Pães e Peixes](roteiros/18-multiplicacao-dos-paes.md) |
| 09 | [As Muralhas de Jericó](roteiros/09-muralhas-de-jerico.md) | 19 | [O Filho Pródigo](roteiros/19-filho-prodigo.md) |
| 10 | [Sansão, o Homem Mais Forte](roteiros/10-sansao.md) | 20 | [Jesus Ressuscitou!](roteiros/20-jesus-ressuscitou.md) 🌅 |

## Como gerar o vídeo de novo

Requisitos: Python 3, `pillow`, `numpy` e `ffmpeg`.

```bash
cd canal-youtube/video
python3 gerar_episodio_01.py saida            # vídeo completo (~2-10 min, conforme o computador)
python3 gerar_episodio_01.py saida --thumbs   # só prévias em PNG de cada cena (rápido)
python3 gerar_miniatura_01.py                  # miniatura 1280x720
```

O vídeo sai **sem narração de voz**, com legendas embutidas e a trilha original. Grave a sua voz seguindo o
arquivo `.srt` e junte no CapCut, DaVinci Resolve ou Shotcut, com a trilha a cerca de −20 dB embaixo da voz.
Para fazer um novo episódio, copie o script, troque a lista `SCENES` (falas) e as funções `sc_*` (desenhos).
