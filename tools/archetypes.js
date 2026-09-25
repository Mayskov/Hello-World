#!/usr/bin/env node
// Archetype balance: find each archetype's best build (training mix + style cards) at several
// career checkpoints, as a best response to the other archetypes' best builds, then report the
// best-vs-best matrix on fresh seeds.
//
//   node tools/archetypes.js [rounds] [--json out.json]
//
// A "build" is how many sessions of each training the fighter did plus the chosen style cards,
// so archetypes are compared at equal training time, not equal points: an archetype that levels
// its own stats faster is allowed to benefit from it.
'use strict';
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const path = require('path');
const fs = require('fs');
const { loadEngine } = require('./harness.js');

const CHECKPOINTS = [
  { sessions: 0, belt: 'white' },
  { sessions: 8, belt: 'blue' },
  { sessions: 16, belt: 'purple' },
  { sessions: 26, belt: 'brown' },
];
const SEARCH = { matchesPerOpponent: 140, maxEvals: 220, patience: 70 };
const FINAL = { matchesPerPair: 800 };

// ---------------- shared helpers ----------------
function naiveBuild(B, arch, cp) {
  // Spread sessions over the trainings whose main gain is one of the archetype's fast stats.
  const fast = B.ARCHETYPES[arch].training.stats;
  const ids = B.TRAININGS.filter(t => fast.includes(Object.keys(t.gains)[0])).map(t => t.id);
  const counts = {};
  for (let k = 0; k < cp.sessions; k++) counts[ids[k % ids.length]] = (counts[ids[k % ids.length]] || 0) + 1;
  return { counts, style: { ...B.STARTERS[arch].style } };
}
function materialise(B, arch, cp, build) {
  const g = B.buildFromTrainings(arch, build.counts, cp.belt, build.style);
  for (const slot of B.STYLE_SLOTS) if (!B.optionUnlocked(g.fighter, B.styleOption(slot.id, build.style[slot.id]))) return null;
  return { fighter: g.fighter, plan: B.compileStyle(build.style) };
}
function winRate(B, a, b, seeds) {
  let w = 0;
  seeds.forEach((s, i) => {
    // Alternate sides so neither slot is favoured.
    const r = i % 2 ? B.runMatch([b.fighter, a.fighter], [b.plan, a.plan], s, { log: false }) : B.runMatch([a.fighter, b.fighter], [a.plan, b.plan], s, { log: false });
    if (r.winner === (i % 2 ? 1 : 0)) w++;
  });
  return w / seeds.length;
}

// ---------------- worker: best response for one archetype at one checkpoint ----------------
function bestResponse(B, arch, cp, start, field, seedBase) {
  const seeds = Array.from({ length: SEARCH.matchesPerOpponent }, (_, i) => B.deriveSeed(seedBase, i));
  const opponents = field.map(f => materialise(B, f.arch, cp, f.build)).filter(Boolean);
  const fitness = build => {
    const me = materialise(B, arch, cp, build);
    if (!me) return -1;
    return opponents.reduce((s, o) => s + winRate(B, me, o, seeds), 0) / opponents.length;
  };
  const rng = B.makeRng(seedBase ^ 0xabcdef);
  const pick = list => list[Math.floor(rng() * list.length)];
  let best = { counts: { ...start.counts }, style: { ...start.style } };
  let bestFit = fitness(best);
  let evals = 1, stale = 0;
  const ids = B.TRAININGS.map(t => t.id);
  while (evals < SEARCH.maxEvals && stale < SEARCH.patience) {
    const cand = { counts: { ...best.counts }, style: { ...best.style } };
    const have = ids.filter(id => cand.counts[id] > 0);
    if (have.length && rng() < 0.7) {
      const from = pick(have), to = pick(ids.filter(id => id !== from));
      const n = Math.min(cand.counts[from], rng() < 0.3 ? 2 : 1);
      cand.counts[from] -= n;
      cand.counts[to] = (cand.counts[to] || 0) + n;
    } else if (rng() < 0.85) {
      const slot = pick(B.STYLE_SLOTS);
      cand.style[slot.id] = pick(slot.options.filter(o => o.id !== cand.style[slot.id])).id;
    } else {
      cand.style.risk = pick(Object.keys(B.RISK_LEVELS).filter(k => k !== cand.style.risk));
    }
    const f = fitness(cand);
    evals++;
    if (f > bestFit) { best = cand; bestFit = f; stale = 0; } else stale++;
  }
  return { build: best, fitness: bestFit, evals };
}

if (!isMainThread) {
  const B = loadEngine();
  if (workerData.patch) new Function('B', workerData.patch)(B);
  const { arch, jobs } = workerData;
  const out = jobs.map(j => ({ cpIndex: j.cpIndex, ...bestResponse(B, arch, CHECKPOINTS[j.cpIndex], j.start, j.field, j.seedBase) }));
  parentPort.postMessage(out);
  return;
}

// ---------------- main ----------------
function runWorkers(archs, jobsByArch, patch) {
  return Promise.all(archs.map(arch => new Promise((resolve, reject) => {
    const w = new Worker(__filename, { workerData: { arch, jobs: jobsByArch[arch], patch } });
    w.on('message', resolve);
    w.on('error', reject);
  })));
}

async function optimise(rounds, patch, log) {
  const B = loadEngine();
  if (patch) new Function('B', patch)(B);
  const archs = Object.keys(B.ARCHETYPES);
  // builds[arch][cpIndex]
  const builds = Object.fromEntries(archs.map(a => [a, CHECKPOINTS.map(cp => naiveBuild(B, a, cp))]));
  for (let r = 0; r < rounds; r++) {
    const jobsByArch = {};
    for (const a of archs) {
      jobsByArch[a] = CHECKPOINTS.map((cp, ci) => ({
        cpIndex: ci, start: builds[a][ci], seedBase: 1000 * (r + 1) + ci,
        field: archs.filter(o => o !== a).map(o => ({ arch: o, build: builds[o][ci] })),
      }));
    }
    const results = await runWorkers(archs, jobsByArch, patch);
    results.forEach((res, i) => { for (const x of res) builds[archs[i]][x.cpIndex] = x.build; });
    if (log) log('round ' + (r + 1) + ' done');
  }
  return { B, archs, builds };
}

function finalMatrix(B, archs, builds) {
  const seeds = Array.from({ length: FINAL.matchesPerPair }, (_, i) => B.deriveSeed(777777, i));
  return CHECKPOINTS.map((cp, ci) => {
    const m = archs.map(a => materialise(B, a, cp, builds[a][ci]));
    const matrix = archs.map((_, i) => archs.map((__, j) => (i === j ? null : winRate(B, m[i], m[j], seeds))));
    const avg = matrix.map(row => row.filter(v => v !== null).reduce((s, v) => s + v, 0) / (archs.length - 1));
    return { cp, matrix, avg, fighters: m };
  });
}

function describeBuild(B, arch, cp, build) {
  const f = materialise(B, arch, cp, build);
  const train = Object.entries(build.counts).filter(([, n]) => n).sort((a, b) => b[1] - a[1]).map(([id, n]) => id + '×' + n).join(' ');
  const style = B.STYLE_SLOTS.map(s => build.style[s.id]).join('/') + '/' + build.style.risk;
  const stats = f ? [...B.ATTRIBUTE_KEYS, ...B.TECHNIQUE_KEYS].map(k => B.statValue(f.fighter, k)).join(' ') : 'locked';
  return { train, style, stats };
}

module.exports = { CHECKPOINTS, optimise, finalMatrix, describeBuild };

if (require.main === module) {
  (async () => {
    const rounds = Number(process.argv[2] || 3);
    const jsonAt = process.argv.indexOf('--json');
    const t0 = Date.now();
    const { B, archs, builds } = await optimise(rounds, null, m => console.log(m + ' (' + ((Date.now() - t0) / 1000).toFixed(0) + ' s)'));
    const res = finalMatrix(B, archs, builds);
    const pct = x => (x === null ? '   -' : (100 * x).toFixed(0).padStart(4));
    for (const r of res) {
      console.log('\n' + r.cp.sessions + ' sessions, ' + r.cp.belt + ' belt  (row beats column, avg vs others)');
      archs.forEach((a, i) => console.log(a.padEnd(18) + r.matrix[i].map(pct).join('') + '   avg ' + pct(r.avg[i])));
      archs.forEach((a, i) => { const d = describeBuild(B, a, r.cp, builds[a][CHECKPOINTS.indexOf(r.cp)]); console.log('  ' + a.padEnd(18) + d.style.padEnd(40) + d.train); });
    }
    if (jsonAt > 0) fs.writeFileSync(process.argv[jsonAt + 1], JSON.stringify({ builds, results: res.map(r => ({ cp: r.cp, matrix: r.matrix, avg: r.avg })) }, null, 1));
    console.log('\ntotal ' + ((Date.now() - t0) / 1000).toFixed(0) + ' s');
  })();
}
