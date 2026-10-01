# Pearl Office Main Repo — Runtime-Optimized v4

This build intentionally keeps the main-repo scene, geometry, materials, antialiasing, pixel ratio, camera, room layout and visual resolution unchanged.

Runtime-only changes:

- Removed extra WebGL render calls from `pointermove`; the RAF loop is the single renderer owner.
- Reuses the static shadow atlas instead of rebuilding it while the player walks.
- Added a spatial broad-phase grid for the many static collision boxes; exact collision math is unchanged.
- Throttled HUD, minimap and interaction-distance DOM updates to 12.5 Hz while 3D rendering stays on every animation frame.
- Removed temporary Vector3 allocation from interaction proximity checks.
- Throttled subtle emissive animation to 30 Hz.
- Clears held keys if the window loses focus.
- Added `RUN_SMOOTH.command`, which launches the same local runtime in a dedicated Chrome app window when Chrome is installed.

Why Signal Atrium felt smoother:

Signal Atrium has a dramatically smaller scene and collision model. It uses a small number of room meshes and hard-coded collision zones. Pearl Office contains an elliptical glass shell split into many panels, room shells, labels, plants, desks, monitors, chairs, furniture collisions, and a live map/HUD. The prior drag branch also rendered directly on every pointer-move event in addition to the animation loop, creating redundant expensive frames while moving the mouse.
