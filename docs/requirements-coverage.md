# Delivery scope and evidence

| Requirement | Implementation/evidence | Boundary |
|---|---|---|
| Compare all versions | Archive inventory, hashes, adjacent comparisons, V3→V7 diffs, six-image review | Earlier chat turns beyond the five retrieved turns were unavailable |
| Extract prompt patterns | User journey, prompt-patterns, staged prompt templates | Patterns are abstractions; unavailable early prompts are not fabricated quotes |
| Gamified intake | CLI quests/badges, two questions per round, structured answers and plan validation | A person/agent must interpret evidence and confirm measurements |
| Locked-plan playable build | CLI approval hash → immutable build → runtime adapters | Generic reconstruction quality depends on supplied plan and authored assets |
| V7 visual fidelity | Detailed procedural Pearl source preserved and extracted | Companion Blender builder is an older, simpler artifact |
| Independent nav/input/render | Separate modules, explicit nav data, single frame owner | Single-floor navigation, not a general physics engine |
| Interaction and minimap | Nearby E actions, Pearl quest progression, world-coordinate map | Pearl partition/furniture collision stays intentionally permissive |
| Browser compatibility | Safari-compatible key normalization/focus/drag; Chrome browser smoke | Exact observed tests are in validation-report, not assumed from architecture |
| Old-build mitigation | New bound local server, badge/hash/port, no-store, integrity manifest | No software can identify a user's manually opened unrelated old page remotely |
| Reusable repository/skill/plugin | README, license, docs, scripts, tests, contracts, skill, plugin.json | Source package only; not installed or uploaded to an account |
| One-command workflow | Quickstart and macOS command files; full staged CLI | Python required locally; Node is optional for tests |
| Public handoff | Local Git repository and distributable source/playable ZIPs | No public push; historical asset licensing needs owner clarification |

The runtime acceptance report is authoritative about executed checks. A successful
source audit, Python test or Blender audit must not be described as proof of actual
Safari hardware input or a complete end-user walk-through.
