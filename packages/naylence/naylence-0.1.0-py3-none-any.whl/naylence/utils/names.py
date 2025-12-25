from __future__ import annotations

import os
import re


def to_package_name(name: str) -> str:
    name = re.sub(r"\s+", "-", name.lower())
    name = name.replace("_", "-")
    name = re.sub(r"[^a-z0-9-@/]", "", name)
    name = re.sub(r"^[^a-z@]", "", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def to_python_package(name: str) -> str:
    name = re.sub(r"\s+", "_", name.lower())
    name = name.replace("-", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"^[^a-z]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def get_project_name(target_dir: str) -> str:
    return os.path.basename(os.path.abspath(target_dir))


def resolve_starters_path(cli_path: str | None = None) -> str | None:
    if cli_path:
        return os.path.abspath(cli_path)
    env_path = os.environ.get("NAYLENCE_STARTERS_PATH")
    if env_path:
        return os.path.abspath(env_path)
    return None


def resolve_github_repo() -> str:
    return os.environ.get("NAYLENCE_STARTERS_GITHUB", "naylence/naylence-starters")


def resolve_git_ref(cli_ref: str | None = None) -> str:
    if cli_ref:
        return cli_ref
    return os.environ.get("NAYLENCE_STARTERS_REF", "main")
