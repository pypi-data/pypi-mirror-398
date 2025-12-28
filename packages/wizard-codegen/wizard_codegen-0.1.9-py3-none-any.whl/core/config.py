from __future__ import annotations

import typer
import yaml
from pathlib import Path
from typing import Any
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from rich.console import Console
from rich.panel import Panel

class ForEachMode(str, Enum):
    FILE = "file"
    MESSAGE = "message"
    ENUM = "enum"
    SERVICE = "service"

class WriteMode(str, Enum):
    OVERWRITE = "overwrite"
    APPEND = "append"
    WRITE_ONCE = "write-once"

class EqualsKV(BaseModel):
    key: str
    value: Any

# A single predicate
class Predicate(BaseModel):
    # dotted selector like "name", "package", "file", "full_name"
    # or "option" for descriptor options/custom options you extract into context
    name: str | None = None
    package: str | None = None
    file: str | None = None
    full_name: str | None = None
    option_equals: EqualsKV | None = Field(default=None, alias="option.equals")

    model_config = {"populate_by_name": True}

class Where(BaseModel):
    all: list[Predicate] = Field(default_factory=list)   # AND
    any: list[Predicate] = Field(default_factory=list)   # OR
    not_: list[Predicate] = Field(default_factory=list, alias="not")  # NOT

    model_config = {"populate_by_name": True}

class RenderTarget(BaseModel):
    template: str
    output: str
    mode: WriteMode = WriteMode.OVERWRITE
    for_each: ForEachMode | None = None
    where: Where | None = None

class ProtoSource(BaseModel):
    git: str
    ref: str = "latest-tag"  # Default to latest semver tag
    fds: str | None = None
    include_info: bool = True

class ProtoConfig(BaseModel):
    cache_dir: str
    includes: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    root: str | None = ""
    source: ProtoSource | None = None

class TargetConfig(BaseModel):
    templates: str
    out: str
    render: list[RenderTarget] = Field(default_factory=list)

class HooksConfig(BaseModel):
    root: str = "wizard"
    module: str | None = None

class CodegenConfig(BaseModel):
    # nice to have: forbid typos in YAML keys
    model_config = ConfigDict(extra="forbid")

    proto: ProtoConfig
    targets: dict[str, TargetConfig]
    hooks: HooksConfig = Field(default_factory=HooksConfig)

def _format_pydantic_errors(e: ValidationError) -> str:
    lines: list[str] = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err.get("loc", [])) or "<root>"
        msg = err.get("msg", "Invalid value")
        lines.append(f"• {loc}: {msg}")
    return "\n".join(lines)

def _die_config(message: str, console: Console, code: int = 2,) -> typer.Never:
    console.print(Panel(message, title="[bold red]Config error[/]", border_style="red"))
    raise typer.Exit(code=code)

def load_config(path: Path, console: Console) -> CodegenConfig:
    # 1) file read
    try:
        raw = path.read_text()
    except FileNotFoundError:
        _die_config(f"[bold]{path}[/] not found.\n\nPass a config with [cyan]--config[/].", console)
    except OSError as e:
        _die_config(f"Could not read [bold]{path}[/]: {e}", console)

    # 2) YAML parse
    try:
        data: dict[str, Any] = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        _die_config(f"Invalid YAML in [bold]{path}[/]:\n\n[dim]{e}[/]", console)

    # 3) Pydantic validate
    try:
        return CodegenConfig.model_validate(data)
    except ValidationError as e:
        problems = _format_pydantic_errors(e)
        hint = (
            "[bold]Expected top-level keys[/]\n"
            "• proto\n"
            "• targets\n"
            "• hooks (optional)\n\n"
            "[bold]Problems[/]\n"
            f"{problems}"
        )
        _die_config(f"In [bold]{path}[/]:\n\n{hint}", console)
