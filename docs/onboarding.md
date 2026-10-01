# Gamified onboarding induction

Use short missions to gather enough information for a useful first playable. Completion means an answer is recorded with its evidence or explicit assumption. Do not reward speed by accepting invented measurements, and do not force optional decoration questions before a walkable MVP can be built. Text answers, marked plans, rough sketches and narrated video are all valid inputs.

## Mission 0 — Build the evidence backpack

Ask for available floor plans, site photos, walkthrough video, dimension notes, entrance photos, furniture references and material references. Ask the owner to mark which plan is newest and which corrections supersede it. Offer a simple naming convention: `plan-latest`, `entry-outside`, `room-id-facing-north`, `room-id-measurements`. Keep originals immutable and create a source inventory with file ID, checksum, type, date if known, coverage and usage rights.

Opening prompt:

> Upload what you already have: your floor plan, entrance photos, room photos or walkthrough video, and any known dimensions. Tell me the newest plan and the one route you want a visitor to complete. Rough information is welcome; I will flag gaps before we lock the plan.

## Mission 1 — Establish the map

Ask at most three related questions per round, prioritizing blockers:

- What is the overall boundary and coordinate orientation? Which side is the external entry?
- What one measured length can establish scale, and what units does it use? If none exists, may this MVP use an explicitly approximate layout?
- Which names are enclosed rooms, open galleries, circulation, outdoor apron or shared work areas?

Unlock: boundary, unit/scale status, outside-to-inside entry and named zones. Store confidence and source for each. Measurements estimated from pictures must not be marked measured.

## Mission 2 — Connect the route

Ask the owner to trace a visitor route on the plan. Mark every doorway/portal, the intended start, destinations, one-way restrictions and prohibited areas. Confirm corridor width or clearance assumptions, door openings and player radius. Ask whether furniture should block movement or remain decorative in the MVP.

Unlock: a connected route graph with explicit portals and a collision policy. For Pearl Office, the recovered requirements specify external entry between Awards and Charity, a clockwise circulation loop, and one central entry near Wine/Manager 1. These are example-specific; never impose them on a new building.

## Mission 3 — Give each room an identity

For each room, gather purpose, must-have furniture, approximate position, count, material/colour references and priority. Keep structural elements separate from decoration. Ask for missing reference angles only where they affect the agreed fidelity. Label decorative substitutions so the owner can review them.

Unlock: room schedule and a fidelity budget. Examples include detailed procedural furniture, supplied GLB assets or separately generated assets. External paid generation requires its own authorization; the default procedural workflow incurs no asset-generation credits.

## Mission 4 — Agree on the experience

Confirm target computer/OS, Safari and/or Chrome, mouse/trackpad/keyboard, first-person height/speed, interactions, minimap and expected display quality. Ask whether the experience is a tour, spatial prototype or a more physical simulation. Confirm a concrete acceptance route and minimum acceptable behavior rather than promising an unmeasured FPS.

Unlock: browser/input matrix, interaction list, quality target and acceptance criteria. Safari is the first acceptance target for this recovered project and is required by the current planning contract; new projects can add secondary targets.

## Mission 5 — Review and lock

Show the plan, entry arrows, route, room schedule, structural barriers, decorative objects, accepted assumptions and remaining limitations together. Call out contradictions between sources rather than choosing silently. Present the exact review file/hash and ask for approval or corrections. The CLI’s `approve` stage records that decision; any material plan edit requires a new lock.

Unlock: approved planning pack. No 3D production build is presented as plan-accurate before this gate.

## Adaptive questioning rules

1. Ask the smallest question that resolves the highest-impact uncertainty.
2. Reuse facts already answered; never ask the owner to restate a clear source.
3. Provide two or three concrete options when appropriate, plus free text.
4. Explain why a question matters in one sentence: “This decides whether the route is passable.”
5. Distinguish **blocking**, **assumption accepted**, **optional** and **resolved**.
6. After each round, show what was learned and what remains. Avoid endless completion scores.
7. If a blocker remains, keep draft planning work moving but do not fabricate approval or geometry.

## Planning-pack content

The machine-readable schema in `schemas/` and the generated project template are the authoritative field names. Semantically the pack must record project/version, units and scale status, source inventory, coordinate system, boundary, rooms, entry/portals, route, navigation/collision policy, furniture/materials, interactions, target browsers/input, quality target, assumptions, contradictions, acceptance criteria and approval provenance. Separate human notes from build-critical geometry. Hash the exact pack that the builder consumes.

## Reusable question example

> Mission: connect the entrance. I can see an entry arrow on the newer plan and a different doorway in an older image. Which should the MVP use: A) the newer marked entrance, B) the doorway shown in the photo, or C) another location you mark? This determines the spawn point and the first walkable connection.

Chinese variant:

> 本轮任务：确认入口。新版平面图和旧照片的入口位置不同。请选 A）新版箭头位置，B）照片中的门，或直接在图上标出正确入口。这一项会决定出生点与第一段可通行动线。

## Running the induction in this repository

All commands use `python3 scripts/harness.py <stage> PROJECT`. Start with `init`, then `ingest PROJECT FILE...`. Run `interrogate PROJECT` to see the next two unresolved quests. Put summaries in an answers JSON file with keys `survey`, `entrance`, `rooms`, `furniture`, `navigation` and `experience`, then use `interrogate PROJECT --answers answer.json`. See `templates/answers.example.json`. Each answer must contain at least 12 characters; this is an input-completeness check, not a substitute for source review.

Use `plan PROJECT --input planning.json` after an agent/owner has assembled the structured geometry. Review its output, then run `approve PROJECT --accept` only for the revision you accept. `build PROJECT` follows the approval. `provenance.scaleConfirmed` means the owner confirmed the chosen scale; if approximate, say that explicitly in `provenance.basis` and `provenance.notes`. It must never be used to disguise an estimate as a survey.

Uploaded private evidence is inventoried, not automatically included in a distributable build. Files explicitly selected in `config.assets` can be copied into the build and therefore need a deliberate distribution decision.
