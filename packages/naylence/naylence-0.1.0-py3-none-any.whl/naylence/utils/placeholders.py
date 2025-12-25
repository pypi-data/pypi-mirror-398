from __future__ import annotations

from pathlib import Path

from naylence.utils.fs import is_binary_file
from naylence.utils.names import to_package_name, to_python_package

PLACEHOLDERS = {
    "__PROJECT_NAME__": "project_name",
    "__PACKAGE_NAME__": "package_name",
    "__PY_PACKAGE__": "py_package",
}


def build_substitutions(project_name: str) -> dict[str, str]:
    return {
        "__PROJECT_NAME__": project_name,
        "__PACKAGE_NAME__": to_package_name(project_name),
        "__PY_PACKAGE__": to_python_package(project_name),
    }


def substitute_in_directory(dir_path: str, substitutions: dict[str, str]) -> None:
    root = Path(dir_path)
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in {"node_modules", ".git"}:
                continue
            continue
        if not path.is_file():
            continue
        substitute_in_file(path, substitutions)


def substitute_in_file(path: Path, substitutions: dict[str, str]) -> None:
    if is_binary_file(str(path)):
        return
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return

    modified = False
    for placeholder, value in substitutions.items():
        if placeholder in content:
            content = content.replace(placeholder, value)
            modified = True

    if modified:
        path.write_text(content, encoding="utf-8")
