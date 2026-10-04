# Blender authoring support

The browser scene is the authoritative preserved V7 experience. The original ZIP's
Blender builder is included as `BUILD_PEARL_OFFICE_UPSTREAM.py`, byte-for-byte.
It is an older, simpler offline companion: its overlapping rectangular floor slabs,
furniture and layout are not identical to the browser scene. Do not export it and
claim full V7 visual parity. The archived script uses the older `BLENDER_EEVEE_NEXT`
engine name and can print warnings while leaving render/export outputs absent.
Run the maintained adapter in a fresh Blender process instead:

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python blender/build_pearl.py -- --output output/pearl-companion
```

The adapter selects an available Eevee engine, applies two exact in-memory
substitutions for engine and output path, and leaves the archive untouched. The
output directory must be empty. It verifies the preview, `.blend`, and `.glb`
outputs and writes `audit.json` plus a hash-bearing `build-report.json`; the
`--python-exit-code 1` option makes a failed build fail the shell command. It resets
only the new process's scene. A successful run proves this companion builds on
the reported Blender version; it does not establish browser parity or approve
the historical layout. Use a new output directory for each comparison run.

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
