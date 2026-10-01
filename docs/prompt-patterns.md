# Prompt patterns extracted from the recovered project

These are reusable, edited patterns derived from the available five-turn conversation and current request. They are not invented verbatim transcripts of missing early rounds. The planning images provide additional visible corrections, not a reconstruction of their author’s exact prompt.

| Pattern | User intent supported by evidence | Engineering response |
|---|---|---|
| Preserve the accepted visual baseline | “without changing the resolution”; same detailed main scene requested. | Freeze scene/quality inventory; isolate runtime changes; compare at the same viewport. |
| Treat a failure as an observation, not a diagnosis | Movement stuck, corridor may be disconnected, drag/view unsynchronized. | State hypotheses and use input→simulation→nav→render telemetry to separate them. |
| Reuse what visibly works | User reports Safari drag success while WASD fails. | Preserve drag path; test keyboard and shared locomotion independently. |
| Ask for all spatial evidence up front | Unified onboarding should collect plans, attachments and gaps. | Create inventory, scale status and source-grounded questions. |
| Resolve topology before modelling | Images revise envelope, entry, galleries, Reception and Tea repeatedly. | Explicit semantic room roles, openings, route and plan lock. |
| Progress to a reviewable MVP | User designates V7 the first Doing MVP. | Reuse V7 code, retain provenance, repair found defects and run meaningful acceptance tests. |
| Make engineering reusable | Public repository/skill/plugin/harness requested. | Stable contracts, commands, prompt templates, risk register, regression tests and packaging. |

## Shared prompt contract

Every work prompt should state the current artifact/build identity, approved constraints, allowed changes, inputs, unresolved questions, acceptance criteria and expected output. Each factual result must reference a source or test. If a required file is missing, say which part cannot be verified and continue independent work. Do not fabricate a code diff from a conversation summary.

The stage prompts in [`prompts/`](../prompts/) are designed to be used with the repository instructions and current project files. Replace placeholder fields with project-specific data. A prompt does not itself authorize paid asset generation, public upload or a plan change beyond the user’s scope.

## Risk-mitigation questions for the agent

Before modelling: Is the plan measured? Are room roles, entry, portals and circulation explicit? Which source wins if pictures conflict? Has the exact planning revision been approved?

Before runtime changes: Is the right build loaded? Which part actually fails? Do physical and virtual inputs agree? Are position and presentation both changing? Is a geometry object being reused as a movement rule?

Before release: Can a new user launch the extracted archive? Does the intended route work without pointer lock? Does the detailed scene remain present? Are native browser tests labelled separately from synthetic checks? Are unresolved constraints stated without declaring total success?

## Example: preserving scope while debugging

> Using build {{build_id}} and planning lock {{plan_hash}}, repair {{observed_failure}}. Keep the approved visual scene, materials, geometry detail and resolution settings. First record physical input, held state, position, nav decisions and rendered frames. Compare physical W with the virtual W control. Change the failing layer, add a behavior regression, then repeat the same route in the target browser. Report measured facts, remaining hypotheses and any untested browser path.
