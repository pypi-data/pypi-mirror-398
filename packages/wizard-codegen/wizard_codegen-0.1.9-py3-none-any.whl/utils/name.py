from __future__ import annotations
import re
from dataclasses import dataclass

_WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+")

def _words(s: str) -> list[str]:
    # Handles "MyMessage", "my_message", "my-message", "my message", "HTTPServer2"
    s = s.replace("_", " ").replace("-", " ").strip()
    parts: list[str] = []
    for token in s.split():
        parts.extend(_WORD_RE.findall(token))
    return [p for p in parts if p]

def to_snake(s: str) -> str:
    w = _words(s)
    return "_".join(p.lower() for p in w)

def to_kebab(s: str) -> str:
    w = _words(s)
    return "-".join(p.lower() for p in w)

def to_pascal(s: str) -> str:
    w = _words(s)
    return "".join(p[:1].upper() + p[1:].lower() for p in w)

def to_camel(s: str) -> str:
    w = _words(s)
    if not w:
        return ""
    first = w[0].lower()
    rest = "".join(p[:1].upper() + p[1:].lower() for p in w[1:])
    return first + rest

def to_macro(s: str) -> str:
    w = _words(s)
    return "".join(p.upper() for p in w)

def to_macro_snake(s: str) -> str:
    w = _words(s)
    return "_".join(p.upper() for p in w)

@dataclass(frozen=True)
class Name:
    raw: str

    @property
    def snake_case(self) -> str:
        return to_snake(self.raw)

    @property
    def kebab_case(self) -> str:
        return to_kebab(self.raw)

    @property
    def pascal_case(self) -> str:
        return to_pascal(self.raw)

    @property
    def camel_case(self) -> str:
        return to_camel(self.raw)

    @property
    def macro_case(self) -> str:
        return to_macro(self.raw)

    @property
    def macro_snake_case(self) -> str:
        return to_macro_snake(self.raw)
