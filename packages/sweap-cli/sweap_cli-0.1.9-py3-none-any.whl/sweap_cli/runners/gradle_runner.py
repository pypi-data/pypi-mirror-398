"""Gradle-based runner for Java guardrail suites."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Mapping

from .base import Runner, RunnerContext


class GradleRunner(Runner):
    """Runner that uses Gradle (or the Gradle wrapper) to execute Java tests."""

    def __init__(self, *, command: str, env: Mapping[str, str] | None = None, raw: dict | None = None) -> None:
        super().__init__(command=command, env=env, raw=raw)

    def setup(self, *, bundle_dir: Path, repo_dir: Path, dependency: object) -> RunnerContext:
        build_rel = dependency.path or "build.gradle"
        build_src = bundle_dir / build_rel
        if not build_src.exists():
            raise FileNotFoundError(f"Missing build.gradle at {build_src}")
        build_dest = repo_dir / build_rel
        build_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(build_src, build_dest)

        settings_rel = (dependency.data or {}).get("settings")
        if settings_rel:
            settings_src = bundle_dir / settings_rel
            if settings_src.exists():
                settings_dest = repo_dir / settings_rel
                settings_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(settings_src, settings_dest)

        gradlew_rel = (dependency.data or {}).get("wrapper")
        if gradlew_rel:
            wrapper_src = bundle_dir / gradlew_rel
            if wrapper_src.exists():
                wrapper_dest = repo_dir / gradlew_rel
                wrapper_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(wrapper_src, wrapper_dest)
                if os.name != "nt":
                    wrapper_dest.chmod(wrapper_dest.stat().st_mode | 0o111)

        env_map = dict(os.environ)
        env_map.update(self.extra_env)

        install_cmd = dependency.install
        if install_cmd:
            formatted = install_cmd.format(
                repo=str(repo_dir),
                build=str(build_dest),
                wrapper=str(repo_dir / gradlew_rel) if gradlew_rel else "",
            )
            subprocess.run(["bash", "-lc", formatted], check=True, cwd=repo_dir, env=env_map)
        else:
            wrapper_cmd = f"./{gradlew_rel}" if gradlew_rel else "gradle"
            bootstrap = (dependency.data or {}).get("bootstrap", f"{wrapper_cmd} --no-daemon testClasses")
            subprocess.run(["bash", "-lc", bootstrap], check=True, cwd=repo_dir, env=env_map)

        return RunnerContext(repo_dir=repo_dir, env=env_map)

    def run_suite(self, *, context: RunnerContext, suite_path: Path) -> int:
        cmd = shlex.split(self.command) + [str(suite_path)]
        proc = subprocess.run(cmd, cwd=context.repo_dir, env=dict(context.env), text=True)
        return proc.returncode

    def teardown(self, *, context: RunnerContext) -> None:
        return
