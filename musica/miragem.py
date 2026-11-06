"""Miragem - full-on in the project house style (Burn in Noise x Regan Nano x Dickster),
with a new palette: G phrygian dominant, darbuka, Karplus-Strong oud, screamer lead,
talking formant synth, half-time mirage section and a semitone key change.
All sounds synthesized from scratch with numpy; only the final mix (MP3) is written."""
import os, subprocess, tempfile, wave, json
import numpy as np
import soundfile as sf
import mido
from scipy.signal import butter, sosfilt, oaconvolve

SR = 44100
BPM = 146
SWING = 0.035
TRANSPOSE = 5          # legacy D-based helpers -> G
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(43)

SECTIONS = [("intro", 16), ("groove1", 32), ("oud", 16), ("build1", 8), ("drop1", 32),
            ("halftime", 16), ("breakdown", 24), ("build2", 8), ("drop2", 48), ("twist", 8),
            ("drop3", 32), ("outro", 28)]
START = {}
_b = 0
for name, n in SECTIONS:
    START[name] = (_b, _b + n)
    _b += n
TOTAL_BARS = _b                        # 268 bars = 7:20 at 146 BPM
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

# ======================= ARRANGEMENT =======================
print("rendering arrangement...")
SWING = 0.045

# INTRO (0:00): straight in, DJ-style - kick, darbuka, filtered bass, sand wind
s0, s1 = START["intro"]
sand_wind(s0, s1 + 8, gain=0.14)
for i, b in enumerate(range(s0, s1)):
    drums_bar(b, hats=i >= 8, shakers=i >= 4, gain=0.95)
    darbuka_bar(b, gain=0.18 + 0.01 * i, fill=(i % 8 == 7))
    bass_line(b, BASS_HYP, cut=0.3 + 0.04 * i, gain=0.7)
VOX("Keep walking.", s0 + 8, g=0.55, ps=0.8, rev=0.5, dly=0.4)

# GROOVE 1 (0:26): Burn in Noise side - hypnotic one note, new acid figure opening, growls late
g0, g1 = START["groove1"]
crash(g0)
for i, b in enumerate(range(g0, g1)):
    drums_bar(b, rides=i >= 16, claps=i >= 8)
    darbuka_bar(b, gain=0.14, fill=(i % 8 == 7))
    bass_line(b, BASS_HYP, cut=1.1)
    acid_g(b, open_=min(1, i / 24), gain=0.24)
    if i >= 20 and i % 2 == 0: add(growl(nr("G2"), S16 * 3), pos(b, 2.5), 0.2, pan=-0.4, rev=0.2, dly=0.3, b="09 Growl")
    if i % 8 == 4: swirl_at(b, 2, 400, 7000, 0.6, 0.15)
VOX("The horizon is lying.", g0 + 12, g=0.55, ps=0.8, mirage=True)

# OUD SECTION (1:19): Dickster side - darbuka up front, swing, talking synth, the oud enters
o0, o1 = START["oud"]
SWING = 0.06
for i, b in enumerate(range(o0, o1)):
    drums_bar(b, hats=True, shakers=True, claps=True, gain=0.95)
    darbuka_bar(b, gain=0.26, fill=(i % 4 == 3))
    bass_line(b, BASS_MOVE, cut=1.2)
    talk_bar(b, gain=0.2)
    if i % 4 == 3: add(elastic(220, up=True), pos(b, 3), 0.17, pan=0.7, rev=0.3, dly=0.4, b="13 FX")
oud_bars(o0 + 8, 8, gain=0.2, cut=0.6)
add(zill(), pos(o0), 0.3, pan=0.5, rev=0.4)
SWING = 0.045

# BUILD 1 (1:45)
u0, u1 = START["build1"]
darbuka_roll(u0, u1)
for i, b in enumerate(range(u0, u1)):
    bass_line(b, BASS_MOVE, cut=0.6 + 0.07 * i, gain=0.85)
    oud_bars(b, 1, gain=0.12 + 0.01 * i, cut=0.5 + 0.06 * i)
    for beat in range(4 if b < u1 - 1 else 3): add(KICK, pos(b, beat), 0.9, b="01 Kick")
uplifter(u0, u1 - 0.25, 0.22)
VOX("Run!", u1 - 1, 3.0, g=0.85, robot=True, ps=0.85, rev=0.4, dly=0.45)

# DROP 1 (1:58): Regan side - screamer hook with bends over moving bass, oud answering
d0, d1 = START["drop1"]
for b in (d0, d0 + 16): crash(b); add(zill(), pos(b), 0.3, pan=-0.5, rev=0.4)
for i, b in enumerate(range(d0, d1)):
    drums_bar(b, rides=True, claps=True, toms=False)
    darbuka_bar(b, gain=0.13, fill=(i % 8 == 7))
    bass_line(b, BASS_MOVE, cut=1.3)
    if i >= 16: acid_g(b, open_=0.6, gain=0.13)
    if i % 8 == 7: add(reverse_swell(BAR), pos(b), 0.16, rev=0.3)
screamer(d0, 32, gain=0.2)
oud_bars(d0 + 8, 8, gain=0.13, oct_=2.0, pan=-0.35)
oud_bars(d0 + 24, 8, gain=0.13, oct_=2.0, pan=-0.35)

# HALF-TIME MIRAGE (2:50): the dare - the groove halves, everything shimmers
h0, h1 = START["halftime"]
for i, b in enumerate(range(h0, h1)):
    for beat in (0, 2):
        add(KICK, pos(b, beat), 0.85, b="01 Kick")
    add(clap(), pos(b, 3), 0.24, rev=0.5, b="06 Claps & Snares")
    add(hat(True), pos(b, 1.5), 0.15, rev=0.2, b="03 Hats"); add(hat(True), pos(b, 3.5), 0.15, rev=0.2, b="03 Hats")
    if i % 2 == 0:
        add(zbass(nr("G1"), 0.8) * 1.0, pos(b, 0.5), 0.8, b="02 Bass")
        add(zbass(nr("Ab1"), 0.8), pos(b, 2.75), 0.7, b="02 Bass")
    darbuka_bar(b, gain=0.1)
shimmer_pad(h0, h1, gain=0.22)
screamer(h0 + 8, 8, gain=0.12, oct_=0.5, pan=0.3)
VOX("Is it real?", h0 + 2, g=0.65, ps=0.8, stut=3, mirage=True)

# BREAKDOWN (3:16): free oud, shimmer, zills, whisper
k0, k1 = START["breakdown"]
shimmer_pad(k0, k1, gain=0.32)
sand_wind(k0, k1, gain=0.16)
for b in range(k0 + 2, k0 + 18, 2):
    oud_bars(b, 1, gain=0.18, pan=0.0)
for b in range(k0, k1, 4):
    add(zill(), pos(b, 1.5), 0.25, pan=0.6 * (-1) ** (b // 4), rev=0.7, dly=0.3)
VOX("Water... somewhere...", k0 + 4, g=0.6, whisper=True, ps=0.9, rev=0.7, dly=0.4)
VOX("Nothing is where it seems.", k0 + 12, g=0.55, ps=1.0, var="en-us+f3", rev=0.6, dly=0.4)
for i, b in enumerate(range(k0 + 16, k1)):
    acid_g(b, open_=0.1 + 0.08 * i, gain=0.12 + 0.015 * i)
    if i >= 4:
        for beat in range(4): add(filt(KICK, 180 + 300 * (i - 4)), pos(b, beat), 0.45, b="01 Kick")

# BUILD 2 (3:56)
u0, u1 = START["build2"]
darbuka_roll(u0, u1, gain=0.34)
snare_roll(u0, u1, gain=0.7, stop_beats=1)
for i, b in enumerate(range(u0, u1)):
    bass_line(b, BASS_HYP, cut=0.5 + 0.08 * i, gain=0.85)
    for beat in range(4 if b < u1 - 1 else 3): add(KICK, pos(b, beat), 0.9, b="01 Kick")
riser(u0 + 4, u1, 500, 11000, 0.22)
VOX("Higher.", u1 - 1, 3.0, g=0.85, robot=True, ps=0.8, rev=0.4, dly=0.45)

# DROP 2 (4:09): the key rises a semitone - everything, at full power
KEY = 2 ** (1 / 12)
e0, e1 = START["drop2"]
for b in (e0, e0 + 16, e0 + 32): crash(b); add(zill(), pos(b), 0.3, pan=0.5, rev=0.4)
for i, b in enumerate(range(e0, e1)):
    drums_bar(b, rides=True, claps=True, metal=i >= 16)
    darbuka_bar(b, gain=0.14, fill=(i % 8 == 7))
    bass_line(b, BASS_MOVE, cut=1.35)
    acid_g(b, open_=0.8 + 0.2 * np.sin(2 * np.pi * i / 16), gain=0.17)
    if i >= 16 and i % 2 == 1: talk_bar(b, gain=0.15)
    if i % 8 == 6: swirl_at(b, 2, 600, 10000, 1.2, 0.13)
    if i % 8 == 3: add(elastic(260, up=i % 16 == 3), pos(b, 3), 0.16, pan=-0.7, rev=0.3, dly=0.4, b="13 FX")
screamer(e0, 48, gain=0.21)
screamer(e0 + 32, 16, gain=0.09, oct_=2.0, pan=-0.3)
oud_bars(e0 + 16, 16, gain=0.12, oct_=2.0, pan=0.4)

# TWIST (5:28): talking synth and elastic stutters over a bare beat
x0, x1 = START["twist"]
for i, b in enumerate(range(x0, x1)):
    drums_bar(b, kick=i >= 2, hats=True, shakers=True, gain=0.9)
    darbuka_bar(b, gain=0.24, fill=True)
    talk_bar(b, gain=0.24, pan=0.0)
    if i >= 2: bass_line(b, BASS_HYP, cut=1.0)
VOX("Mirage.", x0 + 1, g=0.75, robot=True, ps=0.75, stut=4, mirage=True)
riser(x1 - 2, x1, 500, 11000, 0.22)

# DROP 3 (5:41): hypnotic and bright at once, ends on the hook
f0, f1 = START["drop3"]
for b in (f0, f0 + 16): crash(b)
for i, b in enumerate(range(f0, f1)):
    drums_bar(b, rides=True, claps=True, metal=True)
    darbuka_bar(b, gain=0.13, fill=(i % 8 == 7))
    bass_line(b, BASS_HYP if i < 16 else BASS_MOVE, cut=1.35)
    acid_g(b, open_=0.95, gain=0.2)
    if i % 2 == 0: add(growl(nr("G2"), S16 * 3), pos(b, 2.5), 0.18, pan=-0.4, rev=0.2, dly=0.3, b="09 Growl")
screamer(f0 + 16, 16, gain=0.2)
oud_bars(f0, 16, gain=0.12, oct_=2.0, pan=-0.4)
VOX("Nothing is where it seems.", f1 - 4, g=0.55, ps=1.0, var="en-us+f3", mirage=True)

# OUTRO (6:34): DJ friendly, back down the dune
z0, z1 = START["outro"]
KEY = 1.0
for i, b in enumerate(range(z0, z1)):
    if i < 16:
        drums_bar(b, rides=i < 8, claps=i < 8)
        darbuka_bar(b, gain=0.18, fill=(i % 8 == 7))
        bass_line(b, BASS_HYP, cut=1.2 - 0.05 * i)
        if i < 8: acid_g(b, open_=0.6 - 0.06 * i, gain=0.18 - 0.015 * i)
    elif i < 24:
        drums_bar(b, rides=False, shakers=i < 20, gain=1 - (i - 16) / 12)
        darbuka_bar(b, gain=0.16 - 0.01 * (i - 16))
sand_wind(z0 + 16, z1 + 2, gain=0.16, fade_out=True)
oud_bars(z0 + 20, 4, gain=0.12, cut=0.5)
VOX("Keep walking...", z0 + 22, g=0.55, ps=0.8, mirage=True)
add(zill(), pos(z1 - 2), 0.3, rev=0.8, dly=0.3)

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
                    os.path.join(here, "miragem.mp3")], check=True)
print("done", f"{len(mix) / SR:.1f}s")
