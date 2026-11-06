"""Exporta as legendas do film.js (mesma regra: ≥1,8 s e ≥ fala + 0,7 s) para subs.json → srt.py."""
import re, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'film.js'), encoding='utf-8').read()
vd = dict((k, float(v)) for k, v in re.findall(r"(\w+): ([\d.]+)", src[src.index('const VD = {'):src.index('};', src.index('const VD = {'))]))
lines = []
for m in re.finditer(r"L\('(\w+)', ([\d.]+), '((?:[^'\\]|\\.)*)'(, false)?\)", src):
    if m.group(4): continue
    lines.append((float(m.group(2)), vd[m.group(1)], m.group(3)))
cues = []
for i, (t, d, text) in enumerate(lines):
    t0 = t - 0.1; t1 = max(t0 + 1.8, t + d + 0.7)
    if i + 1 < len(lines): t1 = min(t1, lines[i + 1][0] - 0.25)
    cues.append({'t0': round(t0, 3), 't1': round(t1, 3), 'text': text})
json.dump(cues, open(os.path.join(HERE, 'subs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(cues), 'legendas')
