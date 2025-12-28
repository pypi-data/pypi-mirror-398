from __future__ import annotations
from pathlib import Path
import subprocess
import re

from core.config import CodegenConfig, ProtoSource
from utils import expand_path

LATEST_TAG = "latest-tag"


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True, capture_output=True, text=True)
    return result.stdout


def _parse_semver(tag: str) -> tuple[int, int, int, str] | None:
    """
    Parse a semver-like tag into a comparable tuple.
    Supports formats: v1.2.3, 1.2.3, v1.2.3-beta, etc.
    Returns (major, minor, patch, suffix) or None if not a valid semver.
    """
    # Remove leading 'v' if present
    version = tag.lstrip('v')

    # Match semver pattern: major.minor.patch with optional suffix
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(.*)$', version)
    if not match:
        return None

    major, minor, patch, suffix = match.groups()
    return (int(major), int(minor), int(patch), suffix)


def _get_latest_semver_tag(dst: Path) -> str:
    """
    Get all tags from the repo and return the latest one by semver.
    Raises RuntimeError if no valid semver tags are found.
    """
    output = _run(["git", "tag", "--list"], cwd=dst)
    tags = [t.strip() for t in output.strip().split('\n') if t.strip()]

    if not tags:
        raise RuntimeError("No tags found in repository")

    # Parse and filter valid semver tags
    semver_tags = []
    for tag in tags:
        parsed = _parse_semver(tag)
        if parsed:
            # Sort by (major, minor, patch), prefer no suffix over suffix
            # Empty suffix sorts after non-empty (we want stable releases first)
            sort_key = (parsed[0], parsed[1], parsed[2], parsed[3] == '', parsed[3])
            semver_tags.append((sort_key, tag))

    if not semver_tags:
        raise RuntimeError(f"No valid semver tags found. Available tags: {', '.join(tags)}")

    # Sort by semver and get the latest
    semver_tags.sort(reverse=True)
    latest_tag = semver_tags[0][1]

    return latest_tag


def ensure_git_checkout(repo_url: str, ref: str, dst: Path) -> str:
    """
    Ensure git repo is cloned and checked out to the specified ref.
    If ref is "latest-tag", resolves to the latest semver tag.
    Returns the actual ref that was checked out.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        _run(["git", "clone", repo_url, str(dst)])
    _run(["git", "fetch", "--all", "--tags"], cwd=dst)

    actual_ref = ref
    if ref == LATEST_TAG:
        actual_ref = _get_latest_semver_tag(dst)

    _run(["git", "checkout", "--force", actual_ref], cwd=dst)
    return actual_ref

def resolve_proto_root(cfg: CodegenConfig, *, use_local: bool = False) -> Path:
    """
    Resolve the proto root directory.

    Supports environment variables ($VAR, ${VAR}) and ~ in paths.

    When use_local=True (--local flag):
        Uses proto.root from config (local filesystem path)

    When use_local=False (default):
        Uses proto.source.git to clone/fetch from git repository
        Falls back to proto.root if no git source is configured
    """
    if use_local:
        # --local flag: use local proto.root
        if cfg.proto.root and cfg.proto.root != "":
            p = expand_path(cfg.proto.root).resolve()
            if p.exists():
                return p
            raise RuntimeError(f"proto.root path does not exist: {cfg.proto.root} (resolved to: {p})")
        raise RuntimeError("--local flag requires proto.root to be configured")

    # Default: use git source
    if cfg.proto.source:
        src = cfg.proto.source
        git_url = src.git
        ref = src.ref or LATEST_TAG  # Default to latest-tag if not specified
        if git_url:
            cache_dir = expand_path(cfg.proto.cache_dir).resolve()
            ensure_git_checkout(git_url, ref, cache_dir)
            return cache_dir

    # Fallback to local root if no git source configured
    if cfg.proto.root and cfg.proto.root != "":
        p = expand_path(cfg.proto.root).resolve()
        if p.exists():
            return p

    raise RuntimeError("No proto.source.git configured and proto.root not found")
