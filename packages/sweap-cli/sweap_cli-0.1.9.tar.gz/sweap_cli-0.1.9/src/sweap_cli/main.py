"""Command-line interface for SWEAP task authoring and evaluation."""

from __future__ import annotations

import base64
import importlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import hashlib
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from urllib.parse import urlparse

import typer
from rich import print as rprint
from rich.console import Console
from rich.prompt import Confirm

from dataclasses import asdict
from uuid import uuid4

from .api_client import ApiError as ApiClientError, load_api_client_from_env

from .manifest_utils import (
    ManifestError,
    Dependency,
    RunnerInfo,
    find_dependency,
    parse_dependencies,
    parse_runner,
    resolve_runner_dependency,
)
from .runners import MavenRunner, NodeRunner, PytestRunner, Runner

app = typer.Typer(help="CLI for creating and managing SWEAP benchmark tasks")

SCHEMA_VERSION = 2
console = Console()

DEFAULT_LLM_PREFIX = 'codex exec --profile default --dangerously-bypass-approvals-and-sandbox '
DEFAULT_LLM_COMMAND = (
    DEFAULT_LLM_PREFIX
    + '"Work on task ${SWEEP_TASK_ID}. Problem description path: ${SWEEP_PROBLEM_PATH}. '
    + 'Repository workspace: ${SWEEP_REPO_DIR}. Please implement the required changes and exit."'
)

REMOTE_RUN_POLL_SECONDS = 5


class ValidationError(Exception):
    """Raised when validation fails."""


def _load_manifest(bundle_dir: Path) -> tuple[dict[str, Any], Path]:
    manifest_path = bundle_dir / "task.json"
    if not manifest_path.exists():
        raise ValidationError(f"Missing manifest: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - formatting only
        raise ValidationError(f"Invalid JSON in manifest: {exc}") from exc

    required = ["version", "task_id", "repo", "problem", "tests", "solution"]
    missing = [key for key in required if key not in manifest]
    if missing:
        raise ValidationError(f"Manifest missing keys: {missing}")

    version = manifest.get("version")
    try:
        version_int = int(version)
    except (TypeError, ValueError) as exc:
        raise ValidationError("Manifest.version must be an integer.") from exc
    if version_int != SCHEMA_VERSION:
        raise ValidationError(
            f"Unsupported manifest version {version_int}; expected {SCHEMA_VERSION}."
        )

    return manifest, manifest_path


def _extract_full_config(manifest: dict[str, Any]) -> dict[str, Any] | None:
    tests = manifest.get("tests", {})
    full_cfg = tests.get("full")
    if full_cfg is None:
        return None
    if not isinstance(full_cfg, dict):
        raise ValidationError("tests.full must be an object when provided.")

    command = full_cfg.get("command")
    if not command or not isinstance(command, str):
        raise ValidationError("tests.full.command must be a non-empty string.")

    working_dir = full_cfg.get("working_dir", ".")
    if not isinstance(working_dir, str):
        raise ValidationError("tests.full.working_dir must be a string.")

    env_cfg = full_cfg.get("env", {})
    if env_cfg is None:
        env_cfg = {}
    if not isinstance(env_cfg, dict):
        raise ValidationError("tests.full.env must be an object mapping strings to strings.")
    normalized_env: dict[str, str] = {}
    for key, value in env_cfg.items():
        if not isinstance(key, str) or not isinstance(value, (str, int, float, bool)):
            raise ValidationError("tests.full.env keys and values must be strings.")
        normalized_env[key] = str(value)

    def _normalize_command_list(values: Any, field: str) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list):
            raise ValidationError(f"tests.full.{field} must be an array of command strings.")
        normalized: list[str] = []
        for item in values:
            if not isinstance(item, str) or not item.strip():
                raise ValidationError(f"tests.full.{field} entries must be non-empty strings.")
            normalized.append(item)
        return normalized

    prerequisites = _normalize_command_list(full_cfg.get("prerequisites"), "prerequisites")
    cleanup = _normalize_command_list(full_cfg.get("cleanup"), "cleanup")

    return {
        "command": command,
        "working_dir": working_dir,
        "env": normalized_env,
        "prerequisites": prerequisites,
        "cleanup": cleanup,
    }


def _parse_shared_entries(tests: dict[str, Any], key: str) -> list[dict[str, str]]:
    raw = tests.get(key, [])
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValidationError(f"tests.{key} must be an array.")

    normalized: list[dict[str, str]] = []
    for entry in raw:
        if isinstance(entry, str):
            path = entry.strip()
            mode = "fail"
        elif isinstance(entry, dict):
            path = entry.get("path", "")
            mode = entry.get("mode", "fail")
            if not isinstance(mode, str) or not mode.strip():
                raise ValidationError(f"tests.{key} entries must provide a non-empty mode when using objects.")
            mode = mode.strip().lower()
        else:
            raise ValidationError(f"tests.{key} entries must be strings or objects.")

        if not path or not isinstance(path, str):
            raise ValidationError(f"tests.{key} entries must include a non-empty path.")
        path = path.strip()
        if Path(path).is_absolute():
            raise ValidationError(f"tests.{key} entries must use relative paths.")
        if mode not in {"fail", "merge", "overwrite"}:
            raise ValidationError(f"tests.{key} mode must be one of fail, merge, overwrite.")

        normalized.append({"path": path, "mode": mode})

    return normalized


def _parse_dependencies(manifest: dict[str, Any]) -> list[Dependency]:
    environment = manifest.get("environment")
    if not isinstance(environment, dict):
        raise ValidationError("Manifest.environment must be an object.")
    try:
        return parse_dependencies(environment)
    except ManifestError as exc:
        raise ValidationError(str(exc)) from exc


def _require_python_dependency(manifest: dict[str, Any]) -> Dependency:
    dependencies = _parse_dependencies(manifest)
    python_dep = find_dependency(dependencies, "python")
    if python_dep is None or not python_dep.path:
        raise ValidationError(
            "environment.dependencies must include a python dependency with a relative path."
        )
    return python_dep


def _instantiate_runner(runner_info: RunnerInfo) -> Runner:
    runner_type = runner_info.type.lower()
    if runner_type == "pytest":
        return PytestRunner(command=runner_info.command, env=runner_info.env, raw=runner_info.raw)
    if runner_type in {"node", "npm", "yarn"}:
        return NodeRunner(command=runner_info.command, env=runner_info.env, raw=runner_info.raw)
    if runner_type in {"maven", "java"}:
        return MavenRunner(command=runner_info.command, env=runner_info.env, raw=runner_info.raw)
    if runner_type == "gradle":
        return GradleRunner(command=runner_info.command, env=runner_info.env, raw=runner_info.raw)
    raise ValidationError(f"Unsupported runner type '{runner_info.type}'.")


def _warn_if_missing(path: Path, label: str) -> None:
    if not path.exists():
        console.print(f"[yellow]Warning: {label} missing at {path}[/yellow]")


def _encode_file_b64(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


class _TempEnv:
    """Context manager to temporarily set environment variables."""

    def __init__(self, updates: dict[str, str]) -> None:
        self._updates = updates
        self._original: dict[str, Optional[str]] = {}

    def __enter__(self) -> None:
        for key, value in self._updates.items():
            self._original[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, exc_type, exc, tb) -> None:
        for key, original in self._original.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original


def _derive_task_id(repo_url: str) -> str:
    """Generate a human-friendly default task identifier from the repo URL."""
    parsed = urlparse(repo_url)
    repo_name = Path(parsed.path).stem or "task"
    return f"{repo_name}-task"


def _write_file(path: Path, content: str) -> None:
    """Create or overwrite a file with the provided content."""
    path.write_text(content, encoding="utf-8")


EXCLUDED_BUNDLE_DIRS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "venv",
    ".venv",
    ".modal-env",
}

EXCLUDED_BUNDLE_SUFFIXES = {".pyc", ".pyo"}


def _hash_file(path: Path) -> str:
    """Return a sha256:<digest> hash for the provided file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _iter_bundle_files(bundle_dir: Path):
    for filesystem_path in bundle_dir.rglob("*"):
        if filesystem_path.is_dir():
            continue
        relative = filesystem_path.relative_to(bundle_dir)
        if any(part in EXCLUDED_BUNDLE_DIRS for part in relative.parts[:-1]):
            continue
        if relative.name in EXCLUDED_BUNDLE_DIRS:
            continue
        if filesystem_path.suffix in EXCLUDED_BUNDLE_SUFFIXES:
            continue
        yield filesystem_path, relative


def _create_bundle_archive(bundle_dir: Path) -> Path:
    """Create a temporary zip archive of the bundle directory."""

    fd, temp_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    archive_path = Path(temp_path)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for filesystem_path, relative_path in _iter_bundle_files(bundle_dir):
            zipf.write(filesystem_path, arcname=str(relative_path))
    return archive_path


def _artifact_filename(run_id: str, artifact_type: str, model: str) -> str:
    base_model = _sanitize_model_name(model)
    suffix_map = {"log": ".log", "json": ".json"}
    suffix = suffix_map.get(artifact_type, ".bin")
    return f"run_{run_id}_{base_model}_{artifact_type}{suffix}"


def _save_remote_artifacts(
    *,
    bundle_dir: Path,
    client: "SweapApiClient",
    run_record: Dict[str, Any],
    model: str,
) -> List[Path]:
    saved_paths: List[Path] = []
    artifacts = run_record.get("artifacts") or []
    for artifact in artifacts:
        download_url = artifact.get("download_url")
        artifact_type = artifact.get("artifact_type", "other")
        if not download_url:
            continue
        try:
            content = client.download_signed_url(url=download_url)
        except ApiClientError as exc:
            console.print(
                f"[yellow]Failed to download {artifact_type} artifact: {exc}[/yellow]"
            )
            continue
        filename = _artifact_filename(run_record.get("id", "run"), artifact_type, model)
        destination = bundle_dir / filename
        destination.write_bytes(content)
        saved_paths.append(destination)
        console.print(
            f"[green]Saved {artifact_type} artifact to[/green] [bold]{destination}[/bold]."
        )
    return saved_paths


@app.command()
def init(
    repo: str = typer.Option(..., "--repo", help="Git repository URL for the task"),
    commit: str = typer.Option(..., "--commit", help="Commit SHA anchoring the task"),
    task_id: Optional[str] = typer.Option(None, "--task-id", help="Identifier for the task"),
    runner_type: str = typer.Option(
        "pytest",
        "--runner",
        help="Runner type to scaffold (pytest, node, maven)",
        case_sensitive=False,
    ),
    directory: Optional[Path] = typer.Option(
        None,
        "--directory",
        help="Target directory for the task bundle (defaults to task_id)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing directory contents if the path already exists",
    ),
) -> None:
    """Scaffold a new task bundle with manifest and placeholder files."""

    resolved_task_id = task_id or _derive_task_id(repo)
    target_dir = directory or Path(resolved_task_id)
    target_dir = target_dir.resolve()

    if target_dir.exists() and any(target_dir.iterdir()) and not force:
        console.print(
            f"[red]Directory {target_dir} already exists and is not empty. "
            "Use --force to overwrite.[/red]"
        )
        raise typer.Exit(code=1)

    if target_dir.exists() and force:
        if not Confirm.ask(
            f"Directory {target_dir} exists. Overwrite its contents?", default=False
        ):
            console.print("[yellow]Aborted by user.[/yellow]")
            raise typer.Exit(code=1)
    target_dir.mkdir(parents=True, exist_ok=True)

    runner_type_normalized = runner_type.lower()
    allowed_runners = {"pytest", "node", "maven", "gradle"}
    if runner_type_normalized not in allowed_runners:
        console.print(
            "[red]Unsupported runner type. Choose from pytest, node, or maven.[/red]"
        )
        raise typer.Exit(code=1)

    tests_dir = target_dir / "tests"
    fail_dir = tests_dir / "fail2pass"
    pass_dir = tests_dir / "pass2pass"
    for path in (tests_dir, fail_dir, pass_dir):
        path.mkdir(parents=True, exist_ok=True)

    description_path = target_dir / "description.md"
    gold_patch_path = target_dir / "gold_patch.diff"
    manifest_path = target_dir / "task.json"

    if not description_path.exists() or force:
        _write_file(
            description_path,
            "# Problem Statement\n\nDescribe the task requirements, context, and acceptance criteria.",
        )

    if not gold_patch_path.exists() or force:
        _write_file(
            gold_patch_path,
            "# Apply the golden patch here using unified diff format\n",
        )

    def ensure_file(path: Path, content: str) -> None:
        if not path.exists() or force:
            _write_file(path, content)

    if runner_type_normalized == "pytest":
        ensure_file(
            target_dir / "requirements.txt",
            "# Add pinned package versions required to run the task\npytest==8.1.1\n",
        )
    elif runner_type_normalized == "node":
        ensure_file(
            target_dir / "package.json",
            json.dumps(
                {
                    "name": resolved_task_id,
                    "version": "1.0.0",
                    "scripts": {
                        "test": "node -e \"process.exit(process.argv.slice(1).some(arg => arg.includes('fail2pass')) ? 1 : 0)\""
                    },
                    "devDependencies": {},
                },
                indent=2,
            )
            + "\n",
        )
        ensure_file(target_dir / "package-lock.json", "{}\n")
    elif runner_type_normalized == "maven":
        ensure_file(
            target_dir / "pom.xml",
            """<project xmlns=\"http://maven.apache.org/POM/4.0.0\"
    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"
    xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd\">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>{artifact_id}</artifactId>
  <version>0.1.0-SNAPSHOT</version>
  <build>
    <plugins>
      <!-- Add surefire/junit plugins here -->
    </plugins>
  </build>
  <dependencies>
    <!-- Add project dependencies here -->
  </dependencies>
</project>
""".format(artifact_id=resolved_task_id)
        )
        ensure_file(
            target_dir / "mvnw",
            "#!/bin/sh\nexec mvn \"$@\"\n",
        )
        mvnw_path = target_dir / "mvnw"
        if mvnw_path.exists():
            try:
                mvnw_path.chmod(mvnw_path.stat().st_mode | 0o111)
            except PermissionError:
                pass

    if runner_type_normalized == "pytest":
        runner_manifest = {
            "version": 1,
            "type": "pytest",
            "command": {"default": "pytest -q"},
            "python": {"requirements": "requirements.txt", "venv": True},
            "env": {},
        }
        dependencies = [
            {
                "kind": "python",
                "path": "requirements.txt",
                "install": "pip install -r {path}",
            }
        ]
    elif runner_type_normalized == "node":
        runner_manifest = {
            "version": 1,
            "type": "node",
            "command": {"default": "npm test --"},
            "node": {"package_manager": "npm", "lockfile": "package-lock.json"},
            "env": {},
        }
        dependencies = [
            {
                "kind": "node",
                "path": "package.json",
                "lockfile": "package-lock.json",
                "package_manager": "npm",
            }
        ]
    elif runner_type_normalized == "gradle":
        runner_manifest = {
            "version": 1,
            "type": "gradle",
            "command": {"default": "gradle test --no-daemon"},
            "gradle": {"wrapper": "gradlew", "bootstrap": "./gradlew --no-daemon testClasses"},
            "env": {},
        }
        dependencies = [
            {
                "kind": "gradle",
                "path": "build.gradle",
                "wrapper": "gradlew",
                "settings": "settings.gradle",
                "bootstrap": "./gradlew --no-daemon testClasses",
            }
        ]
        ensure_file(
            target_dir / "build.gradle",
            "plugins {\n    id 'java'\n}\n\nrepositories {\n    mavenCentral()\n}\n\ndependencies {\n    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'\n}\n\ntest {\n    useJUnitPlatform()\n}\n",
        )
        ensure_file(
            target_dir / "settings.gradle",
            f"rootProject.name = '{resolved_task_id}'\n",
        )
        ensure_file(
            target_dir / "gradlew",
            "#!/bin/sh\nexec ./gradlew \"$@\"\n",
        )
        gradlew_path = target_dir / "gradlew"
        if gradlew_path.exists():
            try:
                gradlew_path.chmod(gradlew_path.stat().st_mode | 0o111)
            except PermissionError:
                pass
    else:  # maven
        runner_manifest = {
            "version": 1,
            "type": "maven",
            "command": {"default": "mvn -q test"},
            "maven": {"wrapper": "mvnw", "bootstrap": "mvn -B dependency:go-offline"},
            "env": {},
        }
        dependencies = [
            {
                "kind": "maven",
                "path": "pom.xml",
                "wrapper": "mvnw",
                "bootstrap": "mvn -B dependency:go-offline",
            }
        ]

    # Drop None entries from dependency descriptors
    normalized_dependencies: list[dict[str, Any]] = []
    for entry in dependencies:
        normalized = {key: value for key, value in entry.items() if value is not None}
        normalized_dependencies.append(normalized)

    manifest = {
        "version": SCHEMA_VERSION,
        "task_id": resolved_task_id,
        "repo": {"url": repo, "commit": commit},
        "problem": {
            "title": "Fill in a concise title",
            "description_file": "description.md",
        },
        "tests": {
            "fail2pass_dir": "tests/fail2pass",
            "pass2pass_dir": "tests/pass2pass",
            "full": None,
        },
        "solution": {"gold_patch_file": "gold_patch.diff"},
        "runner": runner_manifest,
        "environment": {
            "dependencies": normalized_dependencies,
            "notes": "",
            "modal_image": None,
            "modal_python_version": "3.10",
            "modal_image_id": None,
        },
        "metadata": {"created_by": None, "tags": []},
    }
    _write_file(manifest_path, json.dumps(manifest, indent=2) + "\n")

    console.print(
        "[green]OK[/green] Task bundle scaffolded at "
        f"[bold]{target_dir}[/bold] with ID [cyan]{resolved_task_id}[/cyan]."
    )


def _resolve_remote_task(manifest: dict[str, Any], override_task_id: str | None) -> dict[str, Any]:
    metadata = manifest.get("metadata") or {}
    remote_info = metadata.get("remote") or {}
    if override_task_id:
        remote_info = dict(remote_info)
        remote_info["task_id"] = override_task_id
    return remote_info


def _require_env_api_client() -> "SweapApiClient":
    try:
        return load_api_client_from_env()
    except ApiClientError as exc:
        console.print(f"[red]{exc}")
        raise typer.Exit(code=1)


@app.command()
def info(
    bundle_dir: Path = typer.Argument(
        Path("."), help="Path to the task bundle (defaults to current directory)"
    ),
    remote_task_id: Optional[str] = typer.Option(
        None,
        "--remote-task-id",
        help="Override the remote task id (defaults to metadata.remote.task_id)",
    ),
) -> None:
    """Display remote task metadata using the backend API."""

    bundle_dir = bundle_dir.resolve()
    try:
        manifest, _ = _load_manifest(bundle_dir)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    remote_info = _resolve_remote_task(manifest, remote_task_id)
    task_identifier = remote_info.get("task_id")
    if not task_identifier:
        console.print(
            "[red]Remote task id not found. Run `task submit` first or supply --remote-task-id.[/red]"
        )
        raise typer.Exit(code=1)

    api_client = _require_env_api_client()
    try:
        with api_client as client:
            task_record = client.get_task(task_identifier)
    except ApiClientError as exc:
        console.print(f"[red]{exc}")
        if exc.response_json:
            console.print(f"[red]{exc.response_json}")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Task[/cyan] [bold]{task_record.get('id')}[/bold]")
    console.print(f"Title       : {task_record.get('title')}")
    console.print(f"Repo        : {task_record.get('repo_url')} @ {task_record.get('repo_commit')}")
    console.print(f"Visibility  : {task_record.get('visibility')}")
    console.print(f"Status      : {task_record.get('status')}")
    console.print(f"Latest ver. : {task_record.get('latest_version')}")
    description = task_record.get('description')
    if description:
        console.print("Description :")
        console.print(description)


@app.command()
def submit(
    bundle_dir: Path = typer.Argument(
        Path("."), help="Path to the task bundle (defaults to current directory)"
    ),
    visibility: str = typer.Option(
        "private",
        "--visibility",
        help="Remote task visibility (private or public)",
    ),
    remote_id: Optional[str] = typer.Option(
        None,
        "--remote-id",
        help="Existing remote task ID to update instead of creating a new one",
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        help="Optional notes stored alongside the bundle version",
    ),
) -> None:
    """Submit the bundle to the SWEAP backend and upload the bundle archive."""

    bundle_dir = bundle_dir.resolve()
    try:
        manifest, manifest_path = _load_manifest(bundle_dir)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    remote_info = (manifest.get("metadata") or {}).get("remote", {})

    repo_section = manifest.get("repo", {})
    repo_url = repo_section.get("url")
    repo_commit = repo_section.get("commit")
    if not repo_url or not repo_commit:
        console.print("[red]Manifest.repo must include url and commit.[/red]")
        raise typer.Exit(code=1)

    problem_section = manifest.get("problem", {})
    title = problem_section.get("title") or manifest.get("task_id") or "Untitled Task"
    description_file = problem_section.get("description_file")
    description_text: Optional[str] = None
    if description_file:
        desc_path = bundle_dir / description_file
        if desc_path.exists():
            description_text = desc_path.read_text(encoding="utf-8")
        else:
            console.print(f"[yellow]Description file missing: {desc_path}[/yellow]")

    requirements_hash: Optional[str] = None
    try:
        python_dependency = _require_python_dependency(manifest)
    except ValidationError:
        python_dependency = None
    if python_dependency and python_dependency.path:
        requirements_path = bundle_dir / python_dependency.path
        if requirements_path.exists():
            requirements_hash = _hash_file(requirements_path)
        else:
            console.print(f"[yellow]Requirements file missing: {requirements_path}[/yellow]")

    visibility_normalized = visibility.lower()
    if visibility_normalized not in {"private", "public"}:
        console.print("[red]--visibility must be either 'private' or 'public'.[/red]")
        raise typer.Exit(code=1)

    try:
        api_client = load_api_client_from_env()
    except ApiClientError as exc:
        console.print(f"[red]{exc}")
        raise typer.Exit(code=1)

    task_record: Dict[str, Any]
    try:
        with api_client as client:
            if remote_id:
                task_record = client.get_task(remote_id)
            else:
                try:
                    task_record = client.create_task(
                        title=title,
                        repo_url=repo_url,
                        repo_commit=repo_commit,
                        slug=manifest.get("task_id"),
                        visibility=visibility_normalized,
                        description=description_text,
                    )
                except ApiClientError as creation_error:
                    if creation_error.status_code == 409 and remote_info.get("task_id"):
                        console.print(
                            "[yellow]Task with this slug already exists; reusing remote linkage from manifest metadata.[/yellow]"
                        )
                        task_record = client.get_task(remote_info["task_id"])
                    else:
                        raise

            bundle_response = client.create_bundle_version(
                task_id=task_record["id"],
                manifest=manifest,
                requirements_hash=requirements_hash,
                notes=notes,
            )

            archive_path = _create_bundle_archive(bundle_dir)
            try:
                client.upload_file(upload_url=bundle_response.upload_url, file_path=archive_path)
            finally:
                try:
                    archive_path.unlink()
                except FileNotFoundError:
                    pass

            remote_bundle = client.get_bundle_version(
                task_id=bundle_response.task_id, version=bundle_response.version
            )
    except ApiClientError as exc:
        console.print(f"[red]{exc}")
        if exc.response_json:
            console.print(f"[red]{exc.response_json}")
        raise typer.Exit(code=1)

    metadata = manifest.setdefault("metadata", {})
    remote_meta = metadata.setdefault("remote", {})
    remote_meta.update(
        {
            "task_id": task_record.get("id"),
            "slug": task_record.get("slug"),
            "visibility": task_record.get("visibility"),
            "bundle_version": remote_bundle.get("version"),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    console.print(
        "[green]Submitted bundle[/green] to backend as task "
        f"[bold]{task_record.get('id')}[/bold] version [cyan]{remote_bundle.get('version')}"
        f". Download URL: {remote_bundle.get('download_url')}"
    )


@app.command("runs-get")
def runs_get(
    run_id: str = typer.Argument(..., help="Remote run identifier"),
    bundle_dir: Path = typer.Option(
        Path("."),
        "--bundle-dir",
        help="Directory to save artifacts (defaults to current directory)",
    ),
    download_artifacts: bool = typer.Option(
        False,
        "--download-artifacts/--no-download-artifacts",
        help="Download available artifacts for the run",
    ),
) -> None:
    """Fetch a remote run record and optionally download artifacts."""

    api_client = _require_env_api_client()
    run_record: Dict[str, Any]
    try:
        with api_client as client:
            run_record = client.get_run(run_id)
            if download_artifacts:
                model = run_record.get("model_id") or "model"
                _save_remote_artifacts(
                    bundle_dir=bundle_dir.resolve(),
                    client=client,
                    run_record=run_record,
                    model=model,
                )
    except ApiClientError as exc:
        console.print(f"[red]{exc}")
        if exc.response_json:
            console.print(f"[red]{exc.response_json}")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Run[/cyan] [bold]{run_id}[/bold]")
    console.print(json.dumps(run_record, indent=2))


@app.command()
def fetch_bundle(
    bundle_dir: Path = typer.Argument(
        Path("."), help="Path to the task bundle (defaults to current directory)"
    ),
    version: Optional[int] = typer.Option(
        None,
        "--version",
        help="Remote bundle version to download (defaults to recorded bundle_version or latest)",
    ),
    remote_task_id: Optional[str] = typer.Option(
        None,
        "--remote-task-id",
        help="Override the remote task id (defaults to metadata.remote.task_id)",
    ),
    output: Path = typer.Option(
        Path("downloaded_bundle.zip"),
        "--output",
        help="Destination zip file path",
    ),
    extract: bool = typer.Option(
        False,
        "--extract/--no-extract",
        help="Extract the downloaded bundle into the current directory",
    ),
) -> None:
    """Download a remote bundle archive from the backend."""

    bundle_dir = bundle_dir.resolve()
    try:
        manifest, _ = _load_manifest(bundle_dir)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    remote_info = _resolve_remote_task(manifest, remote_task_id)
    task_identifier = remote_info.get("task_id")
    if not task_identifier:
        console.print(
            "[red]Remote task id not found. Run `task submit` first or supply --remote-task-id.[/red]"
        )
        raise typer.Exit(code=1)

    version_to_use = version if version is not None else remote_info.get("bundle_version")
    if isinstance(version_to_use, dict):
        version_to_use = version_to_use.get("version")

    api_client = _require_env_api_client()
    try:
        with api_client as client:
            if version_to_use is None:
                task_record = client.get_task(task_identifier)
                version_to_use = task_record.get("latest_version")
            if version_to_use is None:
                console.print("[red]No bundle version available to download.[/red]")
                raise typer.Exit(code=1)
            bundle_details = client.get_bundle_version(task_identifier, int(version_to_use))
            download_url = bundle_details.get("download_url")
            if not download_url:
                console.print("[red]Backend did not return a download URL for this version.[/red]")
                raise typer.Exit(code=1)
            data = client.download_signed_url(url=download_url)
    except ApiClientError as exc:
        console.print(f"[red]{exc}")
        if exc.response_json:
            console.print(f"[red]{exc.response_json}")
        raise typer.Exit(code=1)

    output = output.resolve()
    output.write_bytes(data)
    console.print(f"[green]Saved bundle to {output}[/green]")

    if extract:
        with zipfile.ZipFile(output, "r") as zipf:
            zipf.extractall(path=bundle_dir)
        console.print(f"[green]Extracted bundle into {bundle_dir}[/green]")


@app.command()
def build(
    bundle_dir: Path = typer.Argument(
        Path("."), help="Path to the task bundle (defaults to current directory)"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Modal image name to persist (defaults to <task_id>-image)",
    ),
    python_version: Optional[str] = typer.Option(
        None,
        "--python-version",
        help="Python version for the Modal base image (defaults to manifest or 3.10)",
    ),
) -> None:
    """Build and persist a Modal image encapsulating the bundle + dependencies."""

    bundle_dir = bundle_dir.resolve()

    try:
        import modal
    except ImportError as exc:  # pragma: no cover - import guard
        console.print("[red]Modal library not installed. Run `pip install modal`.[/red]")
        raise typer.Exit(code=1) from exc

    try:
        manifest, manifest_path = _load_manifest(bundle_dir)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    env_section = manifest.setdefault("environment", {})

    try:
        runner_info = parse_runner(manifest.get("runner"))
    except ManifestError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    runner_type = runner_info.type.lower()

    if runner_info.type.lower() != "pytest":
        console.print("[red]task build currently supports only pytest runners.[/red]")
        raise typer.Exit(code=1)

    try:
        runner_dependency = resolve_runner_dependency(manifest, runner_info)
    except ManifestError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    dependency_payload = asdict(runner_dependency)
    dependency_rel = dependency_payload.get("path") or ""
    dependency_data: dict[str, Any] = dependency_payload.get("data") or {}

    if dependency_rel:
        dependency_path = bundle_dir / dependency_rel
        if not dependency_path.exists():
            console.print(f"[red]Missing dependency artifact at {dependency_path}[/red]")
            raise typer.Exit(code=1)

    bundle_mount = "/bundle"
    lockfile_rel = dependency_data.get("lockfile")
    wrapper_rel = dependency_data.get("wrapper")

    def _format_install(template: str) -> str:
        context = {
            "path": f"{bundle_mount}/{dependency_rel}" if dependency_rel else bundle_mount,
            "repo": bundle_mount,
            "requirements": f"{bundle_mount}/{dependency_rel}" if dependency_rel else bundle_mount,
            "package_json": f"{bundle_mount}/{dependency_rel}" if dependency_rel else bundle_mount,
            "lockfile": f"{bundle_mount}/{lockfile_rel}" if lockfile_rel else "",
            "wrapper": f"{bundle_mount}/{wrapper_rel}" if wrapper_rel else "",
            "pom": f"{bundle_mount}/{dependency_rel}" if dependency_rel else bundle_mount,
        }
        return template.format(**context)

    target_python = (
        python_version
        or env_section.get("modal_python_version")
        or env_section.get("python_version")
        or "3.10"
    )

    image_name = name or env_section.get("modal_image")
    if not image_name:
        task_id = manifest.get("task_id", "task")
        image_name = f"sweap-{task_id}-image"

    console.print(
        f"[cyan]Building Modal image[/cyan] [bold]{image_name}[/bold] (Python {target_python})..."
    )

    import importlib

    try:
        image_api = modal.Image
    except AttributeError:
        try:
            image_module = importlib.import_module("modal.image")
            image_api = getattr(image_module, "Image")
        except Exception as exc:
            console.print(
                "[red]Modal's Python image API is unavailable. Please install or upgrade the `modal` SDK (e.g. `pip install --upgrade modal`).[/red]"
            )
            raise typer.Exit(code=1) from exc

    try:
        base_image = image_api.debian_slim(python_version=target_python)
    except TypeError:
        base_image = image_api.debian_slim()

    packages = ["git", "python3-venv", "nodejs", "npm"]
    install_commands: list[str] = []

    if runner_type in {"pytest", "python"}:
        requirements_rel = dependency_rel or "requirements.txt"
        requirements_path = bundle_dir / requirements_rel
        if not requirements_path.exists():
            console.print(f"[red]Missing requirements file at {requirements_path}[/red]")
            raise typer.Exit(code=1)

        install_override = runner_dependency.install
        if install_override:
            formatted = _format_install(install_override)
        else:
            formatted = f"/opt/sweap-venv/bin/pip install -r {bundle_mount}/{requirements_rel}"

        install_commands.append(
            "python3 -m venv /opt/sweap-venv && "
            "/opt/sweap-venv/bin/pip install --upgrade pip && "
            + formatted
        )
    elif runner_type in {"node", "npm", "yarn"}:
        package_rel = dependency_rel or "package.json"
        package_path = bundle_dir / package_rel
        if not package_path.exists():
            console.print(f"[red]Missing package.json at {package_path}[/red]")
            raise typer.Exit(code=1)
        if lockfile_rel:
            lockfile_path = bundle_dir / lockfile_rel
            if not lockfile_path.exists():
                console.print(f"[yellow]Lockfile {lockfile_path} missing; continuing without it.[/yellow]")
        install_override = runner_dependency.install
        if install_override:
            formatted = _format_install(install_override)
        else:
            package_manager = dependency_data.get("package_manager", "npm")
            formatted = "npm ci" if package_manager == "npm" else f"{package_manager} install"
        install_commands.append(f"cd {bundle_mount} && {formatted}")
    else:  # Maven/Java/Gradle
        packages.extend(["openjdk-17-jdk", "maven", "gradle"])
        pom_rel = dependency_rel or ("pom.xml" if runner_type != "gradle" else "build.gradle")
        pom_path = bundle_dir / pom_rel
        if not pom_path.exists():
            console.print(f"[red]Missing build file at {pom_path}[/red]")
            raise typer.Exit(code=1)
        install_override = runner_dependency.install
        if wrapper_rel:
            install_commands.append(f"cd {bundle_mount} && chmod +x {wrapper_rel}")
        if install_override:
            formatted = _format_install(install_override)
        else:
            bootstrap = dependency_data.get("bootstrap")
            if not bootstrap:
                if runner_type == "gradle":
                    wrapper_cmd = f"./{wrapper_rel}" if wrapper_rel else "gradle"
                    bootstrap = f"{wrapper_cmd} --no-daemon testClasses"
                else:
                    bootstrap = f"./{wrapper_rel} dependency:go-offline" if wrapper_rel else "mvn -B dependency:go-offline"
            formatted = bootstrap
        install_commands.append(f"cd {bundle_mount} && {formatted}")

    packages = list(dict.fromkeys(packages))

    image = (
        base_image
        .apt_install(*packages)
        .add_local_dir(str(bundle_dir), remote_path="/bundle", copy=True)
        .run_commands("npm install -g @openai/codex")
    )

    for command in install_commands:
        image = image.run_commands(command)

    persisted = False
    try:
        persist_attr = getattr(image, "persist", None)
        if persist_attr is not None:
            try:
                persist_attr(image_name)
                persisted = True
            except Exception:
                remote_attr = getattr(persist_attr, "remote", None)
                call_attr = getattr(persist_attr, "call", None)
                if callable(remote_attr):
                    remote_attr(image_name)
                    persisted = True
                elif callable(call_attr):
                    call_attr(image_name)
                    persisted = True
        if not persisted and hasattr(image, "persisted") and callable(getattr(image, "persisted")):
            image.persisted(image_name)
            persisted = True
        if not persisted and hasattr(image, "push") and callable(getattr(image, "push")):
            image.push(image_name)
            persisted = True
        if not persisted:
            persist_cls_attr = getattr(image_api, "persist", None)
            if callable(persist_cls_attr):
                persist_cls_attr(image, image_name)
                persisted = True
    except Exception as exc:  # pragma: no cover - network failures
        console.print(f"[red]Failed to persist Modal image: {exc}[/red]")
        raise typer.Exit(code=1)

    if persisted:
        env_section["modal_image"] = image_name
        env_section["modal_python_version"] = target_python
        new_image_id = getattr(image, "object_id", None)
        if new_image_id is not None:
            env_section["modal_image_id"] = new_image_id
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        console.print(
            f"[green]Persisted Modal image[/green] [bold]{image_name}[/bold] and updated manifest."
        )
        return

    console.print(
        "[yellow]Persist APIs unavailable; snapshotting sandbox to capture image instead.[/yellow]"
    )

    app = modal.App.lookup("sweap-cli", create_if_missing=True)
    try:
        with modal.enable_output():
            sandbox = modal.Sandbox.create(app=app, image=image)
    except Exception as exc:
        console.print(f"[red]Failed to create Modal sandbox for snapshot: {exc}[/red]")
        raise typer.Exit(code=1)

    try:
        snapshot_image = sandbox.snapshot_filesystem()
    except Exception as exc:
        console.print(f"[red]Failed to snapshot Modal sandbox: {exc}[/red]")
        raise typer.Exit(code=1)
    finally:
        try:
            sandbox.terminate()
        except Exception:
            pass

    image_id = getattr(snapshot_image, "object_id", None)
    if not image_id:
        console.print(
            "[red]Snapshot succeeded but returned image without object_id; cannot record in manifest.[/red]"
        )
        raise typer.Exit(code=1)

    env_section["modal_image_id"] = image_id
    env_section["modal_image"] = None
    env_section["modal_python_version"] = target_python

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    console.print(
        f"[green]Captured Modal sandbox snapshot[/green] [bold]{image_id}[/bold] and updated manifest."
    )
    console.print("[yellow]Run `task build` again after upgrading Modal to switch back to persisted images.[/yellow]")


@app.command()
def validate(
    bundle_dir: Path = typer.Argument(
        Path("."),
        help="Path to the task bundle (defaults to current directory)",
    ),
    use_modal: bool = typer.Option(
        False,
        "--modal",
        help="Run validation inside Modal (requires credentials)",
    ),
    full: bool = typer.Option(
        False,
        "--full/--no-full",
        help="Run the repository's full test command after guardrail checks",
    ),
    snapshots: bool = typer.Option(
        False,
        "--snapshots/--no-snapshots",
        help="Capture repo snapshots during Modal validation (stored alongside the bundle)",
    ),
    modal_timeout: int = typer.Option(
        1800,
        "--modal-timeout",
        help="Timeout in seconds for Modal sandbox during validation",
    ),
) -> None:
    """Validate the task bundle locally or via Modal."""

    bundle_dir = bundle_dir.resolve()
    try:
        manifest, _manifest_path = _load_manifest(bundle_dir)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    try:
        full_config = _extract_full_config(manifest)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    run_full_suite = full
    if run_full_suite and not full_config:
        console.print(
            "[red]Manifest missing tests.full configuration required for --full validation.[/red]"
        )
        raise typer.Exit(code=1)

    repo_url = manifest["repo"].get("url")
    commit = manifest["repo"].get("commit")
    patch_rel = manifest["solution"].get("gold_patch_file", "gold_patch.diff")
    patch_path = bundle_dir / patch_rel

    if not repo_url or not commit:
        console.print("[red]Manifest.repo must include url and commit.[/red]")
        raise typer.Exit(code=1)
    if not patch_path.exists():
        console.print(f"[red]Missing gold patch file: {patch_path}[/red]")
        raise typer.Exit(code=1)

    try:
        runner_info = parse_runner(manifest.get("runner"))
        runner = _instantiate_runner(runner_info)
    except (ManifestError, ValidationError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    runner_type = runner_info.type.lower()
    runner_cmd = runner_info.command

    try:
        runner_dependency = resolve_runner_dependency(manifest, runner_info)
    except ManifestError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    dependency_rel = runner_dependency.path or ""
    dependency_path = bundle_dir / dependency_rel if dependency_rel else None
    if dependency_rel and (dependency_path is None or not dependency_path.exists()):
        console.print(f"[red]Missing dependency artifact: {dependency_path}[/red]")
        raise typer.Exit(code=1)

    runner_payload = {
        "type": runner_info.type,
        "command": runner_info.command,
        "env": runner_info.env,
    }
    dependency_payload = asdict(runner_dependency)

    tests = manifest.get("tests", {})
    fail_dir_rel = tests.get("fail2pass_dir", "tests/fail2pass")
    pass_dir_rel = tests.get("pass2pass_dir", "tests/pass2pass")
    shared_dirs_common = _parse_shared_entries(tests, "shared_dirs")
    shared_dirs_pre = _parse_shared_entries(tests, "shared_dirs_pre")
    shared_dirs_post = _parse_shared_entries(tests, "shared_dirs_post")
    for rel_value, label in ((fail_dir_rel, "fail2pass_dir"), (pass_dir_rel, "pass2pass_dir")):
        if Path(rel_value).is_absolute():
            console.print(f"[red]{label} must be a relative path.[/red]")
            raise typer.Exit(code=1)

    _warn_if_missing(
        bundle_dir / manifest["problem"].get("description_file", "description.md"),
        "description",
    )
    _warn_if_missing(bundle_dir / fail_dir_rel, "fail2pass tests")
    _warn_if_missing(bundle_dir / pass_dir_rel, "pass2pass tests")

    if use_modal:
        try:
            from .modal_runner import validate_in_modal
        except Exception as e:  # pragma: no cover
            console.print(f"[red]Failed to import Modal integration: {e}[/red]")
            raise typer.Exit(code=1)

        github_token = os.environ.get("GITHUB_TOKEN")
        code = validate_in_modal(
            bundle_dir=bundle_dir,
            repo_url=repo_url,
            commit=commit,
            runner=runner_payload,
            dependency=dependency_payload,
            fail_dir_rel=fail_dir_rel,
            pass_dir_rel=pass_dir_rel,
            shared_dirs=shared_dirs_common,
            shared_dirs_pre=shared_dirs_pre,
            shared_dirs_post=shared_dirs_post,
            full_config=full_config if run_full_suite else None,
            run_full=run_full_suite,
            github_token=github_token,
            snapshots=snapshots,
            timeout_seconds=modal_timeout,
        )
        raise typer.Exit(code=code)

    console.print("[cyan]Running local validation...[/cyan]")
    try:
        _validate_locally(
            bundle_dir=bundle_dir,
            repo_url=repo_url,
            commit=commit,
            patch_path=patch_path,
            runner=runner,
            fail_dir_rel=fail_dir_rel,
            pass_dir_rel=pass_dir_rel,
            shared_dirs=shared_dirs_common,
            shared_dirs_pre=shared_dirs_pre,
            shared_dirs_post=shared_dirs_post,
            runner_dependency=runner_dependency,
            run_full=run_full_suite,
            full_config=full_config,
        )
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    console.print("[green]OK[/green] Local validation succeeded.")
    raise typer.Exit(code=0)


def _validate_locally(
    *,
    bundle_dir: Path,
    repo_url: str,
    commit: str,
    patch_path: Path,
    runner: Runner,
    fail_dir_rel: str,
    pass_dir_rel: str,
    shared_dirs: list[dict[str, str]],
    shared_dirs_pre: list[dict[str, str]],
    shared_dirs_post: list[dict[str, str]],
    runner_dependency: Dependency,
    run_full: bool,
    full_config: dict[str, Any] | None,
) -> None:
    console.print("[cyan]Cloning repository...[/cyan]")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        repo_dir = tmp / "repo"
        git_env = {"GIT_TERMINAL_PROMPT": "0"}
        try:
            _run(["git", "clone", repo_url, "repo"], cwd=tmp, env=git_env)
            _run(["git", "checkout", commit], cwd=repo_dir, env=git_env)
            console.print("[cyan]Clone and checkout completed.[/cyan]")
        except subprocess.CalledProcessError as exc:
            raise ValidationError(f"Git operation failed: {exc}") from exc

        try:
            _run(["git", "apply", "--check", str(patch_path)], cwd=repo_dir)
        except subprocess.CalledProcessError as exc:
            raise ValidationError(
                "Golden patch does not apply cleanly to the repo at the specified commit."
            ) from exc

        console.print("[cyan]Preparing runner environment...[/cyan]")
        context = None
        try:
            context = runner.setup(
                bundle_dir=bundle_dir,
                repo_dir=repo_dir,
                dependency=runner_dependency,
            )
        except Exception as exc:  # pragma: no cover - setup errors trigger validation failure
            raise ValidationError(f"Runner setup failed: {exc}") from exc

        pass_dir = repo_dir / Path(pass_dir_rel)
        fail_dir = repo_dir / Path(fail_dir_rel)
        backup_root = tmp / "staged_backups"

        baseline_entries: list[dict[str, str]] = [
            {"path": pass_dir_rel, "mode": "fail"},
            {"path": fail_dir_rel, "mode": "fail"},
            *shared_dirs,
            *shared_dirs_pre,
        ]
        patched_entries: list[dict[str, str]] = [
            {"path": pass_dir_rel, "mode": "fail"},
            {"path": fail_dir_rel, "mode": "fail"},
            *shared_dirs,
            *shared_dirs_post,
        ]

        staged_baseline: list[tuple[Path, Path | None]] = []
        staged_patched: list[tuple[Path, Path | None]] = []

        try:
            console.print("[cyan]Copying bundle artifacts into cloned repo (baseline)...[/cyan]")
            staged_baseline = _stage_bundle_entries(
                bundle_dir=bundle_dir,
                repo_dir=repo_dir,
                entries=baseline_entries,
                backup_root=backup_root,
            )

            console.print("[cyan]Running baseline tests (pass2pass)...[/cyan]")
            if _has_tests(pass_dir):
                rc = runner.run_suite(context=context, suite_path=Path(pass_dir_rel))
                if rc != 0:
                    raise ValidationError("Pass2pass tests failed before applying the patch.")
            else:
                console.print(
                    "[yellow]No files detected in pass2pass directory; skipping baseline pass check.[/yellow]"
                )

            console.print("[cyan]Running baseline tests (fail2pass)...[/cyan]")
            if _has_tests(fail_dir):
                rc = runner.run_suite(context=context, suite_path=Path(fail_dir_rel))
                if rc == 0:
                    raise ValidationError("Fail2pass tests unexpectedly passed before applying the patch.")
            else:
                console.print(
                    "[yellow]No files detected in fail2pass directory; skipping baseline fail check.[/yellow]"
                )

            console.print("[cyan]Cleaning up staged guardrails after baseline...[/cyan]")
            _restore_staged(staged_baseline)
            staged_baseline = []

            console.print("[cyan]Applying golden patch...[/cyan]")
            try:
                _run(["git", "apply", str(patch_path)], cwd=repo_dir)
            except subprocess.CalledProcessError as exc:
                raise ValidationError("Failed to apply golden patch to cloned repo.") from exc

            console.print("[cyan]Copying bundle artifacts into cloned repo (patched)...[/cyan]")
            staged_patched = _stage_bundle_entries(
                bundle_dir=bundle_dir,
                repo_dir=repo_dir,
                entries=patched_entries,
                backup_root=backup_root,
            )

            console.print("[cyan]Running patched tests (pass2pass)...[/cyan]")
            if _has_tests(pass_dir):
                rc = runner.run_suite(context=context, suite_path=Path(pass_dir_rel))
                if rc != 0:
                    raise ValidationError("Pass2pass tests failed after applying the patch.")

            console.print("[cyan]Running patched tests (fail2pass)...[/cyan]")
            if _has_tests(fail_dir):
                rc = runner.run_suite(context=context, suite_path=Path(fail_dir_rel))
                if rc != 0:
                    raise ValidationError("Fail2pass tests are still failing after applying the patch.")

            console.print("[cyan]Cleaning up staged guardrails after patched run...[/cyan]")
            _restore_staged(staged_patched)
            staged_patched = []

            if run_full:
                if not full_config:
                    raise ValidationError(
                        "No tests.full configuration found in manifest for --full validation."
                    )
                _run_full_suite(
                    repo_dir=repo_dir,
                    base_env=dict(context.env),
                    config=full_config,
                )
        finally:
            try:
                _restore_staged(staged_patched)
            except Exception:
                pass
            try:
                _restore_staged(staged_baseline)
            except Exception:
                pass
            if context is not None:
                try:
                    runner.teardown(context=context)
                except Exception:
                    pass


def _copy_bundle_dir(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True)


def _remove_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _backup_path(base: Path, name_hint: str) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{name_hint}_{uuid4()}"


def _copy_with_mode(src: Path, dest: Path, mode: str, backup_root: Path) -> tuple[Path, Path | None]:
    """Copy src into dest respecting collision mode. Returns (dest, backup)."""
    if not src.exists():
        raise ValidationError(f"Shared path missing in bundle: {src}")

    dest_exists = dest.exists()
    backup: Path | None = None

    if dest_exists:
        if mode == "fail":
            raise ValidationError(f"Cannot stage {src} into existing path {dest}; use merge/overwrite.")
        # Snapshot existing content
        backup = _backup_path(backup_root, dest.name or "backup")
        if dest.is_file():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, backup)
        else:
            shutil.copytree(dest, backup)

    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if mode == "overwrite":
                shutil.copy2(src, dest)
            else:  # merge on file collision is not supported
                raise ValidationError(f"File already exists at {dest}; use overwrite.")
        else:
            shutil.copy2(src, dest)
    else:
        if not dest.exists():
            shutil.copytree(src, dest)
        else:
            if mode == "overwrite":
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
                shutil.copytree(src, dest)
            elif mode == "merge":
                for root, _, files in os.walk(src):
                    root_path = Path(root)
                    rel_root = root_path.relative_to(src)
                    for file_name in files:
                        source_file = root_path / file_name
                        target_file = dest / rel_root / file_name
                        if target_file.exists():
                            raise ValidationError(
                                f"Collision staging {source_file} into existing {target_file}; use overwrite."
                            )
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
            else:
                raise ValidationError(f"Unsupported mode {mode} for directory staging.")

    return dest, backup


def _restore_staged(entries: list[tuple[Path, Path | None]]) -> None:
    for dest, backup in reversed(entries):
        if backup is not None:
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            if backup.is_dir():
                shutil.copytree(backup, dest)
                shutil.rmtree(backup)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, dest)
                backup.unlink(missing_ok=True)
        else:
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()


def _stage_bundle_entries(
    *,
    bundle_dir: Path,
    repo_dir: Path,
    entries: list[dict[str, str]],
    backup_root: Path,
) -> list[tuple[Path, Path | None]]:
    staged: list[tuple[Path, Path | None]] = []
    for entry in entries:
        dest, backup = _copy_with_mode(
            bundle_dir / entry["path"],
            repo_dir / entry["path"],
            entry["mode"],
            backup_root,
        )
        staged.append((dest, backup))
    return staged


def _has_tests(path: Path) -> bool:
    if not path.exists():
        return False
    for child in path.rglob("*"):
        if child.is_file():
            return True
    return False
def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> int:
    """Run a command, streaming output. Returns exit code."""

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=merged_env,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        console.print(line.rstrip())
    ret = proc.wait()
    if check and ret != 0:
        raise subprocess.CalledProcessError(ret, cmd)
    return ret


def _run_full_suite(*, repo_dir: Path, base_env: dict[str, str], config: dict[str, Any]) -> None:
    """Execute the repository's full test command as described in the manifest."""

    console.print("[cyan]Running full test command...[/cyan]")
    working_path = Path(config.get("working_dir", "."))
    repo_root = repo_dir.resolve()
    full_workdir = (repo_dir / working_path).resolve()
    try:
        full_workdir.relative_to(repo_root)
    except ValueError as exc:  # pragma: no cover - safety guard
        raise ValidationError("tests.full.working_dir must stay within the cloned repository.") from exc

    full_env = dict(base_env)
    full_env.update(config.get("env", {}))

    def _run_shell(command: str, *, check: bool = True) -> int:
        return _run(
            ["bash", "-lc", command],
            cwd=full_workdir,
            env=full_env,
            check=check,
        )

    try:
        for prereq in config.get("prerequisites", []):
            console.print(f"[cyan]Prerequisite:[/cyan] {prereq}")
            try:
                _run_shell(prereq)
            except subprocess.CalledProcessError as exc:
                raise ValidationError(
                    f"Prerequisite command failed with exit code {exc.returncode}: {prereq}"
                ) from exc

        main_command = config["command"]
        console.print(f"[cyan]Full command:[/cyan] {main_command}")
        exit_code = _run_shell(main_command, check=False)
        if exit_code != 0:
            raise ValidationError(
                f"Full test command failed with exit code {exit_code}: {main_command}"
            )
    finally:
        for cleanup_cmd in config.get("cleanup", []):
            console.print(f"[cyan]Cleanup:[/cyan] {cleanup_cmd}")
            try:
                _run_shell(cleanup_cmd, check=False)
            except subprocess.CalledProcessError as cleanup_exc:
                console.print(
                    f"[yellow]Cleanup command failed (exit code {cleanup_exc.returncode}): {cleanup_cmd}[/yellow]"
                )



if TYPE_CHECKING:  # pragma: no cover
    from .evaluation import EvaluationResult


def _summarize_evaluation(result: "EvaluationResult", bundle_dir: Path) -> None:
    console.print(
        f"[bold]{result.status.upper()}[/bold] model attempt for [cyan]{result.task_id}[/cyan] using [magenta]{result.model}[/magenta]."
    )
    console.print(
        "Baseline: pass2pass={}; fail2pass={}".format(
            result.baseline.get("pass2pass"), result.baseline.get("fail2pass")
        )
    )
    console.print(
        "Patched: pass2pass={}; fail2pass={}".format(
            result.patched.get("pass2pass"), result.patched.get("fail2pass")
        )
    )

    if result.skip_baseline:
        console.print("[yellow]Baseline guardrails skipped via --skip-baseline.[/yellow]")

    if result.stages:
        for stage in result.stages:
            title = stage.get("title") or stage.get("name")
            status = stage.get("status", "unknown")
            console.print(f"Stage {title}: {status}")

    transcript_filename = f"evaluation_{_sanitize_model_name(result.model)}.log"
    transcript_path = bundle_dir / transcript_filename
    if result.transcript is not None:
        transcript_path.write_text(result.transcript, encoding="utf-8")
        result.transcript_path = transcript_filename
        console.print(
            f"[green]Saved full transcript to[/green] [bold]{transcript_path}[/bold]."
        )

    filename = f"evaluation_{_sanitize_model_name(result.model)}.json"
    output_path = bundle_dir / filename
    output_path.write_text(json.dumps(result.as_dict(), indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]Saved evaluation report to[/green] [bold]{output_path}[/bold].")

    if result.snapshots:
        console.print(
            "[green]Snapshots saved:[/green] "
            + ", ".join(result.snapshots)
        )


def _sanitize_model_name(name: str) -> str:
    allowed = {"-", "_", "."}
    return "".join(ch if ch.isalnum() or ch in allowed else "_" for ch in name)


@app.command()
def run(
    bundle_dir: Path = typer.Argument(
        Path("."), help="Path to the task bundle (defaults to current directory)"
    ),
    model: str = typer.Option(
        ..., "--model", "-m", help="Model identifier to evaluate"
    ),
    modal: bool = typer.Option(
        True,
        "--modal/--no-modal",
        help="Run evaluation inside Modal (legacy local flow)",
    ),
    remote: bool = typer.Option(
        False,
        "--remote/--no-remote",
        help="Enqueue the run via the SWEAP backend API and stream status",
    ),
    remote_task_id: Optional[str] = typer.Option(
        None,
        "--remote-task-id",
        help="Override remote task id (defaults to metadata.remote.task_id)",
    ),
    remote_version: Optional[int] = typer.Option(
        None,
        "--remote-version",
        help="Override remote bundle version (defaults to metadata.remote.bundle_version or latest)",
    ),
    llm_command: Optional[str] = typer.Option(
        None,
        "--llm-command",
        help="Override the command used to launch the LLM inside Modal",
    ),
    codex_auth: Optional[Path] = typer.Option(
        None,
        "--codex-auth",
        help="Path to Codex auth.json (defaults to ~/.codex/auth.json if present)",
    ),
    codex_config: Optional[Path] = typer.Option(
        None,
        "--codex-config",
        help="Path to Codex config.toml (defaults to ~/.codex/config.toml if present)",
    ),
    codex_api_key: Optional[str] = typer.Option(
        None,
        "--codex-api-key",
        help="Codex API key to use for sandbox login (overrides OPENAI_API_KEY env vars)",
    ),
    codex_api_key_file: Optional[Path] = typer.Option(
        None,
        "--codex-api-key-file",
        help="Path to a file containing a Codex API key (processed before env vars)",
    ),
    skip_llm_login: Optional[bool] = typer.Option(
        None,
        "--skip-llm-login/--require-llm-login",
        help="Reuse the existing Codex session instead of running 'codex login' inside Modal",
    ),
    skip_baseline: bool = typer.Option(
        False,
        "--skip-baseline",
        help="Skip running baseline guardrail tests before the model attempt",
    ),
    snapshots: bool = typer.Option(
        False,
        "--snapshots/--no-snapshots",
        help="Capture repo snapshots (zip) at key stages during evaluation",
    ),
    modal_timeout: int = typer.Option(
        7200,
        "--modal-timeout",
        help="Timeout in seconds for the Modal sandbox during evaluation",
    ),
    github_token: Optional[str] = typer.Option(
        None,
        "--github-token",
        help="GitHub token for cloning private repos during remote runs (not stored in manifest)",
    ),
) -> None:
    """Evaluate a task bundle via the backend API or legacy Modal flow."""

    bundle_dir = bundle_dir.resolve()
    try:
        manifest, _ = _load_manifest(bundle_dir)
    except ValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    env_llm_command = os.environ.get("SWEEP_LLM_COMMAND")
    effective_llm_command = llm_command or env_llm_command or DEFAULT_LLM_COMMAND

    api_key_value: Optional[str] = None
    if codex_api_key_file is not None:
        key_path = codex_api_key_file.expanduser()
        if key_path.is_file():
            candidate = key_path.read_text(encoding="utf-8").strip()
            if candidate:
                api_key_value = candidate
            else:
                console.print(f"[yellow]Codex API key file at {key_path} is empty; ignoring.[/yellow]")
        else:
            console.print(f"[yellow]Codex API key file not found at {key_path}[/yellow]")

    if codex_api_key is not None:
        candidate = codex_api_key.strip()
        if candidate:
            api_key_value = candidate
        else:
            console.print("[yellow]Ignoring empty --codex-api-key value.[/yellow]")

    if api_key_value is None:
        env_candidate = os.environ.get("OPENAI_API_KEY")
        if env_candidate:
            api_key_value = env_candidate.strip()
        else:
            legacy_candidate = os.environ.get("CODEX_API_KEY")
            if legacy_candidate:
                api_key_value = legacy_candidate.strip()

    resolved_auth_path = (codex_auth or (Path.home() / ".codex" / "auth.json")).expanduser()
    resolved_config_path = (codex_config or (Path.home() / ".codex" / "config.toml")).expanduser()
    has_local_session = resolved_auth_path.is_file() and resolved_config_path.is_file()

    if not api_key_value and not has_local_session:
        console.print(
            "[yellow]No Codex API key or local session files detected; Codex login will likely fail.[/yellow]"
        )

    if remote:
        try:
            api_client = load_api_client_from_env()
        except ApiClientError as exc:
            console.print(f"[red]{exc}")
            raise typer.Exit(code=1)

        remote_info = (manifest.get("metadata") or {}).get("remote", {})
        task_identifier = remote_task_id or remote_info.get("task_id")
        if not task_identifier:
            console.print(
                "[red]Remote task id not found. Run `task submit` first or provide --remote-task-id.[/red]"
            )
            raise typer.Exit(code=1)

        version_to_use = remote_version if remote_version is not None else remote_info.get("bundle_version")
        if isinstance(version_to_use, dict):
            version_to_use = version_to_use.get("version")
        if remote_version is None and version_to_use is None:
            console.print(
                "[yellow]No remote bundle version recorded; backend will use the latest available version.[/yellow]"
            )

        options_payload: Dict[str, Any] = {}
        if effective_llm_command:
            options_payload["llm_command"] = effective_llm_command
        if skip_baseline:
            options_payload["skip_baseline"] = True
        if snapshots:
            options_payload["snapshots"] = True
        if modal_timeout:
            options_payload["modal_timeout"] = int(modal_timeout)
        if github_token:
            masked = github_token[:3] + "..." + github_token[-3:] if len(github_token) >= 6 else "***"
            console.print(f"[cyan]Passing GitHub token to remote worker ({masked}).[/cyan]")
            options_payload["github_token"] = github_token
        if api_key_value:
            console.print(
                "[yellow]Remote runs do not accept inline Codex API keys. Configure the worker environment with OPENAI_API_KEY instead.[/yellow]"
            )

        console.print(
            f"[cyan]Enqueueing remote run for task {task_identifier} "
            f"(version {version_to_use if version_to_use is not None else 'latest'})...[/cyan]"
        )

        saved: List[Path] = []

        try:
            with api_client as client:
                run_record = client.enqueue_run(
                    task_id=task_identifier,
                    model_id=model,
                    task_version=version_to_use,
                    options=options_payload or None,
                )
                run_id = run_record.get("id")
                status = run_record.get("status")
                bundle_url = run_record.get("bundle_download_url")
                message = f"[cyan]Run {run_id} queued with status {status}."
                if bundle_url:
                    message += f" Bundle download: {bundle_url}"
                message += "[/cyan]"
                console.print(message)
                while status in {"queued", "running"}:
                    time.sleep(REMOTE_RUN_POLL_SECONDS)
                    run_record = client.get_run(run_id)
                    new_status = run_record.get("status")
                    console.print(f"[cyan]Run {run_id} status: {new_status}[/cyan]")
                    status = new_status

                message = run_record.get("message")
                if message:
                    console.print(f"[cyan]Message: {message}[/cyan]")

                saved = _save_remote_artifacts(
                    bundle_dir=bundle_dir,
                    client=client,
                    run_record=run_record,
                    model=model,
                )
        except ApiClientError as exc:
            console.print(f"[red]{exc}")
            if exc.response_json:
                console.print(f"[red]{exc.response_json}")
            raise typer.Exit(code=1)

        final_status = run_record.get("status")
        if final_status == "succeeded":
            console.print("[green]Remote run succeeded.[/green]")
        else:
            console.print(f"[red]Remote run finished with status {final_status}.[/red]")
        raise typer.Exit(code=0 if final_status == "succeeded" else 1)

    if not modal:
        console.print(
            "[red]Local evaluation is not implemented yet. Re-run with --modal or --remote.[/red]"
        )
        raise typer.Exit(code=1)
    try:
        from .evaluation import run_modal_evaluation
    except ImportError:
        console.print(
            "[red]Internal evaluation module missing. Please update the CLI to the latest version.[/red]"
        )
        raise typer.Exit(code=1)


    env_updates: dict[str, str] = {}
    if api_key_value:
        env_updates["OPENAI_API_KEY"] = api_key_value

    effective_skip_login = skip_llm_login if skip_llm_login is not None else True
    if api_key_value and skip_llm_login is None:
        effective_skip_login = False

    should_load_auth = codex_auth is not None or not api_key_value
    if should_load_auth:
        auth_path = (codex_auth or (Path.home() / ".codex" / "auth.json")).expanduser()
        if auth_path.is_file():
            env_updates["CODEX_AUTH_JSON_B64"] = _encode_file_b64(auth_path)
        elif codex_auth is not None:
            console.print(f"[yellow]Codex auth file not found at {auth_path}[/yellow]")

    should_load_config = codex_config is not None or not api_key_value
    if should_load_config:
        config_path = (codex_config or (Path.home() / ".codex" / "config.toml")).expanduser()
        if config_path.is_file():
            env_updates["CODEX_CONFIG_TOML_B64"] = _encode_file_b64(config_path)
        elif codex_config is not None:
            console.print(f"[yellow]Codex config file not found at {config_path}[/yellow]")

    if effective_skip_login:
        env_updates.setdefault("CODEX_SKIP_LOGIN", "1")
    else:
        env_updates.pop("CODEX_SKIP_LOGIN", None)

    if llm_command:
        stripped = llm_command.strip()
        if stripped:
            try:
                first_token = shlex.split(stripped)[0]
            except ValueError:
                first_token = ""
            if not first_token.startswith("codex"):
                console.print(
                    "[yellow]Wrapping provided prompt in the default Codex command.[/yellow]"
                )
                effective_llm_command = DEFAULT_LLM_PREFIX + shlex.quote(stripped)
            else:
                effective_llm_command = stripped

    console.print(
        "[cyan]Running Modal evaluation; the configured LLM command will attempt live edits inside the sandbox.[/cyan]"
    )
    try:
        with _TempEnv(env_updates):
            result = run_modal_evaluation(
                bundle_dir=bundle_dir,
                manifest=manifest,
                model=model,
                llm_command=effective_llm_command,
                skip_baseline=skip_baseline,
                snapshots=snapshots,
                timeout_seconds=modal_timeout,
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        console.print(f"[red]Evaluation failed: {exc}[/red]")
        raise typer.Exit(code=1)

    _summarize_evaluation(result, bundle_dir)
    raise typer.Exit(code=0)


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        rprint("[red]\nAborted by user.[/red]")
        sys.exit(1)
