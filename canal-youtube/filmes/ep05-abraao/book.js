// O livro: virada de página em tela cheia e o livro aberto sobre a mesa (fim do filme).
// Técnica de virada (faixas verticais com transformação afim + perspectiva) adaptada do motor crayon-book do Lemo-Opuscar (MIT).
// Espaço da mesa: página direita = [0,1920]×[0,1080], página esquerda = [-1920,0]×[0,1080], lombada em x = 0.
import { line, fill, ellipse, xf, CAM, W, H } from './crayon.js';
import { part } from './rig.js';
import { PAL } from './pal.js';
import { clamp, ss } from '/core/lib.js';
const K = PAL.crayon;
export const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return { c, g: c.getContext('2d') }; };
export const snap = P => { P.g.setTransform(1, 0, 0, 1, 0, 0); P.g.clearRect(0, 0, W, H); P.g.drawImage(document.getElementById('gl'), 0, 0); };
const toS = (x, y, cx, cy, z, f = 1) => [((x - cx) * f) * z + W / 2, ((y - cy) * f) * z + H / 2];

// th: ângulo da virada (0 = deitada à direita, π = virada para a esquerda). pages: { left, right, next, back } (canvases)
// k: 0 = só as páginas (tela cheia), 1 = livro sobre a mesa (sombra, capa, curvatura)
export function drawBook(g, th, pages, cx, cy, z, k) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, W, H);
  const D = 5200;
  const P = (x, y, h = 0) => toS(x, y, cx, cy, z, D / (D - h));
  if (k > 0) {
    g.save(); g.filter = `blur(${Math.max(1, 34 * z)}px)`; g.fillStyle = `rgba(40,22,10,${0.5 * k})`;
    const [a, b] = P(-1920, 20), [c, d] = P(2000, 1180); g.fillRect(a, b, c - a, d - b); g.restore();
    g.fillStyle = '#3a6e4c'; const [a2, b2] = P(-1975, -38), [c2, d2] = P(1975, 1118); rr(g, a2, b2, c2 - a2, d2 - b2, 14 * z); g.fill();
    g.strokeStyle = 'rgba(120,105,80,0.55)'; g.lineWidth = Math.max(1, 1.5 * z);
    for (let i = 1; i <= 4; i++) for (const sgn of [1, -1]) { const [x0, y0] = P(sgn * (1920 + i * 5), 6 + i * 3), [x1, y1] = P(sgn * (1920 + i * 5), 1074 + i * 3); g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); }
  }
  const turning = th > 0.001 && th < Math.PI - 0.001, turned = th >= Math.PI - 0.001;
  if (pages.left) flatPage(g, pages.left.c, -1, P, k);
  flatPage(g, (turned || turning) ? pages.next.c : pages.right.c, 1, P, k);
  if (turned && pages.back) flatPage(g, pages.back.c, -1, P, k);
  if (turning) {
    const edgeX = 1920 * Math.cos(th);
    if (th < Math.PI / 2) { const [ex] = P(Math.max(0, edgeX), 0), [sx0, sy0] = P(0, 0), [, sy1] = P(0, 1080); const gr = g.createLinearGradient(ex, 0, ex + 260 * z * (1 - Math.cos(th)), 0); gr.addColorStop(0, `rgba(30,20,10,${0.35 * Math.sin(th)})`); gr.addColorStop(1, 'rgba(30,20,10,0)'); g.fillStyle = gr; const [rx] = P(1920, 0); g.fillRect(sx0, sy0, rx - sx0, sy1 - sy0); }
    const N = 64;
    for (let i = 0; i < N; i++) {
      const u0 = 1920 * i / N, u1 = 1920 * (i + 1) / N, um = (u0 + u1) / 2;
      const ang = u => th - 0.5 * Math.sin(th) * Math.pow(u / 1920, 1.6);
      const aA = ang(u0), aB = ang(u1), am = ang(um);
      const x0 = u0 * Math.cos(aA), x1 = u1 * Math.cos(aB);
      const front = Math.cos(am) > 0;
      const hA = u0 * Math.sin(aA), hB = u1 * Math.sin(aB);
      const fA = D / (D - hA), fB = D / (D - hB);
      const [XA, YA0] = toS(x0, 0, cx, cy, z, fA), [, YA1] = toS(x0, 1080, cx, cy, z, fA);
      const [XB, YB0] = toS(x1, 0, cx, cy, z, fB);
      if (Math.abs(XB - XA) < 0.2) continue;
      const src = front ? pages.right.c : (pages.back || pages.right).c;
      const sw = 1920 / N, scol = front ? u0 : 1920 - u1;
      g.save();
      if (front) g.setTransform((XB - XA) / sw, (YB0 - YA0) / sw, 0, (YA1 - YA0) / 1080, XA, YA0);
      else g.setTransform((XA - XB) / sw, (YA0 - YB0) / sw, 0, (YA1 - YA0) / 1080, XB, YB0);
      g.drawImage(src, scol, 0, sw, 1080, 0, 0, sw * 1.04, 1080);
      const shade = front ? 0.28 * Math.sin(am) * (0.6 + 0.4 * u0 / 1920) : 0.16 * Math.abs(Math.cos(am));
      g.fillStyle = `rgba(40,28,15,${shade})`; g.fillRect(0, 0, sw * 1.04, 1080);
      g.restore();
    }
  }
  if (k > 0) {
    const [gx] = P(0, 0), [, gy0] = P(0, 0), [, gy1] = P(0, 1080), gw = 200 * z;
    const gr = g.createLinearGradient(gx - gw, 0, gx + gw, 0);
    gr.addColorStop(0, 'rgba(60,40,20,0)'); gr.addColorStop(0.42, 'rgba(60,40,20,0.12)'); gr.addColorStop(0.5, 'rgba(50,32,15,0.34)'); gr.addColorStop(0.58, 'rgba(60,40,20,0.12)'); gr.addColorStop(1, 'rgba(60,40,20,0)');
    g.fillStyle = gr; g.globalAlpha = k; g.fillRect(gx - gw, gy0 - 6 * z, gw * 2, gy1 - gy0 + 12 * z); g.globalAlpha = 1;
  }
}
function flatPage(g, src, side, P, k) {
  const N = 24;
  for (let i = 0; i < N; i++) {
    const u0 = 1920 * i / N, u1 = 1920 * (i + 1) / N;
    const lift = k * 14 * Math.pow(1 - Math.min(1, u0 / 420), 2);
    const xa = side > 0 ? u0 : -u1, xb = side > 0 ? u1 : -u0;
    const [X0, Y0] = P(xa, -lift), [X1, Y1] = P(xb, 1080 + lift * 0.3);
    const scol = side > 0 ? u0 : 1920 - u1;
    g.drawImage(src, scol, 0, 1920 / N, 1080, X0, Y0, X1 - X0 + 0.6, Y1 - Y0);
  }
}
function rr(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }

// Mesa de madeira desenhada em giz + alguns gizes de cera gastos
export function drawDesk(Dk) {
  const R = [[-2600, -1000], [2600, -1000], [2600, 2100], [-2600, 2100]];
  fill(Dk.f, R, { col: K.orange, p: 0.55, gap: 13, w: 16, ang: 0.08, seed: 700, over: 0, boil: 0 });
  fill(Dk.f, R, { col: K.brown, p: 0.55, gap: 18, w: 16, ang: -0.06, seed: 701, over: 0, boil: 0 });
  for (let i = 0; i < 26; i++) {
    const y0 = -1000 + i * 120 + ((i * 37) % 40); const pts = []; for (let x = -2600; x <= 2600; x += 100) pts.push([x, y0 + 16 * Math.sin(x * 0.0021 + i) + 8 * Math.sin(x * 0.009 + i * 2)]);
    line(Dk.l, pts, { w: 5, col: K.brown, p: 0.7, seed: 710 + i, wob: 2, boil: 0.4 });
  }
}
function crayonStick(C, x, y, a, col, len, sd) {
  const r = 46, T = pts => xf(pts, { x, y, r: a });
  const tip = [[len * 0.5, -r * 0.8], [len * 0.5 + 70, -r * 0.3], [len * 0.5 + 84, 0], [len * 0.5 + 70, r * 0.3], [len * 0.5, r * 0.8]];
  const body = [[-len * 0.5, -r], [len * 0.5, -r], ...tip.slice(1, -1), [len * 0.5, r], [-len * 0.5, r]];
  part(C, T(body), { col, p: 0.9, gap: 7, w: 9, ang: a + 1.5, seed: sd }, { w: 4.5, seed: sd + 1, col: K.ink });
  const wr = [[-len * 0.5, -r - 3], [len * 0.28, -r - 3], [len * 0.28, r + 3], [-len * 0.5, r + 3]];
  part(C, T(wr), { col, p: 0.7, gap: 6, w: 8, ang: a, seed: sd + 2 }, { w: 4, seed: sd + 3, col: K.ink });
  [-len * 0.38, len * 0.18].forEach((u, i) => fill(C.f, T([[u, -r - 3], [u + 26, -r - 3], [u + 26, r + 3], [u, r + 3]]), { col: K.ink, p: 0.8, gap: 4, w: 6, seed: sd + 4 + i }));
  line(C.l, T([[-len * 0.46, -r * 0.5], [len * 0.52, -r * 0.45]]), { w: 5, col: K.white, p: 0.9, seed: sd + 8 });
}
export function drawCrayons(C) {
  crayonStick(C, -1100, 1430, 0.1, K.yellow, 520, 800);
  crayonStick(C, -420, 1520, -0.18, K.green, 460, 820);
  crayonStick(C, 300, 1420, 0.25, K.sky, 420, 840);
  crayonStick(C, 1000, 1530, -0.06, K.red, 500, 860);
  crayonStick(C, 1700, 1400, 0.45, K.teal, 440, 880);
  crayonStick(C, -1750, 1560, -0.3, K.orange, 460, 900);
}
export const turnAngle = (t, t0, t1) => Math.PI * ss(clamp((t - t0) / (t1 - t0)));
