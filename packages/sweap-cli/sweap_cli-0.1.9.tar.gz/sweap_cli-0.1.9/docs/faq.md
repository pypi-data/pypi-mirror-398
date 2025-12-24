# Frequently Asked Questions

## How should I manage environment variables and credentials?

- Store shared project settings in `.env` and personal secrets in `.env.local`.
- Codex credentials:
  - Preferred: set `OPENAI_API_KEY` (e.g., via `.env.local`).
  - Alternatives: `--codex-api-key`, `--codex-api-key-file`, or existing
    `~/.codex/{auth.json,config.toml}` with `--codex-auth` / `--codex-config`.
- Remote API access requires `SWEAP_API_URL` and `SWEAP_API_TOKEN`. Remote runs
  refuse to start if either variable is missing.

## The Modal SDK complains about missing `Image.persist`. What now?

Recent Modal releases hide image persistence. `task build` falls back to
snapshotting a sandbox and records `environment.modal_image_id` in the manifest.
If you see `Modal's Python image API is unavailable`, upgrade the SDK
(`pip install --upgrade modal`) and re-run the command.

## How do I clone private repositories inside Modal?

Private repos need credentials inside the sandbox:

- Local/Modal runs: you can export `GITHUB_TOKEN` before running the CLI and it
  will be forwarded into the sandbox for cloning.
- Remote runs: pass `--github-token <PAT>` to `task run --remote` to forward
  your own token for that run. The worker injects it into the sandbox and does
  not store it; only the first/last 3 characters are echoed for confirmation.

If cloning fails, the sandbox will be empty, causing build/tests to fail and the
LLM to complain about an untrusted/non-git directory.

## Why do baseline tests run before the model attempt?

Baseline guardrails ensure the bundle is configured correctly:

- `pass2pass` must succeed on the unpatched repo.
- `fail2pass` must fail until the golden patch is applied.

Use `--skip-baseline` only during targeted debugging; otherwise keep the default
behaviour to catch regressions early.

## Where are evaluation artifacts stored?

- Local Modal runs write `evaluation_<model>.json` and
  `evaluation_<model>.log` into the bundle directory.
- Remote runs store artifacts in Supabase. The CLI downloads them once the run
  completes (`task runs-get <id> --download-artifacts`).

## What does `task build` actually do?

For pytest bundles it copies the task into a Modal image, installs dependencies
into `/opt/sweap-venv`, installs `@openai/codex`, and either persists the image
or snapshots the sandbox. Subsequent Modal runs reuse the prepared environment
to avoid reinstalling packages. Node and Maven runners currently rebuild
dependencies on demand.

## `task run --remote` fails with `JWT expired`. How can I refresh tokens?

Supabase JWTs expire frequently. Re-authenticate using your Supabase credentials
to obtain a fresh access token, set `SWEAP_API_TOKEN` again, and retry:

```bash
curl -s -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"..."}'
```

## Modal downloads fail with `Object not found`.

Confirm:

1. The Supabase storage bucket (`task-bundles` or `run-artifacts`) exists.
2. The worker or CLI environment includes `SUPABASE_SERVICE_ROLE_KEY` (workers)
   or `SWEAP_API_TOKEN` (clients).
3. Signed URLs are consumed before they expire (default 1 hour). Regenerate by
   recreating the bundle or run request.

## How do I override the Codex command?

Pass `--llm-command` to `task run`. If you provide a free-form prompt, the CLI
wraps it in the default `codex exec` invocation automatically. Environment
variable `SWEEP_LLM_COMMAND` is also honoured for backwards compatibility.

## Can I run the full repository test suite?

Yes. Populate `tests.full` in the manifest and run:

```bash
task validate --full
```

The CLI executes optional `prerequisites` and `cleanup` commands around the main
suite and respects custom environment variables and working directory settings.
Remote evaluations currently focus on guardrail suites only.

## How do I troubleshoot run failures?

1. Inspect `evaluation_<model>.json` for stage-level statuses (environment
   setup, baseline, model attempt, patched).
2. Read the paired transcript (`evaluation_<model>.log`) for raw command output.
3. Re-run locally with `task run --modal --model <model>` to reproduce in a
   sandbox you control.
4. If the failure stems from the bundle (missing files, flaky tests), update the
   bundle, rerun `task validate`, and resubmit.
5. If you hit a Modal timeout (e.g., “Runner stopped due to sandbox timeout”),
   increase the sandbox limit with `--modal-timeout <seconds>` on `task run`
   (default is 7200s) or `task validate --modal` (default 1800s), then retry.

## What should I do with legacy documentation?

Historical docs are preserved under `docs/archive/` for reference but should not
be updated. Migrate relevant content into the main guides when you touch those
areas.
