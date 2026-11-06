// Ep. 03 · Noé e a Grande Arca — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part, tube } from './rig.js';
import { person, sheep, rabbit, lion, elephant, giraffe, turtle, bird, sun, cloud, heart, house, tree } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const NOAH = { kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.sky, seed: 2500 };
const WIFE = { kind: 'woman', scarf: K.pink, cloth: K.orange, seed: 2700 };
const SAND = '#e9c58a';

function ark(api, C, x, y, s, g = 1, o = {}) {   // casco + casa + janelas + porta (g = progresso do desenho)
  const { O } = api;
  const hull = smooth([[x - 520 * s, y - 140 * s], [x + 520 * s, y - 140 * s], [x + 460 * s, y + 110 * s], [x - 460 * s, y + 110 * s]], 3); hull.push(hull[0]);
  O(C, hull, K.brown, 4300, { draw: g, fill: clamp(g * 1.4 - 0.3), lw: 8 });
  if (g > 0.5) for (let i = 0; i < 3; i++) line(C.l, [[x - 490 * s + i * 14 * s, y - 80 * s + i * 60 * s], [x + 490 * s - i * 14 * s, y - 80 * s + i * 60 * s]], { w: 4, col: K.ink, seed: 4310 + i, draw: clamp(g * 2 - 1) });
  if (o.house !== false && g > 0.6) {
    const hg = clamp((g - 0.6) / 0.4);
    O(C, [[x - 300 * s, y - 140 * s], [x - 300 * s, y - 330 * s], [x + 300 * s, y - 330 * s], [x + 300 * s, y - 140 * s], [x - 300 * s, y - 140 * s]], K.orange, 4320, { draw: hg, fill: hg });
    O(C, [[x - 340 * s, y - 320 * s], [x, y - 450 * s], [x + 340 * s, y - 320 * s], [x - 340 * s, y - 320 * s]], K.red, 4330, { draw: hg, fill: hg });
    [[-220, -290], [-60, -290], [100, -290]].forEach(([dx, dy], i) => O(C, [[x + dx * s, y + dy * s], [x + (dx + 90) * s, y + dy * s], [x + (dx + 90) * s, y + (dy + 80) * s], [x + dx * s, y + (dy + 80) * s], [x + dx * s, y + dy * s]], o.night ? K.yellow : K.sky, 4340 + i * 3, { draw: hg, fill: hg, lw: 5 }));
    const dc = o.door ?? 0;   // 0 = aberta (rampa), 1 = fechada
    O(C, [[x + 210 * s, y - 140 * s], [x + 210 * s, y - 140 * s - 150 * s * dc], [x + 280 * s, y - 140 * s - 150 * s * dc], [x + 280 * s, y - 140 * s], [x + 210 * s, y - 140 * s]], K.brown, 4350, { draw: hg, fill: hg, lw: 5 });
  }
}
function rain(api, t, k = 1, x0 = 0, x1 = 1920) {
  for (let i = 0; i < 70 * k; i++) { const x = x0 + hash(i) * (x1 - x0), y = ((hash(i + 9) * 1100 + t * 900) % 1200) - 100; line(api.FX, [[x, y], [x - 12, y + 46]], { w: 5, col: K.teal, p: 0.9, seed: 500 + i, wob: 0.2, taper: 0.4 }); }
}
function darkClouds(api, g = 1) { [[300, 160, 1.4], [900, 120, 1.6], [1550, 170, 1.4]].forEach(([x, y, s], i) => cloud(api.TOP, { x, y, s, seed: 1460 + i * 10, draw: g, fill: g, col: K.grey })); }
function rainbow(api, cx, cy, r0, g) { [K.red, K.orange, K.yellow, K.green, K.sky].forEach((c, i) => { const r = r0 - i * 34; const pts = []; for (let k = 0; k <= 40; k++) { const a = Math.PI + k / 40 * Math.PI; pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); } line(api.BG.l, pts, { w: 32, col: c, p: 1, seed: 400 + i, draw: clamp(g * 1.5 - i * 0.1) }); }); }
function dove(api, x, y, s, t, branch = false) { bird(api.TOP, { x, y, s, col: K.white, seed: 960, flip: true, pose: Math.floor(t * 6) % 2 }); if (branch) line(api.TOP.l, [[x - 52 * s, y + 4], [x - 90 * s, y + 20], [x - 110 * s, y + 6]], { w: 6, col: K.green, seed: 4400 }); }
const hammer = (lt, L) => Math.floor(lt * 3) % 2;

export const SCENES = {
  gancho: {
    draw(api, lt, L, d) {
      const { pr } = api;
      api.sky(700, 0.35); sun(api.TOP, { x: 1620, y: 220, R: 110, face: 1, seed: 1100 });
      api.ground(700, 1, SAND, 81);
      for (let i = 0; i < 7; i++) { const x = 520 + i * 140, g = pr(lt, 0.3 + i * 0.15, 0.7 + i * 0.15); line(api.G.l, [[x, 900], [x + 40, 560 + Math.abs(i - 3) * 40]], { w: 16, col: K.brown, seed: 4500 + i, draw: g }); }
      line(api.G.l, [[480, 900], [1460, 900]], { w: 16, col: K.brown, seed: 4520, draw: pr(lt, 0.2, 0.8) });
      const h = hammer(lt);
      person(api.TOP, { ...NOAH, x: 1560, y: 1000, s: 1.3, expr: 'happy', armL: h ? [[-34, -196], [-80, -260], [-110, -320]] : [[-34, -196], [-90, -220], [-140, -200]] });
    },
    fx: [[2.0, 'hammer'], [2.7, 'hammer'], [3.4, 'hammer'], [4.0, 'hammer']],
  },
  s1: {
    draw(api, lt, L) {
      const { pr } = api;
      api.sky(760, 0.35); api.ground(760);
      [[200, 0.9], [470, 0.8], [720, 0.85]].forEach(([x, s], i) => { const g = pr(lt, 0.2 + i * 0.2, 0.8 + i * 0.2); if (g > 0) house(api.G, { x, y: 820, s, seed: 1960 + i * 10, draw: g, fill: g }); });
      fill(api.BG.f, [[-80, -80], [880, -80], [880, 1200], [-80, 1200]], { col: K.grey, p: 0.45, gap: 14, w: 14, seed: 4600, boil: 0, draw: pr(lt, 0.4, 1.6) });
      [[220, 'man'], [480, 'woman'], [700, 'man']].forEach(([x, k], i) => { const g = pr(lt, 0.8 + i * 0.3, 1.5 + i * 0.3); if (g > 0) person(api.F, { x, y: 1060, s: 1.0, kind: k, cloth: K.grey, seed: 2800 + i * 30, expr: 'sad', draw: g, fill: g }); });
      const g2 = pr(lt, L[1], L[1] + 1.2);
      if (g2 > 0) { person(api.F, { ...NOAH, x: 1300, y: 1040, s: 1.25, expr: 'happy', draw: g2, fill: g2 }); person(api.F, { ...WIFE, x: 1520, y: 1040, s: 1.15, expr: 'happy', draw: g2, fill: g2 }); person(api.F, { kind: 'child', cloth: K.yellow, x: 1700, y: 1060, s: 0.8, seed: 2400, expr: 'happy', draw: g2, fill: g2 }); }
      if (g2 >= 1) heart(api.TOP, { x: 1410, y: 600, s: 1.2 * eo(pr(lt, L[1] + 1.2, L[1] + 1.8)), seed: 1300 });
    },
    fx: [[(L) => L[1], 'scratch', { dur: 1.2, pan: 0.5 }]],
  },
  s2: {
    glow: (lt) => [0.3, 0.88, 0.25, 0.5 * clamp(lt / 1.5)],
    draw(api, lt, L) {
      const { pr, O } = api;
      api.sky(800, 0.45); api.ground(800);
      person(api.F, { ...NOAH, x: 540, y: 1040, s: 1.5, expr: 'wow', armR: [[34, -196], [70, -250], [96, -300]] });
      for (let i = 0; i < 6; i++) line(api.TOP.l, [[560 + (i - 2.5) * 60, -20], [560 + (i - 2.5) * 30, 300]], { w: 6, col: K.yellow, seed: 4700 + i, draw: pr(lt, 0.3 + i * 0.1, 1.0 + i * 0.1) });
      const g = pr(lt, L[1] - 0.5, L[1] + 1.5);
      if (g > 0) {
        O(api.G, [[900, 200], [1800, 200], [1800, 720], [900, 720], [900, 200]], K.sky, 4720, { draw: g, fill: g, p: 0.6 });
        const gg = pr(lt, L[1] + 0.6, L[1] + 3.0); if (gg > 0) ark(api, api.TOP, 1350, 560, 0.62, gg);
      }
      if (lt > L[1] + 3.5) api.text('ARCA', 1350, 300, 80, { col: K.ink, reveal: pr(lt, L[1] + 3.5, L[1] + 4.0) });
    },
    fx: [[0.3, 'glow', { dur: 3 }], [(L) => L[1] - 0.5, 'scratch', { dur: 2.0, pan: 0.5 }], [(L) => L[1] + 3.5, 'write', { dur: 0.5 }]],
  },
  s3: {
    draw(api, lt, L, d) {
      const { pr } = api;
      const day = (lt / 2.2) % 1;   // o sol nasce e se põe várias vezes = anos de trabalho
      api.sky(780, 0.4); sun(api.TOP, { x: lerp(-100, 2020, day), y: 260 - Math.sin(day * Math.PI) * 120, R: 80, face: 1, seed: 1100 });
      api.ground(780);
      ark(api, api.G, 1100, 820, 0.85, clamp(lt / (d * 0.75)), { house: true });
      const h = hammer(lt);
      person(api.F, { ...NOAH, x: 1650, y: 1040, s: 1.2, expr: 'smile', armL: h ? [[-34, -196], [-80, -260], [-110, -320]] : [[-34, -196], [-90, -220], [-140, -200]] });
      person(api.F, { kind: 'man', cloth: K.green, x: 600, y: 1040, s: 1.0, seed: 2560, expr: 'smile', armR: h ? [[34, -196], [90, -220], [140, -200]] : [[34, -196], [80, -260], [110, -320]] });
      const g = pr(lt, L[1] - 0.3, L[1] + 0.8);
      if (g > 0 && lt < L[2]) { [[150, 'man', K.grey], [330, 'woman', K.grey]].forEach(([x, k, c], i) => person(api.F, { x, y: 1060, s: 0.9, kind: k, cloth: c, seed: 2800 + i * 30, expr: 'happy', draw: g, fill: g })); api.text('Ha ha!', 240, 640, 80, { col: K.red, reveal: pr(lt, L[1] + 0.3, L[1] + 0.8) }); }
    },
    fx: [[0.6, 'hammer'], [1.3, 'hammer'], [2.0, 'hammer'], [2.6, 'hammer'], [3.3, 'hammer'], [4.0, 'hammer'], [(L) => L[1] + 0.3, 'laugh']],
  },
  s4: {
    extra: 1.5,
    draw(api, lt, L, d) {
      const { pr, O } = api;
      api.sky(700, 0.45); api.ground(700);
      ark(api, api.G, 1350, 720, 0.85, 1);
      O(api.G, [[1520, 600], [1280, 960], [1360, 960], [1590, 600], [1520, 600]], K.brown, 4360, { lw: 5 });
      const walk = (k, slow = 1) => clamp((lt - 0.3 - k * 1.5) / (d * 0.55) * slow);
      const path = u => [lerp(-250, 1330, u), lerp(900, 790, u)];
      const A = [[elephant, 0.95, 800, 1.0], [giraffe, 0.85, 1700, 1.0], [lion, 1.0, 700, 1.0], [rabbit, 1.1, 600, 1.0], [turtle, 1.1, 1800, 0.6]];
      A.forEach(([fn, s, seed, slow], i) => { const u = walk(i, slow); if (u <= 0 || u >= 1) return; for (let p = 0; p < 2; p++) { const [x, y] = path(clamp(u - p * 0.07)); fn(api.F, { x, y: y + p * 20, s, seed: seed + p * 7, flip: false }); } });
    },
    fx: [[1.0, 'toot'], [2.0, 'pop'], [3.0, 'growl'], [4.0, 'squeak'], [5.5, 'pop']],
  },
  s5: {
    extra: 2.0,
    draw(api, lt, L, d) {
      const { pr } = api;
      const dark = pr(lt, L[1] - 0.5, L[1] + 1.0);
      api.sky(700, 0.45 + 0.3 * dark); api.ground(700);
      if (dark > 0) fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 700], [-80, 700]], { col: K.grey, p: 0.5 * dark, gap: 14, w: 14, seed: 4800, boil: 0 });
      ark(api, api.G, 960, 760, 0.95, 1, { door: ss(pr(lt, 0.8, 2.2)) });
      darkClouds(api, dark);
      if (lt > L[1]) rain(api, lt, pr(lt, L[1], L[1] + 2.0));
    },
    glow: (lt) => [0.62, 0.42, 0.15, 0.6 * clamp(lt / 0.8) * (1 - clamp((lt - 2.4) / 0.8))],
    fx: [[2.2, 'thud'], [(L) => L[1], 'rain', { dur: 9 }]],
  },
  s6: {
    draw(api, lt, L, d) {
      const { pr } = api;
      api.sky(1080, 0.6); fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1080], [-80, 1080]], { col: K.grey, p: 0.35 * (1 - pr(lt, L[2], L[2] + 2)), gap: 14, w: 14, seed: 4800, boil: 0 });
      const lvl = lerp(860, 700, pr(lt, L[1], L[1] + 2));
      [[260, 860], [1700, 820]].forEach(([x, y], i) => api.O(api.G, [[x - 220, 1080], [x, y], [x + 220, 1080], [x - 220, 1080]], K.green, 4900 + i * 3));
      api.sea(lvl, 1, lt, 3);
      const bob = Math.sin(lt * 2) * 10;
      ark(api, api.F, 960, lvl - 30 + bob, 0.8, 1, { door: 1, night: true });
      if (lt < L[2] + 1) { darkClouds(api, 1 - pr(lt, L[2], L[2] + 1.5)); rain(api, lt, 1 - pr(lt, L[2], L[2] + 1.5)); }
      if (lt > L[2]) heart(api.TOP, { x: 960, y: 300, s: 1.3 * eo(pr(lt, L[2] + 0.5, L[2] + 1.2)), seed: 1300 });
    },
    fx: [[0, 'rain', { dur: 8 }], [(L) => L[2] + 0.5, 'heart']],
  },
  s7: {
    draw(api, lt, L, d) {
      const { pr } = api;
      api.sky(1080, 0.45); sun(api.TOP, { x: 1650, y: 200, R: 90, face: 1, seed: 1100 });
      api.sea(820, 1, lt, 4);
      ark(api, api.F, 820, 800 + Math.sin(lt * 2) * 8, 0.8, 1, { door: 1 });
      person(api.TOP, { ...NOAH, x: 640, y: 950, s: 0.75, expr: 'happy', armR: [[34, -196], [70, -250], [96, -300]] });
      const u = pr(lt, 0.6, L[1] - 0.2), v = pr(lt, L[1] - 0.2, L[1] + 2.4);
      if (u > 0 && u < 1) dove(api, lerp(720, 1700, u), lerp(560, 300, u), 1.3, lt);
      if (v > 0) dove(api, lerp(1700, 760, v), lerp(300, 560, v), 1.3, lt, true);
    },
    fx: [[0.6, 'flap'], [(L) => L[1], 'flap'], [(L) => L[2], 'glint']],
  },
  s8: {
    extra: 1.5,
    draw(api, lt, L, d) {
      const { pr } = api;
      api.sky(1080, 0.45);
      rainbow(api, 960, 900, 760, pr(lt, L[1], L[1] + 3.0));
      api.O(api.G, [[400, 1080], [960, 640], [1520, 1080], [400, 1080]], K.green, 4950);
      ark(api, api.G, 960, 690, 0.55, 1, { door: 0 });
      const out = pr(lt, 0.4, L[1]);
      [[giraffe, 0.6, 1700, -1], [elephant, 0.6, 800, 1], [lion, 0.65, 700, -1], [sheep, 0.9, 500, 1], [rabbit, 0.8, 600, -1]].forEach(([fn, s, seed, dir], i) => { const u = clamp(out * 1.4 - i * 0.12); if (u <= 0) return; fn(api.F, { x: 960 + dir * (120 + u * (300 + i * 90)), y: 930 + u * 120, s, seed, flip: dir < 0 }); });
      person(api.TOP, { ...NOAH, x: 960, y: 1060, s: 1.1, expr: 'happy', armL: [[-34, -196], [-80, -250], [-110, -310]], armR: [[34, -196], [80, -250], [110, -310]] });
    },
    fx: [[(L) => L[1], 'shimmer', { dur: 3 }]],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      const { pr } = api;
      api.sky(1080, 0.35); rainbow(api, 960, 1000, 820, 1); api.ground(880);
      person(api.F, { kind: 'child', cloth: K.yellow, x: 960, y: 1060, s: 1.3, seed: 2400, expr: 'happy', armR: [[34, -196], [80, -230], [100, -290]] });
      heart(api.TOP, { x: 960, y: 520, s: 1.4 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
      const g = pr(lt, L[1], L[1] + 1.0);
      if (g > 0) { rabbit(api.F, { x: 600, y: 1060, s: 1.2, seed: 600, draw: g, fill: g }); sheep(api.F, { x: 1340, y: 1060, s: 1.4, seed: 500, draw: g, fill: g }); }
    },
    fx: [[0.6, 'glint'], [(L) => L[1], 'scratch', { dur: 1 }]],
  },
};
export function titleArt(api, t) {
  rainbow(api, 960, 1080, 330, api.pr(t, 4.6, 6.4));
}
