from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectFile:
    path: str
    content: str


@dataclass
class Project:
    files: list[ProjectFile] = field(default_factory=list)

    def terraform_files(self) -> list[ProjectFile]:
        """Return Terraform files in the project."""
        return [
            project_file for project_file in self.files if project_file.path.lower().endswith(".tf")
        ]
