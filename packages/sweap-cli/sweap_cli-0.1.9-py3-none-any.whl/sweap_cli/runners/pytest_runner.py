"""Pytest runner implementation for guardrail execution."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .base import Runner, RunnerContext


class PytestRunner(Runner):
    """Runner that executes pytest commands inside an isolated virtualenv."""

    def __init__(self, *, command: str, env: Mapping[str, str] | None = None, raw: dict[str, Any] | None = None) -> None:
        super().__init__(command=command, env=env, raw=raw)

    def setup(self, *, bundle_dir: Path, repo_dir: Path, dependency: Any) -> RunnerContext:
        requirements_rel = dependency.path or "requirements.txt"
        requirements_src = bundle_dir / requirements_rel
        if not requirements_src.exists():
            raise FileNotFoundError(f"Missing requirements file: {requirements_src}")

        requirements_dest = repo_dir / Path(requirements_rel)
        requirements_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(requirements_src, requirements_dest)

        temp_root = Path(tempfile.mkdtemp(prefix="sweap-pytest-runner-"))
        venv_dir = temp_root / "venv"

        try:
            subprocess.run(["python3", "-m", "venv", str(venv_dir)], check=True, cwd=repo_dir)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("Failed to create virtualenv for pytest runner") from exc

        env = _venv_env(venv_dir)
        env.update(self.extra_env)

        pip_bin = _venv_bin(venv_dir, "pip")
        try:
            subprocess.run([pip_bin, "install", "--upgrade", "pip"], check=True, cwd=repo_dir, env=env)
            if getattr(dependency, "install", None):
                install_cmd = dependency.install.format(
                    path=str(requirements_dest),
                    repo=str(repo_dir),
                    requirements=str(requirements_dest),
                )
                subprocess.run(["bash", "-lc", install_cmd], check=True, cwd=repo_dir, env=env)
            else:
                subprocess.run([pip_bin, "install", "-r", str(requirements_dest)], check=True, cwd=repo_dir, env=env)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("Failed to install pytest runner dependencies") from exc

        return RunnerContext(repo_dir=repo_dir, env=env, scratch_dir=temp_root)

    def run_suite(self, *, context: RunnerContext, suite_path: Path) -> int:
        cmd_parts = shlex.split(self.command)
        cmd = cmd_parts + [str(suite_path)]
        proc = subprocess.run(cmd, cwd=context.repo_dir, env=dict(context.env), text=True)
        return proc.returncode

    def teardown(self, *, context: RunnerContext) -> None:
        venv_path = Path(context.env.get("VIRTUAL_ENV", "")) if context.env else Path()
        if venv_path.exists():
            shutil.rmtree(venv_path.parent, ignore_errors=True)
        if context.scratch_dir and context.scratch_dir.exists():
            shutil.rmtree(context.scratch_dir, ignore_errors=True)


def _venv_bin(venv_dir: Path, executable: str) -> str:
    if venv_dir is None:
        raise ValueError("venv_dir is required")
    if (venv_dir / "Scripts").exists():
        return str(venv_dir / "Scripts" / (executable + ".exe"))
    return str(venv_dir / "bin" / executable)


def _venv_env(venv_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    bin_dir = venv_dir / ("Scripts" if (venv_dir / "Scripts").exists() else "bin")
    env["VIRTUAL_ENV"] = str(venv_dir)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    return env
