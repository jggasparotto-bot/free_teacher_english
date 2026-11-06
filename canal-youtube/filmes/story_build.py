"""Monta um episódio a partir do roteiro: falas (frase por frase), narração (Kokoro pf_dora) e story.json.
Uso: $LIB/.venv/bin/python story_build.py <roteiro.md> <pasta-do-episódio> "<título da próxima história>"
Saída: <ep>/lines.json, <ep>/voices/*.wav + dur.json, <ep>/story.json (cenas → falas, com o visual do roteiro)
"""
import sys, os, re, json, subprocess
LIB = os.environ.get('LIB', '/home/user/lemomo-ai/lemo-opuscar')
md, EP, NEXT = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]
src = open(md, encoding='utf-8').read()
title = src.splitlines()[0].split('—', 1)[1].strip()
ref = re.search(r'\*\*Referência:\*\* ([^·]+)', src).group(1).strip()
lesson_sum = re.search(r'\*\*Lição:\*\* (.+)', src).group(1).strip()

def quote(block):
    m = re.search(r'🎙️[^"]*"(.+)"\s*$', block, re.M)
    return m.group(1).strip() if m else None
def sentences(text):
    text = text.replace("'", '"')   # diálogo entre aspas simples → aspas duplas
    parts, cur, depth = [], '', False
    i = 0
    while i < len(text):
        c = text[i]; cur += c
        if c == '"': depth = not depth
        if c in '.!?' and (i + 1 == len(text) or text[i + 1] in ' "'):
            if i + 1 < len(text) and text[i + 1] == '"': cur += '"'; i += 1; depth = not depth
            if not (cur.endswith('...') and i + 1 < len(text) and text[i + 2:i + 3].islower()):
                parts.append(cur.strip()); cur = ''
        i += 1
    if cur.strip(): parts.append(cur.strip())
    out = []   # junta pedaços muito curtos e equilibra as aspas
    for p in parts:
        if out and (len(p) < 18 or len(out[-1]) < 18) and len(out[-1]) + len(p) < 120: out[-1] += ' ' + p
        else: out.append(p)
    fixed, carry = [], False
    for p in out:
        if carry: p = '"' + p
        if p.count('"') % 2: p += '"'; carry = True
        else: carry = False
        fixed.append(p)
    # aspas curvas
    res = []
    for p in fixed:
        q, o = '', True
        for ch in p:
            if ch == '"': q += '“' if o else '”'; o = not o
            else: q += ch
        res.append(q.replace('“”', '').strip())
    return [r for r in res if r]

scenes = []
gancho = re.search(r'## Gancho\n(.*?)\n## ', src, re.S).group(1)
scenes.append({'key': 'gancho', 'name': 'Gancho', 'visual': re.search(r'🎨 (.+)', gancho).group(1), 'text': quote(gancho)})
for m in re.finditer(r'### Cena (\d+) — (.+?)\n(.*?)(?=\n### |\n## )', src, re.S):
    blk = m.group(3)
    scenes.append({'key': f's{m.group(1)}', 'name': m.group(2).strip(), 'visual': re.search(r'🎨 \*\*Visual:\*\* (.+)', blk).group(1), 'text': quote(blk)})
lic = re.search(r'## Lição\n(.*?)\n## ', src, re.S).group(1)
per = re.search(r'## Pergunta para a família\n(.*?)\n## ', src, re.S).group(1)
scenes.append({'key': 'licao', 'name': 'Lição', 'visual': '', 'text': quote(lic) + ' ' + quote(per)})

lines, story = [], {'title': title, 'ref': ref, 'lesson': lesson_sum, 'next': NEXT, 'scenes': []}
lines.append({'id': 'vinheta', 'text': 'Bíblia em Traços!'})
lines.append({'id': 'titulo', 'text': title + '.'})
for sc in scenes:
    ids = []
    for k, s in enumerate(sentences(sc['text'])):
        lid = f"{sc['key']}_{k + 1}"; lines.append({'id': lid, 'text': s}); ids.append(lid)
    story['scenes'].append({'key': sc['key'], 'name': sc['name'], 'visual': sc['visual'], 'lines': ids})
lines.append({'id': 'fim', 'text': f'Inscreva-se no canal! Na próxima história: {NEXT}.'})
os.makedirs(EP, exist_ok=True)
tts = [{'id': l['id'], 'text': re.sub(r'[“”"]', '', l['text']).replace('...', ','), 'voice': 'pf_dora', 'speed': 0.88, 'lang': 'pt-br'} for l in lines]
json.dump(tts, open(os.path.join(EP, 'lines.json'), 'w'), ensure_ascii=False, indent=1)
story['subs'] = {l['id']: l['text'] for l in lines}
subprocess.run([os.path.join(LIB, '.venv/bin/python'), os.path.join(LIB, 'core/tts/tts.py'), os.path.join(EP, 'lines.json'), os.path.join(EP, 'voices')], check=True, capture_output=True)
story['dur'] = json.load(open(os.path.join(EP, 'voices', 'dur.json')))
json.dump(story, open(os.path.join(EP, 'story.json'), 'w'), ensure_ascii=False, indent=1)
tot = sum(story['dur'].values())
print(f'{title}: {len(lines)} falas, {len(story["scenes"])} cenas, voz {tot:.0f}s')
