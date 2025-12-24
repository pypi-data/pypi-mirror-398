# SWEAP CLI

Command-line tooling for authoring, validating, and evaluating SWEAP benchmark
tasks. Each task is a self-contained bundle containing repository metadata,
guardrail tests, and a golden patch that can be reproduced locally or inside
Modal sandboxes.

- Documentation index: [docs/README.md](docs/README.md)
- Latest workflow guides:
  - [Task authoring](docs/task-authoring.md)
  - [Reviewer workflow](docs/reviewing.md)
  - [CLI reference](docs/reference/cli.md)
  - [FAQ & troubleshooting](docs/faq.md)

## Quick Start

```bash
# optional: create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install sweap-cli

# scaffold a new task bundle
task init --repo https://github.com/example/project.git --commit deadbeef

# iterate locally until guardrails behave as expected
task validate

# run the modal evaluation pipeline (baseline + model + patched verification)
task run --model codex
```

### Required Credentials

- `SWEAP_API_URL` and `SWEAP_API_TOKEN` for remote submissions and runs (request an API token from the SWEAP team).
- `OPENAI_API_KEY` for Codex access (optional for local runs; mandatory for remote runs processed by our hosted worker).
- `modal` CLI credentials (`modal setup`) if you plan to run Modal evaluations locally.

Add `--runner node` or `--runner maven` during `task init` to scaffold non-Python
bundles. Use `task validate --modal` to reproduce validation inside Modal and
`task build` to cache Modal environments for pytest bundles.

## Core Commands

- `task init` – scaffold manifests, guardrail directories, and dependency stubs.
- `task validate` – run baseline vs. patched guardrails locally or in Modal.
- `task run` – execute the full evaluation loop (baseline, model attempt,
  patched verification, optional full suite) locally or via the backend.
- `task submit` – register/update tasks with the backend and upload bundle
  archives.
- `task build` – prebuild Modal environments for pytest bundles.
- `task info` / `task fetch-bundle` / `task runs-get` – inspect remote metadata,
  download bundles, and retrieve run artifacts.

See the [CLI reference](docs/reference/cli.md) for detailed options.

## Repository Highlights

- `src/sweap_cli/` – CLI entrypoint, runner implementations, Modal orchestration,
  and backend client.
- `api/` – FastAPI + Supabase service used for remote submissions and runs.
- `project-demo/` – sample task bundle used in integration tests.
- `docs/` – task workflows, architecture notes, and FAQs.

## Need Help?

- Troubleshooting and common questions: [docs/faq.md](docs/faq.md)
- Manifest schema and runner expectations:
  [docs/reference/manifest.md](docs/reference/manifest.md)
