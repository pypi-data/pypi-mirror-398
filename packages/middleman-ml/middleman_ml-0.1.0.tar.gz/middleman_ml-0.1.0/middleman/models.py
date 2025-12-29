"""Data models for Middleman SDK."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status values."""
    QUEUED = "queued"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTING = "checkpointing"
    EVICTED = "evicted"
    RESUMING = "resuming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class GpuType(str, Enum):
    """Available GPU types."""
    T4 = "t4"
    V100 = "v100"
    A100 = "a100"


class Framework(str, Enum):
    """Supported ML frameworks."""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    JAX = "jax"


class Job(BaseModel):
    """Training job model."""
    id: str
    name: Optional[str] = None
    status: JobStatus
    gpu_type: GpuType
    gpu_count: int = 1
    framework: Framework = Framework.PYTORCH
    current_epoch: int = 0
    total_epochs: Optional[int] = None
    current_loss: Optional[float] = None
    reserved_credits: int = 0
    actual_cost: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Check if job is currently active."""
        return self.status in [
            JobStatus.QUEUED,
            JobStatus.PROVISIONING,
            JobStatus.RUNNING,
            JobStatus.PAUSED,
            JobStatus.CHECKPOINTING,
            JobStatus.RESUMING,
        ]

    @property
    def is_terminal(self) -> bool:
        """Check if job has reached a terminal state."""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.CANCELLED,
            JobStatus.FAILED,
        ]


class JobDetail(Job):
    """Detailed job information."""
    script_path: str
    input_data_path: str
    requirements_file: Optional[str] = None
    checkpoint_frequency: int = 10
    max_runtime_hours: int = 4
    environment_variables: dict = Field(default_factory=dict)
    current_region: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class JobCreateRequest(BaseModel):
    """Request to create a new job."""
    name: Optional[str] = None
    gpu_type: GpuType = GpuType.T4
    gpu_count: int = Field(default=1, ge=1, le=8)
    framework: Framework = Framework.PYTORCH
    script_path: str
    input_data_path: str
    requirements_file: Optional[str] = None
    checkpoint_frequency: int = Field(default=10, ge=1)
    max_runtime_hours: int = Field(default=4, ge=1, le=72)
    environment_variables: dict = Field(default_factory=dict)


class JobCreateResponse(BaseModel):
    """Response after creating a job."""
    id: str
    name: Optional[str] = None
    status: JobStatus
    estimated_cost: int
    reserved_credits: int
    queue_position: int
    created_at: datetime


class CreditBalance(BaseModel):
    """Credit balance information."""
    balance: int
    reserved: int
    available: int
    expires_at: Optional[datetime] = None


class CreditPackage(BaseModel):
    """Credit package for purchase."""
    id: str
    name: str
    credits: int
    price_cents: int

    @property
    def price_dollars(self) -> float:
        """Get price in dollars."""
        return self.price_cents / 100


class ApiKey(BaseModel):
    """API key information."""
    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class UploadUrl(BaseModel):
    """Presigned upload URL."""
    upload_url: str
    blob_path: str
    expires_at: datetime


class DownloadUrl(BaseModel):
    """Presigned download URL."""
    download_url: str
    expires_at: datetime
    size_bytes: Optional[int] = None
