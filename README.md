# IAC Converter

A bidirectional YAML and Terraform infrastructure-as-code converter.

## Features

- Convert YAML configuration into Terraform files.
- Convert Terraform projects into YAML.
- Convert YAML project configurations into Terraform project directories.
- Convert Terraform project directories into YAML.
- Validate input paths and handle conversion errors.
- Provide a command-line interface.

## Requirements

- Python 3.11 or newer.

## Installation

Clone the repository and navigate to the project directory:

```powershell
git clone <repository-url>
cd iac-tool
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
python -m pip install -e .
```

For development:

```powershell
python -m pip install -e ".[dev]"
```

## CLI Usage

Display the version:

```powershell
iac-converter --version
```

Display help:

```powershell
iac-converter --help
```

### YAML to Terraform

Convert one YAML file into one Terraform file:

```powershell
iac-converter yaml-to-terraform input.yaml -o output.tf
```

### Terraform to YAML

Convert a Terraform project directory into YAML:

```powershell
iac-converter terraform-to-yaml ./terraform-project -o output.yaml
```

### YAML project to Terraform project

```powershell
iac-converter yaml-project-to-terraform project.yaml -o ./terraform-output
```

### Terraform project to YAML

```powershell
iac-converter terraform-project-to-yaml ./terraform-project -o output.yaml
```

## CLI Options

- `--version`: Display the installed version.
- `--help`: Display command help.
- `--verbose`: Display detailed conversion information.
- `--quiet`: Suppress successful conversion messages.

`--verbose` and `--quiet` cannot be used together.

## Development and Testing

Run the test suite:

```powershell
python -m pytest
```

Run Ruff linting:

```powershell
python -m ruff check .
```

Check formatting:

```powershell
python -m ruff format --check .
```

Run type checking:

```powershell
python -m mypy src
```

## License

License information has not yet been specified.
