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

## Game mode

The page opens in game mode («Путь к чёрному поясу»); the tabs above are behind the «⚙️ Лаборатория» button.

- **Боец**: your fighter card, attribute radar, technique levels and career history.
- **Тренировка**: one real-time session at a time (4–8 hours) that adds experience to 1–2 stats. 100 xp = +1 level, capped by
  belt (white 6 … black 10). A test panel speeds time up (×60, ×600, ×3600) or finishes the session instantly.
- **Стиль**: four cards (standing, top, bottom, finish) plus a risk level. The cards compile into an ordinary 10-step plan,
  so the engine and its balance are unchanged. Cards unlock as stats grow.
- **Лестница**: 15 opponents, belt promotions every 3 rungs. No fights during training.
- **Разбор** after each match: a win-chance graph, the turning point with its cause (which grip made it possible and
  whether you had an answer), plan gaps, and recommendations checked by re-simulating the matchup with +1 to each stat
  and with each alternative card.

Game state is stored in `localStorage` under `bjj-game.v1`.

## Running the engine in Node

The engine lives in `<script id="bjj-engine">` inside `index.html` and never touches the DOM.
`tools/harness.js` extracts it and runs it in Node:

```
node tools/harness.js selftest          # data + engine self-tests
node tools/harness.js match 42 0 1      # one logged match: seed, preset A, preset B
node tools/harness.js matrix 2000       # round robin, matches per pair
node tools/harness.js accept            # every acceptance criterion from the brief
node tools/harness.js archetypes 3      # game-mode archetype balance (best build vs best build, ~3 min)
```

## Tuning

Every number lives in data objects at the top of the engine script: `CONFIG`, `POSITIONS`,
`WEIGHTS`, `ACTION_LIST`, `ARCHETYPES`, `PRESET_FIGHTERS` and `PRESET_PLANS`. See `BALANCE.md`
for what was tuned, why, and which rules were added or interpreted.
