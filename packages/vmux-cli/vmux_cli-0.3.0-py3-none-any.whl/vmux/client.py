"""HTTP client for vmux worker API."""

import json
import os
import time
from typing import Iterator

import httpx

from .config import VmuxConfig, load_config

DEBUG = os.environ.get("VMUX_DEBUG", "").lower() in ("1", "true", "yes")


class TupClient:
    """Client for the vmux worker API."""

    def __init__(self, config: VmuxConfig | None = None):
        self.config = config or load_config()
        self._client = httpx.Client(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(300.0, connect=30.0),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TupClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers

    def run(
        self,
        command: str,
        bundle: str,
        env_vars: dict[str, str] | None = None,
        editables: list[str] | None = None,
    ) -> Iterator[dict]:
        """Run a command and stream logs.

        Args:
            command: Command to run
            bundle: Base64-encoded zip bundle
            env_vars: Environment variables
            editables: List of editable package names (for PYTHONPATH)

        Yields events:
            {"job_id": "..."} - First event with job ID
            {"log": "..."} - Log line
            {"status": "completed"|"failed", "exit_code": int} - Final status
            {"error": "..."} - Error message
        """
        merged_env = {**self.config.env, **(env_vars or {})}

        payload = {
            "command": command,
            "bundle": bundle,
            "env_vars": merged_env,
            "editables": editables or [],
        }

        if DEBUG:
            print(f"[DEBUG] Payload size: {len(json.dumps(payload))} bytes")
            print(f"[DEBUG] Bundle size: {len(bundle)} chars ({len(bundle) * 3 // 4 // 1024} KB)")

        t0 = time.time()
        with self._client.stream(
            "POST",
            "/run",
            json=payload,
            headers={**self._headers(), "Accept": "text/event-stream"},
            timeout=None,
        ) as response:
            if DEBUG:
                print(f"[DEBUG] Response received in {time.time() - t0:.2f}s, status={response.status_code}")
            response.raise_for_status()

            buffer = ""
            first_event = True
            for chunk in response.iter_text():
                if first_event and DEBUG:
                    print(f"[DEBUG] First chunk received in {time.time() - t0:.2f}s")
                    first_event = False
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            return
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            pass

    def list_jobs(self, limit: int = 50) -> list[dict]:
        """List recent jobs."""
        response = self._client.get("/jobs", params={"limit": limit}, headers=self._headers())
        response.raise_for_status()
        return response.json().get("jobs", [])

    def get_job(self, job_id: str) -> dict:
        """Get job status."""
        response = self._client.get(f"/jobs/{job_id}", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def stop_job(self, job_id: str) -> bool:
        """Stop a running job."""
        response = self._client.delete(f"/jobs/{job_id}", headers=self._headers())
        response.raise_for_status()
        return response.json().get("stopped", False)

    def get_logs(self, job_id: str) -> str:
        """Get job logs."""
        response = self._client.get(f"/jobs/{job_id}/logs", headers=self._headers())
        response.raise_for_status()
        return response.text

    def get_usage(self) -> dict:
        """Get current month's usage stats."""
        response = self._client.get("/usage", headers=self._headers())
        response.raise_for_status()
        return response.json()
