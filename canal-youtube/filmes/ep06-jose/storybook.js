// Motor de episódios "Bíblia em Traços": título → cenas (páginas ilustradas desenhadas ao vivo, com virada de página entre elas)
// → lição → livro na mesa → "Próxima história". A linha do tempo sai da duração real de cada fala (story.json).
// Cada episódio fornece episode.js: { SCENES: { <chave>: { draw(api, lt, L, d), cam?(lt, L, d), extra?, fx?: [[lt, tipo, opts]] } }, titleArt?(api, t) }
import { layer, clear, line, fill, dab, text, handCircle, ellipse, smooth, CAM, BOIL, W, H, sx, sy } from './crayon.js';
import { group, clearGroup, part } from './rig.js';
import { heart, tree } from './chars.js';
import { mk, snap, drawBook, drawDesk, drawCrayons, turnAngle } from './book.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, track, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
export const pr = (t, a, b) => clamp((t - a) / (b - a));

const story = await (await fetch('story.json')).json();
const EPI = await import('./episode.js');
const TITLE = 7.0, TURN = 1.3, LEAD = 1.7, GAP = 0.9, TAIL = 1.1;
// —— linha do tempo ——
export const SEG = [];   // { key, t0, t1, L: [início local de cada fala], ids }
export const LINES = [];
let t = 0;
LINES.push({ id: 'vinheta', t: 1.2, d: story.dur.vinheta, text: 'Bíblia em Traços!', sub: false });
LINES.push({ id: 'titulo', t: 3.4, d: story.dur.titulo, text: story.title, sub: false });
t = TITLE;
for (const sc of story.scenes) {
  const def = EPI.SCENES[sc.key] || {};
  const L = []; let c = LEAD;
  for (const id of sc.lines) { L.push(c); LINES.push({ id, t: t + c, d: story.dur[id], text: story.subs[id], sub: true }); c += story.dur[id] + GAP; }
  const d = c - GAP + TAIL + (def.extra || 0);
  SEG.push({ key: sc.key, t0: t, t1: t + d, L, ids: sc.lines, def });
  t += d;
}
const ENDT = t, TURNE = [ENDT + 2.4, ENDT + 3.7];
LINES.push({ id: 'fim', t: ENDT + 3.9, d: story.dur.fim, text: story.subs.fim, sub: true });
export const DUR = +(ENDT + 16).toFixed(2);
export const SUBS = LINES.filter(l => l.sub).map((l, i, A) => { const t0 = l.t - 0.1; let t1 = Math.max(t0 + 1.8, l.t + l.d + 0.7); const nx = A[i + 1]; if (nx) t1 = Math.min(t1, nx.t - 0.25); return { t0, t1, text: l.text }; });

// —— eventos (som) ——
export const EV = [];
const ev = (tt, type, o = {}) => EV.push({ t: +tt.toFixed(3), type, ...o });
LINES.forEach(l => ev(l.t, 'voice', { id: l.id }));
ev(0, 'paper'); ev(0.3, 'write', { dur: 1.6, pan: -0.3 }); ev(2.6, 'write', { dur: 1.4, pan: 0.2 }); ev(4.2, 'write', { dur: 0.8 });
ev(0, 'cue', { id: 'titulo', mood: 'titulo' });
for (const s of SEG) {
  ev(s.t0, 'page', { dur: TURN });
  ev(s.t0 + TURN + 0.1, 'scribble', { dur: 1.4, pan: -0.3 }); ev(s.t0 + TURN + 0.5, 'scratch', { dur: 1.0, pan: 0.3 });
  ev(s.t0, 'cue', { id: s.key, dur: s.t1 - s.t0 });
  (s.def.fx || []).forEach(([lt, type, o]) => ev(s.t0 + (typeof lt === 'function' ? lt(s.L) : lt), type, o || {}));
}
ev(ENDT, 'room'); ev(TURNE[0], 'page', { dur: TURNE[1] - TURNE[0] }); ev(ENDT, 'cue', { id: 'fim' });
ev(ENDT + 4.0, 'write', { dur: 2.4 }); ev(ENDT + 6.6, 'write', { dur: 1.0 });

// —— camadas e API de desenho para as cenas ——
const BG = { f: layer(), l: layer() }, G = group(), F = group(), TOP = group(), FX = layer(), WASH = layer(), SUBK = layer(), SUBT = layer(), TXT = layer();
const DESK = { f: layer(), l: layer() }, OBJ = group(), book = mk();
const PG = { a: mk(), b: mk(), back: mk(), left: mk() };
export const api = {
  BG, G, F, TOP, FX, WASH, K, pr, text: (str, x, y, size, o = {}) => text(o.layer || FX, str, sx(x), sy(y), { size: size * CAM.s, font: o.font || 'Gochi Hand', col: o.col || K.ink, p: 1, stroke: o.font === 'Patrick Hand' ? 1 : 2, seed: o.seed || x * 0.1 + y * 0.03, reveal: o.reveal ?? 1 }),
  sky(y1, p = 0.5, g = 1) { if (g > 0) fill(BG.f, [[-80, -80], [W + 80, -80], [W + 80, y1], [-80, y1]], { col: K.sky, p, gap: 15, w: 14, ang: -0.25, seed: 60, boil: 0, over: 0, draw: g }); },
  ground(y, g = 1, col = K.green, seed = 80) { if (g <= 0) return; const top = []; for (let x = -80; x <= W + 80; x += 30) top.push([x, y + 16 * Math.sin(x / 210 + seed)]); part(G, [[-80, H + 80], ...top, [W + 80, H + 80]], { col, p: 0.8, gap: 12, w: 13, ang: 1.15, seed, boil: 0, draw: g, cross: true, crossP: 0.3 }, null); line(G.l, top, { w: 7, col: K.ink, seed: seed + 1, draw: Math.min(1, g * 2) }); },
  sea(y0, g = 1, t = 0, seed = 3, col = K.teal) { if (g <= 0) return; const top = []; for (let x = -80; x <= W + 80; x += 30) top.push([x, y0 + 14 * Math.sin(x / 80 + seed + t * 1.5)]); part(G, [[-80, H + 80], ...top, [W + 80, H + 80]], { col, p: 0.85, gap: 11, w: 12, ang: 0.15, seed: 90 + seed, boil: 0, draw: g, cross: true, crossP: 0.4 }, null); line(G.l, top, { w: 7, col: K.ink, seed: 91 + seed, draw: Math.min(1, g * 2) }); },
  star(C, x, y, r, s, col = K.yellow, lc = K.orange) { const pts = []; for (let k = 0; k <= 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5; const rr = k % 2 ? r * 0.45 : r; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); } part(C, pts, { col, p: 1, gap: 5, w: 7, seed: s }, { w: 5, col: lc, seed: s + 1 }); },
  O(C, pts, col, s, o = {}) { part(C, pts, col ? { col, p: o.p ?? 0.85, gap: o.gap ?? 10, w: o.w ?? 12, seed: s, ang: o.ang ?? 0.6, draw: o.fill ?? 1, cross: o.cross, crossP: 0.45 } : null, { w: o.lw ?? 7, col: o.lc || K.ink, seed: s + 1, draw: o.draw ?? 1 }); },
  wash(bands, t) { drawWashBands(bands, t); }, washColor: null,
};

// —— página de título ——
function titlePage(comp, t, camv, { subs = true } = {}) {
  [CAM.x, CAM.y, CAM.s] = camv; BOIL.amp = 1;
  [BG.f, BG.l, FX, SUBK, SUBT].forEach(clear); clearGroup(G); clearGroup(F); clearGroup(TOP);
  text(BG.l, 'Bíblia em Traços', sx(960), sy(300), { size: 90 * CAM.s, font: 'Patrick Hand', col: K.ink, reveal: pr(t, 0.3, 1.9), seed: 21, p: 0.95 });
  if (t > 1.9) line(BG.l, [[700, 330], [960, 338], [1220, 330]], { w: 9, col: K.red, seed: 22, draw: pr(t, 1.9, 2.4) });
  const big = story.title.length > 22 ? 120 : 150;
  text(BG.l, story.title, sx(960), sy(520), { size: big * CAM.s, font: 'Gochi Hand', col: K.ink, reveal: pr(t, 2.6, 4.0), seed: 23, p: 0.95, stroke: 2 });
  text(BG.l, story.ref, sx(960), sy(650), { size: 64 * CAM.s, font: 'Patrick Hand', col: K.ink, reveal: pr(t, 4.2, 5.0), seed: 24, p: 0.9 });
  if (EPI.titleArt) EPI.titleArt(api, t);
  if (subs) subTo(SUBK, SUBT, t);
  comp.paperCam(CAM.x, CAM.y, CAM.s); comp.begin();
  comp.crayon(BG.f.c); comp.crayon(BG.l.c); comp.group(G); comp.group(TOP); comp.crayon(FX.c); comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig: 0.3 });
}
// —— uma cena ——
function scenePage(comp, s, t, { subs = true, full = false } = {}) {
  const lt = t - s.t0, d = s.t1 - s.t0;
  const camv = full || !s.def.cam ? [960, 540, full ? 1 : lerp(1.0, 1.06, ss(lt / d))] : s.def.cam(lt, s.L, d);
  [CAM.x, CAM.y, CAM.s] = camv; BOIL.amp = s.def.calm ? 0.6 : 1;
  [BG.f, BG.l, FX, WASH, SUBK, SUBT].forEach(clear); clearGroup(G); clearGroup(F); clearGroup(TOP);
  api.washColor = null;
  if (s.def.draw) s.def.draw(api, lt, s.L, d);
  if (subs) subTo(SUBK, SUBT, t);
  comp.paperCam(CAM.x + hash(SEG.indexOf(s)) * 900, CAM.y, CAM.s); comp.begin();
  comp.crayon(BG.f.c); comp.crayon(BG.l.c);
  const go = [hash(BOIL.step) * 300, hash(BOIL.step + 7) * 300];
  comp.group(G, { goff: go });
  if (api.washColor) comp.wash(WASH.c, { color: api.washColor });
  comp.group(F, { goff: go }); comp.group(TOP, { goff: go }); comp.crayon(FX.c, { goff: go });
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig: 0.3, glow: s.def.glow ? s.def.glow(lt, s.L, d) : [0.5, 0.5, 0.1, 0] });
}
function drawWashBands(bands, t) {
  const g = WASH.g; g.save(); g.setTransform(CAM.s, 0, 0, CAM.s, W / 2 - CAM.x * CAM.s, H / 2 - CAM.y * CAM.s);
  for (const b of bands) {
    const u = clamp((t - b.t0) / (b.t1 - b.t0)); if (u <= 0) continue;
    const f = b.dir > 0 ? lerp(-300, W + 300, ss(u)) : lerp(W + 300, -300, ss(u));
    g.save(); g.beginPath();
    if (b.dir > 0) { g.moveTo(-400, b.y0 - 100); for (let y = b.y0 - 100; y <= b.y1 + 100; y += 20) g.lineTo(f + 60 * Math.sin((y - b.y0) / (b.y1 - b.y0) * Math.PI), y); g.lineTo(-400, b.y1 + 100); }
    else { g.moveTo(W + 400, b.y0 - 100); for (let y = b.y0 - 100; y <= b.y1 + 100; y += 20) g.lineTo(f - 60 * Math.sin((y - b.y0) / (b.y1 - b.y0) * Math.PI), y); g.lineTo(W + 400, b.y1 + 100); }
    g.closePath(); g.clip(); g.fillStyle = '#000'; g.globalAlpha = 0.8; g.fillRect(-400, b.y0, W + 800, b.y1 - b.y0);
    for (let i = 0; i < 18; i++) { const yy = lerp(b.y0, b.y1, hash(i + b.y0)); g.globalAlpha = 0.12; g.fillRect(-400, yy, W + 800, 6 + hash(i) * 20); }
    g.restore();
  }
  g.restore();
}
// —— final: livro na mesa → "Próxima história" ——
function leftPage(comp) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clear(TXT);
  const words = story.lesson.replace(/\.$/, '').split(' '); const half = Math.ceil(words.length / 2);
  const l1 = words.slice(0, half).join(' '), l2 = words.slice(half).join(' ') + '.';
  text(TXT, l1, 960, 470, { size: 70, col: K.ink, seed: 301, p: 0.95, stroke: 1.2 });
  text(TXT, l2, 960, 570, { size: 70, col: K.ink, seed: 302, p: 0.95, stroke: 1.2 });
  text(TXT, story.ref, 960, 700, { size: 56, col: K.ink, seed: 303, p: 0.8 });
  comp.paperCam(2000, 300, 1); comp.begin(); comp.crayon(TXT.c); comp.finish({ vig: 0, emb: 0.55 });
}
function endPage(comp, tt) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clear(TXT); clearGroup(OBJ);
  const t0 = ENDT + 4.0;
  text(TXT, 'Próxima história:', 960, 250, { size: 84, col: K.ink, seed: 311, p: 0.95, reveal: pr(tt, t0, t0 + 0.8) });
  const words = story.next.split(' '); const sz = story.next.length > 22 ? 110 : 140;
  const half = Math.ceil(words.length / 2);
  text(TXT, story.next.length > 16 ? words.slice(0, half).join(' ') : story.next, 960, 410, { size: sz, font: 'Gochi Hand', col: K.green, seed: 312, p: 1, stroke: 2, reveal: pr(tt, t0 + 0.8, t0 + 1.5) });
  if (story.next.length > 16) text(TXT, words.slice(half).join(' '), 960, 545, { size: sz, font: 'Gochi Hand', col: K.green, seed: 313, p: 1, stroke: 2, reveal: pr(tt, t0 + 1.5, t0 + 2.3) });
  text(TXT, 'Inscreva-se!', 960, 700, { size: 96, font: 'Gochi Hand', col: K.red, seed: 314, p: 1, stroke: 2, reveal: pr(tt, t0 + 2.6, t0 + 3.4) });
  const hg = pr(tt, t0 + 3.4, t0 + 3.8); if (hg > 0) heart(OBJ, { x: 1290, y: 680, s: 0.55 * eo(hg), seed: 1330 });
  comp.paperCam(4100, 700, 1); comp.begin(); comp.crayon(TXT.c); comp.group(OBJ); comp.finish({ vig: 0, emb: 0.55 });
}
const camD = track([[ENDT, [960, 540, 1]], [ENDT + 1.8, [0, 580, 0.46]], [ENDT + 2.4, [0, 580, 0.46]], [ENDT + 4.8, [960, 540, 0.9]], [DUR, [960, 540, 0.92]]]);
function deskFrame(comp, tt) {
  const [cx, cy, z] = camD(tt);
  const last = SEG[SEG.length - 1];
  scenePage(comp, last, last.t1 - 0.01, { subs: false, full: true }); snap(PG.a);
  leftPage(comp); snap(PG.left); endPage(comp, tt); snap(PG.b);
  comp.paperCam(700, 3100, 1); comp.begin(); comp.finish({ vig: 0, emb: 0.55 }); snap(PG.back);
  const k = pr(tt, ENDT, ENDT + 0.9);
  CAM.x = cx; CAM.y = cy; CAM.s = z;
  clear(DESK.f); clear(DESK.l); clearGroup(OBJ); clear(SUBK); clear(SUBT);
  drawDesk(DESK); drawCrayons(OBJ);
  drawBook(book.g, turnAngle(tt, TURNE[0], TURNE[1]), { left: PG.left, right: PG.a, next: PG.b, back: PG.back }, cx, cy, z, k);
  subTo(SUBK, SUBT, tt);
  comp.paperCam(cx, cy, z); comp.begin();
  if (k > 0) { comp.crayon(DESK.f.c); comp.crayon(DESK.l.c); }
  comp.image(book.c);
  if (k > 0) comp.group(OBJ, { goff: [hash(BOIL.step) * 200, 0] });
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig: 0.3 * k, emb: 0.55 * k, lamp: [0.42, 0.62, 0.62, 0.8 * k] });
}
// —— quadro ——
export function frame(comp, tt) {
  if (tt >= ENDT) return deskFrame(comp, tt);
  const i = SEG.findIndex(s => tt < s.t1);
  const s = SEG[i];
  if (!s) return titlePage(comp, tt, [960, 540, 1]);
  if (tt < s.t0) return titlePage(comp, tt, [960, 540, lerp(1.0, 1.05, tt / TITLE)]);
  if (tt < s.t0 + TURN) {   // virada de página: a página anterior vira e revela a cena nova
    const prev = SEG[i - 1];
    if (prev) scenePage(comp, prev, prev.t1 - 0.01, { subs: false, full: true }); else titlePage(comp, s.t0 - 0.01, [960, 540, 1], { subs: false });
    snap(PG.a);
    scenePage(comp, s, s.t0 + TURN, { subs: false, full: true }); snap(PG.b);
    comp.paperCam(700, 3100, 1); comp.begin(); comp.finish({ vig: 0, emb: 0.55 }); snap(PG.back);
    drawBook(book.g, turnAngle(tt, s.t0, s.t0 + TURN), { right: PG.a, next: PG.b, back: PG.back }, 960, 540, 1, 0);
    clear(SUBK); clear(SUBT); subTo(SUBK, SUBT, tt);
    comp.paperCam(960, 540, 1); comp.begin(); comp.image(book.c); comp.knock(SUBK.c); comp.crayon(SUBT.c); comp.finish({ vig: 0.3 });
    return;
  }
  scenePage(comp, s, tt);
}
// —— legendas ——
function paperPatch(g, cx, cy, hw, hh) {
  g.save(); g.fillStyle = '#000'; g.beginPath();
  for (let i = 0; i <= 60; i++) { const a = i / 60 * Math.PI * 2; const px = Math.cos(a), py = Math.sin(a); const sq = Math.pow(Math.abs(px), 0.3) * Math.sign(px); const n = 1 + 0.06 * Math.sin(a * 7 + 1.3) + 0.03 * Math.sin(a * 17); const X = cx + sq * hw * n, Y = cy + py * hh * n; i ? g.lineTo(X, Y) : g.moveTo(X, Y); }
  g.closePath(); g.fill(); g.restore();
}
function splitHalf(s) { const w = s.split(' '); let best = 1, bd = 1e9; for (let i = 1; i < w.length; i++) { const d = Math.abs(w.slice(0, i).join(' ').length - w.slice(i).join(' ').length); if (d < bd) { bd = d; best = i; } } return [w.slice(0, best).join(' '), w.slice(best).join(' ')]; }
export function subTo(SK, ST, tt) {
  const S = SUBS.find(s => tt >= s.t0 && tt < s.t1); if (!S) return;
  const rv = pr(tt, S.t0, S.t0 + 0.35);
  const g = SK.g; const mw = s => { g.save(); g.font = '400 54px "Patrick Hand"'; const m = g.measureText(s).width; g.restore(); return m; };
  const two = mw(S.text) > 1500, parts = two ? splitHalf(S.text) : [S.text];
  const w = Math.max(...parts.map(mw)), cy = two ? 972 : 1002;
  paperPatch(g, 960, cy, w / 2 + 46, two ? 76 : 44);
  parts.forEach((p, i) => text(ST, p, 960, cy + 18 + (two ? (i - 0.5) * 62 : 0), { size: 54, col: K.ink, reveal: clamp(rv * parts.length - i), seed: 11 + S.t0 * 3 + i, p: 1, stroke: 1.2 }));
}
