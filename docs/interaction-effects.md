# Visible interaction responses and wall occlusion

Custom procedural and imported-GLB games may enable two optional behaviors. Plans
without these fields keep proximity-only interactions and their existing visual
behavior. Pearl's legacy progression is separate.

## Declared walls block interactions

Set `runtime.interactionOcclusion` to `"structural-segments"` (`"none"` is the
default). Target selection skips any candidate whose horizontal player-to-anchor
line touches a `navigation.segments` wall, including half the declared wall
thickness. It then chooses the closest remaining target at strictly less than
2.15 metres, retaining the first candidate on a tie.

Both the Python planning validator and browser apply this rule. The geometric
test includes endpoints, collinear segments and arbitrarily thin walls without
sampling the sight line. It does not inflate walls by player radius, include
furniture AABBs, raycast visual meshes or model elevation. Declare each structural
wall, leave real openings between wall segments, and put interaction anchors in
front of their wall rather than embedded in it. Missing wall declarations cannot
provide occlusion. Glass and furniture need a different policy if they should
affect visibility.

## Correct objectives change named meshes

Attach an `effects` array to a furniture interaction:

```json
{
  "label": "Turn on television",
  "message": "Welcome home. Visit the bedroom next.",
  "effects": [
    {"objectName": "TVScreen", "emissive": "#286cff", "intensity": 3}
  ]
}
```

The furniture must be referenced by `gameplay.objectives`. Each effect has exactly
the three shown fields, a nonblank name, a six-digit hex colour and finite intensity
from 0 to 20. An object name may belong to only one effect across the entire plan.
Effects require a custom game in procedural or imported-GLB mode.

After GLB loading, every name must resolve to exactly one Mesh with
emissive-capable materials in all its material slots. Missing names, ambiguous
names and unsupported materials block entry with an error. Naming and mesh shape
are checked against the loaded scene; a successful JSON check cannot establish
their existence. Materials are cloned once so changing a screen does not change
other objects that shared its imported material.

Only an interaction that advances the current objective applies its effects.
Wrong-order or repeated interactions leave the visual state unchanged. R restores
the original emissive colour and intensity, player position and objective state.
The diagnostic snapshot includes `interactionEffects` for exact state checks.

Emissive changes brighten the mesh itself. They do not add a light source, cast
new illumination, play video, animate doors or provide arbitrary script execution.
An authored screen can supply an emissive texture for its welcome artwork; those
assets and any additional lighting still require scene implementation and review.

## Reproducible verification

`python3 scripts/verify_harness.py --browser` now runs three synthetic projects:
Pearl, the original discovery studio, and a small imported-model interaction
fixture. Its GLB is generated locally by `tests/make_interaction_fixture.py`.

For the interaction fixture, browser automation walks behind a declared wall and
checks that E cannot trigger the nearby target. It then walks the objective route,
tests wrong-order input, observes both material states and distinct rendered
frames from unchanged viewpoints, resets and repeats. The same checks run after
packaging and independently launching the extracted ZIP. Existing cases cover
shared-material isolation, bad bindings, exact reset, planning rejection and
legacy behavior.

These are synthetic harness checks, not acceptance of a real apartment, a
physical keyboard or Safari. Keep the generated report and source/build hashes
with any verification claim.
