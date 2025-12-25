from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Union

import httpx

from qcos_sdk.models import (
    CircuitJob,
    JobResult,
    JobStatus,
    QCOSError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    JobNotFoundError,
    TimeoutError,
    SupplierInfo,
    ProviderInfo,
    BackendInfo,
)


class QCOSClient:
    """Synchronous QCOS API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://qcos-api.softquantus.com",
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        api_key = api_key or os.getenv("QCOS_API_KEY")
        if not api_key:
            raise AuthenticationError("QCOS API key required (pass api_key or set QCOS_API_KEY)")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.Client(
            timeout=timeout,
            headers={"X-API-Key": api_key, "Authorization": f"Bearer {api_key}"},
        )

    def execute(self, qasm: str, shots: int = 1024) -> JobResult:
        """Submit a circuit and wait for completion."""
        job = self.submit(qasm=qasm, shots=shots)
        return self.wait_for_result(job.job_id)

    def submit(self, qasm: str, shots: int = 1024) -> CircuitJob:
        """Submit a circuit for execution and return a job handle."""
        if not qasm or not isinstance(qasm, str):
            raise ValidationError("qasm must be a non-empty string")
        if shots <= 0:
            raise ValidationError("shots must be > 0")

        url = f"{self.base_url}/execute"
        resp = self._request_with_retries("POST", url, json={"qasm": qasm, "shots": shots})
        data = resp.json()
        if "job_id" not in data:
            raise QCOSError(f"Unexpected response: {data}")
        return CircuitJob(job_id=data["job_id"], status=data.get("status", JobStatus.PENDING))

    def get_status(self, job_id: str) -> JobResult:
        url = f"{self.base_url}/status/{job_id}"
        resp = self._request_with_retries("GET", url)
        return JobResult.from_dict(resp.json())

    def get_result(self, job_id: str) -> JobResult:
        url = f"{self.base_url}/results/{job_id}"
        resp = self._request_with_retries("GET", url)
        return JobResult.from_dict(resp.json())

    def wait_for_result(self, job_id: str, timeout: float = 300.0, poll_interval: float = 2.0) -> JobResult:
        start = time.time()
        last: Optional[JobResult] = None

        while True:
            if time.time() - start > timeout:
                raise TimeoutError(f"Timed out waiting for job {job_id}")

            last = self.get_status(job_id)
            if last.is_complete:
                # If status endpoint doesn't include counts, fall back to results endpoint.
                if last.counts is None and last.status == JobStatus.COMPLETED:
                    try:
                        return self.get_result(job_id)
                    except Exception:
                        return last
                return last

            time.sleep(poll_interval)

    def list_providers(self, supplier: str = "azure_quantum") -> list[ProviderInfo]:
        """List available providers for a supplier.
        
        Args:
            supplier: One of 'azure_quantum', 'ibm_quantum', 'braket'
        
        Returns:
            List of provider information
        """
        url = f"{self.base_url}/api/v1/{supplier}/providers"
        if supplier == "ibm_quantum":
            url = f"{self.base_url}/api/v1/ibm_quantum/backends"
        elif supplier == "braket":
            url = f"{self.base_url}/api/v1/braket/devices"
            
        resp = self._request_with_retries("GET", url)
        data = resp.json()
        
        # Parse response based on supplier
        if supplier == "azure_quantum":
            return [ProviderInfo.from_dict(p) for p in data]
        elif supplier == "ibm_quantum":
            return [ProviderInfo.from_dict({"id": b["backend_name"], "name": b["backend_name"], 
                                            "type": b.get("backend_type", "simulator"),
                                            "num_qubits": b.get("num_qubits", 0)}) 
                    for b in data.get("backends", [])]
        elif supplier == "braket":
            return [ProviderInfo.from_dict({"id": d["name"], "name": d["name"],
                                            "type": d.get("type", "simulator"),
                                            "num_qubits": d.get("num_qubits", 0)})
                    for d in data.get("devices", [])]
        return []

    def execute_on_backend(self, qasm: str, backend: str, supplier: str = "azure_quantum", 
                          shots: int = 1024) -> JobResult:
        """Execute circuit on specific backend.
        
        Args:
            qasm: OpenQASM 2.0 circuit
            backend: Backend name (e.g., 'ionq.simulator', 'ibm_kyoto', 'sv1')
            supplier: Supplier name ('azure_quantum', 'ibm_quantum', 'braket')
            shots: Number of shots
            
        Returns:
            Job result
        """
        url = f"{self.base_url}/api/v1/{supplier}/execute"
        payload = {"circuit": qasm, "shots": shots}
        
        if supplier == "azure_quantum":
            payload["target"] = backend
        elif supplier == "ibm_quantum":
            payload["backend"] = backend
        elif supplier == "braket":
            payload["device"] = backend
            
        resp = self._request_with_retries("POST", url, json=payload)
        data = resp.json()
        job_id = data.get("job_id") or data.get("task_id")
        
        return self.wait_for_result(job_id, timeout=self.timeout)

    def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._client.request(method, url, **kwargs)
                if resp.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                if resp.status_code == 404:
                    raise JobNotFoundError("Job not found")
                if resp.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise QCOSError(f"Request failed after retries: {e}")
                time.sleep(0.5 * (2**attempt))
            except httpx.HTTPStatusError as e:
                raise QCOSError(f"HTTP error: {e.response.status_code} {e.response.text}")

        raise QCOSError(f"Request failed: {last_exc}")


class AsyncQCOSClient:
    """Asynchronous QCOS API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://qcos-api.softquantus.com",
        timeout: float = 300.0,
        max_retries: int = 3,
    ):
        api_key = api_key or os.getenv("QCOS_API_KEY")
        if not api_key:
            raise AuthenticationError("QCOS API key required (pass api_key or set QCOS_API_KEY)")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"X-API-Key": api_key, "Authorization": f"Bearer {api_key}"},
        )

    async def submit(self, qasm: str, shots: int = 1024) -> CircuitJob:
        if not qasm or not isinstance(qasm, str):
            raise ValidationError("qasm must be a non-empty string")
        if shots <= 0:
            raise ValidationError("shots must be > 0")

        url = f"{self.base_url}/execute"
        resp = await self._request_with_retries("POST", url, json={"qasm": qasm, "shots": shots})
        data = resp.json()
        if "job_id" not in data:
            raise QCOSError(f"Unexpected response: {data}")
        return CircuitJob(job_id=data["job_id"], status=data.get("status", JobStatus.PENDING))

    async def get_status(self, job_id: str) -> JobResult:
        url = f"{self.base_url}/status/{job_id}"
        resp = await self._request_with_retries("GET", url)
        return JobResult.from_dict(resp.json())

    async def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await self._client.request(method, url, **kwargs)
                if resp.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                if resp.status_code == 404:
                    raise JobNotFoundError("Job not found")
                if resp.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                resp.raise_for_status()
                return resp
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_exc = e
                if attempt >= self.max_retries:
                    raise QCOSError(f"Request failed after retries: {e}")
                await self._sleep(0.5 * (2**attempt))
            except httpx.HTTPStatusError as e:
                raise QCOSError(f"HTTP error: {e.response.status_code} {e.response.text}")

        raise QCOSError(f"Request failed: {last_exc}")

    async def _sleep(self, seconds: float) -> None:
        import asyncio

        await asyncio.sleep(seconds)
