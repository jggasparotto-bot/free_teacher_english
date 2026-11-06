// Ep. 08 · A Travessia do Mar Vermelho — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, fish, sun, moon, cloud, heart, house } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const SAND = '#e9c58a';
const Li = (L, i) => L[Math.min(i, L.length - 1)];
const MOISES = { kind: 'man', beard: true, cloth: K.red, belt: K.yellow, seed: 2500 };
const ARAO = { kind: 'man', beard: true, beardCol: K.grey, cloth: K.sky, seed: 2560 };
const FARAO = { kind: 'man', crown: true, cloth: K.white, belt: K.sky, seed: 2580 };
const POVO = [['man', K.green], ['woman', K.orange, K.pink], ['child', K.yellow], ['man', K.sky], ['woman', K.green, K.yellow], ['child', K.pink]];

function staff(api, x0, y0, x1, y1, s = 7990) { line(api.TOP.l, [[x0, y0], [x1, y1]], { w: 12, col: K.brown, seed: s }); }
function people(api, lt, x0, y, dx, n, o = {}) { for (let i = 0; i < n; i++) { const [k, c, sc] = POVO[i % POVO.length]; person(api.F, { kind: k, cloth: c, scarf: sc, x: x0 + i * dx, y: y + (i % 2) * 10, s: k === 'child' ? 0.75 : 0.95, seed: 2800 + i * 31, expr: o.expr || 'happy', walk: o.walk ? lt * 6 + i : undefined, flip: o.flip }); } }
function waterWall(api, x0, x1, t, seed, fishOn = true) {
  const pts = []; for (let y = -60; y <= 1140; y += 40) pts.push([x1 + 26 * Math.sin(y / 60 + t * 2 + seed), y]);
  part(api.G, [[x0, -60], ...pts, [x0, 1140]], { col: K.teal, p: 0.85, gap: 11, w: 12, seed, cross: true, crossP: 0.45 }, null);
  line(api.G.l, pts, { w: 7, col: K.ink, seed: seed + 1 });
  if (fishOn) [[0.3, 300], [0.6, 620], [0.45, 880]].forEach(([u, y], i) => fish(api.TOP, { x: lerp(x0, x1, u) + 30 * Math.sin(t + i), y, s: 0.9, col: [K.orange, K.pink, K.yellow][i], seed: seed + 10 + i * 7, flip: x0 > x1, pose: Math.floor(t * 4) % 2 }));
}
function frog(api, x, y, s, seed) { api.O(api.TOP, ellipse(x, y, 40 * s, 28 * s, 20), K.green, seed, { lw: 5 }); [[-16, -24], [16, -24]].forEach(([dx, dy], i) => { api.O(api.TOP, handCircle(x + dx * s, y + dy * s, 11 * s, seed + 3 + i, 0, 14), K.white, seed + 5 + i, { lw: 4 }); dab(api.TOP.l, x + dx * s, y + dy * s, 4 * s, { col: K.ink, p: 1, seed: seed + 8 + i }); }); }
function door(api, x, y, marked, seed) { api.O(api.G, [[x - 70, y], [x - 70, y - 210], [x + 70, y - 210], [x + 70, y], [x - 70, y]], K.brown, seed); if (marked) line(api.TOP.l, [[x - 80, y - 225], [x + 80, y - 225]], { w: 14, col: K.red, seed: seed + 5 }); }
function cloudPillar(api, x, night, seed = 8100) {
  if (night) { const pts = []; for (let y = 160; y <= 760; y += 30) pts.push([x - 50 - 15 * Math.sin(y / 40), y]); for (let y = 760; y >= 160; y -= 30) pts.push([x + 50 + 15 * Math.sin(y / 50), y]); part(api.TOP, pts, { col: K.orange, p: 1, gap: 7, w: 9, seed }, { w: 6, col: K.red, seed: seed + 1 }); }
  else for (let i = 0; i < 6; i++) cloud(api.TOP, { x: x - 60 + (i % 2) * 40, y: 180 + i * 100, s: 0.55, seed: seed + i * 7 });
}
function tambourine(api, x, y, seed) { api.O(api.TOP, handCircle(x, y, 40, seed, 0, 24), K.yellow, seed + 1, { lw: 6 }); for (let i = 0; i < 6; i++) { const a = i / 6 * 6.28; dab(api.TOP.l, x + Math.cos(a) * 40, y + Math.sin(a) * 40, 7, { col: K.grey, p: 1, seed: seed + 3 + i }); } }

export const SCENES = {
  gancho: {
    draw(api, lt, L, d) {
      api.sky(560, 0.4);
      const open = ss(api.pr(lt, 0.3, d * 0.8));
      waterWall(api, -80, lerp(960, 560, open), lt, 8200); waterWall(api, 2000, lerp(960, 1360, open), lt, 8210);
      fill(api.BG.f, [[500, 560], [1420, 560], [1420, 1160], [500, 1160]], { col: SAND, p: 0.6, gap: 12, w: 13, seed: 8220, boil: 0 });
    },
    fx: [[0.3, 'whoosh', { dur: 2.0 }]],
  },
  s1: {
    draw(api, lt, L) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.yellow, p: 0.25, gap: 14, w: 14, seed: 7900, boil: 0 });
      [[180], [1740]].forEach(([x], i) => api.O(api.G, [[x - 50, 1080], [x - 50, 160], [x + 50, 160], [x + 50, 1080], [x - 50, 1080]], K.orange, 7910 + i * 3));
      person(api.F, { ...MOISES, x: 600, y: 1060, s: 1.3, expr: 'smile', armR: [[34, -196], [80, -220], [120, -240]] });
      person(api.F, { ...ARAO, x: 400, y: 1060, s: 1.2, expr: 'smile' });
      person(api.F, { ...FARAO, x: 1350, y: 1060, s: 1.4, expr: lt > Li(L, 1) ? 'sad' : 'smile', armL: lt > Li(L, 1) ? [[-34, -196], [-90, -230], [-140, -250]] : undefined });
      if (lt > Li(L, 1)) api.text('NÃO!', 1350, 380, 140, { col: K.red, reveal: api.pr(lt, Li(L, 1), Li(L, 1) + 0.4) });
    },
    fx: [[(L) => Li(L, 1), 'thud']],
  },
  s2: {
    draw(api, lt, L, d) {
      const u = lt / d;
      api.sky(640, 0.4); api.ground(640, 1, SAND, 82);
      api.sea(820, 1, lt, 2, u < 0.25 ? K.red : K.sky);
      if (u > 0.2) for (let i = 0; i < 8; i++) frog(api, 200 + i * 220, 700 - Math.abs(Math.sin(lt * 4 + i)) * 60, 1.1, 8300 + i * 13);
      if (u > 0.45) for (let i = 0; i < 40; i++) dab(api.FX, hash(i) * 1920, ((hash(i + 3) * 600 + lt * 300) % 640), 4, { col: K.ink, p: 1, seed: 8400 + i });
      if (u > 0.6) for (let i = 0; i < 30; i++) api.O(api.TOP, handCircle(hash(i + 9) * 1920, ((hash(i + 5) * 640 + lt * 500) % 700), 10, 8500 + i, 0, 10), K.white, 8540 + i, { lw: 4 });
      if (u > 0.78) fill(api.FX, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: '#2f3a78', p: 0.45 * clamp((u - 0.78) / 0.1), gap: 14, w: 14, seed: 8580, boil: 0 });
      person(api.F, { ...FARAO, x: 1650, y: 1060, s: 1.2, expr: 'sad' });
    },
    fx: [[2.0, 'squeak'], [3.0, 'squeak'], [6.0, 'rain', { dur: 3 }], [8.0, 'rumble']],
  },
  s3: {
    draw(api, lt, L) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: '#2f3a78', p: 0.9, gap: 10, w: 13, seed: 5500, boil: 0 }); moon(api.TOP, { x: 1700, y: 160, R: 80, seed: 1200 });
      api.ground(880, 1, SAND, 83);
      [[420, 0], [960, 1], [1500, 2]].forEach(([x, i]) => { api.O(api.G, [[x - 220, 880], [x - 220, 560], [x + 220, 560], [x + 220, 880], [x - 220, 880]], K.peach, 8600 + i * 7); door(api, x, 880, api.pr(lt, 0.5 + i * 0.4, 1.0 + i * 0.4) > 0, 8620 + i * 9); });
      if (lt > Li(L, 1)) for (let i = 0; i < 9; i++) line(api.TOP.l, [[960 + (i - 4) * 200, -40], [960 + (i - 4) * 120, 500]], { w: 6, col: K.yellow, seed: 8650 + i, draw: api.pr(lt, Li(L, 1) + i * 0.1, Li(L, 1) + 0.8 + i * 0.1) });
      if (lt > Li(L, 2)) people(api, lt, 200, 1060, 300, 6, { walk: true });
    },
    fx: [[0.5, 'scratch', { dur: 1.5 }], [(L) => Li(L, 1), 'glow', { dur: 2 }]],
  },
  s4: {
    draw(api, lt, L, d) {
      const night = lt > Li(L, 1) + 2.5;
      if (night) { fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: '#2f3a78', p: 0.9, gap: 10, w: 13, seed: 5500, boil: 0 }); } else api.sky(700, 0.4);
      api.ground(800, 1, SAND, 84);
      cloudPillar(api, 1650, night);
      const off = lt * 50;
      people(api, lt, 200 + off - 600, 1060, 260, 7, { walk: true });
      person(api.TOP, { ...MOISES, x: 1250 + off * 0.2, y: 1060, s: 1.2, expr: 'happy', walk: lt * 6 });
      if (!night) api.text('♪', 600, 520, 100, { col: K.red });
    },
    fx: [[0.5, 'crowd', { dur: 4 }], [(L) => Li(L, 1) + 2.5, 'fire']],
  },
  s5: {
    draw(api, lt, L) {
      api.sky(600, 0.45); api.sea(600, 1, lt, 3);
      fill(api.BG.f, [[-80, 860], [2000, 860], [2000, 1160], [-80, 1160]], { col: SAND, p: 0.6, gap: 12, w: 13, seed: 8700, boil: 0 });
      people(api, lt, 900, 1060, 170, 6, { expr: lt > Li(L, 2) ? 'wow' : 'sad' });
      if (lt > Li(L, 1) * 0.6) for (let i = 0; i < 5; i++) person(api.F, { kind: 'man', helmet: true, cloth: K.grey, x: 80 + i * 110, y: 1060, s: 0.7, seed: 2900 + i * 17, expr: 'sad' });
      if (lt > Li(L, 3)) api.text('E agora?', 1300, 520, 110, { col: K.red, reveal: api.pr(lt, Li(L, 3), Li(L, 3) + 0.5) });
    },
    fx: [[1.0, 'rumble', { dur: 2.5 }], [(L) => Li(L, 3), 'crowd', { dur: 2 }]],
  },
  s6: {
    draw(api, lt, L, d) {
      api.sky(1080, 0.45);
      const open = ss(api.pr(lt, Li(L, 2), Li(L, 2) + 3.0));
      waterWall(api, -80, lerp(980, 640, open), lt, 8200, open > 0.3); waterWall(api, 2000, lerp(940, 1280, open), lt, 8210, open > 0.3);
      if (open > 0) fill(api.BG.f, [[lerp(980, 600, open), 300], [lerp(940, 1320, open), 300], [lerp(940, 1320, open), 1160], [lerp(980, 600, open), 1160]], { col: SAND, p: 0.6, gap: 12, w: 13, seed: 8220, boil: 0 });
      const up = lt > Li(L, 2) - 0.5;
      person(api.TOP, { ...MOISES, x: 960, y: 1080, s: 1.45, expr: 'wow', armR: up ? [[34, -196], [70, -250], [96, -310]] : undefined });
      if (up) staff(api, 960 + 96 * 1.45, 1080 - 310 * 1.45 - 160, 960 + 96 * 1.45, 1080 - 310 * 1.45 + 260);
      if (lt > Li(L, 1)) for (let i = 0; i < 6; i++) line(api.FX, [[(lt * 900 + i * 400) % 2400 - 300, 200 + i * 120], [(lt * 900 + i * 400) % 2400 - 100, 200 + i * 120]], { w: 5, col: K.white, p: 0.8, seed: 8800 + i });
    },
    fx: [[(L) => Li(L, 1), 'whoosh', { dur: 2 }], [(L) => Li(L, 2), 'rumble', { dur: 3 }], [(L) => Li(L, 2) + 1.5, 'shimmer']],
  },
  s7: {
    draw(api, lt, L, d) {
      api.sky(1080, 0.45);
      waterWall(api, -80, 560, lt, 8200); waterWall(api, 2000, 1360, lt, 8210);
      fill(api.BG.f, [[540, -80], [1380, -80], [1380, 1160], [540, 1160]], { col: SAND, p: 0.6, gap: 12, w: 13, seed: 8220, boil: 0 });
      const ROW = [[3, 1130, 800, 0.62], [4, 830, 790, 0.6], [0, 780, 1080, 0.95], [2, 1000, 1070, 0.78], [1, 1180, 1085, 0.92]];   // fundo primeiro, frente por último
      ROW.forEach(([i, x, y, s]) => { const [k, c, sc] = POVO[i]; person(api.F, { kind: k, cloth: c, scarf: sc, x, y: y + 6 * Math.sin(lt * 3 + i), s, seed: 2800 + i * 31, expr: k === 'child' ? 'wow' : 'happy', walk: lt * 6 + i }); });
    },
    fx: [[1.0, 'splash', { small: 1 }], [(L) => Li(L, 1), 'glint']],
  },
  s8: {
    draw(api, lt, L, d) {
      api.sky(600, 0.45);
      const close = ss(api.pr(lt, 0.4, 3.0));
      api.sea(lerp(1100, 600, close), 1, lt, 5);
      fill(api.BG.f, [[1300, 820], [2000, 820], [2000, 1160], [1300, 1160]], { col: SAND, p: 0.6, gap: 12, w: 13, seed: 8900, boil: 0 });
      people(api, lt, 1350, 1060, 110, 5, { expr: 'happy' });
      if (lt > Li(L, 2)) api.text('LIVRES!', 1600, 400, 120, { col: K.red, reveal: api.pr(lt, Li(L, 2), Li(L, 2) + 0.5) });
    },
    fx: [[0.4, 'whoosh', { dur: 2.5 }], [(L) => Li(L, 2), 'shimmer']],
  },
  s9: {
    draw(api, lt, L) {
      api.sky(700, 0.4); api.sea(700, 1, lt, 6); fill(api.BG.f, [[-80, 860], [2000, 860], [2000, 1160], [-80, 1160]], { col: SAND, p: 0.6, gap: 12, w: 13, seed: 8950, boil: 0 });
      sun(api.TOP, { x: 1700, y: 200, R: 80, face: 1, seed: 1100 });
      const hop = Math.abs(Math.sin(lt * 5)) * 30;
      person(api.F, { kind: 'woman', scarf: K.sky, cloth: K.pink, x: 900, y: 1060 - hop, s: 1.35, seed: 2760, expr: 'sing', armR: [[34, -196], [80, -250], [110, -310]] });
      tambourine(api, 900 + 110 * 1.35, 1060 - hop - 330 * 1.35, 9000);
      people(api, lt, 300, 1060, 230, 2); people(api, lt, 1280, 1060, 230, 3);
      for (let i = 0; i < 4; i++) api.text('♪', 300 + i * 450, 300 + 40 * Math.sin(lt * 3 + i), 90, { col: K.ink });
    },
    fx: [[0.5, 'shimmer'], [2.0, 'hammer'], [2.4, 'hammer'], [2.8, 'hammer']],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      api.sky(1080, 0.35); api.ground(860);
      person(api.F, { kind: 'child', cloth: K.yellow, x: 960, y: 1060, s: 1.4, seed: 2400, expr: 'happy', armR: [[34, -196], [80, -230], [100, -290]] });
      heart(api.TOP, { x: 960, y: 380, s: 1.4 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
    },
  },
};
export function titleArt(api, t) { const g = api.pr(t, 4.5, 6.0); if (g > 0) [[700, 'L'], [1220, 'R']].forEach(([x], i) => fish(api.TOP, { x, y: 880, s: 1.1 * g, col: [K.orange, K.pink][i], seed: 9100 + i * 7, flip: i === 1 })); }
