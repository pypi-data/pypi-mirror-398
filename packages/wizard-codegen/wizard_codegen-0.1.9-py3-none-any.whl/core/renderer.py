from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config import CodegenConfig
from hooks import load_hooks
from .filter import where_ok
from utils import expand_path

@dataclass
class PlanItem:
    output_path: Path
    content: str
    mode: str = "overwrite"

def _make_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # add a couple generic filters
    env.filters["replace"] = lambda s, a, b: str(s).replace(a, b)
    return env

def _get_items_for_each_type(context: dict, for_each_type: str):
    """Get the appropriate items to iterate over based on for_each type."""
    if for_each_type == "file":
        return context["files"]
    elif for_each_type == "message":
        return context["message"].values()
    elif for_each_type == "enum":
        return context["enum"].values()
    elif for_each_type == "service":
        return context["service"].values()
    else:
        raise ValueError(f"Unknown for_each type: {for_each_type}")

def _render_item(item, context: dict, tpl, out_tpl, out_root: Path, mode: str) -> PlanItem:
    """Render a single item and return a PlanItem."""
    ctx = dict(context)
    ctx["item"] = item
    rel_out = Path(out_tpl.render(**ctx))
    content = tpl.render(**ctx)
    return PlanItem(output_path=out_root / rel_out, content=content, mode=mode)

def render_all(cfg: CodegenConfig, context: dict, out_override: Path | None = None) -> list[PlanItem]:
    plan: list[PlanItem] = []

    for target, tcfg in cfg.targets.items():
        template_dir = expand_path(tcfg.templates).resolve()
        out_root = (out_override or expand_path(tcfg.out)).resolve()

        env = _make_env(template_dir)

        hooks = load_hooks(cfg, expand_path(cfg.hooks.root))
        if hooks:
            hooks.register(env, target=target, config=cfg)

        for ep in tcfg.render:
            tpl = env.get_template(ep.template)
            out_tpl = env.from_string(ep.output)

            if ep.for_each:
                items = _get_items_for_each_type(context, ep.for_each)
                for item in items:
                    if not where_ok(item, ep.where):
                        continue
                    plan_item = _render_item(item, context, tpl, out_tpl, out_root, ep.mode)
                    plan.append(plan_item)
            else:
                rel_out = Path(out_tpl.render(**context))
                content = tpl.render(**context)
                plan.append(PlanItem(output_path=out_root / rel_out, content=content, mode=ep.mode))

    return plan
