from __future__ import annotations

import hashlib
from typing import Literal

from .renderer import PlanItem


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def apply_plan(plan: list[PlanItem], dry_run: bool, verbose: bool):
    for item in plan:
        mode: Literal["overwrite", "append", "write-once"] = getattr(item, "mode", "overwrite")

        # write-once: if the file exists, never touch it
        if mode == "write-once" and item.output_path.exists():
            if verbose:
                print(f"skip (write-once exists): {item.output_path}")
            continue

        if not dry_run:
            item.output_path.parent.mkdir(parents=True, exist_ok=True)

        new_hash = _sha256(item.content)

        old_text = ""
        if item.output_path.exists():
            old_text = item.output_path.read_text(encoding="utf-8")

            if mode == "overwrite":
                old_hash = _sha256(old_text)
                if old_hash == new_hash:
                    if verbose:
                        print(f"skip (unchanged): {item.output_path}")
                    continue

            elif mode == "append":
                # guard against duplicating the same block
                if old_text.endswith(item.content):
                    if verbose:
                        print(f"skip (already appended): {item.output_path}")
                    continue

            elif mode == "write-once":
                # handled earlier, but keep it explicit
                if verbose:
                    print(f"skip (write-once exists): {item.output_path}")
                continue

            else:
                raise ValueError(f"Unknown mode {mode!r} for {item.output_path}")

        action = "append" if mode == "append" and item.output_path.exists() else "write"

        if dry_run:
            print(f"would {action}: {item.output_path}")
            continue

        if mode == "append" and item.output_path.exists():
            # ensure we start on a new line
            prefix = "" if old_text.endswith("\n") or item.content.startswith("\n") else "\n"
            item.output_path.write_text(old_text + prefix + item.content, encoding="utf-8")
        else:
            # overwrite + write_once (new file) both come here
            item.output_path.write_text(item.content, encoding="utf-8")

        if verbose:
            print(f"{action}d: {item.output_path}")
