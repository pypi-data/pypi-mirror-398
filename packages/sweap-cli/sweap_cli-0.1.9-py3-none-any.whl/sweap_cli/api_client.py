"""HTTP client helpers for interacting with the SWEAP backend API."""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


class ApiError(RuntimeError):
    """Error raised when the SWEAP backend returns a non-success response."""

    def __init__(self, message: str, *, status_code: int, response_json: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_json = response_json


@dataclass
class BundleUploadResponse:
    task_id: str
    version: int
    upload_url: str
    download_url: Optional[str]
    expires_at: str


class SweapApiClient(AbstractContextManager["SweapApiClient"]):
    """Simple wrapper around httpx for the SWEAP backend endpoints."""

    def __init__(self, *, base_url: str, access_token: str, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    # context manager support -------------------------------------------------
    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - delegation
        self.close()

    def close(self) -> None:
        self._client.close()

    # API helpers -------------------------------------------------------------
    def create_task(self, *, title: str, repo_url: str, repo_commit: str,
                    slug: str | None = None, visibility: str | None = None,
                    description: str | None = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "repo_url": repo_url,
            "repo_commit": repo_commit,
        }
        if slug:
            payload["slug"] = slug
        if visibility:
            payload["visibility"] = visibility
        if description:
            payload["description"] = description

        resp = self._client.post("/tasks", json=payload)
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to create task (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        return resp.json()

    def get_task(self, task_id: str) -> Dict[str, Any]:
        resp = self._client.get(f"/tasks/{task_id}")
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to fetch task {task_id} (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        return resp.json()

    def create_bundle_version(
        self,
        *,
        task_id: str,
        manifest: Dict[str, Any],
        requirements_hash: str | None,
        notes: str | None = None,
    ) -> BundleUploadResponse:
        payload = {
            "manifest": manifest,
            "requirements_hash": requirements_hash,
            "notes": notes,
        }
        resp = self._client.post(f"/tasks/{task_id}/bundles", json=payload)
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to create bundle version (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        data = resp.json()
        return BundleUploadResponse(
            task_id=data["task_id"],
            version=data["version"],
            upload_url=data["upload_url"],
            download_url=data.get("download_url"),
            expires_at=data["expires_at"],
        )

    def download_signed_url(self, *, url: str) -> bytes:
        resp = httpx.get(url, timeout=self._client.timeout)
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to download artifact (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        return resp.content

    def upload_file(self, *, upload_url: str, file_path: Path, content_type: str = "application/zip") -> None:
        with file_path.open("rb") as fh:
            payload = fh.read()
        resp = httpx.put(
            upload_url,
            content=payload,
            headers={
                "Content-Type": content_type,
                "x-upsert": "false",
            },
            timeout=self._client.timeout,
        )
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to upload file (status {resp.status_code}): {resp.text}",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )

    def get_bundle_version(self, task_id: str, version: int) -> Dict[str, Any]:
        resp = self._client.get(f"/tasks/{task_id}/bundles/{version}")
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to fetch bundle {task_id} v{version} (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        return resp.json()

    def enqueue_run(
        self,
        *,
        task_id: str,
        model_id: str,
        task_version: int | None = None,
        notes: str | None = None,
        options: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model_id": model_id}
        if task_version is not None:
            payload["task_version"] = task_version
        if notes:
            payload["notes"] = notes
        if options:
            payload["options"] = options
        resp = self._client.post(f"/tasks/{task_id}/runs", json=payload)
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to enqueue run (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        return resp.json()

    def get_run(self, run_id: str) -> Dict[str, Any]:
        resp = self._client.get(f"/runs/{run_id}")
        if resp.status_code >= 400:
            raise ApiError(
                f"Failed to fetch run {run_id} (status {resp.status_code})",
                status_code=resp.status_code,
                response_json=_safe_json(resp),
            )
        return resp.json()


def load_api_client_from_env() -> SweapApiClient:
    """Instantiate a SWEAP API client using environment variables."""

    base_url = os.environ.get("SWEAP_API_URL")
    access_token = os.environ.get("SWEAP_API_TOKEN")
    if not base_url or not access_token:
        missing = []
        if not base_url:
            missing.append("SWEAP_API_URL")
        if not access_token:
            missing.append("SWEAP_API_TOKEN")
        raise ApiError(
            f"Missing required environment variables: {', '.join(missing)}",
            status_code=0,
        )
    return SweapApiClient(base_url=base_url, access_token=access_token)


def _safe_json(response: httpx.Response) -> Any | None:
    try:
        return response.json()
    except ValueError:
        return None
