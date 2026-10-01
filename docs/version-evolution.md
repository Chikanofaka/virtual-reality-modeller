# Evidence-backed version evolution

This review inspected all **11 supplied ZIPs**, read the application sources and launchers, compared file hashes, diffed the V3–V7 runtime changes, and visually inspected all six floor-plan images. The retained conversation contains **five turns**, covering V4 through V7 and the request for this harness. Earlier conversations, historical screenshots and a recording were not present in that retrieved text. A prior assistant’s explanation is not treated as a test result.

Evidence labels used here:

- **Code verified:** the archive contains the stated implementation. This does not prove it ran successfully on the original computer.
- **Image verified:** the supplied planning image visibly contains the stated content. It is not a measured survey.
- **User observed:** directly reported by the user in the available conversation.
- **Prior claim:** an earlier assistant’s diagnosis or success assertion, without reproduced historical execution.
- **Inference:** a likely mechanism requiring targeted reproduction to establish historical causality.

See [archive hashes and entry inventory](evidence/archive-manifest.json), [all adjacent archive comparisons](evidence/archive-comparisons.json), and the source-specific diffs in `docs/evidence/`. Adjacent ZIP order is a comparison order, not a claim that every version is a direct code descendant. Compatibility and hybrid players are alternate renderer branches. There was no archive literally named `v1`: “V1” below means the initial autonomous family.

## Planning images: v1.0 → v1.5

Plan version numbers are separate from runtime version numbers. [Original images and contact sheet](../examples/pearl-office/floor-plan-evolution/README.md) preserve the evidence and red annotations.

| Plan | Image-verified change | Planning lesson |
|---|---|---|
| v1.0 | Rounded rectangular envelope; bottom entry; central glass office; several red correction arrows. | Capture envelope and actual entry before furnishing. |
| v1.1 | Three-corner pearl envelope; Awards and Charity are separately labelled; a Corridor / Ops area still appears. | A name on a plan must be classified as room, gallery or circulation. |
| v1.2 | Meeting expands along upper right; Charity is explicitly an open gallery; Reception is shown inside the central area; external entry moves leftward. | Adjacency and openings are independent requirements. |
| v1.3 | Awards/Charity shown as an open continuous left-side area; Reception and Tea appear inside the central envelope; Back Office occupies lower-left. | Record open/enclosed status and boundaries explicitly. |
| v1.4 | Entry moves to left edge between Awards and Charity; Reception and Tea appear on the outer left side; only central portal remains at Wine/Manager junction. | Explicitly lock external entry and the number of central portals. |
| v1.5 | Reception and Tea partitions appear at center-left inside the glass outline; room labels and notes remain partly inconsistent. | Freeze a reviewed semantic plan, not just the newest image. |

All six illustrations state “not to scale.” In v1.5, the Tea/Reception depiction and some text notes are not fully consistent, and a tea-like furniture arrangement remains lower-left. The recovered `data/layout.json` adds descriptive topology but no surveyed geometry. Neither source justifies inventing exact dimensions or silently deciding which conflicting representation is authoritative.

## Runtime inventory and comparison

| Supplied package | Code-verified implementation | What can and cannot be concluded |
|---|---|---|
| `pearl_office_autonomous_game` | Three.js procedural 3D, pointer lock, antialiasing, DPR cap 2, shadows, furniture/wall colliders, interactions, minimap, Blender builder. | Establishes detailed geometry baseline. No archived runtime success trace. |
| `pearl_office_compatibility_game` | Standalone Canvas 2D perspective player, WASD and drag, simple segment collisions, no WebGL. | A renderer fallback exists; this is not equivalent to the full WebGL scene. |
| `pearl_office_smooth_game` | Three.js retains scene families, defaults to drag, optional pointer lock; DPR cap 1.15, no antialiasing/shadows, simpler glass, paced loop. | It reduces quality to reduce work; later user explicitly requires preserving resolution. |
| `pearl_office_hybrid_hd` | Canvas 2D renderer with adaptive internal resolution, photo panels and plan minimap. | Compatibility branch, with different visual/rendering behavior. “HD” is a mode label, not fidelity equivalence. |
| `pearl_office_ultra_hybrid_v2` | Canvas 2D photo-textured branch, quality modes; expanded independent Blender scene builder. | Browser rendering and Blender master are different artifacts; one does not prove the quality of the other. |
| `pearl_office_mainrepo_drag_v3` | Returns to detailed Three.js scene; click-drag changes view; `pointermove` calls `renderNow()` in addition to RAF. | Duplicate rendering during input is code verified; historical GPU/compositor root cause is not measured. |
| `pearl_office_mainrepo_runtime_optimized_v4` | Removes render from pointer movement, caches shadow map, adds collider grid, throttles HUD/minimap to 0.08 s and glow to 30 Hz, clears keys on blur. | Less work does not establish connected navigation. Other direct `renderNow()` calls remain. |
| `pearl_office_mainrepo_signalnav_v5` | Buffers look deltas into RAF, filters nav to named structural colliders, adds 0.045 m substeps/axis sliding, uses WebGL `flush()`. | Fewer colliders and sliding are verified. `flush()` is not proof of a universal compositor fix. |
| `pearl_office_mainrepo_safari_walk_v6` | Changes floor rotation +π/2→−π/2; key/code normalization and focus; replaces collider grid with geometric walkability; uses 0.035 m substeps. | Down-facing normal is corrected, but that rotation also mirrors the floor footprint along Z. Historical screenshot cause remains a claim. |
| `pearl_office_mainrepo_safari_wasd_v7` | Adds code/key/legacy fallback, capture listeners with WeakSet dedup, canvas focus, visibility/pagehide clearing, D-pad, HUD diagnostics, port 8027, `app_v7.js?v=7.0.0`; navigation accepts office envelope except central glass band/portal. | User selected this as Doing MVP. That designation is not evidence that every browser acceptance test passed. |

Layout JSON is byte-identical across autonomous, smooth and main-repo V3–V7. The main-repo Blender builder is also byte-identical across those packages; V2’s expanded builder is a separate artifact. The V3–V7 changes therefore concentrate on the operating layer, with the V6 floor correction as a visual geometry exception. Original default DPR is 1.35 in V3–V7 and optional cinematic DPR is 1.8; “high resolution” should be evaluated at an actual viewport and device scale, not advertised as unrestricted native resolution.

## Failures and stronger conclusions

| Finding | Evidence and confidence | Harness rule |
|---|---|---|
| Movement and view still stuck after optimization | User observed after V4; source still couples navigation to collider geometry. | Measure input, position, navigation result and presented frames separately. |
| Clear corridor may be blocked by props | V1–V4 source registers many furniture colliders; user suspected a disconnected corridor. The exact historical blocked route was not replayed. | Separate structural barriers from decorative meshes; test a connected route with player clearance. |
| Safari drag works while physical WASD does not | User observed. Browser/GPU versions not provided. | Keep drag default; inspect physical-key delivery and focus independently of movement. |
| Floor appears disconnected | User observed. V5 down-facing floor normal and V6 rotation edit code verified. | Validate normals **and** plan-to-world footprint; don't fix one by mirroring the other. |
| V5 was tested while V6 was expected | Prior assistant claim based on unavailable screenshots; shared port 8015 is code verified. | Require matching runtime build ID, served manifest and loaded module hashes before testing. |
| V7 desk interaction throws | `desk()` has no return; `pearlConsole = desk(...)` registers `undefined`; `updateNearest()` dereferences `.position`. Code verified. RAF schedules its next tick before this exception, so the exact symptom is recurring skipped UI/render ticks, not proven permanent loop termination. | All interactable factories must return valid objects; smoke test real runtime after entering and moving. |
| V7 has more than one rendering entry point | `resetPlayer`, quality toggle and resize call `renderNow()` outside RAF. | A single owner presents frames; handlers update state or request invalidation. |
| V7 collision is simplified | `canMove()` ignores visual room walls and furniture. | Declare the collision policy. Keep passable tours distinct from full physical simulation. |
| V7 “unique port” does not prove ownership | Launcher kills all PIDs returned by `lsof` for 8027; old 8015 launchers also remain in ZIP. | Bind safely, verify ownership, fail or choose another port; never kill arbitrary port occupants. |

These defects were discovered by this audit, not asserted as known historical diagnoses. The original V7 sources remain available for comparison; the adapted harness records subsequent fixes in [CHANGELOG](../CHANGELOG.md). See the repository’s current validation report for what has actually been run.

## Interpreting the browser story

The available user report supports Safari as the first local acceptance target. It does not establish that Safari universally outperforms Chrome, that a Chrome app window resolves GPU issues, or that `flush()` cures compositor freezing. Browser, OS, GPU, viewport, build and input method belong in every reproduction record. Chromium automation can validate state changes but cannot certify native Safari presentation or subjective smoothness. Switching browsers must use the same scene, resolution, route and build identity so the comparison is meaningful.

## Reproducing source comparisons

The evidence manifest gives SHA-256 values for each original archive and every archived file. To independently verify a source, hash the ZIP and compare that value before extracting. `archive-comparisons.json` compares normalized paths after removing the top-level package directory and excluding `__MACOSX` from comparisons. It records added, removed, modified and unchanged paths for each pair, including the alternate-renderer branches. Nine unified diffs compare the primary player source across all ten runtime packages, including four main-repo diffs V3→V4→V5→V6→V7. Large alternate-renderer diffs indicate a branch change, not a line-by-line migration recommendation. No runtime outcome is inferred merely from these diffs.

The audit is reproducible with Python’s standard library:

```sh
python3 scripts/audit_archives.py /path/to/source-zips --output /path/to/audit
```

It never executes or extracts ZIP members, bounds decompression, records unsafe member paths, retains resource-fork hashes in inventory while excluding them from comparisons, and writes no source-directory path into reports. Missing archives fail by default; `--allow-missing` produces an explicitly incomplete audit.
