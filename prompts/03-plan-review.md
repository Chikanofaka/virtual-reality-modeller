# Assemble a reviewable planning pack

Inputs: {{sources}}, {{answers}}, {{draft_geometry}}, {{quality_target}}.

Use schemas/planning.schema.json and the repository's semantic checks. Record metres, coordinate mapping, envelope, room roles, openings, spawn, required destinations, route, player clearance, explicit structural colliders, decorative furniture, materials/assets and interaction intent. Keep uncertainty and measurement status readable in provenance.notes and the review. Source detailed facts by inventory ID; preserve conflicting source evidence.

Produce a top-down plan and readable review showing the exact external entry, all portals, closed walls, circulation, must-have furniture and accepted assumptions. Test route feasibility before asking for approval. Do not call the plan approved yourself.

Output the exact pack path and hash, review artifact, remaining blockers and a focused request: approve this revision or identify changes. If prior explicit approval matches this exact revision, record it without requiring redundant confirmation. Any later build-critical edit invalidates the old approval.
