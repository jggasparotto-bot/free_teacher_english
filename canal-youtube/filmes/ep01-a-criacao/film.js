// Bíblia em Traços · Ep. 01 · A Criação — linha do tempo, câmera, páginas e eventos (fonte única de verdade).
// Página 0: título · Página 1: escuridão → luz → céu e mar → terra e plantas → sol, lua e estrelas (wash da noite)
// Página 2: peixes, aves, animais, Adão e Eva, descanso, "você" · Final: o livro na mesa, virada para a próxima história.
import { layer, clear, line, fill, dab, text, handCircle, ellipse, smooth, CAM, BOIL, W, H, sx, sy } from './crayon.js';
import { group, clearGroup, part } from './rig.js';
import { person, sheep, rabbit, lion, elephant, fish, bird, sun, moon, heart, cloud, tree, flower } from './chars.js';
import { mk, snap, drawBook, drawDesk, drawCrayons, turnAngle } from './book.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, track, ss, eo, back, mulberry } from '/core/lib.js';
const K = PAL.crayon;
const pr = (t, a, b) => clamp((t - a) / (b - a));
export const DUR = 131;
const FULL = [1600, 900, 0.6];

// —— narração (t = início da fala; d = duração medida do arquivo de voz) ——
const VD = { vinheta: 1.423, titulo: 1.017, e1: 4.411, e2: 3.443, d1a: 3.102, d1b: 4.594, d2a: 3.873, d2b: 3.005, d3a: 4.447, d3b: 3.896, d4a: 4.194, d4b: 2.695, d5a: 4.4, d5b: 2.843, d6a: 5.205, d6b: 5.035, d6c: 4.686, d7a: 3.67, d7b: 4.145, l1: 3.087, l2: 2.681, l3: 0.764, l4: 4.65, fim: 4.444 };
const L = (id, t, text, sub = true) => ({ id, t, d: VD[id], text, sub });
export const LINES = [
  L('vinheta', 2.7, 'Bíblia em Traços!', false),
  L('titulo', 4.8, 'A Criação.', false),
  L('e1', 10.0, 'No princípio, antes de existir qualquer coisa, tudo era escuro e vazio.'),
  L('e2', 15.3, 'Não havia céu, nem terra, nem mar... Mas Deus já estava lá.'),
  L('d1a', 19.9, 'Então Deus disse: “Haja luz!” E a luz apareceu!'),
  L('d1b', 24.0, 'Deus viu que a luz era boa. Ele chamou a luz de dia, e a escuridão de noite.'),
  L('d2a', 29.6, 'No segundo dia, Deus separou as águas e fez o céu, lá no alto.'),
  L('d2b', 34.4, 'Em cima, o céu azul. Embaixo, as águas do mar.'),
  L('d3a', 38.4, 'No terceiro dia, Deus juntou as águas e fez aparecer a terra seca.'),
  L('d3b', 43.8, 'E da terra brotaram plantas, flores e árvores cheias de frutos!'),
  L('d4a', 48.8, 'No quarto dia, Deus colocou no céu o sol, para brilhar durante o dia...'),
  L('d4b', 54.4, '...e a lua e as estrelas, para iluminar a noite.'),
  L('d5a', 61.0, 'No quinto dia, Deus encheu as águas de peixes de todos os tamanhos...'),
  L('d5b', 66.3, '...e o céu de passarinhos que voavam e cantavam.'),
  L('d6a', 70.1, 'No sexto dia, Deus fez os animais da terra: ovelhas, coelhos, leões, elefantes...'),
  L('d6b', 76.4, 'E então Deus fez a sua criação mais especial: o homem e a mulher, Adão e Eva.'),
  L('d6c', 82.4, 'Deus os fez parecidos com Ele, para cuidarem com carinho de tudo o que Ele criou.'),
  L('d7a', 88.2, 'Deus olhou para tudo o que tinha feito, e viu que era muito bom!'),
  L('d7b', 92.9, 'No sétimo dia, Deus descansou, e fez desse dia um dia especial.'),
  L('l1', 98.2, 'Tudo o que existe foi feito por Deus, com muito amor.'),
  L('l2', 102.3, 'E sabe quem mais Ele fez com todo o carinho?'),
  L('l3', 106.2, 'Você!'),
  L('l4', 108.4, 'Agora converse com sua família: qual parte da criação você mais gosta?'),
  L('fim', 117.6, 'Inscreva-se no canal! Na próxima história: Adão e Eva no Jardim do Éden.'),
];
export const SUBS = LINES.filter(l => l.sub).map((l, i, A) => { const t0 = l.t - 0.1; let t1 = Math.max(t0 + 1.8, l.t + l.d + 0.7); const nx = A[i + 1]; if (nx) t1 = Math.min(t1, nx.t - 0.25); return { t0, t1, text: l.text }; });

// —— páginas e viradas ——
const TURN1 = [7.0, 8.2], TURN2 = [59.0, 60.3], ENDT = 113.6, TURN3 = [116.0, 117.3];

// —— câmera (centro no mundo da página 3200×1800 + zoom; página inteira = 0.6) ——
const camT = track([
  [0, [1600, 700, 0.75]], [3.4, [1600, 700, 0.75]], [4.6, [1600, 1000, 0.72]], [6.4, [1600, 1000, 0.72]], [6.95, FULL],
  [8.2, FULL], [15.3, FULL], [18.6, [1650, 640, 0.9]], [21.3, [1650, 640, 0.9]], [22.6, [1650, 700, 0.72]], [24.0, [1650, 700, 0.72]],
  [28.6, [1600, 800, 0.6]], [29.8, [1600, 560, 0.75]], [33.0, [1600, 700, 0.75]], [37.4, [1600, 1250, 0.75]], [38.6, [1300, 1150, 0.72]],
  [39.4, [900, 1100, 0.8]], [42.8, [900, 1040, 0.8]], [43.8, [450, 1040, 0.95]], [47.8, [1700, 1040, 0.95]], [48.9, [1600, 850, 0.62]],
  [52.8, [1600, 850, 0.62]], [54.4, FULL], [59.0, FULL],
  [60.3, FULL], [61.0, FULL], [62.4, [2650, 1450, 1.05]], [65.8, [2650, 1450, 1.05]], [68.4, [1900, 650, 0.85]], [69.2, [1900, 700, 0.85]],
  [70.6, [450, 1380, 1.0]], [75.4, [1650, 1380, 1.0]], [76.6, [1300, 1320, 0.9]], [77.8, [895, 1330, 1.4]], [81.6, [895, 1330, 1.4]],
  [82.6, [895, 1310, 1.5]], [87.4, [895, 1310, 1.5]], [89.8, FULL], [97.6, FULL], [100.6, [2200, 1500, 1.15]], [113.6, [2200, 1500, 1.15]],
]);
// mesa: z zoom, c centro (coordenadas da mesa)
const camD = track([[ENDT, [960, 540, 1]], [115.4, [0, 580, 0.46]], [116.0, [0, 580, 0.46]], [118.4, [960, 540, 0.9]], [DUR, [960, 540, 0.92]]]);

// —— geometria da página 1 ——
const SUNC = [1650, 560];
const landTop1 = x => x < 1950 ? 1040 + 50 * Math.sin(x / 380 + 0.6) + 25 * Math.sin(x / 150) : lerp(1040 + 50 * Math.sin(1950 / 380 + 0.6) + 25 * Math.sin(13), 1900, (x - 1950) / 450);
const seaTop = x => 1180 + 14 * Math.sin(x * 0.004) + 8 * Math.sin(x * 0.011);
const TREES1 = [[330, 1.1], [820, 1.25], [1330, 1.05]];
const FLOW1 = [[150, K.pink], [520, K.white], [640, K.orange], [1050, K.pink], [1160, K.yellow], [1500, K.white], [1760, K.pink]];
const CLOUDS1 = [[1000, 250, 0.9], [2300, 760, 1.1], [2950, 640, 0.8]];
const MOONP = [3000, 270];
const RNG = mulberry(777);
export const STARS = [];
for (let n = 0; STARS.length < 140 && n < 6000; n++) {
  const x = 40 + RNG() * 3120, y = 30 + RNG() * 1100, sz = RNG();
  if (Math.hypot(x - SUNC[0], y - SUNC[1]) < 380) continue;
  if (Math.hypot(x - MOONP[0], y - MOONP[1]) < 170) continue;
  if (x > 420 && x < 860 && y > 230 && y < 450) continue;      // DIA
  if (x > 2330 && x < 2950 && y > 230 && y < 450) continue;    // NOITE
  if (x < 560 && y < 250) continue;                            // números dos dias
  if (STARS.some(s => Math.hypot(s.x - x, s.y - y) < 85)) continue;
  STARS.push({ x, y, big: sz < 0.45, r: sz < 0.45 ? 13 + RNG() * 12 : 5 + RNG() * 4, seed: 500 + n });
}
// faixas de aquarela da noite (da direita para a esquerda, depois de volta)
const BANDS = [
  { y0: -140, y1: 640, t0: 54.6, t1: 56.2, dir: -1, seed: 1 },
  { y0: 540, y1: 1260, t0: 55.7, t1: 57.2, dir: 1, seed: 2 },
  { y0: 1160, y1: 1920, t0: 56.7, t1: 58.1, dir: -1, seed: 3 },
];
const X0 = -260, X1 = 3460;
function bandFront(b, t) { const u = clamp((t - b.t0) / (b.t1 - b.t0)); const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; const v = 0.15 * u + 0.85 * e; return b.dir > 0 ? lerp(X0, X1, v) : lerp(X1, X0, v); }

// —— geometria da página 2 (manhã) ——
const landTop2 = x => x < 2150 ? 1120 + 40 * Math.sin(x / 420 + 1.2) + 18 * Math.sin(x / 170) : lerp(1120 + 40 * Math.sin(2150 / 420 + 1.2) + 18 * Math.sin(2150 / 170), 1900, (x - 2150) / 600);
const SUN2 = [2860, 300];
const POS = { sheep: [250, 1570, 2.0], rabbit: [520, 1650, 1.7], adam: [800, 1610, 1.25], eve: [990, 1610, 1.2], lion: [1350, 1620, 1.45], elephant: [1800, 1610, 1.35], child: [2180, 1745, 1.1] };
const FISH = [
  { col: K.orange, s: 1.1, y: 1340, x0: 3150, v: -55, seed: 900 },
  { col: K.yellow, s: 0.8, y: 1470, x0: 2400, v: 70, seed: 910 },
  { col: K.pink, s: 1.3, y: 1610, x0: 2900, v: -40, seed: 920 },
  { col: K.sky, s: 0.7, y: 1730, x0: 2550, v: 85, seed: 930 },
];
const FISH_T = [61.6, 62.3, 62.9, 63.5];
const BIRDS = [[K.red, 420, 1.2], [K.sky, 560, 1.0], [K.yellow, 330, 0.9], [K.pink, 700, 1.1]];
const BIRD_T = [66.0, 66.4, 66.8, 67.2];
const AN_T = { sheep: 70.8, rabbit: 71.8, lion: 72.9, elephant: 74.0, adam: 78.0, eve: 79.3, child: 102.6 };

// —— eventos (som e música; exportados para o mix) ——
export const EV = [];
const ev = (t, type, o = {}) => EV.push({ t: +t.toFixed(3), type, ...o });
LINES.forEach(l => ev(l.t, 'voice', { id: l.id }));
ev(0, 'paper'); ev(0.2, 'write', { dur: 2.2, pan: -0.2 }); ev(2.4, 'scratch', { dur: 0.5, pan: 0.2 });
ev(4.5, 'write', { dur: 1.3 }); ev(5.9, 'write', { dur: 0.7, pan: 0.3 });
[TURN1, TURN2, TURN3].forEach(([a, b]) => ev(a, 'page', { dur: b - a }));
ev(8.6, 'darkness', { dur: 1.2 }); ev(17.0, 'dot'); ev(21.5, 'light');
ev(21.6, 'scratch', { dur: 1.2, pan: 0.1 });
const NUM_T = [22.6, 32.6, 41.6, 50.8, 61.6, 74.9, 93.2];
NUM_T.forEach((t, i) => ev(t, 'number', { i }));
ev(25.9, 'write', { dur: 0.6, pan: -0.6 }); ev(27.4, 'write', { dur: 0.7, pan: 0.6 });
ev(29.8, 'scribble', { dur: 2.4, pan: 0 }); ev(32.0, 'scratch', { dur: 1.2, pan: 0.3 });
ev(34.4, 'scratch', { dur: 0.8 }); ev(34.8, 'scribble', { dur: 2.0 }); ev(36.6, 'scratch', { dur: 0.8, pan: 0.4 });
ev(39.2, 'rise', { dur: 2.2 }); ev(40.4, 'scribble', { dur: 2.0, pan: -0.3 });
TREES1.forEach((_, i) => ev(43.9 + i * 1.2, 'scratch', { dur: 0.8, pan: -0.6 + i * 0.5 }));
FLOW1.forEach((_, i) => ev(44.2 + i * 0.48, 'pop', { pan: -0.7 + i * 0.22 }));
ev(49.6, 'scratch', { dur: 1.0 }); ev(53.0, 'set', { dur: 1.4 });
ev(54.6, 'scratch', { dur: 0.8, pan: 0.7 });
BANDS.forEach(b => ev(b.t0, 'brush', { dur: b.t1 - b.t0, dir: b.dir }));
ev(54.5, 'dip');
STARS.forEach(s => { if (!s.big) return; const b = BANDS.find(b => s.y >= b.y0 + 20 && s.y <= b.y1 - 20) || BANDS[0]; const u = b.dir > 0 ? (s.x - X0) / (X1 - X0) : (X1 - s.x) / (X1 - X0); const t = lerp(b.t0, b.t1, clamp(u)); ev(t, 'glint', { pan: (s.x - 1600) / 1600 }); });
FISH_T.forEach((t, i) => { ev(t, 'scratch', { dur: 0.5, pan: 0.6 }); ev(t + 0.5, 'bubble', { pan: 0.6 }); });
ev(64.4, 'splash', { pan: 0.5 }); ev(65.3, 'splash', { pan: 0.4, small: 1 });
BIRD_T.forEach((t, i) => { ev(t, 'scratch', { dur: 0.4, pan: 0.8 }); ev(t + 0.6, 'tweet', { pan: 0.6 - i * 0.3 }); });
['sheep', 'rabbit', 'lion', 'elephant'].forEach(k => { ev(AN_T[k], 'scratch', { dur: 0.6, pan: -0.4 }); ev(AN_T[k] + 0.5, 'scribble', { dur: 0.5, pan: -0.3 }); ev(AN_T[k] + 0.9, k); });
[72.9, 73.25].forEach(t => ev(t - 0.95, 'hop'));
ev(AN_T.adam, 'scratch', { dur: 1.0, pan: -0.2 }); ev(AN_T.adam + 0.6, 'scribble', { dur: 0.8, pan: -0.2 });
ev(AN_T.eve, 'scratch', { dur: 0.9, pan: 0.2 }); ev(AN_T.eve + 0.6, 'scribble', { dur: 0.8, pan: 0.2 });
ev(80.8, 'hands'); ev(83.0, 'scribble', { dur: 0.5 }); ev(83.8, 'heart');
ev(93.6, 'rest'); [94.2, 95.6, 97.0].forEach(t => ev(t, 'zzz'));
ev(AN_T.child, 'scratch', { dur: 1.2, pan: 0.5 }); ev(AN_T.child + 1.0, 'scribble', { dur: 0.9, pan: 0.5 });
ev(105.0, 'silence', { dur: 1.1 }); ev(106.2, 'write', { dur: 0.6, pan: 0.5 }); ev(106.8, 'scratch', { dur: 0.4 }); ev(107.2, 'heart');
ev(ENDT, 'room');
ev(117.4, 'write', { dur: 2.2 }); ev(119.6, 'write', { dur: 1.0 });
[['A', 0], ['B', 8.2], ['C', 21.5], ['D', 54.4], ['E', 60.3], ['F', 76.4], ['G', 88.2], ['H', 98.2], ['I', ENDT]].forEach(([id, t]) => ev(t, 'cue', { id }));

// —— camadas ——
const STAR = group(), BG = { f: layer(), l: layer() }, SUN = group(), LAND = group(), CL = group(), FG = group(), WASH = layer(), FX = layer(), SUBK = layer(), SUBT = layer(), TXT = layer(), DUM = layer();
const DESK = { f: layer(), l: layer() }, OBJ = group(), book = mk();
const PG = { a: mk(), b: mk(), back: mk(), left: mk() };
const boilFor = t => (t > 92.9 && t < 113.6) ? lerp(1, 0.5, pr(t, 92.9, 94.5)) : 1;

// —— página 0: o título ——
function page0(comp, t, cam, { subs = true, vig = 0.3 } = {}) {
  [CAM.x, CAM.y, CAM.s] = cam; BOIL.amp = 1;
  [BG.f, BG.l, SUBK, SUBT].forEach(clear);
  text(BG.l, 'Bíblia em Traços', sx(1600), sy(700), { size: 190 * CAM.s, font: 'Gochi Hand', col: K.ink, reveal: pr(t, 0.2, 2.4), seed: 21, p: 0.95, stroke: 2 });
  const u = pr(t, 2.4, 2.9);
  if (u > 0) line(BG.l, [[960, 780], [1300, 792], [1700, 784], [2240, 790]], { w: 13, col: K.red, p: 0.95, seed: 22, draw: u });
  [[700, 520], [2500, 520], [880, 880], [2330, 900], [1600, 440]].forEach(([x, y], i) => { const g = pr(t, 0.6 + i * 0.3, 0.9 + i * 0.3); if (g > 0) starShape(BG, x, y, 26 * g, 30 + i); });
  text(BG.l, 'A Criação', sx(1600), sy(1090), { size: 260 * CAM.s, font: 'Gochi Hand', col: K.ink, reveal: pr(t, 4.5, 5.8), seed: 31, p: 0.95, stroke: 2.5 });
  text(BG.l, 'Gênesis 1 e 2', sx(1600), sy(1240), { size: 110 * CAM.s, font: 'Patrick Hand', col: K.ink, reveal: pr(t, 5.9, 6.6), seed: 32, p: 0.9 });
  if (subs) subTo(SUBK, SUBT, t);
  comp.paperCam(CAM.x * 0.6, CAM.y * 0.6, CAM.s / 0.6); comp.begin();
  comp.crayon(BG.f.c); comp.crayon(BG.l.c); comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig });
}
function starShape(G, x, y, r, sd, col = K.yellow, lc = K.orange) {
  const pts = []; for (let k = 0; k <= 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5; const rr = k % 2 ? r * 0.45 : r; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
  fill(G.f, pts, { col, p: 0.95, gap: 4, w: 6, over: 1, seed: sd }); line(G.l, pts, { col: lc, w: 4, p: 0.8, seed: sd + 1, wob: 0.3 });
}

// —— página 1 ——
function sunState1(t) {
  const o = { x: SUNC[0], y: SUNC[1], R: 0, rays: 0, face: 0, seed: 1100, outline: true };
  if (t < 17.0) return null;
  o.R = 14 * (1 + 0.15 * Math.sin(t * 4));
  if (t >= 21.5) { o.R = lerp(14, 110, back(pr(t, 21.5, 22.0))); o.rays = pr(t, 21.6, 22.8); }
  o.face = pr(t, 49.6, 50.6);
  const set = ss(pr(t, 53.0, 54.4)); o.y += 720 * set; o.x += 60 * set;
  if (t < 21.5) o.outline = false;
  return o;
}
function page1(comp, t, cam, { subs = true, vig = 0.3, dim = 0, glow = null } = {}) {
  [CAM.x, CAM.y, CAM.s] = cam; BOIL.amp = boilFor(t);
  clearGroup(STAR); clearGroup(SUN); clearGroup(LAND); clearGroup(CL); clearGroup(FG);
  [BG.f, BG.l, WASH, FX, SUBK, SUBT].forEach(clear);
  // estrelas de cera branca: estão na página desde o primeiro quadro, invisíveis até a noite
  for (const s of STARS) { if (s.big) starShape({ f: STAR.f, l: STAR.f }, s.x, s.y, s.r, s.seed, K.white, K.white); else dab(STAR.f, s.x, s.y, s.r, { col: K.white, p: 1, seed: s.seed, gap: 3, w: 4, over: 0.5, boil: 0.25 }); }
  // Dia 1: as palavras
  if (t > 25.9) text(BG.l, 'DIA', sx(640), sy(380), { size: 150 * CAM.s, font: 'Gochi Hand', col: K.orange, reveal: pr(t, 25.9, 26.5), seed: 41, p: 1, stroke: 2 });
  if (t > 27.4) text(BG.l, 'NOITE', sx(2640), sy(380), { size: 150 * CAM.s, font: 'Gochi Hand', col: K.ink, reveal: pr(t, 27.4, 28.1), seed: 42, p: 1, stroke: 2 });
  // números dos dias (lógica de criança: contados no céu)
  NUM_T.slice(0, 4).forEach((t0, i) => { if (t > t0) text(BG.l, String(i + 1), sx(170 + 110 * i), sy(190), { size: 120 * CAM.s, font: 'Gochi Hand', seed: 50 + i, reveal: pr(t, t0, t0 + 0.25), p: 0.9 }); });
  // Dia 2: céu e mar
  const skyP = pr(t, 29.8, 32.2);
  if (skyP > 0) fill(BG.f, [[-80, -80], [3280, -80], [3280, 1200], [-80, 1200]], { col: K.sky, p: 0.55, gap: 15, w: 14, ang: -0.25, seed: 60, draw: skyP, boil: 0, over: 0 });
  CLOUDS1.forEach(([x, y, s], i) => { const g = pr(t, 32.0 + i * 0.35, 32.6 + i * 0.35); if (g > 0) cloud(CL, { x, y, s, seed: 1400 + i * 10, draw: g, fill: pr(t, 32.4 + i * 0.35, 33.0 + i * 0.35) }); });
  const hz = []; for (let x = -80; x <= 3280; x += 40) hz.push([x, seaTop(x)]);
  const seaL = pr(t, 34.4, 35.0), seaF = pr(t, 34.8, 36.8);
  if (seaF > 0) fill(BG.f, [...hz, [3280, 1900], [-80, 1900]], { col: K.teal, p: 0.8, gap: 11, w: 12, ang: 0.15, seed: 61, draw: seaF, boil: 0, cross: true, crossP: 0.45, over: 0 });
  if (seaL > 0) line(BG.l, hz, { w: 7, col: K.ink, p: 0.8, seed: 62, draw: seaL, boil: 0.6 });
  if (t > 36.6) for (let i = 0; i < 16; i++) { const x = 120 + i * 200 + hash(i) * 90, y = 1290 + hash(i + 5) * 520; const g = pr(t, 36.6 + i * 0.05, 36.9 + i * 0.05); line(BG.l, [[x - 22, y], [x - 11, y + 10], [x, y], [x + 11, y + 10], [x + 22, y]], { w: 4.5, col: K.white, p: 0.95, seed: 70 + i, draw: g, boil: 0.6 }); }
  // o sol (a luz do Dia 1 vira o sol do Dia 4)
  const so = sunState1(t); if (so) sun(SUN, so);
  // Dia 3: a terra seca aparece (sobe das águas) e brotam as plantas
  const rise = ss(pr(t, 39.2, 41.4));
  if (rise > 0) {
    const off = (1 - rise) * 640;
    const top = []; for (let x = -80; x <= 2420; x += 40) top.push([x, landTop1(x) + off]);
    part(LAND, [[-80, 1950], ...top, [2420, 1950]], { col: K.green, p: 0.82, gap: 12, w: 13, ang: 1.15, seed: 80, draw: pr(t, 39.6, 41.8), boil: 0, cross: true, crossP: 0.35 }, null);
    line(LAND.l, top, { w: 7.5, col: K.ink, seed: 81, boil: 0.6 });
    TREES1.forEach(([x, s], i) => { const t0 = 43.9 + i * 1.2; const g = pr(t, t0, t0 + 0.7); if (g > 0) tree(LAND, { x, y: landTop1(x) + 40 + off, s, seed: 1500 + i * 20, draw: g, fill: pr(t, t0 + 0.4, t0 + 1.0), fruit: pr(t, t0 + 0.9, t0 + 1.3) }); });
    FLOW1.forEach(([x, c], i) => { const g = pr(t, 44.2 + i * 0.48, 44.6 + i * 0.48); if (g > 0) flower(LAND, { x, y: landTop1(x) + 95, s: 1.2, col: c, seed: 1600 + i * 10, g: eo(g) }); });
  }
  // Dia 4: a lua
  const mg = pr(t, 54.6, 55.4); if (mg > 0) moon(FG, { x: MOONP[0], y: MOONP[1], R: 120, draw: mg, fill: pr(t, 55.0, 55.6) });
  // estrelas brilhando depois do wash
  if (t > 56.5) for (let k = 0; k < 18; k++) {
    const s = STARS[(k * 23) % STARS.length]; if (!s.big) continue;
    const ph = (t * 0.7 + hash(k) * 3) % 3; if (ph > 0.5) continue;
    const a = Math.sin(ph / 0.5 * Math.PI), r = s.r * (1.6 + 1.2 * a);
    line(FX, [[s.x - r, s.y], [s.x + r, s.y]], { w: 3.5, col: K.white, p: a, seed: 800 + k, wob: 0.2 });
    line(FX, [[s.x, s.y - r], [s.x, s.y + r]], { w: 3.5, col: K.white, p: a, seed: 820 + k, wob: 0.2 });
  }
  if (t > BANDS[0].t0) drawWash(WASH, t);
  if (subs) subTo(SUBK, SUBT, t);
  comp.paperCam(CAM.x * 0.6, CAM.y * 0.6, CAM.s / 0.6); comp.begin();
  comp.group(STAR); comp.crayon(BG.f.c); comp.crayon(BG.l.c);
  const go = [hash(BOIL.step) * 300, hash(BOIL.step + 7) * 300];
  comp.group(SUN, { goff: go }); comp.group(LAND, { goff: go }); comp.group(CL, { goff: go });
  if (t > BANDS[0].t0) comp.wash(WASH.c, { color: PAL.wash });
  comp.group(FG, { goff: go }); comp.crayon(FX.c, { goff: go });
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig, dim, glow: glow || [0.5, 0.5, 0.1, 0] });
}
function drawWash(LW, t) {
  const g = LW.g; g.save();
  g.setTransform(CAM.s, 0, 0, CAM.s, W / 2 - CAM.x * CAM.s, H / 2 - CAM.y * CAM.s);
  for (const b of BANDS) {
    if (t < b.t0) continue;
    const f = bandFront(b, t), moving = t < b.t1;
    const top = [], bot = [];
    for (let x = X0; x <= X1; x += 40) {
      top.push([x, b.y0 + 12 * (Math.sin(x * 0.006 + b.seed) + 0.6 * Math.sin(x * 0.017 + b.seed * 3)) + 12 * hash(x * 0.37 + b.seed)]);
      bot.push([x, b.y1 + 14 * (Math.sin(x * 0.005 + b.seed * 2) + 0.5 * Math.sin(x * 0.019 + b.seed)) + 14 * hash(x * 0.71 + b.seed)]);
    }
    const frontX = y => f + b.dir * 70 * Math.sin(clamp((y - b.y0) / (b.y1 - b.y0)) * Math.PI) + 12 * Math.sin(y * 0.05);
    g.save(); g.beginPath();
    if (b.dir > 0) { g.moveTo(X0 - 50, b.y0 - 200); for (let y = b.y0 - 200; y <= b.y1 + 200; y += 20) g.lineTo(frontX(y), y); g.lineTo(X0 - 50, b.y1 + 200); }
    else { g.moveTo(X1 + 50, b.y0 - 200); for (let y = b.y0 - 200; y <= b.y1 + 200; y += 20) g.lineTo(frontX(y), y); g.lineTo(X1 + 50, b.y1 + 200); }
    g.closePath(); g.clip();
    const shape = new Path2D(); top.forEach(([x, y], i) => i ? shape.lineTo(x, y) : shape.moveTo(x, y)); for (let i = bot.length - 1; i >= 0; i--) shape.lineTo(bot[i][0], bot[i][1]); shape.closePath();
    g.fillStyle = '#000'; g.globalAlpha = 0.8; g.fill(shape);
    g.save(); g.clip(shape);
    const R = mulberry(b.seed * 97);
    for (let i = 0; i < 26; i++) {
      const yy = lerp(b.y0, b.y1, R()), wdt = 6 + R() * 30, dark = R() < 0.55;
      g.beginPath(); for (let x = X0; x <= X1; x += 60) { const y = yy + 14 * Math.sin(x * 0.002 + i) + 6 * Math.sin(x * 0.01 + i * 2); x === X0 ? g.moveTo(x, y) : g.lineTo(x, y); }
      g.lineWidth = dark ? wdt : wdt * 0.5; g.globalCompositeOperation = dark ? 'source-over' : 'destination-out'; g.globalAlpha = dark ? 0.14 + R() * 0.12 : 0.05 + R() * 0.07; g.strokeStyle = '#000'; g.stroke();
    }
    g.globalCompositeOperation = 'source-over';
    g.beginPath(); for (let y = b.y0 - 80; y <= b.y1 + 80; y += 16) { const x = frontX(y) - b.dir * 14; y === b.y0 - 80 ? g.moveTo(x, y) : g.lineTo(x, y); }
    g.lineWidth = moving ? 34 : 22; g.globalAlpha = moving ? 0.3 : 0.14; g.stroke();
    g.restore(); g.restore();
  }
  g.restore();
}

// —— página 2 ——
function fishPos(i, t) {
  const F = FISH[i], t0 = FISH_T[i]; if (t < t0) return null;
  const span = 850, x = 2330 + (((F.x0 - 2330) + F.v * (t - t0)) % span + span) % span;
  return { x, y: F.y + 12 * Math.sin(t * 2 + i), flip: F.v < 0 };
}
function page2(comp, t, cam, { subs = true, vig = 0.3, extra = true } = {}) {
  [CAM.x, CAM.y, CAM.s] = cam; BOIL.amp = boilFor(t);
  clearGroup(SUN); clearGroup(LAND); clearGroup(CL); clearGroup(FG);
  [BG.f, BG.l, FX, SUBK, SUBT].forEach(clear);
  const rest = t > 93.6 && t < ENDT + 4;
  // fundo já ilustrado (a página seguinte do livro): céu claro, mar, terra, sol da manhã
  fill(BG.f, [[-80, -80], [3280, -80], [3280, 1200], [-80, 1200]], { col: K.sky, p: 0.4, gap: 16, w: 14, ang: -0.25, seed: 160, boil: 0, over: 0 });
  const hz = []; for (let x = -80; x <= 3280; x += 40) hz.push([x, seaTop(x) + 20]);
  fill(BG.f, [...hz, [3280, 1900], [-80, 1900]], { col: K.teal, p: 0.8, gap: 11, w: 12, ang: 0.15, seed: 161, boil: 0, cross: true, crossP: 0.45, over: 0 });
  line(BG.l, hz, { w: 7, col: K.ink, p: 0.8, seed: 162, boil: 0.6 });
  for (let i = 0; i < 9; i++) { const x = 2350 + i * 95 + hash(i + 30) * 60, y = 1290 + hash(i + 40) * 520; line(BG.l, [[x - 22, y], [x - 11, y + 10], [x, y], [x + 11, y + 10], [x + 22, y]], { w: 4.5, col: K.white, p: 0.95, seed: 170 + i, boil: 0.6 }); }
  NUM_T.slice(4).forEach((t0, i) => { if (t > t0) text(BG.l, String(i + 5), sx(170 + 110 * i), sy(190), { size: 120 * CAM.s, font: 'Gochi Hand', seed: 150 + i, reveal: pr(t, t0, t0 + 0.25), p: 0.9 }); });
  sun(SUN, { x: SUN2[0], y: SUN2[1], R: 100, rays: 1, face: 1, seed: 1150, expr: rest ? 'sleep' : 'smile' });
  [[700, 300, 1.0], [1700, 230, 0.8]].forEach(([x, y, s], i) => cloud(CL, { x, y, s, seed: 1450 + i * 10 }));
  // peixes (Dia 5): nadam no mar, cauda em duas poses
  for (let i = 0; i < FISH.length; i++) {
    const q = fishPos(i, t); if (!q) continue;
    const g = pr(t, FISH_T[i], FISH_T[i] + 0.5);
    fish(FG, { x: q.x, y: q.y, s: FISH[i].s, col: FISH[i].col, seed: FISH[i].seed, flip: q.flip, pose: Math.floor(t * 4) % 2, draw: g, fill: pr(t, FISH_T[i] + 0.3, FISH_T[i] + 0.8) });
  }
  const jt = pr(t, 64.4, 65.3);
  if (jt > 0 && jt < 1) { const q = Math.floor(jt * 22) / 22; fish(FG, { x: lerp(2500, 2900, q), y: 1260 - 300 * Math.sin(q * Math.PI), s: 0.9, col: K.red, seed: 940, r: lerp(-0.7, 0.7, q), pose: Math.floor(t * 8) % 2 }); }
  // passarinhos (Dia 5): atravessam o céu da direita para a esquerda
  BIRDS.forEach(([col, y, s], i) => {
    const t0 = BIRD_T[i]; if (t < t0) return;
    const u = (t - t0) / 7.5; const x = lerp(3000 - i * 120, -300, u); if (x < -260) return;
    bird(FG, { x, y: y + 30 * Math.sin(t * 3 + i), s, col, seed: 950 + i * 10, flip: true, pose: Math.floor(t * 6 + i) % 2, draw: pr(t, t0, t0 + 0.4), fill: pr(t, t0 + 0.3, t0 + 0.7) });
  });
  // terra (com knock: o mar e o céu ficam atrás)
  const top = []; for (let x = -80; x <= 2780; x += 40) top.push([x, landTop2(x)]);
  part(LAND, [[-80, 1950], ...top, [2780, 1950]], { col: K.green, p: 0.82, gap: 12, w: 13, ang: 1.15, seed: 180, boil: 0, cross: true, crossP: 0.35 }, null);
  line(LAND.l, top, { w: 7.5, col: K.ink, seed: 181, boil: 0.6 });
  [[140, 0.95], [1960, 0.9]].forEach(([x, s], i) => tree(LAND, { x, y: landTop2(x) + 30, s, seed: 1550 + i * 20 }));
  [[90, K.pink], [470, K.yellow], [1180, K.white], [1560, K.pink], [2050, K.orange], [2350, K.yellow]].forEach(([x, c], i) => flower(LAND, { x, y: 1760 - hash(i) * 40, s: 1.2, col: c, seed: 1700 + i * 10 }));
  // animais (Dia 6)
  const ex = rest ? 'sleep' : undefined;
  const an = (k, fn, extra = {}) => { const t0 = AN_T[k]; if (t < t0) return; const [x, y, s] = POS[k]; fn(FG, { x, y, s, seed: { sheep: 500, rabbit: 600, lion: 700, elephant: 800 }[k], draw: pr(t, t0, t0 + 0.7), fill: pr(t, t0 + 0.5, t0 + 1.1), expr: ex, ...extra }); };
  an('sheep', sheep);
  const hopY = (t > 71.9 && t < 74.0) ? -Math.abs(Math.sin((t - 71.9) * 5)) * 50 : 0;
  { const t0 = AN_T.rabbit; if (t >= t0) { const [x, y, s] = POS.rabbit; rabbit(FG, { x, y: y + hopY, s, seed: 600, draw: pr(t, t0, t0 + 0.7), fill: pr(t, t0 + 0.5, t0 + 1.1), expr: ex }); } }
  an('lion', lion); an('elephant', elephant);
  // Adão e Eva (Dia 6): desenhados, depois de mãos dadas; o rosa nas bochechas; o coração
  const hold = ss(pr(t, 80.4, 80.9));
  const blush = 0.6 + 0.4 * pr(t, 83.0, 83.5);
  if (t >= AN_T.adam) { const [x, y, s] = POS.adam; person(FG, { x, y, s, kind: 'adam', seed: 2000, draw: pr(t, AN_T.adam, AN_T.adam + 0.9), fill: pr(t, AN_T.adam + 0.6, AN_T.adam + 1.4), expr: rest ? 'sleep' : 'smile', blush, armR: [[34, -196], [lerp(56, 62, hold), lerp(-150, -160, hold)], [lerp(62, 74, hold), lerp(-112, -126, hold)]] }); }
  if (t >= AN_T.eve) { const [x, y, s] = POS.eve; person(FG, { x, y, s, kind: 'eve', seed: 2200, draw: pr(t, AN_T.eve, AN_T.eve + 0.9), fill: pr(t, AN_T.eve + 0.6, AN_T.eve + 1.4), expr: rest ? 'sleep' : (t > 83.0 ? 'happy' : 'smile'), blush, armL: [[-34, -196], [lerp(-56, -62, hold), lerp(-150, -160, hold)], [lerp(-62, -78, hold), lerp(-112, -126, hold)]] }); }
  const hg = pr(t, 83.8, 84.4); if (hg > 0) heart(FG, { x: 895, y: 1120 + 6 * Math.sin(t * 3), s: 1.1 * eo(hg) * (1 + 0.04 * Math.sin(t * 6)), seed: 1300 });
  // descanso (Dia 7): "Zzz"
  if (rest) [[800, 1130], [990, 1140], [1400, 1290], [1880, 1300], [330, 1400]].forEach(([x, y], j) => { for (let k = 0; k < 3; k++) { const t0 = 94.2 + j * 0.3 + k * 1.4; const u = (t - t0) / 3.0; if (u < 0 || u > 1) continue; text(FX, 'z', sx(x + 40 + 50 * u), sy(y - 80 - 130 * u), { size: (40 + 34 * u) * CAM.s, font: 'Gochi Hand', p: 1 - pr(u, 0.6, 1), seed: 60 + j * 3 + k }); } });
  // "você": a criança desenhada no canto, a palavra e a seta
  if (t >= AN_T.child) { const [x, y, s] = POS.child; person(FG, { x, y, s, kind: 'child', seed: 2400, draw: pr(t, AN_T.child, AN_T.child + 1.2), fill: pr(t, AN_T.child + 1.0, AN_T.child + 1.9), expr: t > 106.2 ? 'wow' : 'smile', armR: t > 106.4 ? [[34, -196], [80, -230], [100, -290]] : undefined }); }
  if (t > 106.2) {
    const g = SUBK.g; // um retalho de papel para a palavra
    const cx = sx(2470), cy = sy(1390), hw = 170 * CAM.s, hh = 80 * CAM.s; paperPatch(FG.k.g, cx, cy, hw, hh);
    text(FX, 'VOCÊ', cx, cy + 32 * CAM.s, { size: 130 * CAM.s, font: 'Gochi Hand', col: K.red, reveal: pr(t, 106.2, 106.8), seed: 91, p: 1, stroke: 2 });
    const ag = pr(t, 106.8, 107.2); if (ag > 0) { line(FX, [[2400, 1460], [2330, 1530], [2290, 1590]], { w: 8, col: K.red, seed: 92, draw: ag }); if (ag >= 1) line(FX, [[2262, 1560], [2288, 1594], [2330, 1580]], { w: 8, col: K.red, seed: 93 }); }
    const hg2 = pr(t, 107.2, 107.7); if (hg2 > 0) heart(FG, { x: 2300, y: 1330, s: 0.5 * eo(hg2) * (1 + 0.05 * Math.sin(t * 6)), seed: 1320 });
  }
  if (subs) subTo(SUBK, SUBT, t);
  comp.paperCam(CAM.x * 0.6 + 3000, CAM.y * 0.6, CAM.s / 0.6); comp.begin();
  comp.crayon(BG.f.c); comp.crayon(BG.l.c);
  const go = [hash(BOIL.step) * 300, hash(BOIL.step + 7) * 300];
  comp.group(SUN, { goff: go }); comp.group(CL, { goff: go }); comp.group(LAND, { goff: go }); comp.group(FG, { goff: go }); comp.crayon(FX.c, { goff: go });
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig });
}
function paperPatch(g, cx, cy, hw, hh) {
  g.save(); g.fillStyle = '#000'; g.beginPath();
  for (let i = 0; i <= 60; i++) { const a = i / 60 * Math.PI * 2; const px = Math.cos(a), py = Math.sin(a); const sq = Math.pow(Math.abs(px), 0.3) * Math.sign(px); const n = 1 + 0.06 * Math.sin(a * 7 + 1.3) + 0.03 * Math.sin(a * 17); const X = cx + sq * hw * n, Y = cy + py * hh * n; i ? g.lineTo(X, Y) : g.moveTo(X, Y); }
  g.closePath(); g.fill(); g.restore();
}

// —— páginas do final ——
function leftPage(comp) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clear(TXT);
  text(TXT, 'E Deus viu que tudo', 960, 470, { size: 92, col: K.ink, seed: 301, p: 0.95, stroke: 1.5 });
  text(TXT, 'era muito bom.', 960, 590, { size: 92, col: K.ink, seed: 302, p: 0.95, stroke: 1.5 });
  text(TXT, 'Gênesis 1 e 2', 960, 720, { size: 60, col: K.ink, seed: 303, p: 0.8 });
  comp.paperCam(2000, 300, 1); comp.begin(); comp.crayon(TXT.c); comp.finish({ vig: 0, emb: 0.55 });
}
function endPage(comp, t) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clear(TXT); clearGroup(OBJ);
  text(TXT, 'Próxima história:', 960, 250, { size: 84, col: K.ink, seed: 311, p: 0.95, reveal: pr(t, 117.4, 118.2) });
  text(TXT, 'Adão e Eva no', 960, 400, { size: 140, font: 'Gochi Hand', col: K.green, seed: 312, p: 1, stroke: 2, reveal: pr(t, 118.2, 118.9) });
  text(TXT, 'Jardim do Éden', 960, 540, { size: 140, font: 'Gochi Hand', col: K.green, seed: 313, p: 1, stroke: 2, reveal: pr(t, 118.9, 119.6) });
  text(TXT, 'Inscreva-se!', 960, 700, { size: 96, font: 'Gochi Hand', col: K.red, seed: 314, p: 1, stroke: 2, reveal: pr(t, 119.6, 120.4) });
  const hg = pr(t, 120.4, 120.8); if (hg > 0) heart(OBJ, { x: 1290, y: 680, s: 0.55 * eo(hg), seed: 1330 });
  const ag = pr(t, 118.0, 118.8); if (ag > 0) tree(OBJ, { x: 1610, y: 620, s: 0.75, seed: 1590, draw: ag, fill: pr(t, 118.4, 119.2), fruit: pr(t, 119.0, 119.6) });
  comp.paperCam(4100, 700, 1); comp.begin(); comp.crayon(TXT.c); comp.group(OBJ); comp.finish({ vig: 0, emb: 0.55 });
}

// —— quadro ——
export function frame(comp, t) {
  // viradas de página em tela cheia
  if (t >= TURN1[0] && t < TURN1[1]) return turnFrame(comp, t, TURN1, (tt) => page0(comp, tt, FULL, { subs: false, vig: 0 }), (tt) => page1(comp, tt, FULL, { subs: false, vig: 0 }));
  if (t >= TURN2[0] && t < TURN2[1]) return turnFrame(comp, t, TURN2, (tt) => page1(comp, tt, FULL, { subs: false, vig: 0 }), (tt) => page2(comp, tt, FULL, { subs: false, vig: 0 }));
  if (t >= ENDT) return deskFrame(comp, t);
  const cam = camT(t);
  if (t < TURN1[0]) return page0(comp, t, cam);
  if (t < TURN2[0]) {
    // escuridão: a luz da página se apaga; o pontinho de luz pulsa; "Haja luz!" acende tudo
    const dim = 0.92 * ss(pr(t, 8.6, 9.8)) * (1 - pr(t, 21.45, 21.8));
    let glow = [0.5, 0.5, 0.1, 0];
    const [gx, gy] = [sx(SUNC[0]), sy(SUNC[1])];
    if (t > 17.0 && t < 21.45) glow = [gx / W, 1 - gy / H, 0.05 * CAM.s / 0.6 + 0.02, (0.28 + 0.1 * Math.sin(t * 4)) * pr(t, 17.0, 17.6)];
    if (t >= 21.45 && t < 22.8) glow = [gx / W, 1 - gy / H, lerp(0.08, 0.6, pr(t, 21.45, 22.0)), 1.1 * (1 - pr(t, 21.6, 22.8))];
    return page1(comp, t, cam, { dim, glow });
  }
  return page2(comp, t, cam);
}
function turnFrame(comp, t, [t0, t1], drawA, drawB) {
  drawA(t0); snap(PG.a);
  drawB(t1); snap(PG.b);
  comp.paperCam(700, 3100, 1); comp.begin(); comp.finish({ vig: 0, emb: 0.55 }); snap(PG.back);
  drawBook(book.g, turnAngle(t, t0, t1), { right: PG.a, next: PG.b, back: PG.back }, 960, 540, 1, 0);
  clear(SUBK); clear(SUBT); subTo(SUBK, SUBT, t);
  comp.paperCam(960, 540, 1); comp.begin(); comp.image(book.c); comp.knock(SUBK.c); comp.crayon(SUBT.c); comp.finish({ vig: 0.3 });
}
function deskFrame(comp, t) {
  const [cx, cy, z] = camD(t);
  page2(comp, t, FULL, { subs: false, vig: 0 }); snap(PG.a);
  leftPage(comp); snap(PG.left);
  endPage(comp, t); snap(PG.b);
  comp.paperCam(700, 3100, 1); comp.begin(); comp.finish({ vig: 0, emb: 0.55 }); snap(PG.back);
  const k = pr(t, ENDT, ENDT + 0.9);
  CAM.x = cx; CAM.y = cy; CAM.s = z;
  clear(DESK.f); clear(DESK.l); clearGroup(OBJ); clear(SUBK); clear(SUBT);
  drawDesk(DESK); drawCrayons(OBJ);
  drawBook(book.g, turnAngle(t, TURN3[0], TURN3[1]), { left: PG.left, right: PG.a, next: PG.b, back: PG.back }, cx, cy, z, k);
  subTo(SUBK, SUBT, t);
  comp.paperCam(cx, cy, z); comp.begin();
  if (k > 0) { comp.crayon(DESK.f.c); comp.crayon(DESK.l.c); }
  comp.image(book.c);
  if (k > 0) comp.group(OBJ, { goff: [hash(BOIL.step) * 200, 0] });
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig: 0.3 * k, emb: 0.55 * k, lamp: [0.42, 0.62, 0.62, 0.8 * k] });
}

// —— legendas: as palavras impressas do livro, escritas à mão sobre um retalho de papel ——
export function subTo(SK, ST, t) {
  const S = SUBS.find(s => t >= s.t0 && t < s.t1); if (!S) return;
  const rv = pr(t, S.t0, S.t0 + 0.35);
  const g = SK.g; g.save(); g.font = '400 54px "Patrick Hand"'; const tw = g.measureText(S.text).width; g.restore();
  const twoLines = tw > 1500;
  const parts = twoLines ? splitHalf(S.text) : [S.text];
  const w = twoLines ? Math.max(...parts.map(p => { g.save(); g.font = '400 54px "Patrick Hand"'; const m = g.measureText(p).width; g.restore(); return m; })) : tw;
  const cy = twoLines ? 972 : 1002;
  paperPatch(g, 960, cy, w / 2 + 46, twoLines ? 76 : 44);
  parts.forEach((p, i) => text(ST, p, 960, cy + 18 + (twoLines ? (i - 0.5) * 62 : 0), { size: 54, col: K.ink, reveal: clamp(rv * parts.length - i), seed: 11 + S.t0 * 3 + i, p: 1, stroke: 1.2 }));
}
function splitHalf(s) { const w = s.split(' '); let best = 1, bd = 1e9; for (let i = 1; i < w.length; i++) { const d = Math.abs(w.slice(0, i).join(' ').length - w.slice(i).join(' ').length); if (d < bd) { bd = d; best = i; } } return [w.slice(0, best).join(' '), w.slice(best).join(' ')]; }
