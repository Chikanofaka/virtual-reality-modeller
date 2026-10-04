# Fresh-agent onboarding follow-up — 2026-10-05

A separate agent reviewed repository entrypoints without the previous chat history.
The core journey is usable by a new owner. It found remaining wording that still
imposed the Pearl room's central portal and asked the owner to supply navigation
polygons. Those findings, the earlier mandatory-Safari wording, and the links to
historical evidence are now corrected.

## Changes since the October 4 delivery

- Intake asks for observed dimensions, entrance, destinations, obstacles, player
  goals and target devices/browsers. The agent derives and tests geometry.
- The onboarding guide allows each owner to choose target browsers.
- Journey and native-browser checklists use the current project's route, openings
  and game completion. Pearl's central portal is explicitly example-specific.
- The original release-validation page remains historical evidence, with links to
  the subsequent audit and this follow-up. It is not presented as the current build.
- A real-project intake workspace was initialized locally at
  `projects/photo-game-intake`. It has a brief, unresolved requirements, delegation
  handoffs, empty evidence/answer ledgers and an unconfirmed planning template.
  No photos, dimensions, gameplay specifics or user approval were invented. This
  ignored project directory is separate from the distributable source bundle.

## Verification of this revision

The whole-harness runner completed with **53 Python and
19 JavaScript tests**, zero skipped, and browser checks enabled.
It recorded no source changes during execution. The browser runtime hash remains
identical to the October 4 repaired runtime; this follow-up changes onboarding
wording and documentation.

| Fixture | Build ID | Original and independently extracted browser checks |
|---|---|---|
| Pearl | `71b53e25c80805f8` | Passed |
| External-user discovery game | `ccb1e2b7fabb4a7a` | Passed |

Machine evidence and logs: `test-results/full-audit-20261005/report.json` and its
adjacent `logs/`, `browser/` and `packages/` directories. The new-user run includes
ordered interactions, an out-of-order attempt, reset/replay, standalone serving,
identity checks and exclusion of the synthetic private-upload sentinel.

The intake workspace was separately checked: zero sources, zero recorded answers,
no approval, no build, and scale/entrance/layout confirmation flags all false.
The earlier [code audit](local-audit-2026-10-04.md) contains the runtime, delivery,
GLB and Blender findings and their specific evidence.

## Scope and handoff

Work remains local on `audit/external-user-loop` in the isolated checkout because
the configured repository path is still absent. This agent did not push to GitHub. A path to
any separate working tree is needed to inspect its unpublished changes.

The next real-project step needs the source-photo/plan location, a known dimension
(or a statement that it is unknown), and the player's intended task/device.
The sample desk/chair mission is a synthetic acceptance test, not the user's game
specification. Physical Safari acceptance and real-photo fidelity remain unverified.

The October 5 patch is cumulative from base commit
`efbebd98695456903532aeea22656846365b5ca4`; it is an alternative to the complete
updated source ZIP. Run `git apply --check` against the target checkout before
applying it. The previous October 4 artifacts are retained unchanged.

The checkout now contains local commit `7937639` (`auditted-version1`), detected
during artifact verification and preserved. `local-audit-20261005.patch` contains
all changes from the original `efbebd9` base. For a checkout already at `7937639`,
use `onboarding-7937639-20261005.patch` instead. This follow-up did not create or
rewrite that commit.
