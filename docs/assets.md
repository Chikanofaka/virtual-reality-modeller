# Detailed scene assets

Pearl's detailed procedural scene is retained by `scene.mode = "pearl-v7"`.
For a different space, use `procedural` to construct the measured shell/furniture
and add approved model assets. Use `imported-glb` with `scene.assetId` for a supplied
master model: the runtime loads that model without fabricating room walls/furniture.
It keeps the explicit support floor, navigation and lighting.

Models must be local glTF 2.0 binary `.glb` files with embedded buffers/textures (or
data URIs). External resource URLs and traversal paths are rejected. Draco, meshopt
and KTX2/Basis decoders are not bundled: export uncompressed models first. Preserve
original high-detail assets; do not silently replace failed loads with proxy boxes.

After `ingest`, use the recorded relative file path and SHA-256 in planning.json:

```json
{
  "id": "approved-master",
  "type": "model",
  "path": "private/uploads/HASH-model.glb",
  "sha256": "FULL_64_CHARACTER_SHA256_FROM_SOURCE_MANIFEST",
  "placement": {
    "position": [0, 0, 0],
    "rotation": [0, 0, 0],
    "scale": [1, 1, 1]
  }
}
```

This fragment belongs in the plan's `assets` array. Replace the illustrative path
and hash with actual values. Position is metres in runtime X/Y/Z (Y up), rotation
uses XYZ Euler radians and scale is dimensionless. Do not guess a conversion from
centimetres without checking the model's exported dimensions. Keep all transformations
inside the plan so approval and build identity include them.

The loader verifies the locked checksum and GLB envelope before parsing. Enter stays
disabled until models finish loading. Telemetry exposes imported model/mesh counts.
The same complete asset is copied into the build; no automatic decimation or texture
downscaling is performed. Source ingestion alone does not opt an asset into a public
package; listing it in `assets` does. Review ownership and sensitive content first.

Imported visual geometry never silently becomes a navigation mesh. Supply walkable
polygons, structural blockers, spawn and room access points independently. Walk the
locked route and compare it with the loaded model at the real player height. Geometry
that looks passable but conflicts with the nav contract fails visual/runtime review.
