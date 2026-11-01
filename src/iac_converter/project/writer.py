from __future__ import annotations

from pathlib import Path

from iac_converter.project.project import Project


class ProjectWriteError(ValueError):
    """Raised when a project cannot be written to disk."""


def save_project(project: Project, path: str | Path) -> None:
    """
    Save a Project to a directory.

    ProjectFile paths are relative to the project root and are stored
    using forward slashes. The implementation works on Windows,
    Linux, and macOS.
    """

    root = Path(path).expanduser()

    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ProjectWriteError(f"Failed to create project directory '{root}': {exc}") from exc

    if not root.is_dir():
        raise ProjectWriteError(f"Project path is not a directory: {root}")

    seen_paths: set[str] = set()

    for project_file in project.files:
        relative_path = project_file.path.replace("\\", "/")

        if not relative_path:
            raise ProjectWriteError("Project file path cannot be empty.")

        if relative_path in seen_paths:
            raise ProjectWriteError(f"Duplicate project file path: {relative_path}")

        seen_paths.add(relative_path)

        relative = Path(relative_path)

        if relative.is_absolute():
            raise ProjectWriteError(f"Project file path must be relative: {project_file.path}")

        target = (root / relative).resolve()

        try:
            target.relative_to(root.resolve())
        except ValueError as exc:
            raise ProjectWriteError(
                f"Project file path escapes project directory: {project_file.path}"
            ) from exc

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                project_file.content,
                encoding="utf-8",
            )
        except OSError as exc:
            raise ProjectWriteError(
                f"Failed to write project file '{relative_path}': {exc}"
            ) from exc
