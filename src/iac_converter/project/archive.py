from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from iac_converter.project.project import Project, ProjectFile


class ProjectArchiveError(ValueError):
    """Raised when a project archive cannot be read or written."""


MAX_ARCHIVE_FILES = 1_000
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 100 * 1024 * 1024


def save_project_zip(
    project: Project,
    path: str | Path,
) -> None:
    """
    Save a Project as a ZIP archive.

    ProjectFile paths are stored relative to the archive root.
    """
    archive_path = Path(path).expanduser()

    try:
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        with ZipFile(
            archive_path,
            mode="w",
            compression=ZIP_DEFLATED,
        ) as archive:
            seen_paths: set[str] = set()

            for project_file in project.files:
                relative_path = project_file.path.replace("\\", "/")

                if not relative_path:
                    raise ProjectArchiveError("Project file path cannot be empty.")

                if relative_path in seen_paths:
                    raise ProjectArchiveError(f"Duplicate project file path: {relative_path}")

                seen_paths.add(relative_path)

                if _is_unsafe_archive_path(relative_path):
                    raise ProjectArchiveError(f"Project file path is unsafe: {project_file.path}")

                archive.writestr(
                    relative_path,
                    project_file.content,
                )

    except ProjectArchiveError:
        raise
    except OSError as exc:
        raise ProjectArchiveError(
            f"Failed to create project archive '{archive_path}': {exc}"
        ) from exc


def load_project_zip(
    path: str | Path,
) -> Project:
    """
    Load a Project from a ZIP archive with resource limits.
    """
    archive_path = Path(path).expanduser()

    if not archive_path.exists():
        raise ProjectArchiveError(f"Project archive does not exist: {archive_path}")

    if not archive_path.is_file():
        raise ProjectArchiveError(f"Project archive path is not a file: {archive_path}")

    try:
        with ZipFile(archive_path, mode="r") as archive:
            entries = [info for info in archive.infolist() if not info.is_dir()]

            if len(entries) > MAX_ARCHIVE_FILES:
                raise ProjectArchiveError(
                    f"Project archive contains too many files (maximum {MAX_ARCHIVE_FILES})."
                )

            files: list[ProjectFile] = []
            seen_paths: set[str] = set()
            declared_total_size = 0
            actual_total_size = 0

            for info in entries:
                relative_path = info.filename.replace("\\", "/")

                if _is_unsafe_archive_path(relative_path):
                    raise ProjectArchiveError(
                        f"Project archive contains unsafe path: {info.filename}"
                    )

                if relative_path in seen_paths:
                    raise ProjectArchiveError(
                        f"Project archive contains duplicate path: {relative_path}"
                    )

                seen_paths.add(relative_path)

                if info.file_size > MAX_FILE_SIZE:
                    raise ProjectArchiveError(
                        f"Project archive file exceeds the 10 MB limit: {info.filename}"
                    )

                declared_total_size += info.file_size

                if declared_total_size > MAX_TOTAL_SIZE:
                    raise ProjectArchiveError(
                        "Project archive exceeds the 100 MB total uncompressed size limit."
                    )

                chunks: list[bytes] = []
                actual_file_size = 0

                with archive.open(info, mode="r") as source:
                    while True:
                        remaining_file = MAX_FILE_SIZE - actual_file_size
                        remaining_total = MAX_TOTAL_SIZE - actual_total_size

                        read_size = min(
                            64 * 1024,
                            remaining_file + 1,
                            remaining_total + 1,
                        )

                        chunk = source.read(read_size)

                        if not chunk:
                            break

                        actual_file_size += len(chunk)
                        actual_total_size += len(chunk)

                        if actual_file_size > MAX_FILE_SIZE:
                            raise ProjectArchiveError(
                                f"Project archive file exceeds the 10 MB limit: {info.filename}"
                            )

                        if actual_total_size > MAX_TOTAL_SIZE:
                            raise ProjectArchiveError(
                                "Project archive exceeds the 100 MB total uncompressed size limit."
                            )

                        chunks.append(chunk)

                try:
                    content = b"".join(chunks).decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ProjectArchiveError(
                        f"Project archive file is not valid UTF-8: {info.filename}"
                    ) from exc

                files.append(
                    ProjectFile(
                        path=relative_path,
                        content=content,
                    )
                )

    except ProjectArchiveError:
        raise
    except BadZipFile as exc:
        raise ProjectArchiveError(f"Invalid ZIP project archive: {archive_path}") from exc
    except OSError as exc:
        raise ProjectArchiveError(
            f"Failed to read project archive '{archive_path}': {exc}"
        ) from exc

    files.sort(key=lambda project_file: project_file.path)

    return Project(files=files)


def _is_unsafe_archive_path(path: str) -> bool:
    """
    Return True if a ZIP entry can escape the project root.
    """
    normalized = path.replace("\\", "/")

    if normalized.startswith("/"):
        return True

    if Path(normalized).drive:
        return True

    parts = normalized.split("/")

    return ".." in parts
