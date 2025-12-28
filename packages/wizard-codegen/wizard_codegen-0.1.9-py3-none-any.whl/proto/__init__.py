"""
Protobuf handling functionality.

Handles proto file discovery, descriptor set building, and proto source resolution.
"""

from .discover import discover_proto_files
from .fds_loader import load_fds, print_fds_content
from .proto_source import resolve_proto_root, ensure_git_checkout, LATEST_TAG
from .protoc_runner import build_descriptor_set

__all__ = [
    "discover_proto_files",
    "load_fds",
    "print_fds_content",
    "resolve_proto_root",
    "ensure_git_checkout",
    "build_descriptor_set",
]
