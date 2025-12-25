"""
Proto Generation Information

This file contains information about when and how the proto bindings were generated.
Generated automatically by scripts/generate_proto.py
"""

import subprocess

# Source repository information
PROTO_REPOSITORY = "https://github.com/ehsaniara/joblet-proto"
PROTO_COMMIT_HASH = "208aa454b8b55bb4a7eab554c93251a9b5d46467"
PROTO_TAG = "v2.5.4"
GENERATION_TIMESTAMP = (
    "Wed Dec 10 03:24:19 AM UTC 2025"
)

# Protocol buffer compiler version
try:
    PROTOC_VERSION = subprocess.run(
        ["protoc", "--version"], capture_output=True, text=True
    ).stdout.strip()
except Exception:
    PROTOC_VERSION = "unknown"

# Python grpcio-tools version
GRPCIO_TOOLS_VERSION = "1.75.1"
