// Ep. 09 · As Muralhas de Jericó — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, sun, moon, cloud, heart, house } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const SAND = '#e9c58a';
const Li = (L, i) => L[Math.min(i, L.length - 1)];
const JOSUE = { kind: 'man', beard: true, cloth: K.sky, belt: K.red, seed: 2500 };
const PADRE = (i) => ({ kind: 'man', cloth: K.white, belt: K.sky, seed: 2700 + i * 19 });
const POVO = [['man', K.green], ['woman', K.orange, K.pink], ['child', K.yellow], ['man', K.red], ['woman', K.green, K.yellow], ['child', K.pink]];

function wall(api, x0, x1, top, g = 1, crumble = 0, seed = 9200) {   // muralha de tijolos; crumble = 0..1 desabando
  const rows = 6, bw = 120, bh = 70;
  for (let r = 0; r < rows; r++) for (let c = 0; x0 + c * bw < x1; c++) {
    const i = r * 40 + c; const gi = clamp(g * rows * 1.2 - (rows - 1 - r)); if (gi <= 0) continue;
    let x = x0 + c * bw + (r % 2) * bw / 2, y = top + r * bh;
    let rot = 0;
    if (crumble > 0) { const k = clamp(crumble * 1.6 - hash(i) * 0.6); y += k * k * (rows - r) * bh * 1.4 + k * 30; x += (hash(i + 3) - 0.5) * 120 * k; rot = (hash(i + 7) - 0.5) * 1.6 * k; }
    const cx = x + bw / 2, cy = y + bh / 2, ca = Math.cos(rot), sa = Math.sin(rot);
    const pts = [[-bw / 2, -bh / 2], [bw / 2, -bh / 2], [bw / 2, bh / 2], [-bw / 2, bh / 2], [-bw / 2, -bh / 2]].map(([px, py]) => [cx + px * ca - py * sa, cy + px * sa + py * ca]);
    api.O(api.G, pts, (r + c) % 3 ? K.orange : K.peach, seed + i * 3, { lw: 5, draw: gi, fill: gi });
  }
}
function trumpet(api, x, y, s, seed, flip = 1) { api.O(api.TOP, [[x, y - 8 * s], [x + flip * 150 * s, y - 34 * s], [x + flip * 170 * s, y - 50 * s], [x + flip * 170 * s, y + 30 * s], [x + flip * 150 * s, y + 18 * s], [x, y + 8 * s], [x, y - 8 * s]], K.yellow, seed, { lw: 5 }); }
function guard(api, x, y, s, seed, expr) { person(api.TOP, { kind: 'man', helmet: true, cloth: K.grey, x, y, s, seed, expr }); }
function march(api, lt, y = 1060, n = 6, x0 = -200, speed = 70) { for (let i = 0; i < n; i++) { const [k, c, sc] = POVO[i % 6]; const x = ((x0 + i * 300 + lt * speed) % 2300) - 200; person(api.F, { kind: k, cloth: c, scarf: sc, x, y: y + (i % 2) * 8, s: k === 'child' ? 0.75 : 0.95, seed: 2800 + i * 31, expr: 'smile', walk: lt * 6 + i }); } }

export const SCENES = {
  gancho: {
    draw(api, lt, L, d) {
      api.sky(700, 0.45); api.ground(900, 1, SAND, 81);
      wall(api, 100, 1820, 380, api.pr(lt, 0.2, 2.0));
      [400, 960, 1500].forEach((x, i) => guard(api, x, 380, 0.7, 2900 + i * 17, 'smile'));
      person(api.F, { ...PADRE(0), x: 960, y: 1060, s: 1.3, expr: 'happy', armR: [[34, -196], [70, -240], [40, -260]] }); trumpet(api, 960 + 50, 1060 - 260 * 1.3, 1.2, 9500);
    },
    fx: [[0.3, 'scribble', { dur: 2 }], [(L) => Li(L, 0) + 2.5, 'toot']],
  },
  s1: {
    draw(api, lt, L) {
      api.sky(700, 0.45); sun(api.TOP, { x: 1700, y: 180, R: 80, face: 1, seed: 1100 }); api.ground(820, 1, SAND, 82);
      wall(api, 700, 1900, 320, 1);
      api.O(api.G, [[1180, 740], [1180, 560], [1420, 560], [1420, 740], [1180, 740]], K.brown, 9300); line(api.G.l, [[1300, 560], [1300, 740]], { w: 5, col: K.ink, seed: 9310 });
      if (lt > Li(L, 1) - 0.5) api.O(api.TOP, ellipse(1300, 650, 30, 30, 16), K.grey, 9320, { lw: 5 });
      march(api, 0, 1060, 3, 0, 0);
      person(api.F, { ...JOSUE, x: 900, y: 1060, s: 1.2, expr: 'wow' });
    },
    fx: [[(L) => Li(L, 1) - 0.5, 'thud']],
  },
  s2: {
    glow: (lt) => [0.3, 0.9, 0.25, 0.45 * clamp(lt / 1.5)],
    draw(api, lt, L) {
      api.sky(760, 0.45); api.ground(760, 1, SAND, 83);
      person(api.F, { ...JOSUE, x: 560, y: 1060, s: 1.35, expr: 'wow', armL: [[-34, -196], [-30, -260], [-6, -300]], armR: [[34, -196], [30, -260], [6, -300]] });
      for (let i = 0; i < 6; i++) line(api.TOP.l, [[580 + (i - 2.5) * 60, -20], [580 + (i - 2.5) * 30, 360]], { w: 6, col: K.yellow, seed: 9400 + i });
      const g = api.pr(lt, 0.5, 2.5);
      if (g > 0) { api.O(api.G, handCircle(1350, 520, 260, 9410, 0, 60), null, 9411, { draw: g }); api.O(api.G, [[1250, 420], [1450, 420], [1450, 620], [1250, 620], [1250, 420]], K.orange, 9420, { draw: g, fill: g }); }
      for (let i = 0; i < 7; i++) if (lt > Li(L, 1) + i * 0.35) api.text(String(i + 1), 1350 + Math.cos(i / 7 * 6.28 - 1.57) * 330, 520 + Math.sin(i / 7 * 6.28 - 1.57) * 330, 70, { col: i === 6 ? K.red : K.ink });
    },
    fx: [[0.5, 'scratch', { dur: 2 }], [(L) => Li(L, 1), 'write', { dur: 2.4 }]],
  },
  s3: {
    draw(api, lt, L, d) {
      const day = Math.floor(lt / (d / 6));
      api.sky(700, 0.45); sun(api.TOP, { x: lerp(-100, 2020, (lt / (d / 6)) % 1), y: 200, R: 70, face: 1, seed: 1100 }); api.ground(820, 1, SAND, 84);
      wall(api, 100, 1820, 320, 1);
      [400, 960, 1500].forEach((x, i) => guard(api, x, 320, 0.7, 2900 + i * 17, lt > Li(L, 1) ? 'happy' : 'smile'));
      if (lt > Li(L, 1) && lt < Li(L, 2)) api.text('Ha ha!', 960, 120, 80, { col: K.red });
      march(api, lt);
      api.text(String(Math.min(6, day + 1)), 160, 120, 110, { col: K.red });
    },
    fx: [[0.5, 'hammer'], [1.5, 'hammer'], [2.5, 'hammer'], [(L) => Li(L, 1), 'laugh']],
  },
  s4: {
    draw(api, lt, L, d) {
      api.sky(700, 0.45); api.ground(820, 1, SAND, 85);
      wall(api, 100, 1820, 320, 1);
      march(api, lt, 1060, 6, -200, 220);
      const n = Math.min(7, Math.floor(lt / ((d - 1.5) / 7)) + 1);
      api.text(String(n), 960, 160, 220, { col: n === 7 ? K.red : K.ink, seed: 9600 + n });
    },
    fx: [[1, 'pop'], [2.4, 'pop'], [3.8, 'pop'], [5.2, 'pop'], [6.6, 'pop'], [8.0, 'pop'], [9.4, 'shimmer']],
  },
  s5: {
    draw(api, lt, L) {
      api.sky(700, 0.45); api.ground(820, 1, SAND, 86); wall(api, 100, 1820, 320, 1);
      for (let i = 0; i < 4; i++) { person(api.F, { ...PADRE(i), x: 260 + i * 230, y: 1060, s: 1.05, expr: 'happy', armR: [[34, -196], [70, -240], [40, -260]] }); trumpet(api, 260 + i * 230 + 45, 1060 - 260 * 1.05, 1.0, 9700 + i * 5); }
      person(api.F, { ...JOSUE, x: 1350, y: 1060, s: 1.3, expr: lt > Li(L, 1) ? 'sing' : 'smile', armR: lt > Li(L, 1) ? [[34, -196], [70, -250], [96, -310]] : undefined });
      if (lt > Li(L, 2)) { march(api, 0, 1060, 2, 1780, 0); api.text('EEEH!', 1500, 520, 130, { col: K.red, reveal: api.pr(lt, Li(L, 2), Li(L, 2) + 0.4) }); }
    },
    fx: [[0.6, 'toot'], [1.2, 'toot'], [(L) => Li(L, 2), 'crowd', { dur: 2.5 }]],
  },
  s6: {
    extra: 1.0,
    draw(api, lt, L) {
      api.sky(700, 0.45); api.ground(820, 1, SAND, 87);
      const fall = ss(api.pr(lt, 0.3, 3.0));
      wall(api, 100, 1820, 320, 1, fall);
      if (lt > Li(L, 1)) { house(api.TOP, { x: 1500, y: 700, s: 0.9, seed: 1960 }); line(api.TOP.l, [[1560, 590], [1580, 700], [1570, 820]], { w: 10, col: K.red, seed: 9800 }); }
      if (lt > Li(L, 1)) person(api.F, { kind: 'woman', scarf: K.red, cloth: K.yellow, x: 1250, y: 1060, s: 1.1, seed: 2780, expr: 'happy' });
      march(api, 0, 1060, 3, 100, 0);
    },
    fx: [[0.3, 'rumble', { dur: 3 }], [1.2, 'thud'], [1.8, 'thud'], [(L) => Li(L, 1), 'shimmer']],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      api.sky(1080, 0.35); api.ground(860);
      const hop = Math.abs(Math.sin(lt * 4)) * 20;
      person(api.F, { kind: 'child', cloth: K.yellow, x: 760, y: 1060 - hop, s: 1.3, seed: 2400, expr: 'happy', walk: lt * 6 });
      person(api.F, { kind: 'child', cloth: K.sky, x: 1160, y: 1060, s: 1.25, seed: 2450, expr: 'happy', walk: lt * 6 + 1.5 });
      heart(api.TOP, { x: 960, y: 400, s: 1.4 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
    },
  },
};
export function titleArt(api, t) { trumpet(api, 800, 880, 1.6 * api.pr(t, 4.5, 5.3), 9900); trumpet(api, 1120, 880, 1.6 * api.pr(t, 4.8, 5.6), 9905, -1); }
