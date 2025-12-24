from __future__ import annotations

import sys
import base64
import json
import textwrap
import importlib
from pathlib import Path
from typing import Optional, Any

from rich.console import Console

console = Console()


def validate_in_modal(
    *,
    bundle_dir: Path,
    repo_url: str,
    commit: str,
    runner: dict[str, Any],
    dependency: dict[str, Any],
    fail_dir_rel: str,
    pass_dir_rel: str,
    shared_dirs: list[dict[str, str]],
    shared_dirs_pre: list[dict[str, str]],
    shared_dirs_post: list[dict[str, str]],
    full_config: dict[str, Any] | None,
    run_full: bool,
    github_token: Optional[str] = None,
    snapshots: bool = False,
    timeout_seconds: int = 1800,
) -> int:
    """Run validation inside a Modal sandbox (clone, install deps, execute tests)."""
    try:
        import modal
    except Exception as e:  # pragma: no cover - import guard
        console.print("[red]Modal is not installed. Run `pip install modal`.[/red]")
        return 2

    if run_full and not full_config:
        console.print("[red]Manifest missing tests.full configuration required for --full validation.[/red]")
        return 1

    bundle_dir = bundle_dir.resolve()
    patch_path = bundle_dir / "gold_patch.diff"
    if not patch_path.exists():
        console.print(f"[red]Missing gold_patch.diff at {patch_path}[/red]")
        return 1

    dependency_rel = dependency.get("path")
    if dependency_rel:
        dependency_path = bundle_dir / dependency_rel
        if not dependency_path.exists():
            console.print(f"[red]Missing dependency artifact at {dependency_path}[/red]")
            return 1
    runner_type = (runner.get("type") or "").lower()
    runner_cmd = runner.get("command", "")
    runner_env = runner.get("env") or {}
    if not runner_cmd:
        console.print("[red]Runner command is required for Modal validation.[/red]")
        return 1
    if runner_type in {"node", "npm", "yarn"}:
        lockfile_rel = (dependency.get("data") or {}).get("lockfile")
        if lockfile_rel:
            lockfile_path = bundle_dir / lockfile_rel
            if not lockfile_path.exists():
                console.print(f"[yellow]Lockfile {lockfile_path} missing; continuing without it.[/yellow]")

    secret = None
    if github_token:
        masked = f"{github_token[:3]}...{github_token[-3:]}" if len(github_token) > 6 else "***"
        console.print(f"[cyan]Configuring git with provided GitHub token (masked): {masked}[/cyan]")
        secret = modal.Secret.from_dict({"GITHUB_TOKEN": github_token})

    manifest = json.loads((bundle_dir / "task.json").read_text(encoding="utf-8"))
    environment = manifest.get("environment", {})
    modal_image_name = environment.get("modal_image")
    modal_image_id = environment.get("modal_image_id")
    modal_python_version = environment.get("modal_python_version", "3.10")

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
            return 1

    packages = ["git", "python3-venv"]
    if runner_type in {"node", "npm", "yarn"}:
        packages.extend(["nodejs", "npm"])
    if runner_type in {"maven", "java", "gradle"}:
        packages.extend(["openjdk-17-jdk", "maven", "gradle"])
    packages = list(dict.fromkeys(packages))

    image = None
    if modal_image_id:
        try:
            image = image_api.from_id(modal_image_id)
        except Exception:
            image = None
    if image is None and modal_image_name:
        try:
            image = image_api.from_name(modal_image_name)
        except AttributeError:
            try:
                image = image_api.from_registry(modal_image_name)
            except Exception:
                image = None
    if image is None:
        image = (
            image_api.debian_slim(python_version=modal_python_version)
            .apt_install(*packages)
            .add_local_dir(str(bundle_dir), remote_path="/bundle")
        )

    app = modal.App.lookup("sweap-cli", create_if_missing=True)
    with modal.enable_output():
        sb = modal.Sandbox.create(app=app, image=image, secrets=[secret] if secret else [], timeout=timeout_seconds)
    try:
        # Configure git auth if token is present
        if github_token:
            # Use token via HTTPS auth header for git
            setup = sb.exec(
                "bash",
                "-lc",
                "git config --global http.https://github.com/.extraheader 'Authorization: Basic '$(echo -n x-access-token:$GITHUB_TOKEN | base64 -w0)",
                env={"GITHUB_TOKEN": github_token},
                timeout=30,
            )
            setup.wait()

        git_env = {"GIT_TERMINAL_PROMPT": "0"}
        if github_token:
            git_env["GITHUB_TOKEN"] = github_token

        clone = sb.exec(
            "bash",
            "-lc",
            f"set -euo pipefail; git clone {repo_url} repo && cd repo && git checkout {commit}",
            env=git_env,
        )
        for line in clone.stdout:
            console.print(line, end="")
        rc = clone.wait()
        if rc != 0:
            console.print("[red]Git clone/checkout failed in Modal Sandbox.[/red]")
            return rc
        console.print("[cyan]Clone and checkout completed in Modal sandbox.[/cyan]")

        chk = sb.exec("bash", "-lc", "cd repo && git apply --check /bundle/gold_patch.diff")
        for line in chk.stdout:
            console.print(line, end="")
        rc = chk.wait()
        if rc != 0:
            console.print("[red]Patch does not apply cleanly in Modal Sandbox.[/red]")
            return rc
        runner_cmd = runner.get("command", "")
        runner_env = runner.get("env") or {}

        validation_script = _render_validation_script(
            runner_type=runner_type,
            runner_cmd=runner_cmd,
            runner_env=runner_env,
            dependency=dependency,
            fail_dir_rel=fail_dir_rel,
            pass_dir_rel=pass_dir_rel,
            shared_dirs=shared_dirs,
            shared_dirs_pre=shared_dirs_pre,
            shared_dirs_post=shared_dirs_post,
            full_config=full_config if run_full else None,
            run_full=run_full,
            snapshots=snapshots,
        )
        command = f"python3 - <<'PY'\n{validation_script}\nPY"
        validate_proc = sb.exec(
            "bash",
            "-lc",
            command,
            timeout=1800,
        )
        snapshot_files: list[Path] = []
        for raw_line in validate_proc.stdout:
            line = raw_line.rstrip("\n")
            console.print(line)
            if line.startswith("SNAPSHOT_ZIP::"):
                try:
                    _, label, b64data = line.split("::", 2)
                    data = base64.b64decode(b64data)
                    snap_path = bundle_dir / f"snapshot_{label}.zip"
                    snap_path.write_bytes(data)
                    snapshot_files.append(snap_path)
                except Exception:
                    console.print(f"[yellow]Failed to save snapshot from line: {line}[/yellow]")
        stderr_output = ""
        if validate_proc.stderr is not None:
            stderr_output = validate_proc.stderr.read()
            if stderr_output:
                console.print(stderr_output, end="")
        rc = validate_proc.wait()
        if rc != 0:
            console.print("[red]Modal validation failed.[/red]")
        else:
            console.print("[green]OK[/green] Modal validation succeeded.")
        return rc
    finally:
        try:
            sb.terminate()
        except Exception:
            pass


def _render_validation_script(
    *,
    runner_type: str,
    runner_cmd: str,
    runner_env: dict[str, Any],
    dependency: dict[str, Any],
    fail_dir_rel: str,
    pass_dir_rel: str,
    shared_dirs: list[dict[str, str]],
    shared_dirs_pre: list[dict[str, str]],
    shared_dirs_post: list[dict[str, str]],
    full_config: dict[str, Any] | None,
    run_full: bool,
    snapshots: bool,
) -> str:
    runner_type_literal = json.dumps(runner_type)
    runner_cmd_literal = json.dumps(runner_cmd)
    runner_env_literal = json.dumps({key: str(value) for key, value in runner_env.items()})
    dependency_literal = json.dumps(dependency)
    fail_dir_literal = json.dumps(fail_dir_rel)
    pass_dir_literal = json.dumps(pass_dir_rel)
    shared_dirs_literal = json.dumps(shared_dirs)
    shared_dirs_pre_literal = json.dumps(shared_dirs_pre)
    shared_dirs_post_literal = json.dumps(shared_dirs_post)
    full_config_literal = json.dumps(full_config) if full_config is not None else "null"
    run_full_literal = "True" if run_full else "False"
    snapshots_literal = "True" if snapshots else "False"

    script = textwrap.dedent(
        """
        import json
        import os
        import shlex
        import shutil
        import subprocess
        import sys
        import venv
        import uuid
        from pathlib import Path

        bundle_dir = Path('/bundle')
        repo_dir = Path('repo')
        patch_path = bundle_dir / 'gold_patch.diff'

        runner_type = json.loads(__RUNNER_TYPE__).lower()
        runner_cmd = json.loads(__RUNNER_CMD__)
        runner_env = json.loads(__RUNNER_ENV__)
        dependency = json.loads(__DEPENDENCY__)
        fail_dir_rel = Path(json.loads(__FAIL_DIR__))
        pass_dir_rel = Path(json.loads(__PASS_DIR__))
        shared_dirs = json.loads(__SHARED_DIRS__)
        shared_dirs_pre = json.loads(__SHARED_DIRS_PRE__)
        shared_dirs_post = json.loads(__SHARED_DIRS_POST__)
        run_full = __RUN_FULL__
        full_config = json.loads(\"\"\"__FULL_CONFIG__\"\"\")
        snapshots_enabled = __SNAPSHOTS__

        def log(message: str) -> None:
            print(message, flush=True)

        def run(cmd, *, cwd=None, check=True, env=None):
            shown = " ".join(cmd)
            log("$ " + shown)
            process = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                text=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            if check and process.returncode != 0:
                raise RuntimeError(f"Command failed with exit code {process.returncode}: {shown}")
            return process.returncode

        def copy_artifact(rel_path: str, *, optional: bool = False) -> Path | None:
            if not rel_path:
                return None
            source = bundle_dir / rel_path
            if not source.exists():
                if optional:
                    log(f"Skipping optional artifact missing at {source}")
                    return None
                raise RuntimeError(f"Missing dependency artifact at {source}")
            destination = repo_dir / rel_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            return destination

        def has_tests(path: Path) -> bool:
            return path.exists() and any(child.is_file() for child in path.rglob('*'))

        def _backup_path(base: Path, hint: str) -> Path:
            base.mkdir(parents=True, exist_ok=True)
            return base / f"{hint}_{uuid.uuid4()}"

        def copy_with_mode(src: Path, dest: Path, mode: str, backup_root: Path) -> tuple[Path, Path | None]:
            if not src.exists():
                raise RuntimeError(f"Shared path missing in bundle: {src}")
            dest_exists = dest.exists()
            backup = None
            if dest_exists:
                if mode == 'fail':
                    raise RuntimeError(f"Cannot stage {src} into existing path {dest}; use merge/overwrite.")
                backup = _backup_path(backup_root, dest.name or 'backup')
                if dest.is_file():
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest, backup)
                else:
                    shutil.copytree(dest, backup)

            if src.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    if mode == 'overwrite':
                        shutil.copy2(src, dest)
                    else:
                        raise RuntimeError(f"File already exists at {dest}; use overwrite.")
                else:
                    shutil.copy2(src, dest)
            else:
                if not dest.exists():
                    shutil.copytree(src, dest)
                else:
                    if mode == 'overwrite':
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                        shutil.copytree(src, dest)
                    elif mode == 'merge':
                        for root, _, files in os.walk(src):
                            root_path = Path(root)
                            rel_root = root_path.relative_to(src)
                            for file_name in files:
                                source_file = root_path / file_name
                                target_file = dest / rel_root / file_name
                                if target_file.exists():
                                    raise RuntimeError(f"Collision staging {source_file} into existing {target_file}; use overwrite.")
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(source_file, target_file)
                    else:
                        raise RuntimeError(f"Unsupported mode {mode}")
            return dest, backup

        def stage_entries(entries: list[dict], backup_root: Path) -> list[tuple[Path, Path | None]]:
            staged: list[tuple[Path, Path | None]] = []
            for entry in entries:
                dest, backup = copy_with_mode(
                    bundle_dir / entry['path'],
                    repo_dir / entry['path'],
                    entry['mode'],
                    backup_root,
                )
                staged.append((dest, backup))
            return staged

        def restore_entries(staged: list[tuple[Path, Path | None]]) -> None:
            for dest, backup in reversed(staged):
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

        def run_full_suite(full_cfg, base_env):
            workdir = (repo_dir / Path(full_cfg.get('working_dir', '.'))).resolve()
            repo_root = repo_dir.resolve()
            if not str(workdir).startswith(str(repo_root)):
                raise RuntimeError('tests.full.working_dir must remain within the repository checkout.')

            env_map = base_env.copy()
            extra_env = full_cfg.get('env') or {}
            if not isinstance(extra_env, dict):
                raise RuntimeError('tests.full.env must be a mapping of strings to strings.')
            for key, value in extra_env.items():
                env_map[str(key)] = str(value)

            def _run_shell(command: str, *, check: bool = True):
                return run(['bash', '-lc', command], cwd=workdir, env=env_map, check=check)

            try:
                for prereq in full_cfg.get('prerequisites', []) or []:
                    log(f"Prerequisite: {prereq}")
                    _run_shell(prereq)

                full_command = full_cfg['command']
                log(f"Full command: {full_command}")
                exit_code = _run_shell(full_command, check=False)
                if exit_code != 0:
                    raise RuntimeError(f"Full test command failed with exit code {exit_code}: {full_command}")
            finally:
                for cleanup_cmd in full_cfg.get('cleanup', []) or []:
                    try:
                        log(f"Cleanup: {cleanup_cmd}")
                        _run_shell(cleanup_cmd, check=False)
                    except Exception as cleanup_err:  # pragma: no cover - best effort
                        log(f"Cleanup command failed: {cleanup_cmd} ({cleanup_err})")

        def setup_runner_environment() -> tuple[dict[str, str], list[str]]:
            env_map = os.environ.copy()
            for key, value in runner_env.items():
                env_map[str(key)] = str(value)

            dep_path = dependency.get('path') or ''
            data = dependency.get('data') or {}

            if runner_type in {'pytest', 'python'}:
                if not dep_path:
                    raise RuntimeError('Python runner requires environment.dependencies entry with a path.')
                requirements_target = copy_artifact(dep_path)
                if requirements_target is None:
                    raise RuntimeError('Failed to materialise requirements file.')

                log(f'Using requirements file at {requirements_target}')
                venv_dir = Path('/opt/sweap-venv')
                if venv_dir.exists():
                    log(f'Using prebuilt virtualenv at {venv_dir}')
                    bin_dir = venv_dir / ('Scripts' if os.name == 'nt' else 'bin')
                    env_map['VIRTUAL_ENV'] = str(venv_dir)
                    env_map['PATH'] = str(bin_dir) + os.pathsep + env_map.get('PATH', '')
                else:
                    venv_dir = Path('/tmp/modal-validation-venv')
                    if venv_dir.exists():
                        shutil.rmtree(venv_dir)
                    venv.create(venv_dir, with_pip=True)
                    bin_dir = venv_dir / ('Scripts' if os.name == 'nt' else 'bin')
                    env_map['VIRTUAL_ENV'] = str(venv_dir)
                    env_map['PATH'] = str(bin_dir) + os.pathsep + env_map.get('PATH', '')
                    pip_exe = bin_dir / ('pip.exe' if os.name == 'nt' else 'pip')
                    run([str(pip_exe), 'install', '--upgrade', 'pip'], cwd=repo_dir, env=env_map)
                    install_cmd = dependency.get('install')
                    if install_cmd:
                        formatted = install_cmd.format(
                            path=str(requirements_target),
                            repo=str(repo_dir),
                            requirements=str(requirements_target),
                        )
                        run(['bash', '-lc', formatted], cwd=repo_dir, env=env_map)
                    else:
                        run([str(pip_exe), 'install', '-r', str(requirements_target)], cwd=repo_dir, env=env_map)

            elif runner_type in {'node', 'npm', 'yarn'}:
                if not dep_path:
                    raise RuntimeError('Node runner requires environment.dependencies entry with path to package.json.')
                package_target = copy_artifact(dep_path)
                if package_target is None:
                    raise RuntimeError('Failed to materialise package.json for node runner.')

                lockfile_rel = data.get('lockfile')
                lockfile_target = None
                if lockfile_rel:
                    lockfile_target = copy_artifact(lockfile_rel, optional=True)

                install_cmd = dependency.get('install')
                if install_cmd:
                    formatted = install_cmd.format(
                        path=str(package_target),
                        repo=str(repo_dir),
                        package_json=str(package_target),
                        lockfile=str(lockfile_target) if lockfile_target else '',
                    )
                    run(['bash', '-lc', formatted], cwd=repo_dir, env=env_map)
                else:
                    package_manager = data.get('package_manager', 'npm')
                    default_install = 'npm ci' if package_manager == 'npm' else f"{package_manager} install"
                    run(['bash', '-lc', default_install], cwd=repo_dir, env=env_map)

            elif runner_type in {'maven', 'java', 'gradle'}:
                if not dep_path:
                    raise RuntimeError('Maven/Gradle runner requires environment.dependencies entry with a path (e.g. pom.xml or build.gradle).')
                build_target = copy_artifact(dep_path)
                if build_target is None:
                    raise RuntimeError('Failed to materialise build file for Java runner.')

                wrapper_rel = data.get('wrapper')
                wrapper_target = None
                if wrapper_rel:
                    wrapper_target = copy_artifact(wrapper_rel, optional=True)
                    if wrapper_target and os.name != 'nt':
                        wrapper_target.chmod(wrapper_target.stat().st_mode | 0o111)

                install_cmd = dependency.get('install')
                if install_cmd:
                    formatted = install_cmd.format(
                        repo=str(repo_dir),
                        pom=str(build_target),
                        build=str(build_target),
                        wrapper=str(wrapper_target) if wrapper_target else '',
                    )
                    run(['bash', '-lc', formatted], cwd=repo_dir, env=env_map)
                else:
                    if runner_type == 'gradle':
                        wrapper_cmd = str(wrapper_target) if wrapper_target else 'gradle'
                        bootstrap = data.get('bootstrap', f"{wrapper_cmd} --no-daemon testClasses")
                    else:
                        wrapper_cmd = str(wrapper_target) if wrapper_target else 'mvn'
                        bootstrap = data.get('bootstrap', f"{wrapper_cmd} -B dependency:go-offline")
                    run(['bash', '-lc', bootstrap], cwd=repo_dir, env=env_map)

            else:
                raise RuntimeError(f"Unsupported runner type: {runner_type}")

            cmd_parts = shlex.split(runner_cmd)
            return env_map, cmd_parts

        def main() -> None:
            if not patch_path.exists():
                raise RuntimeError(f"Missing golden patch at {patch_path}")

            env_map, cmd_parts = setup_runner_environment()

            run(['git', 'apply', '--check', str(patch_path)], cwd=repo_dir)

            backup_root = Path('/tmp/modal-validation-backups')
            base_entries = [
                {"path": str(pass_dir_rel), "mode": "fail"},
                {"path": str(fail_dir_rel), "mode": "fail"},
            ]
            baseline_entries = base_entries + shared_dirs + shared_dirs_pre
            patched_entries = base_entries + shared_dirs + shared_dirs_post

            staged_baseline: list[tuple[Path, Path | None]] = []
            staged_patched: list[tuple[Path, Path | None]] = []
            pass_dir = repo_dir / pass_dir_rel
            fail_dir = repo_dir / fail_dir_rel

            def capture(label: str):
                if not snapshots_enabled:
                    return
                snap_path = Path('/tmp') / f"snapshot_{label}.zip"
                if snap_path.exists():
                    snap_path.unlink()
                import zipfile, base64
                with zipfile.ZipFile(
                    snap_path,
                    'w',
                    compression=zipfile.ZIP_DEFLATED,
                    strict_timestamps=False,
                ) as zf:
                    for root, _, files in os.walk(repo_dir):
                        for fname in files:
                            p = Path(root) / fname
                            rel = p.relative_to(repo_dir)
                            zf.write(p, arcname=str(rel))
                b64 = base64.b64encode(snap_path.read_bytes()).decode('utf-8')
                print(f"SNAPSHOT_ZIP::{label}::{b64}", flush=True)

            try:
                capture('A')
                staged_baseline = stage_entries(baseline_entries, backup_root)
                capture('B')

                if has_tests(pass_dir):
                    rc = run(cmd_parts + [str(pass_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                    if rc != 0:
                        raise RuntimeError('Pass2pass tests failed before applying patch.')
                else:
                    log('No pass2pass tests found; skipping baseline pass check.')

                if has_tests(fail_dir):
                    rc = run(cmd_parts + [str(fail_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                    if rc == 0:
                        raise RuntimeError('Fail2pass tests unexpectedly passed before applying patch.')
                else:
                    log('No fail2pass tests found; skipping baseline fail check.')

                restore_entries(staged_baseline)
                staged_baseline = []

                run(['git', 'apply', str(patch_path)], cwd=repo_dir)

                staged_patched = stage_entries(patched_entries, backup_root)
                capture('C')

                if has_tests(pass_dir):
                    rc = run(cmd_parts + [str(pass_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                    if rc != 0:
                        raise RuntimeError('Pass2pass tests failed after applying patch.')

                if has_tests(fail_dir):
                    rc = run(cmd_parts + [str(fail_dir_rel)], cwd=repo_dir, env=env_map, check=False)
                    if rc != 0:
                        raise RuntimeError('Fail2pass tests still failing after applying patch.')

                restore_entries(staged_patched)
                staged_patched = []
                capture('D')

                if run_full:
                    if not full_config:
                        raise RuntimeError('Manifest missing tests.full configuration required for --full validation.')
                    log('Running full test command...')
                    run_full_suite(full_config, env_map)

                log('Modal validation succeeded.')
            finally:
                try:
                    restore_entries(staged_patched)
                except Exception:
                    pass
                try:
                    restore_entries(staged_baseline)
                except Exception:
                    pass

        if __name__ == '__main__':
            try:
                main()
            except Exception as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                sys.exit(1)
        """
    )

    script = script.replace("__RUNNER_TYPE__", runner_type_literal)
    script = script.replace("__RUNNER_CMD__", runner_cmd_literal)
    script = script.replace("__RUNNER_ENV__", runner_env_literal)
    script = script.replace("__DEPENDENCY__", dependency_literal)
    script = script.replace("__FAIL_DIR__", fail_dir_literal)
    script = script.replace("__PASS_DIR__", pass_dir_literal)
    script = script.replace("__SHARED_DIRS__", shared_dirs_literal)
    script = script.replace("__SHARED_DIRS_PRE__", shared_dirs_pre_literal)
    script = script.replace("__SHARED_DIRS_POST__", shared_dirs_post_literal)
    script = script.replace("__RUN_FULL__", run_full_literal)
    script = script.replace("__FULL_CONFIG__", full_config_literal)
    script = script.replace("__SNAPSHOTS__", snapshots_literal)

    return script
