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

module.exports = {
  selftest(BJJ) {
    let ok = printTests('Data self-tests', BJJ.runDataSelfTests());
    if (BJJ.runEngineSelfTests) ok = printTests('Engine self-tests', BJJ.runEngineSelfTests()) && ok;
    return ok;
  },
};
