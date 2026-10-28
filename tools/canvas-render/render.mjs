// canvas-render — frame-accurate render of a canvas composition to MP4.
//
// The page must expose:  window.whenReady (Promise), window.renderAt(t), window.DURATION,
// and a <canvas id="c">. Setting window.__EXPORT before load puts it in export mode.
// Every frame is drawn by renderAt(t) for an exact t, so the output is deterministic and
// independent of how fast the machine is (same principle as hyperframes' paused-timeline seek).
//
// Usage:
//   node render.mjs <page.html> <out.mp4> [--query f=h] [--audio mix.wav] [--fps 30]
//   node render.mjs <page.html> <outprefix> --stills 3,12.5,40 [--query f=h]
import puppeteer from 'puppeteer-core';
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const [page_, out] = args;
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const FPS = Number(opt('fps', 30));
const query = opt('query', '');
const audio = opt('audio');
const stills = opt('stills');

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
  args: ['--force-device-scale-factor=1', '--allow-file-access-from-files'],
});
const page = await browser.newPage();
page.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exitCode = 1; });
await page.evaluateOnNewDocument(() => { window.__EXPORT = true; });
await page.goto('file://' + resolve(page_) + (query ? '?' + query : ''), { waitUntil: 'domcontentloaded' });
await page.evaluate(() => window.whenReady);
const size = await page.evaluate(() => { const c = document.getElementById('c'); return [c.width, c.height]; });
await page.setViewport({ width: size[0], height: size[1], deviceScaleFactor: 1 });
if (await page.evaluate(() => typeof window.fontCheck === 'function')) console.log('fonts', await page.evaluate(() => window.fontCheck()));

const grab = t => page.evaluate(t => { window.renderAt(t); return document.getElementById('c').toDataURL('image/png').slice(22); }, t);

if (stills) {
  for (const t of stills.split(',').map(Number)) writeFileSync(`${out}-${t.toFixed(2).padStart(6, '0')}.png`, Buffer.from(await grab(t), 'base64'));
} else {
  const dur = await page.evaluate(() => window.DURATION);
  const ffArgs = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-'];
  if (audio) ffArgs.push('-i', resolve(audio));
  ffArgs.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', '-r', String(FPS));
  if (audio) ffArgs.push('-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest');
  ffArgs.push('-movflags', '+faststart', resolve(out));
  const ff = spawn('ffmpeg', ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * FPS);
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    if (!ff.stdin.write(Buffer.from(await grab(i / FPS), 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log(`done ${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${out}`);
}
// browser.close() occasionally hangs after still captures; don't let it block the shell
await Promise.race([browser.close(), new Promise(r => setTimeout(r, 3000))]);
process.exit(process.exitCode || 0);
