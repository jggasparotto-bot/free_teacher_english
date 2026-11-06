"""Ruido Lunar - hypnotic night progressive/full-on psytrance, synthesized from scratch with numpy."""
import subprocess, tempfile, os, wave
import numpy as np
from scipy.signal import butter, sosfilt, oaconvolve

SR = 44100
BPM = 144
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(7)

# ---------------- arrangement (in bars) ----------------
SECTIONS = [("intro", 16), ("build1", 16), ("groove1", 32), ("midbreak", 8), ("groove2", 24),
            ("breakdown", 16), ("build2", 8), ("drop", 40), ("outro", 16)]
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


# ================= v2: groove-driven night progressive/full-on =================
def swirl(dur, f0=300, f1=6000, gain=1.0):
    """Psychedelic swoosh: detuned saw cluster through a band filter that rises then falls."""
    n = int(dur * SR)
    base = note("D3") * rng.choice([1, 1.5, 2, 3])
    s = sum(saw(base * r * (1 + rng.uniform(-0.01, 0.01)), n) for r in (1, 1.498, 2.01, 2.997))
    s = s / 4 + noise(n) * 0.3
    half = n // 2
    a = sweep(s[:half], f0, f1, "band")
    b_ = sweep(s[half:], f1, f0, "band")
    out = np.concatenate([a, b_]) * np.hanning(n)
    return out * gain


def pan_lfo(sig, rate, depth=0.9):
    t = t_(len(sig))
    p = np.sin(2 * np.pi * rate * t) * depth
    a = (p + 1) * np.pi / 4
    return sig * np.cos(a), sig * np.sin(a)


def add_st(l, r, start, gain=1.0, rev=0.0, dly=0.0):
    if start >= N: return
    l = l[: N - start] * gain; r = r[: N - start] * gain
    L[start:start + len(l)] += l; R[start:start + len(r)] += r
    if rev: RV[start:start + len(l)] += (l + r) * 0.5 * rev
    if dly: DL[start:start + len(l)] += (l + r) * 0.5 * dly


def shaker():
    n = int(0.045 * SR); t = t_(n)
    return filt(noise(n), [6000, 12000], "band") * np.minimum(1, t / 0.006) * np.exp(-t * 70)


def tom(f=150):
    n = int(0.3 * SR); t = t_(n)
    fr = f * 0.55 + f * 0.45 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 11) * 0.8


def ride():
    n = int(0.35 * SR); t = t_(n)
    metal = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (3470, 5120, 6630, 8210))
    s = filt(metal * 0.25 + noise(n) * 0.5, 6000, "high")
    return s * np.exp(-t * 9) * 0.5


def growl(f, dur):
    """FM growl stab with a closing filter, the twisted night-psy texture."""
    n = int(dur * SR); t = t_(n)
    idx = 6 * np.exp(-t * 9) + 1
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 0.5 * t + 2 * np.sin(2 * np.pi * f * 1.01 * t)))
    s = s * 0.6 + saw(f * 1.004, n) * 0.4
    s = sweep(s, 3500, 350, "low", chunk=1024)
    env = np.minimum(1, t / 0.003) * np.exp(-t * 7)
    return np.tanh(s * env * 2.2) * 0.5


def acid_note(f, dur, accent, open_):
    n = int(dur * SR); t = t_(n)
    raw = saw(f, n)
    c = 500 + 2600 * open_ + 1400 * accent
    reso = filt(raw, [c * 0.8, c * 1.25], "band") * (2.5 + 2 * accent)
    body = filt(raw, c * 0.6)
    fe = np.exp(-t * (24 - 10 * accent))
    env = np.minimum(1, t / 0.002) * np.exp(-t * (10 - 4 * accent))
    env[-60:] *= np.linspace(1, 0, 60)
    return np.tanh((reso * fe + body * (0.5 + 0.5 * fe)) * env * (1.6 + accent)) * 0.45


# Hypnotic bass: almost always D, accents for groove, small octave fill every 8 bars
D2, F2, C2, Eb2 = note("D2"), note("F2"), note("C2"), note("Eb2")


def bass_v2(bar, cut_mult=1.0, gain=1.0):
    lfo = 0.85 + 0.3 * np.sin(2 * np.pi * bar / 8)
    for beat in range(4):
        root = D2
        if bar % 4 == 3 and beat == 3: root = F2 if (bar // 4) % 2 == 0 else Eb2
        for s16 in (1, 2, 3):
            f = root
            if bar % 8 == 7 and beat == 3 and s16 == 3: f = root * 2
            acc = 1.12 if s16 == 1 else 0.95 if s16 == 2 else 1.0
            add(bass_note(f, cut_mult * lfo * (1.1 if s16 == 3 else 1)), pos(bar, beat + s16 / 4), 0.82 * gain * acc)


def drums_v2(bar, kick_cut=None, hats=True, shakers=True, rides=False, claps=False,
             toms=False, gain=1.0):
    for beat in range(4):
        k = KICK if kick_cut is None else filt(KICK, kick_cut)
        add(k, pos(bar, beat), 0.95 * gain)
        if hats:
            add(hat(True), pos(bar, beat + 0.5), 0.2 * gain, pan=0.1, rev=0.08)
        if rides:
            add(ride(), pos(bar, beat + 0.5), 0.12 * gain, pan=-0.25, rev=0.12)
        if shakers:
            for s16 in range(4):
                sw = 0.035 if s16 % 2 else 0.0          # light swing on off-16ths
                v = (0.09 if s16 == 2 else 0.05) + 0.03 * rng.random()
                add(shaker(), pos(bar, beat + s16 / 4 + sw), v * gain, pan=0.35)
        if claps and beat in (1, 3):
            add(clap(), pos(bar, beat), 0.22 * gain, rev=0.3)
    if toms and bar % 2 == 1:
        for beat, f, p in ((2.75, 170, -0.5), (3.25, 140, 0.0), (3.5, 115, 0.5)):
            add(tom(f), pos(bar, beat), 0.32 * gain, pan=p, rev=0.35)


# Acid riff in D phrygian: (step, note, length in 16ths, accent)
RIFF_A = [(0, "D3", 1, 1), (2, "D3", 1, 0), (3, "D4", 1, 1), (5, "Eb3", 2, 0), (7, "D3", 1, 0),
          (8, "F3", 1, 1), (10, "D3", 1, 0), (11, "A3", 1, 0), (13, "C4", 1, 1), (14, "Eb4", 2, 0)]
RIFF_B = [(0, "D3", 1, 1), (1, "D3", 1, 0), (3, "Eb4", 1, 1), (4, "D4", 2, 0), (6, "A3", 1, 0),
          (8, "D3", 1, 1), (9, "F3", 1, 0), (11, "Eb3", 1, 1), (12, "D3", 1, 0), (14, "Bb3", 2, 1)]


def acid_riff(bar, open_, gain=0.32, pan_speed=0.25):
    riff = RIFF_A if bar % 4 < 3 else RIFF_B
    for step, nm, ln, acc in riff:
        sig = acid_note(note(nm), S16 * ln * 0.95, acc, open_)
        p = 0.6 * np.sin(2 * np.pi * pan_speed * (bar + step / 16))
        add(sig, pos(bar, step / 4), gain, pan=p, rev=0.12, dly=0.3)


def growl_bars(bar, gain=0.28):
    # call & response stabs on off-beats, every other bar
    if bar % 2 == 0:
        for beat, nm in ((0.75, "D2"), (1.75, "D2"), (2.5, "Eb2")):
            add(growl(note(nm) * 2, S16 * 3), pos(bar, beat), gain, pan=-0.3, rev=0.15, dly=0.25)
    else:
        add(growl(note("A2") * 2, BEAT * 0.9), pos(bar, 3), gain * 0.9, pan=0.4, rev=0.2, dly=0.4)


def ambience(b0, b1, level=1.0, fade_in=True, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s
    w = filt(noise(n), [200, 900], "band") * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t_(n)))
    env = np.ones(n)
    if fade_in: env *= np.minimum(1, t_(n) / 6)
    if fade_out: env *= np.clip((t_(n)[-1] - t_(n)) / 8, 0, 1)
    l, r = pan_lfo(w * env, 0.05)
    add_st(l, r, s, 0.2 * level, rev=0.2)
    tt = s
    while tt < e - SR:
        k = tt - s
        add(cricket(rng.choice([4300, 4900, 5600])) * env[min(k, n - 1)], tt, 0.04 * level,
            pan=rng.uniform(-0.9, 0.9), rev=0.15)
        tt += int(rng.uniform(0.3, 0.7) * SR)


def drone(b0, b1, gain=0.22, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s; t = t_(n)
    f = note("D1")
    d = np.sin(2 * np.pi * f * t) + filt(saw(f * 2, n), 200) * 0.5
    d += filt(saw(note("Eb2") * 1.003, n), 350) * 0.2 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t))
    env = np.minimum(1, t / 5)
    if fade_out: env *= np.clip((t[-1] - t) / 6, 0, 1)
    add(d * env, s, gain, rev=0.2)


def noise_riser(b0, b1, f0=400, f1=9000, gain=0.2):
    n = pos(b1) - pos(b0)
    r = sweep(noise(n), f0, f1, "band")
    add(r * np.linspace(0, 1, n) ** 2, pos(b0), gain, rev=0.35)


def crash(b, gain=0.22):
    n = int(2.5 * SR)
    add(filt(noise(n), 4500, "high") * np.exp(-t_(n) * 1.8), pos(b), gain, rev=0.4)


print("rendering v2...")

# INTRO: night field, drone, sonar-like pings, voice
i0, i1 = START["intro"]
ambience(i0, START["build1"][1])
drone(i0, i1 + 4)
for b in (0, 6, 12):
    add(bell(note("D5") if b != 6 else note("A4")), pos(i0 + b), 0.28, pan=0.3 - b * 0.05, rev=0.9, dly=0.35)
l, r = pan_lfo(swirl(BAR * 4, 200, 3000), 0.15); add_st(l, r, pos(i0 + 8), 0.25, rev=0.5)
add(voice("Sinal detectado... origem desconhecida."), pos(i0 + 3), 0.55, rev=0.5, dly=0.3)
for b in range(i0 + 8, i1):
    for beat in range(4):
        add(filt(KICK, 150 + 60 * (b - i0 - 8)), pos(b, beat), 0.5)

# BUILD 1: kick + bass open slowly, shaker comes in
b0, b1 = START["build1"]
for i, b in enumerate(range(b0, b1)):
    fr = i / (b1 - b0)
    drums_v2(b, kick_cut=300 + 6000 * fr ** 2, hats=i >= 8, shakers=i >= 4, gain=0.7 + 0.3 * fr)
    bass_v2(b, cut_mult=0.35 + 0.65 * fr, gain=0.55 + 0.45 * fr)
noise_riser(b1 - 4, b1)

# GROOVE 1: hypnotic groove, acid riff slowly opening, swirls every 8 bars
g0, g1 = START["groove1"]
for i, b in enumerate(range(g0, g1)):
    drums_v2(b, rides=i >= 16, toms=i >= 8)
    bass_v2(b)
    if i >= 8:
        acid_riff(b, open_=min(1, (i - 8) / 20), gain=0.26)
    if i % 8 == 4:
        l, r = pan_lfo(swirl(BAR * 2), 0.5); add_st(l, r, pos(b), 0.18, rev=0.3, dly=0.2)
    if i % 8 == 7:
        add(zap(), pos(b, 3.5), 0.18, pan=0.7, dly=0.4)
crash(g0)

# MID-BREAK: bass drops out, acid alone with heavy delay, then slam back
m0, m1 = START["midbreak"]
for i, b in enumerate(range(m0, m1)):
    if i < 6:
        drums_v2(b, kick_cut=None if i >= 4 else 400, hats=i >= 4, shakers=True, gain=0.8)
    acid_riff(b, open_=0.4 + 0.08 * i, gain=0.32)
add(voice("Feche os olhos... sinta o ruido.", whisper=True, pitch_shift=0.9), pos(m0 + 1), 0.6, rev=0.7, dly=0.4)
noise_riser(m1 - 2, m1, 600, 10000, 0.22)

# GROOVE 2: full groove + growl stabs + rides
h0, h1 = START["groove2"]
for i, b in enumerate(range(h0, h1)):
    drums_v2(b, rides=True, toms=True, claps=i >= 8)
    bass_v2(b, cut_mult=1.1)
    growl_bars(b, gain=0.24 + 0.1 * min(1, i / 8))
    if i >= 8:
        acid_riff(b, open_=0.7, gain=0.18, pan_speed=0.5)
    if i % 8 == 0:
        l, r = pan_lfo(swirl(BAR * 2, 400, 8000), 0.8); add_st(l, r, pos(b + 6), 0.16, rev=0.3)
crash(h0)

# BREAKDOWN: dark pad, sparse howl melody, whispers
k0, k1 = START["breakdown"]
CH = [["D3", "F3", "A3"], ["Eb3", "G3", "Bb3"], ["D3", "F3", "A3"], ["C3", "Eb3", "G3"]]
for i, b in enumerate(range(k0, k1)):
    ch = CH[(i // 2) % 4]
    if i % 2 == 0:
        add(pad_chord([note(n) for n in ch] + [note(ch[0][:-1] + "2")], 2 * BAR + 0.7),
            pos(b) - int(0.3 * SR), 0.38, rev=0.6)
THEME = [note(x) for x in ["D4", "F4", "A4", "Eb5", "D5", "C5", "A4", "F4",
                           "D4", "F4", "A4", "C5", "Bb4", "A4", "Eb4", "D4"]]
length = int(16 * BAR * SR)
ev = [(int(i * 2 * BEAT * SR), int(2 * BEAT * SR * 0.95), THEME[i % 16]) for i in range(32)]
slow = fm_line(ev, length, ratio=2.0, index=1.0, glide=0.18, attack=0.08, decay=1.2, sustain=0.7,
               release=0.3, bright=2200)
add(slow * np.minimum(1, t_(length) / 4), pos(k0 + 2), 0.24, pan=0.1, rev=0.6, dly=0.5)
drone(k0, k1, gain=0.16)
add(voice("Nada e real...", whisper=True, pitch_shift=0.88), pos(k0 + 3), 0.6, rev=0.7, dly=0.35)
add(voice("so a frequencia.", whisper=True, pitch_shift=0.88), pos(k0 + 7), 0.6, rev=0.7, dly=0.35)
for i, b in enumerate(range(k0 + 8, k1)):
    acid_riff(b, open_=0.1 + 0.05 * i, gain=0.14 + 0.02 * i)
    if i >= 4:
        for beat in range(4): add(filt(KICK, 160), pos(b, beat), 0.45)

# BUILD 2: snare roll, falling riser, silence, voice
u0, u1 = START["build2"]
for i, b in enumerate(range(u0, u1)):
    sub = 2 if i < 2 else 4 if i < 5 else 8
    last = (b == u1 - 1)
    for k in range(4 * sub):
        beat = k / sub
        if last and beat >= 2: break
        add(snare(), pos(b, beat), 0.12 + 0.35 * ((i * 4 + beat) / 32) ** 1.5, rev=0.25)
    if not last:
        bass_v2(b, cut_mult=0.5 + 0.5 * i / 8, gain=0.8)
        for beat in range(4): add(KICK, pos(b, beat), 0.9)
        acid_riff(b, open_=0.5 + 0.06 * i, gain=0.2)
    else:
        add(KICK, pos(b, 0), 0.9); add(KICK, pos(b, 1), 0.9)
n = pos(u1 - 1, 2) - pos(u0)
r = sweep(noise(n), 9000, 500, "band")
tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(2000, 120, n)) / SR) * 0.3
add((r + tone) * np.linspace(0.1, 1, n) ** 2, pos(u0), 0.24, rev=0.4)
add(voice("Agora."), pos(u1 - 1, 2.2), 0.8, rev=0.6, dly=0.45)

# DROP: everything, acid wide open, growls, twisted lead in the second half
d0, d1 = START["drop"]
for i, b in enumerate(range(d0, d1)):
    drums_v2(b, rides=True, toms=True, claps=True)
    bass_v2(b, cut_mult=1.2)
    acid_riff(b, open_=0.85 + 0.15 * np.sin(2 * np.pi * i / 16), gain=0.3, pan_speed=0.5)
    if i >= 8: growl_bars(b, gain=0.22)
    if i % 8 == 6:
        l, r = pan_lfo(swirl(BAR * 2, 500, 9000), 1.2); add_st(l, r, pos(b), 0.15, rev=0.3, dly=0.2)
    if i % 4 == 3:
        add(zap(up=i % 8 == 3), pos(b, 3), 0.18, pan=-0.7 if i % 8 == 3 else 0.7, dly=0.4)
# short FM motif (half the theme), filtered, as a hook in the second half
length = int(16 * BAR * SR)
ev = []
for bb in range(16):
    for j, f in enumerate(THEME[:8] if bb % 2 == 0 else THEME[8:]):
        ev.append((int((bb * BAR + j * 2 * S16) * SR), int(S16 * SR * 1.6), f))
hook = fm_line(ev, length, ratio=3.5, index=1.8, glide=0.05, decay=8, sustain=0.4, bright=3200)
add(hook, pos(d0 + 20), 0.2, pan=0.2, rev=0.25, dly=0.45)
for b in (d0, d0 + 16, d0 + 32):
    crash(b)

# OUTRO
o0, o1 = START["outro"]
for i, b in enumerate(range(o0, o1)):
    fr = i / (o1 - o0)
    if i < 12:
        drums_v2(b, kick_cut=8000 * (1 - fr) ** 2 + 150, hats=i < 6, shakers=i < 8, gain=1 - fr * 0.7)
    if i < 8:
        bass_v2(b, cut_mult=1 - fr * 1.2, gain=1 - fr)
    if i < 6:
        acid_riff(b, open_=0.6 - i * 0.1, gain=0.2 - i * 0.03)
ambience(o0, o1 + 2, fade_in=True, fade_out=True)
drone(o0 + 4, o1 + 2, gain=0.18, fade_out=True)
add(voice("Fim do sinal."), pos(o0 + 9), 0.6, rev=0.7, dly=0.4)
add(bell(note("D5"), 6), pos(o1 - 2), 0.32, rev=0.9, dly=0.3)

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
wav_path = os.path.join(out_dir, "ruido_lunar.wav")
with wave.open(wav_path, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", wav_path, f"{len(mix)/SR:.1f}s")
