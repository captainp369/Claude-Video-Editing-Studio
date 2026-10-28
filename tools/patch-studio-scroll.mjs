#!/usr/bin/env node
// Neutralises hyperframes-studio's scroll-to-change-value on numeric inputs.
//
// The studio attaches a `wheel` listener directly to each numeric <input> with no
// modifier key and no focus requirement, so merely hovering a field while scrolling
// the inspector rewrites layout values. The label drag-scrub (cursor-ew-resize) and
// the Arrow-key stepper both remain — this only requires the field to be FOCUSED
// before the wheel can touch it (the Figma/Blender convention).
//
// NOTE: hyperframes >= 0.7.x already ships this exact guard upstream. This patch is
// only needed while pinned to 0.6.6; bundles that are already correct are reported
// as "upstream-ok" and left untouched.
//
// Idempotent. Backs up each bundle once as <file>.orig before first patch.
// Re-run after any hyperframes version bump.  Usage: node patch-studio-scroll.mjs [--revert]

import { readFileSync, writeFileSync, existsSync, copyFileSync } from "node:fs";
import { globSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const GUARD = "if(document.activeElement!==v)return;";
// The wheel handler inside the numeric-input component `aA`.
const NEEDLE = "const S=w=>{if(e)return;const A=w.deltaY===0?w.deltaX:w.deltaY;";
const PATCHED = "const S=w=>{if(e)return;" + GUARD + "const A=w.deltaY===0?w.deltaX:w.deltaY;";
const revert = process.argv.includes("--revert");

const bundles = globSync(
  join(homedir(), ".npm/_npx/*/node_modules/hyperframes/dist/studio/assets/index-*.js"),
);

if (!bundles.length) {
  console.error("No hyperframes studio bundle found in the npx cache.");
  process.exit(1);
}

let changed = 0;
for (const file of bundles) {
  const backup = file + ".orig";
  let src = readFileSync(file, "utf8");

  if (revert) {
    if (existsSync(backup)) {
      copyFileSync(backup, file);
      console.log(`reverted  ${file}`);
      changed++;
    } else {
      console.log(`no backup ${file}`);
    }
    continue;
  }

  if (src.includes(PATCHED)) {
    console.log(`already   ${file}`);
    continue;
  }
  const hits = src.split(NEEDLE).length - 1;
  if (hits !== 1) {
    // Upstream (>=0.7.x) ships the focus guard already: `if(e||document.activeElement!==y)return;`
    const upstreamOk = /if\(\w\|\|document\.activeElement!==\w\)return;const \w=\w\.deltaY===0\?/.test(src);
    const label = upstreamOk
      ? "upstream-ok (already guarded, no patch needed)"
      : `no match (${hits} hits — bundle layout differs)`;
    console.log(`${upstreamOk ? "skip ok  " : "SKIP     "} ${label}\n           ${file}`);
    continue;
  }
  if (!existsSync(backup)) copyFileSync(file, backup);
  writeFileSync(file, src.replace(NEEDLE, PATCHED));
  console.log(`patched   ${file}`);
  changed++;
}
console.log(`\n${revert ? "Reverted" : "Patched"} ${changed}/${bundles.length} bundle(s).`);
console.log("Restart the preview server for it to take effect.");
