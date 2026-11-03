from iac_converter.diagnostics import Diagnostic, DiagnosticSeverity


def test_diagnostic_with_all_fields():
    diagnostic = Diagnostic(
        code="TF001",
        severity=DiagnosticSeverity.ERROR,
        message="Invalid Terraform syntax",
        file_path="modules/vpc/main.tf",
        line=10,
        column=5,
        suggestion="Check the expression syntax.",
    )

    assert diagnostic.code == "TF001"
    assert diagnostic.severity == DiagnosticSeverity.ERROR
    assert diagnostic.message == "Invalid Terraform syntax"
    assert diagnostic.file_path == "modules/vpc/main.tf"
    assert diagnostic.line == 10
    assert diagnostic.column == 5
    assert diagnostic.suggestion == "Check the expression syntax."


def test_diagnostic_without_optional_fields():
    diagnostic = Diagnostic(
        code="TF002",
        severity=DiagnosticSeverity.WARNING,
        message="Potentially unsupported syntax",
    )

    assert diagnostic.file_path is None
    assert diagnostic.line is None
    assert diagnostic.column is None
    assert diagnostic.suggestion is None


def test_diagnostic_severity_values():
    assert DiagnosticSeverity.ERROR.value == "error"
    assert DiagnosticSeverity.WARNING.value == "warning"
    assert DiagnosticSeverity.INFO.value == "info"
