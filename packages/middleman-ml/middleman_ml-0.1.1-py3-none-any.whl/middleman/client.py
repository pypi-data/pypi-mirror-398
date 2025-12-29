"""Middleman API client."""

import os
import time
from typing import Optional, Iterator
from pathlib import Path

import httpx

from .models import (
    Job,
    JobDetail,
    JobCreateRequest,
    JobCreateResponse,
    JobStatus,
    GpuType,
    Framework,
    CreditBalance,
    CreditPackage,
    ApiKey,
    UploadUrl,
    DownloadUrl,
)


class MiddlemanError(Exception):
    """Base exception for Middleman SDK."""
    pass


class AuthenticationError(MiddlemanError):
    """Authentication failed."""
    pass


class ApiError(MiddlemanError):
    """API request failed."""
    def __init__(self, message: str, status_code: int, detail: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class MiddlemanClient:
    """
    Client for interacting with the Middleman ML Training Platform API.

    Usage:
        >>> from middleman import MiddlemanClient
        >>> client = MiddlemanClient(api_key="mdlm_...")
        >>> job = client.create_job(
        ...     name="My Training Job",
        ...     gpu_type="t4",
        ...     script_path="/scripts/train.py",
        ...     input_data_path="/data/dataset"
        ... )
        >>> print(f"Job {job.id} created, queue position: {job.queue_position}")
    """

    DEFAULT_BASE_URL = "https://api.middleman.run/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Middleman client.

        Args:
            api_key: Your Middleman API key. If not provided, reads from
                     MIDDLEMAN_API_KEY environment variable.
            base_url: API base URL. Defaults to production API.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("MIDDLEMAN_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Pass api_key parameter or set MIDDLEMAN_API_KEY env var."
            )

        self.base_url = (base_url or os.environ.get("MIDDLEMAN_API_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "middleman-python/0.1.0",
            },
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an API request."""
        response = self._client.request(method, path, json=json, params=params)

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code >= 400:
            try:
                error_detail = response.json().get("detail", response.text)
            except Exception:
                error_detail = response.text
            raise ApiError(
                f"API request failed: {error_detail}",
                status_code=response.status_code,
                detail=error_detail,
            )

        if response.status_code == 204:
            return {}

        return response.json()

    # === Jobs API ===

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        """
        List your training jobs.

        Args:
            status: Filter by job status
            limit: Maximum number of jobs to return (1-100)
            offset: Pagination offset

        Returns:
            Tuple of (jobs list, total count)
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status.value if isinstance(status, JobStatus) else status

        data = self._request("GET", "/jobs", params=params)
        jobs = [Job(**job) for job in data.get("data", [])]
        return jobs, data.get("total", len(jobs))

    def get_job(self, job_id: str) -> JobDetail:
        """
        Get detailed information about a job.

        Args:
            job_id: The job UUID

        Returns:
            JobDetail with full job information
        """
        data = self._request("GET", f"/jobs/{job_id}")
        return JobDetail(**data)

    def create_job(
        self,
        script_path: str,
        input_data_path: str,
        name: Optional[str] = None,
        gpu_type: GpuType | str = GpuType.T4,
        gpu_count: int = 1,
        framework: Framework | str = Framework.PYTORCH,
        requirements_file: Optional[str] = None,
        checkpoint_frequency: int = 10,
        max_runtime_hours: int = 4,
        environment_variables: Optional[dict] = None,
    ) -> JobCreateResponse:
        """
        Create a new training job.

        Args:
            script_path: Path to your training script on the VM
            input_data_path: Path to input data on the VM
            name: Optional job name for identification
            gpu_type: GPU type (t4, v100, a100)
            gpu_count: Number of GPUs (1-8)
            framework: ML framework (pytorch, tensorflow, jax)
            requirements_file: Path to requirements.txt
            checkpoint_frequency: Save checkpoint every N epochs
            max_runtime_hours: Maximum runtime (1-72 hours)
            environment_variables: Environment variables for the job

        Returns:
            JobCreateResponse with job ID, estimated cost, queue position
        """
        request = JobCreateRequest(
            name=name,
            gpu_type=GpuType(gpu_type) if isinstance(gpu_type, str) else gpu_type,
            gpu_count=gpu_count,
            framework=Framework(framework) if isinstance(framework, str) else framework,
            script_path=script_path,
            input_data_path=input_data_path,
            requirements_file=requirements_file,
            checkpoint_frequency=checkpoint_frequency,
            max_runtime_hours=max_runtime_hours,
            environment_variables=environment_variables or {},
        )

        data = self._request("POST", "/jobs", json=request.model_dump(exclude_none=True))
        return JobCreateResponse(**data)

    def cancel_job(self, job_id: str) -> dict:
        """
        Cancel a job and get credits refunded.

        Args:
            job_id: The job UUID

        Returns:
            Dict with job status and refunded credits
        """
        return self._request("POST", f"/jobs/{job_id}/cancel")

    def pause_job(self, job_id: str) -> Job:
        """
        Pause a running job.

        Args:
            job_id: The job UUID

        Returns:
            Updated Job with paused status
        """
        data = self._request("POST", f"/jobs/{job_id}/pause")
        return Job(**data)

    def resume_job(self, job_id: str) -> Job:
        """
        Resume a paused job.

        Args:
            job_id: The job UUID

        Returns:
            Updated Job with resuming status
        """
        data = self._request("POST", f"/jobs/{job_id}/resume")
        return Job(**data)

    def get_job_logs(
        self,
        job_id: str,
        since: Optional[str] = None,
    ) -> list[dict]:
        """
        Get job logs.

        Args:
            job_id: The job UUID
            since: Get logs after this ISO timestamp

        Returns:
            List of log entries
        """
        params = {}
        if since:
            params["since"] = since
        return self._request("GET", f"/jobs/{job_id}/logs", params=params)

    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 10.0,
        timeout: Optional[float] = None,
    ) -> JobDetail:
        """
        Wait for a job to complete.

        Args:
            job_id: The job UUID
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait (None for unlimited)

        Returns:
            Final JobDetail when job reaches terminal state

        Raises:
            TimeoutError: If timeout is reached before job completes
        """
        start_time = time.time()
        while True:
            job = self.get_job(job_id)
            if job.is_terminal:
                return job

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

            time.sleep(poll_interval)

    def stream_job_status(
        self,
        job_id: str,
        poll_interval: float = 5.0,
    ) -> Iterator[JobDetail]:
        """
        Stream job status updates until completion.

        Args:
            job_id: The job UUID
            poll_interval: Seconds between status checks

        Yields:
            JobDetail on each status check
        """
        while True:
            job = self.get_job(job_id)
            yield job
            if job.is_terminal:
                break
            time.sleep(poll_interval)

    # === Billing API ===

    def get_balance(self) -> CreditBalance:
        """
        Get your current credit balance.

        Returns:
            CreditBalance with balance, reserved, and available credits
        """
        data = self._request("GET", "/billing/balance")
        return CreditBalance(**data)

    def get_packages(self) -> list[CreditPackage]:
        """
        Get available credit packages.

        Returns:
            List of purchasable credit packages
        """
        data = self._request("GET", "/billing/packages")
        return [CreditPackage(**pkg) for pkg in data.get("packages", [])]

    def get_transactions(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Get credit transaction history.

        Args:
            limit: Maximum transactions to return
            offset: Pagination offset

        Returns:
            Tuple of (transactions list, total count)
        """
        params = {"limit": limit, "offset": offset}
        data = self._request("GET", "/billing/transactions", params=params)
        return data.get("data", []), data.get("total", 0)

    # === Data API ===

    def get_upload_url(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        job_id: Optional[str] = None,
    ) -> UploadUrl:
        """
        Get a presigned URL for uploading data.

        Args:
            filename: Name of the file to upload
            content_type: MIME type of the file
            size_bytes: File size in bytes
            job_id: Optional job ID to associate the upload with

        Returns:
            UploadUrl with presigned URL and blob path
        """
        params = {}
        if job_id:
            params["job_id"] = job_id

        data = self._request(
            "POST",
            "/data/upload-url",
            json={
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
            },
            params=params,
        )
        return UploadUrl(**data)

    def get_download_url(
        self,
        job_id: str,
        path: Optional[str] = None,
    ) -> DownloadUrl:
        """
        Get a presigned URL for downloading results.

        Args:
            job_id: The job UUID
            path: Optional specific file path within job outputs

        Returns:
            DownloadUrl with presigned URL
        """
        data = self._request(
            "POST",
            "/data/download-url",
            json={"job_id": job_id, "path": path},
        )
        return DownloadUrl(**data)

    def upload_file(
        self,
        local_path: str | Path,
        job_id: Optional[str] = None,
    ) -> str:
        """
        Upload a file to Middleman storage.

        Args:
            local_path: Path to local file
            job_id: Optional job ID to associate with

        Returns:
            Blob path where file was uploaded
        """
        path = Path(local_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        size = path.stat().st_size
        content_type = self._guess_content_type(path.name)

        upload = self.get_upload_url(
            filename=path.name,
            content_type=content_type,
            size_bytes=size,
            job_id=job_id,
        )

        # Upload to presigned URL
        with open(path, "rb") as f:
            response = httpx.put(
                upload.upload_url,
                content=f,
                headers={"Content-Type": content_type},
            )
            response.raise_for_status()

        return upload.blob_path

    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        content_types = {
            "py": "text/x-python",
            "txt": "text/plain",
            "json": "application/json",
            "yaml": "application/x-yaml",
            "yml": "application/x-yaml",
            "zip": "application/zip",
            "tar": "application/x-tar",
            "gz": "application/gzip",
            "pt": "application/octet-stream",
            "pth": "application/octet-stream",
            "h5": "application/x-hdf5",
            "pkl": "application/octet-stream",
            "csv": "text/csv",
        }
        return content_types.get(ext, "application/octet-stream")

    # === API Keys ===

    def list_api_keys(self) -> list[ApiKey]:
        """
        List your API keys.

        Returns:
            List of API keys (without the full key value)
        """
        data = self._request("GET", "/api-keys")
        return [ApiKey(**key) for key in data]

    def create_api_key(
        self,
        name: str,
        scopes: Optional[list[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple[ApiKey, str]:
        """
        Create a new API key.

        Args:
            name: Name for the API key
            scopes: Permissions (default: ["read", "write"])
            expires_in_days: Days until expiration (None for never)

        Returns:
            Tuple of (ApiKey info, full key string)
            Note: The full key is only returned once!
        """
        data = self._request(
            "POST",
            "/api-keys",
            json={
                "name": name,
                "scopes": scopes or ["read", "write"],
                "expires_in_days": expires_in_days,
            },
        )
        full_key = data.pop("key")
        return ApiKey(**data), full_key

    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: The API key UUID

        Returns:
            True if successfully revoked
        """
        data = self._request("DELETE", f"/api-keys/{key_id}")
        return data.get("revoked", False)

    # === Webhooks API ===

    def list_webhooks(self) -> list[dict]:
        """
        List your webhooks.

        Returns:
            List of webhooks
        """
        return self._request("GET", "/webhooks")

    def get_webhook(self, webhook_id: str) -> dict:
        """
        Get a specific webhook.

        Args:
            webhook_id: The webhook UUID

        Returns:
            Webhook details
        """
        return self._request("GET", f"/webhooks/{webhook_id}")

    def create_webhook(
        self,
        name: str,
        url: str,
        events: list[str],
    ) -> dict:
        """
        Create a new webhook.

        Args:
            name: Name for the webhook
            url: Endpoint URL to receive events
            events: List of event types to subscribe to
                   Use "*" to subscribe to all events.
                   Available events:
                   - job.queued, job.started, job.running
                   - job.paused, job.resumed, job.checkpointing
                   - job.evicted, job.completed, job.failed, job.cancelled
                   - credits.low, credits.depleted

        Returns:
            Webhook info including the signing secret (only shown once!)
        """
        return self._request(
            "POST",
            "/webhooks",
            json={
                "name": name,
                "url": url,
                "events": events,
            },
        )

    def update_webhook(
        self,
        webhook_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        """
        Update a webhook.

        Args:
            webhook_id: The webhook UUID
            name: New name
            url: New endpoint URL
            events: New event subscriptions
            is_active: Enable/disable the webhook

        Returns:
            Updated webhook info
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if url is not None:
            payload["url"] = url
        if events is not None:
            payload["events"] = events
        if is_active is not None:
            payload["is_active"] = is_active

        return self._request("PATCH", f"/webhooks/{webhook_id}", json=payload)

    def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook.

        Args:
            webhook_id: The webhook UUID
        """
        self._request("DELETE", f"/webhooks/{webhook_id}")

    def regenerate_webhook_secret(self, webhook_id: str) -> str:
        """
        Regenerate the webhook signing secret.

        Args:
            webhook_id: The webhook UUID

        Returns:
            New signing secret
        """
        data = self._request("POST", f"/webhooks/{webhook_id}/regenerate-secret")
        return data["secret"]

    def test_webhook(self, webhook_id: str) -> dict:
        """
        Send a test event to the webhook.

        Args:
            webhook_id: The webhook UUID

        Returns:
            Delivery result
        """
        return self._request("POST", f"/webhooks/{webhook_id}/test")

    def get_webhook_deliveries(
        self,
        webhook_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Get delivery history for a webhook.

        Args:
            webhook_id: The webhook UUID
            limit: Maximum deliveries to return
            offset: Pagination offset

        Returns:
            Tuple of (deliveries list, total count)
        """
        params = {"limit": limit, "offset": offset}
        data = self._request("GET", f"/webhooks/{webhook_id}/deliveries", params=params)
        return data.get("data", []), data.get("total", 0)

    def get_webhook_events(self) -> list[dict]:
        """
        Get list of available webhook events.

        Returns:
            List of events with descriptions
        """
        data = self._request("GET", "/webhooks/events")
        return data.get("events", [])

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
