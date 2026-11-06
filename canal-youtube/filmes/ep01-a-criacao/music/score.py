"""Trilha original de "A Criação" (Bíblia em Traços): valsa em 3/4, 88 BPM, fá maior.
Ukulele (dedilhado), glockenspiel, flauta doce, clarinete, caixinha de música (modelagem física) e woodblock.
O tema de 8 compassos aparece inteiro uma única vez, na flauta doce, quando Adão e Eva são desenhados.
Lê ../events.json (mesmos tempos do filme). Uso: $LIB/.venv/bin/python music/score.py
Saída: music/score.wav + music/stems/*.wav
"""
import sys, os, json
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', '/home/user/lemomo-ai/lemo-opuscar')
sys.path.insert(0, LIB)
from core.audio import sampler as S, pluck as P
from core.audio.sfx import SR, add

S.seed(5)
E = json.load(open(os.path.join(HERE, '..', 'events.json')))
DUR = E['dur']; EV = E['ev']; N = int(DUR * SR)
cue = {e['id']: e['t'] for e in EV if e['type'] == 'cue'}
B = 60 / 88; BAR = 3 * B
stems = {k: np.zeros((N, 2), np.float32) for k in ['uke', 'glock', 'recorder', 'clarinet', 'mbox', 'perc']}
m = S.midi

def note(st, inst, t, p, d, vel=.6, pan=0., gain=1., **kw):
    if t >= DUR - 0.05: return
    add(stems[st], S.note(inst, p, d, vel, **kw), t, gain, pan)
def mbox(t, p, vel=.6, pan=.1, gain=1., bend=None):
    if t >= DUR - 0.05: return
    x = P.pluck('music_box', m(p) if isinstance(p, str) else p, None, vel)
    if bend:   # caixinha "acabando a corda": o tom cai um pouco
        rate = 2 ** (bend / 12); pos = np.arange(0, len(x) - 1, rate); i = pos.astype(int); f = pos - i; x = (x[i] * (1 - f) + x[i + 1] * f).astype(np.float32)
    add(stems['mbox'], x, t, gain, pan)
def glock(t, p, vel=.5, pan=0., gain=1.): note('glock', 'glockenspiel', t, p, 1.6, vel, pan, gain, release=1.2)
def wood(t, var='a', vel=.4, pan=-.3, gain=1.):
    if t < DUR - 0.05: add(stems['perc'], S.hit('woodblock', var, vel), t, gain, pan)

CH = {'F': ('F2', ['A3', 'C4', 'F4']), 'Bb': ('Bb2', ['Bb3', 'D4', 'F4']), 'C': ('C3', ['G3', 'C4', 'E4']), 'Dm': ('D3', ['A3', 'D4', 'F4']), 'Gm': ('G2', ['Bb3', 'D4', 'G4'])}
PROG = ['F', 'Bb', 'C', 'F', 'F', 'Bb', 'C', 'F']
# tema (compassos de 3 tempos): (nota, tempo de início, duração em tempos)
THEME = [
    [('C5', 0, 1), ('A4', 1, 1), ('F4', 2, 1)],
    [('D5', 0, 1.5), ('C5', 1.5, .5), ('Bb4', 2, 1)],
    [('G4', 0, 1), ('A4', 1, .5), ('Bb4', 1.5, .5), ('C5', 2, 1)],
    [('A4', 0, 3)],
    [('C5', 0, 1), ('A4', 1, 1), ('F5', 2, 1)],
    [('D5', 0, 1.5), ('F5', 1.5, .5), ('D5', 2, 1)],
    [('C5', 0, 1), ('Bb4', 1, 1), ('G4', 2, 1)],
    [('F4', 0, 3)],
]
def theme_bar(i, t0, fn, beat=B, trans=0):
    for p, b, d in THEME[i % 8]: fn(t0 + b * beat, m(p) + trans, d * beat)

def uke_bar(t0, ch, vel=.5, bass=True, pan=-.25, gain=1.):
    root, tri = CH[ch]
    if bass: note('uke', 'ukulele', t0, m(root) + 12 if m(root) + 12 >= m('B2') else m(root) + 24, B * 1.2, vel * 1.1, pan, gain)
    for k in (1, 2):   # "pá-pá" da valsa, dedilhado
        for j, p in enumerate(tri): note('uke', 'ukulele', t0 + k * B + j * 0.018, p, B * 0.9, vel * (0.8 if k == 2 else 0.9), pan + 0.1 * j, gain)
def clar_bass(t0, ch, vel=.45, gain=1., stac=True):
    root = m(CH[ch][0]) + 12
    while root < m('D3'): root += 12
    note('clarinet', 'clarinet_stac' if stac else 'clarinet', t0, root, (.3 if stac else BAR * 0.95), vel, -.2, gain, **({} if stac else {'attack': .2, 'release': .5}))

# ===== A · vinheta (0–8.2): caixinha de música, primeira frase do tema =====
for i in range(3): theme_bar(i, 0.25 + i * BAR, lambda t, p, d: mbox(t, p + 12, .6, .15))
mbox(0.25 + 3 * BAR, 'F5', .55, 0.); mbox(0.25 + 3 * BAR + 0.02, 'A5', .4, .2); mbox(0.25 + 3 * BAR + 0.04, 'C6', .35, -.2)
glock(4.8, 'C6', .35, .3)   # "A Criação"

# ===== B · escuridão (8.2–21.5): só um pedal grave e baixinho; depois silêncio =====
note('clarinet', 'clarinet', 9.6, 'F3', 8.6, .22, -.1, .7, attack=1.5, release=1.2)
note('recorder', 'recorder', 17.0, 'C5', 1.6, .18, .2, .5, attack=.4, release=.6)   # o pontinho de luz
# silêncio de 18.8 a 21.5 (o primeiro som depois dele é a luz)

# ===== C · Dias 1–4 (21.5–54.4): a luz, depois a valsa do ukulele =====
t = cue['C']
for i, p in enumerate(['F5', 'A5', 'C6', 'F6', 'A6']): glock(t + i * 0.06, p, .65 - i * 0.05, -.4 + i * .2, 1.2)
mbox(t, 'F6', .7, 0, 1.0)
note('recorder', 'recorder', t + 0.1, 'F5', BAR * 1.5, .35, .1, .8, attack=.1, release=.8)
t0 = t + BAR; nb = int((cue['D'] - t0) / BAR)
for b in range(nb):
    tb = t0 + b * BAR; ch = PROG[b % 8]
    uke_bar(tb, ch, .42 if b < 2 else .5)
    if b % 2 == 0: clar_bass(tb, ch, .3, .8, stac=False)
    if b % 8 in (3, 7): glock(tb + B, 'C6' if b % 8 == 3 else 'F6', .35, .3)
# acentos: céu, mar, terra, árvores, sol
for tt, p in [(29.8, 'A5'), (34.4, 'C6'), (39.2, 'F5'), (43.9, 'A5'), (45.1, 'C6'), (46.3, 'F6'), (49.6, 'C6')]: glock(tt, p, .4, .2)
note('clarinet', 'clarinet', 53.0, 'C4', 1.4, .35, -.1, .9, attack=.05, release=.5)   # o sol se põe (descida)
note('clarinet', 'clarinet', 53.6, 'A3', 0.9, .3, -.1, .9, release=.6)

# ===== D · a noite (54.4–60.3): o ukulele para; um "plim" por estrela; caixinha bem baixinho =====
t = cue['D']
note('recorder', 'recorder', t, 'A4', BAR * 2.6, .2, .1, .55, attack=.6, release=1.0)
note('clarinet', 'clarinet', t, 'F3', BAR * 2.8, .2, -.2, .6, attack=.8, release=1.2)
pent = ['C6', 'D6', 'F6', 'G6', 'A6', 'C7']
gl = [e for e in EV if e['type'] == 'glint']
for k, e in enumerate(gl): glock(e['t'], pent[k % len(pent)], .22 + 0.08 * ((k * 7) % 3), e.get('pan', 0) * .7, .55)
for i in range(2): theme_bar(i, t + BAR * 0.5 + i * BAR, lambda tt, p, d: mbox(tt, p + 12, .35, .2, .6))

# ===== E · Dias 5–6 (60.3–76.4): manhã; ukulele de novo, woodblock, clarinete com humor =====
t = cue['E']
glock(t, 'F6', .45, 0); glock(t + 0.07, 'C6', .35, .2)
nb = int((cue['F'] - t) / BAR)
for b in range(nb):
    tb = t + b * BAR; ch = PROG[b % 8]
    uke_bar(tb, ch, .5)
    if b >= 1: wood(tb, 'a', .32, -.4); wood(tb + B, 'b', .2, .4); wood(tb + 2 * B, 'b', .2, .4)
    if b >= 4: clar_bass(tb, ch, .4, .9)
    if b in (1, 2, 3): theme_bar(b - 1 + 4, tb, lambda tt, p, d: note('recorder', 'recorder', tt, p, d, .32, .2, .7, release=.3))
# bichos: leão e elefante no clarinete (humor), coelho no woodblock
ani = {e['type']: e['t'] for e in EV if e['type'] in ('sheep', 'rabbit', 'lion', 'elephant')}
note('clarinet', 'clarinet', ani['lion'], 'D3', .5, .55, -.1, 1.0, release=.3)
note('clarinet', 'clarinet', ani['elephant'], 'F3', .25, .5, 0, 1.0, release=.2); note('clarinet', 'clarinet', ani['elephant'] + .28, 'C4', .5, .55, 0, 1.0, release=.4)
for e in EV:
    if e['type'] == 'hop': wood(e['t'], 'c', .45, .2)
    if e['type'] == 'tweet': note('recorder', 'recorder', e['t'], 'C6', .12, .35, e['pan'], .6); note('recorder', 'recorder', e['t'] + .14, 'E6', .12, .35, e['pan'], .6)
    if e['type'] == 'splash': glock(e['t'], 'G6', .35, .4)

# ===== F · Adão e Eva (76.4–88.2): o tema INTEIRO, uma vez, na flauta doce =====
t = cue['F']
for b in range(8):
    tb = t + b * BAR
    uke_bar(tb, PROG[b], .45)
    theme_bar(b, tb, lambda tt, p, d: note('recorder', 'recorder', tt, p, d * 0.95, .45, .15, 1.0, release=.4))
    if b % 2 == 0: clar_bass(tb, PROG[b], .3, .8, stac=False)
for e in EV:
    if e['type'] == 'heart': glock(e['t'], 'A6', .5, 0); glock(e['t'] + .12, 'F6', .4, .1)
    if e['type'] == 'hands': glock(e['t'], 'C6', .35, 0)

# ===== G · Dia 7 (88.2–98.2): a caixinha sozinha, desacelerando (corda acabando) =====
t = cue['G']; tt = t
for b in range(5):
    beat = B * (1 + 0.12 * b)          # ritardando
    theme_bar(b, tt, lambda x, p, d, b=b: mbox(x, p + 12, .5 - .05 * b, .1, 1.0, bend=-0.15 * b * b))
    tt += 3 * beat
note('clarinet', 'clarinet', t, 'F3', 9.0, .18, -.2, .6, attack=1.0, release=1.5)

# ===== H · lição (98.2–113.6): ukulele suave; silêncio antes do "Você!" =====
t = cue['H']
sil = next(e for e in EV if e['type'] == 'silence'); s0, s1 = sil['t'], sil['t'] + sil['dur']
b = 0
while t + b * BAR < cue['I'] - 0.5:
    tb = t + b * BAR
    if not (s0 - BAR < tb < s1): uke_bar(tb, PROG[b % 8], .38)
    b += 1
voce = next(e['t'] for e in EV if e['type'] == 'voice' and e['id'] == 'l3')
for i, p in enumerate(['F5', 'A5', 'C6', 'F6']): glock(voce + 0.8 + i * 0.07, p, .55, -.3 + i * .2)
mbox(voce + 0.8, 'F6', .6, 0)
note('recorder', 'recorder', voce + 0.3, 'A5', BAR * 1.2, .35, .1, .8, release=.6)

# ===== I · final (113.6–fim): conjunto inteiro, acorde que resolve, caixinha até o fim =====
t = cue['I']
for b in range(5):
    tb = t + b * BAR; ch = PROG[b % 8]
    uke_bar(tb, ch, .5)
    wood(tb, 'a', .3, -.4)
    theme_bar(b + 4, tb, lambda tt, p, d: note('recorder', 'recorder', tt, p, d * .95, .4, .15, .9, release=.4))
tr = t + 5 * BAR
for p in ['F3', 'A3', 'C4', 'F4', 'A4']: note('uke', 'ukulele', tr + 0.03 * ['F3', 'A3', 'C4', 'F4', 'A4'].index(p), p, 3.0, .5, -.1, 1.0)
note('recorder', 'recorder', tr, 'F5', BAR * 2, .4, .15, .9, release=1.0)
for i, p in enumerate(['F5', 'A5', 'C6', 'F6']): glock(tr + i * .06, p, .45, -.3 + i * .2)
tt = tr + 2 * BAR
while tt < DUR - 2 * BAR:
    for i in range(4): theme_bar(i, tt + i * BAR, lambda x, p, d: mbox(x, p + 12, .3, .15, .7))
    tt += 4 * BAR

os.makedirs(os.path.join(HERE, 'stems'), exist_ok=True)
fade = np.clip((DUR - np.arange(N) / SR) / 3.0, 0, 1)[:, None]
mix = np.zeros((N, 2), np.float32)
for k, x in stems.items():
    x = x * fade; sf.write(os.path.join(HERE, 'stems', k + '.wav'), x, SR); mix += x
pk = np.abs(mix).max(); mix = mix / pk * 0.8 if pk > 0.8 else mix
sf.write(os.path.join(HERE, 'score.wav'), mix, SR)
print('score.wav', DUR, 's  peak', round(float(pk), 3), ' stems:', ', '.join(stems))
