# Virtual Space MVP Harness

Turn floor-plan evidence into a reviewed planning pack, then build, test and package
a first-person 3D space. The included **Pearl Office** example preserves the detailed
procedural scene from the supplied Safari WASD V7 package. Its navigation, input,
rendering and build identity now have separate responsibilities and regression tests.

**Local-first · Safari-priority · WASD + drag look · no API key · no build service**

This is an engineering harness and reusable agent skill, not automatic reconstruction
of an arbitrary photograph. New projects need measured dimensions and a reviewed
layout. The generic procedural adapter creates a spatial scaffold; matching a custom
high-detail visual target still requires authored scene/assets and visual review.
Approved, self-contained GLB models can be added or used as the primary scene;
see [detailed assets](docs/assets.md).

## Play the preserved Pearl scene

Install Python **3.10+**. Open a terminal in this repository, then run:

```sh
python3 scripts/quickstart.py --browser safari
```

On macOS, `RUN_SAFARI.command` and `RUN_CHROME.command` provide the same workflow.
If Finder refuses to open a downloaded command file, run it explicitly:

```sh
bash RUN_SAFARI.command
```

The launcher builds the bundled approved example, verifies it, chooses an available
loopback port, and opens the exact URL. Keep the terminal open; stop with Ctrl+C.
No npm install, CDN, account, Blender, or paid generation is needed to play Pearl.
Do not use `file://` or an old bookmarked localhost URL. Read the build badge before
reporting a fault. The launcher never terminates an unrelated process.

| Control | Action |
|---|---|
| W / A / S / D | Walk; diagonal speed is normalized |
| Hold mouse and drag | Look; no pointer lock required |
| Arrow keys | Turn/look without a mouse |
| Shift | Sprint |
| E | Interact nearby |
| M | Toggle minimap |
| R | Reset to the approved entrance |
| Q | Change rendering quality |
| On-screen W/A/S/D | Diagnose keyboard delivery using the same movement layer |

## Build your own space

```sh
python3 scripts/harness.py init projects/my-space
python3 scripts/harness.py ingest projects/my-space /path/to/floor-plan.png /path/to/photos.zip
python3 scripts/harness.py interrogate projects/my-space
python3 scripts/harness.py interrogate projects/my-space --answers /path/to/answers.json
# Repeat questions as needed; fill a measured planning.json using templates/.
python3 scripts/harness.py plan projects/my-space --input /path/to/planning.json
# Review the exact plan and planning-review.json before approving it.
python3 scripts/harness.py approve projects/my-space --accept
python3 scripts/harness.py build projects/my-space
python3 scripts/harness.py validate projects/my-space --build
python3 scripts/harness.py play projects/my-space --browser safari
python3 scripts/harness.py package projects/my-space --output dist/my-space-playable.zip
```

The playable ZIP has a standalone `launch.py`. Extract it and run `python3 launch.py`.
Raw uploads stay private; only explicitly selected assets enter the playable package.
Each package includes fresh `validation.json` for its exact build. To retain an
automated browser report, pass `package --browser-report PATH`; mismatched or failed
reports are rejected, and supplied automation remains separate from human acceptance.
Changed plans, answers or source bytes invalidate the approval. Builds are immutable;
rebuilding requires an actual change. The CLI's `play` and `package` commands use
the current build for the currently locked plan.

For rollback, retain a previously verified playable ZIP. Extract it into a separate
folder and run its own `python3 launch.py`. That launcher verifies the package,
chooses a fresh port and opens the URL for that exact build identity. Check the badge
before comparing versions. Project build directories are retained as history, but
the CLI has no old-build selector. To resume development on an older plan, restore
it and its inputs into a separate project workspace, review and approve it again,
then build using the current runtime.

The onboarding journey awards Surveyor, Pathfinder, Architect, Set designer,
Navigator and Pilot badges. It asks two questions per round and reports structural
gaps. A badge is progress feedback, not proof that a measurement is correct.
See [onboarding](docs/onboarding.md), [user journey](docs/user-journey.md),
[prompt patterns](docs/prompt-patterns.md) and [schemas](schemas/).

## Create a custom discovery game

Procedural and imported-GLB plans can declare `gameplay.objectives` as an ordered
list of `{id, label, targetId}` entries, plus a `completionMessage`. Each target ID
references furniture with an `interaction`. E advances only the current objective;
R resets the game. Imported scenes retain these interaction anchors without adding
duplicate primitive furniture. Planning rejects targets with no reachable place
from which the runtime can select them. Interactions use horizontal proximity;
line of sight and vertical occlusion are not modeled.

Follow the [fresh-user trial](docs/external-user-trial.md) for a complete synthetic
studio example, including requirements, delegation, intake, approval, movement,
ordered objectives, replay and independently extracted delivery. The test fixture
is not approval or reconstruction of a real user's photos. Choose the desktop
browsers appropriate to your project; Safari is the Pearl baseline target, not a
mandatory target for every new plan.

## What's included

```text
runtime/                 Detailed Pearl scene, generic adapter, input, nav, renderer
  vendor/                Original Three.js r180 modules and MIT license
scripts/                 CLI, launch and packaging helpers
schemas/                 Planning/build contracts
templates/               Intake and planning examples
prompts/                 Agent prompt patterns and review stages
skills/                  Portable skill entry point
plugin.json              Agent Plugins 1.0 skills-only package manifest
instructions.md          Agent operating contract
examples/pearl-office/   Planning pack, selected original V7 sources, six plan images
blender/                 Original companion builder and evaluated-geometry audit
tests/                   CLI, navigation/input and browser smoke tests
docs/                    Architecture, risk register, journey, version diffs/evidence
```

Use this entire repository as a local skills-only plugin package. The canonical
skill is [skills/virtual-space-mvp-harness/SKILL.md](skills/virtual-space-mvp-harness/SKILL.md).
Installation is host-specific; this source package has not been uploaded, installed
into an account or submitted to a plugin directory. No fictional MCP endpoint is
required. A coding agent can also read [instructions.md](instructions.md) directly.

## What the evolution taught us

Eleven original ZIPs were inventoried and hashed, including six plan images and ten
game packages. Archive names before V3 describe branches rather than a clean numbered
V1→V7 chain. [Version evolution](docs/version-evolution.md) separates code evidence,
user observations and historical assistant hypotheses. Only five recent conversation
turns were available; earlier prompts are not reconstructed as quotations.

- A visually clear corridor can be closed by overlapping furniture colliders.
  Define navigation explicitly and verify connected routes with player clearance.
- Faster collision checks cannot repair disconnected topology. Sliding/substeps
  address edge motion; neither replaces a usable doorway.
- Pointer-lock changes, event-driven rendering and forced presentation calls are
  not universal browser fixes. Buffer input and keep a single frame owner.
- Test key delivery, normalized action, movement and visible presentation separately.
  Safari code/key/legacy fallback, canvas focus and state clearing are all retained.
- A familiar port can serve an old build. Verify build identity and actual port;
  use immutable assets and no-store responses instead of killing whatever owns a port.
- V7 still contained an undefined console interactable and a reflected base-floor
  footprint. Both are fixed in the maintained scene; the original remains available.

## Verification and support

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/runtime*.mjs
```

Run the complete local workflow, including new-user onboarding, private-upload
exclusion, packaging and standalone extraction checks:

```sh
python3 scripts/verify_harness.py
```

With Playwright installed, require real browser checks of both original and
extracted builds:

```sh
python3 scripts/verify_harness.py --browser
```

Each invocation keeps its logs, exact source/build hashes, reports, screenshots and
playable ZIPs in a new `test-results/full-harness-*` directory. Requested browser
checks fail the run if unavailable. Omit `--browser` only for structural/CLI testing;
that result explicitly leaves browser behavior unverified. Use `--node PATH` when
Node is installed outside PATH, and `BROWSER_EXECUTABLE` for local Chrome.
The optional [Blender companion](blender/README.md) has its own compatible build and
geometry audit; it is not the browser scene's visual equivalent.

Node **20+** is needed only for JavaScript tests. The optional browser smoke test
uses Playwright (`npm ci --ignore-scripts`; install its Chromium browser
or set `BROWSER_EXECUTABLE` to local Chrome):

```sh
node tests/browser-smoke.mjs 'http://127.0.0.1:PORT/?build=BUILD_ID'
```

See [browser validation](docs/browser-validation.md) and
[validation report](docs/validation-report.md) for what was actually tested.

| Platform | Support scope |
|---|---|
| macOS Safari | Primary manual target; drag-look and keyboard fallback; WebGL required |
| macOS Chrome | Secondary target; same scene, controls and diagnostics |
| Other desktop OS/browser | Python CLI is portable; one-click `.command` launchers are macOS-specific |
| Mobile/headsets | Touch pad is diagnostic; no mobile UX or WebXR certification |

Known limits: one floor and a 2D navigation union; no stairs or physics simulation.
Pearl intentionally keeps the V7 permissive treatment of furniture/room partitions:
only declared barriers collide. The original plan images have scale/label ambiguities;
the example uses the V7 authored coordinates, not a certified building survey. Custom
GLB imports require embedded textures/buffers and explicit placement; Draco, meshopt
and KTX2 compression need decoders that are not included in this release.
The original Blender companion differs from the browser scene and is not a fidelity
replacement. No test suite can certify every browser/GPU compositor combination.

## Publish to GitHub

Review [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) first: new harness code is MIT,
Three.js is MIT, and the owner needs to state redistribution rights for the supplied
historical Pearl sources/images. The original ZIPs contain no license declaration.
Review content before choosing public visibility. No remote publication is performed
by this repository's launch/build/package commands.

After extracting, inspect `git status`. If Git metadata was not included, initialize
and commit with your own configured author identity:

```sh
git init -b main
git add .
git commit -m "Initial Virtual Space MVP Harness"
```

Create an empty GitHub repository, then add its real URL and push when you are ready:

```sh
git remote add origin https://github.com/YOUR_ACCOUNT/virtual-space-mvp-harness.git
git push -u origin main
```

For changes, read [CONTRIBUTING.md](CONTRIBUTING.md). Keep the evidence trail and
test the actual build being delivered.
