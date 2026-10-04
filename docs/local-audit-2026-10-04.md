# Local audit and external-user trial — 2026-10-04

The maintained local browser harness passed the automated scope below after repair.
A synthetic new owner completed intake → plan → fixture approval → build → gameplay
→ replay → package → independent extraction → gameplay again. This is evidence for
the declared single-floor discovery-game workflow, not universal code correctness
or automatic reconstruction of a real user's photographs.

## Source identity and workspace

The session's configured `/Chikanofaka/virtual-reality-modeller` path did not exist.
A related clean local checkout pointed to `virtual-reality-modeller-test`. GitHub's
compare API confirmed its commit **efbebd98695456903532aeea22656846365b5ca4** was
identical to `Chikanofaka/virtual-reality-modeller` public `main` on this audit date.
An isolated local copy was used at `/private/tmp/virtual-reality-modeller-review-20261004` on branch
`audit/external-user-loop`. Its origin now names the requested public repository.
No commit or push was performed. The original checkout was not edited. Unknown
unpublished changes at any other path have not been inspected or overwritten.

## Code and workflow reviewed

- Maintained Python CLI: input inventories, plan semantics, approval invalidation,
  source/asset hashes, navigation validation, immutable builds, local serving and ZIP delivery.
- Browser runtime: planned/Pearl scenes, asset loading, input state, navigation,
  objective state, readiness, one rendering loop, reset, minimap and build identity.
- Schemas, agent entrypoints, new-user intake and requirement-to-evidence handoffs.
- Unit/browser tests, quickstart, standalone launcher and GitHub workflow wiring.
- Blender companion and evaluated-geometry audit. Historical snapshots remain archival;
  they are not alternative maintained browser entrypoints.
- All five vendored Three.js files matched their recorded size and SHA-256. The library
  was not independently re-audited line by line. Historical eleven-ZIP comparison
  evidence was retained; those original archives were not re-collected in this run.

## Repairs

| Finding | Repair and verification |
|---|---|
| Custom games could show messages but only Pearl had completion state | Optional ordered `gameplay` contract, completion text and replay/reset; pure state tests plus real keyboard route completion |
| Imported master GLBs discarded planned furniture interactions | Stable invisible interaction anchors, without duplicate primitive furniture; GLB browser trial passed |
| Goal IDs alone did not prove an interaction was usable | Reject goals with no connected walkable nearest-target approach, including out-of-bounds and coincident shadowed targets |
| Interaction could use a stale nearest target after movement/reset | Recompute target at interaction time and clear transient state on reset |
| Browser target validation required Safari for every owner | Accept a nonempty unique list of supported desktop targets; report the declared targets |
| Malformed planning sections could raise raw attribute errors | Validate section/item shapes before semantic traversal |
| Build pointer could disagree with selected directory identity | Require pointer, directory and build metadata IDs to agree |
| Source/asset changes during copying could produce inconsistent builds | Verify copied assets and recheck the approval immediately before publishing the build; injected race tests |
| Packages omitted validation evidence | Fresh build/plan-bound `validation.json`; optional matching automated `browser-report.json`, explicitly separate from human acceptance |
| ZIP output could mutate its own immutable build or include concurrent edits | Reject output within the build; stage, hash-check and atomically publish the ZIP without overwriting a competing file; injected race tests |
| Old browser smoke certified only Pearl interactions | Exercise custom route movement with W through the real frame/navigation code, early wrong-order interaction, completion and full replay |
| No single command tested the extracted-delivery loop | `scripts/verify_harness.py`, retained logs/reports, private sentinel scan and independent launch of extracted packages; CI now calls this runner |
| Blender 5.2 rejected the archival Eevee enum | Checked `blender/build_pearl.py` compatibility entrypoint selects a supported engine; upstream bytes remain unchanged |

## Executed evidence

Environment: Python 3.12.4, Node 22.22.1, headless installed Chrome
154.0.8037.95 through Playwright 1.62.1, Blender 5.2.2 LTS.

| Check | Result | Evidence |
|---|---|---|
| Original baseline | 33 Python + 13 JavaScript passed | Read-only baseline at source commit; localhost test rerun outside socket-restricted sandbox |
| Final regression suites | 53 Python + 19 JavaScript; zero skipped | `test-results/full-audit-final/logs/02-python-tests.log` and `03-runtime-tests.log` |
| Complete Pearl delivery | Passed original browser, package, extracted launcher and extracted browser | `test-results/full-audit-final/report.json`; build `2e5d7eab89e7f1fe` |
| Complete fresh-user delivery | Passed intake, planning, gameplay, replay, package and extracted browser | Same report; build `094d85b653c77d29` |
| Imported-GLB gameplay | Passed loading, both ordered interactions, wrong-order check and replay with real movement | `test-results/imported-audit/report.json`; build `a014a6be02fb5647` |
| Source stability | No maintained source changed during final whole-harness run | `source.changedDuringRun = []` in report |
| Privacy and identity | Sentinel absent from every ZIP member; stale URLs rejected; no-store headers; exact IDs retained | Whole-harness report, package reports and regression tests |
| Runtime network use | No external page requests observed in browser runs | Browser reports (`externalRequests = []`); browser process background services are outside this assertion |
| Blender companion | PNG, BLEND, GLB produced; evaluated audit and separate reopen audit passed | `test-results/blender-compat/`; 166 meshes, 15,704 triangles |
| Dependency install | Pinned Playwright installed; npm reported zero known vulnerabilities | `package-lock.json`; this is not a complete supply-chain certification |

The first whole-harness attempt exposed a macOS `/var` versus `/private/var` path
comparison in the new race-injection test. The test now resolves paths before
injecting the mutation. The successful final run is `full-audit-final`; the failed
attempt remains under `full-audit-20261004` for traceability.

## Repeat

```sh
npm ci --ignore-scripts
npx playwright install chromium
python3 scripts/verify_harness.py --browser
```

For an existing local Chrome installation, set `BROWSER_EXECUTABLE` to its executable.
Use `--node PATH` if needed. The runner retains a unique evidence directory, does not
silently skip requested browser checks, and fails if tested source changes during
execution. It approves only the bundled synthetic fixture within the test task.

Optional companion:

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python blender/build_pearl.py -- --output output/pearl-companion
```

Use a fresh output directory. This source is an approximate historical companion,
not a replacement for the browser V7 visual scene.

## Remaining boundaries and real-user inputs

- No physical Safari keyboard/compositor walkthrough was performed. Chrome automation
  is not Safari acceptance, and untested browser/OS combinations remain unverified.
- The CI workflow was updated locally but not run on GitHub, because nothing was
  pushed. Its existing action tags resolve at the official repositories:
  [checkout v7](https://github.com/actions/checkout/tree/v7),
  [setup-python v7](https://github.com/actions/setup-python/tree/v7), and
  [setup-node v7](https://github.com/actions/setup-node/tree/v7).
- This is one-floor navigation with proximity interactions. It does not implement
  line-of-sight interaction blocking, physics, stairs, multiplayer, save games or WebXR.
  Reachability uses a sampled grid; actual movement and visuals still need project review.
- Imported geometry does not create collision automatically. Its explicit navigation
  and interaction coordinates must match the authored asset.
- Photos, floor plan, a reliable measured dimension, desired player objective,
  visual expectations and target device are still required for the actual user's game.
  Synthetic facts, confirmation flags and approval cannot be copied as their consent.
- No paid generation, external source-photo upload, deployment or remote publication
  occurred. Hashes detect inconsistent bytes; they are not signed authenticity proofs.

For the next real project, start with the problem definition and delegation table in
[the fresh-user guide](external-user-trial.md). Translate actual evidence into the
plan, present the concrete layout and gameplay for review, then reuse this tested
build-and-delivery loop.
