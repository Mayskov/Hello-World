# Balance notes

Everything below comes from the Node harness: `node tools/harness.js accept`, plus the
scratch analyses described here. Numbers are win rates from batches of 1,000 to 24,000 matches.
At that size a 95% interval is roughly ±1 percentage point.

## Where it landed

| Criterion | Target | Result |
|---|---|---|
| Clearly better plan and fighter vs clearly worse | 65–75% | **66.9%** |
| Best preset against the round-robin field | ≤ 60% | **56.6%** (wrestler) |
| Pressure passing beats de la Riva | 55–65% | **56.4%** |
| Flexible closed guard beats pressure passing | 55–65% | **55.6%** |
| Wrestling beats the closed-guard puller | 55–65% | **56.4%** |
| Wrestling beats the de la Riva puller | 55–65% | **55.5%** |
| Every position visited in 1,000 matches | all | all (spider guard is rarest at 0.7% of ticks) |
| No position above 35% of ticks | ≤ 35% | 17.0% (closed guard) |
| Same plan, different builds | different | 49.3% vs 37.6% against the field |
| 10,000 matches | < 15 s | about 2.1 s in Node, 2.3 s in Chromium with the page responsive |
| Self-tests | pass | 14/14 |

**Honest caveat:** the four rock-paper-scissors edges pass, but only just. They sit at 55–57%
across independent seeds, never near the middle of the band. Pushing any of them higher pushes
the wrestler past the 60% field cap: it already beats both guard players and the pressure passer
(about 58%). A fifth preset that beats wrestlers would open up room. See the proposals below.

Round-robin matrix (row beats column, 4,000 matches per pair):

|                     | Pressure | Armbar | De la Riva | Wrestler | vs field |
|---------------------|---------:|-------:|-----------:|---------:|---------:|
| Pressure passer     |        – |  44.4% |      56.4% |    42.2% |    47.7% |
| Closed-guard armbar |    55.6% |      – |      68.0% |    43.6% |    55.7% |
| De la Riva back take|    43.6% |  32.0% |          – |    44.5% |    40.0% |
| Wrestler            |    57.8% |  56.4% |      55.5% |        – |    56.6% |

## The three questions

**1. Does writing a plan feel like a decision?** Mostly yes. The same fighter with its preset plan
against the field, compared with an empty plan (archetype instinct only):

| Fighter | With plan | No plan | Plan is worth |
|---|---:|---:|---:|
| Pressure passer | 48.9% | 33.9% | +15 pts |
| Closed-guard armbar | 54.5% | 30.4% | +24 pts |
| De la Riva back take | 41.4% | 24.4% | +17 pts |
| Wrestler | 54.4% | 48.4% | +6 pts |

The wrestler gains least because "shoot a takedown" is both its instinct and its plan. Before
tuning, instinct was as good as any plan (the "worse" fixture beat the "better" one 54–46).
That's why the instinct penalty below exists.

Plan *structure* matters as well as the steps. Two examples that turned up in logs:
- The armbar plan originally took the sleeve grip before breaking posture. That gave the passer a
  free tick to knee through while posture was intact. Swapping the two steps changed the matchup.
- "Armbar, backup: break posture" beats "armbar, backup: triangle". When posture is restored the
  armbar is illegal, and without that backup the pointer moves forward to the sweep instead of
  re-breaking posture.

**2. Can one plan dominate?** Not among the presets (max 56.6%). The Lab flags anything above 60%.
Custom plans weren't searched exhaustively. That's the obvious next Lab feature.

**3. Do attributes and archetypes matter?** Yes. The pressure plan on a pressure build wins 49.3%
against the field; the same plan on a guard build wins 37.6%. Archetype modifiers set the shape of
the rock-paper-scissors triangle. See "What changed" for the wrestler's riding bonuses.

## New rules and interpretations (please review)

The brief asked me to report conflicts rather than silently redesign. These are the places where I
added a rule or had to pick an interpretation. Each is a `CONFIG` value or a data field, so it can
be switched off.

1. **Instinct penalty** (`CONFIG.chance.instinctPenalty = 0.10`, new). An action chosen by archetype
   default behaviour, rather than by a plan step, gets −10%. Without it, a fighter with a bad plan
   and good instincts beat a fighter with a good plan, so the plan didn't matter.
2. **Queued counters make reversals likelier** (`CONFIG.outcome.counterReversal = 0.15`, new). The
   brief says a reversal is "the defender's counter lands instead" and that the losing intent
   "becomes a defensive reaction". I made a queued, legal, position-changing counter (a sweep against
   a pass, a snap-down against a shot) add 15% reversal chance. Without it, the wrestler beat the
   pressure passer about 85% on repeated 2-point takedowns, because a sprawl had no way to pay off.
3. **Initiative noise** (`CONFIG.chance.initiativeNoise = 0.4`). The brief says "the one with the
   better modified chance acts". Read strictly, a bottom player's 30% escape never happens while the
   top player keeps trying a 45% transition. Each side's initiative is its chance plus a uniform
   random 0–0.4; set it to 0 for the strict rule. The same contest also decides between a
   position change and a grip (the brief left that case open).
4. **Reversals only follow failed position changes or submissions.** An early build let a failed
   grip break trigger a full sweep for the other side. That was a bug.
5. **Advantages go to the defender on a close miss**, as the brief says. Real IBJJF rules give the
   attacker the advantage for a near-sweep or near-submission. Worth deciding which you want.
6. **The tap policy is currently dominated by `never_tap`.** Resisting and failing ends the match
   exactly like tapping, and resisting has no other cost to the defender, so never tapping can only
   help your win rate. For the policy to be a real decision, resisting needs a downside, such as a
   carried injury in a tournament or bracket mode, or a stamina cost on success.
7. **Plan pointer semantics.** Each tick the engine tries steps from the pointer to the end, then
   wraps round to the earlier steps (so a plan can pick itself up after a scramble). Success on
   step *k* sets the pointer to *k*+1. Using up a step's tries at the pointer moves the pointer on.
   Try counters reset whenever the position changes.
8. **Data additions to the action shape:** `blockedBy` (opponent grips or flags that make an action
   illegal, e.g. the stack pass is blocked while they hold your sleeve), `removes` (grips or flags
   stripped from the opponent), `partialGrants` (grips a close miss still gives you), and `from` may
   be a list. On any position change all grips and flags are cleared, then the action's `grants`
   apply.
9. **Stamina cost scale** (`CONFIG.stamina.costScale = 0.6`, new, a pure tuning knob). At 1.0 a
   fighter attacking every tick ran out of stamina by about tick 22 and every match ended in a
   fatigue slog.

## What changed and why (tuning pass)

Initial state: the preset triangle ran almost exactly backwards (pressure beat armbar, armbar beat
wrestler, wrestler beat pressure 85%), the armbar plan was dominant at 64%, and better-vs-worse was
46%.

- `attrScale` 0.04 → **0.025**. Specialists stacked +16% from stats alone, and stat gaps drowned
  out plans and archetypes. This was the biggest single improvement.
- **Guard pulls were near-automatic** (closed guard 70% base). Lowered to 55% (open), 55%
  (closed) and 35% (de la Riva). Pulls are now defended by takedown skill, explosiveness and base
  (`pullDef`), so a wrestler can deny them.
- **Submissions** scaled to 75% of their original base chance and `resistBase` 0.40 → 0.45. Mount
  and back finishes were landing about 45% per attempt against balanced defenders.
- **Wrestler identity = riding.** `defend.transition` +8% (hard to re-guard against or scramble
  away from), `defend.posture` +12%, takedown attack +12%. The preset wrestler moved points from
  passing into escapes and cardio. With passing 6 it smashed the pressure passer; with passing 4
  it rides rather than passes.
- **Pressure passer identity = heavy.** Body weight now counts in sprawling (`takedownDef` includes
  pressure), `defend.takedown` +10% and `defend.escape` +8%. The snap-down is recategorised as a
  takedown (it was being crushed by the wrestler's transition defence) and uses pressure and grips.
- **Flexible guard vs pressure**: the knee-through is defended by flexibility (`kneeThroughDef`),
  and guard players get +9% pass defence and +7% posture breaking.
- **Killing the de la Riva hook** now uses pressure (`dlr_kill_hook` uses `pressurePassAtt`), so
  pressure passing beats open guard, as the brief intends.
- **Pins were too sticky**: mount, knee-on-belly, side-control and back escapes were raised. The
  bottom fighter was losing whole matches under one pin.
- **Preset plans rewritten** so each has an answer to its bad matchups. The pressure plan gets a
  kill-the-hook backup and a stand-up step. The wrestler plan gets posture and grip denial in the
  guard before any pass attempt. The armbar plan gets posture-first ordering and "break posture" as
  the armbar's backup.
- `reactionBonus` 0.05 → 0.09 and `initiativeNoise` 0.3 → 0.4 came out of the search below.

**Method.** The first changes were made by hand: condensed match stories and per-action attempt
and success counts showed what was actually happening. After that, a coordinate-descent search over
39 named knobs (CONFIG values, archetype modifiers, a set of base chances) was scored against the
acceptance bands, with fixed seeds so the score is deterministic. A search on one seed overfitted
by 2–3 points, so the final pass scored the average of two seeds and was checked on held-out seeds
at 4,000–5,000 matches per pair.

## Known gaps and proposals

- **The triangle edges sit at the low end of their band.** Proposal: add a fifth preset, a
  submission hunter with a spider guard and a standing guillotine that punishes shots. It would
  give the wrestler a counter, so the triangle edges can widen without breaking the 60% cap. It
  would also make spider guard (currently 0.7% of ticks) a real destination.
- **De la Riva is the weakest preset (40%).** It's allowed by the criteria, but it's the first thing to
  improve once a fifth preset exists.
- **About 19% of matches end with points level** (decided on advantages, stamina or a coin flip).
  That comes from riding-heavy play. If it matters, consider stalling penalties or IBJJF-style
  advantages for near-misses.
- **Plans rarely run to completion** (6–16% of matches). The "plan stalls" column in the Lab shows
  most plans stop progressing between about 1:50 and 2:50. That's realistic, but it also means late plan steps
  are rarely reached, so plan length is a weaker decision than plan order.

## Game mode (progression and ladder)

- Starting builds: 28 attribute and 18 technique points, all within the white-belt cap of 6.
- Ladder opponents grow from 21/12 points at rung 1 to about 44/31 at rung 15 (`GAME.opponent`), spread by the
  preset builds' proportions and capped by the rung's belt.
- A fresh starter wins about 56–69% against rungs 1–2; after that training is needed. A player grown to the same point
  totals as a rung wins roughly 40–60% against it (35–70% depending on the archetype pair).
- Training pace: about 1.5 stat levels per 6-hour session, so the full ladder needs roughly 15–20 sessions.

Open questions:
- **Wrestler is the strongest starter** in game mode (55–70% at matched level), pressure passer the weakest (40–53%).
- **Unlimited attempts**: you can re-fight a rung immediately after a loss, so luck can be ground out. A cooldown or
  an energy system would fix it if that matters.
- **Recommendations** use 200 simulations per variant with common seeds; gains under 3% are hidden as noise.
