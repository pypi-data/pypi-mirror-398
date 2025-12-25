from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from naylence.starters.github import GitHubArchive
from naylence.starters.manifest import (
    discover_templates,
    format_template_list,
    resolve_flavor_path,
    resolve_next_steps,
)
from naylence.utils.fs import (
    copy_template,
    ensure_env_files,
    ensure_gitignore_entries,
    ensure_target_dir,
)
from naylence.utils.names import (
    get_project_name,
    resolve_git_ref,
    resolve_github_repo,
    resolve_starters_path,
)
from naylence.utils.placeholders import build_substitutions, substitute_in_directory


def run_init(args: argparse.Namespace) -> int:
    if args.from_local and args.from_github:
        print("Choose either --from-local or --from-github.", file=sys.stderr)
        return 2

    target_dir = args.target_dir
    if args.list and not target_dir:
        target_dir = "."
    if not args.list and not target_dir:
        print("Target directory is required.", file=sys.stderr)
        return 2

    starters_path = resolve_starters_path()
    use_local = args.from_local or (starters_path is not None and not args.from_github)

    if use_local:
        if not starters_path:
            print(
                "NAYLENCE_STARTERS_PATH is not set. "
                "Set it or use --from-github.",
                file=sys.stderr,
            )
            return 2
        return _run_init_local(starters_path, target_dir, args)

    repo = resolve_github_repo()
    ref = resolve_git_ref(args.ref)
    return _run_init_github(repo, ref, target_dir, args)


def _run_init_local(
    starters_path: str, target_dir: str, args: argparse.Namespace
) -> int:
    warnings: list[str] = []
    try:
        templates, manifest = discover_templates(starters_path, warnings.append)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if warnings:
        for warning in warnings:
            print(f"[warn] {warning}")

    if args.list:
        print(format_template_list(templates))
        return 0

    template_id = args.template or _prompt_choice(
        "Select a template:", [template.id for template in templates], force_prompt=True
    )
    if not template_id:
        print("No template selected.", file=sys.stderr)
        return 2

    template = next((item for item in templates if item.id == template_id), None)
    if not template:
        print(f"Template not found: {template_id}", file=sys.stderr)
        return 2

    try:
        flavor_id = select_flavor(template, args.flavor, default_flavor="py")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not flavor_id:
        print("No flavor selected.", file=sys.stderr)
        return 2

    project_name = get_project_name(target_dir)
    ensure_target_dir(target_dir, args.no_overwrite)

    if manifest is None:
        flavor_path = flavor_id
    else:
        flavor_path = resolve_flavor_path(manifest, template_id, flavor_id) or flavor_id
    template_path = Path(starters_path) / "templates" / template_id / flavor_path

    if not template_path.is_dir():
        print(
            f"Template not found: {template_id}/{flavor_id}\nPath: {template_path}",
            file=sys.stderr,
        )
        return 2

    copy_template(str(template_path), target_dir)
    substitute_in_directory(target_dir, build_substitutions(project_name))
    ensure_env_files(str(template_path), target_dir)
    ensure_gitignore_entries(target_dir)

    if manifest:
        next_steps = resolve_next_steps(manifest, template_id, flavor_id)
        _print_next_steps(next_steps, target_dir)

    print(f"\nProject created at {Path(target_dir).resolve()}\n")
    return 0


def _run_init_github(
    repo: str, ref: str, target_dir: str, args: argparse.Namespace
) -> int:
    try:
        with GitHubArchive(repo, ref) as archive:
            try:
                manifest = archive.load_manifest()
            except Exception as exc:  # noqa: BLE001
                print(f"Failed to load starters manifest: {exc}", file=sys.stderr)
                return 2

            if args.list:
                from naylence.starters.manifest import list_templates_from_manifest

                template_infos = list_templates_from_manifest(".", manifest, check_paths=False)
                print(format_template_list(template_infos))
                return 0

            template_id = args.template or _prompt_choice(
                "Select a template:", [template.id for template in manifest.templates], force_prompt=True
            )
            if not template_id:
                print("No template selected.", file=sys.stderr)
                return 2

            entry = next((item for item in manifest.templates if item.id == template_id), None)
            if not entry:
                print(f"Template not found: {template_id}", file=sys.stderr)
                return 2

            try:
                flavor_id = select_flavor(entry, args.flavor, default_flavor="py")
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            if not flavor_id:
                print("No flavor selected.", file=sys.stderr)
                return 2

            flavor_path = resolve_flavor_path(manifest, template_id, flavor_id) or flavor_id

            project_name = get_project_name(target_dir)
            ensure_target_dir(target_dir, args.no_overwrite)

            with tempfile.TemporaryDirectory() as tmpdir:
                template_path = f"templates/{template_id}/{flavor_path}"
                try:
                    archive.extract_template_to_dir(template_path, tmpdir)
                except Exception as exc:  # noqa: BLE001
                    print(f"Failed to extract template: {exc}", file=sys.stderr)
                    return 2

                copy_template(tmpdir, target_dir)
                substitute_in_directory(target_dir, build_substitutions(project_name))
                ensure_env_files(tmpdir, target_dir)
                ensure_gitignore_entries(target_dir)

            next_steps = resolve_next_steps(manifest, template_id, flavor_id)
            _print_next_steps(next_steps, target_dir)

        print(f"\nProject created at {Path(target_dir).resolve()}\n")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to fetch starters from GitHub: {exc}", file=sys.stderr)
        return 2


def select_flavor(
    template: object,
    requested_flavor: str | None,
    default_flavor: str = "py",
) -> str | None:
    flavors = getattr(template, "flavors", None)
    if not flavors:
        raise ValueError("No flavors available for the selected template.")

    if flavors and not isinstance(flavors[0], str):
        flavors = [flavor.id for flavor in flavors]

    if requested_flavor:
        if requested_flavor not in flavors:
            raise ValueError(
                f"Flavor not found: {requested_flavor}. Use --list to see available templates."
            )
        return requested_flavor

    if default_flavor in flavors:
        return default_flavor
    if len(flavors) == 1:
        return flavors[0]

    return _prompt_choice("Select a flavor:", flavors)


def _prompt_choice(
    title: str, options: Iterable[str], force_prompt: bool = False
) -> str | None:
    options = [opt for opt in options if opt]
    if not options:
        return None
    if len(options) == 1 and not force_prompt:
        return options[0]

    print(title)
    for index, option in enumerate(options, start=1):
        print(f"  {index}. {option}")

    while True:
        choice = input("Enter a number: ").strip()
        if not choice:
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("Invalid choice, try again.")


def _print_next_steps(next_steps: list[str] | None, target_dir: str) -> None:
    if not next_steps:
        return
    print("Next steps:")
    print(f"  cd {target_dir}")
    for step in next_steps:
        print(f"  {step}")
