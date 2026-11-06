// Entrada de um episódio feito com o motor storybook
import { W, H, BOIL } from './crayon.js';
const cv = document.getElementById('gl'); cv.width = W; cv.height = H;
const { makeComp } = await import('./gl.js');
const comp = makeComp(cv);
await Promise.all(['400 40px "Patrick Hand"', '400 40px "Gochi Hand"'].map(f => document.fonts.load(f)));
const M = await import('./storybook.js');
window.DUR = M.DUR; window.EV = M.EV; window.SUBS = M.SUBS;
window.render = t => { BOIL.step = Math.floor(t * 12 + 1e-6); M.frame(comp, t); };
window.READY = true;
