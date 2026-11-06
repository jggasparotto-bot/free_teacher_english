// Arte da marca "Bíblia em Traços" — desenhada no mesmo motor de giz de cera dos episódios.
// Cada página = uma imagem no tamanho exato da plataforma (?page=...&w=...&h=...).
import { layer, clear, line, fill, dab, text, handCircle, ellipse, smooth, CAM, BOIL, W, H } from './crayon.js';
import { group, clearGroup, part } from './rig.js';
import { person, sheep, rabbit, lion, elephant, fish, bird, sun, moon, heart, cloud, tree, flower, serpent, fruit, bush } from './chars.js';
import { PAL } from './pal.js';
import { hash, mulberry } from '/core/lib.js';
const K = PAL.crayon;
const BG = { f: layer(), l: layer() }, G = group(), TOP = group(), TX = layer(), WASH = layer(), TK = layer();
const OUT = { fill: 0 };   // só contorno (página de colorir)

function patch(L, cx, cy, hw, hh) {   // retalho de papel limpo (knock) atrás de um texto
  const g = L.g; g.save(); g.fillStyle = '#000'; g.beginPath();
  for (let i = 0; i <= 60; i++) { const a = i / 60 * Math.PI * 2; const px = Math.cos(a), py = Math.sin(a); const sq = Math.pow(Math.abs(px), 0.3) * Math.sign(px); const n = 1 + 0.06 * Math.sin(a * 7 + 1.3) + 0.03 * Math.sin(a * 17); const X = cx + sq * hw * n, Y = cy + py * hh * n; i ? g.lineTo(X, Y) : g.moveTo(X, Y); }
  g.closePath(); g.fill(); g.restore();
}
const T = (str, x, y, size, o = {}) => text(TX, str, x, y, { size, font: o.font || 'Gochi Hand', col: o.col || K.ink, p: 1, stroke: o.stroke ?? (o.font === 'Patrick Hand' ? 1 : 2), seed: o.seed || (x * 0.13 + y * 0.07), align: o.align });
function sky(x0, y0, x1, y1, p = 0.5) { fill(BG.f, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], { col: K.sky, p, gap: 15, w: 14, ang: -0.25, seed: 60, boil: 0, over: 0 }); }
function hills(yTop, x0 = -60, x1 = W + 60, amp = 30, seed = 80) {
  const top = []; for (let x = x0; x <= x1; x += 30) top.push([x, yTop + amp * Math.sin(x / 260 + seed) + amp * 0.4 * Math.sin(x / 90)]);
  part(G, [[x0, H + 60], ...top, [x1, H + 60]], { col: K.green, p: 0.82, gap: 12, w: 13, ang: 1.15, seed, boil: 0, cross: true, crossP: 0.35 }, null);
  line(G.l, top, { w: 7, col: K.ink, seed: seed + 1 });
}
function seaBand(yTop, x0, x1) {
  const top = []; for (let x = x0; x <= x1; x += 30) top.push([x, yTop + 10 * Math.sin(x * 0.01)]);
  fill(BG.f, [...top, [x1, H + 60], [x0, H + 60]], { col: K.teal, p: 0.8, gap: 11, w: 12, ang: 0.15, seed: 61, boil: 0, cross: true, crossP: 0.45, over: 0 });
  line(BG.l, top, { w: 6, col: K.ink, p: 0.8, seed: 62 });
}
function starsWax(n, y1, seed = 9, avoid = () => false) {
  const R = mulberry(seed); const out = [];
  for (let k = 0; out.length < n && k < n * 40; k++) { const x = R() * W, y = R() * y1; if (avoid(x, y) || out.some(([a, b]) => Math.hypot(a - x, b - y) < 70)) continue; out.push([x, y]); }
  out.forEach(([x, y], i) => { const r = 8 + 10 * hash(i + seed); const pts = []; for (let k = 0; k <= 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5; const rr = k % 2 ? r * 0.45 : r; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); } fill(BG.f, pts, { col: K.white, p: 1, gap: 3, w: 5, over: 1, seed: 300 + i }); });
}
function washAll(y0, y1) { const g = WASH.g; g.save(); g.fillStyle = '#000'; g.globalAlpha = 0.82; g.fillRect(-20, y0, W + 40, y1 - y0); g.restore(); }
function crayonStick(C, x, y, a, col, len, sd) {
  const r = 46, X = pts => pts.map(([px, py]) => [x + px * Math.cos(a) - py * Math.sin(a), y + px * Math.sin(a) + py * Math.cos(a)]);
  const body = [[-len * 0.5, -r], [len * 0.5, -r], [len * 0.5 + 70, -r * 0.3], [len * 0.5 + 84, 0], [len * 0.5 + 70, r * 0.3], [len * 0.5, r], [-len * 0.5, r]];
  part(C, X(body), { col, p: 0.95, gap: 7, w: 9, ang: a + 1.5, seed: sd }, { w: 6, seed: sd + 1, col: K.ink });
  const wr = [[-len * 0.5, -r - 3], [len * 0.28, -r - 3], [len * 0.28, r + 3], [-len * 0.5, r + 3]];
  part(C, X(wr), { col, p: 0.7, gap: 6, w: 8, ang: a, seed: sd + 2 }, { w: 5, seed: sd + 3, col: K.ink });
  [-len * 0.38, len * 0.18].forEach((u, i) => fill(C.f, X([[u, -r - 3], [u + 26, -r - 3], [u + 26, r + 3], [u, r + 3]]), { col: K.ink, p: 0.8, gap: 4, w: 6, seed: sd + 4 + i }));
}
function openBook(C, cx, cy, s, sd = 3000) {
  const L = [[cx, cy + 20 * s], [cx - 60 * s, cy - 10 * s], [cx - 180 * s, cy - 14 * s], [cx - 250 * s, cy + 6 * s], [cx - 250 * s, cy + 150 * s], [cx - 180 * s, cy + 132 * s], [cx - 60 * s, cy + 138 * s], [cx, cy + 170 * s]];
  const R = L.map(([x, y]) => [2 * cx - x, y]);
  part(C, smooth(L, 4, true), { col: K.white, p: 1, gap: 7, w: 9, seed: sd }, { w: 7, seed: sd + 1, col: K.ink });
  part(C, smooth(R, 4, true), { col: K.white, p: 1, gap: 7, w: 9, seed: sd + 2 }, { w: 7, seed: sd + 3, col: K.ink });
  line(C.l, [[cx, cy + 20 * s], [cx, cy + 170 * s]], { w: 6, col: K.ink, seed: sd + 4 });
  for (let i = 0; i < 3; i++) { line(C.l, [[cx - 210 * s, cy + (30 + i * 32) * s], [cx - 50 * s, cy + (34 + i * 32) * s]], { w: 4, col: K.sky, p: 0.9, seed: sd + 10 + i }); line(C.l, [[cx + 50 * s, cy + (34 + i * 32) * s], [cx + 210 * s, cy + (30 + i * 32) * s]], { w: 4, col: K.sky, p: 0.9, seed: sd + 20 + i }); }
}
function icon(kind, cx, cy, s) {
  if (kind === 'play') part(TOP, [[cx - 90 * s, cy - 120 * s], [cx + 130 * s, cy], [cx - 90 * s, cy + 120 * s]], { col: K.red, p: 1, gap: 7, w: 9, seed: 41 }, { w: 9, col: K.ink, seed: 42 });
  if (kind === 'crayon') crayonStick(TOP, cx - 20 * s, cy, -0.7, K.orange, 300 * s, 43);
  if (kind === 'book') openBook(TOP, cx, cy - 80 * s, 0.95 * s, 44);
  if (kind === 'heart') heart(TOP, { x: cx, y: cy, s: 3.2 * s, seed: 45 });
  if (kind === 'star') { const pts = []; for (let k = 0; k <= 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5; const rr = k % 2 ? 70 * s : 160 * s; pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]); } part(TOP, pts, { col: K.yellow, p: 1, gap: 7, w: 9, seed: 46 }, { w: 8, col: K.orange, seed: 47 }); }
  if (kind === 'sun') sun(TOP, { x: cx, y: cy, R: 120 * s, face: 1, seed: 1100, s: 1 });
}

export function draw(comp, page) {
  CAM.x = W / 2; CAM.y = H / 2; CAM.s = 1; BOIL.amp = 1;
  [BG.f, BG.l, TX, WASH, TK].forEach(clear); clearGroup(G); clearGroup(TOP);
  let paper = PAL.paper, vig = 0.22, emb = 0.55, wash = false;
  const P = page || 'avatar';
  if (P === 'avatar' || P === 'mark') {
    const c = W / 2, k = W / 800;
    fill(BG.f, handCircle(c, c, 370 * k, 5, 0, 80), { col: K.sky, p: 0.6, gap: 13 * k, w: 13 * k, ang: -0.3, seed: 7, boil: 0 });
    if (P === 'avatar') { sun(TOP, { x: c, y: c - 70 * k, R: 150 * k, face: 1, seed: 1100 }); openBook(TOP, c, c + 150 * k, 1.05 * k); }
    else sun(TOP, { x: c, y: c, R: 190 * k, face: 1, seed: 1100 });
    vig = 0.1;
  }
  if (P === 'banner') {   // 2560×1440; área segura (celular) = 1546×423 no centro
    sky(-60, -60, W + 60, 900, 0.5);
    starsWax(0, 1); cloud(G, { x: 640, y: 560, s: 1.0, seed: 1400 }); cloud(G, { x: 1990, y: 600, s: 0.85, seed: 1410 });
    sun(TOP, { x: 260, y: 300, R: 120, face: 1, seed: 1100 });
    hills(880);
    [[300, 0.85], [2300, 0.8]].forEach(([x, s], i) => tree(G, { x, y: 900, s, seed: 1500 + i * 20 }));
    sheep(TOP, { x: 120, y: 1000, s: 1.4, seed: 500 }); person(TOP, { x: 290, y: 1010, s: 0.95, kind: 'adam', seed: 2000, armR: [[34, -196], [62, -160], [74, -126]] }); person(TOP, { x: 425, y: 1010, s: 0.92, kind: 'eve', seed: 2200, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] });
    lion(TOP, { x: 2170, y: 1010, s: 0.95, seed: 700 }); elephant(TOP, { x: 2420, y: 1010, s: 0.9, seed: 800 });
    patch(TK, 1280, 715, 700, 215);
    T('Bíblia em Traços', 1280, 690, 190);
    T('Histórias da Bíblia desenhadas para toda a família', 1280, 790, 62, { font: 'Patrick Hand' });
    T('Nova história todo sábado!', 1280, 878, 64, { col: K.red });
    bird(TOP, { x: 1050, y: 300, s: 1.2, col: K.red, seed: 950, flip: true, pose: 1 }); bird(TOP, { x: 1550, y: 260, s: 1.0, col: K.yellow, seed: 960, flip: true });
  }
  if (P === 'pl_at') {    // capa de playlist 1920×1080
    sky(-60, -60, W + 60, 760); seaBand(760, -60, W + 60); hills(760, -60, 1250, 30);
    sun(TOP, { x: 1650, y: 260, R: 110, face: 1, seed: 1100 }); tree(G, { x: 300, y: 800, s: 1.0, seed: 1500 });
    sheep(TOP, { x: 600, y: 960, s: 1.6, seed: 500 }); fish(TOP, { x: 1550, y: 900, s: 1.4, col: K.orange, seed: 900, flip: true });
    patch(TK, 960, 440, 640, 170); T('Antigo Testamento', 960, 445, 150); T('histórias em giz de cera', 960, 545, 64, { font: 'Patrick Hand' });
  }
  if (P === 'pl_nt' || P === 'pl_dormir') {
    sky(-60, -60, W + 60, 800, 0.35); starsWax(60, 760, P === 'pl_nt' ? 21 : 33, (x, y) => Math.abs(x - 960) < 700 && Math.abs(y - 440) < 200); hills(800);
    washAll(-60, H + 60); wash = true;
    if (P === 'pl_nt') icon('star', 1560, 230, 0.8);
    else { moon(TOP, { x: 1600, y: 230, R: 130, seed: 1200 }); sheep(TOP, { x: 520, y: 1000, s: 1.7, seed: 520, expr: 'sleep' }); rabbit(TOP, { x: 1400, y: 1000, s: 1.5, seed: 620, expr: 'sleep' }); }
    patch(TK, 960, 440, 640, 170);
    T(P === 'pl_nt' ? 'Novo Testamento' : 'Histórias para Dormir', 960, 445, 140); T(P === 'pl_nt' ? 'a vida de Jesus em giz de cera' : 'calminhas, para a hora de dormir', 960, 545, 62, { font: 'Patrick Hand' });
  }
  if (P === 'post_ola') {   // 1080×1350
    sun(TOP, { x: 540, y: 300, R: 130, face: 1, seed: 1100 });
    T('Olá!', 540, 650, 210, { col: K.orange }); T('Bem-vindos ao', 540, 770, 80, { font: 'Patrick Hand' }); T('Bíblia em Traços', 540, 900, 130);
    hills(1130, -60, W + 60, 18);
    sheep(TOP, { x: 150, y: 1290, s: 1.3, seed: 500 }); person(TOP, { x: 400, y: 1300, s: 0.9, kind: 'adam', seed: 2000, armR: [[34, -196], [62, -160], [74, -126]] }); person(TOP, { x: 540, y: 1300, s: 0.86, kind: 'eve', seed: 2200, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] }); lion(TOP, { x: 860, y: 1300, s: 0.9, seed: 700 });
  }
  if (P === 'post_como') {
    T('Toda semana', 540, 220, 120, { col: K.red }); T('uma nova história', 540, 340, 92); T('da Bíblia', 540, 440, 92);
    T('desenhada em giz de cera,', 540, 560, 66, { font: 'Patrick Hand' }); T('narrada para toda a família.', 540, 640, 66, { font: 'Patrick Hand' });
    crayonStick(TOP, 300, 860, -0.25, K.red, 280, 70); crayonStick(TOP, 540, 900, 0.1, K.yellow, 280, 80); crayonStick(TOP, 790, 860, 0.35, K.sky, 280, 90);
    heart(TOP, { x: 540, y: 1120, s: 1.8, seed: 1300 }); T('Novo episódio todo sábado', 540, 1290, 62, { font: 'Patrick Hand' });
  }
  if (P === 'post_ep01') {
    sky(-60, -60, W + 60, 700, 0.45); hills(700); sun(TOP, { x: 880, y: 230, R: 100, face: 1, seed: 1100 });
    person(TOP, { x: 430, y: 1180, s: 1.6, kind: 'adam', seed: 2000, armR: [[34, -196], [62, -160], [74, -126]] }); person(TOP, { x: 640, y: 1180, s: 1.55, kind: 'eve', seed: 2200, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] });
    heart(TOP, { x: 535, y: 560, s: 1.4, seed: 1300 }); rabbit(TOP, { x: 140, y: 1220, s: 1.5, seed: 600 }); sheep(TOP, { x: 900, y: 1220, s: 1.7, seed: 500 });
    patch(TK, 400, 220, 340, 150); T('EPISÓDIO 1', 400, 180, 70, { col: K.red }); T('A Criação', 400, 290, 130);
    patch(TK, 540, 1290, 330, 44); T('Já no YouTube!', 540, 1310, 66, { font: 'Patrick Hand' });
  }
  if (P === 'colorir' || P === 'colorir_a4') {
    paper = [0.995, 0.993, 0.985]; vig = 0; emb = 0.2;
    const k = W / 1080;
    T('Pinte a Criação!', W / 2, 150 * k, 120 * k);
    const sk = 1.0 * k;
    sun(TOP, { x: 860 * k, y: 330 * k, R: 90 * k, face: 1, seed: 1100, fill: 0 });
    cloud(TOP, { x: 260 * k, y: 330 * k, s: 0.8 * k, seed: 1400, fill: 0 });
    const top = []; for (let x = -40; x <= W + 40; x += 30) top.push([x, 760 * k + 26 * k * Math.sin(x / (240 * k))]);
    line(TOP.l, top, { w: 7, col: K.ink, seed: 81 });
    tree(TOP, { x: 160 * k, y: 800 * k, s: 0.8 * k, seed: 1500, fill: 0, fruit: 0 });
    person(TOP, { x: 450 * k, y: 1130 * k, s: 1.05 * sk, kind: 'adam', seed: 2000, fill: 0, armR: [[34, -196], [62, -160], [74, -126]] });
    person(TOP, { x: 625 * k, y: 1130 * k, s: 1.0 * sk, kind: 'eve', seed: 2200, fill: 0, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] });
    lion(TOP, { x: 890 * k, y: 1150 * k, s: 0.85 * sk, seed: 700, fill: 0 }); sheep(TOP, { x: 140 * k, y: 1160 * k, s: 1.3 * sk, seed: 500, fill: 0 });
    fish(TOP, { x: 860 * k, y: 640 * k, s: 0.9 * sk, seed: 900, fill: 0, flip: true });
    bird(TOP, { x: 560 * k, y: 450 * k, s: 1.1 * sk, seed: 950, fill: 0, flip: true, pose: 1 });
    T('Bíblia em Traços · Gênesis 1 e 2', W / 2, H - 50 * k, 44 * k, { font: 'Patrick Hand' });
  }
  if (P === 'story_novo' || P === 'reel_ep01' || P === 'short_bg') {   // 1080×1920
    if (P === 'story_novo') {
      sun(TOP, { x: 540, y: 300, R: 110, face: 1, seed: 1100 });
      T('NOVO', 540, 560, 170, { col: K.red }); T('EPISÓDIO!', 540, 720, 150, { col: K.red });
      // moldura para colar a miniatura ou o adesivo de link
      line(TOP.l, [[110, 820], [970, 818], [972, 1330], [108, 1332], [110, 820]], { w: 9, col: K.ink, seed: 51 });
      T('toque no link e assista', 540, 1450, 70, { font: 'Patrick Hand' }); line(TOP.l, [[540, 1490], [540, 1600]], { w: 9, col: K.ink, seed: 52 }); line(TOP.l, [[500, 1560], [540, 1604], [580, 1560]], { w: 9, col: K.ink, seed: 53 });
      hills(1700); sheep(TOP, { x: 200, y: 1880, s: 1.4, seed: 500 }); rabbit(TOP, { x: 880, y: 1890, s: 1.3, seed: 600 });
    } else if (P === 'reel_ep01') {
      sky(-60, -60, W + 60, 1150, 0.45); hills(1150); sun(TOP, { x: 860, y: 190, R: 95, face: 1, seed: 1100 });
      patch(TK, 540, 520, 380, 170); T('EPISÓDIO 1', 540, 470, 70, { col: K.red }); T('A Criação', 540, 590, 150);
      heart(TOP, { x: 540, y: 880, s: 1.4, seed: 1300 });
      person(TOP, { x: 420, y: 1560, s: 1.6, kind: 'adam', seed: 2000, armR: [[34, -196], [62, -160], [74, -126]] }); person(TOP, { x: 640, y: 1560, s: 1.55, kind: 'eve', seed: 2200, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] });
      sheep(TOP, { x: 170, y: 1660, s: 1.5, seed: 500 }); lion(TOP, { x: 930, y: 1660, s: 0.9, seed: 700 });
      patch(TK, 540, 1780, 300, 46); T('Bíblia em Traços', 540, 1800, 64, { font: 'Patrick Hand' });
    } else {   // fundo do Short vertical: vídeo 1080×608 entra em y 656–1264
      sun(TOP, { x: 860, y: 230, R: 90, face: 1, seed: 1100 });
      T('A Criação', 470, 360, 150); T('Bíblia em Traços', 470, 470, 64, { font: 'Patrick Hand' });
      T('Episódio completo', 540, 1440, 96, { col: K.red }); T('no canal!', 540, 1550, 96, { col: K.red });
      hills(1700); sheep(TOP, { x: 200, y: 1880, s: 1.4, seed: 500 }); person(TOP, { x: 540, y: 1890, s: 0.8, kind: 'child', seed: 2400, expr: 'wow', armR: [[34, -196], [80, -230], [100, -290]] }); rabbit(TOP, { x: 880, y: 1890, s: 1.3, seed: 600 });
    }
  }
  if (P === 'thumb_ep02' || P === 'reel_ep02' || P === 'post_ep02') {   // miniatura / capa / post do Ep. 02
    const tall = H > W, k = tall ? 1 : 1;
    const cx = P === 'thumb_ep02' ? 1180 : P === 'reel_ep02' ? 430 : 330, base = P === 'reel_ep02' ? 1560 : P === 'post_ep02' ? 1180 : 1010, s = P === 'reel_ep02' ? 1.25 : P === 'post_ep02' ? 1.25 : 1.25;
    sky(-60, -60, W + 60, base - 330 * s, 0.5); hills(base - 330 * s + 10);
    // árvore especial (copa dourada) com a serpente no galho
    const tx = cx + 230 * s, ty = base - 40 * s;
    part(G, [[tx - 30 * s, ty], [tx - 24 * s, ty - 230 * s], [tx + 24 * s, ty - 230 * s], [tx + 30 * s, ty], [tx - 30 * s, ty]], { col: K.brown, p: 0.9, gap: 8, w: 10, ang: 1.5, seed: 3100 }, { w: 8, col: K.ink, seed: 3101 });
    const crown = []; for (let i = 0; i <= 80; i++) { const a = i / 80 * 6.283; const b = 1 + 0.12 * Math.abs(Math.sin(a * 5)); crown.push([tx + Math.cos(a) * 190 * s * b, ty - 380 * s + Math.sin(a) * 160 * s * b]); }
    part(G, crown, { col: K.yellow, p: 0.95, gap: 11, w: 13, ang: 0.8, seed: 3103, cross: true, crossP: 0.5 }, { w: 8, col: K.orange, seed: 3104 });
    [[-90, -420], [70, -440], [110, -320], [-30, -300], [-130, -330]].forEach(([dx, dy], i) => fruit(G, tx + dx * s, ty + dy * s, 22 * s, 3200 + i * 7));
    serpent(TOP, { x: tx - 40 * s, y: ty - 300 * s, s: 1.45 * s, flip: true, seed: 1900, tongue: true, look: -1 });
    person(TOP, { x: cx - 170 * s, y: base, s: 1.15 * s, kind: 'adam', seed: 2000, expr: 'wow' });
    person(TOP, { x: cx + 10 * s, y: base, s: 1.1 * s, kind: 'eve', seed: 2200, expr: 'wow', armR: [[34, -196], [66, -215], [86, -240]] });
    fruit(TOP, cx + 10 * s + 92 * 1.1 * s, base - 258 * 1.1 * s, 30 * s, 3290);
    if (P === 'thumb_ep02') { patch(TK, 420, 230, 360, 165); T('NÃO COMA!', 420, 200, 120, { col: K.red }); T('Adão e Eva', 420, 320, 100);
      patch(TK, 300, 1000, 250, 44); T('Bíblia em Traços', 300, 1018, 60, { font: 'Patrick Hand' }); }
    else { patch(TK, 540, tall ? 300 : 210, 400, 160); T(tall ? 'EPISÓDIO 2' : 'EPISÓDIO 2', 540, tall ? 250 : 165, 70, { col: K.red }); T('Adão e Eva', 540, tall ? 370 : 280, 140);
      patch(TK, 540, H - 110, 320, 46); T(P === 'post_ep02' ? 'Já no YouTube!' : 'Bíblia em Traços', 540, H - 90, 64, { font: 'Patrick Hand' }); }
  }
  if (P.startsWith('hl_')) {   // destaques do Instagram 1080×1920 (o ícone fica no centro do círculo)
    const col = { hl_episodios: K.yellow, hl_colorir: K.pink, hl_versiculos: K.sky, hl_sobre: K.green, hl_novidades: K.orange }[P];
    fill(BG.f, handCircle(540, 960, 430, 9, 0, 80), { col, p: 0.6, gap: 13, w: 13, ang: -0.3, seed: 8, boil: 0, cross: true, crossP: 0.4 });
    line(BG.l, handCircle(540, 960, 430, 9, 0.04, 80), { w: 8, col: K.ink, seed: 10 });
    icon({ hl_episodios: 'play', hl_colorir: 'crayon', hl_versiculos: 'book', hl_sobre: 'heart', hl_novidades: 'star' }[P], 540, 960, 1.1);
  }
  comp.paperCam(W / 2, H / 2, 1); comp.begin(paper);
  comp.crayon(BG.f.c); comp.crayon(BG.l.c);
  comp.group(G);
  if (wash) comp.wash(WASH.c, { color: PAL.wash });
  comp.group(TOP);
  comp.knock(TK.c); comp.crayon(TX.c);
  comp.finish({ vig, emb });
}
