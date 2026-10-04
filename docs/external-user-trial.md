# Fresh-user acceptance trial

This trial exercises a new project from requirements through a separately extracted
playable package. It uses the synthetic studio in
[`templates/external-user-game.json`](../templates/external-user-game.json) and the
explicit fixture answers in
[`templates/external-user-answers.json`](../templates/external-user-answers.json).
It does not reuse the Pearl project's planning approval or game objectives.

The fixture describes an authored 8 × 6 m studio, a 2.8 m ceiling, a south entrance,
a work desk and a reading chair. These values are test data. No real user's photos,
measurements, source rights or plan approval are asserted. Running this trial under
an authorized repository test task permits a separate approval of the exact
synthetic plan for that test. It does not approve any later real-space project.

## Role-play brief and delegation

The simulated new owner says:

> I want a small desktop discovery game in this synthetic studio. The player
> inspects the work desk, then the reading chair, and sees a completion message.
> I delegate local planning, implementation, verification and packaging to the
> agent within that brief. Use the supplied fixture values and procedural visual
> style. Keep this trial local and identify any unverified browser behavior.

The agent first reads `README.md`, `instructions.md`, and
`skills/virtual-space-mvp-harness/SKILL.md`. It explains that the harness builds a
single-floor, first-person space from an explicit plan and selected assets. It then
turns the brief into the following responsibilities and handoffs:

| Responsibility | Agent work | Evidence or owner decision |
|---|---|---|
| Define the experience | Record the two-object sequence, controls, visual scope and browser targets | This brief and fixture answers; actual users supply their own requirements |
| Interpret evidence | Inventory sources; distinguish authored fixture facts, measurements and assumptions | `sources.json`, `intake.json`, and plan provenance |
| Plan the space | Place rooms, door, furniture, interaction targets and a continuous route | `planning.json`; explain geometry, collision choices and limitations |
| Review the plan | Present the exact plan and review hash | `planning-review.json`; record authorization for this specific test fixture |
| Build and verify | Construct the game, exercise both interactions and reset, check integrity | Immutable build identity and tests of the delivered build |
| Accept and hand off | Record browser observations, package and launch the extracted result | Validation evidence, runnable ZIP and explicit remaining limits |
| Iterate | Reproduce a reported defect against its build, fix and rerun relevant checks | New build identity, regression result and retained previous playable |

A fresh agent must perform the interpretation and planning work. The six intake
answers are not an image-understanding or automatic architecture-reconstruction
service. In a real project, request the available photos/plan and one reliable
measurement, mark the entrance, and establish the visitor's goal. Continue useful
draft work while unknowns remain. Present the resulting real-space plan for its own
decision; do not copy the fixture's confirmation flags as user approval.

## Requirements and acceptance evidence

| Requirement | Contract or artifact | Check before handoff |
|---|---|---|
| Reproducible synthetic inputs | Fixture JSON, ingested source hashes and provenance | Source bytes match inventory; evidence is labelled synthetic |
| Correct entrance and route | Spawn `(0, 1.65, 2.2)`, south door and `desk-chair-return` route | Radius-clear route; entry-to-desk-to-chair-to-entry can be walked |
| Desk blocks movement | Explicit desk blocker and wall segments | Player cannot cross the desk or solid walls; clear approaches remain usable |
| First objective: desk | `gameplay.objectives[0].targetId = work-desk` | Nearby E shows desk feedback and advances to the chair |
| Second objective: chair | `gameplay.objectives[1].targetId = reading-chair` | Nearby E after the desk shows the exact completion message |
| Sequence cannot be skipped | Ordered objectives | Chair before desk does not complete or advance the first objective |
| Replay works | Reset action | R returns to the entrance and restores the first objective; repeat completes |
| Desktop controls work | Runtime browser/input contract | WASD, drag-look, minimap, focus recovery and quality change tested on the same build |
| Approval follows the inputs | Plan review and approval hash | Plan, answers, source or selected-asset edits invalidate the old lock |
| Private evidence stays private | Explicit asset selection; this fixture selects no assets | Extracted ZIP contains no raw uploads or private source sentinel |
| Delivery is self-contained | Playable ZIP, identity and launcher | Extract elsewhere, launch offline, compare badge/build ID and validation evidence |

The nearby approach points are `(0, -2)` for the desk and `(2, 1)` for the chair.
Both are in the declared walkthrough route and outside the desk blocker. The chair
is decorative and does not collide. Returning to the entrance checks route
continuity; completion is triggered by the ordered interactions, not by that return.
Visual acceptance for this fixture is a simple procedural studio, not photographic
reconstruction.

## Run the local trial

Run from the repository root with Python 3.10+. Use a new project directory for each
independent run; builds and package outputs are intentionally not overwritten.

```sh
python3 scripts/harness.py init projects/external-user-trial
python3 scripts/harness.py ingest projects/external-user-trial templates/external-user-game.json
python3 scripts/harness.py interrogate projects/external-user-trial
python3 scripts/harness.py interrogate projects/external-user-trial --answers templates/external-user-answers.json
python3 scripts/harness.py plan projects/external-user-trial --input templates/external-user-game.json
```

Inspect `projects/external-user-trial/planning.json` and
`projects/external-user-trial/planning-review.json`. Record that the exact synthetic
fixture is authorized for this test run. For a real user plan, obtain or record that
user's decision on the concrete revision before the next command.

```sh
python3 scripts/harness.py approve projects/external-user-trial --accept
python3 scripts/harness.py build projects/external-user-trial
python3 scripts/harness.py validate projects/external-user-trial --build
python3 scripts/harness.py play projects/external-user-trial --browser chrome
```

Follow the printed URL and compare the build badge. Enter, approach the chair and
press E first to check ordering. Walk to the desk approach point and press E; then
walk to the chair and press E. Confirm the completion text, return to the entrance,
press R, and complete the sequence again. Check continuous walking/dragging and
focus recovery. Stop the local server with Ctrl+C after inspection.

Run automated verification with Node 20+ and the optional browser dependencies
described in the README:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/runtime*.mjs
SMOKE_OUTPUT=test-results/external-user-trial python3 scripts/run_browser_smoke.py --project projects/external-user-trial
```

The wrapper serves the selected project's current build and closes its server after
testing. It writes this trial's report to `test-results/external-user-trial/report.json`.
Preserve that report with the matching build ID. Automation and native
browser acceptance are separate evidence. A green test run alone does not establish
physical Safari key delivery or macOS compositor behavior. Record those observations
only when actually performed, using the checks in
[`browser-validation.md`](browser-validation.md) with this fixture's route and targets.

```sh
python3 scripts/harness.py package projects/external-user-trial --browser-report test-results/external-user-trial/report.json --output dist/external-user-trial-playable.zip
python3 -m zipfile -e dist/external-user-trial-playable.zip dist/external-user-trial-unpacked
python3 dist/external-user-trial-unpacked/launch.py --no-open
```

Open the printed extracted-package URL and repeat the gameplay checks. Verify that
runtime assets load without external network access and that the badge matches the
tested build. Preserve the ZIP checksum, automated results and any actual native
browser observations alongside the release. Report unperformed checks as unverified.
Listing these commands documents a reproducible procedure; it is not a claim that
the current checkout has executed or passed them.

## Boundaries for a real photo-based project

Photos and walkthrough video help an agent understand appearance and layout. They do
not by themselves establish scale, hidden geometry, navigation or source rights.
The agent must ground or explicitly label geometry assumptions and show the proposed
layout before approval. High-detail custom appearance requires authored procedural
geometry or supplied self-contained GLB assets plus visual review.

This trial covers ordered proximity interactions, movement and reset. It does not
demonstrate physics, stairs, multiplayer, persistent saves, headsets or arbitrary
photo-to-3D reconstruction. Changing the task to require any of those needs a new
scope and corresponding implementation and acceptance evidence. Paid generation,
external upload and publication require the relevant authorization; this local trial
does not perform them.

Interaction selection uses horizontal proximity to the nearest target. It does not
check viewing direction, line of sight, walls between player and target, or vertical
occlusion. Navigation blockers stop movement; they do not prevent an interaction
through a wall. Arrange targets accordingly for this MVP, and add explicit visibility
rules and tests if the real game requires them.
