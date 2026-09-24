# BJJ Plan Simulator (web prototype)

A balance-and-feel prototype for a Brazilian jiu-jitsu game where players don't fight in real time.
Each player builds a fighter and writes a game plan of up to 10 steps. The engine then simulates a
6-minute match in 36 ticks of 10 seconds and explains, tick by tick, why the plan worked or failed.

## Running it

Open `index.html` in a browser. It's one self-contained file with no build step, no dependencies and
no network requests. The interface is in Russian; internal ids (actions, positions) stay English, so
saved fighters and exported JSON are unaffected.

- **Боец** (Fighter): spend 40 attribute points and 30 technique points, then pick an archetype, a tap policy and a gi. Import and export as JSON.
- **План** (Plan): up to 10 steps, each with a technique, an optional backup, a condition and a number of tries. Warnings show up under the list.
- **Схватка** (Match): pick an opponent and a seed, then step through the log. Every attempt shows why its chance was what it was.
- **Лаборатория** (Lab): batch runs (1,000 to 50,000 matches), a round-robin matrix, confidence intervals, a position histogram, CSV export and the self-tests.

## Running the engine in Node

The engine lives in `<script id="bjj-engine">` inside `index.html` and never touches the DOM.
`tools/harness.js` extracts it and runs it in Node:

```
node tools/harness.js selftest          # data + engine self-tests
node tools/harness.js match 42 0 1      # one logged match: seed, preset A, preset B
node tools/harness.js matrix 2000       # round robin, matches per pair
node tools/harness.js accept            # every acceptance criterion from the brief
```

## Tuning

Every number lives in data objects at the top of the engine script: `CONFIG`, `POSITIONS`,
`WEIGHTS`, `ACTION_LIST`, `ARCHETYPES`, `PRESET_FIGHTERS` and `PRESET_PLANS`. See `BALANCE.md`
for what was tuned, why, and which rules were added or interpreted.
