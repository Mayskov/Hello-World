#!/usr/bin/env node
// Tune per-archetype progression power (training.xpBonus) and combat flavour so that best builds
// of every archetype average ~50% against the others at each career checkpoint.
//
//   node tools/tune-archetypes.js [iterations] [rounds]
//
// Each iteration: find best builds for the current numbers (tools/archetypes.js), measure the
// best-vs-best matrix, then nudge every archetype toward 50%: xpBonus for the trained
// checkpoints, combat flavour scale for all of them. Prints the numbers to paste into ARCHETYPES.
'use strict';
const { optimise, finalMatrix, describeBuild, CHECKPOINTS } = require('./archetypes.js');

const iterations = Number(process.argv[2] || 3);
const rounds = Number(process.argv[3] || 2);
const LIMITS = { xpBonus: [0.25, 1.5], flavour: [0.3, 2.5] };

function patchFor(params) {
  // Code run on the engine in every worker before searching.
  return Object.entries(params).map(([a, p]) =>
    `{ const A = B.ARCHETYPES['${a}']; A.training.xpBonus = ${p.xpBonus};` +
    ` for (const side of ['attack', 'defend']) for (const c in A[side]) A[side][c] = A[side][c] * ${p.flavour}; }`).join('\n');
}

(async () => {
  const { loadEngine } = require('./harness.js');
  const B0 = loadEngine();
  const archs = Object.keys(B0.ARCHETYPES);
  const params = Object.fromEntries(archs.map(a => [a, { xpBonus: Number(process.env.XP || B0.ARCHETYPES[a].training.xpBonus), flavour: 1 }]));
  const pct = x => (100 * x).toFixed(0).padStart(4);
  for (let it = 0; it <= iterations; it++) {
    const patch = patchFor(params);
    const { B, builds } = await optimise(rounds, patch);
    const res = finalMatrix(B, archs, builds);
    console.log('\n=== iteration ' + it + ' ' + JSON.stringify(params));
    for (const r of res) console.log(String(r.cp.sessions).padStart(3) + ' ' + r.cp.belt.padEnd(7) + archs.map((a, i) => a.slice(0, 8) + pct(r.avg[i])).join('  ') +
      '   spread ' + pct(Math.max(...r.avg) - Math.min(...r.avg)));
    const late = archs.map((_, i) => res.slice(1).reduce((s, r) => s + r.avg[i], 0) / (res.length - 1));
    const all = archs.map((_, i) => res.reduce((s, r) => s + r.avg[i], 0) / res.length);
    console.log('late avg ' + archs.map((a, i) => a.slice(0, 8) + pct(late[i])).join('  '));
    for (const r of res.slice(-1)) archs.forEach((a, i) => { const d = describeBuild(B, a, r.cp, builds[a][CHECKPOINTS.indexOf(r.cp)]); console.log('   ' + a.padEnd(18) + d.style.padEnd(42) + d.train); });
    if (it === iterations) break;
    archs.forEach((a, i) => {
      const p = params[a];
      p.xpBonus = Math.round(Math.min(LIMITS.xpBonus[1], Math.max(LIMITS.xpBonus[0], p.xpBonus + 4 * (0.5 - late[i]))) * 100) / 100;
      p.flavour = Math.round(Math.min(LIMITS.flavour[1], Math.max(LIMITS.flavour[0], p.flavour * (1 + 6 * (0.5 - all[i])))) * 100) / 100;
    });
  }
})();
