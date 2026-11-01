from __future__ import annotations

from dataclasses import dataclass

from iac_converter.ir.model import ProjectIR


@dataclass
class ProjectFileIR:
    """Intermediate representation of one file in an IaC project."""

    path: str
    project: ProjectIR
