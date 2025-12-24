# SWEAP Documentation

This directory collects the durable documentation for the SWEAP CLI and related
workflow tooling. Each guide targets a specific audience so task authors,
reviewers, and platform maintainers can jump directly to what they need.

## Audience Guide

- **Task authors.** Start with `../README.md` for a high-level orientation, then
  follow the end-to-end instructions in [task-authoring.md](task-authoring.md).
- **Quality reviewers.** Review the expectations and validation flow in
  [reviewing.md](reviewing.md).
- **Operators & contributors.** Deep-dive into the system architecture in
  [architecture/overview.md](architecture/overview.md) and the backend/API design
  in [architecture/backend.md](architecture/backend.md).
- **Anyone using the CLI.** Consult the command catalogue and manifest schema
  under [reference/](reference/) and keep the
  [faq.md](faq.md) handy for common issues.

## File Layout

- `task-authoring.md` – author workflow, from bundle scaffolding to remote runs.
- `reviewing.md` – reviewer workflow and acceptance checklist.
- `reference/cli.md` – CLI command behaviour, inputs, and outputs.
- `reference/manifest.md` – manifest schema v2 and runner dependency guidance.
- `architecture/overview.md` – current system architecture and roadmap summary.
- `architecture/backend.md` – FastAPI + Supabase design for remote task storage
  and evaluation.
- `architecture/tech-debt.md` – active technical debt themes and desired fixes.
- `faq.md` – troubleshooting guide and answers to common questions.
- `archive/` – retained historical design notes for provenance only.

When updating or adding documentation, prefer placing the content in one of the
sections above. If you are unsure where a new document belongs, add a placeholder
here and open a discussion in the pull request.
