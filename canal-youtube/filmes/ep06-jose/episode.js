// Ep. 06 · José e a Túnica Colorida — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, sheep, sun, moon, cloud, heart } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const SAND = '#e9c58a';
const COAT = [K.red, K.orange, K.yellow, K.green, K.sky, K.pink, K.red];
const JOSE = { kind: 'man', cloth: K.white, stripes: COAT, seed: 2500 };
const JOSE_PLAIN = { kind: 'man', cloth: K.sky, seed: 2500 };
const JOSE_GOV = { kind: 'man', cloth: K.white, belt: K.yellow, crown: true, seed: 2500 };
const JACO = { kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.brown, seed: 2560 };
const BRO = [K.green, K.brown, K.sky, K.orange, K.grey];
const bro = (i, o = {}) => ({ kind: 'man', beard: i % 2 === 0, cloth: BRO[i % 5], seed: 2600 + i * 23, ...o });

function pyramids(api) { [[350, 760, 300], [760, 760, 210], [1500, 760, 260]].forEach(([x, y, r], i) => api.O(api.G, [[x - r, y], [x, y - r * 1.1], [x + r, y], [x - r, y]], K.yellow, 6400 + i * 3)); }
function sheaf(api, C, x, y, s, bow, seed) { const r = bow; api.O(C, [[x - 30 * s, y], [x - 10 * s + r * 40, y - 150 * s], [x + 10 * s + r * 40, y - 150 * s], [x + 30 * s, y], [x - 30 * s, y]], K.yellow, seed, { lw: 5 }); line(C.l, [[x - 32 * s, y - 50 * s], [x + 32 * s, y - 50 * s]], { w: 6, col: K.brown, seed: seed + 3 }); }
function dreamCloud(api, x, y, w, h, g, seed) { if (g <= 0) return; const pts = []; for (let i = 0; i <= 80; i++) { const a = i / 80 * 6.283; const b = 1 + 0.08 * Math.abs(Math.sin(a * 6)); pts.push([x + Math.cos(a) * w * b, y + Math.sin(a) * h * b]); } part(api.TOP, pts, { col: K.white, p: 1, gap: 8, w: 10, seed, draw: g }, { w: 6, col: K.ink, seed: seed + 1, draw: g }); [[x - w * 0.6, y + h + 30, 26], [x - w * 0.75, y + h + 80, 16]].forEach(([cx, cy, r], i) => part(api.TOP, handCircle(cx, cy, r, seed + 5 + i, 0, 20), { col: K.white, p: 1, gap: 5, w: 7, seed: seed + 7 + i, draw: g }, { w: 5, col: K.ink, seed: seed + 9 + i, draw: g })); }
function cow(api, C, x, y, fat, seed) { const w = fat ? 80 : 46; api.O(C, ellipse(x, y, w, fat ? 46 : 30, 24), fat ? K.white : K.grey, seed, { lw: 5 }); [-w * 0.6, w * 0.6].forEach((dx, i) => line(C.l, [[x + dx, y + 20], [x + dx, y + 70]], { w: 6, col: K.ink, seed: seed + 3 + i })); api.O(C, handCircle(x + w + 20, y - 20, 24, seed + 6, 0, 18), fat ? K.white : K.grey, seed + 7, { lw: 5 }); if (fat) [[-20, -10], [25, 10]].forEach(([dx, dy], i) => dab(C.f, x + dx, y + dy, 12, { col: K.brown, p: 1, seed: seed + 9 + i })); }
function bars(api, x0, x1, y0, y1) { for (let x = x0; x <= x1; x += 90) line(api.TOP.l, [[x, y0], [x, y1]], { w: 14, col: K.grey, seed: 6500 + x }); line(api.TOP.l, [[x0 - 20, y0], [x1 + 20, y0]], { w: 14, col: K.grey, seed: 6600 }); }
function granary(api, C, x, y, s, g, seed) { api.O(C, smooth([[x - 90 * s, y], [x - 90 * s, y - 220 * s], [x, y - 300 * s], [x + 90 * s, y - 220 * s], [x + 90 * s, y]], 4, false).concat([[x - 90 * s, y]]), K.peach, seed, { draw: g, fill: g }); if (g >= 1) sheaf(api, C, x, y - 20 * s, 0.7 * s, 0, seed + 5); }

export const SCENES = {
  gancho: {
    cam: (lt, L, d) => [960, 480, lerp(1.3, 1.1, ss(lt / d))],
    draw(api, lt, L, d) {
      api.sky(1080, 0.35);
      person(api.F, { ...JOSE, x: 960, y: 960, s: 1.6, expr: 'happy', armL: [[-34, -196], [-90, -230], [-120, -280]], armR: [[34, -196], [90, -230], [120, -280]], draw: api.pr(lt, 0.2, 1.2), fill: api.pr(lt, 0.8, 2.6) });
    },
    fx: [[0.8, 'scribble', { dur: 2.0 }], [2.6, 'shimmer']],
  },
  s1: {
    draw(api, lt, L) {
      api.sky(720, 0.4); api.ground(720);
      person(api.F, { ...JACO, x: 560, y: 1060, s: 1.3, expr: 'happy', armR: [[34, -196], [80, -200], [120, -190]] });
      const coat = api.pr(lt, L[1], L[1] + 1.5);
      person(api.F, { ...(coat > 0 ? { ...JOSE, fill: 1 } : JOSE_PLAIN), x: 820, y: 1060, s: 1.1, expr: coat > 0 ? 'happy' : 'smile', seed: 2500 });
      for (let i = 0; i < 4; i++) person(api.F, bro(i, { x: 1180 + i * 170, y: 1060, s: 0.95, expr: lt > L[2] ? 'sad' : 'smile' }));
    },
    fx: [[(L) => L[1], 'scribble', { dur: 1.5 }], [(L) => L[1] + 1.5, 'shimmer']],
  },
  s2: {
    draw(api, lt, L, d) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: '#2f3a78', p: 0.9, gap: 10, w: 13, seed: 5500, boil: 0 });
      api.ground(900, 1, '#4f7a3f');
      person(api.F, { ...JOSE, x: 300, y: 1110, s: 1.0, expr: 'sleep' });
      dreamCloud(api, 1050, 420, 720, 300, api.pr(lt, 0.3, 1.2), 6700);
      const bow = ss(api.pr(lt, 1.5, 3.0));
      if (lt > 1.2) { sheaf(api, api.TOP, 1050, 560, 1.2, 0, 6720); for (let i = 0; i < 4; i++) sheaf(api, api.TOP, 700 + i * 120 + (i > 1 ? 400 : 0), 600, 0.9, (i < 2 ? 1 : -1) * bow * 0.9, 6730 + i * 9); }
      if (lt > 3.5) { sun(api.TOP, { x: 620, y: 250, R: 50, face: 1, seed: 1100 }); moon(api.TOP, { x: 1480, y: 250, R: 60, seed: 1200 }); for (let i = 0; i < 6; i++) api.star(api.TOP, 820 + i * 90, 220 + (i % 2) * 40, 20, 6760 + i * 2); }
      if (lt > L[1]) for (let i = 0; i < 3; i++) person(api.F, bro(i, { x: 1250 + i * 200, y: 1110, s: 0.95, expr: 'sad' }));
    },
    fx: [[1.5, 'whoosh'], [3.5, 'shimmer']],
  },
  s3: {
    draw(api, lt, L, d) {
      const { pr } = api;
      api.sky(700, 0.4); api.ground(700, 1, SAND, 83);
      api.O(api.G, ellipse(960, 880, 220, 70, 40), K.grey, 6800); api.O(api.G, ellipse(960, 870, 150, 40, 30), K.ink, 6810, { lw: 4 });
      const inWell = lt > 2.5;
      if (!inWell) person(api.F, { ...JOSE, x: 960, y: 1000, s: 1.1, expr: 'wow' });
      else person(api.F, { ...JOSE_PLAIN, x: 960, y: 1080, s: 0.7, expr: 'sad', armL: [[-34, -196], [-60, -250], [-70, -300]], armR: [[34, -196], [60, -250], [70, -300]] });
      if (inWell) api.O(api.TOP, ellipse(960, 900, 220, 70, 40, 0, Math.PI), K.grey, 6820);
      for (let i = 0; i < 3; i++) person(api.F, bro(i, { x: 400 + i * 160, y: 1060, s: 1.0, expr: 'smile' }));
      if (lt > L[1]) { const u = pr(lt, L[1], L[1] + 4); api.O(api.G, [[1300 + u * 300, 900], [1500 + u * 300, 900], [1470 + u * 300, 980], [1330 + u * 300, 980], [1300 + u * 300, 900]], K.brown, 6830); person(api.F, { kind: 'man', cloth: K.orange, scarf: K.red, x: 1450 + u * 300, y: 1060, s: 1.0, seed: 2700, walk: lt * 6 }); }
    },
    fx: [[2.5, 'thud'], [(L) => L[1], 'whoosh']],
  },
  s4: {
    draw(api, lt, L) {
      api.sky(760, 0.4); api.ground(760, 1, SAND, 84); sun(api.TOP, { x: 1700, y: 200, R: 80, face: 1, seed: 1100 }); pyramids(api);
      const work = Math.floor(lt * 2) % 2;
      person(api.F, { ...JOSE_PLAIN, x: 900, y: 1060, s: 1.25, expr: lt > L[1] ? 'happy' : 'smile', armR: work ? [[34, -196], [80, -220], [110, -250]] : [[34, -196], [80, -170], [110, -150]] });
      if (lt > L[1]) { for (let i = 0; i < 5; i++) api.star(api.TOP, 600 + i * 150, 560 - Math.abs(i - 2) * 30, 24, 6900 + i * 2); heart(api.TOP, { x: 900, y: 420, s: 1.0 * eo(api.pr(lt, L[1] + 0.5, L[1] + 1.1)), seed: 1300 }); }
    },
    fx: [[(L) => L[1] + 0.5, 'shimmer']],
  },
  s5: {
    draw(api, lt, L) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.grey, p: 0.4, gap: 14, w: 14, seed: 7000, boil: 0 });
      api.O(api.G, [[820, 200], [1100, 200], [1100, 360], [820, 360], [820, 200]], K.sky, 7010, { lw: 6 });
      person(api.F, { ...JOSE_PLAIN, x: 960, y: 1060, s: 1.2, expr: lt > L[1] ? 'smile' : 'sad', armR: lt > L[1] ? [[34, -196], [70, -250], [96, -300]] : undefined });
      if (lt > L[1]) [[520, K.white], [1400, K.red]].forEach(([x, c], i) => person(api.F, { kind: 'man', cloth: c, x, y: 1060, s: 1.0, seed: 2780 + i * 30, expr: lt > L[2] ? 'happy' : 'wow' }));
      bars(api, 120, 1800, 120, 1080);
    },
    fx: [[0.4, 'thud'], [(L) => L[2], 'shimmer']],
  },
  s6: {
    draw(api, lt, L) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.yellow, p: 0.25, gap: 14, w: 14, seed: 7100, boil: 0 });
      [[200, 1080], [1720, 1080]].forEach(([x], i) => api.O(api.G, [[x - 50, 1080], [x - 50, 180], [x + 50, 180], [x + 50, 1080], [x - 50, 1080]], K.orange, 7110 + i * 3));
      person(api.F, { kind: 'man', crown: true, cloth: K.white, belt: K.sky, x: 520, y: 1060, s: 1.3, seed: 2560, expr: 'wow' });
      dreamCloud(api, 1250, 360, 520, 220, api.pr(lt, 0.3, 1.0), 7120);
      if (lt > 1.0) { for (let i = 0; i < 3; i++) cow(api, api.TOP, 1000 + i * 180, 300, true, 7130 + i * 11); for (let i = 0; i < 3; i++) cow(api, api.TOP, 1000 + i * 180, 450, false, 7170 + i * 11); }
      if (lt > L[1]) person(api.F, { ...JOSE_PLAIN, x: 1250, y: 1060, s: 1.2, expr: 'smile', armR: [[34, -196], [70, -250], [96, -300]] });
      if (lt > L[1] + 3.5) api.text('7 + 7', 1250, 650, 100, { col: K.red, reveal: api.pr(lt, L[1] + 3.5, L[1] + 4.0) });
    },
    fx: [[1.0, 'toot'], [(L) => L[1] + 3.5, 'write', { dur: 0.5 }]],
  },
  s7: {
    draw(api, lt, L, d) {
      api.sky(760, 0.4); api.ground(760, 1, SAND, 85); pyramids(api);
      person(api.F, { ...JOSE_GOV, x: 560, y: 1060, s: 1.3, expr: 'happy' });
      person(api.F, { kind: 'man', crown: true, cloth: K.white, belt: K.sky, x: 300, y: 1060, s: 1.1, seed: 2560, expr: 'happy' });
      for (let i = 0; i < 4; i++) granary(api, api.G, 1000 + i * 230, 1000, 1.0, api.pr(lt, L[1] + i * 0.5, L[1] + 0.8 + i * 0.5), 7200 + i * 13);
    },
    fx: [[0.3, 'shimmer'], [(L) => L[1], 'scratch', { dur: 2.5 }]],
  },
  s8: {
    draw(api, lt, L) {
      api.sky(760, 0.4); api.ground(760, 1, SAND, 86);
      person(api.F, { ...JOSE_GOV, x: 420, y: 1060, s: 1.35, expr: 'wow' });
      const bow = ss(api.pr(lt, L[1], L[1] + 1.2));
      for (let i = 0; i < 5; i++) person(api.F, bro(i, { x: 860 + i * 220, y: 1060 + bow * 20, s: 1.0, r: -0.5 * bow, expr: 'smile' }));
    },
    fx: [[(L) => L[1], 'whoosh']],
  },
  s9: {
    draw(api, lt, L) {
      api.sky(760, 0.4); api.ground(760, 1, SAND, 87);
      const hug = lt > L[1];
      person(api.F, { ...JOSE_GOV, x: 860, y: 1060, s: 1.3, expr: hug ? 'happy' : 'smile', armR: hug ? [[34, -196], [90, -200], [140, -190]] : undefined });
      for (let i = 0; i < 3; i++) person(api.F, bro(i, { x: 1080 + i * 200, y: 1060, s: 1.1, expr: lt > L[2] ? 'happy' : 'wow', armL: hug && i === 0 ? [[-34, -196], [-90, -200], [-140, -190]] : undefined }));
      if (lt > L[3]) person(api.F, { ...JACO, x: 520, y: 1060, s: 1.2, expr: 'happy', draw: api.pr(lt, L[3], L[3] + 0.8), fill: api.pr(lt, L[3] + 0.4, L[3] + 1.2) });
      if (lt > L[2]) heart(api.TOP, { x: 1060, y: 450, s: 1.5 * eo(api.pr(lt, L[2], L[2] + 0.7)), seed: 1300 });
    },
    fx: [[(L) => L[1], 'heart'], [(L) => L[3], 'scratch', { dur: 1 }]],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      api.sky(1080, 0.35); api.ground(860);
      person(api.F, { kind: 'child', cloth: K.yellow, x: 820, y: 1060, s: 1.3, seed: 2400, expr: 'happy', armR: [[34, -196], [80, -200], [120, -190]] });
      person(api.F, { kind: 'child', cloth: K.sky, x: 1100, y: 1060, s: 1.25, seed: 2450, expr: 'happy', armL: [[-34, -196], [-80, -200], [-120, -190]] });
      heart(api.TOP, { x: 960, y: 420, s: 1.5 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
    },
  },
};
export function titleArt(api, t) { COAT.forEach((c, i) => { const g = api.pr(t, 4.5 + i * 0.15, 4.8 + i * 0.15); if (g > 0) line(api.TOP.l, [[600, 820 + i * 26], [1320, 820 + i * 26]], { w: 22, col: c, p: 1, seed: 7300 + i, draw: g }); }); }
