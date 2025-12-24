"""Helpers for parsing manifest runner and dependency sections."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


class ManifestError(ValueError):
    """Raised when a manifest section is invalid."""


@dataclass
class RunnerInfo:
    """Normalized runner configuration extracted from the manifest."""

    type: str
    command: str
    version: int
    env: Dict[str, str]
    commands: Dict[str, str]
    raw: Dict[str, Any]


@dataclass
class Dependency:
    """Normalized dependency descriptor from environment.dependencies."""

    kind: str
    path: Optional[str]
    install: Optional[str]
    data: Dict[str, Any]


def parse_runner(runner_section: Any) -> RunnerInfo:
    """Validate and normalize the `runner` section of the manifest."""

    if not isinstance(runner_section, dict):
        raise ManifestError("Manifest.runner must be an object.")

    runner_type = runner_section.get("type")
    if not isinstance(runner_type, str) or not runner_type.strip():
        raise ManifestError("runner.type must be a non-empty string.")
    runner_type = runner_type.strip()

    version = runner_section.get("version", 1)
    try:
        version_int = int(version)
    except (TypeError, ValueError) as exc:
        raise ManifestError("runner.version must be an integer if provided.") from exc

    command_field = runner_section.get("command")
    commands: Dict[str, str] = {}

    if isinstance(command_field, dict):
        for key, value in command_field.items():
            if not isinstance(key, str) or not key.strip():
                raise ManifestError("runner.command keys must be non-empty strings.")
            if not isinstance(value, str) or not value.strip():
                raise ManifestError("runner.command values must be non-empty strings.")
            commands[key.strip()] = value.strip()
    elif isinstance(command_field, str):
        if not command_field.strip():
            raise ManifestError("runner.command must not be an empty string.")
        commands["default"] = command_field.strip()
    elif command_field is None:
        commands = {}
    else:
        raise ManifestError("runner.command must be a string or object mapping names to commands.")

    command = commands.get("default") or commands.get("baseline")
    if command is None and commands:
        command = next(iter(commands.values()))

    if not command:
        raise ManifestError("runner.command must define at least one command string.")

    env_field = runner_section.get("env") or {}
    if not isinstance(env_field, dict):
        raise ManifestError("runner.env must be an object mapping strings to values.")
    env_normalized: Dict[str, str] = {}
    for key, value in env_field.items():
        if not isinstance(key, str) or not key:
            raise ManifestError("runner.env keys must be non-empty strings.")
        if not isinstance(value, (str, int, float, bool)):
            raise ManifestError("runner.env values must be string-like.")
        env_normalized[key] = str(value)

    return RunnerInfo(
        type=runner_type,
        command=command,
        version=version_int,
        env=env_normalized,
        commands=commands,
        raw=dict(runner_section),
    )


def parse_dependencies(environment_section: Any) -> List[Dependency]:
    """Normalize the dependency descriptors declared in environment.dependencies."""

    if not isinstance(environment_section, dict):
        raise ManifestError("Manifest.environment must be an object.")

    dependencies = environment_section.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ManifestError("environment.dependencies must be a non-empty array of dependency objects.")

    normalized: List[Dependency] = []
    for index, entry in enumerate(dependencies):
        if not isinstance(entry, dict):
            raise ManifestError(f"environment.dependencies[{index}] must be an object.")

        kind = entry.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            raise ManifestError(f"environment.dependencies[{index}].kind must be a non-empty string.")
        kind = kind.strip()

        path = entry.get("path")
        if path is not None:
            if not isinstance(path, str) or not path.strip():
                raise ManifestError(f"environment.dependencies[{index}].path must be a non-empty string when provided.")
            path = path.strip()
            if Path(path).is_absolute():
                raise ManifestError(f"environment.dependencies[{index}].path must be relative to the bundle.")

        install = entry.get("install")
        if install is not None:
            if not isinstance(install, str) or not install.strip():
                raise ManifestError(f"environment.dependencies[{index}].install must be a non-empty string when provided.")
            install = install.strip()

        data = {k: v for k, v in entry.items() if k not in {"kind", "path", "install"}}
        normalized.append(Dependency(kind=kind, path=path, install=install, data=data))

    return normalized


def find_dependency(dependencies: List[Dependency], kind: str) -> Optional[Dependency]:
    """Return the first dependency matching ``kind`` (case-insensitive)."""

    target = kind.lower()
    for dependency in dependencies:
        if dependency.kind.lower() == target:
            return dependency
    return None


def resolve_runner_dependency(manifest: dict[str, Any], runner_info: RunnerInfo) -> Dependency:
    """Return the dependency descriptor required by the configured runner."""

    environment = manifest.get("environment")
    if not isinstance(environment, dict):
        raise ManifestError("Manifest.environment must be an object.")

    dependencies = parse_dependencies(environment)
    runner_type = runner_info.type.lower()

    if runner_type in {"pytest", "python"}:
        dependency = find_dependency(dependencies, "python")
        if dependency is None or not dependency.path:
            raise ManifestError(
                "environment.dependencies must include a python dependency with a relative path."
            )
        return dependency

    if runner_type in {"node", "npm", "yarn"}:
        dependency = find_dependency(dependencies, "node") or find_dependency(dependencies, "npm")
        if dependency is None or not dependency.path:
            raise ManifestError(
                "environment.dependencies must include a node dependency (e.g. package.json)."
            )
        return dependency

    if runner_type in {"maven", "java", "gradle"}:
        dependency = (
            find_dependency(dependencies, "maven")
            or find_dependency(dependencies, "java")
            or find_dependency(dependencies, "gradle")
        )
        if dependency is None or not dependency.path:
            raise ManifestError(
                "environment.dependencies must include a maven/gradle dependency with a relative path (e.g. pom.xml or build.gradle)."
            )
        return dependency

    raise ManifestError(f"Unsupported runner type '{runner_info.type}'.")
