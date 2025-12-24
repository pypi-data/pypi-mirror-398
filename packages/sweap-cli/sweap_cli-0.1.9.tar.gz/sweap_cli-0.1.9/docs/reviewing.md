# Reviewer Workflow

This guide covers the end-to-end process for validating SWEAP bundles authored
by others. Install the CLI with `pip install sweap-cli` (optionally inside a
virtual environment) and ensure you have the required backend credentials.

## 1. Prerequisites

- Supabase/API credentials: `SWEAP_API_URL` and `SWEAP_API_TOKEN`.
- Optional Codex credentials if you plan to reproduce Modal evaluations locally.
- Task ID, bundle version, and relevant run IDs shared by the author.
- Optional local Modal usage: install and configure the `modal` CLI if you want
  to run sandboxes locally. Remote runs rely on the hosted SWEAP worker.

## 2. Inspect Remote Metadata

Use `task info` to inspect the registered task and confirm repo details.

```bash
task info --remote-task-id <task_id>
```

Download the exact bundle version you will be reviewing:

```bash
task fetch-bundle --remote-task-id <task_id> --version <version> --output bundle.zip --extract
```

This hydrates the bundle locally so you can review files without relying on the
author’s filesystem.

## 3. Review the Bundle

1. Read `description.md` for clarity, completeness, and absence of spoilers.
2. Examine `tests/pass2pass` and `tests/fail2pass` to ensure they capture the
   intended behaviour, cannot be trivially bypassed, and are scoped narrowly.
3. Inspect `gold_patch.diff` and, if needed, apply it to the upstream repository
   to judge code quality and broader impact.
4. Check `task.json` for the configured runner, dependencies, and test paths.
   Refer to the [Manifest Reference](reference/manifest.md) if you need to
   cross-check schema expectations.

## 4. Validate Guardrails Locally

Run local validation in the extracted bundle:

```bash
task validate
task validate --modal      # Optional parity check with Modal infrastructure
task validate --full       # Runs repository test command if provided
```

Confirm the golden patch makes fail2pass suites succeed without breaking
pass2pass guardrails. Investigate any flaky behaviour before approving.

## 5. Reproduce Remote Evidence

Check that the author captured model failures on the baseline and success once
patched. You can pull the existing run records:

```bash
task runs-get <run_id> --download-artifacts
```

Or enqueue your own remote run:

```bash
task run --remote --model gpt-5-codex --remote-task-id <task_id> --remote-version <version>
```

Downloaded artifacts include `evaluation_<model>.json` and transcripts that
highlight baseline vs. patched outcomes.

## 6. Provide Feedback

Summarise findings across four areas:

1. **Problem statement** – Is the description complete and actionable?
2. **Guardrails** – Do tests capture the desired behaviour and avoid false
   positives?
3. **Model evidence** – Do baseline attempts fail for the right reasons? Does
   the golden solution succeed?
4. **Code quality** – Does the golden diff meet standards and integrate cleanly?

Return action items or approve the task. Ask the author to resubmit updated
bundles and remote evidence for any revisions.

## 7. Optional Extras

- Smoke-test alternate models (`task run --remote --model <other-model>`) to
  capture benchmarking data.
- File documentation issues when workflows or references need clarification.
