# Browser acceptance

Record OS, browser version, build hash, actual port, viewport and quality mode.
For the recovered Pearl example, Safari on macOS is the primary manual target
because that browser rendered drag motion smoothly in the supplied user observations.
For a new project, use its declared `runtime.browsers` and its own approved route
and objectives. This is a test priority, not a
claim that every Safari/GPU combination is certified. Chromium automation is not
Chrome compositor parity; Playwright WebKit is not installed Safari.

| Check | Action | Pass evidence |
|---|---|---|
| Identity | Open the launcher URL | Badge/hash/port agree with selected build |
| Load | Enter the tour | Scene ready; no console errors or missing assets |
| Physical input | Hold W, A, S, D individually | Raw event and normalized action appear; position changes |
| Virtual input | Hold the on-screen pad | Position changes using the same movement layer |
| Presentation | Drag continuously while walking | Visible intermediate views, not just changing numbers |
| Focus recovery | Switch away with a key held, then return | No stuck movement; click canvas restores input |
| Pointer recovery | Drag outside, release/cancel, resume | No stuck drag or virtual button |
| Navigation | Walk the approved route through required destinations and openings, then return | No artificial dead zones; declared barriers stop movement |
| Interaction | Approach this plan's targets; press E in order and try an out-of-order target | Expected feedback, ordered progression, completion, and successful replay after R |
| Minimap | Walk and toggle M | Position matches world geometry; visibility changes |
| Quality | Toggle Q and resize | Scene detail retained; no duplicate render loop |
| Stale build | Change expected build in URL | Clear error, not an apparently valid old tour |
| Offline | Disable external network after package extraction | Local runtime and dependencies still load |

Pearl's example route is entry → clockwise loop → portal → console, with
reception, wine and console interactions. It is not a route requirement for other
spaces. The [fresh-user trial](external-user-trial.md) uses a desk and chair instead.

Troubleshoot in this order: identity → event delivery → normalized held keys →
simulation displacement → navigation rejection → render calls → visible presentation.
If the pad moves and hardware keys do not, focus/event delivery is implicated. If
both produce held actions but no displacement, inspect navigation and the simulation.
If coordinates move but the displayed view freezes, inspect rendering/presentation.

Run `node tests/browser-smoke.mjs URL` when Playwright and its browser are available.
Use `BROWSER_EXECUTABLE` for a locally installed Chrome. The script must fail on
page errors and check displacement/drag, rather than merely loading the page.
Keep hardware Safari acceptance as a separately reported manual result.

Consult [MDN's code property documentation](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code)
when adapting keyboard mappings and [Three.js documentation](https://threejs.org/docs/)
when changing the pinned renderer. APIs in the bundled r180 files are the build's
actual dependency; current web docs may describe later versions.
