"""QCOS SDK - Softquantus Quantum Circuit Optimization Service.

This SDK is the HTTP client for the public QCOS API gateway.

IMPORTANT (monorepo): this repository also contains a different package named
`qcos` (core/CLI). To avoid import collisions, the SDK import name is
`qcos_sdk`.

Example:
    >>> from qcos_sdk import QCOSClient
    >>> client = QCOSClient(api_key="your-api-key")
    >>> result = client.execute(qasm="...", shots=1024)
    >>> print(result.counts)
    {'00': 512, '11': 512}
"""

from qcos_sdk.client import AsyncQCOSClient, QCOSClient
from qcos_sdk.models import (
    AuthenticationError,
    CircuitJob,
    JobResult,
    JobStatus,
    QCOSError,
    RateLimitError,
    ValidationError,
    ProviderInfo,
    BackendInfo,
    SupplierInfo,
)

__version__ = "2.1.0"
__author__ = "Softquantus"
__email__ = "info@softquantus.com"

__all__ = [
    "QCOSClient",
    "AsyncQCOSClient",
    "JobResult",
    "JobStatus",
    "CircuitJob",
    "QCOSError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "ProviderInfo",
    "BackendInfo",
    "SupplierInfo",
    "__version__",
]
