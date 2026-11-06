"""Trilha original de "Adão e Eva no Jardim do Éden" (Bíblia em Traços): valsa em 3/4, 92 BPM, sol maior.
Ukulele, flauta doce, clarinete, glockenspiel, caixinha de música (modelagem física) e woodblock.
O tema aparece inteiro uma única vez, mais lento, quando Adão e Eva saem do jardim (o cuidado de Deus).
Lê ../events.json. Uso: $LIB/.venv/bin/python music/score.py → music/score.wav + music/stems/*.wav
"""
import sys, os, json
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', '/home/user/lemomo-ai/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S, pluck as P
from core.audio.sfx import SR, add
S.seed(9)
E = json.load(open(os.path.join(HERE, '..', 'events.json'))); DUR = E['dur']; EV = E['ev']; N = int(DUR * SR)
cue = {e['id']: e['t'] for e in EV if e['type'] == 'cue'}
first = lambda ty: next(e for e in EV if e['type'] == ty)
B = 60 / 92; BAR = 3 * B
stems = {k: np.zeros((N, 2), np.float32) for k in ['uke', 'glock', 'recorder', 'clarinet', 'mbox', 'perc']}
m = S.midi
def note(st, inst, t, p, d, vel=.6, pan=0., gain=1., **kw):
    if t < DUR - 0.05: add(stems[st], S.note(inst, p, d, vel, **kw), t, gain, pan)
def mbox(t, p, vel=.6, pan=.1, gain=1., bend=None):
    if t >= DUR - 0.05: return
    x = P.pluck('music_box', m(p) if isinstance(p, str) else p, None, vel)
    if bend:
        rate = 2 ** (bend / 12); pos = np.arange(0, len(x) - 1, rate); i = pos.astype(int); f = pos - i; x = (x[i] * (1 - f) + x[i + 1] * f).astype(np.float32)
    add(stems['mbox'], x, t, gain, pan)
def glock(t, p, vel=.5, pan=0., gain=1.): note('glock', 'glockenspiel', t, p, 1.6, vel, pan, gain, release=1.2)
def wood(t, var='a', vel=.4, pan=-.3, gain=1.):
    if t < DUR - 0.05: add(stems['perc'], S.hit('woodblock', var, vel), t, gain, pan)
CH = {'G': ('G2', ['B3', 'D4', 'G4']), 'C': ('C3', ['C4', 'E4', 'G4']), 'D': ('D3', ['A3', 'D4', 'F#4']), 'Em': ('E3', ['B3', 'E4', 'G4']), 'Am': ('A2', ['A3', 'C4', 'E4'])}
PROG = ['G', 'C', 'D', 'G', 'Em', 'C', 'D', 'G']
THEME = [  # tema próprio do episódio (compasso de 3 tempos)
    [('D5', 0, 1), ('B4', 1, 1), ('G4', 2, 1)],
    [('E5', 0, 1.5), ('D5', 1.5, .5), ('C5', 2, 1)],
    [('A4', 0, 1), ('B4', 1, .5), ('C5', 1.5, .5), ('D5', 2, 1)],
    [('B4', 0, 3)],
    [('G4', 0, 1), ('B4', 1, 1), ('E5', 2, 1)],
    [('E5', 0, 1.5), ('G5', 1.5, .5), ('E5', 2, 1)],
    [('D5', 0, 1), ('C5', 1, 1), ('A4', 2, 1)],
    [('G4', 0, 3)],
]
def theme_bar(i, t0, fn, beat=B, trans=0):
    for p, b, d in THEME[i % 8]: fn(t0 + b * beat, m(p) + trans, d * beat)
def uke_bar(t0, ch, vel=.5, pan=-.25, gain=1., beat=B):
    root, tri = CH[ch]
    r = m(root) + 12
    while r < m('B2'): r += 12
    note('uke', 'ukulele', t0, r, beat * 1.2, vel * 1.1, pan, gain)
    for k in (1, 2):
        for j, p in enumerate(tri): note('uke', 'ukulele', t0 + k * beat + j * 0.018, p, beat * 0.9, vel * (0.8 if k == 2 else 0.9), pan + 0.1 * j, gain)
def clar(t0, p, d, vel=.35, stac=False, gain=1.):
    note('clarinet', 'clarinet_stac' if stac else 'clarinet', t0, p, d, vel, -.2, gain, **({} if stac else {'attack': .15, 'release': .5}))
def waltz(t0, t1, vel=.48, clarinet=True, recorder_bars=(), wb=False):
    nb = int((t1 - t0) / BAR)
    for b in range(nb):
        tb = t0 + b * BAR; ch = PROG[b % 8]
        uke_bar(tb, ch, vel)
        if clarinet and b % 2 == 0: clar(tb, max(m(CH[ch][0]) + 12, m('D3')), BAR * 0.95, .28, gain=.8)
        if wb: wood(tb, 'a', .28, -.4); wood(tb + B, 'b', .18, .4); wood(tb + 2 * B, 'b', .18, .4)
        if b in recorder_bars: theme_bar(b, tb, lambda tt, p, d: note('recorder', 'recorder', tt, p, d * .95, .32, .2, .7, release=.3))

# A · vinheta e título (0–7.6): caixinha com a primeira frase
for i in range(3): theme_bar(i, 0.25 + i * BAR, lambda t, p, d: mbox(t, p + 12, .6, .15))
glock(4.0, 'D6', .35, .3)
# B · gancho (7.6–13.6): a fruta brilha; uma pergunta na flauta
glock(8.6, 'B6', .45, -.1); glock(9.0, 'G6', .35, .1)
note('recorder', 'recorder', 8.0, 'D5', B * 2, .3, .1, .7, release=.6); note('recorder', 'recorder', 9.4, 'E5', B, .28, .1, .7); note('recorder', 'recorder', 10.1, 'F#5', B * 3, .3, .1, .7, release=.8)
note('clarinet', 'clarinet', 8.0, 'D3', BAR * 2.5, .2, -.2, .6, attack=.6, release=.8)
# C · o jardim (13.6–35): valsa do ukulele; flauta em alguns compassos; bichos com humor
waltz(cue['C'], cue['D'], recorder_bars=(2, 3, 6, 7), wb=True)
for e in EV:
    if e['type'] == 'pop' and cue['C'] < e['t'] < cue['D']: glock(e['t'], ['G6', 'B6', 'D7'][int(e['t'] * 10) % 3], .2, e.get('pan', 0) * .6, .6)
an = {e['type']: e['t'] for e in EV if e['type'] in ('lion', 'giraffe', 'turtle')}
clar(an['lion'], 'D3', .5, .55); clar(an['giraffe'], 'G4', .25, .45, True); clar(an['giraffe'] + .25, 'D5', .4, .45, True)
clar(an['turtle'], 'G3', .6, .45); clar(an['turtle'] + .65, 'F#3', .6, .4)
# D · Adão sozinho (35–40.6): só o ukulele, devagar e baixinho
for b in range(2): uke_bar(cue['D'] + b * BAR, ['Em', 'C'][b], .32)
note('recorder', 'recorder', cue['D'] + .5, 'B4', BAR * 2, .2, .1, .6, attack=.3, release=.8)
# E · Eva (40.6–45.4): o glockenspiel faz festa, coração
for i, p in enumerate(['G5', 'B5', 'D6', 'G6']): glock(41.8 + i * .07, p, .45, -.3 + i * .2)
for b in range(2): uke_bar(cue['E'] + b * BAR, ['G', 'D'][b], .45)
glock(first('heart')['t'], 'B6', .5, 0)
# F · a regra (45.4–58): pedal suave, a luz; a fruta brilha quando Deus diz "desta árvore aqui"
clar(cue['F'], 'G3', 11.0, .22); note('recorder', 'recorder', cue['F'] + .3, 'D5', BAR * 3, .22, .1, .6, attack=.5, release=1.0)
for b in range(5): theme_bar(b, cue['F'] + 0.5 + b * BAR, lambda t, p, d: mbox(t, p + 12, .3, .2, .6))
for e in EV:
    if e['type'] == 'glint': glock(e['t'], 'B6', .4, 0)
# G · a serpente (58–70.2): clarinete descendo em cromatismo, ukulele em staccato (curioso, não assustador)
t0 = cue['G']
for b in range(int((cue['H'] - t0) / BAR)):
    tb = t0 + b * BAR
    note('uke', 'ukulele', tb, ['G3', 'F#3', 'F3', 'E3'][b % 4], .25, .4, -.2)
    note('uke', 'ukulele', tb + B, 'D4', .2, .3, .1); note('uke', 'ukulele', tb + 2 * B, 'D4', .2, .3, .1)
    if b % 2 == 1: clar(tb, ['D4', 'C#4', 'C4', 'B3'][(b // 2) % 4], B * .9, .35, True); clar(tb + B, ['C#4', 'C4', 'B3', 'A#3'][(b // 2) % 4], B * .9, .3, True)
# H · a fruta (70.2–74.3): fino, um glock na mordida; depois silêncio
for e in EV:
    if e['type'] == 'bite': glock(e['t'], 'E6', .3, 0, .7)
# (silêncio 74.3–75.8)
# I · tristeza (75.8–81): clarinete grave e lento
clar(cue['I'], 'E3', BAR * 1.2, .3); clar(cue['I'] + BAR * 1.2, 'D3', BAR * 1.2, .28)
# J · entardecer (81–90.6): só a caixinha (devagar) e um pedal; um "plim" quando o coração aparece
clar(cue['J'], 'G3', 9.4, .2, gain=.7)
tt = cue['J'] + .3
for b in range(4): theme_bar(b, tt + b * BAR * 1.15, lambda x, p, d: mbox(x, p + 12, .38, .15, .75), beat=B * 1.15)
rv = first('reveal')['t']
for i, p in enumerate(['G5', 'B5', 'D6', 'G6', 'B6']): glock(rv + i * .09, p, .5 - .04 * i, -.4 + i * .2)
# K · a saída (90.6–106.2): o tema inteiro, mais lento, na flauta doce, com ukulele
bk = B * 1.12
for b in range(8):
    tb = cue['K'] + 0.4 + b * 3 * bk
    uke_bar(tb, PROG[b], .4, beat=bk)
    theme_bar(b, tb, lambda x, p, d: note('recorder', 'recorder', x, p, d * .95, .42, .15, 1.0, release=.5), beat=bk)
    if b % 2 == 0: clar(tb, max(m(CH[PROG[b]][0]) + 12, m('D3')), 3 * bk * .95, .25, gain=.8)
ray = first('ray')['t']
for i, p in enumerate(['D6', 'G6', 'B6']): glock(ray + i * .1, p, .4, 0)
# L · lição (106.2–121.6): ukulele suave; silêncio antes de "E mesmo quando a gente erra…"
sil = [e for e in EV if e['type'] == 'silence'][-1]; s0, s1 = sil['t'], sil['t'] + sil['dur']
b = 0
while cue['L'] + b * BAR < cue['M'] - .5:
    tb = cue['L'] + b * BAR
    if not (s0 - BAR < tb < s1): uke_bar(tb, PROG[b % 8], .36)
    b += 1
for e in EV:
    if e['type'] == 'fence': [wood(e['t'] + k * 0.22, 'c', .25, -.4 + k * .07) for k in range(12)]
    if e['type'] == 'heart' and e['t'] > 100: glock(e['t'], 'G6', .45, 0); glock(e['t'] + .12, 'D6', .35, .1)
# M · final (121.6–fim): conjunto, acorde que resolve, caixinha até o fim
t = cue['M']
for b in range(5):
    tb = t + b * BAR; uke_bar(tb, PROG[b % 8], .48); wood(tb, 'a', .28, -.4)
    theme_bar(b + 4, tb, lambda x, p, d: note('recorder', 'recorder', x, p, d * .95, .38, .15, .9, release=.4))
tr = t + 5 * BAR
for k, p in enumerate(['G3', 'B3', 'D4', 'G4', 'B4']): note('uke', 'ukulele', tr + 0.03 * k, p, 3.0, .5, -.1)
note('recorder', 'recorder', tr, 'G5', BAR * 2, .38, .15, .9, release=1.0)
for i, p in enumerate(['G5', 'B5', 'D6', 'G6']): glock(tr + i * .06, p, .42, -.3 + i * .2)
tt = tr + 2 * BAR
while tt < DUR - 2 * BAR:
    for i in range(4): theme_bar(i, tt + i * BAR, lambda x, p, d: mbox(x, p + 12, .3, .15, .7))
    tt += 4 * BAR

os.makedirs(os.path.join(HERE, 'stems'), exist_ok=True)
fade = np.clip((DUR - np.arange(N) / SR) / 3.0, 0, 1)[:, None]
mix = np.zeros((N, 2), np.float32)
for k, x in stems.items(): x = x * fade; sf.write(os.path.join(HERE, 'stems', k + '.wav'), x, SR); mix += x
pk = np.abs(mix).max(); mix = mix / pk * 0.8 if pk > 0.8 else mix
sf.write(os.path.join(HERE, 'score.wav'), mix, SR)
print('score.wav', DUR, 's  peak', round(float(pk), 3))
