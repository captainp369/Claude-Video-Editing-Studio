// usage: node extract_events.mjs <composition.html> <events.json> [--id compId] [--browser-url http://127.0.0.1:9335]
// Loads a HyperFrames composition headless, walks its GSAP timeline and turns real animation calls into sound-effect
// events with what moved. Nothing is guessed from pixels: every event is a tween the composition really plays.
//   scale-in from ≥1.4 (slam)            → stamp
//   scale-in from ≤0.9 with back/elastic → pop (kind: photo / card / chip / svg / html, from the element's class)
//   background-size sweep (marker)       → marker
//   strokeDashoffset (line draw)         → draw
//   clip-path inset reveal (typing)      → type
//   a number tween with onUpdate         → count
//   a big slide-in (≥300 px) or blur zoom → swoosh
//   scaleX/scaleY 0 → 1 without spring   → wipe
//   fade-up of an HTML element           → rise
// Start values are read from tl.from() vars or fromTo() startAt; long (≥3 s), yoyo and camera/background tweens are ignored.
// An element can ask for a specific voice with data-sfx="tear" (any voice name in sfxkit.py) or for silence with data-sfx="none".
// puppeteer-core is found in this order: $PUPPETEER_CORE (path to its ESM entry), a local node_modules, HyperFrames' npx cache.
// The browser: --browser-url to reuse a running Chrome, else $CHROME_PATH, else HyperFrames' bundled chrome-headless-shell.
import { writeFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path'; import { homedir } from 'os'; import { pathToFileURL } from 'url';
const argv = process.argv.slice(2), flag = (k) => { const i = argv.indexOf(k); return i >= 0 ? argv.splice(i, 2)[1] : null; };
const browserURL = flag('--browser-url'), compId = flag('--id'); const [file, out] = argv;
if (!file || !out) { console.error('usage: node extract_events.mjs <composition.html> <events.json> [--id compId] [--browser-url URL]'); process.exit(1); }
const findIn = (root, name, depth = 6) => { if (depth < 0 || !existsSync(root)) return null;
  for (const e of readdirSync(root, { withFileTypes: true })) { const p = join(root, e.name);
    if (e.name === name && e.isFile()) return p; if (e.isDirectory()) { const r = findIn(p, name, depth - 1); if (r) return r; } } return null; };
async function loadPuppeteer() {
  if (process.env.PUPPETEER_CORE) return (await import(pathToFileURL(process.env.PUPPETEER_CORE).href)).default;
  try { return (await import('puppeteer-core')).default; } catch {}
  const npx = join(homedir(), '.npm/_npx');
  if (existsSync(npx)) for (const d of readdirSync(npx)) { const p = join(npx, d, 'node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js'); if (existsSync(p)) return (await import(pathToFileURL(p).href)).default; }
  throw new Error('puppeteer-core not found: run `npm i puppeteer-core` here, or set PUPPETEER_CORE');
}
const puppeteer = await loadPuppeteer();
let b, launched = false;
if (browserURL) b = await puppeteer.connect({ browserURL });
else { const exe = process.env.CHROME_PATH || findIn(join(homedir(), '.cache/hyperframes/chrome'), 'chrome-headless-shell');
  if (!exe) throw new Error('no Chrome found: set CHROME_PATH or install HyperFrames (it bundles chrome-headless-shell)');
  b = await puppeteer.launch({ executablePath: exe, headless: true, args: ['--allow-file-access-from-files', '--no-sandbox'] }); launched = true; }
const p = await b.newPage(); p.on('pageerror', e => console.log('page error:', e.message));
await p.goto(pathToFileURL(file.startsWith('/') ? file : join(process.cwd(), file)).href, { waitUntil: 'load' }); await new Promise(r => setTimeout(r, 1200));
const ev = await p.evaluate((wantId) => {
  const ids = Object.keys(window.__timelines || {}); const id = wantId || (document.querySelector('[data-composition-id]') || {}).dataset?.compositionId || ids[0];
  const tl = window.__timelines[id]; if (!tl) return { error: 'no timeline ' + id + ' (have ' + ids.join(',') + ')' };
  const res = [];
  const kind = (el) => { if (!(el instanceof Element)) return 'obj'; const c = el.classList, nm = ((el.id || '') + ' ' + (el.getAttribute('class') || '')).toLowerCase();
    if (c.contains('photo') || /photo|img|pic/.test(nm)) return 'photo'; if (c.contains('card') || /card|note|panel/.test(nm)) return 'card';
    if (c.contains('chip') || c.contains('tag') || c.contains('pill') || /chip|tag|pill|badge/.test(nm)) return 'chip';
    if (c.contains('stamp') || /stamp/.test(nm)) return 'stamp'; if (el instanceof SVGElement) return 'svg'; return 'html'; };
  const ambient = (el, d, v) => d >= 3 || (el instanceof Element && /\b(cam|camera|grid|bg|background|grain)\b/.test(((el.id || '') + ' ' + (el.getAttribute('class') || '')).toLowerCase())) || (v.yoyo && v.repeat);
  for (const tw of tl.getChildren(true, true, false)) {
    const v = tw.vars || {}, t = +tw.startTime().toFixed(3), d = +tw.duration().toFixed(3);
    const s = v.runBackwards ? v : (v.startAt || {});             // start values: tl.from() keeps them in vars, fromTo() in startAt
    const tg = tw.targets()[0], ease = String(v.ease || ''), n = tw.targets().length;
    const hint = tg instanceof Element ? (tg.dataset.sfx || '') : '', el = tg instanceof Element ? (tg.id || tg.getAttribute('class') || tg.tagName) : '';
    if (hint === 'none') continue;
    if (tg && !(tg instanceof Element) && v.onUpdate && d > 0 && d <= 6 && !('t' in tg)) { res.push({ t, type: 'count', dur: d }); continue; }
    if (ambient(tg, d, v)) continue;
    const sc = typeof s.scale === 'number' ? s.scale : null, sx = typeof s.scaleX === 'number' ? s.scaleX : null, sy = typeof s.scaleY === 'number' ? s.scaleY : null;
    const springy = /back|elastic/.test(ease);
    if (sc !== null && sc >= 1.4) { res.push({ t, type: 'stamp', el, hint }); continue; }
    if ((sc !== null && sc <= 0.9) && springy) { res.push({ t, type: 'pop', kind: kind(tg), n, el, hint }); continue; }
    if ((sx === 0 || sy === 0) && springy) { res.push({ t, type: 'pop', kind: kind(tg), n, el, hint }); continue; }
    if (sx === 0 || sy === 0) { res.push({ t, type: 'wipe', dur: d, el, hint }); continue; }
    if (v.backgroundSize) { res.push({ t, type: 'marker', dur: d }); continue; }
    if ('strokeDashoffset' in v) { res.push({ t, type: 'draw', dur: d, el, hint }); continue; }
    if (typeof v.clipPath === 'string' && /inset\(\s*-?[\d.]+(px|%)?\s+0%/.test(v.clipPath) && !v.runBackwards) { res.push({ t, type: 'type', dur: d, el, hint }); continue; }
    const bigMove = Math.max(Math.abs(+s.x || 0), Math.abs(+s.y || 0), Math.abs(parseFloat(s.xPercent) || 0) * 10) >= 300;
    if (bigMove || (sc !== null && sc > 1 && s.filter)) { res.push({ t, type: 'swoosh', el, hint }); continue; }
    if (sc !== null && sc <= 0.9 && s.opacity === 0) { res.push({ t, type: 'pop', kind: kind(tg), n, el, hint }); continue; }
    if (s.opacity === 0 && (s.y || s.x) && tg instanceof Element && !(tg instanceof SVGElement)) { res.push({ t, type: 'rise', el, hint }); continue; }
  }
  return { id, dur: tl.duration(), events: res.sort((a, b) => a.t - b.t) };
}, compId);
if (ev.error) { console.error(ev.error); process.exit(1); }
writeFileSync(out, JSON.stringify(ev, null, 1));
const cnt = {}; ev.events.forEach((e) => { const k = e.type + (e.kind ? ':' + e.kind : '') + (e.hint ? '[' + e.hint + ']' : ''); cnt[k] = (cnt[k] || 0) + 1; });
console.log(out, ev.events.length, 'events', JSON.stringify(cnt));
await p.close(); if (launched) await b.close(); else b.disconnect();
