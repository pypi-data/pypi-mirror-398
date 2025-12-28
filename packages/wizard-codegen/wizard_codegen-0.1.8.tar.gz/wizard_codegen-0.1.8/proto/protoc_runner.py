from __future__ import annotations
from pathlib import Path
import subprocess
import tempfile

from core import CodegenConfig
from utils import expand_path


def build_descriptor_set(
    config: CodegenConfig,
    proto_root: Path,
    proto_files: list[Path],
    verbose: bool,
) -> tuple[Path, Path | None]:
    proto_root = proto_root.resolve()

    if config.proto.source and config.proto.source.fds:
        fds_path = expand_path(config.proto.source.fds).resolve()
        return fds_path, None

    if config.proto.cache_dir:
        cache_dir = expand_path(config.proto.cache_dir, mkdir=True).resolve()
    else:
        cache_dir = Path.cwd() / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path(tempfile.mkdtemp(prefix="wizard_protoc_codegen_", dir=cache_dir))
    fds_path = out_dir / "descriptor.pb"

    cmd: list[str] = ["protoc"]

    # Include roots: proto_root + each configured include dir (resolve relative to proto_root)
    include_dirs: list[Path] = [proto_root]
    for inc in (config.proto.includes or []):
        # if you support {proto_root} templating, apply it here the same way you do in discovery
        p = (proto_root / inc).resolve() if "{proto_root}" not in inc else Path(inc.replace("{proto_root}", str(proto_root))).resolve()
        if p.exists():
            include_dirs.append(p)

    # de-dupe include dirs
    seen = set()
    for d in include_dirs:
        ds = str(d)
        if ds not in seen:
            cmd += ["-I", ds]
            seen.add(ds)

    cmd += ["--include_imports"]
    if config.proto.source and getattr(config.proto.source, "include_info", False):
        cmd += ["--include_source_info"]

    cmd += [f"--descriptor_set_out={fds_path}"]

    # pass proto file paths relative to proto_root
    rels = [str(p.resolve().relative_to(proto_root)) for p in proto_files]
    cmd += rels

    if verbose:
        print(" ".join(cmd))

    subprocess.run(cmd, cwd=str(proto_root), check=True)
    return fds_path, out_dir
