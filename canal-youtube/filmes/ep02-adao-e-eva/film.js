// Bíblia em Traços · Ep. 02 · Adão e Eva no Jardim do Éden — linha do tempo, câmera, página e eventos.
// Uma única página (3200×1800) num plano contínuo. Único wash: rosa-violeta do entardecer, que revela o coração de cera branca no céu.
import { layer, clear, line, fill, dab, text, handCircle, CAM, BOIL, W, H, sx, sy } from './crayon.js';
import { group, clearGroup, part } from './rig.js';
import { person, sheep, rabbit, lion, heart, cloud, tree, flower, giraffe, turtle, serpent, bush, house, fence, fruit } from './chars.js';
import { mk, snap, drawBook, drawDesk, drawCrayons, turnAngle } from './book.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, track, ss, eo, mulberry } from '/core/lib.js';
const K = PAL.crayon;
const OLIVE = '#7a8f3a';
const DUSK = [0.66, 0.42, 0.66];   // transmissão do wash rosa-violeta
const pr = (t, a, b) => clamp((t - a) / (b - a));
export const DUR = 139;
const FULL = [1600, 900, 0.6];

const VD = JSON.parse('{"vinheta":1.423,"titulo":2.19,"g1":4.681,"c1a":2.816,"c1b":5.832,"c2a":4.665,"c2b":3.538,"c3a":4.602,"c3b":3.081,"c4a":3.959,"c4b":6.435,"c5a":3.513,"c5b":4.421,"c5c":1.327,"c6a":4.002,"c6b":3.657,"c7a":4.725,"c7b":2.723,"c8a":4.459,"c8b":4.4,"c8c":3.699,"l1":3.471,"l2":3.471,"l3":4.426,"fim":3.834}');
const L = (id, t, text, sub = true) => ({ id, t, d: VD[id], text, sub });
export const LINES = [
  L('vinheta', 1.8, 'Bíblia em Traços!', false),
  L('titulo', 4.0, 'Adão e Eva, no Jardim do Éden.', false),
  L('g1', 7.8, 'Você já quis muito fazer uma coisa que alguém que te ama disse para não fazer?'),
  L('c1a', 13.8, 'Deus plantou um jardim lindo, chamado Éden.'),
  L('c1b', 17.6, 'Ali havia rios de água fresquinha, flores de todas as cores e árvores com frutas deliciosas.'),
  L('c2a', 24.6, 'Deus colocou Adão no jardim para cuidar dele. E Adão deu nome a cada animal:'),
  L('c2b', 30.2, 'o leão, a girafa, a tartaruga... Que trabalho divertido!'),
  L('c3a', 35.0, 'Mas Adão ainda não tinha alguém igual a ele, para conversar e dividir a vida.'),
  L('c3b', 40.6, 'Então Deus fez Eva, e Adão ficou muito feliz!'),
  L('c4a', 45.4, 'Deus disse: “Vocês podem comer de todas as árvores do jardim.'),
  L('c4b', 50.4, 'Só não comam desta árvore aqui, a árvore do conhecimento do bem e do mal. Ela vai fazer mal a vocês.”'),
  L('c5a', 58.0, 'Um dia, uma serpente muito esperta cochichou para Eva:'),
  L('c5b', 62.4, '“Deus não quer que vocês comam, porque vocês ficariam sabidos como Ele.”'),
  L('c5c', 67.8, 'Era uma mentira!'),
  L('c6a', 70.2, 'Eva olhou para a fruta... pegou, comeu, e deu para Adão, que também comeu.'),
  L('c6b', 76.0, 'Na mesma hora, eles se sentiram tristes e envergonhados.'),
  L('c7a', 81.0, 'À tardinha, quando ouviram Deus passeando no jardim, Adão e Eva se esconderam.'),
  L('c7b', 86.8, 'Mas ninguém consegue se esconder de Deus.'),
  L('c8a', 90.6, 'Desobedecer trouxe consequências: eles precisaram sair do jardim.'),
  L('c8b', 96.0, 'Mas Deus fez roupas quentinhas para eles, e continuou cuidando deles.'),
  L('c8c', 101.4, 'E prometeu que, um dia, mandaria alguém para consertar tudo.'),
  L('l1', 106.8, 'As regras de Deus são como uma cerca, que protege a gente.'),
  L('l2', 111.9, 'E mesmo quando a gente erra, Deus não deixa de nos amar.'),
  L('l3', 116.4, 'Converse com sua família: qual é uma regra da sua casa que protege você?'),
  L('fim', 125.4, 'Inscreva-se no canal! Na próxima história: Noé e a Grande Arca.'),
];
export const SUBS = LINES.filter(l => l.sub).map((l, i, A) => { const t0 = l.t - 0.1; let t1 = Math.max(t0 + 1.8, l.t + l.d + 0.7); const nx = A[i + 1]; if (nx) t1 = Math.min(t1, nx.t - 0.25); return { t0, t1, text: l.text }; });

const ENDT = 121.6, TURN3 = [124.0, 125.3];
const WALK = [91.6, 106.1];
const adamX = t => t < 82.2 ? 1250 : t < WALK[0] ? lerp(1250, 1760, ss(pr(t, 82.2, 83.6))) : lerp(1760, -260, pr(t, WALK[0], WALK[1]));

// —— câmera ——
const camT = track([
  [0, [560, 330, 1.2]], [6.2, [560, 330, 1.2]], [8.6, [1520, 1000, 1.55]], [12.6, [1520, 1000, 1.55]], [15.4, [1600, 920, 0.62]], [23.6, [1600, 920, 0.62]],
  [25.0, [1300, 1320, 1.15]], [29.8, [1300, 1320, 1.15]], [30.6, [1700, 1330, 1.0]], [33.6, [2420, 1330, 1.0]], [34.6, [2420, 1330, 1.0]],
  [35.8, [1330, 1330, 1.45]], [44.6, [1330, 1330, 1.45]], [46.2, [1580, 620, 0.9]], [49.6, [1560, 1000, 0.9]], [57.2, [1560, 1000, 0.9]],
  [59.0, [1500, 1150, 1.4]], [69.6, [1500, 1150, 1.4]], [70.8, [1390, 1260, 1.6]], [80.6, [1390, 1260, 1.6]], [82.4, FULL], [89.6, FULL],
  [91.4, [1800, 1350, 1.0]],
]);
const camFollow = t => [Math.max(620, adamX(t) + 90), 1350, 1.0];
const camLesson = track([[105.6, [Math.max(620, adamX(105.6) + 90), 1350, 1.0]], [107.4, [640, 1450, 1.25]], [ENDT, [640, 1450, 1.25]]]);
const cam = t => t < 91.4 ? camT(t) : t < 105.6 ? camFollow(t) : camLesson(t);
const camD = track([[ENDT, [960, 540, 1]], [123.4, [0, 580, 0.46]], [124.0, [0, 580, 0.46]], [126.4, [960, 540, 0.9]], [DUR, [960, 540, 0.92]]]);

// —— geometria da página ——
const hillTop = x => 1030 + 26 * Math.sin(x / 300 + 0.4) + 12 * Math.sin(x / 110);
const riverC = y => [lerp(2800, 2960, pr(y, 1010, 1800)) + 40 * Math.sin(y / 120), lerp(36, 170, pr(y, 1010, 1800))];
const TREE = [1600, 1180, 1.55];
const FRUIT0 = [1478, 1150];
const HEART = [1650, 400, 2.6];
const TREES = [[850, 1190, 1.0], [2300, 1170, 1.1], [3120, 1160, 0.85]];
const FLOW = [[180, K.pink], [430, K.yellow], [620, K.white], [1060, K.orange], [1780, K.pink], [2080, K.white], [2560, K.yellow], [3080, K.pink]];
const POS = { adam: [1250, 1500, 1.2], eve: [1430, 1500, 1.15], lion: [1950, 1500, 1.1], giraffe: [2280, 1490, 1.0], turtle: [2600, 1560, 1.2], sheep: [700, 1580, 1.3], rabbit: [980, 1640, 1.1], bush: [1850, 1570, 1.1], house: [520, 1580, 1.0], child: [780, 1620, 1.0] };
const NAMES = [['LEÃO', 1950, 1250, 30.6], ['GIRAFA', 2480, 1160, 31.3], ['TARTARUGA', 2640, 1400, 32.1]];
const AN = { lion: 30.2, giraffe: 30.9, turtle: 31.7 };
const BANDS = [
  { y0: 1100, y1: 1920, t0: 81.2, t1: 82.8, dir: -1, seed: 1 },
  { y0: 600, y1: 1200, t0: 82.6, t1: 84.4, dir: 1, seed: 2 },
  { y0: -150, y1: 700, t0: 85.6, t1: 87.6, dir: -1, seed: 3 },
];
const X0 = -700, X1 = 3460;
function bandFront(b, t) { const u = clamp((t - b.t0) / (b.t1 - b.t0)); const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; const v = 0.15 * u + 0.85 * e; return b.dir > 0 ? lerp(X0, X1, v) : lerp(X1, X0, v); }
const HEART_T = (() => { const b = BANDS[2]; const u = (X1 - HEART[0]) / (X1 - X0); return lerp(b.t0, b.t1, 0.5 * u + 0.25); })();

// —— eventos ——
export const EV = [];
const ev = (t, type, o = {}) => EV.push({ t: +t.toFixed(3), type, ...o });
LINES.forEach(l => ev(l.t, 'voice', { id: l.id }));
ev(0, 'paper'); ev(0.2, 'write', { dur: 1.6, pan: -0.6 }); ev(3.6, 'write', { dur: 1.2, pan: -0.5 }); ev(4.8, 'write', { dur: 1.0, pan: -0.5 });
ev(6.6, 'scratch', { dur: 1.6, pan: 0 }); ev(7.6, 'scribble', { dur: 1.4 }); ev(8.6, 'pop'); ev(9.0, 'glint', { pan: -0.1 });
ev(13.6, 'scribble', { dur: 2.2, pan: 0 }); ev(13.8, 'scratch', { dur: 0.8, pan: -0.5 }); ev(14.4, 'scribble', { dur: 2.0, pan: -0.3 }); ev(15.4, 'scribble', { dur: 1.4, pan: 0.7 }); ev(15.6, 'water', { dur: 1.2 });
TREES.forEach((_, i) => ev(17.6 + i * 0.6, 'scratch', { dur: 0.6, pan: -0.6 + i * 0.6 }));
FLOW.forEach((_, i) => ev(19.0 + i * 0.3, 'pop', { pan: -0.8 + i * 0.22 }));
ev(20.2, 'scratch', { dur: 0.6, pan: -0.5 }); ev(20.8, 'sheep'); ev(21.0, 'scratch', { dur: 0.5, pan: -0.3 }); ev(21.6, 'rabbit');
ev(25.0, 'scratch', { dur: 1.0, pan: -0.2 }); ev(25.6, 'scribble', { dur: 0.8, pan: -0.2 });
Object.entries(AN).forEach(([k, t]) => { ev(t, 'scratch', { dur: 0.6, pan: 0.4 }); ev(t + 0.6, k); });
NAMES.forEach(([, , , t]) => ev(t, 'write', { dur: 0.5, pan: 0.5 }));
ev(41.0, 'scratch', { dur: 1.0, pan: 0.2 }); ev(41.6, 'scribble', { dur: 0.8, pan: 0.2 }); ev(42.8, 'heart');
ev(45.4, 'glow', { dur: 11.4 }); ev(51.8, 'glint', { pan: -0.1 });
ev(58.2, 'scratch', { dur: 1.0, pan: 0.3 }); ev(59.4, 'hiss', { pan: 0.3 }); ev(63.6, 'hiss', { pan: 0.3 }); ev(65.8, 'hiss', { pan: 0.3 });
ev(70.8, 'reach'); ev(72.0, 'bite', { pan: 0.1 }); ev(73.1, 'reach'); ev(73.8, 'bite', { pan: -0.1 }); ev(74.3, 'silence', { dur: 1.5 });
ev(77.0, 'scribble', { dur: 0.6 });
ev(81.6, 'scratch', { dur: 0.8, pan: 0.4 }); ev(82.2, 'hide', { dur: 1.4 });
BANDS.forEach(b => ev(b.t0, 'brush', { dur: b.t1 - b.t0, dir: b.dir })); ev(81.0, 'dip');
ev(HEART_T, 'reveal');
ev(90.8, 'hide', { dur: 0.6 });
for (let t = WALK[0]; t < WALK[1]; t += 0.45) ev(t, 'step', { pan: clamp((adamX(t) - 1600) / 1600, -1, 1) * 0.5 });
ev(96.8, 'scribble', { dur: 1.2, pan: -0.2 }); ev(101.4, 'ray', { dur: 3.0 });
ev(107.2, 'fence', { dur: 2.6 }); ev(108.0, 'scratch', { dur: 1.0, pan: -0.4 }); ev(110.4, 'silence', { dur: 1.4 }); ev(112.4, 'heart');
ev(ENDT, 'room'); ev(TURN3[0], 'page', { dur: TURN3[1] - TURN3[0] }); ev(125.4, 'write', { dur: 2.2 }); ev(127.6, 'write', { dur: 1.0 });
[['A', 0], ['B', 7.6], ['C', 13.6], ['D', 35.0], ['E', 40.6], ['F', 45.4], ['G', 58.0], ['H', 70.2], ['I', 75.8], ['J', 81.0], ['K', 90.6], ['L', 106.2], ['M', ENDT]].forEach(([id, t]) => ev(t, 'cue', { id }));

// —— camadas ——
const WAX = group(), BG = { f: layer(), l: layer() }, LAND = group(), FG = group(), FRONT = group(), TOP = group(), WASH = layer(), FX = layer(), SUBK = layer(), SUBT = layer(), TXT = layer();
const DESK = { f: layer(), l: layer() }, OBJ = group(), book = mk();
const PG = { a: mk(), b: mk(), back: mk(), left: mk() };

function specialTree(C, t) {
  const [x, y, s] = TREE; const g = pr(t, 6.6, 8.2), f = pr(t, 7.6, 9.0); if (g <= 0) return;
  part(C, [[x - 26 * s, y], [x - 20 * s, y - 170 * s], [x + 20 * s, y - 170 * s], [x + 26 * s, y]], { col: K.brown, p: 0.9, gap: 8, w: 10, ang: 1.5, seed: 3100, draw: f }, { w: 8, col: K.ink, seed: 3101, draw: g });
  line(C.l, [[x - 8 * s, y - 110 * s], [x - 50 * s, y - 70 * s], [FRUIT0[0] + 4, FRUIT0[1] - 28]], { w: 9, col: K.brown, seed: 3102, draw: g });
  const crown = []; for (let i = 0; i <= 80; i++) { const a = i / 80 * 6.283; const b = 1 + 0.12 * Math.abs(Math.sin(a * 5)); crown.push([x + Math.cos(a) * 140 * s * b, y - 260 * s + Math.sin(a) * 120 * s * b]); }
  part(C, crown, { col: K.yellow, p: 0.95, gap: 11, w: 13, ang: 0.8, seed: 3103, cross: true, crossP: 0.5, draw: f }, { w: 8, col: K.orange, seed: 3104, draw: g });
  if (f > 0.6) for (let i = 0; i < 22; i++) { const a = hash(i) * 6.28, r = 40 + hash(i + 7) * 100; dab(C.f, x + Math.cos(a) * r * s, y - 260 * s + Math.sin(a) * r * 0.85 * s, 10 * s, { col: K.orange, p: 0.9, seed: 3110 + i }); }
  if (f > 0.9) [[-70, -300], [50, -320], [80, -230], [-20, -210], [-90, -235], [10, -350]].forEach(([dx, dy], i) => fruit(C, x + dx * s, y + dy * s, 20, 3200 + i * 7));
}
function garden(t) {
  // céu, montes, chão
  const skyP = pr(t, 13.6, 15.8);
  if (skyP > 0) fill(BG.f, [[-80, -80], [3280, -80], [3280, 1080], [-80, 1080]], { col: K.sky, p: 0.5, gap: 15, w: 14, ang: -0.25, seed: 60, draw: skyP, boil: 0, over: 0 });
  const top = []; for (let x = -80; x <= 3280; x += 40) top.push([x, hillTop(x)]);
  const gL = pr(t, 13.8, 14.6), gF = pr(t, 14.4, 16.4);
  if (gF > 0) fill(BG.f, [...top, [3280, 1900], [-80, 1900]], { col: K.green, p: 0.8, gap: 12, w: 13, ang: 1.15, seed: 61, draw: gF, boil: 0, cross: true, crossP: 0.35, over: 0 });
  if (gL > 0) line(BG.l, top, { w: 7, col: K.ink, seed: 62, draw: gL, boil: 0.6 });
  // rio
  const rv = pr(t, 15.4, 16.8);
  if (rv > 0) {
    const Lr = [], Rr = []; for (let y = 1010; y <= 1880; y += 30) { const [c, w] = riverC(y); Lr.push([c - w, y]); Rr.push([c + w, y]); }
    part(LAND, [...Lr, ...Rr.reverse()], { col: K.teal, p: 0.85, gap: 9, w: 11, ang: 0.2, seed: 70, draw: rv, cross: true, crossP: 0.4 }, null);
    line(LAND.l, Lr, { w: 6, col: K.ink, seed: 71, draw: rv }); line(LAND.l, [...Rr].reverse(), { w: 6, col: K.ink, seed: 72, draw: rv });
    if (rv >= 1) for (let i = 0; i < 6; i++) { const y = 1150 + i * 120, [c] = riverC(y); line(LAND.l, [[c - 20, y], [c - 10, y + 8], [c, y], [c + 10, y + 8], [c + 20, y]], { w: 4.5, col: K.white, p: 0.95, seed: 73 + i, boil: 0.6 }); }
  }
  [[600, 260, 1.0], [2500, 220, 0.9]].forEach(([x, y, s], i) => { const g = pr(t, 16.0 + i * 0.4, 16.6 + i * 0.4); if (g > 0) cloud(LAND, { x, y, s, seed: 1400 + i * 10, draw: g, fill: pr(t, 16.3 + i * 0.4, 16.9 + i * 0.4) }); });
  TREES.forEach(([x, y, s], i) => { const t0 = 17.6 + i * 0.6, g = pr(t, t0, t0 + 0.6); if (g > 0) tree(LAND, { x, y, s, seed: 1500 + i * 20, draw: g, fill: pr(t, t0 + 0.4, t0 + 1.0), fruit: pr(t, t0 + 0.8, t0 + 1.2) }); });
  FLOW.forEach(([x, c], i) => { const g = pr(t, 19.0 + i * 0.3, 19.4 + i * 0.3); if (g > 0) flower(LAND, { x, y: 1720 - hash(i + 3) * 60, s: 1.2, col: c, seed: 1600 + i * 10, g: eo(g) }); });
  specialTree(LAND, t);
}

function page(comp, t, camv, { subs = true, vig = 0.3, glow = null } = {}) {
  [CAM.x, CAM.y, CAM.s] = camv; BOIL.amp = t > 87 && t < 90.6 ? 0.6 : 1;
  clearGroup(WAX); clearGroup(LAND); clearGroup(FG); clearGroup(FRONT); clearGroup(TOP);
  [BG.f, BG.l, WASH, FX, SUBK, SUBT].forEach(clear);
  // o coração de cera branca: está no céu desde o primeiro quadro, invisível até o entardecer
  heart({ k: WAX.k, f: WAX.f, l: WAX.f }, { x: HEART[0], y: HEART[1], s: HEART[2], col: K.white, lineCol: K.white, seed: 3300 });
  // título no canto da página
  text(BG.l, 'Bíblia em Traços', sx(520), sy(205), { size: 70 * CAM.s, font: 'Patrick Hand', col: K.ink, reveal: pr(t, 0.2, 1.8), seed: 21, p: 0.95 });
  if (t > 1.2) line(BG.l, [[330, 228], [520, 236], [710, 230]], { w: 8, col: K.red, seed: 22, draw: pr(t, 1.8, 2.3) });
  text(BG.l, 'Adão e Eva', sx(520), sy(340), { size: 150 * CAM.s, font: 'Gochi Hand', col: K.ink, reveal: pr(t, 3.6, 4.8), seed: 23, p: 0.95, stroke: 2 });
  text(BG.l, 'no Jardim do Éden', sx(520), sy(455), { size: 96 * CAM.s, font: 'Gochi Hand', col: K.green, reveal: pr(t, 4.8, 5.8), seed: 24, p: 1, stroke: 2 });
  garden(t);
  // fruta do galho baixo (até Eva pegar)
  const taken = t > 71.2;
  if (!taken && t > 8.6) fruit(LAND, FRUIT0[0], FRUIT0[1] + 4 * Math.sin(t * 2), 26 * eo(pr(t, 8.6, 9.0)), 3290);
  // bichos de antes (jardim) e os que recebem nome
  const exA = t > 87 && t < 92 ? 'sleep' : undefined;
  if (t > 20.2) sheep(FG, { x: POS.sheep[0], y: POS.sheep[1], s: POS.sheep[2], seed: 500, draw: pr(t, 20.2, 20.8), fill: pr(t, 20.6, 21.2), expr: exA });
  if (t > 21.0) rabbit(FG, { x: POS.rabbit[0], y: POS.rabbit[1], s: POS.rabbit[2], seed: 600, draw: pr(t, 21.0, 21.6), fill: pr(t, 21.4, 22.0), expr: exA });
  if (t > AN.lion) lion(FG, { x: POS.lion[0], y: POS.lion[1], s: POS.lion[2], seed: 700, draw: pr(t, AN.lion, AN.lion + 0.6), fill: pr(t, AN.lion + 0.4, AN.lion + 1.0), expr: exA });
  if (t > AN.giraffe) giraffe(FG, { x: POS.giraffe[0], y: POS.giraffe[1], s: POS.giraffe[2], seed: 1700, draw: pr(t, AN.giraffe, AN.giraffe + 0.6), fill: pr(t, AN.giraffe + 0.4, AN.giraffe + 1.0), expr: exA });
  if (t > AN.turtle) turtle(FG, { x: POS.turtle[0], y: POS.turtle[1], s: POS.turtle[2], seed: 1800, draw: pr(t, AN.turtle, AN.turtle + 0.6), fill: pr(t, AN.turtle + 0.4, AN.turtle + 1.0) });
  NAMES.forEach(([w, x, y, t0], i) => { if (t > t0) text(FX, w, sx(x), sy(y), { size: 76 * CAM.s, font: 'Gochi Hand', col: K.red, reveal: pr(t, t0, t0 + 0.5), seed: 80 + i, p: 1, stroke: 2 }); });
  // a serpente (só enquanto conversa com Eva)
  if (t > 58.2 && t < 81.0) serpent(FG, { x: 1700, y: 1010, s: 1.1, flip: true, seed: 1900, draw: pr(t, 58.2, 59.2), fill: pr(t, 58.8, 59.6), tongue: t > 62.4 && t < 67.0 && Math.floor(t * 4) % 2 === 0, look: t > 67.8 ? 1 : -1 });
  // Adão e Eva
  const ax = adamX(t), walking = t > WALK[0] && t < WALK[1], hiding = t > 83.6 && t < 90.8;
  const ay = hiding || (t > 82.2 && t < WALK[0]) ? lerp(1500, 1580, ss(pr(t, 82.2, 83.6))) : 1500;
  const fur = pr(t, 96.8, 98.0);
  const sad = (t > 35.4 && t < 41.6) ? 'adam' : (t > 74.6 && t < 98.4) ? 'both' : '';
  let aArm, eArmR, eArmL, aExpr = 'smile', eExpr = 'smile';
  if (t > 30.0 && t < 34.4) aArm = [[34, -196], [70, -240], [96, -290]];
  if (t > 41.8 && t < 44.0) aExpr = 'happy';
  if (sad === 'adam') aExpr = 'sad';
  if (sad === 'both') { aExpr = 'sad'; eExpr = 'sad'; }
  if (t > 59 && t < 67.8) eExpr = 'wow';
  if (t > 98.4 && t < 106.2) { aExpr = 'smile'; eExpr = 'smile'; }
  // a fruta: Eva pega, morde, entrega a Adão, ele morde, ela cai no chão
  let fr = null;
  if (t > 70.6 && t < 71.2) eArmR = [[34, -196], [50, -240], [44, -300]];
  if (t >= 71.2 && t < 72.9) { eArmR = [[34, -196], [40, -230], [14, -236]]; fr = { who: 'eve', bite: t > 72.0 ? 1 : 0 }; }
  if (t >= 72.9 && t < 73.5) { eArmL = [[-34, -196], [-60, -200], [-82, -190]]; aArm = [[34, -196], [60, -200], [70, -190]]; fr = { who: 'give', bite: 1 }; }
  if (t >= 73.5 && t < 74.6) { aArm = [[34, -196], [40, -230], [14, -236]]; fr = { who: 'adam', bite: 1 }; }
  if (t >= 74.6 && t < 81.0) fr = { who: 'ground', bite: 1 };
  const blush = t > 77.0 && t < 96 ? 1 + 1.2 * pr(t, 77.0, 77.6) : 1;
  const wph = walking ? t * 7 : undefined;
  const gone = t > WALK[1];
  if (t > 25.0 && !gone) person(FG, { x: ax, y: ay, s: POS.adam[2], kind: 'adam', seed: 2000, draw: pr(t, 25.0, 26.0), fill: pr(t, 25.6, 26.6), expr: aExpr, armR: aArm, blush, fur, walk: wph, flip: walking });
  if (t > 41.0 && !gone) person(FG, { x: ax + 180, y: ay, s: POS.eve[2], kind: 'eve', seed: 2200, draw: pr(t, 41.0, 42.0), fill: pr(t, 41.6, 42.4), expr: eExpr, armR: eArmR, armL: eArmL, blush, fur, walk: wph === undefined ? undefined : wph + 1.6, flip: walking });
  if (fr) {
    const P = fr.who === 'eve' ? [ax + 180 + 14 * 1.15, ay - 236 * 1.15] : fr.who === 'give' ? [ax + 84, ay - 228] : fr.who === 'adam' ? [ax + 17, ay - 283] : [1340, 1505];
    fruit(FG, P[0], P[1], 24, 3290, fr.bite);
  }
  const hg = pr(t, 42.8, 43.4); if (hg > 0 && t < 46) heart(TOP, { x: 1340, y: 1110, s: 1.0 * eo(hg), seed: 1310 });
  // o arbusto onde eles se escondem (na frente deles)
  if (t > 81.6) bush(FRONT, { x: POS.bush[0], y: POS.bush[1], s: POS.bush[2], draw: pr(t, 81.6, 82.2), fill: pr(t, 82.0, 82.6) });
  // raio de luz do coração até eles (o cuidado de Deus)
  if (t > 101.4 && t < 106.2) { const g = pr(t, 101.4, 102.4); for (let k = -1; k <= 1; k++) line(TOP.l, [[HEART[0] + k * 30, HEART[1] + 120], [ax + 90 + k * 60, ay - 420]], { w: 6, col: K.yellow, p: 0.95, seed: 3400 + k, draw: g, taper: 0.5 }); }
  // lição: a casinha, a criança e a cerca
  if (t > 106.2) {
    house(TOP, { x: POS.house[0], y: POS.house[1], s: POS.house[2], draw: pr(t, 106.4, 107.2), fill: pr(t, 106.8, 107.6) });
    person(TOP, { x: POS.child[0], y: POS.child[1], s: POS.child[2], kind: 'child', seed: 2400, draw: pr(t, 106.8, 107.8), fill: pr(t, 107.4, 108.2), expr: t > 112.2 ? 'happy' : 'smile', armR: t > 116.4 ? [[34, -196], [80, -230], [100, -290]] : undefined });
    const pts = []; for (let x = 250; x <= 1030; x += 65) pts.push([x, 1740]);
    fence(TOP, { pts, g: pr(t, 107.2, 109.8), seed: 3500 });
    const h2 = pr(t, 112.4, 113.0); if (h2 > 0) heart(TOP, { x: 650, y: 1160, s: 0.9 * eo(h2) * (1 + 0.05 * Math.sin(t * 6)), seed: 1320 });
  }
  if (t > BANDS[0].t0) drawWash(WASH, t);
  if (subs) subTo(SUBK, SUBT, t);
  comp.paperCam(CAM.x * 0.6 + 1200, CAM.y * 0.6, CAM.s / 0.6); comp.begin();
  comp.group(WAX); comp.crayon(BG.f.c); comp.crayon(BG.l.c);
  const go = [hash(BOIL.step) * 300, hash(BOIL.step + 7) * 300];
  comp.group(LAND, { goff: go });
  if (t > BANDS[0].t0) comp.wash(WASH.c, { color: DUSK, resist: 0.93 });
  comp.group(FG, { goff: go }); comp.group(FRONT, { goff: go }); comp.group(TOP, { goff: go }); comp.crayon(FX.c, { goff: go });
  comp.knock(SUBK.c); comp.crayon(SUBT.c);
  comp.finish({ vig, glow: glow || [0.5, 0.5, 0.1, 0] });
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

// —— final ——
function leftPage(comp) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clear(TXT);
  text(TXT, 'E Deus continuou', 960, 470, { size: 92, col: K.ink, seed: 301, p: 0.95, stroke: 1.5 });
  text(TXT, 'cuidando deles.', 960, 590, { size: 92, col: K.ink, seed: 302, p: 0.95, stroke: 1.5 });
  text(TXT, 'Gênesis 2 e 3', 960, 720, { size: 60, col: K.ink, seed: 303, p: 0.8 });
  comp.paperCam(2000, 300, 1); comp.begin(); comp.crayon(TXT.c); comp.finish({ vig: 0, emb: 0.55 });
}
function endPage(comp, t) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clear(TXT); clearGroup(OBJ);
  text(TXT, 'Próxima história:', 960, 250, { size: 84, col: K.ink, seed: 311, p: 0.95, reveal: pr(t, 125.4, 126.2) });
  text(TXT, 'Noé e a', 960, 400, { size: 140, font: 'Gochi Hand', col: K.sky, seed: 312, p: 1, stroke: 2, reveal: pr(t, 126.2, 126.8) });
  text(TXT, 'Grande Arca', 960, 540, { size: 140, font: 'Gochi Hand', col: K.sky, seed: 313, p: 1, stroke: 2, reveal: pr(t, 126.8, 127.6) });
  text(TXT, 'Inscreva-se!', 960, 700, { size: 96, font: 'Gochi Hand', col: K.red, seed: 314, p: 1, stroke: 2, reveal: pr(t, 127.6, 128.4) });
  const hg = pr(t, 128.4, 128.8); if (hg > 0) heart(OBJ, { x: 1290, y: 680, s: 0.55 * eo(hg), seed: 1330 });
  const rg = pr(t, 126.0, 127.4); [K.red, K.orange, K.yellow, K.green, K.sky].forEach((c, i) => { const r = 150 - i * 20; const pts = []; for (let k = 0; k <= 30; k++) { const a = Math.PI + k / 30 * Math.PI; pts.push([1620 + Math.cos(a) * r, 560 + Math.sin(a) * r]); } line(OBJ.l, pts, { w: 16, col: c, p: 1, seed: 1340 + i, draw: clamp(rg * 1.4 - i * 0.08) }); });
  comp.paperCam(4100, 700, 1); comp.begin(); comp.crayon(TXT.c); comp.group(OBJ); comp.finish({ vig: 0, emb: 0.55 });
}
export function frame(comp, t) {
  if (t >= ENDT) return deskFrame(comp, t);
  let glow = null;
  if (t > 45.4 && t < 57.0) { const k = pr(t, 45.4, 46.4) * (1 - pr(t, 56.0, 57.0)); const c = cam(t); [CAM.x, CAM.y, CAM.s] = c; glow = [sx(TREE[0]) / W, 1 - sy(TREE[1] - 400) / H, 0.22, (0.22 + 0.06 * Math.sin(t * 2.5)) * k]; }
  if (t > 101.4 && t < 106.2) { const k = pr(t, 101.4, 102.4) * (1 - pr(t, 105.4, 106.2)); const c = cam(t); [CAM.x, CAM.y, CAM.s] = c; glow = [sx(adamX(t) + 90) / W, 1 - sy(1300) / H, 0.16, 0.28 * k]; }
  return page(comp, t, cam(t), { glow });
}
function deskFrame(comp, t) {
  const [cx, cy, z] = camD(t);
  page(comp, t, FULL, { subs: false, vig: 0 }); snap(PG.a);
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

function paperPatch(g, cx, cy, hw, hh) {
  g.save(); g.fillStyle = '#000'; g.beginPath();
  for (let i = 0; i <= 60; i++) { const a = i / 60 * Math.PI * 2; const px = Math.cos(a), py = Math.sin(a); const sq = Math.pow(Math.abs(px), 0.3) * Math.sign(px); const n = 1 + 0.06 * Math.sin(a * 7 + 1.3) + 0.03 * Math.sin(a * 17); const X = cx + sq * hw * n, Y = cy + py * hh * n; i ? g.lineTo(X, Y) : g.moveTo(X, Y); }
  g.closePath(); g.fill(); g.restore();
}
export function subTo(SK, ST, t) {
  const S = SUBS.find(s => t >= s.t0 && t < s.t1); if (!S) return;
  const rv = pr(t, S.t0, S.t0 + 0.35);
  const g = SK.g; const mw = s => { g.save(); g.font = '400 54px "Patrick Hand"'; const m = g.measureText(s).width; g.restore(); return m; };
  const tw = mw(S.text), two = tw > 1500;
  const parts = two ? splitHalf(S.text) : [S.text];
  const w = Math.max(...parts.map(mw)), cy = two ? 972 : 1002;
  paperPatch(g, 960, cy, w / 2 + 46, two ? 76 : 44);
  parts.forEach((p, i) => text(ST, p, 960, cy + 18 + (two ? (i - 0.5) * 62 : 0), { size: 54, col: K.ink, reveal: clamp(rv * parts.length - i), seed: 11 + S.t0 * 3 + i, p: 1, stroke: 1.2 }));
}
function splitHalf(s) { const w = s.split(' '); let best = 1, bd = 1e9; for (let i = 1; i < w.length; i++) { const d = Math.abs(w.slice(0, i).join(' ').length - w.slice(i).join(' ').length); if (d < bd) { bd = d; best = i; } } return [w.slice(0, best).join(' '), w.slice(best).join(' ')]; }
