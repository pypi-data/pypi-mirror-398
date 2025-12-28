from __future__ import annotations
from pathlib import Path
from collections import defaultdict, deque
from typing import Any, Dict, List

import typer
from google.protobuf import descriptor_pb2
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from .config import CodegenConfig
from utils import Name


def topo_order(files_by_name: dict[str, descriptor_pb2.FileDescriptorProto]) -> list[str]:
    """Topologically sort proto files based on their dependencies."""
    deps = {n: [d for d in f.dependency if d in files_by_name] for n, f in files_by_name.items()}
    indeg = {n: 0 for n in files_by_name}
    rev = defaultdict(list)

    for n, ds in deps.items():
        for d in ds:
            indeg[n] += 1
            rev[d].append(n)

    q = deque([n for n, deg in indeg.items() if deg == 0])
    out = []
    while q:
        n = q.popleft()
        out.append(n)
        for m in rev[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    return out


def _pkg_path(pkg: str) -> str:
    """Convert package name to path format."""
    return pkg.replace(".", "/") if pkg else ""


def _build_full_name(package: str, name: str) -> str:
    """Build fully qualified name for a proto type."""
    return f".{package}.{name}" if package else f".{name}"


def _build_field_data(field: Any) -> Dict[str, Any]:
    """Build field data dictionary from protobuf field descriptor."""
    return {
        "name": Name(field.name),
        "number": field.number,
        "label": int(field.label),
        "type": int(field.type),
        "type_name": field.type_name,
        "json_name": field.json_name,
        "field": field
    }


def _build_method_data(method: Any) -> Dict[str, Any]:
    """Build method data dictionary from protobuf method descriptor."""
    return {
        "name": Name(method.name),
        "input_type": method.input_type,
        "output_type": method.output_type,
        "client_streaming": bool(method.client_streaming),
        "server_streaming": bool(method.server_streaming),
        "options": method.options,
    }


def _build_enum_value_data(value: Any) -> Dict[str, Any]:
    """Build enum value data dictionary from protobuf enum value descriptor."""
    return {"name": value.name, "number": value.number}


def _update_type_index(type_index: Dict[str, Any], full_name: str, kind: str, file_name: str, package: str) -> None:
    """Update the type index with a new type entry."""
    type_index[full_name] = {"kind": kind, "file": file_name, "package": package}


def _process_nested_enum(
        enum: Any,
        parent_full_name: str,
        file_name: str,
        package: str,
        type_index: Dict[str, Any],
        enum_index: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a nested enum within a message."""
    full_name = f"{parent_full_name}.{enum.name}"
    enum_values = [_build_enum_value_data(value) for value in enum.value]

    enum_data = {
        "name": Name(enum.name),
        "full_name": full_name,
        "file": file_name,
        "package": package,
        "enum_values": enum_values,  # Use enum_values to avoid conflict with dict.values()
    }

    _update_type_index(type_index, full_name, "enum", file_name, package)
    enum_index[full_name] = enum_data

    return enum_data


def _process_message_recursive(
        message: Any,
        parent_full_name: str,
        file_name: str,
        package: str,
        type_index: Dict[str, Any],
        message_index: Dict[str, Any],
        enum_index: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a message and its nested types recursively."""
    # Build full name for this message
    if parent_full_name:
        full_name = f"{parent_full_name}.{message.name}"
    else:
        full_name = _build_full_name(package, message.name)

    fields = [_build_field_data(field) for field in message.field]

    # Process nested messages recursively
    nested_messages = []
    for nested_msg in message.nested_type:
        nested_data = _process_message_recursive(
            nested_msg,
            full_name,
            file_name,
            package,
            type_index,
            message_index,
            enum_index
        )
        nested_messages.append(nested_data)

    # Process nested enums
    nested_enums = []
    for nested_enum in message.enum_type:
        nested_enum_data = _process_nested_enum(
            nested_enum,
            full_name,
            file_name,
            package,
            type_index,
            enum_index
        )
        nested_enums.append(nested_enum_data)

    message_data = {
        "name": Name(message.name),
        "full_name": full_name,
        "fields": fields,
        "file": file_name,
        "package": package,
        "nested_messages": nested_messages,
        "nested_enums": nested_enums,
    }

    _update_type_index(type_index, full_name, "message", file_name, package)
    message_index[full_name] = message_data

    return message_data


def _process_messages(
        proto_file: Any,
        file_name: str,
        package: str,
        type_index: Dict[str, Any],
        message_index: Dict[str, Any],
        enum_index: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Process all messages in a proto file, including nested types."""
    messages = []

    for message in proto_file.message_type:
        message_data = _process_message_recursive(
            message,
            "",  # No parent for top-level messages
            file_name,
            package,
            type_index,
            message_index,
            enum_index
        )
        messages.append(message_data)

    return messages


def _process_enums(
        proto_file: Any,
        file_name: str,
        package: str,
        type_index: Dict[str, Any],
        enum_index: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Process all enums in a proto file."""
    enums = []

    for enum in proto_file.enum_type:
        full_name = _build_full_name(package, enum.name)
        enum_values = [_build_enum_value_data(value) for value in enum.value]

        enum_data = {
            "name": Name(enum.name),
            "full_name": full_name,
            "file": file_name,
            "package": package,
            "enum_values": enum_values,  # Use enum_values to avoid conflict with dict.values()
        }

        enums.append(enum_data)
        _update_type_index(type_index, full_name, "enum", file_name, package)
        enum_index[full_name] = enum_data

    return enums


def _process_services(
        proto_file: Any,
        file_name: str,
        package: str,
        service_index: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Process all services in a proto file."""
    services = []

    for service in proto_file.service:
        full_name = _build_full_name(package, service.name)
        methods = [_build_method_data(method) for method in service.method]

        service_data = {
            "name": Name(service.name),
            "methods": methods,
            "file": file_name,
            "package": package
        }

        services.append(service_data)
        service_index[full_name] = service_data

    return services


def _process_proto_file(
        proto_file: Any,
        file_name: str,
        type_index: Dict[str, Any],
        message_index: Dict[str, Any],
        enum_index: Dict[str, Any],
        service_index: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a single proto file and return its context data."""
    package = proto_file.package
    base_name = Path(file_name).stem

    messages = _process_messages(proto_file, file_name, package, type_index, message_index, enum_index)
    enums = _process_enums(proto_file, file_name, package, type_index, enum_index)
    services = _process_services(proto_file, file_name, package, service_index)

    return {
        "name": Name(base_name),
        "full_name": file_name,
        "package": package,
        "package_path": _pkg_path(package),
        "imports": list(proto_file.dependency),
        "messages": messages,
        "enums": enums,
        "services": services,
        "options": proto_file.options,
    }


def build_context(cfg: CodegenConfig, fds: descriptor_pb2.FileDescriptorSet) -> Dict[str, Any]:
    """Build the complete context for code generation from proto file descriptors."""
    files_by_name = {f.name: f for f in fds.file}
    ordered_files = topo_order(files_by_name)

    # Initialize indexes
    type_index = {}
    message_index = {}
    enum_index = {}
    service_index = {}
    ctx_files = []

    # Process each file in topological order
    for file_name in ordered_files:
        proto_file = files_by_name[file_name]
        file_context = _process_proto_file(
            proto_file, file_name, type_index, message_index, enum_index, service_index
        )
        ctx_files.append(file_context)

    return {
        "proto_root": cfg.proto.root,
        "files": ctx_files,
        "types": type_index,
        "message": message_index,
        "enum": enum_index,
        "service": service_index,
    }


def print_build_context(ctx: Dict[str, Any], typer_ctx: typer.Context, console: Console,
                        title: str = "Jinja2 context") -> None:
    """Print the build context if verbose mode is enabled."""
    if typer_ctx.obj.verbose:
        console.print(
            Panel(
                Pretty(ctx, expand_all=True),
                title=f"[bold]{title}[/]",
                border_style="cyan",
            )
        )
