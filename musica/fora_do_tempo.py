"""Fora do Tempo - 7:30 night psytrance about time: clocks, alarms, chimes. Synthesized from scratch with numpy.

Every sound is synthesized here; no recorded samples are used. The chime melody is the
Westminster Quarters (1793, public domain).

Renders, in one pass:
  - the stereo master (WAV + MP3)
  - one stem per layer (24-bit FLAC, all starting at 0:00, effects printed)
  - MIDI files for every note-based layer and a drum MIDI (General MIDI drum map)
Output folder: fora_do_tempo_ableton/ next to this script.
"""
import os, subprocess, tempfile, wave, json
import numpy as np
import soundfile as sf
import mido
from scipy.signal import butter, sosfilt, oaconvolve

SR = 44100
BPM = 145
TRANSPOSE = 2          # D -> E
BEAT = 60 / BPM
S16 = BEAT / 4
BAR = BEAT * 4
rng = np.random.default_rng(23)

SECTIONS = [("intro", 32), ("build1", 16), ("groove1", 32), ("alarm", 8), ("groove2", 32),
            ("breakdown", 32), ("build2", 8), ("drop", 48), ("clockbreak", 8), ("drop2", 32),
            ("outro", 24)]
START = {}
_b = 0
for name, n in SECTIONS:
    START[name] = (_b, _b + n)
    _b += n
TOTAL_BARS = _b                        # 272 bars = 7:30 at 145 BPM
N = int((TOTAL_BARS * BAR + 5) * SR)

STEMS = ["01 Kick", "02 Bass", "03 Hats", "04 Shakers", "05 Ride", "06 Claps & Snares",
         "07 Toms & Metal", "08 Acid", "09 Growl", "10 Lead", "11 Pad & Drone", "12 Clocks & Alarms",
         "13 FX", "14 Atmosphere", "15 Vocals", "16 Chimes & Bells"]
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
        add(s, pos(bar, i / 4), gain, pan=0.5 * np.sin(np.pi * i / 8), rev=0.1, dly=0.25, b="12 Clocks & Alarms")
        mnote("Machine Arp", bar, i / 4, 0.18, f, vel=85)


BLIPS = {s: blip_burst(s) for s in (1, 2, 3, 4)}
def blips(bar, gain=0.16, seed=None):
    if bar % 2: return
    s = BLIPS[seed or (1 + (bar // 2) % 4)]
    l, r = pan_lfo(s, 0.3, 0.8)
    add_st(l, r, pos(bar), gain, rev=0.1, dly=0.2, b="12 Clocks & Alarms")


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

# ======================= TIME INSTRUMENTS =======================
def note_raw(name):
    names = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "Gb": 6, "G": 7, "Ab": 8, "A": 9,
             "Bb": 10, "B": 11, "C#": 1, "D#": 3, "F#": 6, "G#": 8, "A#": 10}
    return 440 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) + 1) - 69 + TRANSPOSE) / 12)


def tick(f=2600, dec=220):
    n = int(0.04 * SR); t = t_(n)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * dec) + filt(noise(n), 3000, "high") * np.exp(-t * 600) * 0.5
    return s * 0.6


def clocks(bar, layers, gain=0.14):
    """Polyrhythmic clocks: each layer = (step in beats, pitch, pan)."""
    for step, f, p in layers:
        k = 0
        beat = (bar * 4) % step   # keep each clock's phase continuous across bars
        beat = (step - beat) % step
        while beat < 4 - 1e-6:
            ff = f if k % 2 == 0 else f * 0.78         # tick ... tock
            add(tick(ff), pos(bar, beat), gain, pan=p, rev=0.15, b="12 Clocks & Alarms")
            mnote("Clocks", bar, beat, 0.1, ff, vel=90)
            beat += step; k += 1


CLK_SLOW = [(1.0, 2600, -0.4)]
CLK_POLY = [(1.0, 2600, -0.5), (0.75, 3300, 0.5), (2 / 3, 1900, -0.2), (1.5, 1500, 0.3)]
CLK_FULL = CLK_POLY + [(0.5, 4300, 0.8), (1.25, 2200, -0.8)]


def alarm(dur, f=2100, rate=19.0):
    """Old twin-bell alarm clock: a hammer rattling between two bells."""
    n = int(dur * SR); out = np.zeros(n)
    hit = int(SR / rate)
    m = int(0.09 * SR); tt = t_(m)
    for k in range(0, n - m, hit):
        ff = f * (1.19 if (k // hit) % 2 else 1.0) * (1 + rng.uniform(-0.004, 0.004))
        strike = np.sin(2 * np.pi * ff * tt + 1.5 * np.exp(-tt * 40) * np.sin(2 * np.pi * ff * 2.76 * tt))
        out[k:k + m] += strike * np.exp(-tt * 45)
    env = np.minimum(1, t_(n) / 0.02) * np.clip((dur - t_(n)) / 0.15, 0, 1)
    return filt(out * env, 900, "high") * 0.35


def alarms_burst(bar, beat, dur, n_clocks=4, gain=0.3):
    for i in range(n_clocks):
        f = rng.choice([1700, 2100, 2500, 2900, 3400])
        st = beat + i * rng.uniform(0.15, 0.6)
        add(alarm(dur - (st - beat) * BEAT, f), pos(bar, st), gain, pan=rng.uniform(-0.9, 0.9),
            rev=0.3, b="12 Clocks & Alarms")


def chime(f, dur=5.0):
    """Tubular bell: inharmonic partials, long decay."""
    n = int(dur * SR); t = t_(n)
    s = np.zeros(n)
    for r, a, d in ((1, 1, 0.9), (2.0, 0.6, 1.4), (2.76, 0.45, 2.0), (5.4, 0.25, 3.5), (8.93, 0.12, 5.0)):
        s += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d)
    s += filt(noise(n), 3000, "high") * np.exp(-t * 300) * 0.3
    return s * np.minimum(1, t / 0.002) * 0.35


def hour_bell(f, dur=7.0):
    n = int(dur * SR); t = t_(n)
    s = np.zeros(n)
    for r, a, d in ((0.5, 0.7, 0.35), (1, 1, 0.5), (1.19, 0.5, 0.8), (1.5, 0.35, 0.9), (2.0, 0.4, 1.2), (2.74, 0.25, 1.8)):
        s += a * np.sin(2 * np.pi * f * r * t + 0.3 * np.sin(2 * np.pi * 1.3 * t)) * np.exp(-t * d)
    return s * np.minimum(1, t / 0.003) * 0.35


# Westminster Quarters (1793, public domain), in E major
WESTMINSTER = [["G#4", "F#4", "E4", "B3"], ["E4", "G#4", "F#4", "B3"], ["E4", "F#4", "G#4", "E4"],
               ["G#4", "E4", "F#4", "B3"], ["B3", "F#4", "G#4", "E4"]]


def westminster(bar, phrases, gain=0.32, oct_=1.0, pan=0.25):
    b = bar
    for ph in phrases:
        for j, nm in enumerate(WESTMINSTER[ph]):
            f = note_raw(nm) * oct_
            dur_beats = 2 if j == 3 else 1
            add(chime(f), pos(b, j), gain, pan=pan, rev=0.7, dly=0.15, b="16 Chimes & Bells")
            mnote("Chimes", b, j, dur_beats, f, vel=95)
        b += 2


def midnight(bar, strikes=12, every_beats=2, gain=0.42):
    f = note_raw("E3")
    for k in range(strikes):
        bb = bar + (k * every_beats) // 4; beat = (k * every_beats) % 4
        add(hour_bell(f), pos(bb, beat), gain, rev=0.8, b="16 Chimes & Bells")
        mnote("Chimes", bb, beat, every_beats, f, vel=110)


def heartbeat(b0, b1, gain=0.5):
    n = int(0.18 * SR); t = t_(n)
    th = np.sin(2 * np.pi * (45 + 30 * np.exp(-t * 30)) * t) * np.exp(-t * 22)
    for b in range(b0, b1):
        for beat in (0, 2):
            add(th, pos(b, beat), gain, b="11 Pad & Drone")
            add(th * 0.7, pos(b, beat + 0.33), gain, b="11 Pad & Drone")


def accel_ticks(b0, b1, gain=0.16):
    """Ticks accelerating from one per beat to 32nds: time running out."""
    total = (b1 - b0) * 4
    beat = 0.0; k = 0
    while beat < total - 0.05:
        fr = beat / total
        step = 1.0 * (1 / 8) ** fr
        f = 2400 + 2400 * fr
        add(tick(f if k % 2 == 0 else f * 0.78), pos(b0, beat), gain * (0.6 + 0.6 * fr),
            pan=0.6 * np.sin(k), rev=0.15, b="12 Clocks & Alarms")
        beat += step; k += 1


def pads_major(b0, b1, gain=0.36):
    CH = [["E3", "G#3", "B3"], ["B2", "D#3", "F#3"], ["C#3", "E3", "G#3"], ["A2", "C#3", "E3"]]
    for i, b in enumerate(range(b0, b1, 2)):
        fs = [note_raw(n) for n in CH[i % 4]]
        fs.append(fs[0] / 2)
        add(pad_chord(fs, 2 * BAR + 0.7), pos(b) - int(0.3 * SR), gain, rev=0.6, b="11 Pad & Drone")
        for f in fs: mnote("Pad", b, 0, 8, f, vel=75)


def pads_dark(b0, b1, gain=0.36):
    CH = [["E3", "G3", "B3"], ["F3", "A3", "C4"]]
    for i, b in enumerate(range(b0, b1, 2)):
        fs = [note_raw(n) for n in CH[i % 2]]
        fs.append(fs[0] / 2)
        add(pad_chord(fs, 2 * BAR + 0.7), pos(b) - int(0.3 * SR), gain, rev=0.6, b="11 Pad & Drone")
        for f in fs: mnote("Pad", b, 0, 8, f, vel=75)


TAPE_STOPS = []   # (start_sample, length) applied to every stem before effects


# ======================= ARRANGEMENT =======================
print("rendering arrangement...")

# INTRO (0:00): a room full of clocks, a heartbeat, the quarter chimes
i0, i1 = START["intro"]
ambience(i0, START["build1"][1], level=0.6)
drone(i0, i1 + 4, gain=0.18)
for i, b in enumerate(range(i0, i1)):
    layers = CLK_SLOW if i < 4 else CLK_POLY[:2] if i < 10 else CLK_POLY if i < 24 else CLK_FULL
    clocks(b, layers, gain=0.08 + 0.004 * i)
heartbeat(i0 + 4, i0 + 20, gain=0.45)
westminster(i0 + 8, [0, 1, 2, 3], gain=0.3)
VO(voice("Tic... tac.", robot=True, pitch_shift=0.76), i0 + 2, g=0.6, rev=0.5, dly=0.35)
VO(voice("O tempo nao espera.", pitch_shift=0.8), i0 + 18, g=0.55, rev=0.5, dly=0.35)
swirl_at(i0 + 20, 4, 200, 4000, 0.2, 0.2)
for b in range(i0 + 24, i1):
    for beat in range(4):
        add(filt(KICK, 150 + 50 * (b - i0 - 24)), pos(b, beat), 0.5, b="01 Kick"); mdrum("kick", b, beat, 60)
alarms_burst(i1 - 1, 0, BAR, n_clocks=5, gain=0.26)

# BUILD 1 (0:53)
b0, b1 = START["build1"]
for i, b in enumerate(range(b0, b1)):
    fr = i / (b1 - b0)
    drums_bar(b, kick_cut=300 + 6000 * fr ** 2, hats=i >= 8, shakers=i >= 4, gain=0.7 + 0.3 * fr)
    bass_bar(b, cut_mult=0.35 + 0.65 * fr, gain=0.55 + 0.45 * fr)
    clocks(b, CLK_SLOW, gain=0.1)
riser(b1 - 4, b1)

# GROOVE 1 (1:19): hypnotic groove, the clock keeps time over the bass
g0, g1 = START["groove1"]
crash(g0); add(hour_bell(note_raw("E3")), pos(g0), 0.3, rev=0.7, b="16 Chimes & Bells")
for i, b in enumerate(range(g0, g1)):
    drums_bar(b, rides=i >= 16, toms=i >= 8)
    bass_bar(b)
    clocks(b, CLK_SLOW if i < 16 else CLK_POLY[:2], gain=0.09)
    if i >= 8: acid_bar(b, open_=min(1, (i - 8) / 24), gain=0.26)
    if i % 8 == 4: swirl_at(b, 2, 300, 6000, 0.5, 0.18)
    if i % 8 == 7: add(zap(), pos(b, 3.5), 0.18, pan=0.7, dly=0.4)

# ALARM BREAK (2:12): every alarm in the house goes off
a0, a1 = START["alarm"]
alarms_burst(a0, 0, BAR * 3, n_clocks=6, gain=0.3)
VO(voice("Acorde!", robot=True, pitch_shift=0.8), a0 + 1, 2, g=0.75, rev=0.4, dly=0.45)
for i, b in enumerate(range(a0, a1)):
    clocks(b, CLK_FULL, gain=0.12)
    if i >= 3: acid_bar(b, open_=0.3 + 0.1 * i, gain=0.26)
    if i >= 4: drums_bar(b, kick=i >= 6, hats=True, shakers=True, gain=0.8)
riser(a1 - 2, a1, 600, 10000, 0.22)

# GROOVE 2 (2:25): late, running - growls, clockwork arp, metal
h0, h1 = START["groove2"]
crash(h0)
for i, b in enumerate(range(h0, h1)):
    drums_bar(b, rides=True, toms=i < 16, metal=True, claps=i >= 8)
    bass_bar(b, cut_mult=1.1)
    growl_bar(b, gain=0.22 + 0.08 * min(1, i / 8))
    if i >= 4: machine_arp_bar(b, gain=0.15, cut=min(1, (i - 4) / 16))
    clocks(b, CLK_POLY, gain=0.08)
    if i >= 16: acid_bar(b, open_=0.6, gain=0.16, pan_speed=0.5)
    if i % 8 == 6: swirl_at(b, 2, 400, 8000, 0.8, 0.15)
VO(stutter(voice("Atrasado.", robot=True, pitch_shift=0.74)), h0 + 16, g=0.7, rev=0.4, dly=0.45)

# BREAKDOWN (3:18): the beat falls away, time slows - major key, chimes, then midnight
k0, k1 = START["breakdown"]
heartbeat(k0, k0 + 16, gain=0.4)
pads_major(k0, k0 + 16)
westminster(k0 + 4, [1, 2], gain=0.3)
westminster(k0 + 10, [3, 4], gain=0.3, oct_=0.5, pan=-0.25)
VO(voice("Quanto tempo voce ainda tem?", whisper=True, pitch_shift=0.88), k0 + 2, g=0.6, rev=0.7, dly=0.35)
VO(voice("Cada segundo... uma batida.", whisper=True, pitch_shift=0.88), k0 + 8, g=0.6, rev=0.7, dly=0.35)
pads_dark(k0 + 16, k1)
drone(k0 + 16, k1, gain=0.16)
midnight(k0 + 18, strikes=12, every_beats=2)
for i, b in enumerate(range(k0 + 16, k1)):
    clocks(b, CLK_SLOW, gain=0.07 + 0.01 * i)
    if i >= 8: acid_bar(b, open_=0.1 + 0.07 * (i - 8), gain=0.16 + 0.02 * (i - 8))
    if i >= 12:
        for beat in range(4):
            add(filt(KICK, 160), pos(b, beat), 0.45, b="01 Kick"); mdrum("kick", b, beat, 60)

# BUILD 2 (4:11): ticks accelerate, then the tape stops
u0, u1 = START["build2"]
snare_roll(u0, u1, stop_beats=1)
accel_ticks(u0, u1 - 0.25)
for i, b in enumerate(range(u0, u1)):
    bass_bar(b, cut_mult=0.5 + 0.5 * i / 8, gain=0.8)
    acid_bar(b, open_=0.5 + 0.06 * i, gain=0.2)
    for beat in range(4):
        add(KICK, pos(b, beat), 0.9, b="01 Kick"); mdrum("kick", b, beat, 110)
TAPE_STOPS.append((pos(u1 - 1, 2), pos(u1) - pos(u1 - 1, 2)))
fall_riser(u0, u1 - 0.5)
VO(voice("Zero.", robot=True, pitch_shift=0.7), u1 - 1, 2.6, g=0.85, rev=0.6, dly=0.45)

# DROP (4:25)
d0, d1 = START["drop"]
for b in (d0, d0 + 16, d0 + 32):
    crash(b); add(hour_bell(note_raw("E3")), pos(b), 0.3, rev=0.7, b="16 Chimes & Bells")
for i, b in enumerate(range(d0, d1)):
    drums_bar(b, rides=True, toms=True, claps=True, metal=i >= 24)
    bass_bar(b, cut_mult=1.2)
    acid_bar(b, open_=0.85 + 0.15 * np.sin(2 * np.pi * i / 16), gain=0.3, pan_speed=0.5)
    clocks(b, CLK_SLOW, gain=0.08)
    if i >= 8: growl_bar(b, gain=0.2)
    if i >= 24: machine_arp_bar(b, gain=0.12)
    if i % 8 == 6: swirl_at(b, 2, 500, 9000, 1.2, 0.15)
    if i % 4 == 3: add(zap(up=i % 8 == 3), pos(b, 3), 0.18, pan=-0.7 if i % 8 == 3 else 0.7, dly=0.4)
hook(d0 + 16, 16, gain=0.2)
hook(d0 + 32, 16, gain=0.12, octave=2.0, pan=-0.3)

# CLOCK BREAK (5:44): only clocks and the voice, polyrhythms colliding
x0, x1 = START["clockbreak"]
for i, b in enumerate(range(x0, x1)):
    clocks(b, CLK_FULL, gain=0.13)
    drums_bar(b, kick=i >= 6, hats=False, shakers=i >= 2, metal=True, gain=0.85)
    if i >= 4: acid_bar(b, open_=0.3 + 0.1 * i, gain=0.2)
VO(stutter(voice("Tic tac.", robot=True, pitch_shift=0.72), reps=4), x0, 0, g=0.75, rev=0.45, dly=0.4, pan=-0.2)
VO(voice("O relogio nao para.", robot=True, pitch_shift=0.74), x0 + 2, 0, g=0.7, rev=0.5, dly=0.35, pan=0.2)
VO(stutter(voice("Tic tac.", robot=True, pitch_shift=0.72), reps=4), x0 + 4, 0, g=0.75, rev=0.45, dly=0.4, pan=0.2)
alarms_burst(x1 - 1, 0, BAR, n_clocks=6, gain=0.28)
snare_roll(x1 - 2, x1, gain=0.9, stop_beats=1)

# DROP 2 (5:58): peak
e0, e1 = START["drop2"]
for b in (e0, e0 + 16):
    crash(b); add(hour_bell(note_raw("E3")), pos(b), 0.3, rev=0.7, b="16 Chimes & Bells")
for i, b in enumerate(range(e0, e1)):
    drums_bar(b, rides=True, toms=True, claps=True, metal=True)
    bass_bar(b, cut_mult=1.25)
    acid_bar(b, open_=0.9 + 0.1 * np.sin(2 * np.pi * i / 8), gain=0.28, pan_speed=0.7)
    growl_bar(b, gain=0.22)
    machine_arp_bar(b, gain=0.12)
    clocks(b, CLK_POLY[:2], gain=0.07)
    if i % 8 == 6: swirl_at(b, 2, 600, 10000, 1.5, 0.15)
    if i % 4 == 3: add(zap(up=i % 8 == 3), pos(b, 3), 0.18, pan=-0.7 if i % 8 == 3 else 0.7, dly=0.4)
hook(e0 + 8, 16, gain=0.2)
hook(e0 + 8, 16, gain=0.1, octave=2.0, pan=-0.35)
VO(voice("Fora do tempo.", robot=True, pitch_shift=0.76), e1 - 4, g=0.65, rev=0.5, dly=0.45)

# OUTRO (6:51): groove, drums, then one clock left ticking
o0, o1 = START["outro"]
for i, b in enumerate(range(o0, o1)):
    if i < 8:
        drums_bar(b, rides=i < 6, toms=i < 4, claps=i < 4, metal=i < 6)
        bass_bar(b, cut_mult=1.1 - 0.06 * i)
        if i < 6: acid_bar(b, open_=0.6 - i * 0.08, gain=0.2 - i * 0.02)
    elif i < 16:
        drums_bar(b, rides=False, shakers=i < 12, gain=1 - (i - 8) / 12)
    clocks(b, CLK_SLOW, gain=0.09)
ambience(o0 + 12, o1 + 2, level=0.6, fade_in=True, fade_out=True)
drone(o0 + 14, o1 + 2, gain=0.16, fade_out=True)
westminster(o0 + 16, [4], gain=0.28)
VO(voice("Fim do tempo..."), o0 + 19, g=0.6, rev=0.7, dly=0.4)
add(hour_bell(note_raw("E3"), 7), pos(o1 - 3), 0.38, rev=0.9, b="16 Chimes & Bells")

# tape stop: playback slows to a halt
for s0, ln in TAPE_STOPS:
    sp = np.linspace(1, 0, ln) ** 1.5
    idx = s0 + np.cumsum(sp)
    for nm_, B in BUS.items():
        if nm_ == "15 Vocals": continue
        for k in ("L", "R", "RV", "DL"):
            x = B[k]
            seg = np.interp(idx, np.arange(s0, s0 + ln + 2), x[s0:s0 + ln + 2])
            x[s0:s0 + ln] = seg * np.linspace(1, 0.0, ln) ** 0.5

# ======================= PROCESSING =======================
print("effects per stem...")
dt = int(0.75 * BEAT * SR)
irn = int(3.2 * SR); tir = t_(irn)
IR = []
for _ in range(2):
    ir = filt(noise(irn), 4000) * np.exp(-tir * 2.0); ir[: int(0.02 * SR)] = 0
    IR.append((ir / np.max(np.abs(ir)) * 0.025).astype(np.float32))

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fora_do_tempo_ableton")
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

master_wav = os.path.join(out_dir, "Fora do Tempo - Master.flac")
sf.write(master_wav, master, SR, subtype="PCM_24")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", master_wav, "-b:a", "320k",
                os.path.join(os.path.dirname(out_dir), "fora_do_tempo.mp3")], check=True)

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

info = {"bpm": BPM, "key": "E phrygian (breakdown in E major)", "bars": TOTAL_BARS, "sample_rate": SR,
        "sections": {k: {"bar_start": v[0] + 1, "time": "%d:%02d" % divmod(int(v[0] * BAR), 60)} for k, v in START.items()},
        "stem_gain_db": float(round(20 * np.log10(stem_gain / g), 1))}
json.dump(info, open(os.path.join(out_dir, "arrangement.json"), "w"), indent=2)
print("done:", out_dir, f"{len(master) / SR:.1f}s")
