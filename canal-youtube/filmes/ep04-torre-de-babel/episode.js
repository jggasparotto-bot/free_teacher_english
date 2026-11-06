// Ep. 04 · A Torre de Babel — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, sun, cloud, heart, house } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const PEOPLE = [['man', K.red], ['woman', K.sky, K.pink], ['man', K.green], ['woman', K.orange, K.yellow], ['man', K.yellow], ['woman', K.green, K.sky]];

function tower(api, C, cx, base, s, tiers, g = 1) {   // torre em andares (g = progresso: andares desenhados de baixo para cima)
  for (let i = 0; i < tiers; i++) {
    const gi = clamp(g * tiers - i); if (gi <= 0) break;
    const w = (560 - i * 62) * s, y = base - i * 130 * s, h = 130 * s;
    api.O(C, [[cx - w / 2, y], [cx + w / 2, y], [cx + w / 2 - 20 * s, y - h], [cx - w / 2 + 20 * s, y - h], [cx - w / 2, y]], i % 2 ? K.orange : K.peach, 4500 + i * 5, { draw: gi, fill: gi, lw: 6 });
    if (gi >= 1) for (let j = 0; j < 3; j++) { const x = cx - w / 2 + 50 * s + j * (w - 100 * s) / 2; api.O(C, [[x - 13 * s, y - 95 * s], [x + 13 * s, y - 95 * s], [x + 13 * s, y - 45 * s], [x - 13 * s, y - 45 * s], [x - 13 * s, y - 95 * s]], K.brown, 4600 + i * 9 + j, { lw: 4 }); }
  }
}
function balloon(api, x, y, txt, g, seed, w = 190) {
  if (g <= 0) return;
  const pts = smooth([[x - w / 2, y - 60], [x + w / 2, y - 60], [x + w / 2, y + 40], [x + 20, y + 40], [x - 10, y + 90], [x - 10, y + 40], [x - w / 2, y + 40]], 4);
  part(api.TOP, pts, { col: K.white, p: 1, gap: 7, w: 9, seed, draw: g }, { w: 6, col: K.ink, seed: seed + 1, draw: g });
  if (g >= 1) api.text(txt, x, y + 8, 56, { col: K.ink, seed });
}
function crowd(api, lt, y = 1000, expr = 'smile', start = 0.3) {
  PEOPLE.forEach(([k, c, sc], i) => { const g = api.pr(lt, start + i * 0.18, start + 0.8 + i * 0.18); if (g > 0) person(api.F, { kind: k, cloth: c, scarf: sc, x: 200 + i * 300, y, s: 1.0, seed: 2800 + i * 37, expr, draw: g, fill: g }); });
}
function banana(api, x, y, s, seed) { part(api.TOP, smooth([[x - 60 * s, y - 20 * s], [x, y + 30 * s], [x + 60 * s, y - 20 * s], [x + 40 * s, y], [x, y + 10 * s], [x - 40 * s, y]], 4), { col: K.yellow, p: 1, gap: 5, w: 7, seed }, { w: 5, col: K.ink, seed: seed + 1 }); }
function brick(api, x, y, seed) { api.O(api.TOP, [[x - 40, y - 22], [x + 40, y - 22], [x + 40, y + 22], [x - 40, y + 22], [x - 40, y - 22]], K.red, seed, { lw: 5 }); }

export const SCENES = {
  gancho: {
    cam: (lt, L, d) => [960, lerp(760, 380, ss(lt / d)), 1.25],
    draw(api, lt, L, d) {
      api.sky(1080, 0.55); api.ground(950);
      tower(api, api.G, 960, 950, 1.0, 7, api.pr(lt, 0.2, d * 0.7));
      [[420, 260, 1.2], [1500, 200, 1.0], [960, 120, 1.4]].forEach(([x, y, s], i) => cloud(api.TOP, { x, y, s, seed: 1400 + i * 10 }));
    },
    fx: [[0.4, 'scribble', { dur: 3 }]],
  },
  s1: {
    draw(api, lt, L) {
      api.sky(700, 0.4); api.ground(700); sun(api.TOP, { x: 1700, y: 200, R: 80, face: 1, seed: 1100 });
      crowd(api, lt);
      PEOPLE.forEach((_, i) => balloon(api, 200 + i * 300, 520, 'Oi!', api.pr(lt, L[1] + i * 0.25, L[1] + 0.5 + i * 0.25), 4700 + i * 3, 150));
    },
    fx: [[0.4, 'crowd', { dur: 4 }], [(L) => L[1], 'pop'], [(L) => L[1] + 0.5, 'pop'], [(L) => L[1] + 1.0, 'pop']],
  },
  s2: {
    draw(api, lt, L) {
      api.sky(650, 0.4); api.ground(650, 1, K.peach, 82);
      api.O(api.G, [[560, 820], [1360, 820], [1300, 880], [620, 880], [560, 820]], K.brown, 4800);
      api.O(api.G, [[760, 760], [1160, 760], [1160, 815], [760, 815], [760, 760]], K.white, 4810, { lw: 5 });
      tower(api, api.TOP, 960, 810, 0.09, 6, 1);
      person(api.F, { kind: 'man', cloth: K.red, x: 460, y: 1060, s: 1.2, seed: 2800, expr: 'happy', armR: [[34, -196], [70, -250], [96, -310]] });
      person(api.F, { kind: 'man', cloth: K.green, x: 1460, y: 1060, s: 1.15, seed: 2874, expr: 'happy' });
      if (lt > L[1]) api.text('!!', 560, 300, 140, { col: K.red, reveal: api.pr(lt, L[1], L[1] + 0.4) });
    },
    fx: [[(L) => L[1], 'write', { dur: 0.4 }]],
  },
  s3: {
    draw(api, lt, L, d) {
      api.sky(1080, 0.5); api.ground(940);
      [[300 + lt * 30, 260, 1.0], [1300 + lt * 20, 180, 1.1]].forEach(([x, y, s], i) => cloud(api.TOP, { x: x % 2100 - 100, y, s, seed: 1400 + i * 10 }));
      tower(api, api.G, 960, 940, 0.9, 7, clamp(lt / (d * 0.9)));
      for (let i = 0; i < 6; i++) brick(api, 300 + (i % 3) * 84, 920 - Math.floor(i / 3) * 44, 4900 + i * 3);
      person(api.F, { kind: 'man', cloth: K.yellow, x: 520, y: 1040, s: 1.0, seed: 2950, expr: lt > L[1] ? 'happy' : 'smile', armR: [[34, -196], [70, -230], [90, -270]] });
      person(api.F, { kind: 'man', cloth: K.sky, x: 1460, y: 1040, s: 1.0, seed: 2990, expr: lt > L[1] ? 'happy' : 'smile', armL: [[-34, -196], [-70, -250], [-90, -300]] });
    },
    fx: [[0.5, 'hammer'], [1.2, 'hammer'], [2.0, 'hammer'], [2.8, 'hammer'], [3.6, 'hammer'], [4.4, 'hammer']],
  },
  s4: {
    cam: (lt, L, d) => [960, lerp(540, 600, ss(lt / d)), lerp(1.35, 1.0, ss(lt / (d * 0.7)))],
    glow: (lt) => [0.5, 0.95, 0.35, 0.4 * clamp(lt / 1.5)],
    draw(api, lt, L, d) {
      api.sky(1080, 0.5); api.ground(980);
      tower(api, api.G, 960, 980, 0.35, 7, 1);
      [[300, 900], [1600, 900]].forEach(([x, y], i) => house(api.G, { x, y, s: 0.35, seed: 1960 + i * 10 }));
      for (let i = 0; i < 9; i++) line(api.TOP.l, [[960 + (i - 4) * 120, -40], [960 + (i - 4) * 50, 520]], { w: 6, col: K.yellow, seed: 5000 + i, draw: api.pr(lt, 0.3 + i * 0.1, 1.2 + i * 0.1) });
    },
    fx: [[0.3, 'glow', { dur: 3 }]],
  },
  s5: {
    draw(api, lt, L, d) {
      const { pr } = api;
      api.sky(700, 0.4); api.ground(700);
      tower(api, api.G, 960, 720, 0.6, 7, 1);
      person(api.F, { kind: 'man', cloth: K.red, x: 520, y: 1060, s: 1.3, seed: 2800, expr: lt > L[2] ? 'wow' : 'smile', armR: [[34, -196], [90, -210], [130, -200]] });
      person(api.F, { kind: 'man', cloth: K.green, x: 1400, y: 1060, s: 1.3, seed: 2874, expr: 'happy', armL: [[-34, -196], [-90, -210], [-140, -200]] });
      balloon(api, 520, 380, 'Tijolo?', pr(lt, L[1], L[1] + 0.4), 5100, 240);
      if (lt > L[2]) { balloon(api, 1400, 380, 'Banana!', pr(lt, L[2], L[2] + 0.4), 5110, 260); banana(api, 1400 - 140 * 1.3, 1060 - 200 * 1.3, 1.4, 5120); }
      if (lt > L[3]) ['?!', '%#', '¿', '!!'].forEach((s, i) => balloon(api, 180 + i * 520, 160, s, pr(lt, L[3] + i * 0.2, L[3] + 0.4 + i * 0.2), 5130 + i * 3, 150));
    },
    fx: [[(L) => L[1], 'pop'], [(L) => L[2], 'squeak'], [(L) => L[3], 'crowd', { dur: 3 }]],
  },
  s6: {
    draw(api, lt, L, d) {
      const { pr } = api;
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.peach, p: 0.35, gap: 14, w: 14, seed: 5200, boil: 0 });
      tower(api, api.G, 960, 600, 0.25, 4, 1);
      const ends = [[220, 200], [1700, 180], [260, 900], [1680, 880]];
      ends.forEach(([x, y], i) => {
        const g = pr(lt, 0.4 + i * 0.4, 2.0 + i * 0.4);
        const pts = []; for (let k = 0; k <= 12; k++) { if (k % 2) continue; const u0 = k / 12, u1 = (k + 1) / 12; pts.push([[lerp(960, x, u0), lerp(560, y, u0)], [lerp(960, x, u1), lerp(560, y, u1)]]); }
        pts.forEach((sg, j) => { if (j / pts.length < g) line(api.G.l, sg, { w: 5, col: K.ink, seed: 5300 + i * 20 + j }); });
        if (g >= 1) house(api.TOP, { x, y: y + 110, s: 0.45, seed: 1960 + i * 10 });
        const u = pr(lt, 1.0 + i * 0.4, d - 1); if (u > 0) person(api.F, { kind: i % 2 ? 'woman' : 'man', cloth: PEOPLE[i][1], scarf: PEOPLE[i][2], x: lerp(960, x, u * 0.8), y: lerp(640, y + 200, u * 0.8), s: 0.55, seed: 2800 + i * 37, walk: lt * 7 });
      });
      if (lt > L[1]) api.text('BABEL', 960, 760, 110, { col: K.red, reveal: pr(lt, L[1] + 1.0, L[1] + 1.6) });
    },
    fx: [[0.4, 'scratch', { dur: 2.4 }], [(L) => L[1] + 1.0, 'write', { dur: 0.6 }]],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      const { pr } = api;
      api.sky(1080, 0.35); api.ground(860);
      person(api.F, { kind: 'child', cloth: K.yellow, x: 960, y: 1060, s: 1.4, seed: 2400, expr: 'happy', armR: [[34, -196], [80, -230], [100, -290]] });
      heart(api.TOP, { x: 960, y: 300, s: 1.3 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
      [['Obrigado!', 380, 360], ['Thank you!', 1540, 360], ['¡Gracias!', 380, 680], ['Merci!', 1540, 680]].forEach(([w, x, y], i) => balloon(api, x, y, w, pr(lt, L[2] + 1.0 + i * 0.6, L[2] + 1.4 + i * 0.6), 5400 + i * 3, 330));
    },
    fx: [[(L) => L[2] + 1.0, 'pop'], [(L) => L[2] + 1.6, 'pop'], [(L) => L[2] + 2.2, 'pop'], [(L) => L[2] + 2.8, 'pop']],
  },
};
export function titleArt(api, t) { tower(api, api.G, 960, 1040, 0.28, 6, api.pr(t, 4.5, 6.5)); }
