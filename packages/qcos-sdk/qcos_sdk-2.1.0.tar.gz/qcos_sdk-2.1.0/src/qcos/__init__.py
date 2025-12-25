"""DEPRECATED: old QCOS SDK import namespace.

The SDK import name is now `qcos_sdk` to avoid collisions with the QCOS
core/CLI package (`qcos`) in this monorepo.

Update code to:

    from qcos_sdk import QCOSClient
"""

raise ImportError(
    "QCOS SDK has moved: use 'qcos_sdk' (e.g. 'from qcos_sdk import QCOSClient')."
)
