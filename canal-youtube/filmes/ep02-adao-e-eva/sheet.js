// Folha de personagens do Ep. 02: ?test=model
import { layer, clear, text, CAM } from './crayon.js';
import { group, clearGroup } from './rig.js';
import { person, giraffe, turtle, serpent, bush, house, fence, fruit, lion, tree } from './chars.js';
import { PAL } from './pal.js';
const K = PAL.crayon;
const G = group(), F = group(), TX = layer();
export function sheet(comp, t, Q) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clearGroup(G); clearGroup(F); clear(TX);
  giraffe(G, { x: 180, y: 520, s: 1.0 }); turtle(G, { x: 470, y: 500, s: 1.3 }); serpent(G, { x: 760, y: 420, s: 1.2, tongue: true });
  house(G, { x: 1150, y: 520, s: 1.0 }); fence(G, { pts: [[1340, 520], [1400, 520], [1460, 520], [1520, 520], [1580, 520]] });
  fruit(G, 1750, 300, 30, 2990, 1); tree(G, { x: 1780, y: 560, s: 0.7, seed: 1590 });
  person(G, { x: 200, y: 1000, s: 1.1, kind: 'adam', expr: 'sad', seed: 2000 });
  person(G, { x: 420, y: 1000, s: 1.05, kind: 'eve', expr: 'sad', seed: 2200, armR: [[34, -196], [50, -240], [58, -262]] });
  person(G, { x: 700, y: 1000, s: 1.1, kind: 'adam', fur: 1, walk: 0.9, seed: 2000 });
  person(G, { x: 920, y: 1000, s: 1.05, kind: 'eve', fur: 1, walk: -0.9, seed: 2200, expr: 'happy' });
  person(F, { x: 1300, y: 1010, s: 1.1, kind: 'adam', seed: 2000, expr: 'sad' }); person(F, { x: 1440, y: 1010, s: 1.05, kind: 'eve', seed: 2200, expr: 'sad' });
  bush(F, { x: 1380, y: 1010, s: 0.9 });
  comp.paperCam(960, 540, 1); comp.begin(); comp.group(G); comp.group(F); comp.crayon(TX.c); comp.finish();
}
