from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QCOSError(RuntimeError):
    pass


class AuthenticationError(QCOSError):
    pass


class RateLimitError(QCOSError):
    pass


class ValidationError(QCOSError):
    pass


class JobNotFoundError(QCOSError):
    pass


class TimeoutError(QCOSError):
    pass


@dataclass
class CircuitJob:
    job_id: str
    status: JobStatus | str = JobStatus.PENDING


@dataclass
class ProviderInfo:
    """Information about a quantum provider."""
    id: str
    name: str
    type: str = "simulator"
    num_qubits: int = 0
    available: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProviderInfo:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", "simulator"),
            num_qubits=data.get("num_qubits", 0),
            available=data.get("available", True)
        )


@dataclass
class BackendInfo:
    """Information about a quantum backend."""
    backend_name: str
    num_qubits: int
    backend_type: str = "simulator"
    available: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BackendInfo:
        return cls(
            backend_name=data.get("backend_name", ""),
            num_qubits=data.get("num_qubits", 0),
            backend_type=data.get("backend_type", "simulator"),
            available=data.get("available", True)
        )


@dataclass
class SupplierInfo:
    """Information about a quantum supplier."""
    id: str
    name: str
    enabled: bool = True
    num_providers: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SupplierInfo:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            num_providers=data.get("num_providers", 0)
        )


@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    counts: Optional[Dict[str, int]] = None
    num_qubits: Optional[int] = None
    shots: Optional[int] = None
    backend: Optional[str] = None
    error: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    @property
    def is_complete(self) -> bool:
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    @property
    def is_successful(self) -> bool:
        return self.status == JobStatus.COMPLETED and not self.error

    def get_probabilities(self) -> Dict[str, float]:
        if not self.counts:
            return {}
        total = sum(self.counts.values()) or 1
        return {k: v / total for k, v in self.counts.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobResult":
        status_raw = (data.get("status") or "pending").lower()
        try:
            status = JobStatus(status_raw)
        except Exception:
            status = JobStatus.PENDING

        # Support either {result:{counts,...}} or top-level counts
        result_block = data.get("result") if isinstance(data.get("result"), dict) else {}
        counts = data.get("counts") or result_block.get("counts")

        return cls(
            job_id=data.get("job_id") or "",
            status=status,
            counts=counts,
            num_qubits=result_block.get("num_qubits") or data.get("num_qubits"),
            shots=result_block.get("shots") or data.get("shots"),
            backend=result_block.get("backend") or data.get("backend"),
            error=data.get("error") or result_block.get("error"),
            raw=data,
        )
