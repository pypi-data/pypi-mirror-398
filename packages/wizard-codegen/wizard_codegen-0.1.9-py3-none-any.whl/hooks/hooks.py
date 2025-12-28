import importlib
from pathlib import Path
from typing import Protocol, runtime_checkable

from jinja2 import Environment
from core import CodegenConfig


@runtime_checkable
class HooksModule(Protocol):
    def register(self, env: Environment, *, target: str, config: CodegenConfig) -> None: ...


def load_hooks(cfg: CodegenConfig, repo_root: Path) -> HooksModule | None:
    if not cfg.hooks.module:
        return None

    import sys
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        module = importlib.import_module(cfg.hooks.module)
        if not isinstance(module, HooksModule):
            raise ValueError(f"Hooks module {cfg.hooks.module} doesn't implement required interface")
        return module
    except ImportError as e:
        raise RuntimeError(f"Failed to import hooks module {cfg.hooks.module}: {e}") from e