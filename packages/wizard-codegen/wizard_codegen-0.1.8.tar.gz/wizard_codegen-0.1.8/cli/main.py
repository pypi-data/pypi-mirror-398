from __future__ import annotations

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.pretty import Pretty
from dataclasses import dataclass
from importlib.metadata import version as get_version
from typing import Optional

from core import *
from proto import *
import shutil

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
console = Console()


def version_callback(value: bool):
    if value:
        ver = get_version("wizard-codegen")
        console.print(f"wizard-codegen [bold cyan]{ver}[/]")
        raise typer.Exit()


@dataclass
class Ctx:
    verbose: bool = False
    dry_run: bool = False
    local: bool = False
    config_path: Path = Path("wizard/codegen.yaml")


@app.callback()
def common(
        ctx: typer.Context,
        version: Optional[bool] = typer.Option(
            None, "--version", "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="More logs"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without changing files"),
        local: bool = typer.Option(False, "--local", "-l", help="Use local proto.root instead of git source"),
        config_path: Path = typer.Option(
            Path("wizard/codegen.yaml"),
            "--config", "-c",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to codegen config YAML",
        ),
):
    ctx.obj = Ctx(verbose=verbose, dry_run=dry_run, local=local, config_path=config_path)


@app.command(help="Generate code from protos")
def generate(ctx: typer.Context):
    _print_verbose_enabled(ctx)
    config = _load_config(ctx.obj.config_path, ctx)
    proto_root = resolve_proto_root(config, use_local=ctx.obj.local)
    files = discover_proto_files(proto_root, config)
    _validate_proto_files(files, config, proto_root)
    if ctx.obj.verbose:
        _print_files_table(files, proto_root)

    fds_path, tmp_dir = build_descriptor_set(config, proto_root, files, ctx.obj.verbose)
    print_fds_content(fds_path, ctx, console)
    fds = load_fds(fds_path)
    jinja_ctx = build_context(config, fds)
    print_build_context(jinja_ctx, ctx, console)
    plan = render_all(config, jinja_ctx)

    apply_plan(plan, ctx.obj.dry_run, ctx.obj.verbose)

    # Cleanup Tmp Dir
    if tmp_dir:
        shutil.rmtree(tmp_dir)

    if ctx.obj.dry_run:
        console.print("[bold green]✓[/] Dry run finished")
    else:
        console.print("[bold green]✓[/] Generated code")


@app.command("list-protos", help="List available protos")
def list_protos(ctx: typer.Context):
    _print_verbose_enabled(ctx)
    config = _load_config(ctx.obj.config_path, ctx)
    proto_root = resolve_proto_root(config, use_local=ctx.obj.local)
    files = discover_proto_files(proto_root, config)
    _print_files_table(files, proto_root)


@app.command(help="Validate the jinja2 templates, resolves proto root (git checkout), runs protoc descriptor build if needed, prints missing filters/variables")
def validate(ctx: typer.Context):
    _print_verbose_enabled(ctx)
    config = _load_config(ctx.obj.config_path, ctx)
    proto_root = resolve_proto_root(config, use_local=ctx.obj.local)
    files = discover_proto_files(proto_root, config)
    _validate_proto_files(files, config, proto_root)

    if ctx.obj.verbose:
        _print_files_table(files, proto_root)

    fds_path, tmp_dir = build_descriptor_set(config, proto_root, files, ctx.obj.verbose)
    print_fds_content(fds_path, ctx, console)
    fds = load_fds(fds_path)
    jinja_ctx = build_context(config, fds)
    print_build_context(jinja_ctx, ctx, console)
    render_all(config, jinja_ctx)

    # Cleanup Tmp Dir
    if tmp_dir:
        shutil.rmtree(tmp_dir)

    console.print("[bold green]✓[/] Validation successful")


def _print_files_table(files, proto_root):
    table = Table(title="Available proto schemas")
    table.add_column("Name", style="bold")
    table.add_column("Path", style="dim")
    for f in files:
        table.add_row(f.stem, f.relative_to(proto_root).as_posix())
    console.print(table)


def _validate_proto_files(files: list[Path], config: CodegenConfig, proto_root: Path) -> None:
    """Validate that proto files were discovered, exit with helpful error if not."""
    if files:
        return

    includes = config.proto.includes or ["(root)"]
    patterns = config.proto.files

    console.print("[bold red]Error:[/] No proto files found!")
    console.print()
    console.print(f"[dim]Proto root:[/]  {proto_root}")
    console.print(f"[dim]Includes:[/]    {', '.join(includes)}")
    console.print(f"[dim]File patterns:[/] {', '.join(patterns)}")
    console.print()
    console.print("[yellow]Hint:[/] Check that your [bold]proto.includes[/] directories exist and contain")
    console.print(f"      files matching [bold]{', '.join(patterns)}[/]")
    raise typer.Exit(1)


def _print_verbose_enabled(ctx: typer.Context):
    if ctx.obj.verbose:
        console.print("[dim]Verbose enabled[/]")

def _load_config(path: Path, ctx: typer.Context) -> CodegenConfig:
    config = load_config(path, console)
    if ctx.obj.verbose:
        console.print(
            Panel(
                Pretty(
                    # pydantic v2
                    config.model_dump(mode="python"),
                    expand_all=True,
                ),
                title=f"[bold]Loaded config[/] [dim]{path}[/]",
                border_style="cyan",
            )
        )
    return config

def main():
    app()

if __name__ == "__main__":
    main()
