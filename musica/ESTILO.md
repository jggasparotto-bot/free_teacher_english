# Estilo do projeto: full-on próprio

A assinatura do projeto é a soma de três influências. Toda faixa nova deve trazer **as três**, mas com **material novo**: riffs, tom, timbres e estrutura diferentes das faixas anteriores.

| Influência | O que a gente pega | O que NÃO é |
|---|---|---|
| **Burn in Noise** | Groove hipnótico com baixo numa nota só, acid que abre aos poucos, growls, swirls psicodélicos, seções escuras de "twist" | Não é melodia o tempo todo |
| **Regan Nano** | Harmonia frígia escura, lead "torcido" com bends e vibrato, efeitos psicodélicos (swells reversos, boings) | Não é eufórico em tom maior |
| **Dickster** | Kick e baixo duros (full power), swing nas percussões, elementos funky e brincalhões (wah, stabs, formantes "falando", sons elásticos), humor nas vozes | Não é sério e rígido o tempo todo |

## Regras fixas
- **Andamento:** 144–150 BPM, 4/4, com o baixo rolante em semicolcheias depois de cada kick (padrão K-B-B-B).
- **Duração:** 7 a 8 minutos, com intro e outro mixáveis para DJ (só kick, percussão e baixo no começo e no fim).
- **Tons:** menores ou modais escuros (frígio, frígio dominante, menor harmônico).
- **Vozes:** em **inglês**, frases curtas e originais, com efeito (robô, sussurro, stutter, eco). Nunca usar letras ou samples de outras músicas.
- **Sons:** todos sintetizados. Não usar samples gravados de terceiros.
- **Estrutura:** alternar seções hipnóticas (lado Burn in Noise) com seções de drop melódico e torcido (lado Regan), com pelo menos um momento funky ou brincalhão (lado Dickster).

## Para cada faixa nova ser diferente
Antes de compor, confira esta tabela e escolha valores que ainda **não** foram usados:

| Faixa | BPM | Tom | Tema | Timbres principais | Truque de arranjo |
|---|---|---|---|---|---|
| Três Luas | 148 | F♯ frígio | três luas, noite | acid, wah, stabs, lead torcido, supersaw | pergunta e resposta a cada 2 compassos |
| Miragem | 146 | G frígio dominante | deserto, miragem | darbuka, oud (Karplus-Strong), screamer, synth "falante" | seção half-time e modulação de meio tom no drop 2 |
| Tempestade Elétrica | 147 | B menor harmônico | tempestade, chuva | baixo em tercina, arpejo FM "vidro", hook supersaw gated (Avalon), chuva e trovões | ponte em 3/4 e final seco |

Ideias ainda não usadas: 150 BPM, percussão metálica de oficina, coral sintético, menor melódico ou dórico, baixo com slides 303 por baixo de tudo, compasso 7/8 numa quebra, tema de cidade, máquinas, floresta ou espaço.

Influências já usadas além do trio base: Avalon (hooks grandes e builds épicos) na Tempestade Elétrica.

## Código
Cada faixa é um script em `musica/` que gera o MP3 (`python3 <faixa>.py`). Os instrumentos são sintetizados com `numpy`/`scipy`, e as vozes usam o `espeak-ng`.
