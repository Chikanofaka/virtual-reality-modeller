# Blender authoring support

The browser scene is the authoritative preserved V7 experience. The original ZIP's
Blender builder is included as `BUILD_PEARL_OFFICE_UPSTREAM.py`, byte-for-byte.
It is an older, simpler offline companion: its overlapping rectangular floor slabs,
furniture and layout are not identical to the browser scene. Do not export it and
claim full V7 visual parity. Running it in a new Blender process writes to the repo's
`output/` directory; it resets that process's scene.

Use `audit_scene.py` on a separately authored `.blend` master to report evaluated
world-space bounds, triangle count, floor normals and nonmanifold edges:

```sh
blender -b path/to/master.blend --python blender/audit_scene.py -- --output audit.json
```

Mark intended floor meshes with custom property `role = "floor"` or a name beginning
with `floor`. This audit checks their upward faces. A visual scene must also pass
opening and floor-plan parity review; a topology report alone cannot prove that a
room matches a photograph. Floors with top and bottom faces are expected to have
both normal directions; the report requires an upward face and reports their counts.

Use metre units, Blender X/Y for plan and Z up. For runtime, convert to X/Z plan and
Y up via the glTF exporter. Keep collision/nav in the planning contract. Review four
corners, entrance, every opening, overhead, center-up and opposed ceiling obliques.
Never export decorative door trim as proof of a cut opening. Build actual apertures
with wall thickness and a destination. Preserve approval and evidence alongside the
master source before final export.
