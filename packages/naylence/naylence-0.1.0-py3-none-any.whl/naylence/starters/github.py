from __future__ import annotations

import os
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from naylence.starters.manifest import parse_manifest
from naylence.starters.models import TemplateManifest


class GitHubArchive:
    def __init__(self, repo: str, ref: str) -> None:
        self.repo = repo
        self.ref = ref
        self._archive_path: Optional[Path] = None
        self._root_prefix: Optional[str] = None

    def __enter__(self) -> "GitHubArchive":
        self._archive_path = self._download_archive()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._archive_path and self._archive_path.exists():
            try:
                self._archive_path.unlink()
            except OSError:
                pass

    def load_manifest(self) -> TemplateManifest:
        tar = self._open_tar()
        try:
            member = self._find_member(tar, suffix="templates/manifest.json")
            if not member:
                raise FileNotFoundError("templates/manifest.json not found in archive")
            file_obj = tar.extractfile(member)
            if not file_obj:
                raise FileNotFoundError("Unable to read manifest from archive")
            raw = file_obj.read().decode("utf-8")
            return parse_manifest(raw, f"github:{self.repo}@{self.ref}")
        finally:
            tar.close()

    def extract_template_to_dir(self, template_path: str, dest_dir: str) -> str:
        tar = self._open_tar()
        try:
            root_prefix = self._get_root_prefix(tar)
            prefix = f"{root_prefix}/{template_path.strip('/')}"
            extracted_any = False

            for member in tar.getmembers():
                if not member.name.startswith(prefix):
                    continue
                relative = member.name[len(prefix) :].lstrip("/")
                if not relative:
                    continue

                if Path(relative).is_absolute() or ".." in Path(relative).parts:
                    continue

                dest_path = Path(dest_dir) / relative
                if member.isdir():
                    dest_path.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        with dest_path.open("wb") as handle:
                            handle.write(file_obj.read())
                    extracted_any = True

            if not extracted_any:
                raise FileNotFoundError(
                    f"Template path not found in archive: {template_path}"
                )

            return dest_dir
        finally:
            tar.close()

    def _download_archive(self) -> Path:
        url = f"https://codeload.github.com/{self.repo}/tar.gz/{self.ref}"
        with urllib.request.urlopen(url) as response:
            data = response.read()

        fd, path = tempfile.mkstemp(suffix=".tar.gz")
        os.close(fd)
        archive_path = Path(path)
        archive_path.write_bytes(data)
        return archive_path

    def _open_tar(self) -> tarfile.TarFile:
        if not self._archive_path:
            raise RuntimeError("Archive not downloaded")
        return tarfile.open(self._archive_path, mode="r:gz")

    def _find_member(self, tar: tarfile.TarFile, suffix: str) -> Optional[tarfile.TarInfo]:
        for member in tar.getmembers():
            if member.isfile() and member.name.endswith(suffix):
                return member
        return None

    def _get_root_prefix(self, tar: tarfile.TarFile) -> str:
        if self._root_prefix:
            return self._root_prefix
        for member in tar.getmembers():
            parts = member.name.split("/", 1)
            if parts:
                self._root_prefix = parts[0]
                return self._root_prefix
        raise FileNotFoundError("Archive is empty")
