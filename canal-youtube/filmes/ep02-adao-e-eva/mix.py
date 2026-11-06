# Mixagem: trilha (music/stems) + foley de material (giz no papel, pincel molhado, páginas) + bichos + ambientes + narração → mix.wav
# Funções de foley e a cadeia de voz adaptadas do demo crayon-book do Lemo-Opuscar (MIT).
# Uso: $LIB/.venv/bin/python mix.py
import sys, os, json, numpy as np, soundfile as sf, soxr
from scipy.ndimage import uniform_filter1d
from scipy.signal import fftconvolve, sosfilt as _sosfilt
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB', '/home/user/lemomo-ai/lemo-opuscar')
sys.path.insert(0, os.path.join(LIB, 'core/audio'))
from sfx import *

VLANG = os.environ.get('VLANG', 'pt'); VDIR = 'voices' if VLANG == 'pt' else 'voices_' + VLANG   # idioma da narração
E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']; N = int(DUR * SR)
tt = np.arange(N) / SR
rng = np.random.default_rng(12)
def nz(d): return rng.standard_normal(int(round(d * SR)))
def T(d): return np.arange(int(round(d * SR))) / SR
def fade(x, a=.01, b=.03):
    n = len(x); ia, ib = min(n, int(a * SR)), min(n, int(b * SR))
    if ia: x[:ia] *= np.linspace(0, 1, ia)
    if ib: x[-ib:] *= np.linspace(1, 0, ib)
    return x
def envelope(d, pts):
    k = np.array(pts, float); return np.interp(T(d), k[:, 0] * d, k[:, 1])

# ——— giz no papel: atrito "gruda-solta" = ruído filtrado × grão irregular ———
def crayon(d, speed=1.0, v=1.0):
    n = nz(d)
    rate = int(SR / (70 + 90 * speed))
    grain = uniform_filter1d((rng.random(len(n) // rate + 2) ** 3).repeat(rate)[:len(n)], rate // 3 + 1)
    x = bp(n, 1400 + 600 * speed, 6500, 2) * (0.35 + grain * 1.6) + bp(n, 300, 900, 1) * 0.15
    return fade(x * envelope(d, [(0, 0), (.08, 1), (.85, .9), (1, 0)]) * v * 0.22, .01, .04)
def scribble(d, rate=6.5, v=1.0):
    out = np.zeros(int(d * SR)); t = 0.0
    while t < d - 0.08:
        L = 1 / rate * (0.8 + 0.4 * rng.random()); s = crayon(min(L, d - t), 1.3, v * (0.7 + 0.3 * rng.random()))
        i = int(t * SR); out[i:i + len(s)] += s[:len(out) - i]; t += L
    return out
def write(d, v=1.0):
    out = np.zeros(int(d * SR)); t = 0.0
    while t < d - 0.1:
        L = 0.07 + 0.1 * rng.random(); s = crayon(L, 0.8, v); i = int(t * SR); out[i:i + len(s)] += s[:len(out) - i]; t += L + 0.03 * rng.random()
    return out
def paper_rustle(d=0.6, v=1.0):
    n = nz(d); cr = (rng.random(len(n)) < 0.004) * rng.standard_normal(len(n)) * 3
    return fade((hp(n, 900) * 0.25 + bp(cr, 1500, 8000)) * envelope(d, [(0, 0), (.2, 1), (1, 0)]) * v * 0.25)
def page_turn(d=1.2, v=1.0):
    out = np.zeros(int((d + 0.4) * SR))
    lift = hp(nz(0.35), 700) * envelope(0.35, [(0, 0), (.5, .6), (1, .2)]) * 0.18
    wh = bp(nz(0.6), 300, 4000) * np.sin(np.linspace(0, np.pi, int(0.6 * SR))) ** 1.5 * 0.35
    cr = (rng.random(int(0.6 * SR)) < 0.003) * rng.standard_normal(int(0.6 * SR)) * 2.5
    ft = T(0.25); flap = (lp(nz(0.25), 1500) * np.exp(-ft / 0.03) * 0.6 + np.sin(2 * np.pi * 90 * ft) * np.exp(-ft / 0.05) * 0.3)
    for x, at in [(lift, 0.0), (wh + bp(cr, 2000, 9000), 0.25), (flap, d - 0.1)]:
        i = int(at * SR); out[i:i + len(x)] += x[:len(out) - i]
    return out * v
def brush(d, v=1.0):
    n = nz(d); wet = lp(n, 1800) * 0.5 + bp(n, 1800, 5000) * 0.18
    grain = uniform_filter1d(np.abs(rng.standard_normal(len(n))), 400) * 0.6 + 0.7
    return fade(wet * grain * envelope(d, [(0, 0), (.06, .9), (.3, 1), (.8, .85), (1, 0)]) * 0.22 * v, .03, .1)
def plip(v=1.0):
    t = T(0.25); x = np.sin(2 * np.pi * np.cumsum(900 + 1400 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.05)
    return fade(x * 0.25 * v + bp(nz(0.25), 2000, 7000) * np.exp(-t / 0.02) * 0.08 * v)
def swell(d, f0, f1, v=1.0):   # sopro grave que sobe/desce (terra subindo, sol se pondo, luz apagando): duas cores de ruído cruzadas
    n = nz(d); u = np.linspace(0, 1, len(n))
    a_, b_ = bp(n, max(50, f0 * 0.6), f0 * 1.6, 1), bp(n, max(50, f1 * 0.6), f1 * 1.6, 1)
    a_ /= np.sqrt(np.mean(a_ ** 2)) + 1e-9; b_ /= np.sqrt(np.mean(b_ ** 2)) + 1e-9
    out = a_ * np.cos(u * np.pi / 2) + b_ * np.sin(u * np.pi / 2)
    return fade(out * envelope(d, [(0, 0), (.3, 1), (.75, .8), (1, 0)]) * 0.05 * v, .05, .2)
def felt(v=1.0):
    t = T(0.22); return fade((np.sin(2 * np.pi * 105 * t) * np.exp(-t / 0.05) * 0.7 + lp(nz(0.22), 600) * np.exp(-t / 0.03) * 0.5) * v * 0.45)
def baa(v=1.0, f0=430):
    d = 0.5; t = T(d); f = f0 * (1 + 0.02 * np.sin(2 * np.pi * 7 * t)) * (1 - 0.08 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR; saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    x = bp(saw, 600, 1100) + bp(saw, 1900, 2600) * 0.5
    return fade(x * (1 + 0.5 * np.sin(2 * np.pi * 18 * t)) * envelope(d, [(0, 0), (.1, 1), (.7, .8), (1, 0)]) * 0.12 * v, .02, .08)
def growl(v=1.0):   # "rrr" fofo do leão
    d = 0.7; t = T(d); f = 95 * (1 + 0.15 * np.sin(2 * np.pi * 3 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR; saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    x = lp(saw, 900) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 22 * t))) + lp(nz(d), 500) * 0.3
    return fade(x * envelope(d, [(0, 0), (.15, 1), (.7, .7), (1, 0)]) * 0.25 * v, .03, .15)
def toot(v=1.0):    # trombinha do elefante
    d = 0.6; t = T(d); f = 380 * (1 + 0.5 * np.clip(t / 0.15, 0, 1)) * (1 - 0.15 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR; sq = np.sign(np.sin(ph)) * 0.5 + 2 * ((ph / (2 * np.pi)) % 1) - 1
    x = bp(sq, 300, 2500) * (1 + 0.3 * np.sin(2 * np.pi * 9 * t))
    return fade(x * envelope(d, [(0, 0), (.05, 1), (.8, .8), (1, 0)]) * 0.12 * v, .01, .1)
def squeak(v=1.0):  # coelhinho
    t = T(0.12); return fade(np.sin(2 * np.pi * np.cumsum(2200 + 900 * np.sin(np.pi * t / 0.12)) / SR) * np.exp(-t / 0.06) * 0.08 * v)
def tweet(v=1.0):
    out = np.zeros(int(0.5 * SR))
    for k in range(3):
        t = T(0.07); x = np.sin(2 * np.pi * np.cumsum(3200 + 1600 * (1 - t / 0.07)) / SR) * np.sin(np.pi * t / 0.07)
        i = int(k * 0.11 * SR); out[i:i + len(x)] += x
    return out * 0.06 * v
def bubble(v=1.0):
    out = np.zeros(int(0.6 * SR))
    for k in range(4):
        t = T(0.06); f0 = 500 + 400 * rng.random(); x = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * t / 0.06)) / SR) * np.exp(-t / 0.02)
        i = int(k * 0.12 * SR + rng.random() * 0.04 * SR); out[i:i + len(x)] += x
    return out * 0.12 * v
def splash(v=1.0, small=False):
    d = 0.5 if small else 0.8; n = nz(d); t = T(d)
    return fade((bp(n, 500, 6000) * np.exp(-t / (0.08 if small else 0.15)) + bp(n, 2000, 9000) * 0.3 * np.exp(-t / 0.04)) * 0.3 * v, .003, .1)
def pat(v=1.0):
    t = T(0.12); return fade(lp(nz(0.12), 500) * np.exp(-t / 0.025) * 0.5 * v + np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.03) * 0.2 * v)
def popfx(v=1.0):   # flor brotando
    t = T(0.08); return fade(np.sin(2 * np.pi * np.cumsum(700 + 1500 * t / 0.08) / SR) * np.exp(-t / 0.025) * 0.12 * v)
def tick(v=1.0, hi=True):
    t = T(0.04); return fade(bp(nz(0.04), 2500 if hi else 1800, 7000) * np.exp(-t / 0.006) * 0.12 * v, .0005, .01)
def cricket(d=1.2, v=1.0):
    out = np.zeros(int(d * SR)); t = 0
    while t < d - 0.1:
        for k in range(3):
            tc = T(0.018); c = np.sin(2 * np.pi * 4700 * tc) * np.sin(np.pi * tc / 0.018)
            i = int((t + k * 0.026) * SR); out[i:i + len(c)] += c[:len(out) - i]
        t += 0.32 + 0.1 * rng.random()
    return out * 0.05 * v
def birdsong(d, v=1.0):
    out = np.zeros(int(d * SR)); t = 0.3
    while t < d - 0.6:
        x = tweet(0.5 + 0.5 * rng.random()); i = int(t * SR); out[i:i + len(x)] += x[:len(out) - i]; t += 1.2 + 1.8 * rng.random()
    return out * v

buf = np.zeros((N, 2)); amb = np.zeros((N, 2))
def put(x, at, g=1.0, pan=0.0, b=None): add(buf if b is None else b, np.asarray(x, np.float64), at, g, pan)

def hiss(v=1.0):   # "sss" suave da serpente
    d = 0.7; n = nz(d); return fade(bp(n, 4500, 9000) * envelope(d, [(0, 0), (.2, 1), (.7, .7), (1, 0)]) * 0.05 * v, .03, .2)
def crunch(v=1.0):  # mordida crocante, baixinha
    out = np.zeros(int(0.25 * SR))
    for k in range(5):
        t = T(0.02); x = bp(nz(0.02), 1500, 7000) * np.exp(-t / 0.004); i = int((k * 0.035 + rng.random() * 0.01) * SR); out[i:i + len(x)] += x
    return out * 0.35 * v
def grass_step(v=1.0):
    t = T(0.12); return fade((bp(nz(0.12), 800, 5000) * np.exp(-t / 0.03) * 0.5 + lp(nz(0.12), 300) * np.exp(-t / 0.02) * 0.4) * 0.25 * v)
def rustle(d=0.8, v=1.0):   # folhas do arbusto
    n = nz(d); cr = (rng.random(len(n)) < 0.01) * rng.standard_normal(len(n)) * 2
    return fade((bp(n, 1200, 6000) * 0.4 + bp(cr, 2000, 8000)) * envelope(d, [(0, 0), (.2, 1), (.8, .8), (1, 0)]) * 0.12 * v)
def stream(d, v=1.0):   # água do rio
    n = nz(d); x = bp(n, 400, 3000) * (0.6 + 0.4 * uniform_filter1d(np.abs(rng.standard_normal(len(n))), 800))
    return x * 0.015 * v

for e in EV:
    t, ty, pan = e['t'], e['type'], e.get('pan', 0.0)
    if ty == 'scratch': put(crayon(e['dur'], 1.1), t, 1.0, pan)
    elif ty == 'write': put(write(e['dur']), t, 0.9, pan)
    elif ty == 'scribble': put(scribble(e['dur']), t, 0.75, pan)
    elif ty == 'paper': put(paper_rustle(0.8), t, 0.8)
    elif ty == 'page': put(page_turn(e['dur']), t, 0.16, -0.1)
    elif ty == 'pop': put(popfx(), t, 1.0, pan)
    elif ty == 'water': put(stream(e['dur'], 3.0), t, 1.0, 0.6)
    elif ty == 'sheep': put(baa(1.0, 430), t, 1.0, -0.5)
    elif ty == 'rabbit': put(squeak(), t, 1.0, -0.3)
    elif ty == 'lion': put(growl(), t, 1.0, 0.2)
    elif ty == 'giraffe': put(popfx(0.8), t, 1.0, 0.4)
    elif ty == 'turtle': put(felt(0.5), t, 1.0, 0.6)
    elif ty == 'hiss': put(hiss(), t, 1.0, pan)
    elif ty == 'reach': put(swell(0.4, 600, 1500, 0.4), t, 1.0)
    elif ty == 'bite': put(crunch(), t, 1.0, pan)
    elif ty == 'hide': put(rustle(e['dur']), t, 1.0, 0.3)
    elif ty == 'step': put(grass_step(0.8), t, 1.0, pan)
    elif ty == 'brush':
        d = e['dur'] + 0.25; x = brush(d); p0, p1 = (-0.85, 0.85) if e['dir'] > 0 else (0.85, -0.85)
        L = len(x); s = int(t * SR); pn = np.linspace(p0, p1, L)
        l, r = np.cos((pn + 1) * np.pi / 4) * 1.414, np.sin((pn + 1) * np.pi / 4) * 1.414
        e2 = min(N, s + L); buf[s:e2, 0] += (x * l)[:e2 - s]; buf[s:e2, 1] += (x * r)[:e2 - s]
    elif ty == 'dip': put(plip(), t, 0.9, 0.5)
    elif ty == 'reveal': put(swell(1.2, 400, 2400, 0.5), t - 0.3, 1.0)
    elif ty == 'ray': put(swell(e['dur'], 300, 1800, 0.35), t, 1.0)
    elif ty == 'fence': [put(crayon(0.14, 1.5), t + k * 0.22, 0.8, -0.4 + k * 0.07) for k in range(12)]
    elif ty == 'heart': put(pat(0.4), t, 1.0)
    elif ty == 'room':
        d = DUR - t; x = lp(brown(d), 400) * 0.02 * envelope(d, [(0, 0), (.08, 1), (1, 1)])
        add(amb, x, t, 1.0, 0.0)
        k = 0; tc = t + 0.3
        while tc < DUR - 0.2: add(amb, tick(0.8, k % 2 == 0), tc, 1.0, 0.5); tc += 1.0; k += 1

# ambientes: passarinhos e o rio no jardim (até o entardecer); grilos no entardecer e na lição; ar de papel
bs = birdsong(67.0, 0.45); i = int(14.0 * SR); L_ = min(len(bs), N - i)
fadeb = np.interp(np.arange(L_) / SR, [0, 1, 64, 67], [0, 1, 1, 0])
amb[i:i + L_, 0] += bs[:L_] * fadeb; amb[i:i + L_, 1] += np.roll(bs[:L_], 1500) * fadeb
rv = stream(DUR, 1.0) * np.interp(tt, [15.4, 17, 80, 84, 121, 122], [0, 1, 1, 0.5, 0.5, 0])
amb[:, 0] += rv * 0.7; amb[:, 1] += np.roll(rv, 700)
nb = np.zeros(N)
for t0 in np.arange(82.0, 121.0, 1.7): x = cricket(1.2, 0.35); i = int(t0 * SR); nb[i:i + len(x)] += x[:N - i]
amb[:, 0] += nb; amb[:, 1] += np.roll(nb, 900)
air = hp(nz(DUR), 3000) * 0.0025
amb[:, 0] += air; amb[:, 1] += np.roll(air, 2000)

# ——— narração: Kokoro pf_dora, 24k → 48k; comprime primeiro, EQ quente, de-esser, nível por RMS, reverb curta e quente ———
def biquad(x, kind, f0, gain_db, q=0.707):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; cw, sw = np.cos(w), np.sin(w); al = sw / (2 * q)
    if kind == 'peak': b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
    else:
        s2 = 2 * np.sqrt(A) * al; sg = 1 if kind == 'high' else -1
        b = [A * ((A + 1) + sg * (A - 1) * cw + s2), -2 * sg * A * ((A - 1) + sg * (A + 1) * cw), A * ((A + 1) + sg * (A - 1) * cw - s2)]
        a = [(A + 1) - sg * (A - 1) * cw + s2, 2 * sg * ((A - 1) - sg * (A + 1) * cw), (A + 1) - sg * (A - 1) * cw - s2]
    return _sosfilt(np.array([b + a]) / a[0], x)
def deess(x, lo=4800, hi=10000, thr_rel=0.5, ratio=4.0):
    band = bp(x, lo, hi, 2)
    eb = uniform_filter1d(np.abs(band), int(0.004 * SR)); ef = uniform_filter1d(np.abs(x), int(0.004 * SR))
    over = eb / (ef * thr_rel + 1e-9); g = np.where(over > 1, over ** (1 / ratio - 1), 1.0); g = uniform_filter1d(g, int(0.003 * SR))
    return x - band + band * g
VO_RMS = 10 ** (-21.0 / 20)
vo = np.zeros((N, 2)); vmask = np.zeros(N)
for e in [x for x in EV if x['type'] == 'voice']:
    a, sr = sf.read(os.path.join(HERE, VDIR, e['id'] + '.wav'))
    if a.ndim > 1: a = a.mean(1)
    a = soxr.resample(a, sr, SR); a = hp(a, 75)
    a = compress(a / (np.abs(a).max() + 1e-9) * 0.8, thr=.2, ratio=2.5, att=.008, rel=.14)
    a = biquad(a, 'low', 220, 1.5); a = biquad(a, 'peak', 3200, -2.0, 1.0); a = biquad(a, 'high', 6000, -3.0)
    a = deess(a)
    act = np.abs(a) > np.abs(a).max() * 0.05
    a = a * VO_RMS / (np.sqrt(np.mean(a[act] ** 2)) + 1e-9)
    add(vo, a, e['t'], 1.0, 0.0); s = int(e['t'] * SR); vmask[s:s + len(a)] = 1
def warm_ir(seed):
    r = np.random.default_rng(seed); L = int(0.9 * SR); ir = np.zeros(L); pd = int(0.012 * SR)
    for ms, g in [(7, .5), (11, .38), (17, .3), (23, .22), (31, .16)]: ir[pd + int((ms + r.uniform(-1, 1)) * SR / 1000)] += g * r.choice([-1, 1])
    t_ = np.arange(L - pd) / SR; tail = r.standard_normal(L - pd) * np.exp(-t_ / 0.11) * np.clip(t_ / 0.02, 0, 1) * 0.35
    ir[pd:] += lp(tail, 3200); return lp(ir, 5000)
dry = vo.copy()
for c in range(2):
    wet = fftconvolve(dry[:, c], warm_ir(31 + c), 'full')[:N]
    vo[:, c] += wet * (10 ** (-17 / 20)) / (np.sqrt(np.mean(wet ** 2)) / (np.sqrt(np.mean(dry[:, c] ** 2)) + 1e-12) + 1e-12)

# ——— trilha ———
SG = {'uke': 1.0, 'glock': 1.35, 'recorder': 0.9, 'clarinet': 1.0, 'mbox': 1.45, 'perc': 0.8}
mus = np.zeros((N, 2))
for k, g in SG.items():
    m_, msr = sf.read(os.path.join(HERE, 'music', 'stems', k + '.wav'))
    if m_.ndim == 1: m_ = np.stack([m_, m_], 1)
    L = min(N, len(m_)); mus[:L] += m_[:L] * g
for c in range(2): mus[:, c] += bp(mus[:, c], 3000, 7000, 2) * 0.3   # brilho do metal (glock, caixinha)
duck = uniform_filter1d(vmask, int(0.25 * SR)); duck = np.clip(duck * 1.6, 0, 1)
mus *= (1 - duck * (1 - 10 ** (-12 / 20)))[:, None]
buf *= (1 - duck * (1 - 10 ** (-6 / 20)))[:, None]
# a valsa sobe um pouco sem fala (página 2, tema inteiro, final)
mus *= (10 ** (np.interp(tt, [0, 7, 7.6, 121.6, 122.6, 139], [2, 2, 0, 0, 2, 2]) / 20))[:, None]

mix = mus * 0.75 + buf + amb + vo
for c in range(2): mix[:, c] = limit(mix[:, c], .95)
sf.write(os.path.join(HERE, 'mix.wav' if VLANG == 'pt' else f'mix_{VLANG}.wav'), mix.astype(np.float32), SR)
def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
for name, x in [('music', mus), ('foley', buf), ('amb', amb), ('voice', vo), ('mix', mix)]: print(f'{name:6s} RMS {db(x):6.1f} dB  peak {20*np.log10(np.abs(x).max()+1e-9):6.1f}')
dur = json.load(open(os.path.join(HERE, VDIR, 'dur.json')))
worst = []
for e in [x for x in EV if x['type'] == 'voice']:
    s = int(e['t'] * SR); L = int(dur[e['id']] * SR)
    bed = mus[s:s + L] * 0.75 + buf[s:s + L] + amb[s:s + L]; worst.append((db(vo[s:s + L]) - db(bed), e['id']))
print('voz acima do fundo (dB): min %.1f (%s), mediana %.1f' % (min(worst)[0], min(worst)[1], sorted(worst)[len(worst) // 2][0]))
