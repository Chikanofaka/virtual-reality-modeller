# Diagnose a failed play session

Expected build: {{build_id}}. Expected module hash: {{module_hash}}. Browser/OS/input: {{environment}}. User observation: {{symptom}}. Reproduction route: {{route}}.

First verify the page identity against the served manifest and package. Then inspect browser errors, raw/normalized key events, held keys, focus, virtual control, simulation position, nav rejection and frame/presentation evidence. Hold physical W and virtual W separately, then drag while moving. Check blur/return and pointer release outside the control.

Identify the first broken link. Distinguish code-verified defects from hypotheses about OS/browser presentation. Preserve accepted scene detail and resolution while isolating the failure. A WebGL flush or browser switch is an experiment, not a universal fix. Do not terminate an unidentified process merely because it occupies a port.

Output: concise reproduction; evidence table; highest-confidence fault; smallest repair; meaningful regression; new build identity; same-route retest; unresolved browser/manual checks.
