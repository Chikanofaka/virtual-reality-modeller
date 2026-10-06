# Your first space: a 14-step guide

You describe the place and decide whether the proposed layout feels right. Your
coding agent turns that brief into a plan, builds the scene, runs checks and delivers
a playable ZIP. You do not need to write JSON, draw navigation polygons or learn
Blender to commission a project.

The included Midtown apartment shows the destination: a furnished two-bedroom,
two-bathroom home with desktop walking, a television, a bedside lamp and a balcony
discovery sequence. It is locally authored geometry based on a floor plan and photo
observations, with explicitly accepted approximate dimensions. It is not automatic
photogrammetry or a surveyed building model.

**Only want to play?** Follow steps 1–5. **Want your own space?** Continue through
step 14. Before commissioning a similar project, read the
[measured resource reference](resource-budget.md); playing an existing build does
not require an AI model, while commissioning a new one consumes your agent plan's
usage.

## 1. Choose the right download

There are two different kinds of folder:

| What you have | What it is for | File that identifies it |
|---|---|---|
| The complete GitHub repository | Running examples and asking an agent to create your own project | `scripts/harness.py`, `README.md`, `instructions.md` |
| An extracted playable ZIP | Playing one finished build | `launch.py`, `runtime/`, `validation.json` |

To work on your own project, open the repository on GitHub, select **Code → Download
ZIP**, then extract it. On Windows, use **Extract All**; viewing files inside a ZIP
is not extraction. Keep the whole extracted folder together.

If you already use Git, you can fork the repository into your account and clone
your fork instead. Forking creates a GitHub copy; cloning creates the local folder
your agent can use. Neither is required for a first local trial. A downloaded ZIP
has no Git history, which is normal; the agent should report that fact rather than
pretend it has checked a branch. You can publish your work later by a separate
decision.

## 2. Install only what your task needs

| Task | Needed | Not needed for this task |
|---|---|---|
| Play the bundled Midtown apartment or Pearl Office | Python **3.10+**, a desktop WebGL browser; use Chrome for the Midtown reference | AI account, Node, npm, Blender, API key |
| Commission your own project | Complete repository, Python, an agent that can read and edit your local folder; access to that agent's service | A harness-specific account, MCP server or harness API key |
| Author or change a Blender model | Blender and the model's build instructions | Blender is not required to play an exported model |
| Run JavaScript and automated browser tests | Node **20+**, repository test dependencies, Playwright and a compatible installed browser | These are development checks, not player prerequisites |

Install Python from [python.org](https://www.python.org/downloads/) if you do not
already have it. Open a new terminal after installation. Anaconda is not required.
The recorded Midtown build used Python **3.12.4**, Node **22.22.1**, Blender
**5.2.2 LTS** and Chrome **154.0.8037.95** on macOS. These are the measured versions,
not a promise that every other version has been tested.

Windows commands below are a portable launch recipe; the Midtown acceptance run
was on macOS Chrome. Windows, Linux, Safari and mobile acceptance for this apartment
have not been demonstrated by those results.

## 3. Open a terminal in the repository folder

A terminal is a text window for running a command. `cd` means “change directory.”
The command acts inside the current directory, so finding the right folder comes
before launching anything.

**macOS:** open **Terminal**. Type `cd `, including the space, drag the extracted
repository folder from Finder into Terminal, and press Return. This avoids guessing
whether your folder is on Desktop, Downloads or an iCloud location. Alternatively,
use a quoted full path, replacing this example with your actual folder:

```sh
cd "/Users/your-name/Downloads/virtual-reality-modeller-main"
pwd
ls scripts/harness.py
python3 --version
```

**Windows:** open the extracted repository in File Explorer, copy its full folder
path from the address bar, then open **PowerShell** and use that path:

```powershell
Set-Location "C:\Users\your-name\Downloads\virtual-reality-modeller-main"
Get-Location
Test-Path .\scripts\harness.py
py -3 --version
```

`Test-Path` should print `True`; the macOS `ls` command should list the file. Python
should report 3.10 or newer. If Windows does not recognize `py`, try `python
--version`; if that reports a suitable installed Python, use `python` in place of
`py -3` below. If neither works, finish the Python installation before continuing.

Do not assume the Windows Desktop is `C:\Users\your-name\Desktop`: OneDrive may
move it. The folder name after extraction may also differ from these examples.
Use the actual path, keep quotation marks around paths containing spaces, and omit
the terminal prompt itself when copying a command.

## 4. Launch the flagship example

From the repository root, run one command:

**macOS**

```sh
python3 scripts/replay_midtown.py --no-open
```

**Windows PowerShell**

```powershell
py -3 scripts/replay_midtown.py --no-open
```

The script checks the bundled archive, extracts a fresh copy under
`projects/example-replays/`, verifies its runtime files and prints a local address.
Copy the **entire printed URL** into Chrome, including `?build=...`. Keep Terminal
or PowerShell running. The command continues running because it is serving the
game; that is expected.

This replays a finished build from
`examples/midtown-apartment/midtown-playable.zip`. It does not regenerate the model
or use an AI service. You may omit `--no-open` to let the script open your default
browser; if the default is not Chrome, use Chrome manually for the reference run.

For the earlier Pearl Office example, use
`python3 scripts/quickstart.py --browser chrome` on macOS, or
`py -3 scripts/quickstart.py --no-open` on Windows and open the printed address in
Chrome. The [synthetic studio trial](external-user-trial.md) explains the smaller
two-object discovery game and its full planning workflow.

## 5. Walk through the result

Click **Enter** in the game. Click the game view if another control has keyboard
focus.

| Control | Action |
|---|---|
| W / A / S / D | Walk forward / left / back / right |
| Hold the mouse button and drag | Look around |
| Arrow keys | Look without dragging |
| Shift while walking | Move faster |
| E near a target | Interact |
| M | Show or hide the minimap |
| Q | Change rendering quality |
| R | Return to the entrance and reset the game |

In Midtown, approach the **living-room television**, press E, then find the
**primary-bedroom bedside lamp** and press E. Finish at the **balcony** with E.
Press R and try the sequence again. The other rooms can be explored freely.

When finished, return to the terminal and press **Ctrl+C**. That stops this local
server. Restart the command for a later visit and use its newly printed URL; an old
browser tab or bookmarked port may point to a different session.

## 6. Choose Codex or Claude Code

“Connect the harness” means giving a coding agent access to the **complete local
repository folder** and asking it to read the repository's instructions. There is
no harness API key or MCP endpoint to configure. This is not a claim that a plugin
has been installed into your account.

**Codex:** follow the official [desktop quickstart](https://learn.chatgpt.com/docs/quickstart)
to download the app, sign in, open the local repository folder and choose Codex for
software-development work. Prefer a terminal interface? Follow the official
[Codex CLI setup](https://developers.openai.com/codex/cli), then start it in this
same folder. Platform availability and account requirements belong to those
official instructions.

**Claude Code:** install it using the official
[quickstart](https://code.claude.com/docs/en/quickstart). In a terminal, check
`claude --version`, change into the repository folder as in step 3, then run
`claude` and follow its sign-in flow. This is a documented integration route;
Claude Code was not the tool used for the Midtown verification run.

The harness serves finished games locally with bundled runtime assets. Your coding
agent is a separate service: prompts, images and repository context may be sent to
its provider according to your agent settings and plan. “Local-first harness” does
not mean “offline AI.” Decide which private materials you are comfortable sharing
before attaching them to an agent conversation.

## 7. Give the agent the starting brief

Start a new conversation inside the opened folder. Copy this prompt and replace
the square-bracketed parts with a sentence in your own words. “I don't know” is a
useful answer; you do not need to fill in technical details.

```text
Be my spatial-game Copilot. Use this repository's harness to help me complete
a runnable project, from requirements to a tested playable ZIP.

First locate the actual repository root and inspect existing changes. Report
the branch and git status if this is a Git checkout; say so if it is a ZIP copy.
Read README.md, instructions.md,
skills/virtual-space-mvp-harness/SKILL.md and prompts/00-orchestrator.md.
Then inspect the implementation relevant to the current stage.

My space or experience: [describe it, or ask me to choose a small first case].
My materials: [local file paths, floor plan, photos, or none yet].
What the player should do: [my idea, or help me define it].
Device and appearance: [for example, desktop Chrome and a furnished apartment].

Create a new project for me. Do not reuse an example's dimensions, objectives
or approval as my requirements. Record sources, measurements, accepted design
estimates, assumptions and unresolved questions separately. Ask at most two
important questions per round and keep working on independent tasks.

Translate my descriptions into layout, scale, entrances, clear routes,
collisions, interactions and acceptance checks. Do not ask me to write JSON.
Present the specific layout and gameplay for review before locking the plan.
Once I accept that revision, continue authorized local implementation, repair,
tests and packaging without asking me to repeat the same authorization.

I delegate routine local file operations, modelling, diagnostics and tests to
you. Explain any environment permission request and request only what is needed.
Keep the work local. Do not push, publish, spend generation credits or upload
materials to additional services without my explicit authorization.

Deliver a playable ZIP, editable source and necessary assets, launch guidance,
the exact build identity, verification report and screenshots. Extract the ZIP
elsewhere and actually check launch, walking, interactions, completion and replay.
Separate automated checks from any human/device checks not performed.

Record active work time and model usage from available evidence as we work.
Distinguish elapsed time, overlapping work and cumulative usage counters.
Mark unavailable metrics unknown; do not invent token counts or costs.
Use docs/resource-budget.md for the reporting method and previous case evidence.
```

The agent's first useful response should identify the folder, describe what this
harness can produce, establish your new project and ask a small set of questions.
If it cannot access the files, correct the open folder before giving it more
design instructions.

## 8. Supply the evidence you have

Keep your original files in a clearly named local folder. Give the agent their
paths or attach them using your agent's supported interface. Useful inputs are a
floor plan, room photos, the entrance location and one reliable measurement.

Explain which photo belongs to which room if you know. If a dimension is unknown,
say so. The agent can propose a scale for an experience prototype, but must label
it as an estimate and show it to you. “A typical two-bedroom apartment” establishes
an intention, not a measured area.

Local file bytes can be inventoried and hashed. A picture visible only in a chat
may support visual observations without being available as a local original. Ask
the agent to record that distinction, as it did for Midtown. Do not let it claim
to have preserved or measured an original file it cannot access.

## 9. Agree on a small first experience

Decide what a successful first visit looks like. For example: enter through the
foyer, walk into each room, turn on the television, light a bedside lamp, reach the
balcony and restart. Tell the agent whether layout, visual similarity, game
mechanics or performance matters most to you.

The current harness supports a single-floor first-person space, declared movement
barriers, ordered nearby interactions and optional changes to named mesh materials.
Stairs, physics, multiplayer, persistent saves and headset support require extra
implementation and corresponding tests. A simpler agreed scope generally needs
less modelling and less verification than a new system.

Ask for a short budget checkpoint before a major increase in visual detail or
scope. The [resource reference](resource-budget.md) explains what was actually
measured for the flagship and which quantities remain unavailable.

## 10. Review a concrete layout, then approve that revision

Expect a furniture plan or preview, proposed dimensions, entrance and route,
interaction sequence, assumptions and acceptance criteria. Check the things you
care about: the correct rooms, beds in bedrooms, television opposite seating,
doors with space to pass and a clear route to every objective.

You can reply in ordinary language: “Move the sofa away from the balcony door,”
or “Accept V1; continue the local build.” Approval applies to the version you saw.
The agent records it and runs the plan-lock command on your behalf. Passing a
test does not replace your design decision.

Changed plans or source evidence invalidate the old technical lock. The agent
must explain what changed and establish the appropriate approval basis for the
new version, without treating an unrelated example's approval as yours.

## 11. Let the agent build and diagnose

The agent now handles scene construction, selected assets, navigation data,
interaction wiring and local builds. It should retain build history and keep the
original evidence. You may see a permission prompt if your platform restricts a
local server, browser automation or a modelling application; the agent should
identify the concrete action and its purpose.

For an ordinary local build, no paid mesh generator or external hosting service
is required. If an optional service would improve the result, the agent should
first explain the asset, destination and cost that need your decision.

Ask for meaningful progress updates: what is complete, what failed, what was
fixed and whether the accepted scope changed. The underlying CLI workflow is
`init → ingest → interrogate → plan → approve → build → validate → play → package`;
you do not have to type those commands while the agent is doing the work.

## 12. Require evidence from the delivered build

Before accepting delivery, ask the agent to show evidence for:

- Startup of the original build and a separately extracted playable ZIP.
- Walking from the entrance to each agreed room and interaction target.
- Movement blocked by declared walls and furniture, with clear doorways.
- Correct interaction order, visible feedback and completion.
- Reset and a second complete playthrough.
- Matching build identities, relevant error logs and actual browser screenshots.

Automated browser input is useful evidence. It is not the same as a person trying
a physical keyboard on every operating system. The report should name the tested
browser and state what remains unverified. If a check fails, expect a fix and
retest, or a clear account of the unresolved problem—not an unsupported “passed.”

## 13. Unpack and launch your own finished game

Save both deliverables: the **playable ZIP** for visits and the **source project**
for later changes. Extract the playable ZIP into a new folder. Open that folder
and find `launch.py`; some extraction tools add an outer folder, so go one level
deeper if necessary.

**macOS Terminal** — substitute your actual extracted path:

```sh
cd "/Users/your-name/Downloads/my-space-playable"
ls launch.py
python3 launch.py --no-open
```

**Windows PowerShell** — substitute your actual extracted path:

```powershell
Set-Location "C:\Users\your-name\Downloads\my-space-playable"
Test-Path .\launch.py
py -3 launch.py --no-open
```

Copy the entire printed URL into Chrome and leave the terminal open while playing.
Do not double-click `runtime/index.html`; the game uses a local server. Do not run
`python3 launch.py` from Desktop unless Desktop itself contains that file. The
repository root uses scripts under `scripts/`; the extracted game uses its own
top-level `launch.py`.

Give your agent the handoff's build ID if you report a problem. Avoid editing files
inside `runtime/` in a finished package: the integrity check intentionally rejects
changed game bytes. Make changes in the source project and build a new package.

## 14. Keep a useful handoff for the next session

Keep the playable ZIP, editable source, plan, asset sources and licenses, build ID,
validation report, screenshots and launch instructions together. Read the reported
limitations before assuming that a device or interaction was tested.

For changes later, reopen the source folder in your agent and say:

```text
Resume this project. Read its handoff, current plan and approval, source inventory
and verification report. Check existing changes before editing. I want to change
[describe the change]. Explain the affected layout or gameplay, preserve the
previous playable, and build and verify a new delivery within that scope.
```

Each handoff should also preserve the measured resource record: model names where
known, active work intervals, tool execution durations, usage counters and their
limits. This makes the next decision about quality, cost and time more concrete
than an unsupported universal estimate.

## If something does not launch

| What you see | What to do |
|---|---|
| `can't open file ... launch.py` | You are in the wrong folder, or the ZIP is not fully extracted. Find `launch.py`, change into that folder, then run it. |
| `scripts/harness.py` cannot be found | Open the complete repository root, not a playable folder or its parent. |
| Python is not found, or is too old | Install Python 3.10+, reopen the terminal and repeat the version check. On Windows, try the verified `python` command if `py` is unavailable. |
| `Build integrity failed` after browsing the old Midtown package in Finder | Use the current bundled archive. Its launcher ignores unmanifested `.DS_Store` Finder metadata while retaining game-file integrity checks. |
| Integrity failure lists changed, missing or unexpected game files | Preserve the error, extract a fresh complete ZIP into a new folder and retry. Ask the agent to investigate persistent differences. Do not disable verification. |
| The browser shows an old game, a 409 error or cannot connect | Keep the current server running and open its exact newly printed URL. Check the build badge. Do not reuse an old tab's port. |
| The terminal appears to sit still after printing a URL | The local server is running normally. Visit the URL; use Ctrl+C to stop it. |
| A conda startup warning appears | Anaconda is not required by this harness. Check whether `python3 --version` succeeds, then read the actual launcher error separately. Avoid changing your whole conda installation to solve a folder mistake. |
| Keys seem inactive | Click Enter and the game view, release held keys, then try WASD or the on-screen controls. Report the browser and build ID if it persists. |
| A platform denies localhost or a browser launch | Read the permission request and authorize the specific local action if you intend to run it. `--no-open` avoids automatic browser opening; it still needs a local server. |

For a useful support report, include the operating system, browser version, build
ID, exact command, current folder and full error text. Do not include credentials
or private photos unless they are necessary and you choose to share them.
