#!/usr/bin/env node
// hf-mixer — the audio + cut/trim panel HyperFrames Studio doesn't have.
//
// Studio is a layout editor: it has X/Y/W/H/Layer/Opacity and timeline drag, but
// zero audio controls (no volume, no mute, no solo) and trim only as drag handles
// that become unreachable when a clip runs past the composition end.
//
// This edits the composition HTML directly with surgical, id-targeted attribute
// rewrites — no DOM round-trip, so hand-authored formatting/SVG survives byte-exact.
// Studio hot-reloads on file change, so run both side by side.
//
//   node server.mjs <comp-dir> [--port 3010]

import { createServer } from "node:http";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2).filter((a) => !a.startsWith("--"));
const portArg = process.argv.indexOf("--port");
const PORT = portArg > -1 ? Number(process.argv[portArg + 1]) : 3010;
const COMP_DIR = resolve(args[0] || process.cwd());
const FILE = join(COMP_DIR, "index.html");

if (!existsSync(FILE)) {
  console.error(`No index.html in ${COMP_DIR}`);
  process.exit(1);
}

/* ---------------- HTML scanning (quote-aware, no DOM round-trip) ---------------- */

// Scan every opening tag, respecting quoted attribute values that may contain '>'.
function scanTags(html) {
  const out = [];
  const re = /<([a-zA-Z][a-zA-Z0-9-]*)(?=[\s/>])/g;
  let m;
  while ((m = re.exec(html))) {
    let i = m.index + m[0].length;
    let q = null;
    while (i < html.length) {
      const c = html[i];
      if (q) {
        if (c === q) q = null;
      } else if (c === '"' || c === "'") q = c;
      else if (c === ">") break;
      i++;
    }
    out.push({ tag: m[1], start: m.index, end: i + 1, text: html.slice(m.index, i + 1) });
    re.lastIndex = i;
  }
  return out;
}

function attrsOf(tagText) {
  const a = {};
  const re = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*("([^"]*)"|'([^']*)')/g;
  let m;
  while ((m = re.exec(tagText))) a[m[1]] = m[3] !== undefined ? m[3] : m[4];
  return a;
}

function setAttrInTag(tagText, name, value) {
  const esc = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`\\s${esc}\\s*=\\s*("[^"]*"|'[^']*')`);
  if (value === null) return tagText.replace(re, "");
  if (re.test(tagText)) return tagText.replace(re, ` ${name}="${value}"`);
  // insert before the tag's closing '>' (or '/>')
  return tagText.replace(/\s*\/?>$/, (m2) => ` ${name}="${value}"${m2.trimStart() || ">"}`);
}

function readComp() {
  const html = readFileSync(FILE, "utf8");
  const tags = scanTags(html);
  const rootTag = tags.find((t) => attrsOf(t.text)["data-composition-id"]);
  const root = rootTag ? attrsOf(rootTag.text) : {};
  const clips = [];
  for (const t of tags) {
    const a = attrsOf(t.text);
    if (a["data-composition-id"]) continue; // the root itself
    if (a["data-start"] === undefined) continue;
    const tag = t.tag.toLowerCase();
    const style = a.style || "";
    clips.push({
      id: a.id || null,
      tag,
      kind: tag === "audio" || tag === "video" ? "audio" : "visual",
      isMedia: tag === "audio" || tag === "video",
      src: a.src || null,
      srcName: a.src ? basename(a.src) : null,
      start: parseFloat(a["data-start"]) || 0,
      duration: a["data-duration"] !== undefined ? parseFloat(a["data-duration"]) : null,
      mediaStart: a["data-media-start"] !== undefined ? parseFloat(a["data-media-start"]) : null,
      volume: a["data-volume"] !== undefined ? parseFloat(a["data-volume"]) : 1,
      hasVolumeAttr: a["data-volume"] !== undefined,
      prevol: a["data-hf-prevol"] !== undefined ? parseFloat(a["data-hf-prevol"]) : null,
      track: a["data-track-index"] !== undefined ? parseInt(a["data-track-index"], 10) : null,
      muted: tag === "video" ? a.muted !== undefined : false,
      hidden: a["data-hf-hidden"] === "1" || /display\s*:\s*none/.test(style),
      cls: a.class || "",
    });
  }
  return {
    file: FILE,
    dir: COMP_DIR,
    project: basename(COMP_DIR),
    compId: root["data-composition-id"] || "?",
    compDuration: parseFloat(root["data-duration"]) || 0,
    width: parseInt(root["data-width"], 10) || 0,
    height: parseInt(root["data-height"], 10) || 0,
    clips,
  };
}

const undoStack = [];
function writeComp(next) {
  undoStack.push(readFileSync(FILE, "utf8"));
  if (undoStack.length > 50) undoStack.shift();
  writeFileSync(FILE, next);
}

// Rewrite the tag carrying id=<id> using fn(tagText) -> tagText
function mutateTag(id, fn) {
  const html = readFileSync(FILE, "utf8");
  const tags = scanTags(html);
  const hit = tags.find((t) => attrsOf(t.text).id === id);
  if (!hit) throw new Error(`no element with id="${id}"`);
  const nextTag = fn(hit.text);
  writeComp(html.slice(0, hit.start) + nextTag + html.slice(hit.end));
}

function setAttrs(id, attrs) {
  mutateTag(id, (txt) => {
    let out = txt;
    for (const [k, v] of Object.entries(attrs)) out = setAttrInTag(out, k, v);
    return out;
  });
}

const r2 = (n) => Math.round(n * 100) / 100;

/* ---------------- operations ---------------- */

function opSet({ id, attrs }) {
  setAttrs(id, attrs);
}

function opVolume({ id, volume }) {
  setAttrs(id, { "data-volume": r2(Math.max(0, Math.min(1, volume))) });
}

// Mute remembers the prior level in data-hf-prevol so unmute is exact.
function opMute({ id, on }) {
  const clip = readComp().clips.find((c) => c.id === id);
  if (!clip) throw new Error(`no clip ${id}`);
  if (on) {
    if (clip.volume === 0) return;
    setAttrs(id, { "data-hf-prevol": clip.volume, "data-volume": 0 });
  } else {
    const back = clip.prevol !== null ? clip.prevol : 1;
    setAttrs(id, { "data-volume": r2(back), "data-hf-prevol": null });
  }
}

function opSolo({ id, on }) {
  const media = readComp().clips.filter((c) => c.isMedia && c.tag === "audio" && c.id);
  for (const c of media) {
    if (c.id === id) {
      if (c.volume === 0 && c.prevol !== null) opMute({ id: c.id, on: false });
      continue;
    }
    opMute({ id: c.id, on: !!on });
  }
}

function opHide({ id, on }) {
  const html = readFileSync(FILE, "utf8");
  const tags = scanTags(html);
  const hit = tags.find((t) => attrsOf(t.text).id === id);
  if (!hit) throw new Error(`no clip ${id}`);
  const style = attrsOf(hit.text).style || "";
  if (on) {
    const nextStyle = (style.replace(/display\s*:\s*none;?\s*/g, "").trim() + ";display:none")
      .replace(/^;/, "");
    setAttrs(id, { "data-hf-hidden": "1", style: nextStyle });
  } else {
    const nextStyle = style.replace(/;?\s*display\s*:\s*none;?/g, "").trim();
    setAttrs(id, nextStyle ? { "data-hf-hidden": null, style: nextStyle } : { "data-hf-hidden": null, style: null });
  }
}

// Clamp duration so the clip ends exactly at the composition end.
function opFit({ id }) {
  const comp = readComp();
  const clip = comp.clips.find((c) => c.id === id);
  if (!clip) throw new Error(`no clip ${id}`);
  const dur = r2(Math.max(0.1, comp.compDuration - clip.start));
  setAttrs(id, { "data-duration": dur });
  return { duration: dur };
}

// Split a media clip in two at absolute time `at`, preserving source sync.
function opSplit({ id, at }) {
  const comp = readComp();
  const clip = comp.clips.find((c) => c.id === id);
  if (!clip) throw new Error(`no clip ${id}`);
  if (!clip.isMedia) throw new Error("split only supports <audio>/<video> clips");
  if (clip.duration === null) throw new Error("clip has no data-duration");
  const end = clip.start + clip.duration;
  if (!(at > clip.start + 0.05 && at < end - 0.05)) {
    throw new Error(`split time must be between ${r2(clip.start)} and ${r2(end)}`);
  }
  const html = readFileSync(FILE, "utf8");
  const tags = scanTags(html);
  const openTag = tags.find((t) => attrsOf(t.text).id === id);
  const closeIdx = html.indexOf(`</${clip.tag}>`, openTag.end);
  const outerEnd = closeIdx === -1 ? openTag.end : closeIdx + clip.tag.length + 3;
  const outer = html.slice(openTag.start, outerEnd);

  let newId = `${id}-b`;
  const taken = new Set(comp.clips.map((c) => c.id));
  let n = 2;
  while (taken.has(newId)) newId = `${id}-b${n++}`;

  let left = setAttrInTag(openTag.text, "data-duration", r2(at - clip.start));
  let rightTag = setAttrInTag(openTag.text, "id", newId);
  rightTag = setAttrInTag(rightTag, "data-start", r2(at));
  rightTag = setAttrInTag(rightTag, "data-duration", r2(end - at));
  const nextMediaStart = (clip.mediaStart || 0) + (at - clip.start);
  rightTag = setAttrInTag(rightTag, "data-media-start", r2(nextMediaStart));

  const leftOuter = outer.replace(openTag.text, left);
  const rightOuter = outer.replace(openTag.text, rightTag);
  writeComp(html.slice(0, openTag.start) + leftOuter + "\n  " + rightOuter + html.slice(outerEnd));
  return { newId };
}

function opDelete({ id }) {
  const comp = readComp();
  const clip = comp.clips.find((c) => c.id === id);
  if (!clip) throw new Error(`no clip ${id}`);
  const html = readFileSync(FILE, "utf8");
  const tags = scanTags(html);
  const openTag = tags.find((t) => attrsOf(t.text).id === id);
  const closeIdx = html.indexOf(`</${clip.tag}>`, openTag.end);
  const outerEnd =
    clip.isMedia && closeIdx !== -1 ? closeIdx + clip.tag.length + 3 : openTag.end;
  if (!clip.isMedia) throw new Error("delete is limited to <audio>/<video> clips (visual clips carry scene content)");
  writeComp(html.slice(0, openTag.start) + html.slice(outerEnd));
}

function opUndo() {
  if (!undoStack.length) throw new Error("nothing to undo");
  writeFileSync(FILE, undoStack.pop());
}

const OPS = {
  set: opSet,
  volume: opVolume,
  mute: opMute,
  solo: opSolo,
  hide: opHide,
  fit: opFit,
  split: opSplit,
  delete: opDelete,
  undo: opUndo,
};

/* ---------------- server ---------------- */

const send = (res, code, body, type = "application/json") => {
  res.writeHead(code, { "content-type": type, "cache-control": "no-store" });
  res.end(typeof body === "string" ? body : JSON.stringify(body));
};

createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    if (url.pathname === "/" || url.pathname === "/index.html") {
      return send(res, 200, readFileSync(join(HERE, "ui.html"), "utf8"), "text/html");
    }
    if (url.pathname === "/api/clips") return send(res, 200, readComp());
    if (url.pathname === "/api/op" && req.method === "POST") {
      const body = await new Promise((ok) => {
        let d = "";
        req.on("data", (c) => (d += c));
        req.on("end", () => ok(d));
      });
      const { op, ...rest } = JSON.parse(body || "{}");
      if (!OPS[op]) return send(res, 400, { error: `unknown op: ${op}` });
      const result = OPS[op](rest) || {};
      return send(res, 200, { ok: true, ...result, state: readComp() });
    }
    send(res, 404, { error: "not found" });
  } catch (e) {
    send(res, 400, { error: String(e.message || e) });
  }
}).listen(PORT, () => {
  const c = readComp();
  console.log(`hf-mixer  →  http://localhost:${PORT}`);
  console.log(`project   ${c.project}  (${c.compId}, ${c.compDuration}s, ${c.width}x${c.height})`);
  console.log(`file      ${FILE}`);
  console.log(`clips     ${c.clips.length} (${c.clips.filter((x) => x.isMedia).length} media)`);
});
