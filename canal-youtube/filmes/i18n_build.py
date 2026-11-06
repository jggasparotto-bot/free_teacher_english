"""Versões em outros idiomas de um episódio: narração + legendas + i18n.js para o desenho.
Uso: $LIB/.venv/bin/python i18n_build.py <pasta-do-episódio> <idioma>     (idioma: en | es; textos em <ep>/i18n/<idioma>.json)
- As falas começam nos MESMOS instantes da versão em português (toda a animação, a música e os efeitos continuam sincronizados).
- Se uma fala traduzida não cabe no espaço até a próxima, a voz é sintetizada um pouco mais rápida (até 1,15×).
Saída: <ep>/voices_<idioma>/*.wav + dur.json, <ep>/i18n.js (todos os idiomas), <ep>/<nome>_<idioma>.srt
"""
import sys, os, re, json, glob
import numpy as np, soundfile as sf
LIB = os.environ.get('LIB', '/home/user/lemomo-ai/lemo-opuscar')
EP, LANG = os.path.abspath(sys.argv[1]), sys.argv[2]
src = open(os.path.join(EP, 'film.js'), encoding='utf-8').read()
starts = [(m.group(1), float(m.group(2)), not m.group(3)) for m in re.finditer(r"L\('(\w+)', ([\d.]+), '(?:[^'\\]|\\.)*'(, false)?\)", src)]
cfg = json.load(open(os.path.join(EP, 'i18n', LANG + '.json'), encoding='utf-8'))
from kokoro_onnx import Kokoro
k = Kokoro(os.path.join(LIB, 'core/tts/kokoro-v1.0.onnx'), os.path.join(LIB, 'core/tts/voices-v1.0.bin'))
def say(text):
    t = re.sub(r'[“”«»"]', '', text).replace('...', ',')
    return t.strip(' ,')
def synth(text, speed):
    a, sr = k.create(say(text), voice=cfg['voice'], speed=speed, lang=cfg['kokoro'])
    nz = np.where(np.abs(a) > np.abs(a).max() * .02)[0]
    return a[max(0, nz[0] - int(.03 * sr)): nz[-1] + int(.08 * sr)], sr
out = os.path.join(EP, 'voices_' + LANG); os.makedirs(out, exist_ok=True)
dur = {}
for i, (id_, t, sub) in enumerate(starts):
    nxt = starts[i + 1][1] if i + 1 < len(starts) else t + 8
    room = nxt - t - 0.3
    text = cfg['lines'][id_]
    speed = 0.88; a, sr = synth(text, speed)
    d = len(a) / sr
    if d > room:
        speed = min(1.15, 0.88 * d / room * 1.03); a, sr = synth(text, speed); d = len(a) / sr
    sf.write(os.path.join(out, id_ + '.wav'), a, sr); dur[id_] = round(d, 3)
    print(f'{id_:8s} {d:5.2f}s / espaço {room:5.2f}s  vel {speed:.2f}{"  ⚠ não coube" if d > room + 0.05 else ""}')
json.dump(dur, open(os.path.join(out, 'dur.json'), 'w'), indent=1)
# i18n.js com todos os idiomas já gerados
data = {}
for f in sorted(glob.glob(os.path.join(EP, 'i18n', '*.json'))):
    lg = os.path.basename(f)[:-5]; dj = os.path.join(EP, 'voices_' + lg, 'dur.json')
    if not os.path.exists(dj): continue
    c = json.load(open(f, encoding='utf-8')); data[lg] = {'lines': c['lines'], 'ui': c['ui'], 'dur': json.load(open(dj))}
open(os.path.join(EP, 'i18n.js'), 'w', encoding='utf-8').write(
    '// Gerado por i18n_build.py: textos, durações das falas e textos da página por idioma (?lang=en | es)\n'
    "export const LANG = new URLSearchParams(location.search).get('lang') || 'pt';\n"
    f'export const I18N = {json.dumps(data, ensure_ascii=False)};\n'
    'export const I = I18N[LANG] || null;\n'
    'export const U = (k, d) => (I && I.ui[k]) || d;\n')
# legendas
subs = [(t, dur[i], cfg['lines'][i]) for i, t, s in starts if s]
def ts(x): h, x = divmod(x, 3600); m, x = divmod(x, 60); s = int(x); ms = int(round((x - s) * 1000)); return f'{int(h):02d}:{int(m):02d}:{s:02d},{min(ms, 999):03d}'
name = os.path.basename(EP).split('-', 1)[1]
with open(os.path.join(EP, f'{name}_{LANG}.srt'), 'w', encoding='utf-8') as fh:
    for n, (t, d, text) in enumerate(subs):
        t0 = t - 0.1; t1 = max(t0 + 1.8, t + d + 0.7)
        if n + 1 < len(subs): t1 = min(t1, subs[n + 1][0] - 0.25)
        fh.write(f'{n + 1}\n{ts(t0)} --> {ts(t1)}\n{text}\n\n')
print('ok', LANG, len(dur), 'falas')
