// Arte da marca: ?page=<nome>&w=<largura>&h=<altura>
import { W, H, BOIL } from './crayon.js';
const cv = document.getElementById('gl'); cv.width = W; cv.height = H;
const { makeComp } = await import('./gl.js');
const comp = makeComp(cv);
await Promise.all(['400 40px "Patrick Hand"', '400 40px "Gochi Hand"'].map(f => document.fonts.load(f)));
const PG = new URLSearchParams(location.search).get('page') || '';
const B = await import(PG.startsWith('cb_') ? './colorir.js' : './brand.js');
window.DUR = 1;
window.render = t => { BOIL.step = 3; B.draw(comp, PG.replace(/^cb_/, '')); };
window.READY = true;
