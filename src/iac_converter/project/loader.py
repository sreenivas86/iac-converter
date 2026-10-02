from __future__ import annotations

from pathlib import Path

from iac_converter.project.project import Project, ProjectFile


class ProjectLoadError(ValueError):
    """Raised when a project cannot be loaded from disk."""


def load_project(path: str | Path) -> Project:
    """
    Load a project directory into a Project.

    All files are loaded recursively.

    Filesystem paths are handled using pathlib, so this works on
    Linux, Windows, and macOS.

    Paths stored in ProjectFile are relative to the project root
    and always use forward slashes.
    """

    root = Path(path).expanduser()

    if not root.exists():
        raise ProjectLoadError(
            f"Project path does not exist: {root}"
        )

    if not root.is_dir():
        raise ProjectLoadError(
            f"Project path is not a directory: {root}"
        )

    files: list[ProjectFile] = []

    file_paths = [
        file_path
        for file_path in root.rglob("*")
        if file_path.is_file()
    ]

    file_paths.sort(
        key=lambda file_path: file_path.relative_to(root).as_posix()
    )

    for file_path in file_paths:
        relative_path = file_path.relative_to(root).as_posix()

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectLoadError(
                f"Project file is not valid UTF-8: {relative_path}"
            ) from exc
        except OSError as exc:
            raise ProjectLoadError(
                f"Failed to read project file '{relative_path}': {exc}"
            ) from exc

        files.append(
            ProjectFile(
                path=relative_path,
                content=content,
            )
        )

    return Project(files=files)