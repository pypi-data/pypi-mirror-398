"""Runner interfaces for executing guardrail suites across frameworks."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional


@dataclass
class RunnerContext:
    """Context shared across runner operations."""

    repo_dir: Path
    env: Mapping[str, str]
    scratch_dir: Optional[Path] = None


class Runner(abc.ABC):
    """Abstract runner interface used by validation/evaluation flows."""

    def __init__(self, *, command: str, env: Mapping[str, str] | None = None, raw: dict[str, Any] | None = None) -> None:
        self.command = command
        self.extra_env = dict(env or {})
        self.raw_config = raw or {}

    @abc.abstractmethod
    def setup(self, *, bundle_dir: Path, repo_dir: Path, dependency: Any) -> RunnerContext:
        """Prepare the execution environment and return the runner context."""

    @abc.abstractmethod
    def run_suite(self, *, context: RunnerContext, suite_path: Path) -> int:
        """Execute the runner command against the provided suite; return exit code."""

    @abc.abstractmethod
    def teardown(self, *, context: RunnerContext) -> None:
        """Clean up any runner-produced artifacts."""
