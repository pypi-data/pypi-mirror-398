from __future__ import annotations
from pathlib import Path

import typer
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel

from google.protobuf import descriptor_pb2

def load_fds(path: Path) -> descriptor_pb2.FileDescriptorSet:
    fds = descriptor_pb2.FileDescriptorSet()
    fds.ParseFromString(path.read_bytes())
    return fds

def print_fds_content(fds_path: Path, ctx: typer.Context, console: Console) -> None:
    if not ctx.obj.verbose:
        return

    fds = descriptor_pb2.FileDescriptorSet()
    fds.ParseFromString(fds_path.read_bytes())

    tree = Tree(f"[bold]Descriptor Set[/] [dim]{fds_path}[/]")

    files_node = tree.add(f"[cyan]Files[/] ({len(fds.file)})")
    for fd in sorted(fds.file, key=lambda x: x.name):
        file_node = files_node.add(f"[bold]{fd.name}[/] [dim]package={fd.package or '-'}[/]")

        if fd.dependency:
            deps = file_node.add(f"[dim]deps[/] ({len(fd.dependency)})")
            for d in fd.dependency:
                deps.add(d)

        if fd.message_type:
            msgs = file_node.add(f"[green]messages[/] ({len(fd.message_type)})")
            for m in fd.message_type:
                msgs.add(m.name)

        if fd.enum_type:
            enums = file_node.add(f"[magenta]enums[/] ({len(fd.enum_type)})")
            for e in fd.enum_type:
                enums.add(e.name)

        if fd.service:
            svcs = file_node.add(f"[yellow]services[/] ({len(fd.service)})")
            for s in fd.service:
                svc = svcs.add(s.name)
                for meth in s.method:
                    svc.add(f"{meth.name}  [dim]{meth.input_type} -> {meth.output_type}[/]")

    console.print(Panel(tree, title="[bold]Descriptor contents[/]", border_style="blue"))
