"""Tempestade Eletrica - full-on in the style of Burn in Noise, Avalon and Dickster.
B harmonic minor, 147 BPM: rolling and triplet basses, glass FM arps, a big gated
supersaw hook, a 3/4 bridge, rain and thunder, and a hard stop at the end.
All sounds synthesized from scratch with numpy; only the final mix (MP3) is written."""
import os, subprocess, tempfile, wave, json
import numpy as np
import soundfile as sf
import mido
from scipy.signal import butter, sosfilt, oaconvolve

SR = 44100
BPM = 147
SWING = 0.035
TRANSPOSE = -3         # legacy D-based helpers -> B
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(53)

SECTIONS = [("intro", 16), ("groove1", 32), ("stormbreak", 8), ("groove2", 32), ("bridge34", 6),
            ("build1", 8), ("drop1", 32), ("breakdown", 24), ("build2", 8), ("drop2", 48),
            ("twist", 8), ("drop3", 32), ("outro", 26)]
START = {}
_b = 0
for name, n in SECTIONS:
    START[name] = (_b, _b + n)
    _b += n
TOTAL_BARS = _b                        # 280 bars = 7:37 at 147 BPM
N = int((TOTAL_BARS * BAR + 5) * SR)

STEMS = ["01 Kick", "02 Bass", "03 Hats", "04 Shakers", "05 Ride", "06 Claps & Snares",
         "07 Toms & Metal", "08 Acid", "09 Growl", "10 Lead", "11 Pad & Drone", "12 Machine",
         "13 FX", "14 Atmosphere", "15 Vocals"]
BUS = {}


def bus(name):
    if name not in BUS:
        BUS[name] = {k: np.zeros(N, np.float32) for k in ("L", "R", "RV", "DL")}
    return BUS[name]


def pos(bar, beat=0.0):
    return int(round((bar * BAR + beat * BEAT) * SR))


def add(sig, start, gain=1.0, pan=0.0, rev=0.0, dly=0.0, b="13 FX"):
    if start >= N or start < 0:
        return
    sig = (sig[: N - start] * gain).astype(np.float32)
    B = bus(b); e = start + len(sig)
    a = (pan + 1) * np.pi / 4
    B["L"][start:e] += sig * np.cos(a)
    B["R"][start:e] += sig * np.sin(a)
    if rev: B["RV"][start:e] += sig * rev
    if dly: B["DL"][start:e] += sig * dly


def add_st(l, r, start, gain=1.0, rev=0.0, dly=0.0, b="13 FX"):
    if start >= N: return
    l = (l[: N - start] * gain).astype(np.float32); r = (r[: N - start] * gain).astype(np.float32)
    B = bus(b); e = start + len(l)
    B["L"][start:e] += l; B["R"][start:e] += r
    if rev: B["RV"][start:e] += (l + r) * 0.5 * rev
    if dly: B["DL"][start:e] += (l + r) * 0.5 * dly

# ---------------- MIDI capture ----------------
MIDI = {}
DRUM_MAP = {"kick": 36, "snare": 38, "clap": 39, "shaker": 42, "tom_lo": 45, "tom_mid": 47,
            "tom_hi": 48, "open_hat": 46, "ride": 51, "metal": 56}


def hz2midi(f):
    return int(round(69 + 12 * np.log2(f / 440)))


def mnote(track, bar, beat, dur_beats, f=None, vel=100, pitch=None):
    p = pitch if pitch is not None else hz2midi(f)
    MIDI.setdefault(track, []).append((bar * 4 + beat, dur_beats, p, int(np.clip(vel, 1, 127))))


def mdrum(name, bar, beat, vel=100):
    mnote("Drums", bar, beat, 0.25, pitch=DRUM_MAP[name], vel=vel)

# ---------------- DSP helpers ----------------
_sos = {}
def filt(x, cut, btype="low", order=2):
    key = (round(float(cut)) if np.ndim(cut) == 0 else tuple(round(float(c)) for c in cut), btype, order)
    if key not in _sos:
        c = np.clip(np.array(cut, float), 20, SR / 2 - 100)
        _sos[key] = butter(order, c, btype=btype, fs=SR, output="sos")
    return sosfilt(_sos[key], x, axis=-1)


def sweep(x, c0, c1, btype="low", chunk=2048):
    out = np.zeros(len(x) + chunk); win = np.hanning(chunk); hop = chunk // 2
    for s in range(0, len(x), hop):
        seg = x[s:s + chunk]
        c = c0 * (c1 / c0) ** (s / max(1, len(x)))
        y = filt(seg, [c * 0.7, c * 1.4], "band") if btype == "band" else filt(seg, c, btype)
        out[s:s + len(y)] += y * win[:len(y)]
    return out[:len(x)]


def saw(freq, n):
    return 2 * (np.cumsum(np.broadcast_to(freq, (n,)) / SR) % 1.0) - 1


def square(freq, n):
    return np.sign(np.sin(2 * np.pi * np.cumsum(np.broadcast_to(freq, (n,))) / SR))


def noise(n):
    return rng.uniform(-1, 1, n)


def t_(n):
    return np.arange(n) / SR


def note(name):
    names = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7,
             "Ab": 8, "A": 9, "Bb": 10, "B": 11}
    return 440 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) + 1) - 69 + TRANSPOSE) / 12)


def crush(x, bits=5, hold=6):
    y = np.repeat(x[::hold], hold)[:len(x)]
    q = 2 ** (bits - 1)
    return np.round(y * q) / q


def pan_lfo(sig, rate, depth=0.9):
    p = np.sin(2 * np.pi * rate * t_(len(sig))) * depth
    a = (p + 1) * np.pi / 4
    return sig * np.cos(a), sig * np.sin(a)

# ---------------- instruments ----------------
def _kick():
    n = int(0.32 * SR); t = t_(n)
    f = 44 + 120 * np.exp(-t * 38)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    click = filt(noise(n), 2500, "high") * np.exp(-t * 500) * 0.35
    return np.tanh((s + click) * 1.8) * 0.95
KICK = _kick()


def bass_note(f, cut_mult=1.0):
    n = int(S16 * SR * 0.92); t = t_(n)
    raw = saw(f, n) * 0.6 + saw(f * 1.006, n) * 0.4
    fe = np.exp(-t * 45)
    s = filt(raw, 1100 * cut_mult) * fe + filt(raw, 280 * cut_mult) * (1 - fe)
    env = np.minimum(1, t / 0.002) * np.exp(-t * 18); env[-80:] *= np.linspace(1, 0, 80)
    return np.tanh(s * env * 2.6) * 0.55

_hn = filt(noise(int(0.2 * SR)), 7500, "high", 4)
def hat(open_=True):
    n = int((0.11 if open_ else 0.03) * SR)
    return _hn[:n] * np.exp(-t_(n) * (28 if open_ else 160))


def clap():
    n = int(0.25 * SR); t = t_(n)
    env = np.exp(-t * 22)
    for d in (0.0, 0.011, 0.022):
        k = int(d * SR); env[k:k + 60] += 0.6
    return filt(noise(n), [900, 4000], "band") * env * 0.6


def snare():
    n = int(0.12 * SR); t = t_(n)
    return filt(noise(n), [1500, 7000], "band") * np.exp(-t * 35) + np.sin(2 * np.pi * 210 * t) * np.exp(-t * 40) * 0.4


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
    return filt(metal * 0.25 + noise(n) * 0.5, 6000, "high") * np.exp(-t * 9) * 0.5


def clank():
    """Metallic machine hit: inharmonic FM, short."""
    n = int(0.18 * SR); t = t_(n)
    s = np.sin(2 * np.pi * 820 * t + 4 * np.exp(-t * 30) * np.sin(2 * np.pi * 820 * 1.414 * t))
    s += np.sin(2 * np.pi * 1730 * t) * 0.4
    return filt(s, 600, "high") * np.exp(-t * 28) * 0.6


def acid_note(f, dur, accent, open_):
    n = int(dur * SR); t = t_(n)
    raw = saw(f, n)
    c = 500 + 2600 * open_ + 1400 * accent
    reso = filt(raw, [c * 0.8, c * 1.25], "band") * (2.5 + 2 * accent)
    fe = np.exp(-t * (24 - 10 * accent))
    env = np.minimum(1, t / 0.002) * np.exp(-t * (10 - 4 * accent)); env[-60:] *= np.linspace(1, 0, 60)
    return np.tanh((reso * fe + filt(raw, c * 0.6) * (0.5 + 0.5 * fe)) * env * (1.6 + accent)) * 0.45


def growl(f, dur):
    n = int(dur * SR); t = t_(n)
    idx = 6 * np.exp(-t * 9) + 1
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 0.5 * t + 2 * np.sin(2 * np.pi * f * 1.01 * t)))
    s = sweep(s * 0.6 + saw(f * 1.004, n) * 0.4, 3500, 350, "low", chunk=1024)
    env = np.minimum(1, t / 0.003) * np.exp(-t * 7)
    return np.tanh(s * env * 2.2) * 0.5


def fm_line(events, length, ratio=2.0, index=2.5, glide=0.03, attack=0.004,
            decay=6.0, sustain=0.6, release=0.03, bright=4500):
    freq = np.zeros(length); amp = np.zeros(length)
    prev = events[0][2]
    for st, du, f in events:
        if st >= length: break
        rel = int(release * SR)
        nseg = min(du + rel, length - st)
        tt = t_(nseg)
        freq[st:st + nseg] = prev * (f / prev) ** np.minimum(1, tt / max(glide, 1e-4))
        e = np.minimum(1, tt / attack) * (sustain + (1 - sustain) * np.exp(-tt * decay))
        if du < nseg: e[du:] *= np.exp(-(tt[du:] - tt[du]) / release)
        amp[st:st + nseg] = np.maximum(amp[st:st + nseg], e)
        prev = f
    freq[freq == 0] = prev
    ph = 2 * np.pi * np.cumsum(freq) / SR
    s = np.sin(ph + np.sin(ph * ratio) * index * (0.4 + 0.6 * amp)) * 0.7 + saw(freq, length) * 0.18
    return filt(s, bright) * amp


def bell(f, dur=5.0):
    n = int(dur * SR); t = t_(n)
    return np.sin(2 * np.pi * f * t + 3 * np.exp(-t * 2) * np.sin(2 * np.pi * f * 3.5 * t)) * np.exp(-t * 1.1) * 0.5


def pad_chord(freqs, dur):
    n = int(dur * SR); t = t_(n)
    s = sum(saw(f * (1 + d), n) for f in freqs for d in (-0.008, 0, 0.007))
    s = filt(s / (3 * len(freqs)), 1300)
    return s * np.clip(np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.7), 0, 1)


def cricket(f):
    n = int(0.16 * SR); t = t_(n)
    pulses = filt((np.sin(2 * np.pi * 28 * t) > 0.3).astype(float), 300)
    return np.sin(2 * np.pi * f * t) * pulses * np.hanning(n)


def zap(up=False):
    n = int(0.2 * SR); t = t_(n)
    f = 300 + 3200 * (1 - np.exp(-t * 25) if up else np.exp(-t * 25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.5


def swirl(dur, f0=300, f1=6000):
    n = int(dur * SR)
    base = note("D3") * rng.choice([1, 1.5, 2, 3])
    s = sum(saw(base * r * (1 + rng.uniform(-0.01, 0.01)), n) for r in (1, 1.498, 2.01, 2.997)) / 4 + noise(n) * 0.3
    h = n // 2
    return np.concatenate([sweep(s[:h], f0, f1, "band"), sweep(s[h:], f1, f0, "band")]) * np.hanning(n)


def blip_burst(seed, dur_bars=2):
    """Computer chatter: crushed square blips on a 32nd grid, fixed pattern per seed."""
    r = np.random.default_rng(seed)
    n = int(dur_bars * BAR * SR)
    out = np.zeros(n)
    scale = [note(x) for x in ("D6", "Eb6", "F6", "A6", "C7", "D7")]
    step = BEAT / 8
    for k in range(int(dur_bars * 32)):
        if r.random() < 0.28:
            m = int(step * SR * r.choice([0.5, 0.9]))
            f = r.choice(scale)
            s = square(f, m) * np.exp(-t_(m) * 30)
            st = int(k * step * SR)
            out[st:st + m] += s[: n - st]
    return crush(filt(out, 7000) * 0.35, bits=5, hold=4)


def machine_arp_note(f):
    n = int(S16 * SR * 0.7); t = t_(n)
    s = square(f, n) * 0.6 + saw(f * 2.003, n) * 0.3
    s = filt(s, 1800 + 1500 * np.exp(-0.0))
    return crush(s * np.exp(-t * 22), bits=6, hold=3) * 0.4


def voice(text, whisper=False, pitch_shift=0.82, robot=False):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "v.wav")
        v = "en-us+whisper" if whisper else VOICE_VAR
        subprocess.run(["espeak-ng", "-v", v, "-p", "15" if robot else "18", "-s", "105" if robot else "115",
                        "-w", p, text], check=True, capture_output=True)
        with wave.open(p) as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    ratio = sr / SR * pitch_shift
    y = np.interp(np.arange(0, len(x) - 1, ratio), np.arange(len(x)), x)
    y = filt(y, 5500)
    if robot:
        y = y * np.sin(2 * np.pi * 70 * t_(len(y))) * 0.6 + y * 0.5
        y = crush(y, bits=7, hold=3)
    elif not whisper:
        y = y * (0.75 + 0.25 * np.sin(2 * np.pi * 55 * t_(len(y))))
    return y / (np.max(np.abs(y)) + 1e-9) * 0.6


def stutter(sig, piece_s=0.104, reps=3):
    """Machine stutter: repeat the first syllable chunk before the full word."""
    k = int(piece_s * SR)
    chunk = sig[:k] * np.hanning(k) ** 0.3
    gap = np.zeros(int(S16 * SR) - k) if int(S16 * SR) > k else np.zeros(0)
    return np.concatenate([np.concatenate([chunk, gap])] * reps + [sig])

# ---------------- patterns ----------------
D2, F2, C2, Eb2 = note("D2"), note("F2"), note("C2"), note("Eb2")


def bass_bar(bar, cut_mult=1.0, gain=1.0):
    lfo = 0.85 + 0.3 * np.sin(2 * np.pi * bar / 8)
    for beat in range(4):
        root = D2
        if bar % 4 == 3 and beat == 3: root = F2 if (bar // 4) % 2 == 0 else Eb2
        for s16 in (1, 2, 3):
            f = root * (2 if (bar % 8 == 7 and beat == 3 and s16 == 3) else 1)
            acc = 1.12 if s16 == 1 else 0.95 if s16 == 2 else 1.0
            g = 0.82 * gain * acc
            if g <= 0: continue
            add(bass_note(f, cut_mult * lfo * (1.1 if s16 == 3 else 1)), pos(bar, beat + s16 / 4), g, b="02 Bass")
            mnote("Bass", bar, beat + s16 / 4, 0.23, f, vel=70 + 50 * min(1, g))


def drums_bar(bar, kick_cut=None, kick=True, hats=True, shakers=True, rides=False, claps=False,
              toms=False, metal=False, gain=1.0):
    for beat in range(4):
        if kick:
            add(KICK if kick_cut is None else filt(KICK, kick_cut), pos(bar, beat), 0.95 * gain, b="01 Kick")
            mdrum("kick", bar, beat, 110 * gain)
        if hats:
            add(hat(True), pos(bar, beat + 0.5), 0.2 * gain, pan=0.1, rev=0.08, b="03 Hats")
            mdrum("open_hat", bar, beat + 0.5, 90 * gain)
        if rides:
            add(ride(), pos(bar, beat + 0.5), 0.12 * gain, pan=-0.25, rev=0.12, b="05 Ride")
            mdrum("ride", bar, beat + 0.5, 70 * gain)
        if shakers:
            for s16 in range(4):
                sw = SWING if s16 % 2 else 0.0
                v = (0.09 if s16 == 2 else 0.05) + 0.03 * rng.random()
                add(shaker(), pos(bar, beat + s16 / 4 + sw), v * gain, pan=0.35, b="04 Shakers")
                mdrum("shaker", bar, beat + s16 / 4 + sw, 500 * v * gain)
        if claps and beat in (1, 3):
            add(clap(), pos(bar, beat), 0.22 * gain, rev=0.3, b="06 Claps & Snares")
            mdrum("clap", bar, beat, 100 * gain)
    if toms and bar % 2 == 1:
        for beat, f, p, nm in ((2.75, 170, -0.5, "tom_hi"), (3.25, 140, 0.0, "tom_mid"), (3.5, 115, 0.5, "tom_lo")):
            add(tom(f), pos(bar, beat), 0.32 * gain, pan=p, rev=0.35, b="07 Toms & Metal")
            mdrum(nm, bar, beat, 100 * gain)
    if metal:
        for beat in ((1.75, 3.5) if bar % 2 == 0 else (0.75, 2.25, 3.75)):
            add(clank(), pos(bar, beat), 0.22 * gain, pan=rng.uniform(-0.6, 0.6), rev=0.2, dly=0.15, b="07 Toms & Metal")
            mdrum("metal", bar, beat, 90 * gain)


RIFF_A = [(0, "D3", 1, 1), (2, "D3", 1, 0), (3, "D4", 1, 1), (5, "Eb3", 2, 0), (7, "D3", 1, 0),
          (8, "F3", 1, 1), (10, "D3", 1, 0), (11, "A3", 1, 0), (13, "C4", 1, 1), (14, "Eb4", 2, 0)]
RIFF_B = [(0, "D3", 1, 1), (1, "D3", 1, 0), (3, "Eb4", 1, 1), (4, "D4", 2, 0), (6, "A3", 1, 0),
          (8, "D3", 1, 1), (9, "F3", 1, 0), (11, "Eb3", 1, 1), (12, "D3", 1, 0), (14, "Bb3", 2, 1)]


def acid_bar(bar, open_, gain=0.3, pan_speed=0.25):
    for step, nm, ln, acc in (RIFF_A if bar % 4 < 3 else RIFF_B):
        p = 0.6 * np.sin(2 * np.pi * pan_speed * (bar + step / 16))
        add(acid_note(note(nm), S16 * ln * 0.95, acc, open_), pos(bar, step / 4), gain, pan=p, rev=0.12, dly=0.3, b="08 Acid")
        mnote("Acid", bar, step / 4, ln * 0.25 * 0.95, note(nm), vel=80 + 40 * acc)


def growl_bar(bar, gain=0.26):
    if bar % 2 == 0:
        for beat, nm in ((0.75, "D3"), (1.75, "D3"), (2.5, "Eb3")):
            add(growl(note(nm), S16 * 3), pos(bar, beat), gain, pan=-0.3, rev=0.15, dly=0.25, b="09 Growl")
            mnote("Growl", bar, beat, 0.75, note(nm))
    else:
        add(growl(note("A3"), BEAT * 0.9), pos(bar, 3), gain * 0.9, pan=0.4, rev=0.2, dly=0.4, b="09 Growl")
        mnote("Growl", bar, 3, 0.9, note("A3"))


ARP = ["D4", "D5", "A4", "Eb5", "D4", "C5", "A4", "D5"]
def machine_arp_bar(bar, gain=0.2, cut=1.0):
    for i in range(16):
        nm = ARP[i % 8] if bar % 2 == 0 else ARP[(i + 3) % 8]
        f = note(nm)
        s = machine_arp_note(f)
        if cut < 1: s = filt(s, 300 + 5000 * cut)
        add(s, pos(bar, i / 4), gain, pan=0.5 * np.sin(np.pi * i / 8), rev=0.1, dly=0.25, b="12 Machine")
        mnote("Machine Arp", bar, i / 4, 0.18, f, vel=85)


BLIPS = {s: blip_burst(s) for s in (1, 2, 3, 4)}
def blips(bar, gain=0.16, seed=None):
    if bar % 2: return
    s = BLIPS[seed or (1 + (bar // 2) % 4)]
    l, r = pan_lfo(s, 0.3, 0.8)
    add_st(l, r, pos(bar), gain, rev=0.1, dly=0.2, b="12 Machine")


def ambience(b0, b1, level=1.0, fade_in=True, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s
    w = filt(noise(n), [200, 900], "band") * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t_(n)))
    env = np.ones(n)
    if fade_in: env *= np.minimum(1, t_(n) / 6)
    if fade_out: env *= np.clip((t_(n)[-1] - t_(n)) / 8, 0, 1)
    l, r = pan_lfo(w * env, 0.05)
    add_st(l, r, s, 0.2 * level, rev=0.2, b="14 Atmosphere")
    tt = s
    while tt < e - SR:
        add(cricket(rng.choice([4300, 4900, 5600])) * env[min(tt - s, n - 1)], tt, 0.04 * level,
            pan=rng.uniform(-0.9, 0.9), rev=0.15, b="14 Atmosphere")
        tt += int(rng.uniform(0.3, 0.7) * SR)


def drone(b0, b1, gain=0.22, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s; t = t_(n)
    f = note("D1")
    d = np.sin(2 * np.pi * f * t) + filt(saw(f * 2, n), 200) * 0.5
    d += filt(saw(note("Eb2") * 1.003, n), 350) * 0.2 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t))
    env = np.minimum(1, t / 5)
    if fade_out: env *= np.clip((t[-1] - t) / 6, 0, 1)
    add(d * env, s, gain, rev=0.2, b="11 Pad & Drone")
    mnote("Drone", b0, 0, (b1 - b0) * 4, f, vel=80)


def riser(b0, b1, f0=400, f1=9000, gain=0.2):
    n = pos(b1) - pos(b0)
    add(sweep(noise(n), f0, f1, "band") * np.linspace(0, 1, n) ** 2, pos(b0), gain, rev=0.35)


def fall_riser(b0, b1, gain=0.24):
    n = pos(b1) - pos(b0)
    r = sweep(noise(n), 9000, 500, "band")
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(2000, 120, n)) / SR) * 0.3
    add((r + tone) * np.linspace(0.1, 1, n) ** 2, pos(b0), gain, rev=0.4)


def crash(bar, gain=0.22):
    n = int(2.5 * SR)
    add(filt(noise(n), 4500, "high") * np.exp(-t_(n) * 1.8), pos(bar), gain, rev=0.4)


def swirl_at(bar, bars=2, f0=400, f1=8000, rate=0.6, gain=0.16):
    l, r = pan_lfo(swirl(BAR * bars, f0, f1), rate)
    add_st(l, r, pos(bar), gain, rev=0.3, dly=0.2)


def snare_roll(b0, b1, gain=1.0, stop_beats=2):
    nb = b1 - b0
    for i, b in enumerate(range(b0, b1)):
        sub = 2 if i < nb * 0.25 else 4 if i < nb * 0.6 else 8
        for k in range(4 * sub):
            beat = k / sub
            if b == b1 - 1 and beat >= 4 - stop_beats: break
            v = (0.12 + 0.35 * ((i * 4 + beat) / (nb * 4)) ** 1.5) * gain
            add(snare(), pos(b, beat), v, rev=0.25, b="06 Claps & Snares")
            mdrum("snare", b, beat, 60 + 60 * v / 0.47)


VO = lambda sig, bar, beat=0, g=0.6, rev=0.5, dly=0.3, pan=0.0: add(sig, pos(bar, beat), g, pan=pan, rev=rev, dly=dly, b="15 Vocals")
THEME = [note(x) for x in ["D4", "F4", "A4", "Eb5", "D5", "C5", "A4", "F4",
                           "D4", "F4", "A4", "C5", "Bb4", "A4", "Eb4", "D4"]]


def hook(bar0, nbars, gain=0.2, octave=1.0, pan=0.2):
    length = int(nbars * BAR * SR); ev = []
    for bb in range(nbars):
        for j, f in enumerate(THEME[:8] if bb % 2 == 0 else THEME[8:]):
            ev.append((int((bb * BAR + j * 2 * S16) * SR), int(S16 * SR * 1.6), f * octave))
            mnote("Lead Hook", bar0 + bb, j * 0.5, 0.4, f * octave, vel=95)
    add(fm_line(ev, length, ratio=3.5, index=1.8, glide=0.05, decay=8, sustain=0.4, bright=3200),
        pos(bar0), gain, pan=pan, rev=0.25, dly=0.45, b="10 Lead")


def pads(b0, b1, gain=0.38):
    CH = [["D3", "F3", "A3"], ["Eb3", "G3", "Bb3"], ["D3", "F3", "A3"], ["C3", "Eb3", "G3"]]
    for i, b in enumerate(range(b0, b1, 2)):
        ch = CH[i % 4]
        fs = [note(n) for n in ch] + [note(ch[0][:-1] + "2")]
        add(pad_chord(fs, 2 * BAR + 0.7), pos(b) - int(0.3 * SR), gain, rev=0.6, b="11 Pad & Drone")
        for f in fs: mnote("Pad", b, 0, 8, f, vel=75)


def slow_lead(b0, nbars, gain=0.24):
    length = int(nbars * BAR * SR)
    k = nbars * 2
    ev = [(int(i * 2 * BEAT * SR), int(2 * BEAT * SR * 0.95), THEME[i % 16]) for i in range(k)]
    for i in range(k): mnote("Lead Slow", b0 + i // 2, (i % 2) * 2, 1.9, THEME[i % 16], vel=80)
    s = fm_line(ev, length, ratio=2.0, index=1.0, glide=0.18, attack=0.08, decay=1.2, sustain=0.7, release=0.3, bright=2200)
    add(s * np.minimum(1, t_(length) / 4), pos(b0), gain, pan=0.1, rev=0.6, dly=0.5, b="10 Lead")

# ======================= MARE NOTURNA: new instruments =======================
def note_raw(name):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11, "Bb": 10, "Eb": 3}
    return 440 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) + 1) - 69 + TRANSPOSE) / 12)

A1, Bb1, G1 = note_raw("A1"), note_raw("Bb1"), note_raw("G1")
CHORD_ROOTS = [A1, Bb1, A1, G1]          # Am - Bb - Am - Gm (A phrygian), one bar each


def bass_roots(bar, root, cut_mult=1.0, gain=1.0):
    """Full-on bass following the chord root (Regan/Nano side)."""
    for beat in range(4):
        for s16 in (1, 2, 3):
            f = root * (2 if (bar % 4 == 3 and beat == 3 and s16 == 3) else 1)
            acc = 1.12 if s16 == 1 else 0.95 if s16 == 2 else 1.0
            add(bass_note(f, cut_mult * (1.1 if s16 == 3 else 1)), pos(bar, beat + s16 / 4), 0.82 * gain * acc, b="02 Bass")


def supersaw_line(events, length, cut=5500, gate_depth=0.0, glide=0.02):
    """7-voice supersaw, stereo, optional 16th trance gate. events: (start, dur, freq) in samples."""
    freq = np.zeros(length); amp = np.zeros(length)
    prev = events[0][2]
    for st, du, f in events:
        if st >= length: break
        rel = int(0.04 * SR); nseg = min(du + rel, length - st); tt = t_(nseg)
        freq[st:st + nseg] = prev * (f / prev) ** np.minimum(1, tt / glide)
        e = np.minimum(1, tt / 0.004) * (0.65 + 0.35 * np.exp(-tt * 6))
        if du < nseg: e[du:] *= np.exp(-(tt[du:] - tt[du]) / 0.04)
        amp[st:st + nseg] = np.maximum(amp[st:st + nseg], e)
        prev = f
    freq[freq == 0] = prev
    det = [-0.019, -0.011, -0.004, 0.0, 0.005, 0.012, 0.02]
    l = np.zeros(length); r = np.zeros(length)
    for i, d in enumerate(det):
        s = saw(freq * (1 + d), length)
        w = (i / 6)
        l += s * (1 - w) + s * 0.3; r += s * w + s * 0.3
    if gate_depth:
        g = 1 - gate_depth * ((np.arange(length) / (S16 * SR)) % 1 > 0.6)
        g = filt(g.astype(float), 200)
        amp = amp * g
    l = filt(l / 7, cut) * amp; r = filt(r / 7, cut) * amp
    return l, r


def pluck(f):
    n = int(0.25 * SR); t = t_(n)
    raw = saw(f, n) * 0.6 + square(f * 1.003, n) * 0.4
    fe = np.exp(-t * 28)
    s = filt(raw, 4500) * fe + filt(raw, 700) * (1 - fe)
    return s * np.minimum(1, t / 0.002) * np.exp(-t * 14) * 0.45


ARP = {0: ["A4", "A5", "E5", "A4", "Bb4", "A5", "E5", "C5", "A4", "A5", "E5", "A4", "C5", "Bb4", "A4", "E5"],
       1: ["Bb4", "Bb5", "F5", "Bb4", "C5", "Bb5", "F5", "D5", "Bb4", "Bb5", "F5", "Bb4", "D5", "C5", "Bb4", "F5"],
       2: ["A4", "A5", "E5", "A4", "Bb4", "A5", "E5", "C5", "A4", "E5", "A5", "C6", "Bb5", "A5", "E5", "C5"],
       3: ["G4", "G5", "D5", "G4", "Bb4", "G5", "D5", "Bb4", "G4", "G5", "D5", "G4", "A4", "Bb4", "C5", "D5"]}


def pluck_bar(bar, gain=0.2, cut=1.0, chord=None):
    c = chord if chord is not None else bar % 4
    for i, nm in enumerate(ARP[c]):
        s = pluck(note_raw(nm))
        if cut < 1: s = filt(s, 400 + 6000 * cut)
        add(s, pos(bar, i / 4), gain, pan=0.45 * np.sin(np.pi * i / 4), rev=0.2, dly=0.35, b="12 Machine")


MELODY = [[(0, 3, "E5"), (3, 3, "A5"), (6, 2, "Bb5"), (8, 4, "A5"), (12, 2, "G5"), (14, 2, "E5")],
          [(0, 3, "F5"), (3, 3, "Bb5"), (6, 2, "D6"), (8, 4, "C6"), (12, 2, "Bb5"), (14, 2, "F5")],
          [(0, 3, "E5"), (3, 3, "A5"), (6, 2, "C6"), (8, 4, "E6"), (12, 2, "D6"), (14, 2, "C6")],
          [(0, 6, "D6"), (6, 2, "C6"), (8, 4, "Bb5"), (12, 4, "A5")]]


def lead_melody(bar0, nbars, gain=0.22, octave=1.0, gate=0.55, cut=6000, slow=1):
    """Euphoric supersaw melody over Am-F-C-G. slow=2 stretches each bar over 2 bars."""
    length = int(nbars * BAR * SR); ev = []
    for bb in range(nbars // slow):
        for st, ln, nm in MELODY[bb % 4]:
            ev.append((int(((bb * 16 + st) * slow) * S16 * SR), int(ln * slow * S16 * SR * 0.95), note_raw(nm) * octave))
    l, r = supersaw_line(ev, length, cut=cut, gate_depth=gate)
    add_st(l, r, pos(bar0), gain, rev=0.3, dly=0.3, b="10 Lead")


def chords_pad(b0, b1, gain=0.3, slow=1):
    CH = [["A3", "C4", "E4"], ["Bb3", "D4", "F4"], ["A3", "C4", "E4"], ["G3", "Bb3", "D4"]]
    for i, b in enumerate(range(b0, b1, slow)):
        fs = [note_raw(n) for n in CH[i % 4]]; fs.append(fs[0] / 2)
        add(pad_chord(fs, slow * BAR + 0.7), pos(b) - int(0.3 * SR), gain, rev=0.6, b="11 Pad & Drone")


def waves(b0, b1, gain=0.22, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s; t = t_(n)
    swell = (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.0 - np.pi / 2)) ** 2
    w = filt(noise(n), 900) * swell + filt(noise(n), [2000, 6000], "band") * swell ** 3 * 0.4
    env = np.minimum(1, t / 6)
    if fade_out: env *= np.clip((t[-1] - t) / 8, 0, 1)
    l, r = pan_lfo(w * env, 0.03, 0.6)
    add_st(l, r, s, gain, rev=0.25, b="14 Atmosphere")


TWIST = ["A4", None, "C5", "Bb4", "A4", "E5", None, "D5", "C5", "Bb4", "A4", None, "G4", "A4", "Bb4", "C5",
         "A5", None, "E5", "F5", "E5", "Bb4", None, "A4", "E5", "D5", "C5", None, "Bb4", "C5", "D5", "E5"]


def twisted_lead(bar0, nbars, gain=0.2, pan=0.0, octave=1.0):
    """Psychedelic full-on lead: every note dives in from a fifth above, FM squelch, wobble."""
    length = int(nbars * BAR * SR)
    freq = np.zeros(length); amp = np.zeros(length)
    step = int(S16 * SR)
    for k in range(nbars * 16):
        nm = TWIST[k % 32]
        if nm is None: continue
        f = note_raw(nm) * octave
        st = k * step; n = min(int(step * 1.7), length - st)
        tt = t_(n)
        freq[st:st + n] = f * (1 + 0.5 * np.exp(-tt * 70))          # dive from a fifth above
        amp[st:st + n] = np.maximum(amp[st:st + n], np.minimum(1, tt / 0.002) * np.exp(-tt * 9))
    freq[freq == 0] = note_raw("A4") * octave
    t = t_(length)
    freq *= 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    idx = 2.5 + 2 * np.sin(2 * np.pi * t / (BAR * 4))               # timbre morphs every 4 bars
    s = np.sin(ph + idx * amp * np.sin(ph * 1.5)) * 0.6 + saw(freq, length) * 0.3
    s = filt(s, [500, 6000], "band") * amp
    l, r = pan_lfo(np.tanh(s * 1.5), 0.25, 0.5)
    add_st(l, r, pos(bar0), gain, rev=0.2, dly=0.4, b="10 Lead")


def boing(up=False):
    n = int(0.35 * SR); t = t_(n)
    f = 90 + 900 * (np.exp(-t * 12) if not up else 1 - np.exp(-t * 12))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph + 3 * np.sin(ph * 0.5)) * np.exp(-t * 7) * 0.5


def reverse_swell(dur):
    n = int(dur * SR); t = t_(n)
    s = sum(saw(note_raw(x) * (1 + d), n) for x in ("A3", "E4", "A4") for d in (-0.006, 0.006)) / 6
    s = filt(s + noise(n) * 0.2, 2500)
    return s * (t / dur) ** 3


def uplifter(b0, b1, gain=0.2):
    """Rising supersaw-noise sweep: full-on style lift into a drop."""
    n = pos(b1) - pos(b0)
    f = np.geomspace(200, 3000, n)
    s = sum(saw(f * (1 + d), n) for d in (-0.01, 0, 0.012)) / 3
    s = sweep(s + noise(n) * 0.3, 500, 9000, "band")
    add(s * np.linspace(0, 1, n) ** 2, pos(b0), gain, rev=0.35)

# ======================= TRES LUAS: key, kick and Dickster-side instruments =======================
_NR = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "Ab": 8,
       "A": 9, "Bb": 10, "B": 11}
RAW_SHIFT = -3        # melodies written in A phrygian -> played in F# phrygian


def note_raw(name):
    return 440 * 2 ** ((_NR[name[:-1]] + 12 * (int(name[-1]) + 1) - 69 + RAW_SHIFT) / 12)


A1, Bb1, G1 = note_raw("A1"), note_raw("Bb1"), note_raw("G1")
CHORD_ROOTS = [A1, Bb1, A1, G1]      # F#m - G - F#m - Em


def _punch_kick():
    """Harder, shorter full-power kick."""
    n = int(0.28 * SR); t = t_(n)
    f = 46 + 150 * np.exp(-t * 45)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9.5)
    click = filt(noise(n), 3000, "high") * np.exp(-t * 700) * 0.5
    return np.tanh((s + click) * 2.3) * 0.95
KICK = _punch_kick()


def vfilt(x, center_fn, q=0.35, chunk=1024):
    """Band-pass with a time-varying center: center_fn(time_s) -> Hz."""
    out = np.zeros(len(x) + chunk); win = np.hanning(chunk); hop = chunk // 2
    for s in range(0, len(x), hop):
        seg = x[s:s + chunk]
        c = float(center_fn(s / SR))
        y = filt(seg, [c * (1 - q), c * (1 + q)], "band")
        out[s:s + len(y)] += y * win[:len(y)]
    return out[:len(x)]


# Funky wah riff, written in D phrygian (played in F# through TRANSPOSE): (16th step, note, len)
WAH = [(0, "D3", 1), (2, "D3", 1), (3, "F3", 1), (6, "D3", 1), (7, "A3", 2), (10, "C4", 1),
       (11, "A3", 1), (13, "F3", 1), (14, "Eb3", 2)]


def wah_bar(bar, gain=0.22, pan=0.0):
    n = int(BAR * SR); sig = np.zeros(n)
    for st, nm, ln in WAH:
        f = note(nm); m = int(ln * S16 * SR * 0.9); tt = t_(m)
        s = (saw(f, m) * 0.6 + square(f * 1.003, m) * 0.4) * np.minimum(1, tt / 0.003) * np.exp(-tt * 6)
        a = int(st * S16 * SR); sig[a:a + m] += s[: n - a]
        mnote("Wah", bar, st / 4, ln * 0.225, f)
    sig = vfilt(sig, lambda tm: 500 * (1 + 3.5 * (0.5 + 0.5 * np.sin(2 * np.pi * tm / BEAT - np.pi / 2))))
    add(np.tanh(sig * 2) * 0.6, pos(bar), gain, pan=pan, rev=0.12, dly=0.25, b="10 Lead")


def stab(chord_notes):
    n = int(0.16 * SR); t = t_(n)
    s = sum(saw(note(x) * (1 + d), n) for x in chord_notes for d in (-0.005, 0.005)) / (2 * len(chord_notes))
    s = filt(s, 4500) * np.exp(-t * 22) * np.minimum(1, t / 0.002)
    return filt(s, 250, "high")


STAB_CH = ["D4", "F4", "A4", "C5"]          # i-m7, the funky chord
def stabs_bar(bar, gain=0.2):
    hits = (0.75, 1.5, 2.75) if bar % 2 == 0 else (0.75, 2.25, 3.5, 3.75)
    for bt in hits:
        add(stab(STAB_CH), pos(bar, bt), gain, pan=0.35 if bt % 1 else -0.35, rev=0.2, dly=0.3, b="11 Pad & Drone")


def elastic(base=180, up=True):
    """Rubber-band twang: pitch wobble whose speed accelerates."""
    n = int(0.7 * SR); t = t_(n)
    rate = 5 + 30 * t / 0.7
    wob = np.sin(2 * np.pi * np.cumsum(rate) / SR) * 0.45 * np.exp(-t * 2.5)
    f = base * (1 + wob) * (1 + (0.6 * t if up else -0.4 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph + 1.2 * np.sin(ph * 2)) * np.exp(-t * 4.5) * 0.5


def rim():
    n = int(0.03 * SR); t = t_(n)
    return filt(noise(n), [1800, 3200], "band") * np.exp(-t * 180) * 1.5


def rims_bar(bar, gain=0.12):
    for k in (1, 3, 6, 9, 11, 14):
        sw = SWING if k % 2 else 0.0
        add(rim(), pos(bar, k / 4 + sw), gain * (1.2 if k in (6, 14) else 0.8), pan=-0.45, rev=0.1,
            b="07 Toms & Metal")

RAW_SHIFT = 0
# ======================= MIRAGEM: new palette (nothing reused from earlier tracks' riffs) =======================
from scipy.signal import lfilter

KEY = 1.0          # global key multiplier: drop 2 modulates up a semitone
VOICE_VAR = "en-us+m3"


def nr(name):
    """Absolute note name -> Hz, times the current key multiplier."""
    return note_raw(name) * KEY


def _knock_kick():
    """Full-on 'knock' kick: tight body with a short tonal tail."""
    n = int(0.3 * SR); t = t_(n)
    f = 48 + 170 * np.exp(-t * 55) + 30 * np.exp(-t * 12)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
    click = filt(noise(n), [2500, 9000], "band") * np.exp(-t * 900) * 0.6
    return np.tanh((s + click) * 2.6) * 0.95
KICK = _knock_kick()


# ---- bass: zappy square/saw with a pitch blip on every note, moves inside phrygian dominant ----
def zbass(f, cut=1.0):
    n = int(S16 * SR * 0.9); t = t_(n)
    fr = f * (1 + 0.18 * np.exp(-t * 140))
    ph = np.cumsum(fr) / SR
    raw = (2 * (ph % 1) - 1) * 0.55 + np.sign(np.sin(2 * np.pi * ph)) * 0.25 + np.sin(2 * np.pi * ph) * 0.5
    fe = np.exp(-t * 55)
    s = filt(raw, 1500 * cut) * fe + filt(raw, 320 * cut) * (1 - fe)
    env = np.minimum(1, t / 0.0015) * np.exp(-t * 20); env[-60:] *= np.linspace(1, 0, 60)
    return np.tanh(s * env * 3.0) * 0.5

# per-bar bass phrases (notes for the 3 off-kick 16ths of each beat); 4-bar cycle
BASS_HYP = [["G1"] * 12, ["G1"] * 12, ["G1"] * 12, ["G1"] * 9 + ["G2", "G1", "G1"]]
BASS_MOVE = [["G1"] * 12,
             ["G1"] * 6 + ["Ab1"] * 6,
             ["G1"] * 12,
             ["F1"] * 6 + ["G1", "G1", "G2", "Ab1", "G1", "B1"]]


def bass_line(bar, phrases, cut=1.0, gain=1.0):
    ph = phrases[bar % 4]
    for beat in range(4):
        for j, s16 in enumerate((1, 2, 3)):
            nm = ph[beat * 3 + j]
            acc = 1.15 if s16 == 1 else 0.92 if s16 == 2 else 1.0
            add(zbass(nr(nm), cut), pos(bar, beat + s16 / 4), 0.85 * gain * acc, b="02 Bass")


# ---- darbuka: doum / tek / ka ----
def doum():
    n = int(0.22 * SR); t = t_(n)
    return np.sin(2 * np.pi * np.cumsum(95 + 60 * np.exp(-t * 30)) / SR) * np.exp(-t * 14) * 0.9


def tek(bright=1.0):
    n = int(0.07 * SR); t = t_(n)
    s = filt(noise(n), [1800, 6000 * bright], "band") * np.exp(-t * 90) + np.sin(2 * np.pi * 740 * t) * np.exp(-t * 60) * 0.4
    return s


DARB = {0: "D", 0.75: "t", 1.0: "T", 1.5: "D", 2.0: "T", 2.5: "t", 2.75: "t", 3.0: "T", 3.5: "k", 3.75: "t"}


def darbuka_bar(bar, gain=0.3, fill=False):
    hits = dict(DARB)
    if fill:
        hits.update({3.0: "T", 3.25: "t", 3.5: "T", 3.75: "t"})
    for bt, k in hits.items():
        sw = SWING if (bt * 4) % 2 == 1 else 0
        if k == "D":
            add(doum(), pos(bar, bt), gain, pan=-0.15, rev=0.15, b="07 Toms & Metal")
        else:
            add(tek(1.3 if k == "T" else 1.0), pos(bar, bt + sw), gain * (0.8 if k == "T" else 0.5),
                pan=0.3 if k != "k" else -0.4, rev=0.15, b="07 Toms & Metal")


def darbuka_roll(b0, b1, gain=0.32):
    nb = b1 - b0
    for i, b in enumerate(range(b0, b1)):
        sub = 4 if i < nb * 0.5 else 8 if i < nb * 0.85 else 12
        for k in range(4 * sub):
            beat = k / sub
            if b == b1 - 1 and beat >= 3: break
            v = gain * (0.35 + 0.65 * ((i * 4 + beat) / (nb * 4)))
            add(tek(1.0 + 0.5 * (k % 2)), pos(b, beat), v, pan=0.4 * np.sin(k), rev=0.2, b="07 Toms & Metal")


def zill():
    n = int(0.6 * SR); t = t_(n)
    f = 4200
    return np.sin(2 * np.pi * f * t + 2 * np.exp(-t * 6) * np.sin(2 * np.pi * f * 3.1 * t)) * np.exp(-t * 6) * 0.25


# ---- oud-like pluck: Karplus-Strong ----
def oud(f, dur=0.6, bright=0.5):
    n = int(dur * SR)
    P = max(2, int(round(SR / f)))
    exc = np.zeros(n); burst = filt(noise(P), 1500 + 5000 * bright)
    exc[:P] = burst
    a = np.zeros(P + 2); a[0] = 1; a[P] = -0.497; a[P + 1] = -0.497
    y = lfilter([1.0], a, exc)
    y = y + filt(y, [180, 900], "band") * 0.6           # wooden body resonance
    return y / (np.max(np.abs(y)) + 1e-9) * 0.5 * np.minimum(1, t_(n) / 0.001)

# 2-bar oud riff in G phrygian dominant: (16th step, note) ; None = rest
OUD_A = ["G4", "Ab4", "B4", None, "C5", "B4", "Ab4", "G4", "F4", "G4", "Ab4", None, "G4", None, "D4", None,
         "G4", "Ab4", "B4", "D5", "C5", "B4", "Ab4", None, "B4", "Ab4", "G4", "F4", "G4", None, None, None]


def oud_bars(bar0, nbars, gain=0.22, oct_=1.0, pan=0.25, cut=1.0):
    for k in range(nbars * 16):
        nm = OUD_A[k % 32]
        if nm is None: continue
        s = oud(nr(nm) * oct_)
        if cut < 1: s = filt(s, 500 + 7000 * cut)
        add(s, pos(bar0, k / 4), gain, pan=pan + 0.15 * np.sin(k), rev=0.25, dly=0.3, b="12 Machine")


# ---- screamer lead: saturated saw stack, bends up into each phrase, vibrato on long notes ----
SCREAM = [(0, 4, "D5"), (4, 2, "Eb5"), (6, 2, "D5"), (8, 2, "C5"), (10, 2, "B4"), (12, 4, "C5"),
          (16, 3, "B4"), (19, 3, "Ab4"), (22, 10, "G4"),
          (32, 4, "G5"), (36, 2, "F5"), (38, 2, "Eb5"), (40, 2, "D5"), (42, 2, "Eb5"), (44, 4, "D5"),
          (48, 3, "C5"), (51, 3, "B4"), (54, 2, "Ab4"), (56, 8, "B4")]


def screamer(bar0, nbars, gain=0.2, oct_=1.0, pan=0.0):
    length = int(nbars * BAR * SR)
    freq = np.zeros(length); amp = np.zeros(length)
    prev = nr("G4") * oct_
    for cyc in range(0, nbars, 4):
        for st, ln, nm in SCREAM:
            f = nr(nm) * oct_
            a = int((cyc * 16 + st) * S16 * SR)
            if a >= length: break
            n = min(int(ln * S16 * SR), length - a); tt = t_(n)
            bend = prev * (f / prev) ** np.minimum(1, tt / 0.05) if st % 16 else f * 2 ** ((-2 + 2 * np.minimum(1, tt / 0.12)) / 12)
            vib = 1 + 0.008 * np.sin(2 * np.pi * 6 * tt) * np.minimum(1, tt / 0.25)
            freq[a:a + n] = bend * vib
            amp[a:a + n] = np.minimum(1, tt / 0.005) * (0.8 + 0.2 * np.exp(-tt * 4))
            amp[a + n - min(n, 200):a + n] *= np.linspace(1, 0.3, min(n, 200))
            prev = f
    freq[freq == 0] = prev
    s = sum(saw(freq * (1 + d), length) for d in (-0.012, -0.004, 0.004, 0.012)) / 4
    s = np.tanh(filt(s, [700, 5000], "band") * 3) * amp
    l, r = pan_lfo(s, 0.15, 0.35)
    add_st(l, r, pos(bar0), gain, rev=0.25, dly=0.35, b="10 Lead")


# ---- talking formant synth (the playful Dickster element, new form) ----
VOWELS = {"a": (800, 1150), "e": (400, 2000), "i": (300, 2500), "o": (450, 800), "u": (325, 700)}
TALK = [(0, "G2", "a"), (2, "G2", "o"), (3, "G3", "i"), (6, "G2", "a"), (8, "F2", "u"), (10, "G2", "e"),
        (11, "Ab2", "a"), (14, "G2", "o")]


def talk_bar(bar, gain=0.22, pan=-0.25):
    n = int(BAR * SR); sig = np.zeros(n)
    for st, nm, v in TALK:
        f = nr(nm); m = int(S16 * SR * 1.6); tt = t_(m)
        raw = saw(f, m) * np.minimum(1, tt / 0.004) * np.exp(-tt * 5)
        f1, f2 = VOWELS[v]
        s = filt(raw, [f1 * 0.8, f1 * 1.2], "band") * 2 + filt(raw, [f2 * 0.85, f2 * 1.15], "band") * 1.2
        a = int(st * S16 * SR); sig[a:a + m] += s[: n - a]
    add(np.tanh(sig * 2.5) * 0.5, pos(bar), gain, pan=pan, rev=0.12, dly=0.25, b="10 Lead")


# ---- new acid figure for the hypnotic sections (phrygian dominant, not the old riffs) ----
ACID_G = [(0, "G2", 1, 1), (1, "G2", 1, 0), (3, "G3", 1, 1), (4, "Ab2", 1, 0), (6, "G2", 1, 0), (7, "B2", 1, 1),
          (9, "G2", 1, 0), (10, "D3", 2, 1), (12, "G2", 1, 0), (13, "Ab3", 1, 1), (14, "G3", 1, 0), (15, "F3", 1, 0)]


def acid_g(bar, open_, gain=0.26):
    for st, nm, ln, acc in ACID_G:
        p = 0.55 * np.sin(2 * np.pi * (bar * 16 + st) / 48)
        add(acid_note(nr(nm), S16 * ln * 0.95, acc, open_), pos(bar, st / 4), gain, pan=p, rev=0.12, dly=0.3, b="08 Acid")


# ---- heat shimmer: flanged pad / sand wind ----
def flange(x, depth_ms=3.0, rate=0.15, mix=0.7):
    t = t_(len(x))
    d = (0.5 + 0.5 * np.sin(2 * np.pi * rate * t)) * depth_ms / 1000 * SR + 1
    idx = np.arange(len(x)) - d
    return x + mix * np.interp(idx, np.arange(len(x)), x, left=0)


def shimmer_pad(b0, b1, gain=0.3, slow=2):
    CH = [["G3", "B3", "D4"], ["Ab3", "C4", "Eb4"], ["G3", "B3", "D4"], ["F3", "Ab3", "C4"]]
    for i, b in enumerate(range(b0, b1, slow)):
        fs = [nr(x) for x in CH[i % 4]]; fs.append(fs[0] / 2)
        p = flange(pad_chord(fs, slow * BAR + 0.7), rate=0.2 + 0.05 * (i % 3))
        add(p, pos(b) - int(0.3 * SR), gain, pan=0.1 * (-1) ** i, rev=0.6, b="11 Pad & Drone")


def sand_wind(b0, b1, gain=0.18, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s; t = t_(n)
    w = vfilt(noise(n), lambda tm: 900 + 2600 * (0.5 + 0.5 * np.sin(2 * np.pi * tm / 7.3)), q=0.25, chunk=2048)
    env = np.minimum(1, t / 4)
    if fade_out: env *= np.clip((t[-1] - t) / 6, 0, 1)
    l, r = pan_lfo(w * env, 0.07, 0.8)
    add_st(l, r, s, gain, rev=0.25, b="14 Atmosphere")


def mirage_echo(sig, n_echo=5, beat_gap=0.75):
    """Echoes that drift down in pitch: the mirage."""
    out = np.zeros(len(sig) + int(n_echo * beat_gap * BEAT * SR) + SR)
    for k in range(n_echo + 1):
        r = 1 - 0.035 * k
        y = np.interp(np.arange(0, len(sig) - 1, r), np.arange(len(sig)), sig) * (0.6 ** k)
        a = int(k * beat_gap * BEAT * SR)
        out[a:a + len(y)] += y
    return out


def VOX(text, bar, beat=0, g=0.6, whisper=False, ps=0.82, robot=False, var=None, rev=0.5, dly=0.3, pan=0.0, stut=0, mirage=False):
    global VOICE_VAR
    old = VOICE_VAR
    if var: VOICE_VAR = var
    sig = voice(text, whisper=whisper, pitch_shift=ps, robot=robot)
    VOICE_VAR = old
    if stut: sig = stutter(sig, reps=stut)
    if mirage: sig = mirage_echo(sig)
    add(sig, pos(bar, beat), g, pan=pan, rev=rev, dly=dly, b="15 Vocals")

_NR.update({"A#": 10, "D#": 3})
# ======================= TEMPESTADE ELETRICA: new palette =======================
def _storm_kick():
    n = int(0.34 * SR); t = t_(n)
    f = 47 + 140 * np.exp(-t * 40) + 18 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8.5)
    click = filt(noise(n), [3000, 10000], "band") * np.exp(-t * 800) * 0.55
    return np.tanh((s + click) * 2.4) * 0.95
KICK = _storm_kick()

B1 = note_raw("B1")
ROOTS = {"Bm": note_raw("B1"), "G": note_raw("G1"), "Em": note_raw("E2"), "F#": note_raw("F#1")}
PROG = ["Bm", "G", "Em", "F#"]                               # i - VI - iv - V (harmonic minor)
CHORD_TONES = {"Bm": ["B", "D", "F#"], "G": ["G", "B", "D"], "Em": ["E", "G", "B"], "F#": ["F#", "A#", "C#"]}


def sbass(f, cut=1.0, dur16=0.9):
    """Rolling storm bass: detuned saws + sub, tight filter envelope."""
    n = int(S16 * SR * dur16); t = t_(n)
    raw = saw(f, n) * 0.4 + saw(f * 1.008, n) * 0.4 + np.sin(2 * np.pi * f * t) * 0.6
    fe = np.exp(-t * 50)
    s = filt(raw, 1300 * cut) * fe + filt(raw, 300 * cut) * (1 - fe)
    env = np.minimum(1, t / 0.0015) * np.exp(-t * 19); env[-60:] *= np.linspace(1, 0, 60)
    return np.tanh(s * env * 2.8) * 0.52


def bass_straight(bar, root, cut=1.0, gain=1.0, hyp=False):
    for beat in range(4):
        for s16 in (1, 2, 3):
            f = root
            if not hyp and bar % 4 == 3 and beat == 3 and s16 == 3: f = root * 2
            acc = 1.15 if s16 == 1 else 0.92 if s16 == 2 else 1.0
            add(sbass(f, cut), pos(bar, beat + s16 / 4), 0.85 * gain * acc, b="02 Bass")


def bass_triplet(bar, root, cut=1.0, gain=1.0):
    """Triplet rolling bass: kick, then two notes on the 2nd and 3rd triplet of each beat."""
    for beat in range(4):
        for k, tr in enumerate((1 / 3, 2 / 3)):
            f = root * (2 if (beat == 3 and k == 1 and bar % 2 == 1) else 1)
            add(sbass(f, cut, dur16=1.2), pos(bar, beat + tr), 0.85 * gain * (1.1 if k == 0 else 0.95), b="02 Bass")


def glass(f):
    n = int(0.4 * SR); t = t_(n)
    s = np.sin(2 * np.pi * f * t + 3 * np.exp(-t * 18) * np.sin(2 * np.pi * f * 2 * t))
    s += np.sin(2 * np.pi * f * 4.01 * t) * 0.15 * np.exp(-t * 25)
    return s * np.minimum(1, t / 0.001) * np.exp(-t * 9) * 0.4


ARP_SHAPE = [0, 1, 2, 3, 2, 4, 3, 5, 0, 2, 1, 3, 4, 3, 5, 6]


def chord_ladder(ch, base_oct=4):
    names = CHORD_TONES[ch]
    out = []
    for o in range(3):
        for nm in names:
            out.append(note_raw(f"{nm}{base_oct + o}"))
    return out


def glass_arp_bar(bar, ch, gain=0.16, cut=1.0, pan=0.3):
    lad = chord_ladder(ch)
    for i, k in enumerate(ARP_SHAPE):
        s = glass(lad[k])
        if cut < 1: s = filt(s, 600 + 7000 * cut)
        add(s, pos(bar, i / 4), gain, pan=pan * np.sin(np.pi * i / 4), rev=0.25, dly=0.35, b="12 Machine")


def storm_pad(b0, b1, gain=0.3):
    for i, b in enumerate(range(b0, b1)):
        ch = PROG[i % 4]
        fs = [note_raw(f"{nm}3") for nm in CHORD_TONES[ch]]; fs.append(fs[0] / 2)
        add(pad_chord(fs, BAR + 0.7), pos(b) - int(0.3 * SR), gain, rev=0.6, b="11 Pad & Drone")


# Avalon-style big gated hook (B harmonic minor), 4-bar cycle over the progression
HOOK = [[(0, 4, "F#5"), (4, 2, "D5"), (6, 2, "B4"), (8, 3, "C#5"), (11, 3, "D5"), (14, 2, "E5")],
        [(0, 4, "D5"), (4, 2, "B4"), (6, 2, "G4"), (8, 4, "B4"), (12, 4, "D5")],
        [(0, 3, "E5"), (3, 3, "G5"), (6, 2, "B5"), (8, 4, "G5"), (12, 2, "F#5"), (14, 2, "E5")],
        [(0, 4, "F#5"), (4, 4, "A#5"), (8, 6, "C#6"), (14, 2, "A#5")]]


def big_hook(bar0, nbars, gain=0.22, octave=1.0, gate=0.6, cut=6500):
    length = int(nbars * BAR * SR); ev = []
    for bb in range(nbars):
        for st, ln, nm in HOOK[bb % 4]:
            ev.append((int((bb * 16 + st) * S16 * SR), int(ln * S16 * SR * 0.95), note_raw(nm) * octave))
    l, r = supersaw_line(ev, length, cut=cut, gate_depth=gate)
    add_st(l, r, pos(bar0), gain, rev=0.3, dly=0.3, b="10 Lead")


ACID_B = [(0, "B2", 1, 1), (2, "B2", 1, 0), (3, "D3", 1, 0), (4, "B2", 1, 1), (6, "A#2", 1, 0), (7, "B2", 1, 0),
          (8, "F#3", 2, 1), (10, "B2", 1, 0), (11, "G3", 1, 1), (12, "F#3", 1, 0), (13, "B3", 1, 1), (14, "A#3", 1, 0),
          (15, "B2", 1, 0)]


def acid_b(bar, open_, gain=0.25):
    for st, nm, ln, acc in ACID_B:
        p = 0.6 * np.sin(2 * np.pi * (bar * 16 + st) / 40)
        add(acid_note(note_raw(nm), S16 * ln * 0.95, acc, open_), pos(bar, st / 4), gain, pan=p, rev=0.12, dly=0.3, b="08 Acid")


# ---- weather ----
def rain(b0, b1, gain=0.2, fade_out=False):
    s, e = pos(b0), pos(b1); n = e - s; t = t_(n)
    drops = (rng.random(n) < 45 / SR) * rng.uniform(0.2, 1, n)
    patter = filt(drops, [2200, 7000], "band", 4) * 6
    bed = filt(noise(n), [800, 6000], "band") * (0.25 + 0.1 * np.sin(2 * np.pi * 0.11 * t))
    env = np.minimum(1, t / 5)
    if fade_out: env *= np.clip((t[-1] - t) / 6, 0, 1)
    l, r = pan_lfo((patter + bed) * env, 0.04, 0.7)
    add_st(l, r, s, gain, rev=0.2, b="14 Atmosphere")


def thunder(dur=6.0):
    n = int(dur * SR); t = t_(n)
    brown = np.cumsum(noise(n)); brown -= filt(brown, 15)
    brown /= np.max(np.abs(brown)) + 1e-9
    rumble = filt(brown, 220) * (np.exp(-t * 0.9) * (1 + 0.6 * np.sin(2 * np.pi * 0.8 * t) ** 2))
    crack = filt(noise(n), 1500, "high") * np.exp(-t * 9) * 0.5
    s = (rumble * 1.6 + crack) * np.minimum(1, t / 0.03)
    return s / (np.max(np.abs(s)) + 1e-9) * 0.6


def lightning():
    n = int(0.35 * SR); t = t_(n)
    s = filt(noise(n), 3000, "high") * np.exp(-t * 18)
    s += np.sin(2 * np.pi * np.cumsum(np.geomspace(7000, 150, n)) / SR) * np.exp(-t * 10) * 0.6
    return s * 0.6


def strike(bar, beat=0, gain=0.3):
    add(lightning(), pos(bar, beat), gain, pan=rng.uniform(-0.7, 0.7), rev=0.5, dly=0.2, b="13 FX")
    add(thunder(), pos(bar, beat) + int(0.25 * SR), gain * 0.9, rev=0.4, b="14 Atmosphere")


def pitch_riser(b0, b1, gain=0.2):
    """Avalon-style epic riser: rising supersaw + noise, accelerating tremolo."""
    n = pos(b1) - pos(b0); t = t_(n)
    f = np.geomspace(110, 1760, n)
    s = sum(saw(f * (1 + d), n) for d in (-0.012, 0, 0.012)) / 3 + noise(n) * 0.25
    s = sweep(s, 400, 9000, "band")
    trem = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(np.geomspace(2, 16, n)) / SR))
    add(s * trem * np.linspace(0, 1, n) ** 2, pos(b0), gain, rev=0.35)


# ======================= ARRANGEMENT =======================
print("rendering arrangement...")
SWING = 0.035

# INTRO (0:00): rain on the roof, a distant strike, kick + percussion for the DJ
i0, i1 = START["intro"]
rain(i0, START["groove1"][0] + 8, gain=0.22)
strike(i0 + 2, gain=0.24)
for i, b in enumerate(range(i0, i1)):
    drums_bar(b, hats=i >= 8, shakers=i >= 4, gain=0.95)
    rims_bar(b, gain=0.07)
    bass_straight(b, B1, cut=0.3 + 0.045 * i, gain=0.7, hyp=True)
VOX("Here comes the storm.", i0 + 4, g=0.6, ps=0.8, rev=0.55, dly=0.4)

# GROOVE 1 (0:26): Burn in Noise - hypnotic one note, new acid, growls, thunder
g0, g1 = START["groove1"]
crash(g0)
for i, b in enumerate(range(g0, g1)):
    drums_bar(b, rides=i >= 16, toms=i >= 8, claps=i >= 8)
    bass_straight(b, B1, cut=1.15, hyp=True)
    acid_b(b, open_=min(1, i / 24), gain=0.24)
    if i >= 20 and i % 2 == 1: add(growl(B1 * 2, S16 * 3), pos(b, 1.75), 0.2, pan=0.4, rev=0.2, dly=0.3, b="09 Growl")
    if i % 8 == 4: swirl_at(b, 2, 300, 7000, 0.6, 0.15)
strike(g0 + 15, 3, gain=0.22)

# STORM BREAK (1:18): bass out, the glass arps reveal the chords, lightning
m0, m1 = START["stormbreak"]
for i, b in enumerate(range(m0, m1)):
    drums_bar(b, kick=i >= 6, hats=True, shakers=True, gain=0.85)
    glass_arp_bar(b, PROG[i % 4], gain=0.16, cut=0.4 + 0.08 * i)
storm_pad(m0, m1, gain=0.22)
strike(m0, gain=0.3)
VOX("Can you feel the pressure?", m0 + 2, g=0.6, ps=0.82, mirage=False, rev=0.5, dly=0.4)
riser(m1 - 2, m1, 600, 10000, 0.2)

# GROOVE 2 (1:31): Dickster - triplet bass, swing, stabs, elastic
h0, h1 = START["groove2"]
crash(h0)
SWING = 0.06
for i, b in enumerate(range(h0, h1)):
    drums_bar(b, rides=True, claps=True, toms=i >= 16)
    rims_bar(b, gain=0.1)
    bass_triplet(b, ROOTS[PROG[b % 4]] if i >= 16 else B1, cut=1.25)
    if i >= 8: stabs_bar(b, gain=0.15)
    if i >= 16: glass_arp_bar(b, PROG[b % 4], gain=0.1, cut=0.7, pan=-0.4)
    if i % 4 == 3: add(elastic(240, up=i % 8 == 3), pos(b, 3), 0.17, pan=0.7, rev=0.3, dly=0.4, b="13 FX")
VOX("Bounce!", h0 + 8, g=0.75, robot=True, ps=0.85, stut=3, rev=0.4, dly=0.45)
SWING = 0.035

# 3/4 BRIDGE (2:23): the dare - 8 measures of waltz time inside the storm
w0, w1 = START["bridge34"]
for m in range(8):
    base = m * 3                                  # beat offset from w0
    add(KICK, pos(w0, base), 0.9, b="01 Kick")
    for bt in (1, 2):
        add(sbass(ROOTS[PROG[(m // 2) % 4]], 0.9, dur16=2.5), pos(w0, base + bt), 0.75, b="02 Bass")
        add(hat(True), pos(w0, base + bt + 0.5), 0.14, rev=0.15, b="03 Hats")
    ch = PROG[(m // 2) % 4]
    lad = chord_ladder(ch)
    for k in range(9):                            # triplet-8th glass in 3/4
        add(glass(lad[[0, 2, 4, 3, 5, 4, 6, 5, 3][k]]), pos(w0, base + k / 3), 0.15, pan=0.5 * np.sin(k), rev=0.3, dly=0.3, b="12 Machine")
storm_pad(w0, w1, gain=0.18)
VOX("One... two... three...", w0, 0, g=0.55, whisper=True, ps=0.9, rev=0.6, dly=0.3)

# BUILD 1 (2:33): straight 4/4 again, Avalon-style lift
u0, u1 = START["build1"]
snare_roll(u0, u1, stop_beats=1)
for i, b in enumerate(range(u0, u1)):
    bass_straight(b, ROOTS[PROG[b % 4]], cut=0.55 + 0.07 * i, gain=0.85)
    glass_arp_bar(b, PROG[b % 4], gain=0.12, cut=0.5 + 0.06 * i)
    for beat in range(4 if b < u1 - 1 else 3): add(KICK, pos(b, beat), 0.9, b="01 Kick")
pitch_riser(u0, u1 - 0.25, 0.2)
VOX("Turn it up!", u1 - 1, 3.0, g=0.85, ps=0.85, rev=0.4, dly=0.45)

# DROP 1 (2:46): Avalon - big gated hook over the progression
d0, d1 = START["drop1"]
for b in (d0, d0 + 16): crash(b); strike(b, gain=0.18)
for i, b in enumerate(range(d0, d1)):
    drums_bar(b, rides=True, toms=True, claps=True)
    bass_straight(b, ROOTS[PROG[b % 4]], cut=1.35)
    glass_arp_bar(b, PROG[b % 4], gain=0.1, pan=-0.4)
    if i >= 16: acid_b(b, open_=0.6, gain=0.13)
    if i % 8 == 7: add(reverse_swell(BAR), pos(b), 0.15, rev=0.3)
big_hook(d0, 32, gain=0.22)
storm_pad(d0, d1, gain=0.1)

# BREAKDOWN (3:38): rain, pad, slow glass melody, female voice
k0, k1 = START["breakdown"]
rain(k0, k1, gain=0.2)
storm_pad(k0, k1, gain=0.32)
for i, b in enumerate(range(k0 + 4, k0 + 20)):
    for st, ln, nm in HOOK[i % 4][::2]:
        add(glass(note_raw(nm)) * 1.0, pos(b, st / 4), 0.2, pan=0.2, rev=0.7, dly=0.45, b="12 Machine")
strike(k0 + 1, gain=0.26); strike(k0 + 13, 2, gain=0.22)
VOX("Let the rain fall.", k0 + 6, g=0.6, ps=1.0, var="en-us+f3", rev=0.7, dly=0.4)
for i, b in enumerate(range(k0 + 16, k1)):
    acid_b(b, open_=0.1 + 0.09 * i, gain=0.12 + 0.015 * i)
    if i >= 4:
        for beat in range(4): add(filt(KICK, 180 + 350 * (i - 4)), pos(b, beat), 0.45, b="01 Kick")

# BUILD 2 (4:17): the big one
u0, u1 = START["build2"]
snare_roll(u0, u1, stop_beats=1)
for i, b in enumerate(range(u0, u1)):
    bass_straight(b, ROOTS[PROG[b % 4]], cut=0.5 + 0.08 * i, gain=0.85)
    for beat in range(4 if b < u1 - 1 else 3): add(KICK, pos(b, beat), 0.9, b="01 Kick")
pitch_riser(u0, u1 - 0.25, 0.24)
VOX("Lightning!", u1 - 1, 3.0, g=0.85, robot=True, ps=0.8, rev=0.4, dly=0.45)

# DROP 2 (4:30): everything - hook doubled, acid, glass, storm
e0, e1 = START["drop2"]
for b in (e0, e0 + 16, e0 + 32): crash(b); strike(b, gain=0.18)
for i, b in enumerate(range(e0, e1)):
    drums_bar(b, rides=True, toms=True, claps=True, metal=i >= 16)
    rims_bar(b, gain=0.08)
    bass_straight(b, ROOTS[PROG[b % 4]], cut=1.4)
    acid_b(b, open_=0.8 + 0.2 * np.sin(2 * np.pi * i / 16), gain=0.16)
    glass_arp_bar(b, PROG[b % 4], gain=0.09, pan=-0.4)
    if i >= 24 and i % 2 == 0: stabs_bar(b, gain=0.12)
    if i % 8 == 6: swirl_at(b, 2, 600, 10000, 1.2, 0.13)
    if i % 8 == 3: add(elastic(260, up=True), pos(b, 3), 0.16, pan=-0.7, rev=0.3, dly=0.4, b="13 FX")
big_hook(e0, 48, gain=0.21)
big_hook(e0 + 16, 32, gain=0.09, octave=2.0)

# TWIST (5:48): Burn in Noise darkness - one note, growls, stutter
x0, x1 = START["twist"]
for i, b in enumerate(range(x0, x1)):
    drums_bar(b, kick=i >= 2, hats=i >= 2, metal=True, gain=0.9)
    if i >= 2: bass_straight(b, B1, cut=1.0, hyp=True)
    add(growl(B1 * 2, S16 * 3), pos(b, 0.75), 0.24, pan=-0.3, rev=0.15, dly=0.25, b="09 Growl")
    add(growl(note_raw("C3"), BEAT * 0.9), pos(b, 3), 0.22, pan=0.4, rev=0.2, dly=0.4, b="09 Growl")
    acid_b(b, open_=0.5 + 0.06 * i, gain=0.26)
VOX("Thunder.", x0, 0, g=0.75, robot=True, ps=0.75, stut=4, rev=0.45, dly=0.4)
riser(x1 - 2, x1, 500, 11000, 0.22)

# DROP 3 (6:01): triplet bass under the hook - Dickster and Avalon at once
f0, f1 = START["drop3"]
for b in (f0, f0 + 16): crash(b)
SWING = 0.05
for i, b in enumerate(range(f0, f1)):
    drums_bar(b, rides=True, claps=True, metal=True)
    rims_bar(b, gain=0.09)
    bass_triplet(b, ROOTS[PROG[b % 4]], cut=1.35)
    acid_b(b, open_=0.95, gain=0.18)
    if i % 2 == 1: stabs_bar(b, gain=0.12)
big_hook(f0 + 8, 24, gain=0.2)
SWING = 0.035

# OUTRO (6:53): DJ friendly, rain returns, then one last strike and a hard stop
z0, z1 = START["outro"]
for i, b in enumerate(range(z0, z1 - 1)):
    if i < 12:
        drums_bar(b, rides=i < 8, claps=i < 8)
        bass_straight(b, B1, cut=1.2 - 0.05 * i, hyp=True)
        if i < 8: acid_b(b, open_=0.6 - 0.06 * i, gain=0.18 - 0.015 * i)
    else:
        drums_bar(b, rides=False, shakers=i < 20, gain=1 - (i - 12) / 20)
rain(z0 + 8, z1, gain=0.2)
VOX("Storm's over.", z0 + 18, g=0.6, ps=0.8, rev=0.6, dly=0.4)
add(KICK, pos(z1 - 1), 1.0, b="01 Kick")
add(lightning(), pos(z1 - 1), 0.45, rev=0.3, b="13 FX")
add(thunder(4.5), pos(z1 - 1), 0.5, rev=0.2, b="14 Atmosphere")
crash(z1 - 1, 0.3)

# ======================= MIX =======================
print("mixing...")
dt = int(0.75 * BEAT * SR)
irn = int(3.2 * SR); tir = t_(irn)
IR = []
for _ in range(2):
    ir = filt(noise(irn), 4500) * np.exp(-tir * 2.0); ir[: int(0.02 * SR)] = 0
    IR.append((ir / np.max(np.abs(ir)) * 0.025).astype(np.float32))
END = int((TOTAL_BARS * BAR + 3) * SR)
mixL = np.zeros(N, np.float32); mixR = np.zeros(N, np.float32)
for name in list(BUS):
    B = BUS.pop(name)
    mixL += B["L"]; mixR += B["R"]
    if np.any(B["DL"]):
        dl = filt(B["DL"], 3500).astype(np.float32)
        for k in range(1, 7):
            tgt = mixL if k % 2 else mixR
            tgt[k * dt:] += dl[:N - k * dt] * (0.5 ** k)
    if np.any(B["RV"]):
        mixL += oaconvolve(B["RV"], IR[0])[:N].astype(np.float32)
        mixR += oaconvolve(B["RV"], IR[1])[:N].astype(np.float32)
mix = np.stack([mixL, mixR], 1)[:END].astype(np.float64)
mix = filt(mix.T, 25, "high").T
mix /= np.percentile(np.abs(mix), 99.9) + 1e-9
mix = np.tanh(mix * 1.1) * 0.92
fade = int(2 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
here = os.path.dirname(os.path.abspath(__file__))
with tempfile.TemporaryDirectory() as d:
    w = os.path.join(d, "m.wav")
    sf.write(w, mix, SR, subtype="PCM_24")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", w, "-b:a", "320k",
                    os.path.join(here, "tempestade_eletrica.mp3")], check=True)
print("done", f"{len(mix) / SR:.1f}s")
