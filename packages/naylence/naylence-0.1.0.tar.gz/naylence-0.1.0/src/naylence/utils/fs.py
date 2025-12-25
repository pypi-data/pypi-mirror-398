from __future__ import annotations

import os
import shutil
from pathlib import Path

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".pdf",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".node",
    ".wasm",
}

EXCLUDE_DIRS = {".git", "node_modules", "dist", ".tmp", "__pycache__", ".venv", "venv"}
EXCLUDE_FILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", ".env"}


def ensure_target_dir(target_dir: str, no_overwrite: bool) -> None:
    path = Path(target_dir)
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"Target path exists but is not a directory: {target_dir}")
        if no_overwrite:
            contents = list(path.iterdir())
            if contents:
                raise ValueError(
                    "Target directory is not empty: "
                    f"{target_dir}\nPlease choose an empty directory or a new path."
                )
    else:
        path.mkdir(parents=True, exist_ok=True)


def is_binary_file(path: str) -> bool:
    return Path(path).suffix.lower() in BINARY_EXTENSIONS


def copy_template(src: str, dest: str) -> None:
    src_path = Path(src)
    dest_path = Path(dest)
    if not src_path.is_dir():
        raise ValueError(f"Template path is not a directory: {src}")

    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        rel_parts = Path(rel_root).parts if rel_root != "." else ()

        if any(part in EXCLUDE_DIRS for part in rel_parts):
            dirs[:] = []
            continue

        dest_root = dest_path / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)

        for name in list(dirs):
            if name in EXCLUDE_DIRS:
                dirs.remove(name)

        for filename in files:
            src_file = Path(root) / filename
            rel_file = Path(os.path.relpath(src_file, src))
            if len(rel_file.parts) == 1 and filename in EXCLUDE_FILES:
                continue
            if filename.startswith(".env.") and filename.endswith(".template"):
                continue

            dest_file = dest_path / rel_file
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)


def ensure_env_files(template_dir: str, dest_dir: str) -> None:
    for name in ("agent", "client"):
        template_path = Path(template_dir) / f".env.{name}.template"
        out_path = Path(dest_dir) / f".env.{name}"
        if out_path.exists():
            continue
        if template_path.exists():
            shutil.copy2(template_path, out_path)


def ensure_gitignore_entries(dest_dir: str) -> None:
    gitignore_path = Path(dest_dir) / ".gitignore"
    entries = [".env.agent", ".env.client"]

    if not gitignore_path.exists():
        gitignore_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
        return

    content = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    existing = {line for line in lines if line}
    missing = [entry for entry in entries if entry not in existing]
    if not missing:
        return

    separator = "" if content.endswith("\n") else "\n"
    updated = f"{content}{separator}{'\n'.join(missing)}\n"
    gitignore_path.write_text(updated, encoding="utf-8")
