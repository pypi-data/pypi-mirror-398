"""Minimal CLI wrapper for the SDK.

This is intentionally named `qcos-sdk` as an entrypoint to avoid colliding
with the core CLI (`qcos`).
"""

from __future__ import annotations

import json
import sys

import typer

from qcos_sdk.client import QCOSClient


app = typer.Typer(add_completion=False, help="QCOS SDK CLI (client for QCOS public API)")


@app.command()
def execute(qasm_file: str, shots: int = 1024, base_url: str = "https://qcos-api.softquantus.com"):
    """Submit a QASM file and wait for counts."""
    with open(qasm_file, "r", encoding="utf-8") as f:
        qasm = f.read()

    client = QCOSClient(base_url=base_url)
    res = client.execute(qasm=qasm, shots=shots)
    print(json.dumps(res.raw or {}, indent=2, sort_keys=True))


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())
