# CLI Reference

The SWEAP CLI is implemented with [Typer](https://typer.tiangolo.com) and ships
the commands described below. All commands accept `--help` for additional
details. Paths default to the current working directory (`.`) unless otherwise
stated.

## Run Modes

- **Local**: runs on your machine without Modal (`task validate`).
- **Modal (local Modal)**: runs inside a Modal sandbox launched from your machine (`task validate --modal`, `task run --modal`).
- **Remote**: enqueues the run on the backend worker, which executes in its own Modal sandbox and stores artifacts in Supabase (`task run --remote`).

## `task init`

Scaffold a new task bundle.

- `--repo` (**required**) – source repository URL.
- `--commit` (**required**) – commit SHA anchoring the task.
- `--runner` – runner type to scaffold (`pytest`, `node`, or `maven`).
- `--task-id` – override the derived task ID/slug.
- `--directory` – output directory (defaults to `<task_id>`).
- `--force` – overwrite an existing directory after confirmation.

Creates the manifest (`task.json`), guardrail directories, runner-specific
dependency stubs, and placeholder files (`description.md`, `gold_patch.diff`).

## `task validate`

Validate guardrails locally or inside Modal.

- `--modal` – run inside Modal instead of locally (requires Modal credentials).
- `--full` – execute the repository’s native test command described in
  `tests.full`.
- Supported runners: `pytest`, `node`/`npm`/`yarn`, `maven`, and `gradle`.
  Modal sandboxes auto-install the required toolchain (Node for JS runners,
  OpenJDK 17 + Maven/Gradle for Java runners) based on your manifest
  dependencies.
- `--modal-timeout` – override the Modal sandbox timeout in seconds (default
  1800) if your validation needs more or less time.

Baseline guardrails must pass (`pass2pass`) and fail (`fail2pass`) before the
golden patch is applied. After applying the patch both suites must succeed.
`--full` runs prerequisites, the command, and cleanup declared in the manifest.

## `task build`

Build a reusable Modal image or snapshot (best with pytest runners; Node/Maven
workloads still rely on per-run installs inside the sandbox).

- `--name` – friendly Modal image name (`<task_id>-image` by default).
- `--python-version` – override the Python version for the base image.

The command installs declared dependencies, prepares `/opt/sweap-venv`, and
records `environment.modal_image` or `environment.modal_image_id` inside the
manifest for later Modal runs.

## `task run`

Execute the evaluation workflow locally (Modal) or enqueue a remote run.

- `--model` (**required**) – model identifier stored in evaluation artifacts.
- `--modal/--no-modal` – toggle local Modal execution (legacy non-Modal path is
  not implemented).
- `--remote` – enqueue via the backend API and poll for results.
- `--remote-task-id` / `--remote-version` – override remote identifiers when the
  manifest lacks metadata.
- `--llm-command` – custom Codex invocation. Free-form prompts are wrapped in
  the default `codex exec …` prefix if needed.
- `--skip-baseline` – skip baseline guardrail execution (use sparingly).
- `--snapshots` – capture zipped repo snapshots at key stages (pre-baseline,
  post-baseline, post-model/patch, post-patched-tests). Helpful for inspecting
  shared_dirs overlays and file layout; artifacts are saved alongside other run
  outputs (local) or downloadable via `runs-get` for remote runs.
- `--modal-timeout` – sandbox timeout in seconds for Modal evaluation (default
  7200). Increase if your task needs longer than the default.
- `--github-token` – pass a GitHub token for private repos on remote runs; the
  worker injects it into the sandbox for cloning (Modal/local Modal runs use it
  too). Only a masked prefix/suffix is logged for confirmation. Use HTTPS repo
  URLs so header-based auth works (e.g. `https://github.com/org/repo.git`).
- LLM credential options: `--codex-auth`, `--codex-config`, `--codex-api-key`,
  `--codex-api-key-file`, and `--skip-llm-login/--require-llm-login`.

Local Modal runs download artifacts (evaluation JSON + transcript) directly into
the bundle directory. Remote runs store artifacts with the backend and download
them at the end of polling.

## `task submit`

Register or update a task with the backend and upload the bundle archive.

- `--visibility` – `private` (default) or `public`.
- `--remote-id` – update an existing task even if the manifest lacks metadata.
- `--notes` – optional version notes stored with the bundle.

The manifest’s `metadata.remote` section is updated with the task ID, slug,
visibility, and bundle version returned by the backend.

## `task info`

Fetch remote task metadata from the backend.

- `--remote-task-id` – override the task ID stored in the manifest.

Outputs task title, repository details, visibility, status, and latest bundle
version, plus any stored description text.

## `task fetch-bundle`

Download and optionally extract a bundle from the backend.

- `--remote-task-id` – override the manifest’s task ID.
- `--version` – specific bundle version (defaults to recorded or latest).
- `--output` – destination zip path (defaults to `downloaded_bundle.zip`).
- `--extract` – unzip into the working directory after download.

## `task runs-get`

Retrieve a remote run record and (optionally) its artifacts.

- `--bundle-dir` – location to write downloaded artifacts.
- `--download-artifacts` – toggle artifact download.

The command prints the run record as formatted JSON and saves artifacts such as
evaluation reports or transcripts when requested.
