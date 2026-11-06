// Livro para colorir "Bíblia em Traços": capa + 20 histórias + página livre. A4 retrato (1240×1754 = 150 dpi).
// Cada página é desenhada colorida; o script de exportação tira só o contorno marrom para a versão de pintar.
import { layer, clear, line, fill, dab, text, handCircle, ellipse, smooth, CAM, BOIL, W, H, MODE } from './crayon.js';
import { group, clearGroup, part, tube, curve } from './rig.js';
import { person, sheep, rabbit, lion, elephant, fish, bird, sun, moon, heart, cloud, tree, giraffe, turtle, serpent, bush, house, fence, baby } from './chars.js';
import { PAL } from './pal.js';
import { hash } from '/core/lib.js';
const K = PAL.crayon, INK = K.ink;
const BG = { f: layer(), l: layer() }, G = group(), TOP = group(), TX = layer();
const ol = (s, w = 7, col = INK) => ({ w, col, seed: s });
const fl = (col, s, p = 0.85, o = {}) => ({ col, p, gap: 10, w: 12, seed: s, ...o });
const O = (C, pts, col, s, w = 7) => part(C, pts, col ? fl(col, s) : null, ol(s + 1, w));
const Tt = (str, x, y, size, o = {}) => text(TX, str, x, y, { size, font: o.font || 'Gochi Hand', col: o.col || INK, p: 1, stroke: o.font === 'Patrick Hand' ? 1 : 2, seed: x * 0.1 + y * 0.03 });
const circ = (x, y, r, s) => handCircle(x, y, r, s, 0, 40);
function ground(y, s = 1) { const top = []; for (let x = -40; x <= W + 40; x += 30) top.push([x, y + 18 * Math.sin(x / 200 + s)]); part(G, [[-40, H + 40], ...top, [W + 40, H + 40]], fl(K.green, 80 + s, 0.8, { ang: 1.15, boil: 0 }), null); line(G.l, top, ol(81 + s)); }
function skyFill(y1) { fill(BG.f, [[-40, -40], [W + 40, -40], [W + 40, y1], [-40, y1]], { col: K.sky, p: 0.45, gap: 15, w: 14, ang: -0.25, seed: 60, boil: 0, over: 0 }); }
function waves(y0, y1, s = 3) { const top = []; for (let x = -40; x <= W + 40; x += 30) top.push([x, y0 + 16 * Math.sin(x / 70 + s)]); part(G, [[-40, y1], ...top, [W + 40, y1]], fl(K.teal, 90 + s, 0.85, { ang: 0.15, boil: 0 }), null); line(G.l, top, ol(91 + s)); }
function star(C, x, y, r, s, col = K.yellow) { const pts = []; for (let k = 0; k <= 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5; const rr = k % 2 ? r * 0.45 : r; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); } part(C, pts, fl(col, s, 1, { gap: 5, w: 7 }), ol(s + 1, 5)); }
function flowerO(C, x, y, s, col) { line(C.l, [[x, y], [x, y - 50 * s]], ol(s * 7 + x, 6, INK)); for (let i = 0; i < 5; i++) { const a = i / 5 * 6.28; part(C, circ(x + Math.cos(a) * 15 * s, y - 50 * s + Math.sin(a) * 15 * s, 11 * s, x + i), fl(col, x + i * 3, 0.95, { gap: 4, w: 6 }), ol(x + i * 5, 4)); } part(C, circ(x, y - 50 * s, 9 * s, x + 9), fl(K.yellow, x + 11, 1, { gap: 4, w: 6 }), ol(x + 12, 4)); }
function fruitO(C, x, y, r, s) { part(C, circ(x, y, r, s), fl(K.red, s, 1, { gap: 5, w: 7 }), ol(s + 1, 5)); line(C.l, [[x, y - r], [x + 4, y - r - 14]], ol(s + 2, 4)); }
function staff(C, x0, y0, x1, y1, s) { if (MODE.nofill) { const dx = y1 - y0, dy = x0 - x1, n = Math.hypot(dx, dy) || 1; [-7, 7].forEach((d, j) => line(C.l, [[x0 + dx / n * d, y0 + dy / n * d], [x1 + dx / n * d, y1 + dy / n * d]], { w: 4, seed: s + j })); return; } line(C.l, [[x0, y0], [x1, y1]], { w: 12, col: INK, seed: s }); line(C.l, [[x0, y0], [x1, y1]], { w: 7, col: K.brown, seed: s + 1 }); }
const P = (x, y) => [x, y];

const PAGES = {
  capa() {
    skyFill(1100); sun(TOP, { x: 1080, y: 200, R: 80, face: 1, seed: 1100 });
    ground(1150);
    person(TOP, { x: 330, y: 1500, s: 1.2, kind: 'adam', seed: 2000, armR: [[34, -196], [62, -160], [74, -126]] });
    person(TOP, { x: 500, y: 1500, s: 1.15, kind: 'eve', seed: 2200, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] });
    lion(TOP, { x: 860, y: 1520, s: 1.1, seed: 700 }); sheep(TOP, { x: 150, y: 1540, s: 1.5, seed: 500 });
    elephant(TOP, { x: 1080, y: 1560, s: 0.9, seed: 800 });
    Tt('Meu livro de', 620, 470, 110); Tt('COLORIR', 620, 620, 190, { col: K.red });
    Tt('20 histórias da Bíblia para pintar', 620, 740, 62, { font: 'Patrick Hand' });
    Tt('Bíblia em Traços', 620, 1690, 70, { font: 'Patrick Hand' });
  },
  dono() {
    Tt('Este livro pertence a:', 620, 380, 110);
    line(TOP.l, [[200, 600], [1040, 600]], ol(30, 6)); line(TOP.l, [[200, 760], [1040, 760]], ol(31, 6));
    Tt('Minha idade:', 420, 950, 80, { font: 'Patrick Hand' }); part(TOP, circ(780, 930, 80, 33), null, ol(34));
    heart(TOP, { x: 620, y: 1300, s: 2.6, seed: 1300 });
    sun(TOP, { x: 220, y: 1250, R: 80, face: 1, seed: 1100 }); star(TOP, 1020, 1240, 70, 40);
    Tt('Deus fez você com muito amor!', 620, 1600, 66, { font: 'Patrick Hand' });
  },
  h01() { // A Criação
    sun(TOP, { x: 1000, y: 360, R: 100, face: 1, seed: 1100 }); cloud(TOP, { x: 300, y: 380, s: 1.0, seed: 1400 });
    bird(TOP, { x: 620, y: 480, s: 1.5, col: K.red, seed: 950, flip: true, pose: 1 });
    waves(980, 1250); fish(TOP, { x: 950, y: 1100, s: 1.2, col: K.orange, seed: 900, flip: true });
    ground(1050); tree(G, { x: 180, y: 1080, s: 1.0, seed: 1500, fruit: 1 });
    person(TOP, { x: 520, y: 1520, s: 1.3, kind: 'adam', seed: 2000, armR: [[34, -196], [62, -160], [74, -126]] });
    person(TOP, { x: 715, y: 1520, s: 1.25, kind: 'eve', seed: 2200, expr: 'happy', armL: [[-34, -196], [-62, -160], [-78, -126]] });
    lion(TOP, { x: 1010, y: 1540, s: 1.0, seed: 700 }); sheep(TOP, { x: 200, y: 1560, s: 1.6, seed: 500 });
  },
  h02() { // Adão e Eva
    skyFill(950); ground(950);
    const tx = 860, ty = 1300;
    O(G, [[tx - 40, ty], [tx - 30, ty - 300], [tx + 30, ty - 300], [tx + 40, ty], [tx - 40, ty]], K.brown, 3100);
    const crown = []; for (let i = 0; i <= 80; i++) { const a = i / 80 * 6.283; const b = 1 + 0.12 * Math.abs(Math.sin(a * 5)); crown.push([tx + Math.cos(a) * 270 * b, ty - 560 + Math.sin(a) * 230 * b]); }
    part(G, crown, fl(K.yellow, 3103, 0.95, { cross: true, crossP: 0.5 }), ol(3104));
    [[-120, -640], [80, -680], [160, -500], [-60, -440], [-200, -520], [20, -560]].forEach(([dx, dy], i) => fruitO(G, tx + dx, ty + dy, 30, 3200 + i * 7));
    serpent(TOP, { x: tx - 60, y: ty - 330, s: 1.6, flip: true, seed: 1900, tongue: true });
    person(TOP, { x: 260, y: 1560, s: 1.3, kind: 'adam', seed: 2000, expr: 'wow' });
    person(TOP, { x: 470, y: 1560, s: 1.25, kind: 'eve', seed: 2200, expr: 'wow', armR: [[34, -196], [66, -215], [86, -240]] });
    fruitO(TOP, 470 + 86 * 1.25, 1560 - 250 * 1.25, 34, 3290);
    rabbit(TOP, { x: 1080, y: 1600, s: 1.3, seed: 600 });
  },
  h03() { // Noé e a arca
    const R = [K.red, K.orange, K.yellow, K.green, K.sky]; R.forEach((c, i) => { const r = 520 - i * 38; const pts = []; for (let k = 0; k <= 40; k++) { const a = Math.PI + k / 40 * Math.PI; pts.push([620 + Math.cos(a) * r, 760 + Math.sin(a) * r]); } if (MODE.nofill) { [-17, 17].forEach((d, j) => line(BG.l, pts.map(([x, y]) => [620 + (x - 620) * (r + d) / r, 760 + (y - 760) * (r + d) / r]), { w: 4, col: INK, seed: 410 + i * 2 + j })); } else { line(BG.l, pts, { w: 34, col: c, p: 1, seed: 400 + i }); line(BG.l, pts, { w: 4, col: INK, seed: 410 + i, p: 0.8 }); } });
    waves(1300, H + 40);
    const hull = smooth([[140, 1060], [1100, 1060], [1040, 1320], [200, 1320]], 3); hull.push(hull[0]);
    O(G, hull, K.brown, 4300, 8);
    for (let i = 0; i < 3; i++) line(G.l, [[170 + i * 10, 1130 + i * 60], [1080 - i * 10, 1130 + i * 60]], ol(4310 + i, 4));
    O(G, [[320, 1060], [320, 860], [920, 860], [920, 1060], [320, 1060]], K.orange, 4320);
    O(G, [[280, 870], [620, 740], [960, 870], [280, 870]], K.red, 4330);
    [[400, 920], [560, 920], [720, 920]].forEach(([x, y], i) => O(G, [[x, y], [x + 100, y], [x + 100, y + 90], [x, y + 90], [x, y]], K.yellow, 4340 + i * 3, 5));
    giraffe(TOP, { x: 860, y: 1062, s: 0.95, seed: 1700 }); elephant(TOP, { x: 450, y: 1062, s: 0.6, seed: 800 });
    person(TOP, { x: 640, y: 1060, s: 0.75, kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.sky, seed: 2500, armR: [[34, -196], [70, -240], [96, -290]] });
    bird(TOP, { x: 1000, y: 330, s: 1.5, col: K.white, seed: 960, flip: true, pose: 1 });
    line(TOP.l, [[930, 336], [900, 350], [880, 340]], ol(4400, 5, K.green));
  },
  h04() { // Torre de Babel
    skyFill(1250); ground(1250); cloud(TOP, { x: 260, y: 300, s: 1.1, seed: 1400 }); cloud(TOP, { x: 1000, y: 520, s: 0.9, seed: 1410 });
    for (let i = 0; i < 7; i++) { const w = 560 - i * 66, y = 1260 - i * 140; O(G, [[620 - w / 2, y], [620 + w / 2, y], [620 + w / 2 - 20, y - 140], [620 - w / 2 + 20, y - 140], [620 - w / 2, y]], i % 2 ? K.orange : K.peach, 4500 + i * 5);
      for (let j = 0; j < 3; j++) O(G, [[620 - w / 2 + 50 + j * (w - 100) / 2 - 14, y - 100], [620 - w / 2 + 50 + j * (w - 100) / 2 + 14, y - 100], [620 - w / 2 + 50 + j * (w - 100) / 2 + 14, y - 50], [620 - w / 2 + 50 + j * (w - 100) / 2 - 14, y - 50]], K.brown, 4600 + i * 9 + j, 4); }
    person(TOP, { x: 220, y: 1600, s: 1.0, kind: 'man', cloth: K.red, seed: 2500, expr: 'wow' }); person(TOP, { x: 1010, y: 1600, s: 1.0, kind: 'woman', scarf: K.sky, cloth: K.orange, seed: 2700, expr: 'wow' });
    Tt('?', 220, 1100, 160); Tt('!?', 1010, 1100, 160);
  },
  h05() { // Abraão e as estrelas
    fill(BG.f, [[-40, -40], [W + 40, -40], [W + 40, 1150], [-40, 1150]], { col: K.sky, p: 0.7, gap: 12, w: 13, ang: -0.25, seed: 61, boil: 0, over: 0 });
    for (let i = 0; i < 26; i++) star(TOP, 80 + hash(i) * 1080, 260 + hash(i + 40) * 800, 18 + hash(i + 9) * 22, 500 + i * 3);
    moon(TOP, { x: 1020, y: 330, R: 100, seed: 1200 });
    ground(1150); O(G, [[700, 1350], [900, 1060], [1120, 1350], [700, 1350]], K.orange, 4700); line(G.l, [[900, 1060], [900, 1350]], ol(4710, 5));
    person(TOP, { x: 400, y: 1600, s: 1.35, kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.sky, seed: 2500, expr: 'wow', armL: [[-34, -196], [-80, -250], [-110, -310]] });
    staff(TOP, 400 + 70 * 1.35, 1600 - 230 * 1.35, 400 + 110 * 1.35, 1600, 4720);
  },
  h06() { // José e a túnica colorida
    skyFill(1050); ground(1050);
    [[260, 1050, 260], [520, 1050, 180]].forEach(([x, y, r], i) => O(G, [[x - r, y], [x, y - r * 1.1], [x + r, y], [x - r, y]], K.yellow, 4800 + i * 3));
    sun(TOP, { x: 1080, y: 480, R: 70, face: 1, seed: 1100 });
    person(TOP, { x: 680, y: 1600, s: 1.6, kind: 'man', cloth: K.white, stripes: [K.red, K.orange, K.yellow, K.green, K.sky, K.pink, K.red], seed: 2500, expr: 'happy', armL: [[-34, -196], [-90, -230], [-120, -280]], armR: [[34, -196], [90, -230], [120, -280]] });
    star(TOP, 300, 600, 40, 4850); star(TOP, 1050, 650, 40, 4860);
  },
  h07() { // O bebê Moisés no cesto
    skyFill(800); waves(800, H + 40);
    for (let i = 0; i < 9; i++) { const x = 60 + i * 50 + (i > 4 ? 760 : 0); line(G.l, [[x, 1500], [x + 10, 1050 - hash(i) * 120]], { w: 10, col: K.green, seed: 4900 + i }); part(G, ellipse(x + 12, 1030 - hash(i) * 120, 14, 50, 16), fl(K.brown, 4920 + i, 1, { gap: 5, w: 7 }), ol(4940 + i, 4)); }
    const bx = 620, by = 1180;
    O(G, smooth([[bx - 250, by - 60], [bx + 250, by - 60], [bx + 210, by + 90], [bx - 210, by + 90]], 3).concat([[bx - 250, by - 60]]), K.orange, 4960, 8);
    for (let i = 0; i < 4; i++) line(G.l, [[bx - 220 + i * 20, by - 20 + i * 30], [bx + 220 - i * 20, by - 20 + i * 30]], ol(4970 + i, 4));
    baby(TOP, { x: bx + 70, y: by - 60, s: 1.6, seed: 2600 });
    person(TOP, { x: 950, y: 790, s: 1.0, kind: 'woman', crown: true, cloth: K.pink, seed: 2700, expr: 'happy' });
    bird(TOP, { x: 260, y: 400, s: 1.4, col: K.sky, seed: 960, flip: true });
  },
  h08() { // A travessia do Mar Vermelho
    skyFill(700);
    [[-40, 420], [820, W + 40]].forEach(([a, b], k) => { const pts = []; for (let y = 600; y <= H + 40; y += 40) pts.push([k ? a + 30 * Math.sin(y / 60) : b + 30 * Math.sin(y / 60), y]); const poly = k ? [[b, 600], ...pts, [b, H + 40]] : [[a, 600], ...pts, [a, H + 40]]; part(G, poly, fl(K.teal, 5000 + k, 0.85, { cross: true, crossP: 0.4 }), null); line(G.l, pts, ol(5010 + k));
      fish(TOP, { x: k ? 1000 : 230, y: 900 + k * 220, s: 1.0, col: k ? K.orange : K.pink, seed: 5020 + k, flip: !!k }); });
    fill(BG.f, [[420, 1100], [820, 1100], [820, H], [420, H]], { col: K.brown, p: 0.35, gap: 14, w: 14, seed: 5030, boil: 0 });
    person(TOP, { x: 620, y: 1500, s: 1.35, kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.red, seed: 2500, expr: 'wow', armR: [[34, -196], [70, -250], [96, -300]] });
    staff(TOP, 620 + 96 * 1.35, 1500 - 520, 620 + 96 * 1.35, 1500 - 200, 5040);
  },
  h09() { // As muralhas de Jericó
    skyFill(1000); ground(1250);
    for (let r = 0; r < 6; r++) for (let c = 0; c < 9; c++) { const x = 100 + c * 120 + (r % 2) * 60, y = 640 + r * 100; const tilt = r < 2 ? (hash(c + r * 9) - 0.5) * 0.3 : 0; if (x > 1100) continue; const pts = [[x, y], [x + 116, y], [x + 116, y + 96], [x, y + 96], [x, y]].map(([px, py]) => [px + (py - y) * tilt, py - (r < 2 ? hash(c) * 40 : 0)]); O(G, pts, K.orange, 5100 + r * 20 + c, 5); }
    person(TOP, { x: 360, y: 1600, s: 1.25, kind: 'man', cloth: K.white, seed: 2500, expr: 'sing', armR: [[34, -196], [60, -230], [90, -250]] });
    O(TOP, [[360 + 40 * 1.25, 1600 - 260 * 1.25], [360 + 260, 1600 - 420], [360 + 290, 1600 - 330], [360 + 60 * 1.25, 1600 - 240 * 1.25]], K.yellow, 5300);
    person(TOP, { x: 860, y: 1600, s: 1.25, kind: 'man', beard: true, cloth: K.sky, seed: 2550, expr: 'wow', armL: [[-34, -196], [-80, -250], [-100, -300]] });
    Tt('7x', 1080, 450, 120, { col: K.red });
  },
  h10() { // Sansão
    O(G, [[160, 1500], [160, 500], [300, 500], [300, 1500], [160, 1500]], K.peach, 5400); O(G, [[940, 1500], [940, 500], [1080, 500], [1080, 1500], [940, 1500]], K.peach, 5410);
    O(G, [[100, 500], [1140, 500], [1140, 380], [100, 380], [100, 500]], K.orange, 5420);
    ground(1500);
    person(TOP, { x: 620, y: 1560, s: 1.6, kind: 'woman', hair: K.brown, cloth: K.green, seed: 2500, expr: 'happy', armL: [[-34, -196], [-140, -230], [-200, -300]], armR: [[34, -196], [140, -230], [200, -300]] });
    lion(TOP, { x: 1000, y: 1650, s: 0.8, seed: 700, expr: 'sleep' });
  },
  h11() { // Davi e Golias
    skyFill(1100); ground(1100);
    person(TOP, { x: 820, y: 1620, s: 2.6, kind: 'man', beard: true, helmet: true, cloth: K.grey, seed: 2560, expr: 'wow', armR: [[34, -196], [80, -200], [100, -230]] });
    staff(TOP, 820 + 260, 1620 - 1050, 820 + 260, 1620, 5500); O(TOP, [[820 + 240, 1620 - 1050], [820 + 260, 1620 - 1130], [820 + 280, 1620 - 1050], [820 + 240, 1620 - 1050]], K.grey, 5510, 5);
    person(TOP, { x: 260, y: 1620, s: 1.0, kind: 'child', cloth: K.orange, seed: 2400, expr: 'happy', armR: [[34, -196], [70, -250], [60, -310]] });
    line(TOP.l, [[260 + 60, 1620 - 310], [230, 1620 - 380], [300, 1620 - 420], [340, 1620 - 360]], ol(5520, 5, K.brown));
    [[180, 1660], [330, 1680], [400, 1650]].forEach(([x, y], i) => part(TOP, circ(x, y, 22, 5530 + i), fl(K.grey, 5540 + i, 0.9, { gap: 5, w: 7 }), ol(5550 + i, 5)));
  },
  h12() { // Daniel na cova dos leões
    fill(BG.f, [[-40, -40], [W + 40, -40], [W + 40, H + 40], [-40, H + 40]], { col: K.brown, p: 0.25, gap: 16, w: 14, seed: 5600, boil: 0 });
    line(G.l, smooth([[0, 460], [300, 360], [620, 330], [940, 360], [1240, 460]], 6, false), ol(5610, 8));
    person(TOP, { x: 620, y: 1450, s: 1.4, kind: 'man', beard: true, cloth: K.sky, seed: 2500, expr: 'happy', armL: [[-34, -196], [-30, -260], [-6, -300]], armR: [[34, -196], [30, -260], [6, -300]] });
    person(TOP, { x: 620, y: 700, s: 0.9, kind: 'man', wings: true, halo: true, cloth: K.white, seed: 2580, expr: 'happy' });
    lion(TOP, { x: 260, y: 1650, s: 1.25, seed: 700, expr: 'sleep' }); lion(TOP, { x: 980, y: 1650, s: 1.25, seed: 710, flip: true, expr: 'sleep' });
    Tt('Zzz', 330, 1330, 70); Tt('Zzz', 920, 1330, 70);
  },
  h13() { // Os três amigos na fornalha
    O(G, smooth([[180, 1500], [180, 700], [400, 480], [840, 480], [1060, 700], [1060, 1500]], 4, false).concat([[180, 1500]]), K.grey, 5700, 9);
    for (let i = 0; i < 9; i++) { const x = 260 + i * 90; part(G, smooth([[x - 40, 1500], [x - 20, 1300 - hash(i) * 200], [x, 1200 - hash(i + 3) * 250], [x + 20, 1300 - hash(i) * 150], [x + 40, 1500]], 4, false), fl(i % 2 ? K.orange : K.yellow, 5710 + i, 0.9), ol(5730 + i, 5)); }
    [[380, K.red], [560, K.sky], [740, K.green]].forEach(([x, c], i) => person(TOP, { x, y: 1480, s: 0.95, kind: 'man', cloth: c, seed: 2500 + i * 30, expr: 'happy' }));
    person(TOP, { x: 900, y: 1480, s: 0.95, kind: 'man', wings: true, halo: true, cloth: K.white, seed: 2600, expr: 'happy' });
  },
  h14() { // Jonas e o grande peixe
    skyFill(700); waves(700, H + 40);
    const body = smooth([[160, 1150], [400, 850], [800, 820], [1080, 1000], [1180, 920], [1200, 1200], [1080, 1150], [820, 1380], [400, 1400], [160, 1250]], 6); body.push(body[0]);
    O(G, body, K.sky, 5800, 8);
    O(G, smooth([[160, 1150], [420, 1080], [420, 1300], [160, 1250]], 4).concat([[160, 1150]]), K.red, 5810, 6);
    part(G, circ(520, 950, 40, 5820), fl(K.white, 5821, 1, { gap: 5, w: 7 }), ol(5822, 6)); part(G, circ(530, 955, 16, 5823), fl(INK, 5824, 1, { gap: 3, w: 5 }), null);
    person(TOP, { x: 300, y: 1270, s: 0.9, kind: 'man', beard: true, cloth: K.yellow, seed: 2500, expr: 'wow', armR: [[34, -196], [70, -240], [96, -290]] });
    [[700, 650], [760, 560], [820, 480]].forEach(([x, y], i) => part(TOP, circ(x, y, 20 + i * 6, 5830 + i), null, ol(5840 + i, 5)));
  },
  h15() { // A rainha Ester
    fill(BG.f, [[-40, -40], [W + 40, -40], [W + 40, H + 40], [-40, H + 40]], { col: K.pink, p: 0.25, gap: 16, w: 14, seed: 5900, boil: 0 });
    O(G, [[780, 1550], [780, 700], [880, 620], [1080, 620], [1180, 700], [1180, 1550], [780, 1550]], K.orange, 5910);
    person(TOP, { x: 980, y: 1500, s: 1.15, kind: 'man', crown: true, beard: true, cloth: K.red, seed: 2560, expr: 'happy', armL: [[-34, -196], [-80, -230], [-120, -260]] });
    staff(TOP, 980 - 140, 1500 - 300, 980 - 330, 1500 - 520, 5920); part(TOP, circ(980 - 340, 1500 - 530, 26, 5925), fl(K.yellow, 5926, 1, { gap: 5, w: 7 }), ol(5927, 5));
    person(TOP, { x: 400, y: 1600, s: 1.45, kind: 'woman', crown: true, cloth: K.sky, seed: 2700, expr: 'smile', armR: [[34, -196], [90, -240], [120, -290]] });
  },
  h16() { // O nascimento de Jesus
    fill(BG.f, [[-40, -40], [W + 40, -40], [W + 40, 1000], [-40, 1000]], { col: K.sky, p: 0.7, gap: 12, w: 13, seed: 61, boil: 0 });
    star(TOP, 620, 380, 100, 6000); for (let i = 0; i < 6; i++) line(TOP.l, [[620, 490], [620 + (i - 2.5) * 70, 640]], ol(6010 + i, 4, K.yellow));
    ground(1000); [[220, 1040], [1020, 1040]].forEach(([x, y], i) => O(G, [[x - 22, y + 300], [x - 22, y - 60], [x + 22, y - 60], [x + 22, y + 300], [x - 22, y + 300]], K.brown, 6024 + i * 3)); O(G, [[140, 1000], [620, 700], [1100, 1000], [140, 1000]], K.brown, 6020);
    O(G, [[440, 1400], [500, 1250], [740, 1250], [800, 1400], [440, 1400]], K.orange, 6030);
    for (let i = 0; i < 5; i++) line(G.l, [[520 + i * 40, 1255], [510 + i * 45, 1220]], ol(6040 + i, 5, K.yellow));
    baby(TOP, { x: 680, y: 1250, s: 1.6, seed: 2600 });
    person(TOP, { x: 270, y: 1500, s: 1.1, kind: 'woman', scarf: K.sky, cloth: K.white, seed: 2700, expr: 'happy' });
    person(TOP, { x: 990, y: 1500, s: 1.1, kind: 'man', beard: true, cloth: K.orange, seed: 2560, expr: 'happy' });
    sheep(TOP, { x: 620, y: 1640, s: 1.5, seed: 500 });
  },
  h17() { // Jesus acalma a tempestade
    fill(BG.f, [[-40, -40], [W + 40, -40], [W + 40, 900], [-40, 900]], { col: K.grey, p: 0.5, gap: 14, w: 14, seed: 6100, boil: 0 });
    cloud(TOP, { x: 260, y: 300, s: 1.1, seed: 1400 }); cloud(TOP, { x: 960, y: 260, s: 1.0, seed: 1410 });
    O(TOP, [[620, 330], [560, 460], [620, 460], [560, 600], [700, 420], [640, 420], [700, 330], [620, 330]], K.yellow, 6110);
    waves(1250, H + 40, 5);
    const hull = [[200, 1150], [1040, 1150], [960, 1350], [280, 1350], [200, 1150]]; O(G, hull, K.brown, 6120, 8);
    line(G.l, [[620, 1150], [620, 650]], { w: 12, col: K.brown, seed: 6130 }); O(G, [[630, 680], [900, 1080], [630, 1080], [630, 680]], K.white, 6140);
    person(TOP, { x: 420, y: 1160, s: 1.0, kind: 'man', beard: true, cloth: K.white, belt: K.red, seed: 2500, expr: 'smile', armR: [[34, -196], [90, -240], [130, -300]] });
    person(TOP, { x: 820, y: 1160, s: 0.85, kind: 'man', cloth: K.orange, seed: 2560, expr: 'wow' });
  },
  h18() { // A multiplicação dos pães e peixes
    skyFill(900); ground(900);
    person(TOP, { x: 400, y: 1620, s: 1.2, kind: 'child', cloth: K.yellow, seed: 2400, expr: 'happy', armR: [[34, -196], [90, -180], [140, -160]] });
    const bx = 700, by = 1450; O(TOP, smooth([[bx - 200, by - 120], [bx + 200, by - 120], [bx + 160, by + 80], [bx - 160, by + 80]], 3).concat([[bx - 200, by - 120]]), K.orange, 6200, 8);
    for (let i = 0; i < 5; i++) part(TOP, ellipse(bx - 150 + i * 75, by - 150, 44, 30, 20), fl(K.peach, 6210 + i, 0.9, { gap: 6, w: 8 }), ol(6220 + i, 5));
    fish(TOP, { x: bx - 60, y: by - 230, s: 0.8, col: K.sky, seed: 6230 }); fish(TOP, { x: bx + 90, y: by - 240, s: 0.8, col: K.sky, seed: 6240, flip: true });
    person(TOP, { x: 960, y: 1550, s: 1.3, kind: 'man', beard: true, cloth: K.white, belt: K.red, seed: 2500, expr: 'happy', armL: [[-34, -196], [-70, -240], [-100, -290]] });
  },
  h19() { // O filho pródigo
    skyFill(1000); ground(1000); house(G, { x: 980, y: 1060, s: 1.2, seed: 1960 });
    line(G.l, [[520, 1754], [700, 1060]], ol(6300, 6)); line(G.l, [[820, 1754], [780, 1060]], ol(6301, 6));
    person(TOP, { x: 470, y: 1580, s: 1.4, kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.red, seed: 2560, expr: 'happy', armR: [[34, -196], [90, -210], [140, -200]] });
    person(TOP, { x: 680, y: 1580, s: 1.3, kind: 'man', cloth: K.brown, seed: 2500, expr: 'happy', armL: [[-34, -196], [-90, -210], [-120, -200]] });
    heart(TOP, { x: 580, y: 850, s: 1.6, seed: 1300 }); sun(TOP, { x: 180, y: 500, R: 70, face: 1, seed: 1100 });
  },
  h20() { // Jesus ressuscitou
    skyFill(1000);
    for (let i = 0; i < 9; i++) { const a = Math.PI + (i + 0.5) / 9 * Math.PI; line(BG.l, [[620 + Math.cos(a) * 300, 1000 + Math.sin(a) * 300], [620 + Math.cos(a) * 560, 1000 + Math.sin(a) * 560]], { w: 12, col: K.yellow, seed: 6400 + i }); }
    ground(1000);
    O(G, smooth([[260, 1450], [260, 1000], [420, 780], [820, 780], [980, 1000], [980, 1450]], 4, false).concat([[260, 1450]]), K.grey, 6420, 9);
    O(G, smooth([[470, 1450], [470, 1150], [620, 1060], [770, 1150], [770, 1450]], 4, false).concat([[470, 1450]]), INK, 6430, 6);
    part(G, circ(1100, 1380, 150, 6440), fl(K.grey, 6441, 0.8), ol(6442, 8));
    person(TOP, { x: 620, y: 1420, s: 1.0, kind: 'man', wings: true, halo: true, cloth: K.white, seed: 2580, expr: 'happy' });
    [[180, 1650, K.pink], [360, 1700, K.yellow], [880, 1690, K.sky], [1060, 1650, K.red]].forEach(([x, y, c], i) => flowerO(TOP, x, y, 1.5, c));
  },
  livre() {
    Tt('Desenhe aqui a sua', 620, 200, 100); Tt('história favorita!', 620, 320, 100, { col: K.red });
    line(TOP.l, [[100, 420], [1140, 420], [1140, 1600], [100, 1600], [100, 420]], ol(30, 7));
    sun(TOP, { x: 1100, y: 1640, R: 50, face: 1, seed: 1100 }); star(TOP, 140, 1640, 40, 40);
  },
};
export const ORDER = ['capa', 'dono', 'h01', 'h02', 'h03', 'h04', 'h05', 'h06', 'h07', 'h08', 'h09', 'h10', 'h11', 'h12', 'h13', 'h14', 'h15', 'h16', 'h17', 'h18', 'h19', 'h20', 'livre'];
const INFO = {
  h01: ['A Criação', 'Gênesis 1 e 2'], h02: ['Adão e Eva', 'Gênesis 2 e 3'], h03: ['Noé e a Grande Arca', 'Gênesis 6 a 9'], h04: ['A Torre de Babel', 'Gênesis 11'],
  h05: ['Abraão e as Estrelas', 'Gênesis 15'], h06: ['José e a Túnica Colorida', 'Gênesis 37'], h07: ['O Bebê Moisés', 'Êxodo 2'], h08: ['O Mar Vermelho', 'Êxodo 14'],
  h09: ['As Muralhas de Jericó', 'Josué 6'], h10: ['Sansão', 'Juízes 16'], h11: ['Davi e Golias', '1 Samuel 17'], h12: ['Daniel e os Leões', 'Daniel 6'],
  h13: ['Os Três Amigos na Fornalha', 'Daniel 3'], h14: ['Jonas e o Grande Peixe', 'Jonas 1 e 2'], h15: ['A Rainha Ester', 'Ester 5'], h16: ['O Nascimento de Jesus', 'Lucas 2'],
  h17: ['Jesus Acalma a Tempestade', 'Marcos 4'], h18: ['Os Pães e os Peixes', 'João 6'], h19: ['O Filho Pródigo', 'Lucas 15'], h20: ['Jesus Ressuscitou!', 'Mateus 28'],
};
export function draw(comp, page) {
  CAM.x = W / 2; CAM.y = H / 2; CAM.s = 1; BOIL.amp = 1;
  [BG.f, BG.l, TX].forEach(clear); clearGroup(G); clearGroup(TOP);
  (PAGES[page] || PAGES.capa)();
  if (INFO[page]) {
    const n = +page.slice(1);
    const g = TX.g; g.save(); g.fillStyle = '#000'; g.restore();
    Tt(INFO[page][0], 620, 120, INFO[page][0].length > 20 ? 84 : 104);
    Tt(INFO[page][1] + '  ·  ' + n + '/20', 620, 200, 46, { font: 'Patrick Hand' });
    Tt('Bíblia em Traços', 620, 1710, 40, { font: 'Patrick Hand' });
  }
  comp.paperCam(W / 2, H / 2, 1); comp.begin([0.99, 0.985, 0.97]);
  comp.crayon(BG.f.c); comp.crayon(BG.l.c); comp.group(G); comp.group(TOP); comp.crayon(TX.c);
  comp.finish({ vig: 0, emb: 0.25 });
}
