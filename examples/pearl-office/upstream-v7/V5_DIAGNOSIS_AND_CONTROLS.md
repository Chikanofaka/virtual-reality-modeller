# V5 diagnosis and controls

This build does **not** lower scene resolution or replace the original main-repo 3D model.

## Root causes found by comparing Pearl Office with Signal Atrium
1. Signal Atrium has a small, explicit navigation contract. Pearl Office treated nearly every visual object (walls, glass, desks, chairs, pedestals, plants, etc.) as a collision candidate.
2. Pearl Office had no explicit connected corridor/navmesh. Its apparent corridor was visual geometry; movement was `outer polygon AND not any collider`.
3. When a Pearl Office movement frame touched one collider, the entire movement step was reverted. Near tight door/corridor edges this feels like the keyboard stopped working.
4. Signal Atrium uses a single animation-loop owner for camera movement and presentation. V5 buffers drag deltas and consumes them in the same tick as WASD and rendering.
5. V5 keeps only architectural collision for navigation, substeps movement, and slides along walls. Furniture remains visually detailed but cannot accidentally seal the route.
6. V5 explicitly flushes the WebGL command stream after each render to reduce the macOS/Chrome symptom where visual updates appear only after another UI event.

## Controls
- WASD: move
- click + drag: look
- Shift: sprint
- arrows: fallback look
- E: interact
- M: minimap
- R: reset
- Q: quality toggle (default resolution unchanged)

Recommended first test: `bash RUN_CHROME_SMOOTH.command`.
If Chrome still presents stale frames, test the identical runtime in Safari with `bash RUN_SAFARI_SMOOTH.command`.
