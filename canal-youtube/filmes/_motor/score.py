"""Trilha original gerada a partir do clima de cada cena (music.json) e da linha do tempo (events.json).
Valsa em 3/4 com ukulele, flauta doce, clarinete, glockenspiel, caixinha de música e woodblock (bibliotecas CC0).
music.json: {"key": "F", "bpm": 88, "moods": {"gancho": "wonder", "s1": "sad", ...}}
Climas: wonder · happy · calm · sad · tense · storm · triumph · lesson. Uso: $LIB/.venv/bin/python score.py
"""
import sys, os, json
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', '/home/user/lemomo-ai/lemo-opuscar'); sys.path.insert(0, LIB)
from core.audio import sampler as S, pluck as P
from core.audio.sfx import SR, add
cfg = json.load(open(os.path.join(HERE, 'music.json')))
E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']; N = int(DUR * SR)
S.seed(cfg.get('seed', 7))
NOTE = {'C': 60, 'D': 62, 'E': 64, 'F': 65, 'G': 67, 'A': 69, 'Bb': 70}
TON = NOTE[cfg.get('key', 'F')]               # tônica da melodia (oitava 4)
if TON > 67: TON -= 12
B = 60 / cfg.get('bpm', 88); BAR = 3 * B
stems = {k: np.zeros((N, 2), np.float32) for k in ['uke', 'glock', 'recorder', 'clarinet', 'mbox', 'perc']}
def note(st, inst, t, p, d, vel=.6, pan=0., gain=1., **kw):
    if 0 <= t < DUR - 0.05: add(stems[st], S.note(inst, p, d, vel, **kw), t, gain, pan)
def mbox(t, p, vel=.5, pan=.1, gain=1.):
    if 0 <= t < DUR - 0.05: add(stems['mbox'], P.pluck('music_box', p, None, vel), t, gain, pan)
def glock(t, p, vel=.45, pan=0., gain=1.):
    while p < 79: p += 12
    while p > 96: p -= 12
    note('glock', 'glockenspiel', t, p, 1.6, vel, pan, gain, release=1.2)
def wood(t, var='a', vel=.3, pan=-.3):
    if 0 <= t < DUR - 0.05: add(stems['perc'], S.hit('woodblock', var, vel), t, 1.0, pan)
CH = {'I': [0, 4, 7], 'IV': [5, 9, 12], 'V': [7, 11, 14], 'vi': [9, 12, 16], 'ii': [2, 5, 9]}
PROG = ['I', 'IV', 'V', 'I', 'vi', 'IV', 'V', 'I']
THEME = [[(7, 0, 1), (4, 1, 1), (0, 2, 1)], [(9, 0, 1.5), (7, 1.5, .5), (5, 2, 1)], [(2, 0, 1), (4, 1, .5), (5, 1.5, .5), (7, 2, 1)], [(4, 0, 3)],
         [(0, 0, 1), (4, 1, 1), (9, 2, 1)], [(9, 0, 1.5), (12, 1.5, .5), (9, 2, 1)], [(7, 0, 1), (5, 1, 1), (2, 2, 1)], [(0, 0, 3)]]
REC = TON if TON >= 65 else TON + 12      # flauta doce: F4–E6
def theme_bar(i, t0, fn, beat=B, base=TON):
    for p, b, d in THEME[i % 8]: fn(t0 + b * beat, base + p, d * beat)
def uke_bar(t0, ch, vel=.45, beat=B, stac=False):
    root = TON - 12 + CH[ch][0]
    while root < 47: root += 12
    note('uke', 'ukulele', t0, root, beat * 1.2, vel * 1.1, -.25)
    for k in (1, 2):
        for j, p in enumerate(CH[ch]): note('uke', 'ukulele', t0 + k * beat + j * .018, TON - 12 + p + (12 if TON - 12 + p < 55 else 0), beat * (0.35 if stac else 0.9), vel * (0.8 if k == 2 else 0.9), -.15 + .1 * j)
def clar(t0, p, d, vel=.3, stac=False, gain=.9):
    while p < 50: p += 12
    note('clarinet', 'clarinet_stac' if stac else 'clarinet', t0, p, d, vel, -.2, gain, **({} if stac else {'attack': .2, 'release': .6}))
def rec(t0, p, d, vel=.32, gain=.8):
    while p < 65: p += 12
    note('recorder', 'recorder', t0, p, d, vel, .15, gain, release=.4)

def section(mood, t0, t1):
    nb = max(1, int((t1 - t0 - 0.3) / BAR))
    for b in range(nb):
        tb = t0 + 0.3 + b * BAR; ch = PROG[b % 8]
        if mood == 'happy':
            uke_bar(tb, ch, .48); wood(tb, 'a', .28, -.4); wood(tb + B, 'b', .17, .4); wood(tb + 2 * B, 'b', .17, .4)
            if b % 4 in (1, 2): theme_bar(b, tb, lambda t, p, d: rec(t, p - TON + REC, d * .95))
        elif mood == 'calm':
            uke_bar(tb, ch, .36)
            if b % 4 == 1: theme_bar(b, tb, lambda t, p, d: rec(t, p - TON + REC, d * .95, .26))
        elif mood == 'lesson':
            uke_bar(tb, ch, .34)
        elif mood == 'wonder':
            theme_bar(b, tb, lambda t, p, d: mbox(t, p + 12, .42, .15))
            if b % 2 == 0: clar(tb, TON - 12 + CH[ch][0], BAR * 1.9, .2)
            if b % 2 == 1: glock(tb + 2 * B, TON + 24 + CH[ch][2], .3, .3)
        elif mood == 'sad':
            clar(tb, TON - 12 + CH[['vi', 'IV', 'ii', 'V'][b % 4]][0], BAR * .95, .28)
            if b % 2 == 0: note('uke', 'ukulele', tb + B, TON + CH[['vi', 'IV', 'ii', 'V'][b % 4]][1], B * 2, .25, .1)
        elif mood == 'tense':
            note('uke', 'ukulele', tb, TON - 12 + [7, 6, 5, 4][b % 4], .25, .4, -.2); note('uke', 'ukulele', tb + B, TON + 2, .2, .3, .1); note('uke', 'ukulele', tb + 2 * B, TON + 2, .2, .3, .1)
            if b % 2: clar(tb, TON + [2, 1, 0, -1][(b // 2) % 4], B * .9, .33, True); clar(tb + B, TON + [1, 0, -1, -2][(b // 2) % 4], B * .9, .28, True)
        elif mood == 'storm':
            if b % 2 == 0: clar(tb, TON - 12, BAR * 2, .26)
            for k in range(6): wood(tb + k * B / 2, 'c', .1 + .05 * (k % 2), -.6 + k * .2)
        elif mood == 'triumph':
            uke_bar(tb, ch, .52); wood(tb, 'a', .3, -.4)
            theme_bar(b, tb, lambda t, p, d: rec(t, p - TON + REC, d * .95, .4, 1.0))
            if b % 2 == 0: clar(tb, TON - 12 + CH[ch][0], BAR * .95, .3)
            if b % 4 == 3: [glock(tb + i * .07, TON + 24 + q, .4, -.3 + i * .2) for i, q in enumerate([0, 4, 7, 12])]

cues = [e for e in EV if e['type'] == 'cue']
moods = cfg.get('moods', {})
for i, c in enumerate(cues):
    t0 = c['t']; t1 = cues[i + 1]['t'] if i + 1 < len(cues) else DUR
    if c['id'] == 'titulo':
        for k in range(3): theme_bar(k, 0.25 + k * BAR, lambda t, p, d: mbox(t, p + 12, .55, .15))
        glock(3.4, TON + 24, .35, .3)
    elif c['id'] == 'fim':
        for b in range(4):
            tb = t0 + b * BAR; uke_bar(tb, PROG[b + 4], .48); wood(tb, 'a', .28, -.4); theme_bar(b + 4, tb, lambda t, p, d: rec(t, p - TON + REC, d * .95, .36))
        tr = t0 + 4 * BAR
        for k, p in enumerate([-12, -8, -5, 0, 4]): note('uke', 'ukulele', tr + .03 * k, TON + p if TON + p >= 47 else TON + p + 12, 3.0, .5, -.1)
        rec(tr, REC + 12 if REC < 70 else REC, BAR * 2, .38, .9)
        for k, q in enumerate([0, 4, 7, 12]): glock(tr + k * .06, TON + 24 + q, .4, -.3 + k * .2)
        tt = tr + 2 * BAR
        while tt < DUR - 2 * BAR:
            for k in range(4): theme_bar(k, tt + k * BAR, lambda t, p, d: mbox(t, p + 12, .28, .15, .7))
            tt += 4 * BAR
    else:
        section(moods.get(c['id'], 'calm'), t0, t1)
for e in EV:   # acentos musicais ligados a ações
    if e['type'] in ('glint', 'heart'): glock(e['t'], TON + 24 + 7, .42, e.get('pan', 0))
    if e['type'] == 'shimmer': [glock(e['t'] + k * .12, TON + 24 + q, .38, -.4 + k * .16) for k, q in enumerate([0, 4, 7, 12, 16, 19])]
os.makedirs(os.path.join(HERE, 'music', 'stems'), exist_ok=True)
fade = np.clip((DUR - np.arange(N) / SR) / 3.0, 0, 1)[:, None]
mix = np.zeros((N, 2), np.float32)
for k, x in stems.items(): x = x * fade; sf.write(os.path.join(HERE, 'music', 'stems', k + '.wav'), x, SR); mix += x
pk = np.abs(mix).max(); print('trilha', DUR, 's  pico', round(float(pk), 3))
