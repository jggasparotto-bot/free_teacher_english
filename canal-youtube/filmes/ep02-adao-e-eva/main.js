// Entrada: ?test=model abre a folha de personagens; senão, renderiza o filme
import { makeComp } from './gl.js';
import { BOIL } from './crayon.js';
const Q = new URLSearchParams(location.search);
const comp = makeComp(document.getElementById('gl'));
window.DUR = 1;
await Promise.all(['400 40px "Patrick Hand"', '400 40px "Gochi Hand"'].map(f => document.fonts.load(f)));
if (Q.get('test')) {
  const T = await import('./sheet.js');
  window.render = t => { BOIL.step = Math.floor(t * 12); T.sheet(comp, t, Q); };
} else {
  const M = await import('./film.js');
  window.DUR = M.DUR; window.EV = M.EV; window.SUBS = M.SUBS;
  window.render = t => { BOIL.step = Math.floor(t * 12 + 1e-6); M.frame(comp, t); };
}
window.READY = true;
