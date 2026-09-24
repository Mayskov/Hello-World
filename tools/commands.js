'use strict';
// Console commands for tools/harness.js. Each returns false on failure.

function printTests(title, results) {
  console.log('\n' + title);
  let ok = true;
  for (const r of results) {
    console.log((r.ok ? '  PASS ' : '  FAIL ') + r.name + (r.ok ? '' : '  -> ' + r.detail));
    if (!r.ok) ok = false;
  }
  return ok;
}
const pct = x => (100 * x).toFixed(1) + '%';

function runBatch(BJJ, entries, mode, total, seed, subject, opponents) {
  const batch = BJJ.newBatch(entries);
  const jobs = BJJ.planJobs(mode, entries.length, total, subject, opponents);
  for (let k = 0; k < jobs.length; k++) BJJ.runJob(batch, jobs, k, seed);
  return BJJ.summariseBatch(batch);
}

// Benchmark fighters used only by the acceptance check.
function fixtures(BJJ) {
  const P = BJJ.PRESET_FIGHTERS, PL = BJJ.PRESET_PLANS;
  // Same archetype and plan family as the pressure passer, but the points are spent
  // on the wrong things and the plan skips its setups.
  const worseFighter = {
    name: 'Unfocused passer', archetype: 'pressure_passer', tapPolicy: 'balanced',
    attributes: { gripStrength: 6, pressure: 5, flexibility: 9, explosiveness: 5, cardio: 5, defense: 10 },
    techniques: { takedowns: 4, guard: 8, passing: 3, transitions: 3, submissions: 8, escapes: 4 },
  };
  const s = (primary, fallback, condition, maxAttempts) => ({ primary, fallback: fallback || null, condition: condition || 'always', maxAttempts: maxAttempts || 2 });
  const worsePlan = {
    name: 'Scattered plan',
    steps: [
      s('double_leg', null, 'always', 3),
      s('mt_armbar', null, 'always', 3),          // no arm isolation step
      s('og_toreando', null, 'always', 3),        // no pant grip step
      s('sc_kimura', null, 'always', 3),          // no wrist step
      s('bk_rnc', null, 'always', 3),
    ],
  };
  const mismatched = { // identical plan to the pressure passer, points in the guard player's places
    ...P.pressure, name: 'Pressure plan, guard build',
    attributes: { ...P.closed_guard.attributes }, techniques: { ...P.closed_guard.techniques },
  };
  return {
    better: { id: 'better', label: 'Pressure passer', fighter: P.pressure, plan: PL.passing },
    worse: { id: 'worse', label: 'Unfocused passer', fighter: worseFighter, plan: worsePlan },
    mismatched: { id: 'mismatched', label: 'Pressure plan, guard build', fighter: mismatched, plan: PL.passing },
  };
}

function describeAttempt(BJJ, at, names) {
  const a = BJJ.ACTIONS[at.actionId];
  const c = at.chance;
  let s = names[at.actor] + ' ' + a.name + ' [' + pct(c.total) + ' = base ' + pct(c.base) +
    ' attr ' + (c.attr * 100).toFixed(1) + ' arch ' + (c.archetype * 100).toFixed(1) +
    ' stam ' + (c.stamina * 100).toFixed(1) + ' fam ' + (c.familiarity * 100).toFixed(1) +
    ' react ' + (c.reaction * 100).toFixed(1) + '] roll ' + at.roll.toFixed(3) + ' -> ' + at.outcome;
  if (at.counterId) s += ' (countered with ' + BJJ.ACTIONS[at.counterId].name + ')';
  if (at.sub) s += ' sub:' + at.sub.decision + (at.sub.roll !== null ? ' ' + pct(at.sub.resistChance) + ' roll ' + at.sub.roll.toFixed(2) + (at.sub.survived ? ' survived' : ' caught') : '');
  return s;
}

module.exports = {
  selftest(BJJ) {
    let ok = printTests('Data self-tests', BJJ.runDataSelfTests());
    ok = printTests('Engine self-tests', BJJ.runEngineSelfTests()) && ok;
    return ok;
  },

  match(BJJ, args) {
    const seed = Number(args[0] || 1);
    const e = BJJ.presetEntries();
    const ia = Number(args[1] || 0), ib = Number(args[2] || 1);
    const A = e[ia], B = e[ib];
    const r = BJJ.runMatch([A.fighter, B.fighter], [A.plan, B.plan], seed);
    const names = ['A', 'B'];
    console.log('A = ' + A.label + ', B = ' + B.label + ', seed ' + seed);
    for (const t of r.log) {
      console.log('t' + String(t.tick).padStart(2) + ' ' + t.pos + (t.dom === null ? '' : ' (dom ' + names[t.dom] + ')') +
        ' intents: ' + t.intents.map(it => it ? it.actionId + '/' + it.source : '-').join(' | '));
      for (const at of t.attempts) console.log('     ' + describeAttempt(BJJ, at, names));
      for (const ev of t.events) if (ev.type !== 'plan_advance') console.log('     * ' + ev.type + ' ' + (ev.who !== undefined ? names[ev.who] : '') + ' ' + (ev.actionId || ev.step || ''));
      const st = t.state;
      console.log('     = pts ' + st.points + ' adv ' + st.adv + ' sta ' + st.stamina.map(x => x.toFixed(0)) + ' ptr ' + st.ptr + ' grips ' + JSON.stringify(st.grips) + ' flags ' + JSON.stringify(st.flags));
    }
    console.log('Winner ' + names[r.winner] + ' by ' + r.method);
  },

  matrix(BJJ, args) {
    const perPair = Number(args[0] || 1000);
    const entries = BJJ.presetEntries();
    const pairs = entries.length * (entries.length - 1) / 2;
    const sum = runBatch(BJJ, entries, 'matrix', perPair * pairs, 99);
    printSummary(sum);
  },

  accept(BJJ, args) {
    const scale = Number(args[0] || 1);
    let ok = true;
    const report = (name, pass, detail) => { console.log((pass ? '  PASS ' : '  FAIL ') + name + '  ' + detail); if (!pass) ok = false; };
    const entries = BJJ.presetEntries();
    const idx = id => entries.findIndex(e => e.id === id);
    const fx = fixtures(BJJ);

    console.log('\nAcceptance criteria');
    // 1. Better beats worse 65-75%.
    const bw = runBatch(BJJ, [fx.better, fx.worse], 'vs', 4000 * scale, 7, 0, [1]);
    report('Clearly better plan+fighter beats a clearly worse one 65-75%', bw.rows[0].winRate >= 0.65 && bw.rows[0].winRate <= 0.75, pct(bw.rows[0].winRate));

    // 2. Round robin: no preset above 60%.
    const pairs = entries.length * (entries.length - 1) / 2;
    const t0 = Date.now();
    const rr = runBatch(BJJ, entries, 'matrix', 2000 * pairs * scale, 11);
    const ms = Date.now() - t0;
    printSummary(rr);
    const top = Math.max(...rr.rows.map(r => r.winRate));
    report('No preset above 60% against the field', top <= 0.6, 'max ' + pct(top));

    // 3. Rock-paper-scissors.
    const m = rr.matrix;
    const rps = [['pressure', 'dlr', 'pressure passing beats open guard'],
      ['armbar', 'pressure', 'flexible guard beats slow pressure'],
      ['wrestler', 'armbar', 'wrestling beats closed-guard puller'],
      ['wrestler', 'dlr', 'wrestling beats de la Riva puller']];
    for (const [a, b, label] of rps) {
      const v = m[idx(a)][idx(b)];
      report('RPS: ' + label + ' by 55-65%', v >= 0.55 && v <= 0.65, pct(v));
    }

    // 4. Positions over 1000 matches.
    const thousand = runBatch(BJJ, entries, 'matrix', 1000, 3);
    const unvisited = thousand.visits.filter(v => !v.ticks).map(v => v.pos);
    const maxShare = Math.max(...thousand.visits.map(v => v.share));
    report('Every position visited in 1000 matches', !unvisited.length, unvisited.join(', ') || 'all visited');
    report('No position above 35% of ticks', maxShare <= 0.35, 'max ' + pct(maxShare) + ' (' + thousand.visits.find(v => v.share === maxShare).pos + ')');

    // 5. Attributes matter with an identical plan.
    const field = entries.slice();
    const e1 = runBatch(BJJ, [fx.better, ...field], 'vs', 4000 * scale, 21, 0, field.map((_, i) => i + 1));
    const e2 = runBatch(BJJ, [fx.mismatched, ...field], 'vs', 4000 * scale, 21, 0, field.map((_, i) => i + 1));
    const a1 = e1.rows[0], a2 = e2.rows[0];
    report('Same plan, different builds give different win rates', a1.ci.lo > a2.ci.hi || a2.ci.lo > a1.ci.hi,
      pct(a1.winRate) + ' vs ' + pct(a2.winRate));

    // 6-8. Determinism, speed, self-tests.
    const t1 = Date.now();
    runBatch(BJJ, entries, 'matrix', 10000, 5);
    const tenK = Date.now() - t1;
    report('10,000 matches in under 15 s (Node)', tenK < 15000, tenK + ' ms (round robin of ' + rr.matches + ' took ' + ms + ' ms)');
    const tests = [...BJJ.runDataSelfTests(), ...BJJ.runEngineSelfTests(1000)];
    const failed = tests.filter(t => !t.ok);
    report('Self-test suite passes (includes same-seed reproduction)', !failed.length, failed.map(t => t.name + ': ' + t.detail).join('; ') || tests.length + ' tests');
    return ok;
  },
};

function printSummary(sum) {
  console.log('\n' + 'entry'.padEnd(24) + 'win%   95% CI        sub%  dec%  tie%  len   stall  done');
  for (const r of sum.rows) {
    console.log(r.entry.label.padEnd(24) + pct(r.winRate).padStart(6) + '  ' + (pct(r.ci.lo) + '-' + pct(r.ci.hi)).padEnd(12) +
      pct(r.submissionShare).padStart(6) + pct(r.decisionShare).padStart(6) + pct(r.tieShare).padStart(6) +
      r.avgTicks.toFixed(1).padStart(6) + r.avgStallTick.toFixed(1).padStart(7) + pct(r.finishedPlanShare).padStart(7) + (r.dominant ? '  DOMINANT' : ''));
  }
  console.log('\nmatrix (row beats column)');
  console.log(''.padEnd(24) + sum.rows.map(r => r.entry.id.slice(0, 8).padStart(9)).join(''));
  sum.matrix.forEach((row, i) => console.log(sum.rows[i].entry.label.padEnd(24) + row.map(v => (v === null ? '-' : pct(v)).padStart(9)).join('')));
  console.log('\npositions: ' + sum.visits.map(v => v.pos + ' ' + pct(v.share)).join(', '));
  console.log('methods: ' + JSON.stringify(sum.methods) + ', avg ticks ' + sum.avgTicks.toFixed(1));
}
