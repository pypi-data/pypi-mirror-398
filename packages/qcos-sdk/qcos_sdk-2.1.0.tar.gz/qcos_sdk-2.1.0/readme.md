# QCOS SDK - Softquantus Quantum Computing Platform

[![PyPI version](https://badge.fury.io/py/qcos-sdk.svg)](https://badge.fury.io/py/qcos-sdk)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [Softquantus QCOS](https://docs.softquantus.com) - Quantum Circuit Optimization Service.

## Installation

```bash
pip install qcos-sdk
```

## Quick Start

```python
from qcos_sdk import QCOSClient

# Initialize client
client = QCOSClient(api_key="your-api-key")

# Execute a Bell state circuit
result = client.execute(
    qasm="""
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0],q[1];
    measure q -> c;
    """,
    shots=1024
)

print(result.counts)
# {'00': 512, '11': 512}
```

## Features

- 🚀 **GPU-Accelerated**: Execute on NVIDIA A100 GPUs via LUMI supercomputer
- ⚡ **Up to 100 qubits**: Large-scale quantum circuit simulation
- 🔄 **Async Support**: Non-blocking execution for batch jobs
- 🔗 **Qiskit Integration**: Direct QuantumCircuit support
- 🔐 **Enterprise Security**: TLS 1.3, API key authentication

**API Endpoint**: `https://qcos-api.softquantus.com`

## Documentation

Full documentation available at [docs.softquantus.com](https://docs.softquantus.com)

## API Reference

### QCOSClient

```python
from qcos import QCOSClient

client = QCOSClient(
    api_key="your-api-key",           # Required
    base_url="https://api.softquantus.com",  # Optional
    timeout=300,                       # Request timeout in seconds
    max_retries=3                      # Retry failed requests
)
```

### Execute Circuit

```python
# From OpenQASM string
result = client.execute(qasm="...", shots=1024)

# From Qiskit QuantumCircuit
from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

result = client.execute(circuit=qc, shots=1024)
```

### Async Execution

```python
import asyncio
from qcos import AsyncQCOSClient

async def main():
    client = AsyncQCOSClient(api_key="your-api-key")
    
    # Submit multiple jobs
    jobs = await asyncio.gather(
        client.submit(qasm=circuit1, shots=1024),
        client.submit(qasm=circuit2, shots=1024),
        client.submit(qasm=circuit3, shots=1024),
    )
    
    # Wait for results
    results = await asyncio.gather(
        *[client.wait_for_result(job.job_id) for job in jobs]
    )
    
    for r in results:
        print(r.counts)

asyncio.run(main())
```

### Result Object

```python
result = client.execute(qasm="...", shots=1024)

result.job_id      # Unique job identifier
result.status      # 'completed', 'pending', 'failed'
result.counts      # {'00': 512, '11': 512}
result.num_qubits  # Number of qubits
result.shots       # Shots executed
result.backend     # Backend used (e.g., 'AerSimulator')
result.duration    # Execution time in seconds
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📧 Email: support@softquantus.com
- 📚 Docs: [docs.softquantus.com](https://docs.softquantus.com)
- 🐛 Issues: [GitHub Issues](https://github.com/roytmanpiccoli/qcos_core/issues)
