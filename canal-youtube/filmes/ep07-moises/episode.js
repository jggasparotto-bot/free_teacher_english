// Ep. 07 · O Bebê Moisés e a Sarça Ardente — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, sheep, sun, cloud, heart, baby, bird } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const SAND = '#e9c58a';
const Li = (L, i) => L[Math.min(i, L.length - 1)];
const MAE = { kind: 'woman', scarf: K.sky, cloth: K.orange, seed: 2700 };
const PRINCESA = { kind: 'woman', crown: true, cloth: K.pink, seed: 2750 };
const MIRIA = { kind: 'child', cloth: K.green, seed: 2450 };
const MOISES = { kind: 'man', beard: true, cloth: K.red, belt: K.yellow, seed: 2500 };
const ARAO = { kind: 'man', beard: true, beardCol: K.grey, cloth: K.sky, seed: 2560 };
const FARAO = { kind: 'man', crown: true, cloth: K.white, belt: K.sky, seed: 2580 };

function nile(api, y0, t) { api.sea(y0, 1, t, 2, K.sky); }
function reeds(api, x0, n, y = 1080) { for (let i = 0; i < n; i++) { const x = x0 + i * 46; line(api.TOP.l, [[x, y], [x + 8, y - 260 - hash(i + x0) * 120]], { w: 9, col: K.green, seed: 7400 + x }); api.O(api.TOP, ellipse(x + 10, y - 270 - hash(i + x0) * 120, 12, 42, 14), K.brown, 7500 + x, { lw: 4 }); } }
function basket(api, C, x, y, s, seed = 7600) { api.O(C, smooth([[x - 160 * s, y - 40 * s], [x + 160 * s, y - 40 * s], [x + 130 * s, y + 60 * s], [x - 130 * s, y + 60 * s]], 3).concat([[x - 160 * s, y - 40 * s]]), K.orange, seed, { lw: 7 }); for (let i = 0; i < 3; i++) line(C.l, [[x - 140 * s + i * 14 * s, y - 10 * s + i * 22 * s], [x + 140 * s - i * 14 * s, y - 10 * s + i * 22 * s]], { w: 4, col: K.ink, seed: seed + 5 + i }); }
function pyramids(api) { [[350, 740, 280], [760, 740, 200], [1550, 740, 240]].forEach(([x, y, r], i) => api.O(api.G, [[x - r, y], [x, y - r * 1.1], [x + r, y], [x - r, y]], K.yellow, 6400 + i * 3)); }
function bricks(api, x, y, n, seed) { for (let i = 0; i < n; i++) api.O(api.TOP, [[x + (i % 3) * 70, y - Math.floor(i / 3) * 36], [x + (i % 3) * 70 + 66, y - Math.floor(i / 3) * 36], [x + (i % 3) * 70 + 66, y - Math.floor(i / 3) * 36 - 32], [x + (i % 3) * 70, y - Math.floor(i / 3) * 36 - 32], [x + (i % 3) * 70, y - Math.floor(i / 3) * 36]], K.red, seed + i * 3, { lw: 4 }); }
function burningBush(api, x, y, s, t, g = 1) {
  const leaf = []; for (let i = 0; i <= 60; i++) { const a = Math.PI + i / 60 * Math.PI; const b = 1 + 0.15 * Math.abs(Math.sin(a * 5)); leaf.push([x + Math.cos(a) * 220 * s * b, y + Math.sin(a) * 180 * s * b]); } leaf.push([x + 220 * s, y], [x - 220 * s, y]);
  part(api.G, leaf, { col: K.green, p: 0.9, gap: 10, w: 12, seed: 7700, cross: true, crossP: 0.4 }, { w: 7, col: K.ink, seed: 7701 });
  if (g <= 0) return;
  const step = Math.floor(t * 8);
  for (let i = 0; i < 7; i++) { const fx = x + (i - 3) * 60 * s, h = (160 + 70 * hash(i + step * 0.37)) * s * g; part(api.TOP, smooth([[fx - 34 * s, y - 60 * s], [fx - 20 * s, y - 60 * s - h * 0.6], [fx + (hash(i + step) - 0.5) * 30 * s, y - 60 * s - h], [fx + 20 * s, y - 60 * s - h * 0.6], [fx + 34 * s, y - 60 * s]], 4, false).concat([[fx - 34 * s, y - 60 * s]]), { col: i % 2 ? K.orange : K.yellow, p: 1, gap: 6, w: 8, seed: 7710 + i * 3 + step % 2 }, { w: 5, col: K.red, seed: 7740 + i }); }
}

export const SCENES = {
  gancho: {
    cam: (lt, L, d) => [lerp(700, 1000, ss(lt / d)), 640, 1.25],
    draw(api, lt) {
      api.sky(600, 0.4); nile(api, 600, lt); reeds(api, 60, 8); reeds(api, 1500, 9);
      const bob = Math.sin(lt * 2) * 10;
      basket(api, api.F, 900 + lt * 25, 860 + bob, 1.3); baby(api.TOP, { x: 960 + lt * 25, y: 820 + bob, s: 1.5, seed: 2600 });
    },
    fx: [[0.4, 'splash', { small: 1 }]],
  },
  s1: {
    draw(api, lt, L) {
      api.sky(740, 0.4); api.ground(740, 1, SAND, 81); sun(api.TOP, { x: 1700, y: 190, R: 80, face: 1, seed: 1100 }); pyramids(api);
      person(api.F, { ...FARAO, x: 300, y: 1060, s: 1.35, expr: 'sad', armR: [[34, -196], [90, -220], [130, -200]] });
      [[800, K.grey], [1100, K.grey], [1400, K.grey]].forEach(([x, c], i) => { const g = api.pr(lt, Li(L, 1) + i * 0.3, Li(L, 1) + 0.8 + i * 0.3); if (g > 0) { person(api.F, { kind: 'man', cloth: c, x, y: 1060, s: 1.0, seed: 2800 + i * 30, expr: 'sad', draw: g, fill: g, armL: [[-34, -196], [-50, -260], [-20, -300]], armR: [[34, -196], [50, -260], [20, -300]] }); bricks(api, x - 100, 1060 - 300, 3, 7800 + i * 10); } });
    },
    fx: [[(L) => Li(L, 1), 'hammer'], [(L) => Li(L, 1) + 0.8, 'hammer']],
  },
  s2: {
    draw(api, lt, L) {
      api.sky(700, 0.35); nile(api, 860, lt); reeds(api, 1400, 10);
      api.ground(860, 1, '#7bae5a', 82);
      person(api.F, { ...MAE, x: 700, y: 1000, s: 1.3, expr: lt > Li(L, 1) ? 'smile' : 'sad', armR: [[34, -196], [70, -150], [100, -110]] });
      const g = api.pr(lt, Li(L, 2), Li(L, 2) + 1.5);
      if (g > 0) { basket(api, api.F, 1050 + g * 150, 960 + Math.sin(lt * 2) * 8, 1.0); baby(api.TOP, { x: 1100 + g * 150, y: 930 + Math.sin(lt * 2) * 8, s: 1.2, seed: 2600 }); }
      else baby(api.TOP, { x: 820, y: 860, s: 1.2, seed: 2600 });
    },
    fx: [[(L) => Li(L, 2) + 1.2, 'splash', { small: 1 }]],
  },
  s3: {
    draw(api, lt, L) {
      api.sky(640, 0.4); nile(api, 860, lt); reeds(api, 60, 6);
      api.ground(860, 1, '#7bae5a', 83);
      person(api.F, { ...PRINCESA, x: 1050, y: 1030, s: 1.35, expr: 'happy', armL: [[-34, -196], [-80, -170], [-120, -150]] });
      basket(api, api.F, 640, 880, 0.9); baby(api.TOP, { x: 680, y: 855, s: 1.1, seed: 2600 });
      const g = api.pr(lt, Li(L, 1), Li(L, 1) + 0.8);
      if (g > 0) person(api.F, { ...MIRIA, x: 1500, y: 1040, s: 1.0, expr: 'happy', draw: g, fill: g });
      const g2 = api.pr(lt, Li(L, 2), Li(L, 2) + 0.8);
      if (g2 > 0) person(api.F, { ...MAE, x: 1720, y: 1040, s: 1.2, expr: 'happy', draw: g2, fill: g2 });
      if (lt > Li(L, 2) + 0.8) heart(api.TOP, { x: 1600, y: 560, s: 1.1 * eo(api.pr(lt, Li(L, 2) + 0.8, Li(L, 2) + 1.4)), seed: 1300 });
    },
    fx: [[(L) => Li(L, 2) + 0.8, 'heart']],
  },
  s4: {
    draw(api, lt, L) {
      const grown = lt > Li(L, 1);
      if (!grown) {
        fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.yellow, p: 0.25, gap: 14, w: 14, seed: 7900, boil: 0 });
        [[300], [1620]].forEach(([x], i) => api.O(api.G, [[x - 50, 1080], [x - 50, 160], [x + 50, 160], [x + 50, 1080], [x - 50, 1080]], K.orange, 7910 + i * 3));
        person(api.F, { ...PRINCESA, x: 820, y: 1060, s: 1.3, expr: 'happy' }); person(api.F, { kind: 'child', crown: true, cloth: K.white, x: 1080, y: 1060, s: 1.0, seed: 2470, expr: 'happy' });
        api.text('MOISÉS', 960, 300, 110, { col: K.red, reveal: api.pr(lt, 1.0, 1.8) });
      } else {
        api.sky(720, 0.4); api.ground(720, 1, SAND, 84); sun(api.TOP, { x: 1700, y: 200, R: 80, face: 1, seed: 1100 });
        person(api.F, { ...MOISES, x: 800, y: 1060, s: 1.3, expr: 'smile' });
        line(api.TOP.l, [[800 + 90, 1060 - 330], [800 + 110, 1060]], { w: 10, col: K.brown, seed: 7920 });
        [1150, 1400, 1650].forEach((x, i) => sheep(api.F, { x, y: 1060 - i * 10, s: 1.4, seed: 500 + i * 7 }));
      }
    },
    fx: [[1.0, 'write', { dur: 0.8 }], [(L) => Li(L, 1), 'page', { dur: 1.0 }], [(L) => Li(L, 1) + 1.5, 'baa']],
  },
  s5: {
    glow: (lt) => [0.66, 0.42, 0.18, 0.5 * clamp(lt / 1.5)],
    draw(api, lt, L) {
      api.sky(720, 0.4); api.ground(720, 1, SAND, 85);
      burningBush(api, 1260, 900, 1.2, lt, api.pr(lt, 0.5, 2.0));
      const near = api.pr(lt, Li(L, 1) - 1, Li(L, 1) + 1);
      person(api.F, { ...MOISES, x: lerp(500, 760, near), y: 1060, s: 1.3, expr: 'wow', walk: near > 0 && near < 1 ? lt * 6 : undefined });
      if (lt > Li(L, 1) + 1.2) api.text('Moisés!', 1260, 330, 100, { col: K.red, reveal: api.pr(lt, Li(L, 1) + 1.2, Li(L, 1) + 1.8) });
    },
    fx: [[0.5, 'fire'], [2.0, 'fire'], [3.5, 'fire'], [5.0, 'fire'], [(L) => Li(L, 1) + 1.2, 'glow', { dur: 1.5 }]],
  },
  s6: {
    glow: (lt) => [0.66, 0.42, 0.2, 0.5],
    draw(api, lt, L) {
      api.sky(720, 0.4); api.ground(720, 1, SAND, 86); burningBush(api, 1260, 900, 1.2, lt, 1);
      person(api.F, { ...MOISES, x: 700, y: 1060, s: 1.3, expr: 'wow', armL: [[-34, -196], [-30, -260], [-6, -300]], armR: [[34, -196], [30, -260], [6, -300]] });
      if (lt > 1.2) [[560, 1070], [640, 1080]].forEach(([x, y], i) => api.O(api.TOP, ellipse(x, y, 40, 14, 16), K.brown, 7950 + i * 3, { lw: 5 }));
      if (lt > Li(L, 1)) for (let i = 0; i < 3; i++) person(api.TOP, { kind: 'man', cloth: K.grey, x: 220 + i * 110, y: 600, s: 0.4, seed: 2800 + i * 30, expr: 'sad' });
    },
    fx: [[0.5, 'fire'], [2.5, 'fire'], [1.2, 'thud']],
  },
  s7: {
    draw(api, lt, L) {
      api.sky(720, 0.4); api.ground(720, 1, SAND, 87);
      person(api.F, { ...MOISES, x: 760, y: 1060, s: 1.3, expr: lt > Li(L, 1) ? 'smile' : 'sad' });
      if (lt < Li(L, 1)) api.text('?', 760, 520, 140, { col: K.red });
      if (lt > Li(L, 1)) { heart(api.TOP, { x: 760, y: 470, s: 1.2 * eo(api.pr(lt, Li(L, 1), Li(L, 1) + 0.6)), seed: 1300 }); for (let i = 0; i < 6; i++) line(api.TOP.l, [[760 + (i - 2.5) * 60, -20], [760 + (i - 2.5) * 30, 380]], { w: 6, col: K.yellow, seed: 7970 + i }); }
      const g = api.pr(lt, Li(L, 2), Li(L, 2) + 1.0);
      if (g > 0) person(api.F, { ...ARAO, x: 1150, y: 1060, s: 1.3, expr: 'happy', draw: g, fill: g, armL: [[-34, -196], [-90, -210], [-140, -200]] });
    },
    fx: [[(L) => Li(L, 1), 'heart'], [(L) => Li(L, 2), 'scratch', { dur: 1 }]],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      api.sky(1080, 0.35); api.ground(860);
      person(api.F, { kind: 'woman', scarf: K.pink, cloth: K.sky, x: 860, y: 1060, s: 1.35, seed: 2700, expr: 'happy', armR: [[34, -196], [80, -190], [130, -170]] });
      person(api.F, { kind: 'child', cloth: K.yellow, x: 1100, y: 1060, s: 1.0, seed: 2400, expr: 'happy', armL: [[-34, -196], [-80, -190], [-120, -170]] });
      heart(api.TOP, { x: 980, y: 420, s: 1.5 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
    },
  },
};
export function titleArt(api, t) { const g = api.pr(t, 4.5, 6.0); if (g > 0) { basket(api, api.G, 960, 900, 0.9 * g); } }
