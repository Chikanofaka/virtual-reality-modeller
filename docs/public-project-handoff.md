# A repeatable public-project handoff

Use this when a project is selected from a Ready queue, including a Trello card,
and its owner asks for a repository or reusable harness. A board status supplies
context; it does not grant publication, spending, or access to private attachments.
Apply the owner's actual authorization, and finish the local work before requesting
any genuinely missing publication decision. This document does not connect to or
modify a board.

Every handoff has three front-door elements:

1. **What it does, with evidence.** One concrete flagship, actual screenshots,
   inputs → decisions → outputs, a runnable example, and the precise limits of the
   result. Label mockups, synthetic fixtures and historical demonstrations.
2. **How a new user starts.** Prerequisites by task; obtain/open the repo; connect a
   local coding agent; a copyable first prompt; two or three short questions at a
   time; a concrete approval checkpoint; build, extract, launch, and troubleshoot.
   Give separate macOS and Windows commands and label untested platforms.
3. **What it consumed.** Measured resource evidence for the flagship, with model,
   scope, dates, retries and coverage. Unknown values stay unknown. Explain the
   difference between replaying a finished artifact and creating a new one.

## Record resources from the beginning

Create a project-local record from [the resource template](../templates/resource-usage.example.json).
Record a stable work scope and the acceptance target before collecting totals.
For each model request, retain the provider's usage totals and model/service tier;
count only unique requests belonging to that scope. Cached input may already be
included in input tokens; reasoning may already be included in output. Record
those semantics and never add a subset a second time. Include actual delegated
work, but exclude inherited transcript history from child totals. Do not publish
raw chats, API keys, billing identifiers or local account paths.

Measure tool commands with a monotonic clock. Record start/end, result, and the
parent run so intervals can be combined without counting a server and its browser
child twice. Track model activity separately when provider timing exists. Exclude
user response time, paused sessions, quota recovery and installation downloads from
an explicitly labelled active-work metric. If those intervals cannot be separated,
report **command elapsed time** or **session elapsed time**, never active backend
time. CPU time is a different metric again.

Separate first-time harness engineering, project-specific creation, successful
verification, failed attempts, and later publication/support. Retain actual cost
from a project-attributable invoice or provider usage export when available. A
current model rate is a reference, not proof of a historical bill. Do not turn a
subscription message limit into tokens or dollars.

## Spend effort where it changes the outcome

- Try a bundled replay before starting paid agent work.
- Start with a small accepted scope and reuse the runtime; change the room data and
  assets where possible.
- Read the four entry documents once, then inspect implementation as needed.
- Assign bounded independent reviews when useful; avoid parallel agents repeating
  the same exploration. Include their usage in the resource record.
- Use the selected capable model for uncertain layout/reasoning decisions; consider
  a lower-cost available model for bounded checks after requirements stabilize.
  This is a workflow choice, not an unmeasured quality or cost guarantee.
- Reuse passed evidence when its inputs are unchanged. After a change, rerun the
  checks it can affect and the required delivery check, without repeating unrelated
  render/asset-generation work.

## Close the loop

Ship the playable artifact, editable source/selected assets, launch guide, exact
build identity, actual reports and screenshots, measured resource record, known
limits, and modification entry points. Extract the deliverable elsewhere and test
the documented command. Scan public files for private inputs and local paths.
Keep the previous working package for rollback.

Compare another harness only with a matched scene, visual target, model/tier,
machine, acceptance suite, retry policy, and timing definition. Without that
experiment, describe capabilities and measured artifacts; do not claim a percentage
cost saving or speed advantage.
