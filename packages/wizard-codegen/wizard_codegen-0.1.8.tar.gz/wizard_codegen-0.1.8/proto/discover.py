from __future__ import annotations

from pathlib import Path
import re

from core import CodegenConfig


_PROTO_ROOT_TOKEN = re.compile(r"\{\s*proto_root\s*\}")

def _resolve_include(proto_root: Path, inc: str) -> list[Path]:
    """
    inc can be:
      - relative folder: "google" or "foo/bar"
      - templated: "{proto_root}/google" or "{ proto_root }/google"
      - globby: "google/**" or "{proto_root}/**/v1"
    Returns 1..N base paths (if glob expands).
    """
    proto_root = proto_root.resolve()

    # Replace mustache-ish token if present
    if _PROTO_ROOT_TOKEN.search(inc):
        expanded = _PROTO_ROOT_TOKEN.sub(str(proto_root), inc)
        base = Path(expanded)
    else:
        base = proto_root / inc

    # If include contains glob chars, expand it
    s = str(base)
    if any(ch in s for ch in ["*", "?", "["]):
        # glob needs a directory base; easiest is to glob from filesystem root if absolute
        if base.is_absolute():
            # Use Path("/") as root for absolute globs
            matches = [p.resolve() for p in Path("/").glob(s.lstrip("/"))]
        else:
            matches = [p.resolve() for p in proto_root.glob(str(base.relative_to(proto_root)))]
        return [p for p in matches if p.exists()]
    else:
        return [base.resolve()]


def discover_proto_files(proto_root: Path, config: CodegenConfig) -> list[Path]:
    proto_root = proto_root.resolve()

    roots: list[Path] = []
    if config.proto.includes:
        for inc in config.proto.includes:
            for r in _resolve_include(proto_root, inc):
                # keep only dirs that are inside proto_root (avoid escaping)
                if r == proto_root or proto_root in r.parents:
                    roots.append(r)
    else:
        roots = [proto_root]

    out: list[Path] = []
    for base in roots:
        if not base.exists():
            continue
        for pat in config.proto.files:
            out.extend(base.glob(pat))  # supports **/*.proto, etc.

    # unique + stable
    uniq: list[Path] = []
    seen: set[Path] = set()
    for p in sorted(out):
        rp = p.resolve()
        if rp.is_file() and rp.suffix == ".proto" and rp not in seen:
            uniq.append(rp)
            seen.add(rp)
    return uniq
