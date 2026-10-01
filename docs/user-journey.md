# User journey: source material to a playable space

The user is the space owner and player. The agent handles files, modelling, runtime engineering and packaging. The user should not need to debug a browser, operate Blender, or translate sketches into collision code to get an MVP.

The recovered request adds three product constraints: preserve the detailed main scene and resolution, provide smooth walking and looking, and turn repeated correction cycles into a reusable onboarding and validation process. The current harness makes those constraints explicit at every gate.

| Stage | User experience | Agent deliverable | Exit criterion |
|---|---|---|---|
| `init` | Choose a project name and describe its purpose. | Workspace, planning template, evidence ledger. | One project identity and output location. |
| `ingest` | Upload plan, annotated sketches, photos, walkthrough video and known measurements. | Inventory, checksums, source references, unresolved facts. | Every supplied source tracked; unsupported inputs named. |
| `interrogate` | Answer a few high-value questions in short missions. | Updated facts, contradiction list and next missing fields. | No unresolved blocking facts; accepted assumptions recorded. |
| `plan` | Review a top-down layout, route, opening list, furniture and quality target. | Structured planning pack and readable review. | Boundaries, units, entries, reachable destinations and fidelity target are reviewable. |
| `approve` | Confirm the specific plan or describe corrections. | Approval tied to the exact planning-pack hash. | Explicit approval for this plan revision; edits invalidate the lock. |
| `build` | Agent builds the experience from the locked inputs. | Detailed scene, independent navigation, runtime manifest and launchers. | Build matches approved plan and source provenance is recorded. |
| `validate` | Agent runs checks; user completes the target-browser route. | Machine results plus native-browser acceptance record. | Structural checks pass; required manual checks are honestly marked. |
| `play` | Enter, walk, look, interact, reset, complete a loop. | Telemetry-supported playable MVP. | Correct build badge; required route and interactions accessible. |
| `package` | Receive an archive and a clear run/publish guide. | Reproducible package, provenance and known limitations. | Contents verified; public distribution rights and push intent handled explicitly. |

Planning lock is a scope agreement, not a guarantee of exact architectural accuracy. A scale inferred from photographs must stay labelled as an estimate. If the user already approved the exact pack, do not request redundant approval; capture the authorization and continue. If geometry changes after lock, show only the relevant changes and seek approval for the new revision.

## The first successful play session

1. Launch from the packaged command and match the runtime badge to the build manifest.
2. Click Enter. Verify the canvas has focus and no blocking error appears.
3. Hold W, then A/S/D. Position should change continuously; release must stop movement.
4. Drag continuously while walking. View and direction must remain synchronized.
5. Walk from entry through the required destinations, through the approved central portal and back to entry.
6. Trigger an interaction, toggle the minimap and reset.
7. Switch away while holding a movement key, return, and verify no stuck movement.
8. Report any failure with the build/browser identity, reproduction steps and telemetry. A screenshot alone does not establish presented motion; use a short recording when needed.

## How feedback becomes a bounded next iteration

Translate “it is stuck” into a layer-specific observation: no key event, held input but no movement, navigation rejection, changing position with stale presentation, or an exception. Preserve the accepted plan, visual assets and quality settings while isolating the failing layer. Add a regression that checks the behavior, update the risk register, rebuild with a new identity, and repeat the same acceptance route. If a fallback renderer has lower fidelity, show that difference explicitly and retain the detailed master scene.

## What is automated and what needs evidence

The CLI manages project state, contracts, approval lock, checks and packaging. It does not reliably extract architectural truth from arbitrary photographs or video by itself. An agent or the owner must interpret those inputs, cite the source, and resolve contradictory openings or measurements before lock. Likewise a schema-valid plan is not proof of connectivity, and a connectivity test is not proof of comfortable human movement or native Safari presentation.
