// Ep. 05 · Abraão e as Estrelas do Céu — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, sheep, sun, moon, cloud, heart, house, baby } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo, mulberry } from '/core/lib.js';
const K = PAL.crayon;
const SAND = '#e9c58a';
const ABRAO = { kind: 'man', beard: true, beardCol: K.white, hair: K.white, cloth: K.sky, belt: K.red, seed: 2500 };
const SARA = { kind: 'woman', scarf: K.pink, hair: K.white, cloth: K.orange, seed: 2700 };
const R = mulberry(55); const STARS = []; for (let i = 0; i < 160; i++) STARS.push([R() * 1920, R() * 640, 8 + R() * 14, R()]);

function night(api) { fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: '#2f3a78', p: 0.95, gap: 9, w: 13, ang: -0.2, seed: 5500, boil: 0, cross: true, crossP: 0.6 }); }
function stars(api, n, t = 0) { for (let i = 0; i < n && i < STARS.length; i++) { const [x, y, r, ph] = STARS[i]; api.star(api.TOP, x, y, r * (0.8 + 0.2 * Math.sin(t * 3 + ph * 6)), 5600 + i * 2); } }
function tent(api, C, x, y, s, seed = 5700) { api.O(C, [[x - 220 * s, y], [x, y - 260 * s], [x + 220 * s, y], [x - 220 * s, y]], K.orange, seed); api.O(C, [[x - 50 * s, y], [x, y - 130 * s], [x + 50 * s, y], [x - 50 * s, y]], K.brown, seed + 3, { lw: 5 }); for (let i = 1; i < 4; i++) line(C.l, [[x - 220 * s + i * 40 * s, y - i * 47 * s], [x + 220 * s - i * 40 * s, y - i * 47 * s]], { w: 4, col: K.red, seed: seed + 6 + i }); }
function camel(api, C, x, y, s, seed, t = 0) {
  const leg = (dx, ph) => api.O(C, [[x + (dx - 9) * s, y - 150 * s], [x + (dx + 9) * s, y - 150 * s], [x + (dx + 9 + 8 * Math.sin(t * 6 + ph)) * s, y], [x + (dx - 9 + 8 * Math.sin(t * 6 + ph)) * s, y], [x + (dx - 9) * s, y - 150 * s]], SAND, seed + dx, { lw: 5 });
  [-60, -30, 40, 70].forEach((dx, i) => leg(dx, i));
  api.O(C, smooth([[x - 100 * s, y - 140 * s], [x - 70 * s, y - 230 * s], [x - 20 * s, y - 180 * s], [x + 20 * s, y - 240 * s], [x + 90 * s, y - 150 * s], [x + 80 * s, y - 120 * s], [x - 90 * s, y - 110 * s]], 4), SAND, seed + 90);
  api.O(C, smooth([[x + 80 * s, y - 150 * s], [x + 130 * s, y - 250 * s], [x + 170 * s, y - 250 * s], [x + 175 * s, y - 225 * s], [x + 140 * s, y - 215 * s], [x + 105 * s, y - 130 * s]], 4), SAND, seed + 95);
  dab(C.l, x + 155 * s, y - 238 * s, 4 * s, { col: K.ink, p: 1, seed: seed + 99 });
}
function crib(api, C, x, y, s, seed) { api.O(C, smooth([[x - 110 * s, y - 70 * s], [x + 110 * s, y - 70 * s], [x + 90 * s, y + 20 * s], [x - 90 * s, y + 20 * s]], 3).concat([[x - 110 * s, y - 70 * s]]), K.brown, seed); [[-80, 20], [80, 20]].forEach(([dx], i) => line(C.l, [[x + dx * s, y + 20 * s], [x + (dx + (i ? 20 : -20)) * s, y + 70 * s]], { w: 7, col: K.ink, seed: seed + 5 + i })); }
function confetti(api, t, n = 40) { for (let i = 0; i < n; i++) { const x = hash(i) * 1920, y = ((hash(i + 3) * 1080 + t * 160) % 1150) - 60; api.star(api.TOP, x, y, 10 + hash(i + 7) * 8, 5900 + i * 2, [K.yellow, K.pink, K.sky, K.orange][i % 4]); } }

export const SCENES = {
  gancho: {
    cam: (lt, L, d) => [960, lerp(640, 520, ss(lt / d)), 1.1],
    draw(api, lt, L, d) {
      night(api); stars(api, Math.floor(api.pr(lt, 0, d * 0.8) * 160), lt); moon(api.TOP, { x: 1700, y: 160, R: 90, seed: 1200 });
      api.ground(900, 1, '#4f7a3f');
      person(api.F, { ...ABRAO, x: 760, y: 1120, s: 1.3, expr: 'wow', armL: [[-34, -196], [-80, -250], [-110, -310]] });
    },
    fx: [[0.5, 'shimmer'], [(L) => L[1], 'glint']],
  },
  s1: {
    glow: (lt) => [0.25, 0.9, 0.25, 0.4 * clamp((lt - 2) / 1.5)],
    draw(api, lt, L) {
      api.sky(720, 0.45); api.ground(720, 1, SAND, 81); sun(api.TOP, { x: 1700, y: 200, R: 80, face: 1, seed: 1100 });
      [[1200, 0.8], [1450, 0.9], [1700, 0.75]].forEach(([x, s], i) => house(api.G, { x, y: 800, s, seed: 1960 + i * 10 }));
      person(api.F, { ...ABRAO, x: 600, y: 1060, s: 1.35, expr: lt > L[1] ? 'wow' : 'smile', armR: lt > L[1] ? [[34, -196], [70, -250], [96, -300]] : undefined });
      if (lt > L[1]) for (let i = 0; i < 6; i++) line(api.TOP.l, [[620 + (i - 2.5) * 60, -20], [620 + (i - 2.5) * 30, 380]], { w: 6, col: K.yellow, seed: 5950 + i, draw: api.pr(lt, L[1] + i * 0.1, L[1] + 0.8 + i * 0.1) });
      if (lt > L[2]) heart(api.TOP, { x: 600, y: 450, s: 1.0 * eo(api.pr(lt, L[2], L[2] + 0.6)), seed: 1300 });
    },
    fx: [[(L) => L[1], 'glow', { dur: 2 }], [(L) => L[2], 'heart']],
  },
  s2: {
    draw(api, lt, L, d) {
      api.sky(700, 0.4); api.ground(700, 1, SAND, 83); sun(api.TOP, { x: 1650, y: 210, R: 90, face: 1, seed: 1100 });
      const pts = []; for (let k = 0; k < 18; k += 2) { const u0 = k / 18, u1 = (k + 1) / 18; pts.push([[lerp(100, 1820, u0), 760 + 40 * Math.sin(u0 * 6)], [lerp(100, 1820, u1), 760 + 40 * Math.sin(u1 * 6)]]); }
      pts.forEach((sg, j) => { if (j / pts.length < api.pr(lt, 0.3, 3)) line(api.G.l, sg, { w: 6, col: K.red, seed: 6000 + j }); });
      const off = lt * 40;
      camel(api, api.F, 1350 - off, 1000, 1.2, 6100, lt); sheep(api.F, { x: 1650 - off, y: 1040, s: 1.4, seed: 500 }); sheep(api.F, { x: 1800 - off, y: 1060, s: 1.2, seed: 507 });
      person(api.TOP, { ...ABRAO, x: 760 - off, y: 1060, s: 1.15, walk: lt * 6, flip: true });
      person(api.TOP, { ...SARA, x: 960 - off, y: 1060, s: 1.1, walk: lt * 6 + 1.5, flip: true });
    },
    fx: [[0.6, 'baa'], [3.0, 'baa']],
  },
  s3: {
    draw(api, lt, L) {
      api.sky(720, 0.35); api.ground(720, 1, SAND, 84); tent(api, api.G, 960, 820, 1.4);
      person(api.F, { ...ABRAO, x: 640, y: 1060, s: 1.25, expr: lt > L[1] ? 'sad' : 'smile' });
      person(api.F, { ...SARA, x: 1280, y: 1060, s: 1.2, expr: lt > L[1] ? 'sad' : 'smile' });
      crib(api, api.F, 960, 1000, 1.2, 6200);
    },
  },
  s4: {
    cam: (lt, L, d) => [960, lerp(600, 420, ss(lt / d)), 1.1],
    draw(api, lt, L, d) {
      night(api); stars(api, Math.floor(api.pr(lt, 0.5, d * 0.9) ** 2 * 160), lt);
      api.ground(880, 1, '#4f7a3f'); tent(api, api.G, 1550, 900, 0.9);
      person(api.F, { ...ABRAO, x: 760, y: 1110, s: 1.3, expr: 'wow', armL: [[-34, -196], [-80, -250], [-110, -310]], armR: [[34, -196], [80, -250], [110, -310]] });
    },
    fx: [[0.5, 'shimmer'], [(L) => L[1], 'shimmer']],
  },
  s5: {
    draw(api, lt, L, d) {
      night(api); stars(api, 160, lt); api.ground(880, 1, '#4f7a3f');
      const hg = api.pr(lt, 0.3, 1.5); if (hg > 0) heart(api.TOP, { x: 960, y: 330, s: 3.2 * eo(hg), seed: 1300, col: K.yellow });
      person(api.F, { ...ABRAO, x: 960, y: 1110, s: 1.35, expr: 'happy' });
      if (lt > L[1] + 1.0) api.text('ABRAÃO', 960, 650, 110, { col: K.yellow, reveal: api.pr(lt, L[1] + 1.0, L[1] + 1.8) });
    },
    fx: [[0.3, 'shimmer'], [(L) => L[1] + 1.0, 'write', { dur: 0.8 }]],
  },
  s6: {
    draw(api, lt, L) {
      api.sky(720, 0.4); api.ground(720, 1, SAND, 85); tent(api, api.G, 1480, 840, 1.3);
      [[360, K.white], [560, K.white], [760, K.white]].forEach(([x, c], i) => person(api.F, { kind: 'man', cloth: c, belt: K.yellow, x, y: 1060, s: 1.1, seed: 2580 + i * 20, expr: 'happy', halo: true }));
      person(api.F, { ...SARA, x: 1480, y: 1000, s: 0.95, expr: lt > L[1] ? 'happy' : 'wow' });
      if (lt > L[1]) api.text('hi hi!', 1480, 560, 80, { col: K.red, reveal: api.pr(lt, L[1], L[1] + 0.5) });
    },
    fx: [[(L) => L[1], 'laugh']],
  },
  s7: {
    draw(api, lt, L, d) {
      api.sky(720, 0.45); api.ground(720, 1, SAND, 86); sun(api.TOP, { x: 1700, y: 200, R: 90, face: 1, seed: 1100 });
      tent(api, api.G, 400, 820, 1.0);
      const jump = Math.abs(Math.sin(lt * 4)) * 30;
      person(api.F, { ...ABRAO, x: 760, y: 1060 - jump, s: 1.25, expr: 'happy', armL: [[-34, -196], [-80, -250], [-110, -310]], armR: [[34, -196], [80, -250], [110, -310]] });
      person(api.F, { ...SARA, x: 1160, y: 1060, s: 1.2, expr: 'happy', armR: [[34, -196], [60, -170], [40, -150]], armL: [[-34, -196], [-60, -170], [-40, -150]] });
      baby(api.TOP, { x: 1210, y: 1060 - 160 * 1.2, s: 1.1, seed: 2600 });
      if (lt > L[1] + 1.5) api.text('ISAQUE', 1160, 600, 100, { col: K.red, reveal: api.pr(lt, L[1] + 1.5, L[1] + 2.2) });
      if (lt > L[2] - 0.5) confetti(api, lt);
    },
    fx: [[0.3, 'shimmer'], [(L) => L[1] + 1.5, 'write', { dur: 0.7 }], [(L) => L[2], 'laugh']],
  },
  licao: {
    calm: true,
    draw(api, lt, L, d) {
      night(api); stars(api, 160, lt); api.ground(880, 1, '#4f7a3f'); house(api.G, { x: 1500, y: 960, s: 0.9, seed: 1960 });
      person(api.F, { kind: 'man', cloth: K.green, x: 640, y: 1110, s: 1.2, seed: 2560, expr: 'happy', armR: [[34, -196], [70, -250], [96, -300]] });
      person(api.F, { kind: 'child', cloth: K.yellow, x: 860, y: 1110, s: 0.95, seed: 2400, expr: 'wow', armR: [[34, -196], [80, -230], [100, -290]] });
      if (lt > L[3]) ['1', '2', '3'].forEach((n, i) => api.text(n, 500 + i * 220, 200 + i * 40, 90, { col: K.yellow, reveal: api.pr(lt, L[3] + 0.4 + i * 0.5, L[3] + 0.6 + i * 0.5) }));
    },
    fx: [[(L) => L[3] + 0.4, 'write', { dur: 1.4 }]],
  },
};
export function titleArt(api, t) { for (let i = 0; i < 12; i++) if (api.pr(t, 4.5 + i * 0.12, 4.7 + i * 0.12) > 0) api.star(api.TOP, 260 + i * 130, 860 + 40 * Math.sin(i), 26, 5800 + i * 2); }
