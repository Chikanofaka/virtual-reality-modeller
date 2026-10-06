# Virtual Space MVP Harness

**Bring a floor plan to life with an AI Copilot—and leave with a game you can
unpack, walk through and play again.**

Describe your space, share the reference material you have, and review a concrete
layout. The agent handles planning data, furniture, navigation, interactions,
diagnosis and packaging. You receive a playable desktop experience, editable
sources, a furnished plan and evidence tied to the delivered build.

**Local game runtime · Codex / Claude Code workflow · no harness API key ·
Python + browser to play**

[Start here: 14-step beginner guide](docs/getting-started.md) ·
[Play the flagship](#play-the-flagship) ·
[Actual time and usage](#what-did-this-project-consume) ·
[Technical reference](docs/harness-reference.md)

## Flagship: a furnished Midtown two-bedroom apartment

![Actual browser screenshot of the furnished Midtown living room](examples/midtown-apartment/images/living-browser.png)

*Actual browser screenshot, not a concept image. The public replay retains this
scene and gameplay; its build identity and verification are in the case study.*

One unscaled floor plan, six house-tour photo observations and a short brief became
a furnished two-bedroom, two-bathroom apartment. The owner accepted approximate
dimensions and a three-stop arrival tour: **television → bedside lamp → balcony**.

| Need, paraphrased | Delivered result |
|---|---|
| Put a TV and sofa in the living room, beds in the bedrooms | 43 authored furniture groups across bedrooms, living/dining, kitchen, baths, laundry and balcony |
| Let me explore the whole apartment | Eight visitable areas, deliberate wall/furniture collision and connected routes |
| Give it a little interaction | A welcome screen, a lamp material change, ordered completion and reset/replay |
| Make it something I can keep | Standalone playable ZIP, Blender master, model generator, plan, reports and screenshots |
| Prove the ZIP works | Original and separately extracted packages exercised in Chrome, including walking and full replay |

![Furnished floor-plan render of the complete apartment](examples/midtown-apartment/images/furnished-floorplan.png)

*Top-down Blender render of the authored model. Dimensions are accepted design
estimates; this is an interactive prototype, not a measured architectural survey.*

[Explore the flagship, evidence and editable assets →](examples/midtown-apartment/README.md)

Two earlier examples show the progression:

| Example | What it demonstrates | Start |
|---|---|---|
| **Midtown apartment — flagship** | A real commission taken from visual references through furnished, interactive delivery | [Case study](examples/midtown-apartment/README.md) / replay below |
| **Pearl Office — preserved baseline** | The detailed historical office scene, desktop controls, explicit navigation and build identity | `python3 scripts/quickstart.py --browser chrome` / [reference](docs/harness-reference.md) |
| **Discovery studio — synthetic trial** | A small, inspectable new-user workflow: ordered desk/chair tasks, completion and reset | [Walkthrough and commands](docs/external-user-trial.md) |

The studio is explicitly synthetic. Pearl has its own historical source provenance;
see [third-party notices](THIRD_PARTY_NOTICES.md). Neither example supplies approval
or measurements for a new user's room.

## Play the flagship

1. Download this **whole repository** using GitHub's **Code → Download ZIP**, then
   extract it. Or clone your fork.
2. Install Python **3.10+** and a WebGL-capable desktop browser. Chrome is the
   tested browser for this apartment.
3. Open Terminal on macOS or PowerShell on Windows **inside the extracted repository
   folder**. You should see `README.md` and `scripts/harness.py`.
4. Run the command for your system:

**macOS**

```sh
python3 scripts/replay_midtown.py --no-open
```

**Windows PowerShell**

```powershell
py -3 scripts/replay_midtown.py --no-open
```

5. Copy the entire printed localhost URL into Chrome, keep the terminal open, and
   click **Enter**. Use **WASD** to walk, **mouse drag or arrows** to look, **E** to
   interact and **R** to replay. Stop the server with **Ctrl+C**.

This checks and extracts the [bundled playable ZIP](examples/midtown-apartment/midtown-playable.zip).
It does not call an AI model, generate assets, install npm packages or use Blender.
If you download that playable ZIP separately, extract it and run `python3 launch.py`
on macOS or `py -3 launch.py` on Windows from the folder containing `launch.py`.
The [full guide](docs/getting-started.md) explains paths, installation and common errors.

**Compatibility:** macOS Chrome was actually exercised. Windows commands use the
portable Python launcher but Windows acceptance remains unverified. The model is
single-floor; mobile, VR headsets and multi-user play need additional work.

## Create your own space: the 14 steps

The [complete beginner manual](docs/getting-started.md) explains every step, with
copyable prompts, macOS/Windows commands and expected results. No JSON writing is
required from the person commissioning a space.

1. **Get the right folder.** Download/extract the complete repository, or fork and
   clone it. A playable ZIP is for playing one finished result.
2. **Check prerequisites.** Python and a browser for playback; a coding-agent
   account for creation. Blender and Node are only needed for relevant authoring/tests.
3. **Find the repository root.** Verify `scripts/harness.py` exists before running
   commands. Use your actual folder path, including spaces or OneDrive locations.
4. **Run the flagship once.** Learn what the current scene quality and controls feel like.
5. **Try the game loop.** Visit the TV, lamp and balcony; reset and replay.
6. **Open the repo in your agent.** In Codex, select the local folder. In Claude
   Code, start `claude` from that folder. This folder access is the harness connection;
   there is no harness MCP endpoint to configure.
7. **Paste the starting brief.** Use the [ready-to-copy prompt](docs/getting-started.md#7-give-the-agent-the-starting-brief).
   Ask the agent to read the four entry documents and inspect existing changes.
8. **Share your available evidence.** Floor plan, photos, entrance and any reliable
   measurement. Say when something is unknown.
9. **Define a small first experience.** Choose rooms, visual expectations, player
   actions and target browser. Set a checkpoint before major scope/cost increases.
10. **Review and accept a specific layout.** The agent presents furniture, estimated
    dimensions, doorways, routes, gameplay and acceptance criteria for your decision.
11. **Delegate the local build.** The agent models, implements, runs, diagnoses and
    repairs within the authorization you gave.
12. **Require actual evidence.** Check the exact build's walking, collisions,
    interactions, completion and replay—not merely a screenshot of a start screen.
13. **Unpack the delivered game.** Run its `launch.py` from the correct directory.
    Keep the terminal open and use its exact URL.
14. **Keep the source and resource record.** Save the editable project, build ID,
    reports, limitations and measured usage so another session can continue it.

Provider setup: [official Codex quickstart](https://learn.chatgpt.com/docs/quickstart),
[Codex CLI](https://developers.openai.com/codex/cli),
[Claude Code quickstart](https://code.claude.com/docs/en/quickstart).
Account access and installation details come from those providers. The Claude Code
route is documented; this case was developed using Codex. The game runs locally,
while agent prompts/images may be processed by your chosen provider.

## What did this project consume?

**Real recorded GPT-6 Astra usage, not a hypothetical estimate:**

| Metric | Midtown reference case |
|---|---|
| Intake → first completed delivery | **18,136,004 recorded tokens across 179 responses** |
| Input breakdown | 1,058,289 uncached + 16,928,000 cached input |
| Output | 149,715 tokens, including reasoning already counted within output |
| Later Finder launch repair | 1,408,726 additional recorded tokens; initial delivery plus repair: **19,544,730** |
| Final original + extracted-package verification | **3m 40s** elapsed; this is verification time, **not apartment creation time** |
| All three recorded verification attempts | **5m 49s** across run windows; interruption gaps excluded |
| Complete active backend project time / actual bill | **Not captured**; no invented hours or currency total |
| Asset footprint | 4.32 MB GLB, 0.96 MB editable Blender file; no paid external asset generator invoked |

About 94% of the initial run's input was cached. Input includes repeated context
across requests; this is not 18 million unique words. The first run also added
harness features and repaired tests, so it is not a clean repeat-project budget.
Missing telemetry is disclosed rather than counted as zero. Playing the finished
example requires no model tokens.

[Read the scope, actual ledger, timing exclusions and dated price reference →](docs/resource-budget.md)

We optimize for an accepted result with evidence: agree scope early, reuse the
runtime, inspect relevant files, bound delegated tasks and avoid repeating
unchanged work. We have not run a matched comparison with competing harnesses and
do not claim an unmeasured speed or cost advantage.

## For agents and contributors

Read [instructions.md](instructions.md),
[the harness skill](skills/virtual-space-mvp-harness/SKILL.md) and
[the orchestrator prompt](prompts/00-orchestrator.md). Then inspect the relevant
implementation. The CLI sequence is:

`init → ingest → interrogate → plan → approve → build → validate → play → package`

The [technical reference](docs/harness-reference.md) contains full commands,
contracts, dependency setup, tests and preserved history. Run the whole harness
with `python3 scripts/verify_harness.py --browser` when the optional browser tooling
is installed; each run writes actual evidence under `test-results/`.
The [local handoff checks](docs/evidence/public-handoff-checks.json) summarize the
current regression tests, replay entry command and documentation review.

New public projects should include a flagship, beginner onboarding and an honest
resource record. Follow [the reusable handoff protocol](docs/public-project-handoff.md)
and [resource template](templates/resource-usage.example.json), including projects
started from a Ready queue. Board status alone is not publication authorization.

Known boundaries: authored modelling rather than automatic photo reconstruction;
single-floor 2D navigation; horizontal nearby interactions with optional declared
wall occlusion; no built-in physics, save system, multiplayer or WebXR. Original
reference-photo files and raw private conversation/usage logs are not part of the
Midtown showcase. New-user plans need their own review. Publishing and paid
generation follow the user's authorization.
