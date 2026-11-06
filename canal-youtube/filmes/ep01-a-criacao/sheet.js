// Folha de personagens: ?test=model
import { layer, clear, text, CAM } from './crayon.js';
import { group, clearGroup } from './rig.js';
import { person, sheep, rabbit, lion, elephant, fish, bird, sun, moon, heart, cloud, tree, flower } from './chars.js';
import { PAL } from './pal.js';
const K = PAL.crayon;
const G = group(), TX = layer();
export function sheet(comp, t, Q) {
  CAM.x = 960; CAM.y = 540; CAM.s = 1; clearGroup(G); clear(TX);
  const page = Q.get('page') || 'people';
  if (page === 'people') {
    person(G, { x: 260, y: 900, s: 1.3, kind: 'adam', seed: 2000 });
    person(G, { x: 640, y: 900, s: 1.3, kind: 'eve', seed: 2200, expr: 'happy' });
    person(G, { x: 980, y: 900, s: 0.95, kind: 'child', seed: 2400, expr: 'wow', armR: [[34, -196], [80, -230], [100, -290]] });
    person(G, { x: 1320, y: 900, s: 1.0, kind: 'adam', seed: 2600, expr: 'sleep', armR: [[34, -196], [70, -160], [100, -130]] });
    person(G, { x: 1640, y: 900, s: 1.0, kind: 'eve', seed: 2800, expr: 'sing', armL: [[-34, -196], [-70, -160], [-100, -130]] });
    text(TX, 'Adão · Eva · você · descanso', 960, 1030, { size: 54, col: K.ink });
  } else if (page === 'animals') {
    sheep(G, { x: 220, y: 450, s: 1.4, seed: 500 });
    rabbit(G, { x: 560, y: 450, s: 1.4, seed: 600 });
    lion(G, { x: 980, y: 450, s: 1.2, seed: 700 });
    elephant(G, { x: 1560, y: 470, s: 1.2, seed: 800 });
    fish(G, { x: 240, y: 760, s: 1.2, col: K.orange, seed: 900 });
    fish(G, { x: 520, y: 780, s: 1.0, col: K.yellow, seed: 910, pose: 1, flip: true });
    bird(G, { x: 800, y: 760, s: 1.4, col: K.red, seed: 950 });
    bird(G, { x: 1000, y: 780, s: 1.4, col: K.sky, seed: 960, pose: 1 });
    sun(G, { x: 1350, y: 800, R: 90, face: 1, seed: 1100 });
    moon(G, { x: 1700, y: 800, R: 110, seed: 1200 });
    text(TX, 'animais · peixes · aves · sol · lua', 960, 1040, { size: 50, col: K.ink });
  } else {
    tree(G, { x: 300, y: 900, s: 1.2, seed: 1500 });
    cloud(G, { x: 900, y: 300, s: 1.3, seed: 1400 });
    heart(G, { x: 900, y: 700, s: 1.4, seed: 1300 });
    [0, 1, 2, 3].forEach(i => flower(G, { x: 1300 + i * 120, y: 900, s: 1.3, col: [K.pink, K.yellow, K.white, K.orange][i], seed: 1600 + i * 10 }));
  }
  comp.paperCam(960, 540, 1); comp.begin(); comp.group(G); comp.crayon(TX.c); comp.finish();
}
