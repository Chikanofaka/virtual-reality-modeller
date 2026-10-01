# Risk register and acceptance gates

Evidence origins are defined in [version evolution](version-evolution.md). Severity describes impact on the MVP, not proof that every cause occurred historically. Proposed controls are release requirements; consult current test output before declaring them passed.

| ID | Risk and observed/code basis | Prevention and detection | Release evidence / owner |
|---|---|---|---|
| PLAN-01 | Newest drawing still contains contradictory labels or openings. Image verified in v1.5. | Evidence IDs, contradiction ledger, top-down review and exact pack lock. | Owner-approved resolved plan; agent records sources. |
| PLAN-02 | Rendered diagram mistaken for surveyed dimensions. Images explicitly not to scale. | Units/scale status; one measured anchor or accepted approximate mode. | Review lists every estimate; planning agent. |
| NAV-01 | Dense visual props seal visible corridors. V1–V4 collider population verified. | Explicit nav layer and collider roles; no automatic decorative colliders. | Reachability route at player clearance; runtime engineer. |
| NAV-02 | Small islands or narrow gaps trap the player. User suspected; V6/V7 nav edits verified. | Continuous walkable surface, portal width checks, spawn/destination flood-fill or equivalent route test. | Required loop and central portal traversable; runtime engineer. |
| NAV-03 | Entire step rollback sticks at a corner; large step tunnels through walls. Source verified. | Bounded delta time, substeps, axis sliding; explicit speed/radius. | Diagonal corner and low-frame-rate movement checks. |
| NAV-04 | Connected fail-safe nav permits passage through visible room walls. V7 source verified. | Declare collision policy and model intended structural barriers/door gaps independently. | All intended blocked/passable boundaries tested; planning owner + engineer. |
| VIS-01 | Floor normal faces down, or normal fix mirrors footprint. V5/V6 source verified. | World XZ mapping and triangle winding; compare footprint to shell and nav. | Upward-normal and footprint/route support check; visual engineer. |
| INPUT-01 | Safari key representations differ or canvas lacks focus. User failure, source fallback edits. | Prefer code; key/legacy fallback; focus on entry/click; ignore editable targets. | Physical and virtual input comparison, raw/normalized telemetry. |
| INPUT-02 | Blur, tab change, pointer cancel or button release leaves held input. | Clear input on lifecycle loss; handle pointer release outside control and multi-source state. | Walk → blur → return stops; D-pad release outside stops. |
| INPUT-03 | Multiple capture listeners toggle actions more than once. V7 dedup verified. | One normalized dispatch or event identity dedup; ignore repeat for actions. | E/M/R/Q respond once per press. |
| LOOP-01 | Pointer handler renders while RAF also renders. V3 source verified; other handlers persist in V7. | Only loop presents; handlers accumulate state; throttle UI work separately. | Instrumented render ownership and drag+move test. |
| LOOP-02 | Undefined interactable causes recurring exception before presentation. V7 source verified. | Factories return valid objects; validate registrations; runtime smoke beyond start screen. | Enter + movement + interaction with no page errors. |
| BROWSER-01 | State changes while image appears frozen. User reports across browser comparison; compositor cause unproved. | Record build/browser/GPU where available, positions, look and rendered-frame counters; repeat same scene in Safari/Chrome. | Native-browser continuous movement/drag observation; no universal `flush()` claim. |
| BROWSER-02 | Pointer lock is a hard dependency. Autonomous source verified. | Click-drag baseline; optional pointer lock only with graceful fallback. | Tour completes without pointer lock. |
| BUILD-01 | Old localhost server, cached module or stale tab contaminates results. Shared port code verified; old screenshot diagnosis prior claim. | Served build manifest, content hash, visible module/build/port badge, no-store dev responses. | Page identity matches package, actual module hash and requested build. |
| BUILD-02 | Launcher kills another application’s process. Original V7 launcher code verified. | Never kill by port alone; safely bind free loopback port or fail with clear action. | Occupied-port test preserves existing service. |
| BUILD-03 | Download strips executable bit or macOS blocks launch. Prior report; not reproduced here. | Shell-invocable `.command`, clear terminal alternative; no blanket quarantine/security disabling. | Extracted archive launches using documented command. |
| BUILD-04 | Rollback is confused with the current project build, or bypasses a changed planning lock. | Keep verified playable ZIPs. Extract the selected historical package separately and run its own `python3 launch.py`; verify its badge and manifest on the fresh port. The project CLI uses the current locked plan and has no old-build selector. | Historical package integrity and identity verified; restoring a plan for new development requires review/reapproval and a new build. |
| ASSET-01 | CDN unavailable, dependency changes or missing relative asset. | Pin dependencies, bundle when licensing permits, verify local URLs; distinguish online requirements. | Fresh package launch and dependency inventory. |
| QUALITY-01 | “Fix” silently lowers resolution or swaps detailed scene for simplified renderer. User explicitly prohibited. | Preserve master scene/settings; log any quality/fallback choice and ask when it changes accepted target. | Before/after resolution and scene inventory at same viewport. |
| RIGHTS-01 | User-supplied floor plans/photos/code are assumed covered by new MIT license. | Keep provenance and rights status; separate new code from supplied sources/assets. | Publisher confirms distribution rights; never auto-publish. |
| CLAIM-01 | Passing unit tests is advertised as all-browser success. | Separate source audit, automation and native manual evidence. | Test report includes not-run checks and environment. |

## Failure triage: read the first broken link

| What telemetry/observation shows | First investigation |
|---|---|
| Neither raw nor normalized key event appears; virtual control moves | Focus, OS/browser delivery, editable element or event handler. |
| Raw event appears but held key does not | Normalization, event dedup, input lifecycle. |
| Held key appears but position does not change | Started state, movement calculation, nav rejection or exception. |
| Physical and virtual controls both fail to move | Shared locomotion/update path, not just physical keyboard. |
| Position changes but camera image stays still | Render invocation, exception, scene/camera binding or presentation. |
| Image updates but floor appears disconnected | World transform, normals, geometry support or material; do not assume nav has a gap. |
| Navigation passes but player crosses a visible wall | Collision policy or nav/visual mismatch. |
| Badge or module hash differs | Stop comparison and launch the intended build before diagnosing. |

## Release checklist

- [ ] Planning pack is source-grounded, schema-valid and approved at its current hash.
- [ ] Scene, navigation and input/render contracts are independently inspectable.
- [ ] Spawn, route, door/portal and collision behavior pass automated checks.
- [ ] Rendering floor supports the route and uses correct world orientation.
- [ ] Physical input, virtual input, drag, blur recovery and actions behave correctly.
- [ ] No repeated runtime errors during play; interaction factories return usable objects.
- [ ] Package identity, port behavior and cache policy have been tested.
- [ ] Detailed scene and agreed resolution are retained, or a change is explicitly accepted.
- [ ] Safari and Chrome results identify exactly which checks ran and which remain manual.
- [ ] Source asset rights, known limitations, launch guide and package hash are recorded.
