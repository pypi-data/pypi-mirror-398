# Manifest Reference

SWEAP task bundles use `task.json` (schema version 2) to describe the repository
snapshot, guardrail layout, runner configuration, and remote metadata. This
reference summarises each section and the validation rules enforced by the CLI.

All paths in the manifest must be **relative to the bundle root**. Absolute
paths are rejected.

## Top-Level Keys

- `version` – manifest schema version. The CLI currently requires `2`.
- `task_id` – slug used when creating tasks remotely (optional but recommended).
- `repo` – repository metadata:
  - `url` – Git clone URL.
  - `commit` – commit SHA that anchor guardrails and the golden patch.
- `problem` – author-provided description metadata:
  - `title` – optional human-friendly title (defaults to `task_id` during submit).
  - `description_file` – path to `description.md` (defaults to `"description.md"`).
- `tests`
  - `fail2pass_dir` – directory staged for failing guardrails (`tests/fail2pass`).
  - `pass2pass_dir` – directory staged for guardrails that must always pass (`tests/pass2pass`).
  - `shared_dirs` (optional) – additional paths staged for both baseline and patched phases. Each entry can be a string (path) or an object `{ "path": "...", "mode": "fail|merge|overwrite" }`. Paths are copied to the same relative location inside the repo (e.g., `"sample/app/fixtures"` → `/repo/sample/app/fixtures`). Default mode is `fail` (abort if the target already exists); `merge` copies only new files; `overwrite` allows replacing existing files. Existing content is backed up and restored after guardrails run.
  - `shared_dirs_pre` / `shared_dirs_post` (optional) – like `shared_dirs` but staged only for the baseline phase (pre-model/patch) or the patched phase (post-model/patch) respectively.
  - `full` (optional) – config for `task validate --full` (see below).
- `solution`
  - `gold_patch_file` – path to the unified diff applied during validation (defaults to `gold_patch.diff`).
- `runner` – runner configuration (see [Runner Configuration](#runner-configuration)).
- `environment` – dependency descriptors (see [Dependencies](#dependencies)).
- `metadata` (optional) – additional bookkeeping fields. The CLI stores
  backend linkage under `metadata.remote` after `task submit`.

## Runner Configuration

The runner section declares how to execute guardrail suites.

```json
"runner": {
  "type": "pytest",
  "version": 1,
  "command": {
    "default": "pytest -q",
    "baseline": "pytest -q",
    "patched": "pytest -q"
  },
  "env": {
    "PYTHONPATH": "."
  }
}
```

- `type` – runner identifier (`pytest`, `node`, `maven`, or other supported
  plugins).
- `version` – runner schema version. Currently `1`.
- `command` – either a string (`"pytest -q"`) or an object mapping stage names
  to commands (e.g., `"baseline"`, `"patched"`, `"full"`). At least one command
  must be provided. The CLI picks `default`, then `baseline`, then the first
  available command when executing guardrails.
- `env` – optional map of environment variables injected into runner commands.
  Values are coerced to strings.

The CLI converts this section into a `RunnerInfo` instance before invoking
framework-specific logic. Unsupported runner types raise validation errors.

## Dependencies

`environment.dependencies` is a **non-empty array** describing the artifacts
required to install and execute guardrails. Each entry has:

- `kind` – descriptive label (e.g., `"python"`, `"node"`, `"maven"`).
- `path` – relative path to the dependency file (requirements, package.json,
  pom.xml). Paths must stay inside the bundle.
- `install` – optional command template executed before validation/evaluation.
- Additional keys in the object become `data` for the runner (e.g.,
  `lockfile`, `package_manager`, `wrapper`, `bootstrap`).

Runner-specific expectations:

| Runner type | Required dependency |
| ----------- | ------------------- |
| `pytest` / `python` | `{"kind": "python", "path": "requirements.txt"}` |
| `node` / `npm` / `yarn` | `{"kind": "node", "path": "package.json", "lockfile": "package-lock.json", "package_manager": "npm"}` |
| `maven` / `java` / `gradle` | `{"kind": "maven", "path": "pom.xml", "wrapper": "mvnw", "bootstrap": "mvn -B dependency:go-offline"}` |

Templates passed in `install` can use placeholders:

- `{path}` / `{requirements}` / `{package_json}` / `{pom}` – resolved to the
  absolute path of the declared artifact inside the sandbox.
- `{lockfile}` – resolved when `lockfile` is present.
- `{wrapper}` – resolved when `wrapper` is present (e.g., `mvnw`).

The CLI validates that each dependency required by the runner exists and rejects
absolute paths. For python runners, at least one dependency with `kind:
"python"` and a `path` is mandatory.

### Full Test Configuration

`tests.full` provides the command executed by `task validate --full`. Remote
evaluations currently ignore this stanza, but it remains in the schema for
future expansion.

```json
"tests": {
  "fail2pass_dir": "tests/fail2pass",
  "pass2pass_dir": "tests/pass2pass",
  "shared_dirs": [
    "tests/fixtures",
    { "path": "sample/app/package.json", "mode": "overwrite" }
  ],
  "shared_dirs_pre": [
    { "path": "tests/baseline-stubs", "mode": "merge" }
  ],
  "shared_dirs_post": [],
  "full": {
    "command": "npm test",
    "working_dir": ".",
    "env": {
      "NODE_ENV": "test"
    },
    "prerequisites": ["docker compose up -d redis"],
    "cleanup": ["docker compose down"]
  }
}
```

- `command` (**required**) – shell command executed via `bash -lc`.
- `working_dir` – relative directory within the cloned repo (defaults to `.`).
- `env` – environment overrides (stringified).
- `prerequisites` / `cleanup` – arrays of shell commands run before/after the
  main command. Cleanup always runs, even if earlier commands fail.

## Remote Metadata

After `task submit`, the CLI writes:

```json
"metadata": {
  "remote": {
    "task_id": "task-123",
    "slug": "example-task",
    "visibility": "private",
    "bundle_version": 2
  }
}
```

These values are used by `task info`, `task fetch-bundle`, and `task run
--remote` when flags are not provided. Do not hand-edit this section; re-run
`task submit` to refresh it.
