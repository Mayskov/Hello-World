#!/usr/bin/env node
// Loads the engine <script id="bjj-engine"> out of index.html and runs it in Node.
// Usage:
//   node tools/harness.js selftest          data + engine self-tests
//   node tools/harness.js match [seed]      one match between the first two presets, printed log
//   node tools/harness.js matrix [n]        round-robin of all preset entries, n matches per pair
//   node tools/harness.js accept            checks every acceptance criterion
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function loadEngine() {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  const m = html.match(/<script id="bjj-engine">([\s\S]*?)<\/script>/);
  if (!m) throw new Error('engine script not found in index.html');
  const context = { console };
  vm.createContext(context);
  vm.runInContext(m[1], context, { filename: 'index.html#bjj-engine' });
  return context.BJJ;
}

module.exports = { loadEngine };

if (require.main === module) {
  const BJJ = loadEngine();
  const cmd = process.argv[2] || 'selftest';
  const commands = require('./commands.js');
  if (!commands[cmd]) {
    console.error('unknown command ' + cmd + '; try: ' + Object.keys(commands).join(', '));
    process.exit(2);
  }
  Promise.resolve(commands[cmd](BJJ, process.argv.slice(3))).then(ok => process.exit(ok === false ? 1 : 0));
}
