"""HTTP client for tup worker API."""

import json
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

from .config import TupConfig, load_config
from .types import JobStatus


@dataclass
class JobResponse:
    """Response from job creation."""

    job_id: str
    status: str
    message: str | None = None


class TupClient:
    """Client for the tup worker API."""

    def __init__(self, config: TupConfig | None = None):
        self.config = config or load_config()
        # api_url defaults to https://tup.prava.dev if not overridden
        self._client = httpx.Client(
            base_url=self.config.api_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "TupClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers

    # -------------------------------------------------------------------------
    # Job Management
    # -------------------------------------------------------------------------

    def create_command_job(
        self,
        command: str,
        bundle: str,  # base64 encoded
        name: str | None = None,
        instance_type: str = "standard-1",
        env_vars: dict[str, str] | None = None,
        timeout: str | None = None,
    ) -> JobResponse:
        """Create a job that runs a shell command.

        Args:
            command: Shell command to run (e.g., "uv run python train.py")
            bundle: Base64-encoded zip of the code directory
            name: Optional job name
            instance_type: Container instance type
            env_vars: Environment variables to inject
            timeout: Max runtime (e.g., "2h", "1d")

        Returns:
            JobResponse with job_id and status
        """
        # Merge config env vars with provided env vars
        merged_env = {**self.config.env, **(env_vars or {})}

        payload = {
            "type": "command",
            "command": command,
            "bundle": bundle,
            "name": name,
            "instance_type": instance_type,
            "env_vars": merged_env,
            "timeout": timeout,
        }

        response = self._client.post("/jobs", json=payload, headers=self._headers())
        response.raise_for_status()
        data = response.json()
        return JobResponse(
            job_id=data["job_id"],
            status=data["status"],
            message=data.get("message"),
        )

    def create_swarm_jobs(
        self,
        sweep_name: str,
        jobs: list[dict[str, Any]],  # [{"config": base64, "log_relpath": str}]
        bundle: str,  # base64 encoded
        instance_type: str = "standard-1",
        env_vars: dict[str, str] | None = None,
        max_concurrent: int = 10,
    ) -> list[JobResponse]:
        """Create multiple jobs for a swarm/sweep.

        Args:
            sweep_name: Name for the sweep
            jobs: List of job configs (pickled JobConfig as base64)
            bundle: Base64-encoded zip of the code directory
            instance_type: Container instance type
            env_vars: Environment variables to inject
            max_concurrent: Max concurrent containers

        Returns:
            List of JobResponse for each job
        """
        merged_env = {**self.config.env, **(env_vars or {})}

        payload = {
            "type": "swarm",
            "sweep_name": sweep_name,
            "jobs": jobs,
            "bundle": bundle,
            "instance_type": instance_type,
            "env_vars": merged_env,
            "max_concurrent": max_concurrent,
        }

        response = self._client.post("/jobs", json=payload, headers=self._headers())
        response.raise_for_status()
        data = response.json()

        return [
            JobResponse(job_id=j["job_id"], status=j["status"], message=j.get("message"))
            for j in data["jobs"]
        ]

    def get_job(self, job_id: str) -> JobStatus:
        """Get status of a job."""
        response = self._client.get(f"/jobs/{job_id}", headers=self._headers())
        response.raise_for_status()
        return JobStatus(**response.json())

    def list_jobs(self, limit: int = 50) -> list[JobStatus]:
        """List recent jobs."""
        response = self._client.get(
            "/jobs", params={"limit": limit}, headers=self._headers()
        )
        response.raise_for_status()
        return [JobStatus(**j) for j in response.json()["jobs"]]

    def stop_job(self, job_id: str) -> bool:
        """Stop a running job."""
        response = self._client.delete(f"/jobs/{job_id}", headers=self._headers())
        response.raise_for_status()
        return response.json().get("stopped", False)

    def get_latest_job_id(self) -> str | None:
        """Get the ID of the most recent job."""
        jobs = self.list_jobs(limit=1)
        return jobs[0].job_id if jobs else None

    # -------------------------------------------------------------------------
    # Log Streaming
    # -------------------------------------------------------------------------

    def stream_logs(self, job_id: str) -> Iterator[str]:
        """Stream logs from a job via Server-Sent Events.

        Yields log lines as they arrive. Blocks until job completes.
        """
        with self._client.stream(
            "GET",
            f"/jobs/{job_id}/logs",
            headers={**self._headers(), "Accept": "text/event-stream"},
            timeout=None,  # No timeout for streaming
        ) as response:
            response.raise_for_status()

            buffer = ""
            for chunk in response.iter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.startswith("data: "):
                        data = line[6:]  # Strip "data: " prefix
                        if data == "[DONE]":
                            return
                        try:
                            parsed = json.loads(data)
                            if "line" in parsed:
                                yield parsed["line"]
                            elif "error" in parsed:
                                yield f"[ERROR] {parsed['error']}"
                            elif "status" in parsed:
                                yield f"[STATUS] {parsed['status']}"
                        except json.JSONDecodeError:
                            # Plain text log line
                            yield data

    def get_logs(self, job_id: str) -> str:
        """Get all logs for a job (non-streaming)."""
        response = self._client.get(
            f"/jobs/{job_id}/logs",
            headers={**self._headers(), "Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json().get("logs", "")
