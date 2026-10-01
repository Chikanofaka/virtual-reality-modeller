# Contributing

Keep one change focused on one observed failure or capability. Include the build
hash, browser/version, reproduction steps, expected behavior and measured behavior.
Do not submit private floor plans or video without permission.

Preserve the detailed Pearl scene unless the change explicitly concerns it. A
navigation change must not lower texture resolution or remove props. Keep the
runtime's only render call inside its frame owner; input callbacks only update
state. Add regression tests for behavioral failures, especially radius clearance,
sliding, key release, plan invalidation and build identity.

Run `python3 -m unittest discover -s tests -p 'test_*.py'` and
`node --test tests/runtime*.mjs`. Browser checks are described in
`docs/browser-validation.md`. Passing pure tests alone does not verify a compositor.

New risk-register entries need a source, evidence level, impact, mitigation and
validation method. Treat anecdotal observations separately from reproducible code
defects. Do not reword earlier evidence to hide a regression.

Pull requests should state the trigger, resulting behavior, test evidence and any
remaining limitation. Do not update historical snapshots in place.
