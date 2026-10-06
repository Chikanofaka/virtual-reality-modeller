# What the flagship actually consumed

The Midtown case produced a furnished two-bedroom, two-bathroom apartment from an
unscaled floor plan, six photo observations and a short user brief. The result has
eight visitable areas, 43 authored furniture groups and three ordered interactions.
The user reviewed and accepted the approximate layout before construction.

This page reports **one observed first-run case**, not a quote for your project.
It includes implementing missing interaction features, modelling, test development,
repairs and delivery. Replaying the bundled game does not invoke an AI model.
Using the existing harness for another room is a different workload; no matched
repeat-project or competing-harness benchmark has been measured here.

## Actual model usage: GPT-6 Astra

The [sanitized usage ledger](evidence/midtown-resource-usage.json) was reconstructed
from local per-response Codex telemetry, using the apartment-intake through first
completed-delivery boundary. All 179 recorded responses identify `gpt-6-astra`.
Only each agent's own responses were counted; inherited parent history and parent
cumulative counters were not added again. Raw conversations remain private.

| Metric | Recorded tokens | Interpretation |
|---|---:|---|
| Input | 17,986,289 | Includes repeated context sent across requests |
| Of that, cached input | 16,928,000 | Already included in input; 94.12% of input |
| Uncached input | 1,058,289 | Input minus cached input |
| Output | 149,715 | Includes recorded reasoning output |
| Of that, reasoning | 39,722 | Already included in output |
| **Total input + output** | **18,136,004** | 179 unique recorded responses |

Of the total, 100 main-agent responses account for 12,653,308 tokens; 79 exclusive
sub-agent responses account for 5,482,696. The number is cumulative model traffic,
not 18 million unique words, not the size of the generated code, and not a token
allowance every similar project will require.

Three quota-blocked sub-agent attempts have no usage records; their usage is
unknown, not asserted as zero. Unrecorded provider-side billing or compaction is
not reconstructed. The totals exclude the earlier general repository audit, later
checksum rechecks and this public-documentation work. They are the **available
recorded usage**, not a certified complete invoice.

The later macOS Finder launch repair consumed a separately recorded **1,408,726
tokens across 10 responses**, including 1,395,072 cached input tokens. Initial
delivery plus this support fix therefore has **19,544,730 recorded tokens** across
189 responses. Keep the categories separate when comparing first delivery with
post-delivery support.

## Effective work time: what is and is not known

**Complete active backend project time was not recorded.** Neither active model
inference time nor CPU time can be recovered reliably from the available evidence.
The conversation spans quota interruptions and waiting for user decisions; using
its calendar duration would answer a different question.

The following are actual elapsed durations of bounded local verification runs:

| Recorded work | Seconds | Readable duration |
|---|---:|---|
| Successful original-build browser checks | 106.338 | 1m 46s |
| Successful independently extracted ZIP browser checks | 104.239 | 1m 44s |
| Both browser runs, within the final verification | 210.577 | 3m 31s |
| **Final validate → browser → package → extract → browser run** | **220.454** | **3m 40s** |
| Two failed browser attempts, before automated-walker corrections | 117.191 | 1m 57s |
| All three verification run windows, including setup/packaging | 348.700 | 5m 49s |

Do not add these rows together: several are subtotals. The standalone server ran
while its extracted-browser child was running, so those intervals count once.
These local elapsed measurements exclude gaps between recorded attempts, but are
not CPU measurements and do not include the entire design/build process. The
**3m 40s result is verification time, not time to create an apartment**.

The two failed attempts are retained in the ledger. Both concerned the automated
walker's path handling; the eventual original and extracted runs passed on the same
commissioned game build `fba11bc23842a21a`. The later public replay has its own
identity and report; its preparation is excluded from this historical case total.

## Tangible resources and deliverables

| Resource | Observed result |
|---|---|
| Visual inputs | One floor plan and six photos visible in conversation; original image bytes were unavailable locally |
| Model | 43 furniture groups, 167 exported mesh objects, 89,740 triangles |
| Exported GLB | 4,319,484 bytes, embedded geometry/materials; no external model/texture downloads |
| Editable Blender file | 955,910 bytes |
| Initial playable ZIP | 1,308,282 bytes; later packaging/launcher revisions have separately recorded sizes |
| Initial complete source/evidence ZIP | 39,392,452 bytes; includes more than the playable runtime |
| Tools used | Local Python, Node/Playwright, Chrome and Blender |
| Paid external asset generation | No paid image/mesh generator was invoked |
| Hosting | Local loopback server; no hosting service provisioned |

The measured environment used Python 3.12.4, Node 22.22.1, Blender 5.2.2 LTS and
Chrome 154.0.8037.95 on macOS. Hardware-normalized performance, energy use and
memory peaks were not captured. Browser automation is separate from human
physical-keyboard or other-platform acceptance.

## Price reference, not an invented bill

The actual amount billed for this case is **unavailable**. Codex subscription
allowances, purchased credits and API billing are different payment contexts.
Token telemetry alone does not establish which was charged, and the recorded
work does not carry a verified invoice or complete rate/tier history.

For context, the official GPT-6 Astra API page checked on **2026-10-06** lists
standard short-context rates per million tokens of **$10 input, $1 cached input,
$12.50 cache writes and $50 output**. Long-context and processing-tier rates
differ. These are dated API reference rates, not the cost of this Codex session.
See the [official model page](https://developers.openai.com/api/docs/models/gpt-6-astra)
and [pricing](https://developers.openai.com/api/docs/pricing) for current conditions.
We do not multiply a single flat rate by the total token count and call it a bill.

## Make the next project more economical

First replay the example and decide whether its quality and controls fit your need.
Then agree on a small concrete version: rooms, furniture, interactions, visual
target and browser. Reuse the runtime, model patterns and passed tests where their
inputs have not changed. Ask the agent to inspect the relevant implementation
after reading the entry documents, rather than repeatedly absorbing the whole repo.

Use bounded sub-agent tasks for independent work; measure their usage as well as
the main agent. Reserve more capable models for uncertain design/reasoning work
and consider an available lower-cost model for narrow, well-specified tasks. Avoid
unnecessary re-rendering and repeated tests when no relevant input changed. These
are resource-control practices, not a claimed percentage saving.

Start the next case with [the resource template](../templates/resource-usage.example.json)
and follow [the handoff protocol](public-project-handoff.md). A useful comparison
needs the same scene, quality bar, model/tier, device and acceptance tests, including
retries. This repository has no evidence for “faster” or “cheaper” than another
harness yet.
