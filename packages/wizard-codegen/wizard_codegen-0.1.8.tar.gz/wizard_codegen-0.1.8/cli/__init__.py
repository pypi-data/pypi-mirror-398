# Re-export everything from main for backwards compatibility
from cli.main import (
    app,
    console,
    Ctx,
    main,
    common,
    generate,
    list_protos,
    validate,
    _print_files_table,
    _print_verbose_enabled,
    _load_config,
)

__all__ = [
    "app",
    "console",
    "Ctx",
    "main",
    "common",
    "generate",
    "list_protos",
    "validate",
    "_print_files_table",
    "_print_verbose_enabled",
    "_load_config",
]
