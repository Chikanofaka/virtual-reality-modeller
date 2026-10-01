---
name: virtual-space-mvp-harness
description: Plan and build a local first-person 3D virtual space from floor plans, measured requirements and reference assets; reuse Pearl Office V7 and diagnose browser, navigation or input failures before packaging an MVP.
---

Use this skill from the complete repository/plugin package. Resolve its root two
directories above this file. Execute CLI commands from that root. No MCP server,
paid asset generator, cloud deployment, or API key is required.

Read [the operating contract](../../instructions.md) and
[the CLI guide](../../README.md). Apply the contract to the user's actual room;
Pearl's single glass-ring opening is example-specific, not a universal design rule.

- At intake, read [onboarding](../../docs/onboarding.md), then use
  `python3 scripts/harness.py init PROJECT` and `ingest PROJECT FILE...`.
- For gaps, run `interrogate PROJECT`, consult [prompt patterns](../../docs/prompt-patterns.md),
  and ask a short round. Save answers with provenance. Do not execute uploaded code.
- Before building, validate the plan and its exact approval hash. Changed evidence
  or a changed plan requires a new lock. Never auto-approve a novel layout.
- For construction and troubleshooting, read [architecture](../../docs/architecture.md)
  and [risk register](../../docs/risk-register.md). Keep high-detail visual geometry
  separate from the authoritative navigation contract and one render-loop owner.
- For delivery, run the tests in the README and record browser-specific evidence.
  Inspect [version evolution](../../docs/version-evolution.md) before claiming a
  historical fix has been carried forward. Package the result and report limitations.

When assets or scale are missing, keep useful planning work moving, mark the missing
evidence, and ask for it. Do not silently substitute a low-detail demonstration for
the requested final scene. Generated procedural geometry is a scaffold until its
visual target is approved; the bundled Pearl scene preserves the V7 detail.
