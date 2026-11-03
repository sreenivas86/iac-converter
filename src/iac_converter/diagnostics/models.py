from dataclasses import dataclass
from enum import Enum


class DiagnosticSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Diagnostic:
    """Structured diagnostic information for IaC conversion."""

    code: str
    severity: DiagnosticSeverity
    message: str
    file_path: str | None = None
    line: int | None = None
    column: int | None = None
    suggestion: str | None = None
