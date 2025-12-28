from __future__ import annotations
import re
from typing import Any
from .config import Where, Predicate
import fnmatch

def _get_opt(item: dict, key: str) -> Any:
    # expect custom options extracted into item["options"] as dict
    return (item.get("options") or {}).get(key)

def _match_regex(value: str | None, pattern: str) -> bool:
    if value is None:
        return False

    # Treat patterns containing glob chars as glob
    if any(ch in pattern for ch in ["*", "?", "[", "]"]):
        return fnmatch.fnmatch(value, pattern)

    return re.search(pattern, value) is not None

def _pred_ok(item: dict, p: Predicate) -> bool:
    if p.name and not _match_regex(_name_raw(item), p.name):
        return False
    if p.package and not _match_regex(item.get("package"), p.package):
        return False
    if p.file and not _match_regex(item.get("file"), p.file):
        return False
    if p.full_name and not _match_regex(item.get("full_name"), p.full_name):
        return False
    if p.option_equals:
        if _get_opt(item, p.option_equals.key) != p.option_equals.value:
            return False
    return True

def where_ok(item: dict, where: Where | None) -> bool:
    if where is None:
        return True

    # NOT
    for p in where.not_:
        if _pred_ok(item, p):
            return False

    # ALL (AND)
    for p in where.all:
        if not _pred_ok(item, p):
            return False

    # ANY (OR) - if present, must match at least one
    if where.any:
        if not any(_pred_ok(item, p) for p in where.any):
            return False

    return True

def _name_raw(item: dict) -> str | None:
    n = item.get("name")
    if n is None:
        return None
    if isinstance(n, str):
        return n
    if isinstance(n, dict):
        return n.get("raw")
    # dataclass / pydantic / simple object
    return getattr(n, "raw", str(n))