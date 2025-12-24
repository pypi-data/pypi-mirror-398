"""Node-based runner that executes npm scripts for guardrail suites."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Mapping

from .base import Runner, RunnerContext


class NodeRunner(Runner):
    """Runner that uses npm or yarn to execute JavaScript/TypeScript test commands."""

    def __init__(self, *, command: str, env: Mapping[str, str] | None = None, raw: dict | None = None) -> None:
        super().__init__(command=command, env=env, raw=raw)

    def setup(self, *, bundle_dir: Path, repo_dir: Path, dependency: object) -> RunnerContext:
        npm_config = getattr(dependency, "data", {})
        package_json_rel = dependency.path or "package.json"
        lockfile_rel = npm_config.get("lockfile") or "package-lock.json"
        package_manager = npm_config.get("package_manager", "npm")

        package_src = bundle_dir / package_json_rel
        if not package_src.exists():
            raise FileNotFoundError(f"Missing package definition: {package_src}")
        package_dest = repo_dir / package_json_rel
        package_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_src, package_dest)

        lock_src = bundle_dir / lockfile_rel
        if lock_src.exists():
            shutil.copy2(lock_src, repo_dir / lockfile_rel)

        env = dict(os.environ)
        env.update(self.extra_env)

        install_cmd = npm_config.get("install")
        if install_cmd:
            resolved_install = install_cmd.format(
                repo=str(repo_dir),
                package_json=str(package_dest),
                lockfile=str(repo_dir / lockfile_rel),
            )
            subprocess.run(["bash", "-lc", resolved_install], check=True, cwd=repo_dir, env=env)
        else:
            install_command = "npm ci" if package_manager == "npm" else f"{package_manager} install"
            subprocess.run(["bash", "-lc", install_command], check=True, cwd=repo_dir, env=env)

        return RunnerContext(repo_dir=repo_dir, env=env)

    def run_suite(self, *, context: RunnerContext, suite_path: Path) -> int:
        cmd_parts = shlex.split(self.command)
        cmd = cmd_parts + [str(suite_path)]
        proc = subprocess.run(cmd, cwd=context.repo_dir, env=dict(context.env), text=True)
        return proc.returncode

    def teardown(self, *, context: RunnerContext) -> None:
        # Nothing to clean up for npm-based runs
        return

