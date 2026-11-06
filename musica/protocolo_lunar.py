"""Protocolo Lunar - 8 min hypnotic night psytrance, synthesized from scratch with numpy.

Renders, in one pass:
  - the stereo master (WAV + MP3)
  - one stem per layer (24-bit FLAC, all starting at 0:00, effects printed)
  - MIDI files for every note-based layer and a drum MIDI (General MIDI drum map)
Output folder: protocolo_lunar_ableton/ next to this script.
"""
import os, subprocess, tempfile, wave, json
import numpy as np
import soundfile as sf
import mido
from scipy.signal import butter, sosfilt, oaconvolve

SR = 44100
BPM = 144
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(11)

SECTIONS = [("intro", 32), ("build1", 16), ("groove1", 32), ("midbreak", 8), ("groove2", 32),
            ("breakdown", 24), ("build2", 8), ("drop", 48), ("machine", 8), ("drop2", 40),
            ("outro", 40)]
START = {}
_b = 0
for name, n in SECTIONS:
    START[name] = (_b, _b + n)
    _b += n
TOTAL_BARS = _b                        # 288 bars = 8:00 at 144 BPM
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
    return 440 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) + 1) - 69) / 12)


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
        v = "pt-br+whisper" if whisper else "pt-br+m3"
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
                sw = 0.035 if s16 % 2 else 0.0
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

# ======================= ARRANGEMENT =======================
print("rendering arrangement...")

# INTRO (0:00) - night field, machine waking up
i0, i1 = START["intro"]
ambience(i0, START["build1"][1])
drone(i0, i1 + 4)
for b, nm in ((0, "D5"), (12, "A4"), (24, "D5")):
    add(bell(note(nm)), pos(i0 + b), 0.28, pan=0.3 - b * 0.02, rev=0.9, dly=0.35)
swirl_at(i0 + 8, 4, 200, 3000, 0.15, 0.25)
swirl_at(i0 + 20, 4, 300, 5000, 0.25, 0.2)
VO(voice("Sistema ativado.", robot=True, pitch_shift=0.78), i0 + 4, g=0.6, rev=0.5, dly=0.35)
for b in range(i0 + 16, i1):
    blips(b, gain=0.06 + 0.006 * (b - i0 - 16))
for b in range(i0 + 20, i1):
    for beat in range(4):
        add(filt(KICK, 150 + 40 * (b - i0 - 20)), pos(b, beat), 0.5, b="01 Kick")
        mdrum("kick", b, beat, 60)
VO(voice("Sinal detectado... origem desconhecida."), i0 + 26, g=0.55)

# BUILD 1 (0:53)
b0, b1 = START["build1"]
for i, b in enumerate(range(b0, b1)):
    fr = i / (b1 - b0)
    drums_bar(b, kick_cut=300 + 6000 * fr ** 2, hats=i >= 8, shakers=i >= 4, gain=0.7 + 0.3 * fr)
    bass_bar(b, cut_mult=0.35 + 0.65 * fr, gain=0.55 + 0.45 * fr)
riser(b1 - 4, b1)

# GROOVE 1 (1:20) - hypnotic, acid opening
g0, g1 = START["groove1"]
crash(g0)
for i, b in enumerate(range(g0, g1)):
    drums_bar(b, rides=i >= 16, toms=i >= 8)
    bass_bar(b)
    if i >= 8: acid_bar(b, open_=min(1, (i - 8) / 24), gain=0.26)
    if i % 8 == 4: swirl_at(b, 2, 300, 6000, 0.5, 0.18)
    if i % 8 == 7: add(zap(), pos(b, 3.5), 0.18, pan=0.7, dly=0.4)

# MID-BREAK (2:13)
m0, m1 = START["midbreak"]
for i, b in enumerate(range(m0, m1)):
    if i < 6: drums_bar(b, kick_cut=None if i >= 4 else 400, hats=i >= 4, gain=0.8)
    acid_bar(b, open_=0.4 + 0.08 * i, gain=0.32)
    blips(b, gain=0.12)
VO(voice("Ordem recebida.", robot=True, pitch_shift=0.76), m0 + 1, g=0.65, rev=0.5, dly=0.4)
riser(m1 - 2, m1, 600, 10000, 0.22)

# GROOVE 2 (2:27) - the machine takes over
h0, h1 = START["groove2"]
crash(h0)
for i, b in enumerate(range(h0, h1)):
    drums_bar(b, rides=True, toms=i < 16, metal=True, claps=i >= 8)
    bass_bar(b, cut_mult=1.1)
    growl_bar(b, gain=0.22 + 0.08 * min(1, i / 8))
    if i >= 4: machine_arp_bar(b, gain=0.16, cut=min(1, (i - 4) / 16))
    blips(b, gain=0.1)
    if i >= 16: acid_bar(b, open_=0.6, gain=0.16, pan_speed=0.5)
    if i % 8 == 6: swirl_at(b, 2, 400, 8000, 0.8, 0.15)
VO(stutter(voice("Obedeca.", robot=True, pitch_shift=0.74)), h0 + 16, g=0.7, rev=0.4, dly=0.45)

# BREAKDOWN (3:20)
k0, k1 = START["breakdown"]
pads(k0, k1)
slow_lead(k0 + 4, 16)
drone(k0, k1, gain=0.16)
VO(voice("Nada e real...", whisper=True, pitch_shift=0.88), k0 + 5, g=0.6, rev=0.7, dly=0.35)
VO(voice("so a frequencia.", whisper=True, pitch_shift=0.88), k0 + 9, g=0.6, rev=0.7, dly=0.35)
VO(voice("Voce agora pertence a maquina.", robot=True, pitch_shift=0.78), k0 + 14, g=0.55, rev=0.6, dly=0.4)
for i, b in enumerate(range(k0 + 12, k1)):
    blips(b, gain=0.05 + 0.005 * i)
for i, b in enumerate(range(k0 + 16, k1)):
    acid_bar(b, open_=0.1 + 0.06 * i, gain=0.14 + 0.02 * i)
    if i >= 4:
        for beat in range(4):
            add(filt(KICK, 160), pos(b, beat), 0.45, b="01 Kick"); mdrum("kick", b, beat, 60)

# BUILD 2 (4:00)
u0, u1 = START["build2"]
snare_roll(u0, u1)
for i, b in enumerate(range(u0, u1 - 1)):
    bass_bar(b, cut_mult=0.5 + 0.5 * i / 8, gain=0.8)
    acid_bar(b, open_=0.5 + 0.06 * i, gain=0.2)
    for beat in range(4):
        add(KICK, pos(b, beat), 0.9, b="01 Kick"); mdrum("kick", b, beat, 110)
for beat in (0, 1):
    add(KICK, pos(u1 - 1, beat), 0.9, b="01 Kick"); mdrum("kick", u1 - 1, beat, 110)
fall_riser(u0, u1 - 0.5)
VO(voice("Executar.", robot=True, pitch_shift=0.72), u1 - 1, 2.1, g=0.85, rev=0.6, dly=0.45)

# DROP (4:13)
d0, d1 = START["drop"]
for b in (d0, d0 + 16, d0 + 32): crash(b)
for i, b in enumerate(range(d0, d1)):
    drums_bar(b, rides=True, toms=True, claps=True, metal=i >= 24)
    bass_bar(b, cut_mult=1.2)
    acid_bar(b, open_=0.85 + 0.15 * np.sin(2 * np.pi * i / 16), gain=0.3, pan_speed=0.5)
    if i >= 8: growl_bar(b, gain=0.2)
    if i >= 24: machine_arp_bar(b, gain=0.12)
    if i % 8 == 6: swirl_at(b, 2, 500, 9000, 1.2, 0.15)
    if i % 4 == 3: add(zap(up=i % 8 == 3), pos(b, 3), 0.18, pan=-0.7 if i % 8 == 3 else 0.7, dly=0.4)
hook(d0 + 16, 16, gain=0.2)
hook(d0 + 32, 16, gain=0.12, octave=2.0, pan=-0.3)

# MACHINE BREAK (5:33) - the orders: stripped beat, stutters, commands
x0, x1 = START["machine"]
for i, b in enumerate(range(x0, x1)):
    drums_bar(b, kick=i >= 6, hats=i >= 2, shakers=True, metal=True, gain=0.85)
    machine_arp_bar(b, gain=0.2, cut=0.3 + 0.1 * i)
    blips(b, gain=0.16)
    if i >= 4: acid_bar(b, open_=0.3 + 0.1 * i, gain=0.2)
VO(stutter(voice("Dance.", robot=True, pitch_shift=0.72), reps=4), x0, 0, g=0.75, rev=0.45, dly=0.4, pan=-0.2)
VO(voice("Nao pense. Obedeca.", robot=True, pitch_shift=0.74), x0 + 2, 0, g=0.7, rev=0.5, dly=0.35, pan=0.2)
VO(stutter(voice("Dance.", robot=True, pitch_shift=0.72), reps=4), x0 + 4, 0, g=0.75, rev=0.45, dly=0.4, pan=0.2)
snare_roll(x1 - 2, x1, gain=0.9, stop_beats=1)
riser(x1 - 4, x1, 500, 11000, 0.24)

# DROP 2 (5:47) - peak: everything together
e0, e1 = START["drop2"]
for b in (e0, e0 + 16, e0 + 32): crash(b)
for i, b in enumerate(range(e0, e1)):
    drums_bar(b, rides=True, toms=True, claps=True, metal=True)
    bass_bar(b, cut_mult=1.25)
    acid_bar(b, open_=0.9 + 0.1 * np.sin(2 * np.pi * i / 8), gain=0.28, pan_speed=0.7)
    growl_bar(b, gain=0.22)
    machine_arp_bar(b, gain=0.13)
    blips(b, gain=0.08)
    if i % 8 == 6: swirl_at(b, 2, 600, 10000, 1.5, 0.15)
    if i % 4 == 3: add(zap(up=i % 8 == 3), pos(b, 3), 0.18, pan=-0.7 if i % 8 == 3 else 0.7, dly=0.4)
hook(e0 + 8, 16, gain=0.2)
hook(e0 + 8, 16, gain=0.1, octave=2.0, pan=-0.35)
VO(voice("Protocolo lunar... completo.", robot=True, pitch_shift=0.76), e1 - 4, g=0.6, rev=0.5, dly=0.45)

# OUTRO (6:53) - DJ friendly: groove, then drums, then kick, then night
o0, o1 = START["outro"]
for i, b in enumerate(range(o0, o1)):
    if i < 16:
        drums_bar(b, rides=i < 12, toms=i < 8, claps=i < 8, metal=i < 12)
        bass_bar(b, cut_mult=1.1 - 0.04 * i)
        if i < 10: acid_bar(b, open_=0.6 - i * 0.05, gain=0.22 - i * 0.015)
        if i < 8: machine_arp_bar(b, gain=0.1, cut=1 - i / 8)
    elif i < 24:
        drums_bar(b, rides=False, shakers=True)
    elif i < 32:
        drums_bar(b, shakers=False, hats=True, gain=1 - (i - 24) / 12)
ambience(o0 + 24, o1 + 2, fade_in=True, fade_out=True)
drone(o0 + 28, o1 + 2, gain=0.18, fade_out=True)
VO(voice("Fim do sinal."), o0 + 32, g=0.6, rev=0.7, dly=0.4)
add(bell(note("D5"), 6), pos(o1 - 3), 0.32, rev=0.9, dly=0.3)

# ======================= PROCESSING =======================
print("effects per stem...")
dt = int(0.75 * BEAT * SR)
irn = int(3.2 * SR); tir = t_(irn)
IR = []
for _ in range(2):
    ir = filt(noise(irn), 4000) * np.exp(-tir * 2.0); ir[: int(0.02 * SR)] = 0
    IR.append((ir / np.max(np.abs(ir)) * 0.025).astype(np.float32))

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "protocolo_lunar_ableton")
os.makedirs(os.path.join(out_dir, "Stems"), exist_ok=True)
os.makedirs(os.path.join(out_dir, "MIDI"), exist_ok=True)
END = int((TOTAL_BARS * BAR + 3) * SR)

stems = {}
for name in STEMS:
    if name not in BUS: continue
    B = BUS[name]
    L, R = B["L"], B["R"]
    if np.any(B["DL"]):
        dl = filt(B["DL"], 3200).astype(np.float32)
        for k in range(1, 7):
            tgt = L if k % 2 else R
            tgt[k * dt:] += dl[:N - k * dt] * (0.5 ** k)
    if np.any(B["RV"]):
        L += oaconvolve(B["RV"], IR[0])[:N].astype(np.float32)
        R += oaconvolve(B["RV"], IR[1])[:N].astype(np.float32)
    del B["RV"], B["DL"]
    st = np.stack([L, R], 1)[:END]
    st = filt(st.T, 25, "high").T.astype(np.float32)
    stems[name] = st
    del BUS[name]
    print("  ", name)

mix = sum(stems.values())
g = 1.0 / (np.percentile(np.abs(mix), 99.9) + 1e-9)
master = np.tanh(mix * g * 1.1) * 0.92
fade = int(2 * SR); master[-fade:] *= np.linspace(1, 0, fade)[:, None]

# stems: same gain as the master, -6 dB of headroom so they sum without clipping
stem_gain = g * 0.5
peak = max(np.max(np.abs(s)) for s in stems.values()) * stem_gain
if peak > 0.98: stem_gain *= 0.98 / peak
for name, st in stems.items():
    sf.write(os.path.join(out_dir, "Stems", f"{name}.flac"), st * stem_gain, SR, subtype="PCM_24")

master_wav = os.path.join(out_dir, "Protocolo Lunar - Master.wav")  # converted to FLAC for the package
sf.write(master_wav, master, SR, subtype="PCM_24")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master_wav, "-b:a", "320k",
                os.path.join(os.path.dirname(out_dir), "protocolo_lunar.mp3")], check=True)

# ---------------- MIDI export ----------------
TPB = 480
for track, notes in MIDI.items():
    mf = mido.MidiFile(ticks_per_beat=TPB)
    tr = mido.MidiTrack(); mf.tracks.append(tr)
    tr.append(mido.MetaMessage("track_name", name=track, time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    ch = 9 if track == "Drums" else 0
    ev = []
    for st, du, p, v in notes:
        a = int(round(st * TPB)); b = a + max(1, int(round(du * TPB)))
        ev.append((a, 1, p, v)); ev.append((b, 0, p, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    last = 0
    for t, on, p, v in ev:
        msg = "note_on" if on else "note_off"
        tr.append(mido.Message(msg, note=int(np.clip(p, 0, 127)), velocity=v, channel=ch, time=t - last))
        last = t
    mf.save(os.path.join(out_dir, "MIDI", f"{track}.mid"))

info = {"bpm": BPM, "key": "D phrygian", "bars": TOTAL_BARS, "sample_rate": SR,
        "sections": {k: {"bar_start": v[0] + 1, "time": "%d:%02d" % divmod(int(v[0] * BAR), 60)} for k, v in START.items()},
        "stem_gain_db": float(round(20 * np.log10(stem_gain / g), 1))}
json.dump(info, open(os.path.join(out_dir, "arrangement.json"), "w"), indent=2)
print("done:", out_dir, f"{len(master) / SR:.1f}s")
