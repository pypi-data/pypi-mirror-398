"""
Type mapping hooks for code generation templates.

Provides filters for mapping proto types to language-specific types,
handling optionality, and repeated fields.
"""
from jinja2 import Environment
from google.protobuf.descriptor_pb2 import FieldDescriptorProto as F

# =============================================================================
# Proto Constants
# =============================================================================

# Field labels
LABEL_OPTIONAL = 1
LABEL_REQUIRED = 2
LABEL_REPEATED = 3

# Field types
TYPE_DOUBLE = 1
TYPE_FLOAT = 2
TYPE_INT64 = 3
TYPE_UINT64 = 4
TYPE_INT32 = 5
TYPE_FIXED64 = 6
TYPE_FIXED32 = 7
TYPE_BOOL = 8
TYPE_STRING = 9
TYPE_GROUP = 10
TYPE_MESSAGE = 11
TYPE_BYTES = 12
TYPE_UINT32 = 13
TYPE_ENUM = 14
TYPE_SFIXED32 = 15
TYPE_SFIXED64 = 16
TYPE_SINT32 = 17
TYPE_SINT64 = 18


# =============================================================================
# Nested Type Resolution Utilities
# =============================================================================

def _resolve_nested_type_name(type_name: str, prefix_style: str = "concat") -> str:
    """
    Resolve a proto type_name to the correct prefixed name for nested types.

    For a type_name like ".customer.Customer.Profile.Avatar":
    - Parts: ["", "customer", "Customer", "Profile", "Avatar"]
    - Package: "customer"
    - Type path: ["Customer", "Profile", "Avatar"]

    prefix_style options:
    - "concat": CustomerProfileAvatar (TypeScript)
    - "underscore": Customer_Profile_Avatar (Go)
    - "short": Avatar (Swift/Kotlin - uses actual nesting)
    """
    if not type_name:
        return "unknown"

    parts = type_name.split(".")
    # Remove empty first element and package
    # type_name is like ".package.Type" or ".package.Parent.Nested"
    if parts[0] == "":
        parts = parts[1:]

    if len(parts) < 2:
        # Just a type name, no package
        return parts[-1] if parts else "unknown"

    # First part is package, rest are type hierarchy
    type_parts = parts[1:]  # Skip package

    if len(type_parts) == 1:
        # Top-level type, no nesting
        return type_parts[0]

    # Nested type - apply prefix style
    if prefix_style == "concat":
        # TypeScript: CustomerProfile, CustomerProfileAvatar
        return "".join(type_parts)
    elif prefix_style == "underscore":
        # Go: Customer_Profile, Customer_Profile_Avatar
        return "_".join(type_parts)
    else:
        # Swift/Kotlin: just use the short name (they have real nesting)
        return type_parts[-1]


# =============================================================================
# TypeScript Type Mapping
# =============================================================================

TS_TYPE_MAP = {
    TYPE_DOUBLE: "number",
    TYPE_FLOAT: "number",
    TYPE_INT64: "bigint",
    TYPE_UINT64: "bigint",
    TYPE_INT32: "number",
    TYPE_FIXED64: "bigint",
    TYPE_FIXED32: "number",
    TYPE_BOOL: "boolean",
    TYPE_STRING: "string",
    TYPE_BYTES: "Uint8Array",
    TYPE_UINT32: "number",
    TYPE_SFIXED32: "number",
    TYPE_SFIXED64: "bigint",
    TYPE_SINT32: "number",
    TYPE_SINT64: "bigint",
}


def ts_type(field) -> str:
    """Map proto field to TypeScript type."""
    base_type = _get_ts_base_type(field)
    return _wrap_ts_type(field, base_type)


def _get_ts_base_type(field) -> str:
    """Get the base TypeScript type for a field."""
    if field.get("type_name"):
        # Message or enum reference - resolve nested type names
        return _resolve_nested_type_name(field["type_name"], prefix_style="concat")

    field_type = field.get("type", 0)
    if field_type == TYPE_ENUM:
        type_name = field.get("type_name", "")
        return _resolve_nested_type_name(type_name, prefix_style="concat") if type_name else "number"

    return TS_TYPE_MAP.get(field_type, "unknown")


def _wrap_ts_type(field, base_type: str) -> str:
    """Wrap type with array/optional as needed."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return f"{base_type}[]"

    return base_type


def ts_type_optional(field) -> str:
    """Get TypeScript type with optional marker for non-required fields."""
    base = ts_type(field)
    label = field.get("label", LABEL_OPTIONAL)

    # In proto3, all scalar fields are optional by default
    if label != LABEL_REPEATED:
        return f"{base} | undefined"

    return base


def is_ts_optional(field) -> bool:
    """Check if field should be optional in TypeScript."""
    label = field.get("label", LABEL_OPTIONAL)
    return label == LABEL_OPTIONAL


def is_repeated(field) -> bool:
    """Check if field is repeated (array)."""
    return field.get("label", LABEL_OPTIONAL) == LABEL_REPEATED


# =============================================================================
# Swift Type Mapping
# =============================================================================

SWIFT_TYPE_MAP = {
    TYPE_DOUBLE: "Double",
    TYPE_FLOAT: "Float",
    TYPE_INT64: "Int64",
    TYPE_UINT64: "UInt64",
    TYPE_INT32: "Int32",
    TYPE_FIXED64: "UInt64",
    TYPE_FIXED32: "UInt32",
    TYPE_BOOL: "Bool",
    TYPE_STRING: "String",
    TYPE_BYTES: "Data",
    TYPE_UINT32: "UInt32",
    TYPE_SFIXED32: "Int32",
    TYPE_SFIXED64: "Int64",
    TYPE_SINT32: "Int32",
    TYPE_SINT64: "Int64",
}


def swift_type(field) -> str:
    """Map proto field to Swift type."""
    base_type = _get_swift_base_type(field)
    return _wrap_swift_type(field, base_type)


def _get_swift_base_type(field) -> str:
    """Get the base Swift type for a field."""
    if field.get("type_name"):
        return field["type_name"].split(".")[-1]

    field_type = field.get("type", 0)
    return SWIFT_TYPE_MAP.get(field_type, "Any")


def _wrap_swift_type(field, base_type: str) -> str:
    """Wrap type with array/optional as needed."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return f"[{base_type}]"

    return base_type


def swift_type_optional(field) -> str:
    """Get Swift type as optional."""
    base = swift_type(field)
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return base  # Arrays are already optional-friendly

    return f"{base}?"


def swift_default_value(field) -> str:
    """Get Swift default value for a field."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return "[]"

    field_type = field.get("type", 0)

    if field_type == TYPE_STRING:
        return '""'
    elif field_type == TYPE_BOOL:
        return "false"
    elif field_type in (TYPE_DOUBLE, TYPE_FLOAT):
        return "0.0"
    elif field_type in (TYPE_INT32, TYPE_INT64, TYPE_UINT32, TYPE_UINT64,
                        TYPE_FIXED32, TYPE_FIXED64, TYPE_SFIXED32, TYPE_SFIXED64,
                        TYPE_SINT32, TYPE_SINT64):
        return "0"
    elif field_type == TYPE_BYTES:
        return "Data()"
    elif field.get("type_name"):
        # Message type
        type_name = field["type_name"].split(".")[-1]
        return f"{type_name}()"

    return "nil"


# =============================================================================
# Kotlin Type Mapping
# =============================================================================

KOTLIN_TYPE_MAP = {
    TYPE_DOUBLE: "Double",
    TYPE_FLOAT: "Float",
    TYPE_INT64: "Long",
    TYPE_UINT64: "ULong",
    TYPE_INT32: "Int",
    TYPE_FIXED64: "ULong",
    TYPE_FIXED32: "UInt",
    TYPE_BOOL: "Boolean",
    TYPE_STRING: "String",
    TYPE_BYTES: "ByteArray",
    TYPE_UINT32: "UInt",
    TYPE_SFIXED32: "Int",
    TYPE_SFIXED64: "Long",
    TYPE_SINT32: "Int",
    TYPE_SINT64: "Long",
}


def kotlin_type(field) -> str:
    """Map proto field to Kotlin type."""
    base_type = _get_kotlin_base_type(field)
    return _wrap_kotlin_type(field, base_type)


def _get_kotlin_base_type(field) -> str:
    """Get the base Kotlin type for a field."""
    if field.get("type_name"):
        return field["type_name"].split(".")[-1]

    field_type = field.get("type", 0)
    return KOTLIN_TYPE_MAP.get(field_type, "Any")


def _wrap_kotlin_type(field, base_type: str) -> str:
    """Wrap type with List/nullable as needed."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return f"List<{base_type}>"

    return base_type


def kotlin_type_nullable(field) -> str:
    """Get Kotlin type as nullable."""
    base = kotlin_type(field)
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return base

    return f"{base}?"


def kotlin_default_value(field) -> str:
    """Get Kotlin default value for a field."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return "emptyList()"

    field_type = field.get("type", 0)

    if field_type == TYPE_STRING:
        return '""'
    elif field_type == TYPE_BOOL:
        return "false"
    elif field_type in (TYPE_DOUBLE, TYPE_FLOAT):
        return "0.0"
    elif field_type in (TYPE_INT32, TYPE_SINT32, TYPE_SFIXED32):
        return "0"
    elif field_type in (TYPE_INT64, TYPE_SINT64, TYPE_SFIXED64):
        return "0L"
    elif field_type in (TYPE_UINT32, TYPE_FIXED32):
        return "0u"
    elif field_type in (TYPE_UINT64, TYPE_FIXED64):
        return "0uL"
    elif field_type == TYPE_BYTES:
        return "byteArrayOf()"
    elif field.get("type_name"):
        type_name = field["type_name"].split(".")[-1]
        return f"{type_name}()"

    return "null"


# =============================================================================
# Go Type Mapping
# =============================================================================

GO_TYPE_MAP = {
    TYPE_DOUBLE: "float64",
    TYPE_FLOAT: "float32",
    TYPE_INT64: "int64",
    TYPE_UINT64: "uint64",
    TYPE_INT32: "int32",
    TYPE_FIXED64: "uint64",
    TYPE_FIXED32: "uint32",
    TYPE_BOOL: "bool",
    TYPE_STRING: "string",
    TYPE_BYTES: "[]byte",
    TYPE_UINT32: "uint32",
    TYPE_SFIXED32: "int32",
    TYPE_SFIXED64: "int64",
    TYPE_SINT32: "int32",
    TYPE_SINT64: "int64",
}


def go_type(field) -> str:
    """Map proto field to Go type."""
    base_type = _get_go_base_type(field)
    return _wrap_go_type(field, base_type)


def _get_go_base_type(field) -> str:
    """Get the base Go type for a field."""
    if field.get("type_name"):
        # Resolve nested type names with underscore style
        type_name = _resolve_nested_type_name(field["type_name"], prefix_style="underscore")
        # In Go, message types are typically pointers
        if field.get("type") == TYPE_MESSAGE:
            return f"*{type_name}"
        return type_name  # Enum

    field_type = field.get("type", 0)
    return GO_TYPE_MAP.get(field_type, "interface{}")


def _wrap_go_type(field, base_type: str) -> str:
    """Wrap type with slice as needed."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        # Don't double-wrap []byte
        if base_type == "[]byte":
            return "[][]byte"
        return f"[]{base_type}"

    return base_type


def go_type_pointer(field) -> str:
    """Get Go type as pointer for optional fields."""
    base = go_type(field)
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return base

    # Already a pointer for message types
    if base.startswith("*"):
        return base

    return f"*{base}"


def go_zero_value(field) -> str:
    """Get Go zero value for a field."""
    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_REPEATED:
        return "nil"

    field_type = field.get("type", 0)

    if field_type == TYPE_STRING:
        return '""'
    elif field_type == TYPE_BOOL:
        return "false"
    elif field_type in (TYPE_DOUBLE, TYPE_FLOAT):
        return "0"
    elif field_type in (TYPE_INT32, TYPE_INT64, TYPE_UINT32, TYPE_UINT64,
                        TYPE_FIXED32, TYPE_FIXED64, TYPE_SFIXED32, TYPE_SFIXED64,
                        TYPE_SINT32, TYPE_SINT64):
        return "0"
    elif field_type == TYPE_BYTES:
        return "nil"
    elif field.get("type_name"):
        return "nil"

    return "nil"


def go_json_tag(field) -> str:
    """Generate Go JSON struct tag for a field."""
    json_name = field.get("json_name", "")
    if not json_name:
        # Fallback to field name
        name_obj = field.get("name")
        if name_obj:
            json_name = getattr(name_obj, "raw", str(name_obj))

    label = field.get("label", LABEL_OPTIONAL)

    if label == LABEL_OPTIONAL:
        return f'`json:"{json_name},omitempty"`'

    return f'`json:"{json_name}"`'


# =============================================================================
# Register all filters
# =============================================================================

def register(env: Environment, *, target: str, config) -> None:
    """Register all type mapping filters for the given target."""

    # Common filters
    env.filters["is_repeated"] = is_repeated

    # TypeScript filters
    env.filters["ts_type"] = ts_type
    env.filters["ts_type_optional"] = ts_type_optional
    env.filters["is_ts_optional"] = is_ts_optional

    # Swift filters
    env.filters["swift_type"] = swift_type
    env.filters["swift_type_optional"] = swift_type_optional
    env.filters["swift_default"] = swift_default_value

    # Kotlin filters
    env.filters["kotlin_type"] = kotlin_type
    env.filters["kotlin_type_nullable"] = kotlin_type_nullable
    env.filters["kotlin_default"] = kotlin_default_value

    # Go filters
    env.filters["go_type"] = go_type
    env.filters["go_type_pointer"] = go_type_pointer
    env.filters["go_zero"] = go_zero_value
    env.filters["go_json_tag"] = go_json_tag
