"""DEPRECATED: old SDK CLI module path.

The SDK import name is now `qcos_sdk` and its CLI entrypoint is `qcos-sdk`.

Use:
  - `qcos-sdk ...` (SDK client CLI)
  - `qcos ...` (core/optimizer CLI)
"""

import sys

raise ImportError(
    "Deprecated: use the `qcos_sdk` package and the `qcos-sdk` CLI entrypoint."
)
