// Ep. 10 · Sansão, o Homem Mais Forte — uma página ilustrada por cena (motor storybook)
import { line, fill, dab, handCircle, ellipse, smooth } from './crayon.js';
import { part } from './rig.js';
import { person, lion, sun, moon, cloud, heart, house, baby } from './chars.js';
import { PAL } from './pal.js';
import { clamp, lerp, hash, ss, eo } from '/core/lib.js';
const K = PAL.crayon;
const SAND = '#e9c58a';
const Li = (L, i) => L[Math.min(i, L.length - 1)];
const SANSAO = { kind: 'woman', hair: K.brown, cloth: K.green, belt: K.brown, seed: 2500 };   // cabelo comprido (tipo "woman" = cabelo longo)
const SANSAO_CURTO = { kind: 'man', hair: K.brown, cloth: K.green, belt: K.brown, seed: 2500 };
const DALILA = { kind: 'woman', crown: false, scarf: K.red, cloth: K.pink, seed: 2760 };
const FILISTEU = (i) => ({ kind: 'man', helmet: true, beard: true, cloth: K.grey, seed: 2900 + i * 19 });
const STRONG = { armL: [[-34, -196], [-120, -230], [-170, -300]], armR: [[34, -196], [120, -230], [170, -300]] };

function gate(api, C, x, y, s, seed = 10000) { api.O(C, [[x - 160 * s, y], [x - 160 * s, y - 260 * s], [x + 160 * s, y - 260 * s], [x + 160 * s, y], [x - 160 * s, y]], K.brown, seed, { lw: 7 }); for (let i = 1; i < 4; i++) line(C.l, [[x - 160 * s + i * 80 * s, y], [x - 160 * s + i * 80 * s, y - 260 * s]], { w: 5, col: K.ink, seed: seed + 5 + i }); }
function pillar(api, x, top, bot, tilt, seed) { const dx = tilt * (bot - top); api.O(api.G, [[x - 60, bot], [x - 60 + dx, top], [x + 60 + dx, top], [x + 60, bot], [x - 60, bot]], K.peach, seed); }
function coins(api, x, y, n, seed) { for (let i = 0; i < n; i++) api.O(api.TOP, handCircle(x + (i % 3) * 46, y - Math.floor(i / 3) * 30, 20, seed + i, 0, 16), K.yellow, seed + 20 + i, { lw: 4 }); }
function ropes(api, x, y, s, seed) { for (let i = 0; i < 3; i++) line(api.TOP.l, [[x - 80 * s, y - (150 + i * 40) * s], [x + 80 * s, y - (170 + i * 40) * s]], { w: 8, col: K.brown, seed: seed + i }); }

export const SCENES = {
  gancho: {
    draw(api, lt, L, d) {
      api.sky(720, 0.45); sun(api.TOP, { x: 1700, y: 200, R: 80, face: 1, seed: 1100 }); api.ground(820, 1, SAND, 81);
      const lift = ss(api.pr(lt, 0.8, 2.5));
      person(api.F, { ...SANSAO, x: 960, y: 1080, s: 1.5, expr: 'happy', ...STRONG });
      gate(api, api.TOP, 960, 650 - 20 * lift, 1.2);
    },
    fx: [[0.8, 'rumble', { dur: 1.5 }], [2.5, 'shimmer']],
  },
  s1: {
    draw(api, lt, L) {
      api.sky(760, 0.4); api.ground(760);
      house(api.G, { x: 1600, y: 820, s: 1.1, seed: 1960 });
      person(api.F, { kind: 'man', beard: true, cloth: K.sky, x: 600, y: 1060, s: 1.25, seed: 2560, expr: 'wow' });
      person(api.F, { kind: 'woman', scarf: K.yellow, cloth: K.orange, x: 820, y: 1060, s: 1.2, seed: 2700, expr: 'wow' });
      person(api.TOP, { kind: 'man', wings: true, halo: true, cloth: K.white, x: 1200, y: 900, s: 1.0, seed: 2580, expr: 'happy' });
      if (lt > Li(L, 2)) baby(api.TOP, { x: 760, y: 1060 - 170 * 1.2, s: 1.3, seed: 2600 });
      if (lt > Li(L, 2)) api.text('SANSÃO', 720, 420, 100, { col: K.red, reveal: api.pr(lt, Li(L, 2), Li(L, 2) + 0.6) });
    },
    fx: [[0.3, 'glow', { dur: 2 }], [(L) => Li(L, 2), 'write', { dur: 0.6 }]],
  },
  s2: {
    draw(api, lt, L) {
      api.sky(760, 0.4); api.ground(760, 1, SAND, 82);
      const second = lt > Li(L, 1);
      person(api.F, { ...SANSAO, x: 760, y: 1060, s: 1.35, expr: 'happy', ...(second ? STRONG : { armR: [[34, -196], [120, -200], [170, -190]] }) });
      if (!second) lion(api.F, { x: 1250, y: 1060, s: 1.3, seed: 700, flip: true, expr: lt > 2 ? 'sleep' : undefined });
      else gate(api, api.TOP, 760, 660, 1.1);
      if (second) house(api.G, { x: 1500, y: 820, s: 1.0, seed: 1970 });
    },
    fx: [[0.6, 'growl'], [(L) => Li(L, 1), 'rumble', { dur: 1.5 }]],
  },
  s3: {
    draw(api, lt, L) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.pink, p: 0.2, gap: 14, w: 14, seed: 10100, boil: 0 });
      api.O(api.G, [[1300, 1080], [1300, 300], [1500, 300], [1500, 1080], [1300, 1080]], K.red, 10110);
      person(api.F, { ...DALILA, x: 700, y: 1060, s: 1.3, expr: 'smile', armR: [[34, -196], [80, -180], [120, -170]] });
      [0, 1].forEach(i => person(api.F, FILISTEU(i) && { ...FILISTEU(i), x: 1150 + i * 200, y: 1060, s: 1.1, expr: 'smile' }));
      coins(api, 860, 880, 6, 10120);
    },
    fx: [[1.0, 'shimmer']],
  },
  s4: {
    draw(api, lt, L, d) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.pink, p: 0.2, gap: 14, w: 14, seed: 10100, boil: 0 });
      const k = Math.min(2, Math.floor(lt / ((Li(L, 1) || d) / 3)));
      person(api.F, { ...SANSAO, x: 760, y: 1060, s: 1.35, expr: 'happy', ...(Math.floor(lt * 2) % 2 && lt < Li(L, 1) ? STRONG : {}) });
      if (lt < Li(L, 1)) ropes(api, 760, 1060, 1.35, 10200 + k * 10);
      person(api.F, { ...DALILA, x: 1250, y: 1060, s: 1.25, expr: lt > Li(L, 1) ? 'happy' : 'sad' });
      if (lt > Li(L, 1) + 1) heart(api.TOP, { x: 760, y: 440, s: 0.9, seed: 1300, col: K.yellow });
    },
    fx: [[1.0, 'thud'], [3.0, 'thud'], [5.0, 'thud']],
  },
  s5: {
    draw(api, lt, L) {
      const night = lt < Li(L, 1);
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: night ? '#2f3a78' : K.grey, p: night ? 0.85 : 0.35, gap: 12, w: 14, seed: 10300, boil: 0 });
      if (night) { moon(api.TOP, { x: 1700, y: 180, R: 80, seed: 1200 }); person(api.F, { ...SANSAO, x: 760, y: 1060, s: 1.3, expr: 'sleep', r: -0.15 }); api.text('Zzz', 900, 520, 70, { col: K.white }); }
      else { person(api.F, { ...SANSAO_CURTO, x: 760, y: 1060, s: 1.3, expr: 'sad' }); for (let i = 0; i < 2; i++) person(api.F, { ...FILISTEU(i), x: 1150 + i * 220, y: 1060, s: 1.1, expr: 'smile' }); }
      if (lt > Li(L, 2)) for (let x = 120; x <= 1800; x += 90) line(api.TOP.l, [[x, 120], [x, 1080]], { w: 14, col: K.grey, seed: 10400 + x });
    },
    fx: [[(L) => Li(L, 1), 'thud'], [(L) => Li(L, 2), 'thud']],
  },
  s6: {
    draw(api, lt, L, d) {
      fill(api.BG.f, [[-80, -80], [2000, -80], [2000, 1160], [-80, 1160]], { col: K.grey, p: 0.35, gap: 14, w: 14, seed: 10300, boil: 0 });
      const grow = api.pr(lt, 0.5, d * 0.6);
      const praying = lt > Li(L, 1);
      person(api.F, { ...(grow > 0.5 ? SANSAO : SANSAO_CURTO), x: 960, y: 1060, s: 1.4, expr: praying ? 'smile' : 'sad', ...(praying ? { armL: [[-34, -196], [-30, -260], [-6, -300]], armR: [[34, -196], [30, -260], [6, -300]] } : {}) });
      if (praying) for (let i = 0; i < 6; i++) line(api.TOP.l, [[980 + (i - 2.5) * 60, -20], [980 + (i - 2.5) * 30, 360]], { w: 6, col: K.yellow, seed: 10500 + i, draw: api.pr(lt, Li(L, 1) + i * 0.1, Li(L, 1) + 0.8 + i * 0.1) });
      for (let x = 120; x <= 1800; x += 90) line(api.TOP.l, [[x, 120], [x, 1080]], { w: 14, col: K.grey, seed: 10400 + x });
    },
    fx: [[(L) => Li(L, 1), 'glow', { dur: 2.5 }]],
  },
  s7: {
    extra: 1.0,
    draw(api, lt, L, d) {
      api.sky(1080, 0.35);
      const push = ss(api.pr(lt, Li(L, 1) - 0.5, Li(L, 1) + 2.0));
      pillar(api, 560, 220, 1080, -0.08 * push, 10600); pillar(api, 1360, 220, 1080, 0.08 * push, 10610);
      api.O(api.G, [[300 - 80 * push, 220 + 120 * push], [1620 + 80 * push, 220 + 120 * push], [1620 + 80 * push, 120 + 120 * push], [300 - 80 * push, 120 + 120 * push], [300 - 80 * push, 220 + 120 * push]], K.orange, 10620);
      person(api.F, { ...SANSAO, x: 960, y: 1080, s: 1.4, expr: 'happy', armL: [[-34, -196], [-200, -230], [-330, -250]], armR: [[34, -196], [200, -230], [330, -250]] });
      if (lt > Li(L, 2)) heart(api.TOP, { x: 960, y: 520, s: 1.3 * eo(api.pr(lt, Li(L, 2), Li(L, 2) + 0.6)), seed: 1300 });
    },
    fx: [[(L) => Li(L, 1), 'rumble', { dur: 3 }], [(L) => Li(L, 1) + 1.5, 'thud'], [(L) => Li(L, 2), 'shimmer']],
  },
  licao: {
    calm: true,
    draw(api, lt, L) {
      api.sky(1080, 0.35); api.ground(860);
      person(api.F, { kind: 'child', cloth: K.yellow, x: 960, y: 1060, s: 1.4, seed: 2400, expr: 'happy', ...STRONG });
      heart(api.TOP, { x: 960, y: 360, s: 1.4 * (1 + 0.05 * Math.sin(lt * 5)), seed: 1300 });
    },
  },
};
export function titleArt(api, t) { const g = api.pr(t, 4.5, 6.0); if (g > 0) gate(api, api.G, 960, 1000, 0.7 * g); }
