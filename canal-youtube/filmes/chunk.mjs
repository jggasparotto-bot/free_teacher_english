// Renderização retomável em blocos: node chunk.mjs <ep> --out <arquivo.mp4> [--q 'lang=en'] [--workers 4] [--fps 24] [--chunk 240]
// Cada bloco de quadros vira um .mp4 próprio em <out>.blocos/ (gravado com nome temporário e renomeado no fim),
// então se a máquina reiniciar, rodar de novo continua do primeiro bloco que falta. No fim junta tudo sem reencodar.
import fs from 'fs'; import path from 'path'; import { spawn, execFileSync } from 'child_process';
const LIB = process.env.LIB || '/home/user/lemomo-ai/lemo-opuscar';
const { openDemo, closeServer, requireDemo } = await import(path.join(LIB, 'core/render/page.mjs'));
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const dir = path.resolve(args[0]); requireDemo(dir);
const FPS = +opt('--fps', 24), WK = +opt('--workers', 4), Q = opt('--q', ''), CH = +opt('--chunk', 240);
const out = path.resolve(opt('--out', path.join(dir, 'out', 'video.mp4'))), bd = out + '.blocos';
fs.mkdirSync(bd, { recursive: true });
for (const n of fs.readdirSync(bd)) if (n.startsWith('tmp_')) fs.rmSync(path.join(bd, n));   // blocos interrompidos
const probe = await openDemo(dir, { q: Q }); const DUR = await probe.page.evaluate(() => window.DUR); await probe.browser.close();
const TOTAL = Math.round(DUR * FPS), N = Math.ceil(TOTAL / CH), name = i => `b_${String(i).padStart(4, '0')}.mp4`;
const todo = [...Array(N).keys()].filter(i => !fs.existsSync(path.join(bd, name(i))));
console.log(`${N} blocos, faltam ${todo.length}`); const t0 = Date.now(); let feitos = N - todo.length;
await Promise.all([...Array(Math.min(WK, todo.length))].map(async () => {
  const { browser, page } = await openDemo(dir, { q: Q });
  for (let i; (i = todo.shift()) !== undefined;) {
    const a = i * CH, b = Math.min(TOTAL, a + CH), tmp = 'tmp_' + name(i);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', tmp], { cwd: bd, stdio: ['pipe', 'inherit', 'inherit'] });
    const closed = new Promise(r => ff.on('close', r));
    for (let f = a; f < b; f++) {
      await page.evaluate(t => window.render(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); if (await closed !== 0) { console.error('ffmpeg falhou no bloco', i); process.exit(1); }
    fs.renameSync(path.join(bd, tmp), path.join(bd, name(i)));
    console.log(`bloco ${i} ok  (${++feitos}/${N})  ${((Date.now() - t0) / 60000).toFixed(1)} min`);
  }
  await browser.close();
}));
fs.writeFileSync(path.join(bd, 'lista.txt'), [...Array(N).keys()].map(i => `file '${name(i)}'`).join('\n'));
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'lista.txt', '-c', 'copy', 'junto.mp4'], { cwd: bd, stdio: 'inherit' });
fs.renameSync(path.join(bd, 'junto.mp4'), out); fs.rmSync(bd, { recursive: true, force: true });
console.log('done', out, TOTAL, 'quadros'); closeServer();
