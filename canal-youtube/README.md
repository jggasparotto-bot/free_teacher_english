# 🎨 Bíblia em Traços — Canal de YouTube

Histórias da Bíblia desenhadas para toda a família.

| O quê | Onde |
|---|---|
| 📺 Plano completo do canal (identidade, formatos, calendário, SEO, configuração, crescimento) | [`01-plano-do-canal.md`](01-plano-do-canal.md) |
| 🎨 **Marca: imagens e textos do YouTube e do Instagram** (perfil, banner, playlists, posts, destaques, story, Reels, desenho para colorir) | [`marca/TEXTOS.md`](marca/TEXTOS.md) · [`marca/youtube/`](marca/youtube/) · [`marca/instagram/`](marca/instagram/) |
| 📝 Roteiros das 20 histórias (cenas, narração, lição, Short, título, tags e miniatura) | [`roteiros/`](roteiros/) |
| ⭐ **Episódio 1 oficial: A Criação, no estilo giz de cera** (1080p, 2min11, narrado, trilha com instrumentos reais, legendas) | [`filmes/ep01-a-criacao/a-criacao.mp4`](filmes/ep01-a-criacao/a-criacao.mp4) |
| 🖼️ Miniatura do episódio 1 (giz de cera) | [`filmes/ep01-a-criacao/poster.jpg`](filmes/ep01-a-criacao/poster.jpg) |
| 🎥 Como o filme foi pensado (estrutura, planos, música, som) | [`filmes/ep01-a-criacao/TREATMENT.md`](filmes/ep01-a-criacao/TREATMENT.md) |
| ⭐ **Episódio 2: Adão e Eva no Jardim do Éden** (giz de cera, narrado, legendas) | [`filmes/ep02-adao-e-eva/adao-e-eva.mp4`](filmes/ep02-adao-e-eva/adao-e-eva.mp4) · [miniatura](filmes/ep02-adao-e-eva/poster.jpg) · [tratamento](filmes/ep02-adao-e-eva/TREATMENT.md) |
| 🎬 Primeira versão do piloto (desenho vetorial simples) | [`video/ep01/ep01_a_criacao.mp4`](video/ep01/ep01_a_criacao.mp4) |
| 🎙️ Amostra das 3 vozes de narrador disponíveis (Dora, Alex, Santa) | [`video/ep01/amostra_vozes.mp3`](video/ep01/amostra_vozes.mp3) |
| 🔊 Só o áudio do episódio (voz + trilha) | [`video/ep01/audio_narrado.mp3`](video/ep01/audio_narrado.mp3) |
| 🖼️ Miniatura do piloto (1280×720) | [`video/ep01/miniatura_ep01.png`](video/ep01/miniatura_ep01.png) |
| ⏱️ Legendas com o tempo de cada fala (pode subir no YouTube como legenda) | [`video/ep01/ep01_a_criacao.srt`](video/ep01/ep01_a_criacao.srt) |
| ⚙️ Gerador do vídeo (desenhos, animação, narração e trilha feitos 100% em código) | [`video/gerar_episodio_01.py`](video/gerar_episodio_01.py) |

## Roteiros

| Nº | História | Nº | História |
|---|---|---|---|
| 01 | [A Criação](roteiros/01-a-criacao.md) ✅ vídeo | 11 | [Davi e o Gigante Golias](roteiros/11-davi-e-golias.md) |
| 02 | [Adão e Eva no Jardim do Éden](roteiros/02-adao-e-eva.md) ✅ vídeo | 12 | [Daniel na Cova dos Leões](roteiros/12-daniel-na-cova-dos-leoes.md) |
| 03 | [Noé e a Grande Arca](roteiros/03-noe-e-a-arca.md) | 13 | [Os Três Amigos na Fornalha](roteiros/13-tres-amigos-na-fornalha.md) |
| 04 | [A Torre de Babel](roteiros/04-torre-de-babel.md) | 14 | [Jonas e o Grande Peixe](roteiros/14-jonas.md) |
| 05 | [Abraão e as Estrelas do Céu](roteiros/05-abraao.md) | 15 | [A Rainha Ester](roteiros/15-rainha-ester.md) |
| 06 | [José e a Túnica Colorida](roteiros/06-jose.md) | 16 | [O Nascimento de Jesus](roteiros/16-nascimento-de-jesus.md) 🎄 |
| 07 | [O Bebê Moisés e a Sarça Ardente](roteiros/07-moises-bebe-e-sarca.md) | 17 | [Jesus Acalma a Tempestade](roteiros/17-jesus-acalma-a-tempestade.md) |
| 08 | [A Travessia do Mar Vermelho](roteiros/08-mar-vermelho.md) | 18 | [A Multiplicação dos Pães e Peixes](roteiros/18-multiplicacao-dos-paes.md) |
| 09 | [As Muralhas de Jericó](roteiros/09-muralhas-de-jerico.md) | 19 | [O Filho Pródigo](roteiros/19-filho-prodigo.md) |
| 10 | [Sansão, o Homem Mais Forte](roteiros/10-sansao.md) | 20 | [Jesus Ressuscitou!](roteiros/20-jesus-ressuscitou.md) 🌅 |

## Como gerar o episódio em giz de cera

O estilo "Crayon Picture Book" vem da biblioteca [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) (licença MIT).
Precisa de Node 20+, Python 3.11+ e ffmpeg; a biblioteca instala o resto:

```bash
git clone https://github.com/lemomo-ai/lemo-opuscar.git ~/lemo-opuscar
cd ~/lemo-opuscar && sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice music
sh tools/fetch.sh instruments vcsl && sh tools/fetch.sh instruments freepats && sh tools/fetch.sh instruments vsco2ce
LIB=~/lemo-opuscar sh /caminho/para/canal-youtube/filmes/ep01-a-criacao/build.sh
```

Tudo o que aparece e soa no filme está em código: `film.js` (linha do tempo, câmera, páginas), `chars.js`
(personagens), `music/score.py` (trilha), `mix.py` (efeitos, voz e mixagem) e `lines.json` (as falas).
Para um novo episódio, copie a pasta e troque as falas, os desenhos e a linha do tempo.

## Como gerar a primeira versão (desenho vetorial simples)

Requisitos: Python 3, `pillow`, `numpy`, `ffmpeg`, `espeak-ng` e `pip install kokoro-onnx soundfile`.
Na primeira execução, o modelo de voz (~350 MB) é baixado sozinho para `video/modelos/`.

```bash
cd canal-youtube/video
python3 gerar_episodio_01.py saida            # vídeo completo e narrado (~3-10 min, conforme o computador)
VOZ=pm_alex python3 gerar_episodio_01.py saida # mesmo vídeo com voz masculina (pf_dora | pm_alex | pm_santa)
python3 gerar_episodio_01.py saida --sem-voz  # só trilha + legendas, para gravar a própria voz
python3 gerar_episodio_01.py saida --thumbs   # só prévias em PNG de cada cena (rápido)
python3 gerar_miniatura_01.py                  # miniatura 1280x720
```

O vídeo sai **narrado** por uma voz neural gratuita em português, que roda no próprio computador. A música
abaixa sozinha enquanto o narrador fala, e o áudio já sai no volume que o YouTube recomenda (cerca de −14 a −15 LUFS).
Também dá para mudar a velocidade da fala com `VELOCIDADE_VOZ=0.8`. Para trocar pela sua própria voz depois,
use `--sem-voz` e grave seguindo o arquivo `.srt`.
Para fazer um novo episódio, copie o script, troque a lista `SCENES` (falas) e as funções `sc_*` (desenhos).
