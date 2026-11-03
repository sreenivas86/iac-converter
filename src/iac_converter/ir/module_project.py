from __future__ import annotations

from dataclasses import dataclass, field

from iac_converter.ir.model import ProjectIR
from iac_converter.ir.project_file import ProjectFileIR


@dataclass
class ModuleProjectIR:
    """Intermediate representation of a Terraform module directory."""

    path: str
    project: ProjectIR = field(default_factory=ProjectIR)
    files: list[ProjectFileIR] = field(default_factory=list)
    child_modules: list[ModuleProjectIR] = field(default_factory=list)
