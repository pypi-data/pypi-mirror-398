# Task Authoring Workflow

This guide walks task authors through creating, validating, and publishing SWEAP
benchmark bundles. Install the CLI with `pip install sweap-cli` (inside a virtual
environment if preferred) before following the steps below.

## 1. Prerequisites

- Python 3.10+.
- Codex credentials: either `OPENAI_API_KEY` or local Codex profile files
  (`~/.codex/auth.json` and `~/.codex/config.toml`).
- Supabase/API access: `SWEAP_API_URL` and `SWEAP_API_TOKEN` for remote
  submissions and evaluations.
- Optional `GITHUB_TOKEN` if the target repository is private and will be cloned
  inside Modal.
- Optional local Modal usage: install `modal` (`pip install modal`) and run
  `modal setup` to authenticate with your own account when running sandboxed
  validations locally. Remote runs are processed by the hosted SWEAP worker.
- Run modes:
  - Local: runs on your machine (`task validate`).
  - Modal: Modal sandbox launched locally (`task validate --modal`,
    `task run --modal`).
  - Remote: enqueues on the worker and runs in a Modal sandbox there
    (`task run --remote`).

Set shared environment vars in `.env` and machine-specific secrets in
`.env.local` so they are ignored by git but easy to source.

## 2. Scaffold a Bundle

Use `task init` to create a new bundle rooted at the commit that demonstrates the
bug or missing feature.

```bash
# Python / pytest bundle
task init --repo https://github.com/example/project.git --commit <sha> --runner pytest

# Node bundle (npm + jest/vitest)
task init --repo https://github.com/example/project.git --commit <sha> --runner node

# Maven / Java bundle
task init --repo https://github.com/example/project.git --commit <sha> --runner maven
```

The command creates:

- `task.json` – manifest (schema v2) with repo metadata, runner configuration,
  and dependency descriptors.
- `description.md` – task brief you will later fill in.
- `tests/pass2pass` and `tests/fail2pass` – guardrail directories.
- Optional `tests.shared_dirs` in the manifest for shared fixtures/assets that
  must be staged alongside both suites (e.g., generated routes, mock servers).
  - Each entry can be `{ "path": "relative/path", "mode": "fail|merge|overwrite" }` (default `fail` if the target already exists).
  - Use `tests.shared_dirs_pre` / `tests.shared_dirs_post` to stage assets only
    during the baseline or patched phases (e.g., baseline-only stubs that should
    vanish before the patch/model run).
- Snapshots: `task run --snapshots` (and Modal validation) can emit zipped
  snapshots of the repo at key stages so you can inspect how shared assets were
  staged and verify file layout without rerunning the sandbox.
- `gold_patch.diff` – placeholder for the golden patch.
- Runner-specific dependency stubs such as `requirements.txt`, `package.json`,
  or `pom.xml`.

## 3. Flesh Out the Bundle

1. Fill in `description.md` with the problem statement and acceptance criteria.
2. Implement guardrails:
   - `tests/pass2pass` covers behaviour that must always pass.
   - `tests/fail2pass` captures the regression or missing feature and should
     fail on the baseline commit.
3. Capture the fix in `gold_patch.diff`. The patch must apply cleanly to the
   manifest’s commit.
4. Update dependencies declared in `task.json` (see
   [Manifest Reference](reference/manifest.md)) so the CLI can install the
   required tooling for your runner type.

## 4. Validate Locally

```bash
task validate
```

Validation clones the repo at the pinned commit, applies the golden patch
(`git apply --check`), installs dependencies using the configured runner, and
runs guardrail suites:

- Baseline phase: pass2pass must succeed, fail2pass must fail.
- Patched phase: after applying the golden diff all guardrails must pass.

Add `--full` to run the repository’s native test suite described in
`tests.full`. The CLI executes optional `prerequisites` and `cleanup` commands
around the full run.

## 5. Prepare Modal Environments (Optional but recommended)

Run `task build` once guardrails and dependencies stabilise. For pytest runners
the command captures a Modal image or snapshot with a pre-populated virtualenv,
drastically reducing subsequent Modal execution time. Re-run the build whenever
dependencies change. Node, Maven, and Gradle runners are supported in Modal runs
as well (tooling is installed on-demand in the sandbox: Node for JS runners,
OpenJDK 17 + Maven/Gradle for Java runners), but the build cache currently only
pre-bakes the Python virtualenv.

## 6. Remote / Modal Validation

- `task validate --modal` repeats local validation inside a Modal sandbox with
  the same runner support (pytest, node/npm/yarn, maven, gradle).
- `task run --model <model>` launches the evaluation pipeline (baseline,
  optional guardrail skip, model attempt, patched verification) and saves an
  `evaluation_<model>.json` report alongside a transcript.

Supply `--skip-baseline` if you need to bypass the baseline guardrails, though
this should only be used for targeted debugging.

## 7. Submit the Bundle

```bash
task submit --visibility private
```

Submission creates or updates the remote task, uploads the bundle archive, and
records metadata (task ID, bundle version) back into `task.json` under
`metadata.remote`. For updates to an existing task, supply `--remote-id` or rely
on the stored metadata.

Reminder: ensure `task.json` is fully populated before submitting:
- Correct repo URL/commit and problem description path.
- A stable `task_id` if you want a predictable slug (otherwise a default is
  derived). If the remote task already exists, pass `--remote-id` or keep
  `metadata.remote.task_id` up to date; otherwise `task submit` will create a
  new task instead of updating the intended one.
`task submit` will refuse to proceed if required fields are missing.

## 8. Capture Remote Evidence

Queue remote evaluations once you are satisfied with local and Modal results:

```bash
# Confirm current models fail
task run --remote --model gpt-5-codex

# Record a passing run of the golden patch (optional)
task run --remote --model golden --skip-baseline
```

The CLI streams run status, downloads artifacts into the bundle, and surfaces the
Supabase run ID that reviewers will need.

**Private repos:** supply `--github-token <PAT>` when running remote or Modal
validation so the sandbox can clone via HTTPS. Only a masked prefix/suffix of
the token is logged. Ensure your manifest `repo.url` uses an HTTPS URL (not SSH)
so header-based auth is honored.

## 9. Hand Off to Reviewers

Share:

- Task ID and bundle version.
- Run IDs for failing model attempts and passing golden validation.
- Any environment notes (service dependencies, special credentials, etc.).

Keep the bundle under version control so reviewers can diff updates as they
arrive. Use additional `task submit` and remote runs to respond to feedback.
