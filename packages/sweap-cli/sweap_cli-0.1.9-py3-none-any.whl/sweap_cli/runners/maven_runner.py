"""Maven-based runner that executes Java guardrail suites.""" 

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Mapping

from .base import Runner, RunnerContext


class MavenRunner(Runner):
    """Runner that uses Maven/Gradle-compatible installs to run Java tests."""

    def __init__(self, *, command: str, env: Mapping[str, str] | None = None, raw: dict | None = None) -> None:
        super().__init__(command=command, env=env, raw=raw)

    def setup(self, *, bundle_dir: Path, repo_dir: Path, dependency: object) -> RunnerContext:
        pom_rel = dependency.path or "pom.xml"
        package_src = bundle_dir / pom_rel
        if not package_src.exists():
            raise FileNotFoundError(f"Missing pom.xml at {package_src}")
        package_dest = repo_dir / pom_rel
        package_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_src, package_dest)

        mavenw_rel = (dependency.data or {}).get("wrapper")
        if mavenw_rel:
            wrapper_src = bundle_dir / mavenw_rel
            if wrapper_src.exists():
                wrapper_dest = repo_dir / mavenw_rel
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
                pom=str(package_dest),
                wrapper=str(repo_dir / mavenw_rel) if mavenw_rel else "",
            )
            subprocess.run(["bash", "-lc", formatted], check=True, cwd=repo_dir, env=env_map)
        else:
            bootstrap = (dependency.data or {}).get("bootstrap", "mvn -B dependency:go-offline")
            subprocess.run(["bash", "-lc", bootstrap], check=True, cwd=repo_dir, env=env_map)

        return RunnerContext(repo_dir=repo_dir, env=env_map)

    def run_suite(self, *, context: RunnerContext, suite_path: Path) -> int:
        cmd = shlex.split(self.command) + [str(suite_path)]
        proc = subprocess.run(cmd, cwd=context.repo_dir, env=dict(context.env), text=True)
        return proc.returncode

    def teardown(self, *, context: RunnerContext) -> None:
        return
