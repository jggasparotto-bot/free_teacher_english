// Personagens desenhados em giz: Adão, Eva, a criança ("você"), ovelha, coelho, leão, elefante, peixe, passarinho, sol, lua, coração.
// Todos paramétricos: posição (pés), escala, expressão, e "draw" (0–1) para o traço ir aparecendo ao vivo.
import { line, fill, dab, ellipse, handCircle, xf, smooth } from './crayon.js';
import { part, tube, curve } from './rig.js';
import { PAL } from './pal.js';
import { clamp, lerp } from '/core/lib.js';
const K = PAL.crayon;
const LW = 7;

function T0(o) { const k = o.flip ? -1 : 1; return pts => xf(pts, { x: o.x || 0, y: o.y || 0, s: o.s || 1, r: o.r || 0, sx: k }); }
const lo = (seed, o, extra = {}) => ({ w: LW, seed, col: K.ink, draw: o.draw ?? 1, ...extra });
const fo = (col, seed, o, extra = {}) => ({ col, p: 0.8, gap: 9, w: 11, seed, draw: o.fill ?? 1, ...extra });

// ——— rosto (origem = centro do rosto) ———
function face(C, P, o, sd, skin) {
  const ex = o.expr || 'smile';
  const eyes = [[-22, 2], [22, 2]];
  eyes.forEach(([x, y], i) => {
    if (ex === 'sleep' || ex === 'happy') {
      const up = ex === 'happy' ? -1 : 1;
      line(C.l, P([[x - 10, y], [x - 4, y + 6 * up], [x + 4, y + 6 * up], [x + 10, y]]), lo(sd + i, o, { w: 5, taper: 0.3 }));
      return;
    }
    part(C, P(ellipse(x, y, 6.5, 8.5, 16)), { col: K.ink, p: 1, gap: 3, w: 5, over: 0.5, seed: sd + 2 + i, draw: o.fill ?? 1 }, lo(sd + 4 + i, o, { w: 4 }), { occ: false });
    dab(C.l, ...P([[x + 2.5, y - 3.5]])[0], 2.4 * (o.s || 1), { col: K.white, p: o.fill ?? 1, seed: sd + 6 + i, gap: 2, w: 3 });
  });
  [[-38, 22], [38, 22]].forEach(([x, y], i) => dab(C.f, ...P([[x, y]])[0], 10 * (o.s || 1), { col: K.pink, p: 0.8 * (o.blush ?? 1) * (o.fill ?? 1), seed: sd + 8 + i, sq: 0.75 }));
  if (ex === 'sing' || ex === 'wow') part(C, P(ellipse(0, 30, 8, 10, 18)), { col: K.red, p: 0.85, gap: 3, w: 4, over: 0.5, seed: sd + 10, draw: o.fill ?? 1 }, lo(sd + 11, o, { w: 4.5 }), { occ: false });
  else if (ex === 'sleep') line(C.l, P([[-7, 28], [0, 32], [7, 28]]), lo(sd + 12, o, { w: 4.5 }));
  else if (ex === 'sad') { line(C.l, P([[-12, 34], [-5, 27], [5, 27], [12, 34]]), lo(sd + 12, o, { w: 4.5 })); [[-22, 2], [22, 2]].forEach(([x], i) => line(C.l, P([[x - 11, -16 + (i ? 4 : -4) * -1], [x + 11, -16 - (i ? 4 : -4) * -1]]), lo(sd + 15 + i, o, { w: 4 }))); }
  else part(C, P([[-13, 24], [-6, 34], [6, 34], [13, 24]]), { col: K.red, p: 0.8, gap: 3, w: 4, over: 0.5, seed: sd + 13, draw: o.fill ?? 1 }, lo(sd + 14, o, { w: 4.5 }), { occ: false });
}

// ——— pessoa (origem = entre os pés, altura ≈ 330) ———
// o.kind: 'adam' | 'eve' | 'child'; o.armL / o.armR: pontos [ombro, cotovelo, mão] locais; o.expr; o.draw (traço), o.fill (cor)
export function person(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 2000, kind = o.kind || 'adam';
  const skinCol = o.skin || (kind === 'adam' ? K.brown : K.peach);
  const skinF = fo(skinCol, sd + 1, o, { p: kind === 'adam' ? 0.42 : 0.6, gap: 10, w: 12, ang: 0.6, over: 3 });
  const clothCol = o.cloth || (kind === 'child' ? K.yellow : K.green);
  const robe = o.robe || kind === 'man' || kind === 'woman';
  const clothF = fo(clothCol, sd + 2, o, { p: 0.82, gap: 10, w: 12, ang: kind === 'eve' ? -0.4 : 0.35, cross: kind !== 'child', crossP: 0.4 });
  const hairCol = o.hair || (kind === 'eve' ? K.orange : kind === 'adam' ? K.ink : K.brown);
  const hairF = fo(hairCol, sd + 3, o, { p: 0.9, gap: 7, w: 9, ang: 1.2, over: 2 });
  const limb = (pts, w, f, s) => part(C, P(tube(curve(pts, 5), w)), f, lo(s, o));
  const hand = (c, s) => part(C, P(handCircle(c[0], c[1], 11, s, 0, 18)), skinF, lo(s, o, { w: 5.5 }));
  // cabelo comprido atrás (Eva)
  if (kind === 'eve' || kind === 'woman') part(C, P(smooth([[-70, -300], [-84, -230], [-80, -160], [-50, -150], [0, -170], [50, -150], [80, -160], [84, -230], [70, -300], [0, -330]], 6)), hairF, lo(sd + 4, o));
  // pernas e pés
  const wk = o.walk === undefined ? 0 : Math.sin(o.walk);
  [[[-17, -96], [-18 + 10 * wk, -52], [-20 + 22 * wk, -14 - 8 * Math.max(0, wk)]], [[17, -96], [18 - 10 * wk, -52], [20 - 22 * wk, -14 - 8 * Math.max(0, -wk)]]].forEach((lg, i) => {
    limb(lg, 20, skinF, sd + 10 + i * 3);
    part(C, P(ellipse(lg[2][0] + (i ? 8 : -8), -6, 18, 9, 18)), skinF, lo(sd + 11 + i * 3, o));
  });
  // braços (atrás da roupa quando pendem)
  const aL = o.armL || [[-34, -196], [-56, -150], [-62, -112]];
  const aR = o.armR || [[34, -196], [56, -150], [62, -112]];
  // roupa de folhas (Adão e Eva) / camiseta (criança)
  if (o.wings) [-1, 1].forEach(sg => part(C, P(smooth([[sg * 30, -190], [sg * 120, -260], [sg * 150, -200], [sg * 120, -120], [sg * 40, -130]], 5)), fo(K.white, sd + 90 + sg, o, { p: 1, gap: 7, w: 9 }), lo(sd + 92 + sg, o)));
  const hemY = robe ? -12 : kind === 'child' ? -92 : -84;
  const body = robe ? smooth([[-30, -206], [30, -206], [50, -182], [72, hemY], [-72, hemY], [-50, -182]], 3) : smooth([[-30, -206], [30, -206], [48, -182], [66, hemY], [-66, hemY], [-48, -182]], 3);
  part(C, P(body), clothF, lo(sd + 20, o));
  if (o.fur) {   // roupas quentinhas: pele marrom riscada por cima das folhas
    fill(C.f, P(body), { col: K.brown, p: 0.95 * o.fur, gap: 7, w: 10, ang: -0.6, seed: sd + 25, draw: o.fur, cross: true, crossP: 0.6 });
    if (o.fur >= 1) [[-30, -170], [10, -140], [-14, -110], [30, -116]].forEach(([x, y], i) => line(C.l, P(curve([[x - 8, y], [x, y - 6], [x + 8, y]])), lo(sd + 26 + i, o, { w: 3.5, col: K.ink, p: 0.6 })));
  }
  if (robe) {   // faixa na cintura e listras (José: túnica colorida)
    line(C.l, P([[-56, -120], [56, -120]]), lo(sd + 55, o, { w: 6, col: o.belt || K.brown }));
    if (o.stripes) o.stripes.forEach((c, i) => { const y = -190 + i * 26; if (y > -30) return; const hw = 34 + (y + 206) * 0.2; fill(C.f, P([[-hw, y], [hw, y], [hw + 4, y + 22], [-hw - 4, y + 22]]), { col: c, p: 1, gap: 5, w: 7, seed: sd + 56 + i, draw: o.fill ?? 1 }); line(C.l, P([[-hw, y], [hw, y]]), lo(sd + 70 + i, o, { w: 3.5 })); });
  }
  if (kind !== 'child' && !robe && !(o.fur >= 1)) {   // barra de folhas
    for (let i = 0; i < 6; i++) {
      const x0 = -66 + i * 22;
      const leaf = smooth([[x0, hemY - 2], [x0 + 11, hemY + 24], [x0 + 22, hemY - 2], [x0 + 11, hemY + 6]], 4);
      part(C, P(leaf), fo(K.green, sd + 30 + i, o, { p: 0.95, gap: 5, w: 7, ang: 1.2 }), lo(sd + 40 + i, o, { w: 4.5 }));
    }
    if (kind === 'eve') [[-20, -160], [18, -130], [-8, -110]].forEach(([x, y], i) => dab(C.f, ...P([[x, y]])[0], 7 * (o.s || 1), { col: K.pink, p: o.fill ?? 1, seed: sd + 50 + i }));
  } else {
    line(C.l, P([[-40, -150], [40, -150]]), lo(sd + 52, o, { w: 5, col: K.orange, p: 0.9 }));   // listra da camiseta
  }
  [aL, aR].forEach((a, i) => { limb(a, 16, skinF, sd + 60 + i * 4); hand(a[a.length - 1], sd + 62 + i * 4); });
  // cabeça
  const hc = [0, -262];
  const Ph = pts => P(pts.map(([x, y]) => [x + hc[0], y + hc[1]]));
  part(C, Ph(ellipse(0, 0, 64, 60, 44)), skinF, lo(sd + 70, o));
  if (kind === 'adam' || kind === 'man') {
    const cur = []; for (let i = 0; i <= 60; i++) { const a = Math.PI + i / 60 * Math.PI; const r = 68 + 9 * Math.abs(Math.sin(i / 60 * Math.PI * 6)); cur.push([Math.cos(a) * r, Math.sin(a) * r * 0.82 - 8]); }
    cur.push([60, -20], [30, -30], [0, -36], [-30, -30], [-60, -20]);
    part(C, Ph(cur), hairF, lo(sd + 72, o, { w: 6.5 }));
  } else if (kind === 'eve' || kind === 'woman') {
    part(C, Ph(smooth([[-66, -4], [-62, -38], [-36, -62], [0, -70], [36, -62], [62, -38], [66, -4], [44, -30], [10, -40], [-24, -34], [-50, -18]], 4)), hairF, lo(sd + 72, o, { w: 6.5 }));
    if (kind === 'eve') // flor no cabelo
    for (let k = 0; k < 5; k++) { const a = k / 5 * 6.28; dab(C.f, ...Ph([[44 + Math.cos(a) * 11, -46 + Math.sin(a) * 11]])[0], 8 * (o.s || 1), { col: K.pink, p: o.fill ?? 1, seed: sd + 74 + k }); }
    dab(C.f, ...Ph([[44, -46]])[0], 6 * (o.s || 1), { col: K.yellow, p: o.fill ?? 1, seed: sd + 79 });
  } else {
    part(C, Ph(smooth([[-64, -10], [-58, -40], [-30, -62], [0, -66], [34, -60], [60, -38], [64, -10], [40, -36], [0, -44], [-40, -34]], 4)), hairF, lo(sd + 72, o, { w: 6.5 }));
    line(C.l, Ph(curve([[-4, -64], [2, -88], [18, -92], [16, -78]])), lo(sd + 73, o, { w: 6, col: K.brown, p: 0.95 }));
  }
  face(C, Ph, o, sd + 80, skinCol);
  if (o.beard) part(C, Ph(smooth([[-54, 6], [-46, 52], [-20, 84], [0, 90], [20, 84], [46, 52], [54, 6], [36, 40], [14, 44], [0, 40], [-14, 44], [-36, 40]], 4)), fo(o.beardCol || K.brown, sd + 120, o, { p: 0.9, gap: 6, w: 8 }), lo(sd + 121, o, { w: 6 }));
  if (o.beard) line(C.l, Ph([[-12, 30], [0, 34], [12, 30]]), lo(sd + 122, o, { w: 4.5 }));
  if (o.scarf) part(C, Ph(smooth([[-78, 40], [-76, -30], [-50, -72], [0, -84], [50, -72], [76, -30], [78, 40], [60, 10], [56, -30], [30, -50], [0, -56], [-30, -50], [-56, -30], [-60, 10]], 4)), fo(o.scarf, sd + 124, o, { p: 0.85, gap: 7, w: 9 }), lo(sd + 125, o, { w: 6 }));
  if (o.crown) part(C, Ph([[-50, -50], [-56, -112], [-30, -80], [0, -122], [30, -80], [56, -112], [50, -50], [-50, -50]]), fo(K.yellow, sd + 126, o, { p: 1, gap: 6, w: 8 }), lo(sd + 127, o, { w: 6, col: K.orange }));
  if (o.helmet) part(C, Ph(smooth([[-70, -10], [-64, -60], [-30, -90], [0, -96], [30, -90], [64, -60], [70, -10], [40, -24], [0, -30], [-40, -24]], 4)), fo(K.grey, sd + 128, o, { p: 0.9, gap: 7, w: 9 }), lo(sd + 129, o, { w: 6 }));
  if (o.halo) line(C.l, Ph(ellipse(0, -96, 50, 14, 30)), lo(sd + 130, o, { w: 6, col: K.yellow }));
}

// ——— ovelha (origem = pés) ———
export function sheep(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 500, s = o.s || 1;
  [[-26, 0], [-10, 4], [12, 4], [28, 0]].forEach(([x, y], i) => part(C, P(tube([[x, y - 30], [x, y]], 12)), fo(K.ink, sd + i, o, { p: 0.85, gap: 4, w: 6 }), lo(sd + 10 + i, o, { w: 4.5 })));
  const body = []; const n = 11;
  for (let i = 0; i <= n * 6; i++) { const a = i / (n * 6) * Math.PI * 2; const b = Math.abs(Math.sin(a * n / 2)); body.push([Math.cos(a) * (50 + 7 * b), -46 + Math.sin(a) * (34 + 6 * b)]); }
  part(C, P(body), fo(K.white, sd + 20, o, { p: 0.95, gap: 6, w: 8, over: 2 }), lo(sd + 21, o, { w: 6 }));
  [[-14, -50], [12, -40], [-2, -34], [20, -58]].forEach(([x, y], i) => line(C.l, P(ellipse(x, y, 7, 6, 10, 0.4, 5.6)), lo(sd + 30 + i, o, { w: 3.5, p: 0.55 })));
  const hx = 50, hy = -62;
  part(C, P(ellipse(hx - 14, hy - 8, 8, 14, 12, 0, 6.3, 0.9)), fo(K.ink, sd + 40, o, { p: 0.85, gap: 3, w: 5 }), lo(sd + 41, o, { w: 4 }));
  part(C, P(ellipse(hx, hy, 21, 18, 20)), fo(K.ink, sd + 42, o, { p: 0.6, gap: 4, w: 6 }), lo(sd + 43, o, { w: 5 }));
  if (o.expr === 'sleep') line(C.l, P([[hx + 2, hy - 2], [hx + 7, hy + 2], [hx + 12, hy - 2]]), lo(sd + 46, o, { w: 3.5, col: K.white, p: 1 }));
  else dab(C.l, ...P([[hx + 7, hy - 3]])[0], 3.4 * s, { col: K.white, p: o.fill ?? 1, seed: sd + 46, gap: 2, w: 3 });
}

// ——— coelho ———
export function rabbit(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 600, s = o.s || 1;
  const furF = fo(K.peach, sd + 1, o, { p: 0.7, gap: 8, w: 10, ang: 0.4 });
  part(C, P(handCircle(-48, -44, 14, sd + 2, 0, 18)), fo(K.white, sd + 3, o, { p: 1, gap: 4, w: 6 }), lo(sd + 4, o, { w: 5 }));
  part(C, P(ellipse(-6, -42, 46, 38, 30)), furF, lo(sd + 5, o));
  [[-12, -150, -0.12], [16, -146, 0.18]].forEach(([x, y, r], i) => {
    part(C, P(ellipse(x, y, 13, 46, 24, 0, 6.3, r)), furF, lo(sd + 6 + i, o));
    dab(C.f, ...P([[x, y + 4]])[0], 6 * s, { col: K.pink, p: 0.8 * (o.fill ?? 1), seed: sd + 8 + i, sq: 2.6 });
  });
  part(C, P(handCircle(24, -88, 34, sd + 10, 0, 30)), furF, lo(sd + 11, o));
  if (o.expr === 'sleep') line(C.l, P([[26, -92], [32, -88], [38, -92]]), lo(sd + 12, o, { w: 4 }));
  else { dab(C.l, ...P([[34, -94]])[0], 4.5 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 12 }); dab(C.l, ...P([[35.5, -96]])[0], 1.6 * s, { col: K.white, p: o.fill ?? 1, seed: sd + 13 }); }
  dab(C.l, ...P([[56, -82]])[0], 5 * s, { col: K.pink, p: o.fill ?? 1, seed: sd + 14 });
  [[-20, -6], [14, -4]].forEach(([x, y], i) => part(C, P(ellipse(x, y, 16, 8, 14)), furF, lo(sd + 15 + i, o, { w: 5 })));
}

// ——— leão ———
export function lion(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 700, s = o.s || 1;
  const bodyF = fo(K.yellow, sd + 1, o, { p: 0.85, gap: 9, w: 11, ang: 0.4, cross: true, crossP: 0.4 });
  line(C.l, P(curve([[-90, -90], [-130, -110], [-136, -150]])), lo(sd + 2, o, { w: 6 }));
  part(C, P(handCircle(-138, -156, 14, sd + 3, 0, 18)), fo(K.brown, sd + 4, o, { p: 0.9, gap: 4, w: 6 }), lo(sd + 5, o, { w: 5 }));
  [[-70, 0], [-40, 0], [36, 0], [64, 0]].forEach(([x], i) => part(C, P(tube([[x, -60], [x, -6]], 22)), bodyF, lo(sd + 10 + i, o)));
  part(C, P(ellipse(-8, -86, 96, 50, 36)), bodyF, lo(sd + 20, o));
  // juba
  const mane = []; for (let i = 0; i <= 80; i++) { const a = i / 80 * Math.PI * 2; const r = 84 + 12 * Math.abs(Math.sin(a * 6)); mane.push([70 + Math.cos(a) * r, -142 + Math.sin(a) * r]); }
  part(C, P(mane), fo(K.orange, sd + 21, o, { p: 0.9, gap: 8, w: 10, ang: 1.0, cross: true, crossP: 0.5 }), lo(sd + 22, o));
  part(C, P(handCircle(70, -142, 52, sd + 23, 0, 36)), fo(K.yellow, sd + 24, o, { p: 0.9, gap: 7, w: 9 }), lo(sd + 25, o));
  if (o.expr === 'sleep') [[52, -150], [88, -150]].forEach(([x, y], i) => line(C.l, P([[x - 8, y], [x, y + 5], [x + 8, y]]), lo(sd + 26 + i, o, { w: 4.5 })));
  else [[52, -152], [88, -152]].forEach(([x, y], i) => { dab(C.l, ...P([[x, y]])[0], 6 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 26 + i }); dab(C.l, ...P([[x + 2, y - 2]])[0], 2 * s, { col: K.white, p: o.fill ?? 1, seed: sd + 28 + i }); });
  part(C, P([[62, -132], [78, -132], [70, -120]]), fo(K.brown, sd + 30, o, { p: 1, gap: 3, w: 5 }), null, { occ: false });
  line(C.l, P([[56, -112], [70, -104], [84, -112]]), lo(sd + 31, o, { w: 4.5 }));
}

// ——— elefante ———
export function elephant(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 800, s = o.s || 1;
  const gF = fo(K.grey, sd + 1, o, { p: 0.85, gap: 10, w: 12, ang: 0.5, cross: true, crossP: 0.45 });
  line(C.l, P(curve([[-120, -120], [-140, -100], [-138, -70]])), lo(sd + 2, o, { w: 6 }));
  [[-90, 0], [-50, 0], [40, 0], [78, 0]].forEach(([x], i) => part(C, P(tube([[x, -80], [x, -10]], 36)), gF, lo(sd + 10 + i, o)));
  part(C, P(ellipse(-20, -128, 116, 78, 40)), gF, lo(sd + 20, o));
  // tromba
  const trunk = tube(curve([[120, -150], [150, -110], [160, -60], [150, -30], [134, -28]], 6), 34, 18);
  part(C, P(trunk), gF, lo(sd + 21, o));
  part(C, P(handCircle(100, -170, 60, sd + 22, 0, 36)), gF, lo(sd + 23, o));
  part(C, P(ellipse(52, -168, 44, 56, 30)), gF, lo(sd + 24, o));
  dab(C.f, ...P([[52, -168]])[0], 26 * s, { col: K.pink, p: 0.7 * (o.fill ?? 1), seed: sd + 25, sq: 1.3 });
  part(C, P(smooth([[128, -138], [150, -132], [158, -118], [140, -124]], 4)), fo(K.white, sd + 28, o, { p: 1, gap: 3, w: 5 }), lo(sd + 29, o, { w: 4 }));
  if (o.expr === 'sleep') line(C.l, P([[118, -192], [127, -185], [136, -192]]), lo(sd + 26, o, { w: 5 }));
  else { part(C, P(ellipse(127, -190, 8, 10, 14)), fo(K.ink, sd + 26, o, { p: 1, gap: 3, w: 5, over: 0.5 }), null, { occ: false, kn: false }); dab(C.l, ...P([[129, -194]])[0], 2.6 * s, { col: K.white, p: o.fill ?? 1, seed: sd + 27 }); }
}

// ——— peixe (origem = centro; olha para a direita) ———
export function fish(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 900, col = o.col || K.orange, s = o.s || 1;
  const F = fo(col, sd + 1, o, { p: 0.9, gap: 7, w: 9, ang: 1.2 });
  const tw = o.pose ? 14 : -14;   // duas poses de cauda (substituição)
  part(C, P([[-50, 0], [-90, -34 + tw], [-84, 0], [-90, 34 + tw]]), F, lo(sd + 2, o));
  part(C, P(ellipse(0, 0, 58, 34, 32)), F, lo(sd + 3, o));
  line(C.l, P([[-8, -30], [-14, 0], [-8, 30]]), lo(sd + 4, o, { w: 4.5 }));
  [[14, -4]].forEach(([x, y]) => { part(C, P(handCircle(x + 14, y - 6, 9, sd + 5, 0, 14)), fo(K.white, sd + 6, o, { p: 1, gap: 3, w: 5 }), lo(sd + 7, o, { w: 4 }), { occ: false }); dab(C.l, ...P([[x + 16, y - 6]])[0], 3.5 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 8 }); });
  line(C.l, P([[44, 8], [50, 12], [56, 8]]), lo(sd + 9, o, { w: 4 }));
}

// ——— passarinho (origem = centro; voa para a esquerda quando flip) ———
export function bird(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 950, col = o.col || K.red, s = o.s || 1;
  const F = fo(col, sd + 1, o, { p: 0.9, gap: 6, w: 8 });
  const up = o.pose ? 1 : 0;
  part(C, P(ellipse(0, 0, 34, 24, 26)), F, lo(sd + 2, o));
  part(C, P([[30, -8], [52, -2], [30, 6]]), fo(K.orange, sd + 3, o, { p: 1, gap: 3, w: 5 }), lo(sd + 4, o, { w: 4 }));
  const wing = up ? [[-14, -6], [-4, -60], [16, -8]] : [[-14, 2], [-4, 40], [16, 4]];
  part(C, P(wing), fo(col, sd + 5, o, { p: 0.95, gap: 5, w: 7 }), lo(sd + 6, o, { w: 5 }));
  dab(C.l, ...P([[18, -6]])[0], 3.6 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 7 });
  part(C, P([[-30, -4], [-52, -16], [-50, 8]]), F, lo(sd + 8, o, { w: 4.5 }));
}

// ——— sol (origem = centro). o.r0 = raio do disco; o.rays = progresso dos raios; o.face = 0–1 ———
export function sun(C, o) {
  const s = o.s || 1, sd = o.seed || 1100, x = o.x, y = o.y, R = (o.R ?? 110) * s;
  const rays = o.rays ?? 1;
  for (let i = 0; i < 14; i++) {
    const a = i / 14 * Math.PI * 2 + 0.2, r0 = R + 26 * s, r1 = R + (i % 2 ? 150 : 210) * s;
    const d = clamp(rays * 1.6 - i * 0.045); if (d <= 0) continue;
    line(C.l, [[x + Math.cos(a) * r0, y + Math.sin(a) * r0], [x + Math.cos(a) * r1, y + Math.sin(a) * r1]], { w: 11, col: i % 2 ? K.orange : K.yellow, p: 0.95, seed: sd + i, draw: d, taper: 0.4 });
  }
  if (R > 2) part(C, handCircle(x, y, R, sd + 20, 0.06), { col: K.yellow, p: 1.05, gap: 10, w: 13, seed: sd + 21, cross: true, crossP: 0.6, draw: o.fill ?? 1 }, o.outline === false ? null : { w: 8, col: K.orange, seed: sd + 22, draw: o.draw ?? 1 });
  const f = o.face ?? 0;
  if (f > 0) {
    const P = pts => pts.map(([px, py]) => [x + px * R / 110, y + py * R / 110]);
    if (o.expr === 'sleep') [[-36, -10], [36, -10]].forEach(([ex, ey], i) => line(C.l, P([[ex - 13, ey], [ex - 5, ey + 7], [ex + 5, ey + 7], [ex + 13, ey]]), { w: 6, col: K.ink, seed: sd + 30 + i, draw: f }));
    else [[-36, -14], [36, -14]].forEach(([ex, ey], i) => { if (f > 0.3) { dab(C.l, ...P([[ex, ey]])[0], 10 * R / 110, { col: K.ink, p: 1, seed: sd + 30 + i }); dab(C.l, ...P([[ex + 3, ey - 4]])[0], 3 * R / 110, { col: K.white, p: 1, seed: sd + 32 + i }); } });
    line(C.l, P([[-40, 26], [-20, 50], [20, 50], [40, 26]]), { w: 7, col: K.ink, seed: sd + 34, draw: clamp(f * 2 - 0.6) });
    if (f > 0.8) [[-66, 30], [66, 30]].forEach(([cx, cy], i) => dab(C.f, ...P([[cx, cy]])[0], 15 * R / 110, { col: K.orange, p: 0.75, seed: sd + 36 + i, sq: 0.7 }));
  }
}

// ——— lua crescente (sonolenta) ———
export function moon(C, o) {
  const x = o.x, y = o.y, R = (o.R ?? 120), sd = o.seed || 1200;
  const pts = [];
  for (let i = 0; i <= 30; i++) { const a = -Math.PI / 2 + i / 30 * Math.PI; pts.push([x + Math.cos(a) * R * -1, y + Math.sin(a) * R]); }
  for (let i = 30; i >= 0; i--) { const a = -Math.PI / 2 + i / 30 * Math.PI; pts.push([x - R * 0.25 + Math.cos(a) * R * -0.55, y + Math.sin(a) * R * 0.92]); }
  part(C, pts, { col: K.yellow, p: 1.05, gap: 8, w: 10, seed: sd + 1, ang: 1.1, cross: true, crossP: 0.6, draw: o.fill ?? 1 }, { w: 7, col: K.orange, seed: sd + 2, draw: o.draw ?? 1 });
  if ((o.fill ?? 1) > 0.6) {
    line(C.l, [[x - R * 0.78, y - R * 0.12], [x - R * 0.7, y - R * 0.05], [x - R * 0.6, y - R * 0.12]], { w: 5, col: K.ink, seed: sd + 3 });
    dab(C.f, x - R * 0.72, y + R * 0.14, R * 0.08, { col: K.orange, p: 0.7, seed: sd + 4 });
  }
}

// ——— coração ———
export function heart(C, o) {
  const s = o.s || 1, x = o.x, y = o.y;
  const pts = []; for (let i = 0; i <= 50; i++) { const a = i / 50 * Math.PI * 2; const hx = 16 * Math.pow(Math.sin(a), 3), hy = 13 * Math.cos(a) - 5 * Math.cos(2 * a) - 2 * Math.cos(3 * a) - Math.cos(4 * a); pts.push([x + hx * 3.4 * s, y - hy * 3.4 * s]); }
  part(C, pts, { col: o.col || K.red, p: 1, gap: 6, w: 8, seed: o.seed || 1300, ang: 0.7, draw: o.fill ?? 1 }, { w: 6, col: o.lineCol || K.ink, seed: (o.seed || 1300) + 1, draw: o.draw ?? 1 });
}

// ——— nuvem (cera branca + contorno) ———
export function cloud(C, o) {
  const x = o.x, y = o.y, s = o.s || 1, sd = o.seed || 1400;
  const pts = []; for (let i = 0; i <= 90; i++) { const a = i / 90 * Math.PI * 2; const b = 1 + 0.16 * Math.abs(Math.sin(a * 3.5)); pts.push([x + Math.cos(a) * 150 * s * b, y + Math.sin(a) * 62 * s * b * (Math.sin(a) > 0 ? 0.7 : 1)]); }
  part(C, pts, { col: o.col || K.white, p: 1, gap: 7, w: 9, seed: sd + 1, draw: o.fill ?? 1 }, { w: 6.5, col: K.ink, p: 0.85, seed: sd + 2, draw: o.draw ?? 1 });
}

// ——— árvore e flor ———
export function tree(C, o) {
  const x = o.x, y = o.y, s = o.s || 1, sd = o.seed || 1500;
  const trunk = [[x - 22 * s, y], [x - 18 * s, y - 170 * s], [x + 18 * s, y - 170 * s], [x + 22 * s, y]];
  part(C, trunk, { col: K.brown, p: 0.85, gap: 8, w: 10, ang: 1.5, seed: sd, draw: o.fill ?? 1 }, { w: 7, col: K.ink, seed: sd + 1, draw: o.draw ?? 1 });
  const crown = []; for (let i = 0; i <= 72; i++) { const a = i / 72 * 6.283; const b = 1 + 0.1 * Math.abs(Math.sin(a * 4.5)); crown.push([x + Math.cos(a) * 130 * s * b, y - 250 * s + Math.sin(a) * 115 * s * b]); }
  part(C, crown, { col: K.green, p: 0.85, gap: 11, w: 13, ang: 0.8, seed: sd + 2, cross: true, crossP: 0.45, draw: o.fill ?? 1 }, { w: 7.5, col: K.ink, seed: sd + 3, draw: o.draw ?? 1 });
  if ((o.fruit ?? 1) > 0) [[-60, -280], [40, -300], [70, -230], [-30, -210], [0, -330], [-80, -235]].forEach(([dx, dy], i) => { if (i / 6 < (o.fruit ?? 1)) dab(C.f, x + dx * s, y + dy * s, 14 * s, { col: K.red, p: 0.95, seed: sd + 10 + i }); });
}
export function flower(C, o) {
  const x = o.x, y = o.y, s = o.s || 1, sd = o.seed || 1600, g = o.g ?? 1;
  if (g <= 0) return;
  line(C.l, [[x, y], [x + 3 * s, y - 60 * s * g]], { w: 6, col: K.green, seed: sd, p: 0.95 });
  if (g < 0.6) return;
  const k = clamp((g - 0.6) / 0.4);
  for (let i = 0; i < 5; i++) { const a = i / 5 * 6.28; dab(C.f, x + 3 * s + Math.cos(a) * 15 * s, y - 60 * s + Math.sin(a) * 15 * s, 11 * s * k, { col: o.col || K.pink, p: 0.95, seed: sd + 1 + i }); }
  dab(C.f, x + 3 * s, y - 60 * s, 8 * s * k, { col: K.yellow, p: 1, seed: sd + 7 });
}

// ———————— novos no Ep. 02 ————————
export function giraffe(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 1700, s = o.s || 1;
  const F = fo(K.yellow, sd + 1, o, { p: 0.85, gap: 9, w: 11, ang: 0.5, cross: true, crossP: 0.35 });
  [[-50, 0], [-26, 0], [30, 0], [54, 0]].forEach(([x], i) => part(C, P(tube([[x, -120], [x, -6]], 16)), F, lo(sd + 10 + i, o)));
  part(C, P(ellipse(0, -150, 80, 46, 30)), F, lo(sd + 20, o));
  part(C, P(tube(curve([[48, -170], [70, -260], [86, -350]]), 30, 22)), F, lo(sd + 21, o));
  part(C, P(ellipse(100, -372, 40, 26, 24, 0, 6.3, 0.2)), F, lo(sd + 22, o));
  [[86, -400], [104, -404]].forEach(([x, y], i) => { line(C.l, P([[x, y + 8], [x, y - 14]]), lo(sd + 23 + i, o, { w: 5 })); dab(C.l, ...P([[x, y - 16]])[0], 5 * s, { col: K.brown, p: o.fill ?? 1, seed: sd + 25 + i }); });
  [[-30, -160, 14], [20, -140, 12], [-4, -176, 10], [52, -150, 9], [64, -230, 9], [78, -300, 8], [-52, -136, 9]].forEach(([x, y, r], i) => dab(C.f, ...P([[x, y]])[0], r * s, { col: K.orange, p: 0.9 * (o.fill ?? 1), seed: sd + 30 + i }));
  if (o.expr === 'sleep') line(C.l, P([[106, -380], [112, -376], [118, -380]]), lo(sd + 40, o, { w: 4 }));
  else { dab(C.l, ...P([[112, -380]])[0], 4.5 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 40 }); dab(C.l, ...P([[113.5, -382]])[0], 1.6 * s, { col: K.white, p: o.fill ?? 1, seed: sd + 41 }); }
  line(C.l, P([[124, -362], [132, -358]]), lo(sd + 42, o, { w: 4 }));
}
export function turtle(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 1800, s = o.s || 1;
  const skin = fo(K.green, sd + 1, o, { p: 0.6, gap: 7, w: 9 });
  [[-40, -6], [36, -6]].forEach(([x, y], i) => part(C, P(ellipse(x, y, 16, 10, 16)), skin, lo(sd + 2 + i, o, { w: 5 })));
  part(C, P(handCircle(66, -34, 22, sd + 4, 0, 20)), skin, lo(sd + 5, o, { w: 5 }));
  const shell = []; for (let i = 0; i <= 40; i++) { const a = Math.PI + i / 40 * Math.PI; shell.push([Math.cos(a) * 62, -10 + Math.sin(a) * 52]); }
  part(C, P(shell), fo(K.brown, sd + 6, o, { p: 0.8, gap: 8, w: 10, cross: true, crossP: 0.4 }), lo(sd + 7, o));
  [[-30, -34], [0, -46], [30, -34]].forEach(([x, y], i) => line(C.l, P(handCircle(x, y, 12, sd + 8 + i, 0, 14)), lo(sd + 11 + i, o, { w: 4, col: K.orange })));
  dab(C.l, ...P([[74, -40]])[0], 3.6 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 14 });
  line(C.l, P([[74, -26], [80, -24], [86, -27]]), lo(sd + 15, o, { w: 3.5 }));
}
// serpente curiosa (não assustadora): corpo em S enrolado num galho, olhos grandes, língua
export function serpent(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 1900, s = o.s || 1;
  const body = [[-120, 30], [-80, -10], [-30, 20], [20, -14], [60, 12], [92, -20], [110, -60]];
  part(C, P(tube(curve(body, 6), 26, 20)), fo('#7a8f3a', sd + 1, o, { p: 0.95, gap: 7, w: 9, ang: 0.9 }), lo(sd + 2, o));
  [[-90, 2], [-40, 10], [10, -2], [56, 2], [96, -36]].forEach(([x, y], i) => dab(C.f, ...P([[x, y]])[0], 5 * s, { col: K.yellow, p: o.fill ?? 1, seed: sd + 3 + i }));
  part(C, P(ellipse(126, -82, 30, 22, 24, 0, 6.3, -0.5)), fo('#7a8f3a', sd + 10, o, { p: 0.95, gap: 6, w: 8 }), lo(sd + 11, o));
  [[118, -94], [138, -100]].forEach(([x, y], i) => { part(C, P(handCircle(x, y, 8, sd + 12 + i, 0, 14)), fo(K.white, sd + 14 + i, o, { p: 1, gap: 3, w: 5 }), lo(sd + 16 + i, o, { w: 3.5 }), { occ: false }); dab(C.l, ...P([[x + 2 + (o.look || 0) * 3, y + 1]])[0], 3.4 * s, { col: K.ink, p: o.fill ?? 1, seed: sd + 18 + i }); });
  if (o.tongue) line(C.l, P([[150, -70], [170, -66], [178, -74], [172, -64], [180, -58]]), lo(sd + 20, o, { w: 3.5, col: K.red }));
  line(C.l, P([[128, -66], [140, -68], [150, -72]]), lo(sd + 21, o, { w: 3.5 }));
}
export function bush(C, o) {
  const x = o.x, y = o.y, s = o.s || 1, sd = o.seed || 1950;
  const pts = []; for (let i = 0; i <= 90; i++) { const a = Math.PI + i / 90 * Math.PI; const b = 1 + 0.14 * Math.abs(Math.sin(a * 5)); pts.push([x + Math.cos(a) * 240 * s * b, y + Math.sin(a) * 170 * s * b]); }
  pts.push([x + 240 * s, y + 20 * s], [x - 240 * s, y + 20 * s]);
  part(C, pts, { col: '#7a8f3a', p: 0.9, gap: 10, w: 12, seed: sd, ang: 0.9, cross: true, crossP: 0.5, draw: o.fill ?? 1 }, { w: 7, col: K.ink, seed: sd + 1, draw: o.draw ?? 1 });
  [[-120, -80], [40, -120], [140, -50], [-30, -40]].forEach(([dx, dy], i) => dab(C.f, x + dx * s, y + dy * s, 12 * s, { col: K.pink, p: 0.9 * (o.fill ?? 1), seed: sd + 5 + i }));
}
export function house(C, o) {
  const x = o.x, y = o.y, s = o.s || 1, sd = o.seed || 1960;
  const wall = [[x - 130 * s, y], [x - 130 * s, y - 180 * s], [x + 130 * s, y - 180 * s], [x + 130 * s, y]];
  part(C, wall, { col: K.peach, p: 0.85, gap: 9, w: 11, seed: sd, ang: -0.4, draw: o.fill ?? 1 }, { w: 7, col: K.ink, seed: sd + 1, draw: o.draw ?? 1 });
  part(C, [[x - 165 * s, y - 175 * s], [x, y - 320 * s], [x + 165 * s, y - 175 * s]], { col: K.red, p: 0.9, gap: 9, w: 11, seed: sd + 2, ang: 0.6, draw: o.fill ?? 1 }, { w: 7, col: K.ink, seed: sd + 3, draw: o.draw ?? 1 });
  part(C, [[x - 30 * s, y], [x - 30 * s, y - 95 * s], [x + 30 * s, y - 95 * s], [x + 30 * s, y]], { col: K.brown, p: 0.9, gap: 7, w: 9, seed: sd + 4, ang: 1.4, draw: o.fill ?? 1 }, { w: 6, col: K.ink, seed: sd + 5, draw: o.draw ?? 1 });
  part(C, [[x + 60 * s, y - 140 * s], [x + 110 * s, y - 140 * s], [x + 110 * s, y - 95 * s], [x + 60 * s, y - 95 * s]], { col: K.yellow, p: 1, gap: 6, w: 8, seed: sd + 6, draw: o.fill ?? 1 }, { w: 6, col: K.ink, seed: sd + 7, draw: o.draw ?? 1 });
}
export function fence(C, o) {   // cerca de giz: estacas desenhadas uma a uma (o.g = progresso)
  const g = o.g ?? 1, pts = o.pts, sd = o.seed || 1980;
  const n = pts.length - 1;
  for (let i = 0; i <= n; i++) { if (i / n > g) break; const [x, y] = pts[i]; part(C, [[x - 12, y], [x - 12, y - 90], [x, y - 108], [x + 12, y - 90], [x + 12, y]], { col: K.white, p: 1, gap: 5, w: 7, seed: sd + i * 3 }, { w: 5, col: K.brown, seed: sd + i * 3 + 1 }); }
  if (g > 0.3) for (const h of [-34, -70]) line(C.l, pts.slice(0, Math.max(2, Math.ceil((n + 1) * g))).map(([x, y]) => [x, y + h]), { w: 6, col: K.brown, seed: sd + 200 + h, draw: clamp((g - 0.3) / 0.7) });
}
export function fruit(C, x, y, r = 22, sd = 2990, bite = 0) {
  const pts = handCircle(x, y, r, sd, 0, 30);
  part(C, pts, { col: K.red, p: 1, gap: 4, w: 6, seed: sd }, { w: 5, col: K.ink, seed: sd + 1 });
  line(C.l, [[x, y - r], [x + 4, y - r - 14]], { w: 4, col: K.brown, seed: sd + 2 });
  dab(C.l, x - r * 0.35, y - r * 0.35, r * 0.22, { col: K.white, p: 1, seed: sd + 3 });
  if (bite > 0) { const bx = x + r * 0.8, by = y - r * 0.1; part(C, handCircle(bx, by, r * 0.5, sd + 4, 0, 16), { col: K.peach, p: 0.5, gap: 3, w: 4, seed: sd + 5 }, null); }
}

export function baby(C, o) {
  const T = T0(o), P = pts => T(pts), sd = o.seed || 2600, s = o.s || 1;
  part(C, P(smooth([[-70, 0], [-60, -40], [0, -54], [60, -40], [74, 0], [40, 20], [-40, 20]], 5)), fo(K.white, sd, o, { p: 1, gap: 7, w: 9 }), lo(sd + 1, o));
  [[-30, -40, -20, 10], [10, -44, 20, 14]].forEach(([a, b, c, d], i) => line(C.l, P([[a, b], [c, d]]), lo(sd + 2 + i, o, { w: 4 })));
  part(C, P(handCircle(-78, -26, 34, sd + 4, 0, 28)), fo(K.peach, sd + 5, o, { p: 0.6, gap: 8, w: 10 }), lo(sd + 6, o));
  [[-90, -30], [-68, -32]].forEach(([x, y], i) => line(C.l, P([[x - 5, y], [x, y + 4], [x + 5, y]]), lo(sd + 7 + i, o, { w: 3.5 })));
  line(C.l, P([[-84, -14], [-78, -10], [-72, -14]]), lo(sd + 9, o, { w: 3.5 }));
}
