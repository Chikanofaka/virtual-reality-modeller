# Apartment interaction preparation — 2026-10-05

This is a historical checkpoint before V1 acceptance. For the later completed
apartment and its verification, see [the flagship case](../examples/midtown-apartment/README.md).

At this checkpoint the real apartment was still at V1 layout review. No owner acceptance, model build
or playable delivery for that apartment has been recorded. The work below adds
reusable runtime behavior and verifies it on synthetic fixtures only.

## Implemented

- Optional horizontal interaction occlusion against declared structural segments,
  consistently applied to Python target reachability and browser target selection.
- Named-mesh emissive effects that run only when the current objective advances.
  Materials are isolated from other objects sharing the imported material.
- Reset restores the original material values as well as objective progress.
  Wrong-order and repeated interactions do not change these visual states.
- Invalid scene bindings block entry instead of silently omitting effects.

The contract and limits are in [interaction-effects.md](interaction-effects.md).
The actual apartment still needs its mesh names, materials and navigation wired
to these capabilities after layout acceptance.

## Executed verification

Equivalent command for the recorded run, with the account-specific Node path
replaced by `node` from PATH:

```sh
BROWSER_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' python3 scripts/verify_harness.py --browser --node node --output test-results/interaction-preparation-20261005
```

Result: **passed**, 60 Python tests and 35 JavaScript tests, zero skipped. The
source manifest did not change during the run. Browser execution used local
Chrome 154.0.8037.95 through Playwright's Chromium driver.

| Synthetic project | Build ID | Original browser | Extracted standalone browser |
|---|---|---|---|
| Pearl | `2d23b8f3e631e893` | Passed | Passed |
| Discovery studio | `ea14eca5d17395d8` | Passed | Passed |
| Imported interaction fixture | `2345236ac2ac937a` | Passed | Passed |

The imported fixture is three cuboids, deliberately representing two effect
targets and a wall, not the user's furnished apartment. Its tests walked using
keyboard input, attempted E within proximity but across the wall, exercised
wrong-order input, completed both effects with changes to captured canvas pixels,
reset their material values and completed the game again. Both the original and
extracted builds performed the full replay. Automated steering selected yaw;
translation followed the normal frame loop and collision logic.

Each extracted package was launched with its own `launch.py`. The harness checked
build identity, stale-URL rejection, no-store responses, private-input exclusion
and absence of external browser requests, then stopped only its owned servers.

Runtime SHA-256:
`97f61f2f86e52ef2316f11ff13309e6ef98319bcdc2e548b608cc54025e9dc14`

Local evidence:

- `test-results/interaction-preparation-20261005/report.json`
- `test-results/interaction-preparation-20261005/browser/interaction-effects/report.json`
- `test-results/interaction-preparation-20261005/browser/interaction-effects-extracted/report.json`
- The corresponding browser directories include screenshots; `logs/` preserves
  command output, and `packages/` contains the tested synthetic ZIPs.

These checks do not certify a hardware keyboard, Safari, a visible macOS window
compositor, the furnished apartment's appearance, or actual building dimensions.
Material emission changes the object itself; it does not introduce a new light
source or full 3D optical occlusion.

## Project continuity

The V1 review files still match their saved hashes. The real project's three
provenance confirmations remain false, with no `approval.json` or
`current-build.json`. Its readiness note is saved at
`projects/photo-game-intake/evidence/runtime-preparation.json`. This preserves the
user's requested layout-confirmation step while completing independent runtime
preparation. No GitHub push, publication, paid generation or external upload was
performed.
