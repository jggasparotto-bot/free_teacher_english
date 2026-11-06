"""Frequencia Lunar - night full-on psytrance, synthesized from scratch with numpy."""
import subprocess, tempfile, os, wave
import numpy as np
from scipy.signal import butter, sosfilt, oaconvolve

SR = 44100
BPM = 147
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(7)

# ---------------- arrangement (in bars) ----------------
SECTIONS = [("intro", 16), ("build1", 16), ("groove1", 24), ("breakdown", 16),
            ("build2", 8), ("drop", 32), ("outro", 16)]
START = {}
b = 0
for name, n in SECTIONS:
    START[name] = (b, b + n)
    b += n
TOTAL_BARS = b
N = int((TOTAL_BARS * BAR + 6) * SR)

L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
RV = np.zeros(N, np.float32)          # reverb send (mono)
DL = np.zeros(N, np.float32)          # ping-pong delay send (mono)


def pos(bar, beat=0.0):
    return int(round((bar * BAR + beat * BEAT) * SR))


def add(sig, start, gain=1.0, pan=0.0, rev=0.0, dly=0.0):
    if start >= N:
        return
    sig = sig[: N - start] * gain
    a = (pan + 1) * np.pi / 4
    L[start:start + len(sig)] += sig * np.cos(a)
    R[start:start + len(sig)] += sig * np.sin(a)
    if rev: RV[start:start + len(sig)] += sig * rev
    if dly: DL[start:start + len(sig)] += sig * dly


_sos = {}
def filt(x, cut, btype="low", order=2):
    key = (round(float(cut)) if np.ndim(cut) == 0 else tuple(round(float(c)) for c in cut), btype, order)
    if key not in _sos:
        c = np.clip(np.array(cut, float), 20, SR / 2 - 100)
        _sos[key] = butter(order, c, btype=btype, fs=SR, output="sos")
    return sosfilt(_sos[key], x)


def sweep(x, cut_start, cut_end, btype="low", chunk=2048):
    """Time-varying filter via overlap-add of windowed chunks."""
    out = np.zeros(len(x) + chunk)
    win = np.hanning(chunk)
    hop = chunk // 2
    n = max(1, (len(x) - chunk) // hop + 1)
    for i in range(n + 1):
        s = i * hop
        seg = x[s:s + chunk]
        if len(seg) == 0: break
        frac = s / max(1, len(x))
        c = cut_start * (cut_end / cut_start) ** frac
        if btype == "band":
            y = filt(seg, [c * 0.7, c * 1.4], "band")
        else:
            y = filt(seg, c, btype)
        out[s:s + len(y)] += y * win[:len(y)]
    return out[:len(x)]


def saw(freq, n):
    ph = np.cumsum(np.broadcast_to(freq, (n,)) / SR)
    return 2 * (ph % 1.0) - 1


def noise(n):
    return rng.uniform(-1, 1, n)


def t_(n):
    return np.arange(n) / SR


def note(name):
    names = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7,
             "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    p, o = name[:-1], int(name[-1])
    return 440 * 2 ** ((names[p] + 12 * (o + 1) - 69) / 12)

# ---------------- instruments ----------------
def kick():
    n = int(0.32 * SR); t = t_(n)
    f = 44 + 120 * np.exp(-t * 38)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    click = filt(noise(n), 2500, "high") * np.exp(-t * 500) * 0.35
    return np.tanh((s + click) * 1.8) * 0.95

KICK = kick()


def bass_note(f, cut_mult=1.0):
    n = int(S16 * SR * 0.92); t = t_(n)
    raw = saw(f, n) * 0.6 + saw(f * 1.006, n) * 0.4
    bright = filt(raw, 1100 * cut_mult)
    dark = filt(raw, 280 * cut_mult)
    fe = np.exp(-t * 45)
    s = bright * fe + dark * (1 - fe)
    env = np.minimum(1, t / 0.002) * np.exp(-t * 18)
    env[-80:] *= np.linspace(1, 0, 80)
    return np.tanh(s * env * 2.6) * 0.55

_hn = filt(noise(int(0.2 * SR)), 7500, "high", 4)
def hat(open_=True):
    n = int((0.11 if open_ else 0.03) * SR); t = t_(n)
    return _hn[:n] * np.exp(-t * (28 if open_ else 160))


def clap():
    n = int(0.25 * SR); t = t_(n)
    nz = filt(noise(n), [900, 4000], "band")
    env = np.exp(-t * 22)
    for d in (0.0, 0.011, 0.022):
        k = int(d * SR); env[k:k + 60] += 0.6
    return nz * env * 0.6


def snare():
    n = int(0.12 * SR); t = t_(n)
    s = filt(noise(n), [1500, 7000], "band") * np.exp(-t * 35)
    s += np.sin(2 * np.pi * 210 * t) * np.exp(-t * 40) * 0.4
    return s


def acid(f, open_):
    n = int(S16 * SR * 0.85); t = t_(n)
    raw = saw(f, n)
    bright = filt(raw, [800 + 2600 * open_, 1600 + 4000 * open_], "band") * 2.2
    dark = filt(raw, 500)
    fe = np.exp(-t * 30)
    env = np.minimum(1, t / 0.002) * np.exp(-t * 14)
    env[-60:] *= np.linspace(1, 0, 60)
    return np.tanh((bright * fe + dark * (1 - fe)) * env * 2) * 0.5


def fm_line(events, length, ratio=2.0, index=2.5, glide=0.03, attack=0.004,
            decay=6.0, sustain=0.6, release=0.03, bright=4500):
    """events: list of (start, dur, freq) in samples relative to region start."""
    freq = np.zeros(length); amp = np.zeros(length)
    prev = events[0][2]
    for st, du, f in events:
        end = min(length, st + du)
        if st >= length: break
        nseg = length - st if st + du + int(release * SR) > length else du + int(release * SR)
        tt = t_(nseg)
        g = np.minimum(1, tt / max(glide, 1e-4))
        freq[st:st + nseg] = prev * (f / prev) ** g
        e = np.minimum(1, tt / attack) * (sustain + (1 - sustain) * np.exp(-tt * decay))
        rel_start = du
        e[rel_start:] *= np.exp(-(tt[rel_start:] - tt[rel_start]) / release) if rel_start < nseg else 1
        amp[st:st + nseg] = np.maximum(amp[st:st + nseg], e)
        prev = f
    freq[freq == 0] = prev
    ph = 2 * np.pi * np.cumsum(freq) / SR
    mod = np.sin(ph * ratio) * index * (0.4 + 0.6 * amp)
    s = np.sin(ph + mod) * 0.7 + saw(freq, length) * 0.18
    return filt(s, bright) * amp


def bell(f, dur=5.0):
    n = int(dur * SR); t = t_(n)
    idx = 3 * np.exp(-t * 2)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t))
    return s * np.exp(-t * 1.1) * 0.5


def pad_chord(freqs, dur):
    n = int(dur * SR); t = t_(n)
    s = np.zeros(n)
    for f in freqs:
        for d in (-0.008, 0, 0.007):
            s += saw(f * (1 + d), n)
    s = filt(s / (3 * len(freqs)), 1300)
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.7)
    return s * np.clip(env, 0, 1)


def cricket(f):
    n = int(0.16 * SR); t = t_(n)
    pulses = (np.sin(2 * np.pi * 28 * t) > 0.3).astype(float)
    pulses = filt(pulses, 300)
    return np.sin(2 * np.pi * f * t) * pulses * np.hanning(n)


def zap(up=False):
    n = int(0.2 * SR); t = t_(n)
    f = 300 + 3200 * (np.exp(-t * 25) if not up else 1 - np.exp(-t * 25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.5


def voice(text, whisper=False, pitch_shift=0.82):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "v.wav")
        v = "pt-br+whisper" if whisper else "pt-br+m3"
        subprocess.run(["espeak-ng", "-v", v, "-p", "18", "-s", "115", "-w", p, text],
                       check=True, capture_output=True)
        with wave.open(p) as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    # resample to SR and pitch down (slower playback = deeper, darker voice)
    ratio = sr / SR * pitch_shift
    idx = np.arange(0, len(x) - 1, ratio)
    y = np.interp(idx, np.arange(len(x)), x)
    y = filt(y, 5500)
    # light ring-mod for a robotic edge
    if not whisper:
        y = y * (0.75 + 0.25 * np.sin(2 * np.pi * 55 * t_(len(y))))
    return y / (np.max(np.abs(y)) + 1e-9) * 0.6

# ---------------- patterns ----------------
D2, F2, C2, Eb2 = note("D2"), note("F2"), note("C2"), note("Eb2")
BASS_ROOTS = [[D2] * 4, [D2, D2, F2, D2], [D2] * 4, [C2, D2, Eb2, D2]]

THEME = ["D4", "F4", "A4", "Eb5", "D5", "C5", "A4", "F4",
         "D4", "F4", "A4", "C5", "Bb4", "A4", "Eb4", "D4"]
THEME = [note(x) for x in THEME]

ACID_PAT = [  # (step, note) over 2 bars = 32 steps
    (0, "D4"), (3, "D4"), (6, "F4"), (10, "Eb5"), (14, "A4"),
    (16, "D4"), (19, "C5"), (22, "D4"), (26, "Eb4"), (28, "F4"), (30, "A4")]
ACID_PAT = [(s, note(n)) for s, n in ACID_PAT]


def drums(bar, kick_cut=None, hats=True, closed=True, claps=False, kick_on=True, gain=1.0):
    for beat in range(4):
        if kick_on:
            k = KICK if kick_cut is None else filt(KICK, kick_cut)
            add(k, pos(bar, beat), 0.95 * gain)
        if hats:
            add(hat(True), pos(bar, beat + 0.5), 0.22 * gain, pan=0.15, rev=0.1)
        if closed:
            for s16 in range(4):
                v = 0.06 + 0.04 * rng.random()
                add(hat(False), pos(bar, beat + s16 / 4), v * gain, pan=-0.3 + 0.6 * rng.random())
        if claps and beat in (1, 3):
            add(clap(), pos(bar, beat), 0.28 * gain, rev=0.25)


def bassline(bar, cut_mult=1.0, gain=1.0):
    roots = BASS_ROOTS[bar % 4]
    for beat in range(4):
        for s16 in (1, 2, 3):
            add(bass_note(roots[beat], cut_mult), pos(bar, beat + s16 / 4), 0.8 * gain)


def acid_bars(bar, gain=0.35, open_=0.5):
    for step, f in ACID_PAT:
        b = bar + step // 16
        if (step // 16) != (bar % 2):
            continue
        pan = -0.6 if (bar // 1) % 2 == 0 else 0.6
        add(acid(f, open_), pos(bar - bar % 2 + step // 16, (step % 16) / 4), gain,
            pan=pan, rev=0.15, dly=0.35)


def lead_region(bar0, nbars, octave=1.0, gain=0.4, pan=0.0, glide=0.035, ratio=2.0, idx=2.4, bright=4500):
    length = int(nbars * BAR * SR)
    ev = []
    step = int(S16 * SR)
    for b in range(nbars):
        for i, f in enumerate(THEME):
            st = int((b * BAR + i * S16) * SR)
            ev.append((st, int(step * 0.8), f * octave))
    s = fm_line(ev, length, ratio=ratio, index=idx, glide=glide, decay=10, sustain=0.45, bright=bright)
    add(s, pos(bar0), gain, pan=pan, rev=0.25, dly=0.45)

# ---------------- render sections ----------------
print("rendering...")
TOT = N

# ambience: wind + crickets + drone (intro and outro), soft through the night
def ambience(b0, b1, level=1.0, fade_in=True, fade_out=False):
    s, e = pos(b0), pos(b1)
    n = e - s
    w = filt(noise(n), [250, 1100], "band") * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t_(n)))
    env = np.ones(n)
    if fade_in: env *= np.minimum(1, t_(n) / 6)
    if fade_out: env *= np.clip((t_(n)[-1] - t_(n)) / 8, 0, 1)
    add(w * env, s, 0.18 * level, pan=-0.2, rev=0.2)
    add(np.roll(w, 20000) * env, s, 0.18 * level, pan=0.4)
    tt = s
    while tt < e - SR:
        f = rng.choice([4300, 4900, 5600])
        k = int((tt - s))
        add(cricket(f) * env[min(k, n - 1)], tt, 0.05 * level, pan=rng.uniform(-0.9, 0.9), rev=0.15)
        tt += int(rng.uniform(0.25, 0.6) * SR)


def drone(b0, b1, gain=0.25, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s; t = t_(n)
    f = note("D1")
    d = np.sin(2 * np.pi * f * t) + filt(saw(f * 2, n), 220) * 0.6
    d += filt(saw(note("A1") * 1.003, n), 300) * 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))
    env = np.minimum(1, t / 5)
    if fade_out: env *= np.clip((t[-1] - t) / 6, 0, 1)
    add(d * env, s, gain, rev=0.2)

# INTRO
i0, i1 = START["intro"]
ambience(i0, START["build1"][1], fade_out=False)
drone(i0, i1 + 4)
for b in (0, 8):
    add(bell(note("D5")), pos(i0 + b), 0.35, pan=0.3, rev=0.9, dly=0.3)
add(bell(note("A4")), pos(i0 + 12, 2), 0.25, pan=-0.4, rev=0.9)
add(voice("Quando a cidade dorme... a floresta acorda."), pos(i0 + 4), 0.55, rev=0.5, dly=0.25)
for b in range(i0 + 8, i1):  # muffled heartbeat-kick
    add(filt(KICK, 180), pos(b), 0.5)
    add(filt(KICK, 180), pos(b, 2), 0.5)

# BUILD 1
b0, b1 = START["build1"]
for i, b in enumerate(range(b0, b1)):
    frac = i / (b1 - b0)
    drums(b, kick_cut=250 + 6000 * frac ** 2, hats=i >= 4, closed=i >= 8, gain=0.6 + 0.4 * frac)
    bassline(b, cut_mult=0.35 + 0.65 * frac, gain=0.5 + 0.5 * frac)
w = sweep(noise(pos(b1) - pos(b1 - 4)), 400, 8000, "band")
add(w * np.linspace(0, 1, len(w)) ** 2, pos(b1 - 4), 0.18, rev=0.3)

# GROOVE 1
g0, g1 = START["groove1"]
for b in range(g0, g1):
    drums(b, claps=False)
    bassline(b)
    if b >= g0 + 4:
        acid_bars(b, gain=0.33, open_=min(1, (b - g0) / 16))
    if b % 8 == 7:
        add(zap(), pos(b, 3.5), 0.2, pan=0.7, dly=0.4)
add(bell(note("D5")), pos(g0 + 16), 0.2, rev=0.8, dly=0.3)
# filtered lead preview in last 8 bars of groove
lead_region(g1 - 8, 8, gain=0.16, bright=1200, pan=-0.2)

# BREAKDOWN
k0, k1 = START["breakdown"]
CH = [["D3", "F3", "A3"], ["Eb3", "G3", "Bb3"], ["D3", "F3", "A3"], ["C3", "E3", "G3"]]
for i, b in enumerate(range(k0, k1, 1)):
    ch = CH[i % 4]
    add(pad_chord([note(n) for n in ch] + [note(ch[0][:-1] + "2")], BAR + 0.7), pos(b) - int(0.3 * SR),
        0.4, rev=0.6)
# slow lead: theme one note per beat, long glide = howl
length = int(16 * BAR * SR)
ev = [(int(i * BEAT * SR), int(BEAT * SR * 0.95), THEME[i % 16]) for i in range(64)]
slow = fm_line(ev, length, ratio=2.0, index=1.2, glide=0.12, attack=0.05, decay=1.5, sustain=0.7,
               release=0.2, bright=2500)
fade = np.minimum(1, t_(length) / 4)
add(slow * fade, pos(k0), 0.28, pan=0.1, rev=0.6, dly=0.5)
drone(k0, k1, gain=0.18)
add(voice("Siga a lua...", whisper=True, pitch_shift=0.9), pos(k0 + 2), 0.6, rev=0.7, dly=0.3)
add(voice("dance com as sombras.", whisper=True, pitch_shift=0.9), pos(k0 + 6), 0.6, rev=0.7, dly=0.3)
add(voice("A noite nao tem fim.", whisper=True, pitch_shift=0.9), pos(k0 + 10), 0.6, rev=0.7, dly=0.3)
for b in range(k0 + 12, k1):
    add(filt(KICK, 160), pos(b), 0.45); add(filt(KICK, 160), pos(b, 2), 0.45)

# BUILD 2
u0, u1 = START["build2"]
for i, b in enumerate(range(u0, u1)):
    sub = 2 if i < 2 else 4 if i < 4 else 8
    last = (b == u1 - 1)
    for k in range(4 * sub):
        beat = k / sub
        if last and beat >= 2:
            break
        v = 0.12 + 0.35 * ((i * 4 + beat) / 32) ** 1.5
        add(snare(), pos(b, beat), v, pan=0.0, rev=0.25)
    if not last:
        bassline(b, cut_mult=0.6 + 0.4 * i / 8, gain=0.8)
        for beat in range(4):
            add(KICK, pos(b, beat), 0.9)
    else:
        bassline(b, gain=0.0)
        add(KICK, pos(b, 0), 0.9); add(KICK, pos(b, 1), 0.9)
# descending riser (more tension) + falling tone
n = pos(u1 - 1, 2) - pos(u0)
r = sweep(noise(n), 9000, 600, "band")
tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(1800, 140, n)) / SR) * 0.3
env = np.linspace(0.1, 1, n) ** 2
add((r + tone) * env, pos(u0), 0.25, rev=0.4)
add(voice("Desligue a luz."), pos(u1 - 1, 2), 0.75, rev=0.6, dly=0.4)

# DROP
d0, d1 = START["drop"]
for b in range(d0, d1):
    drums(b, claps=True)
    bassline(b, cut_mult=1.25)
    if b >= d0 + 16:
        acid_bars(b, gain=0.2, open_=0.8)
    if b >= d0 + 16 and b % 4 == 3:
        add(zap(up=b % 8 == 3), pos(b, 3), 0.22, pan=-0.7 if b % 8 == 3 else 0.7, dly=0.4)
lead_region(d0, 32, gain=0.36, pan=0.0)
# "howl" layer an octave up with long glide on the final 8 bars
lead_region(d1 - 8, 8, octave=2.0, gain=0.14, glide=0.09, ratio=3.5, idx=1.6, pan=0.35)
add(np.ones(1), 0)  # noop
crash = filt(noise(int(2.5 * SR)), 4000, "high") * np.exp(-t_(int(2.5 * SR)) * 1.8)
for b in (d0, d0 + 16):
    add(crash, pos(b), 0.25, rev=0.4)

# OUTRO
o0, o1 = START["outro"]
for i, b in enumerate(range(o0, o1)):
    frac = i / (o1 - o0)
    if i < 12:
        drums(b, kick_cut=8000 * (1 - frac) ** 2 + 150, hats=i < 6, closed=i < 3, gain=1 - frac * 0.7)
    if i < 8:
        bassline(b, cut_mult=1 - frac * 1.2, gain=1 - frac)
ambience(o0, o1 + 2, fade_in=True, fade_out=True)
drone(o0 + 4, o1 + 2, gain=0.2, fade_out=True)
add(voice("Ate o amanhecer..."), pos(o0 + 8), 0.6, rev=0.7, dly=0.35)
add(bell(note("D5"), 6), pos(o1 - 2), 0.35, rev=0.9, dly=0.3)

# ---------------- FX buses ----------------
print("fx...")
# ping-pong delay, dotted eighth, darkened
dt = int(0.75 * BEAT * SR)
dl = filt(DL, 3200)
for k in range(1, 7):
    g = 0.5 ** k
    sh = np.zeros(N, np.float32); sh[k * dt:] = dl[:N - k * dt] * g
    if k % 2: L += sh
    else: R += sh

# dark hall reverb
irn = int(3.2 * SR)
tir = t_(irn)
for ch in (L, R):
    ir = filt(noise(irn), 4000) * np.exp(-tir * 2.0)
    ir[: int(0.02 * SR)] = 0
    wet = oaconvolve(RV, ir.astype(np.float32))[:N]
    ch += (wet / np.max(np.abs(ir)) * 0.025).astype(np.float32)

# ---------------- master ----------------
print("master...")
mix = np.stack([L, R], 1).astype(np.float64)
mix = filt(mix.T, 25, "high").T          # clean sub rumble
mix /= np.percentile(np.abs(mix), 99.9) + 1e-9
mix = np.tanh(mix * 1.1) * 0.92
end = int((TOTAL_BARS * BAR + 4) * SR)
mix = mix[:end]
mix[-int(2 * SR):] *= np.linspace(1, 0, int(2 * SR))[:, None]

out_dir = os.path.dirname(os.path.abspath(__file__))
wav_path = os.path.join(out_dir, "frequencia_lunar.wav")
with wave.open(wav_path, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", wav_path, f"{len(mix)/SR:.1f}s")
