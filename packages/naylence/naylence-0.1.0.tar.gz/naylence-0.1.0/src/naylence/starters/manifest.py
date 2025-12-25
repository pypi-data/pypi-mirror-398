from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from pydantic import ValidationError

from naylence.starters.models import TemplateFlavor, TemplateInfo, TemplateManifest

MANIFEST_FILENAME = "manifest.json"
TEMPLATES_DIR = "templates"


def load_manifest_from_path(starters_path: str) -> TemplateManifest:
    manifest_path = Path(starters_path) / TEMPLATES_DIR / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Templates manifest not found: {manifest_path}\n"
            "Make sure NAYLENCE_STARTERS_PATH points to the starters repo root."
        )
    raw = manifest_path.read_text(encoding="utf-8")
    return parse_manifest(raw, str(manifest_path))


def parse_manifest(raw: str, manifest_path: str) -> TemplateManifest:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in manifest: {manifest_path}") from exc

    try:
        return TemplateManifest.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid manifest schema: {manifest_path}\n{exc}") from exc


def discover_templates(
    starters_path: str, on_warning: Optional[Callable[[str], None]] = None
) -> tuple[list[TemplateInfo], Optional[TemplateManifest]]:
    try:
        manifest = load_manifest_from_path(starters_path)
    except FileNotFoundError as exc:
        if on_warning:
            on_warning(str(exc))
        return scan_templates(starters_path), None
    except ValueError as exc:
        if on_warning:
            on_warning(str(exc))
        return scan_templates(starters_path), None

    return list_templates_from_manifest(starters_path, manifest, check_paths=True), manifest


def list_templates_from_manifest(
    starters_path: str, manifest: TemplateManifest, check_paths: bool = True
) -> list[TemplateInfo]:
    templates: list[TemplateInfo] = []
    templates_dir = Path(starters_path) / TEMPLATES_DIR

    for entry in manifest.templates:
        template_root = templates_dir / entry.id
        if check_paths and not template_root.is_dir():
            continue

        flavors: list[str] = []
        flavor_details: dict[str, TemplateFlavor] = {}

        for flavor in entry.flavors:
            relative_path = flavor.path or flavor.id
            if check_paths:
                flavor_dir = template_root / relative_path
                if not flavor_dir.is_dir():
                    continue
            flavors.append(flavor.id)
            flavor_details[flavor.id] = flavor

        if not flavors:
            continue

        templates.append(
            TemplateInfo(
                id=entry.id,
                name=entry.name,
                description=entry.description,
                flavors=flavors,
                flavor_details=flavor_details,
                order=entry.order,
                category=entry.category,
                aliases=entry.aliases,
                hidden=entry.hidden,
                deprecated=entry.deprecated,
            )
        )

    return sort_templates(templates)


def scan_templates(starters_path: str) -> list[TemplateInfo]:
    templates_dir = Path(starters_path) / TEMPLATES_DIR
    if not templates_dir.exists():
        raise FileNotFoundError(
            f"Templates directory not found: {templates_dir}\n"
            "Make sure NAYLENCE_STARTERS_PATH points to the starters repo root."
        )

    templates: list[TemplateInfo] = []
    for template_dir in templates_dir.iterdir():
        if not template_dir.is_dir():
            continue
        flavors = [child.name for child in template_dir.iterdir() if child.is_dir()]
        if not flavors:
            continue

        templates.append(
            TemplateInfo(
                id=template_dir.name,
                name=template_dir.name,
                description=None,
                flavors=flavors,
                flavor_details={
                    flavor_id: TemplateFlavor(id=flavor_id) for flavor_id in flavors
                },
            )
        )

    return sort_templates(templates)


def resolve_flavor_path(
    manifest: TemplateManifest, template_id: str, flavor_id: str
) -> str | None:
    for entry in manifest.templates:
        if entry.id != template_id:
            continue
        for flavor in entry.flavors:
            if flavor.id == flavor_id:
                return flavor.path or flavor.id
    return None


def resolve_next_steps(
    manifest: TemplateManifest, template_id: str, flavor_id: str
) -> list[str] | None:
    for entry in manifest.templates:
        if entry.id != template_id:
            continue
        for flavor in entry.flavors:
            if flavor.id == flavor_id:
                if flavor.next_steps:
                    return list(flavor.next_steps)
    return None


def format_template_list(templates: list[TemplateInfo]) -> str:
    if not templates:
        return "No templates found."

    lines = ["Available templates:", ""]
    for template in templates:
        label = f"{template.name} ({template.id})" if template.name != template.id else template.id
        lines.append(f"  {label}")
        if template.description:
            lines.append(f"    {template.description}")
        lines.append(f"    flavors: {', '.join(template.flavors)}")
    return "\n".join(lines)


def sort_templates(templates: list[TemplateInfo]) -> list[TemplateInfo]:
    def _sort_key(template: TemplateInfo) -> tuple[float, str]:
        order = template.order if template.order is not None else float("inf")
        name = (template.name or template.id).lower()
        return (order, name)

    return sorted(templates, key=_sort_key)
