# IAC Converter

**IAC Converter** is a bidirectional Infrastructure as Code (IaC) conversion tool that converts YAML configurations into Terraform configurations and Terraform configurations back into YAML.

It supports single-file conversion, multi-file projects, nested Terraform modules, and Terraform/OpenTofu validation.

---

## 1. Features

- YAML to Terraform conversion.
- Terraform to YAML conversion.
- Single-file configuration conversion.
- Multi-file project conversion.
- Preservation of project directory structures.
- Nested Terraform module support.
- Module variables, outputs, and module references.
- Terraform and OpenTofu validation.
- Unsupported syntax diagnostics.
- REST API using FastAPI.
- Command-line interface (CLI).
- Verbose and quiet execution modes.
- Input validation and error handling.

## 2. System Requirements

Install the following software before using IAC Converter.

| Software | Requirement | Purpose |
|---|---|---|
| Python | 3.11 or newer | Runs IAC Converter |
| pip | Current version recommended | Installs Python packages |
| Git | Recommended | Downloads the source code |
| Terraform | Recommended | Validates Terraform configurations |
| OpenTofu | Optional | Alternative IaC validator |

### 2.1 Install Python

Download Python from:

https://www.python.org/downloads/

During Windows installation:

1. Start the Python installer.
2. Enable **Add Python to PATH**.
3. Complete the installation.
4. Open PowerShell.
5. Verify the installation:

```powershell
python --version
```

Expected: Python 3.11 or newer.

Verify pip:

```powershell
python -m pip --version
```

### 2.2 Install Git

Download Git from:

https://git-scm.com/downloads

Verify:

```powershell
git --version
```

### 2.3 Install Terraform

Download Terraform from:

https://developer.hashicorp.com/terraform/install

Follow the installation instructions for Windows.

Verify:

```powershell
terraform version
```

Terraform is required when using the Terraform validation functionality.

### 2.4 Install OpenTofu (Optional)

Download OpenTofu from:

https://opentofu.org/docs/intro/install/

Verify:

```powershell
tofu version
```

IAC Converter can use Terraform or OpenTofu for project validation.

---

## 3. Install IAC Converter from PyPI

IAC Converter is published on the Python Package Index (PyPI). This is the recommended installation method for users who want to use the application without downloading or modifying its source code.

**PyPI project:** https://pypi.org/project/iac-converter/

### 3.1 Prerequisites

- Python 3.11 or newer.
- pip.
- An internet connection.

Verify Python and pip:

```powershell
python --version
python -m pip --version
```

### 3.2 Create a Virtual Environment

A virtual environment isolates IAC Converter's dependencies from other Python applications.

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, allow them for the current session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.3 Install from PyPI

Upgrade pip and install the published package:

```powershell
python -m pip install --upgrade pip
python -m pip install iac-converter
```

### 3.4 Verify the Installation

```powershell
python -m pip show iac-converter
python -m iac_converter.cli --version
python -m iac_converter.cli --help
```

For version `0.1.0`, the version command should display:

```text
iac-converter 0.1.0
```

You can now use IAC Converter. The examples in the CLI, validation, and API sections below use `python -m iac_converter.cli`, which avoids depending on a platform-specific console-script launcher.

### 3.5 Optional: Install Terraform or OpenTofu

Terraform and OpenTofu are not required for YAML/Terraform text conversion. Install one of them if you want to use IAC Converter's external validation command.

See Section 2.3 for Terraform installation and Section 2.4 for OpenTofu installation.

---

## 4. Install IAC Converter from GitHub Source

Use this method if you want to inspect, modify, test, or contribute to the source code. For normal use, install from PyPI as described in Section 3.

### 4.1 Clone the Repository

Repository:

https://github.com/sreenivas86/iac-converter

Open PowerShell and run:

```powershell
git clone https://github.com/sreenivas86/iac-converter.git
cd iac-converter
```

Verify the project structure:

```powershell
Get-ChildItem
```

The project should contain files and directories similar to:

```text
iac-converter/
├── src/
│   └── iac_converter/
├── tests/
├── examples/
├── README.md
├── pyproject.toml
└── .gitignore
```

### 4.2 Create and Activate a Virtual Environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4.3 Install the Source Project

For development, install the project in editable mode with its development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

This installs the application and development tools declared in `pyproject.toml`, including pytest, Ruff, MyPy, and httpx.

If you only want to install the source project without development tools, use:

```powershell
python -m pip install -e .
```

### 4.4 Verify the Source Installation

```powershell
python -m pip show iac-converter
python -m iac_converter.cli --version
python -m iac_converter.cli --help
```

The version command should display the version declared by the checked-out source.

### 4.5 Run Tests

After installing the development dependencies:

```powershell
python -m pytest
```

For linting, formatting, and type checking, see Section 13.

---

## 5. Install from a Built Distribution Package

This method is intended for users who have already obtained a wheel or source distribution file, for example from a GitHub Release or a locally built `dist` directory.

### 5.1 Install a Wheel

```powershell
python -m pip install .\dist\iac_converter-0.1.0-py3-none-any.whl
```

### 5.2 Install a Source Distribution

```powershell
python -m pip install .\dist\iac_converter-0.1.0.tar.gz
```

### 5.3 Verify the Installation

```powershell
python -m iac_converter.cli --version
```

For the `0.1.0` release, expected output is:

```text
iac-converter 0.1.0
```

For most users, the simpler PyPI installation in Section 3 is recommended.

---

## 6. YAML Configuration Format

IAC Converter uses YAML to represent Terraform configuration.

A simple YAML configuration looks like this:

```yaml
version: "1"
terraform:
  required_version: ">= 1.5.0"
providers:
  aws:
    properties:
      region: us-east-1
resources:
  - type: aws_s3_bucket
    name: example
    properties:
      bucket: example-bucket
```

The configuration contains:

- `version`: YAML configuration format version.
- `terraform`: Terraform configuration settings.
- `providers`: Provider configurations.
- `resources`: Terraform resources and their properties.

The converter translates these YAML definitions into Terraform configuration.

---

## 7. Command-Line Interface

IAC Converter provides four main conversion commands and one validation command.

### 7.1 Display Application Version

```powershell
python -m iac_converter.cli --version
```

### 7.2 Display Help

```powershell
python -m iac_converter.cli --help
```

To see command-specific help:

```powershell
python -m iac_converter.cli yaml-project-to-terraform --help
```

### 7.3 YAML File to Terraform File

Convert a single YAML file:

```powershell
python -m iac_converter.cli yaml-to-terraform input.yaml -o output.tf
```

Example:

```powershell
python -m iac_converter.cli yaml-to-terraform .\examples\aws\s3-bucket.yaml -o .\output.tf
```

The generated Terraform file contains the corresponding Terraform configuration.

### 7.4 Terraform Project to YAML File

Convert a Terraform project directory into one YAML file:

```powershell
python -m iac_converter.cli terraform-to-yaml .\terraform-project -o .\output.yaml
```

### 7.5 YAML Project to Terraform Project

Convert a YAML project file or directory into a Terraform project directory:

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\yaml-project -o .\terraform-output
```

For example:

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\examples\aws\nested-module-test-yaml -o .\terraform-output
```

The converter preserves the project directory structure and generates corresponding `.tf` files.

### 7.6 Terraform Project to YAML Project

Convert a Terraform project directory into a YAML project directory:

```powershell
python -m iac_converter.cli terraform-project-to-yaml .\terraform-project -o .\yaml-output
```

To generate a single YAML document instead:

```powershell
python -m iac_converter.cli terraform-project-to-yaml .\terraform-project -o .\output.yaml
```

---

## 8. Working with Multiple Files and Terraform Modules

IAC Converter supports multi-file projects and nested module directories.

Example YAML project:

```text
yaml-project/
│
├── main.yaml
├── variables.yaml
├── outputs.yaml
│
└── modules/
    └── vpc/
        └── main.yaml
```

The corresponding Terraform project:

```text
terraform-project/
│
├── main.tf
├── variables.tf
├── outputs.tf
│
└── modules/
    └── vpc/
        └── main.tf
```

The converter preserves the relative directory structure when converting between YAML and Terraform project directories.

### 8.1 Example Module Configuration

Root YAML configuration:

```yaml
version: "1"
terraform:
  required_version: ">= 1.5.0"
providers:
  aws:
    properties:
      region: ap-south-1
modules:
  - name: vpc
    source: ./modules/vpc
    arguments:
      cidr_block: "10.0.0.0/16"
      environment: production
```

Module YAML configuration:

```yaml
version: "1"
variables:
  - name: cidr_block
    type: string
  - name: environment
    type: string
resources:
  - type: aws_vpc
    name: main
    properties:
      cidr_block:
        expression: var.cidr_block
outputs:
  - name: vpc_id
    value:
      expression: aws_vpc.main.id
```

Convert the complete project:

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\yaml-project -o .\terraform-project
```

---

## 9. Terraform and OpenTofu Validation

IAC Converter provides a validation command to initialize and validate Terraform or OpenTofu projects.

### 9.1 Automatic Tool Detection

```powershell
python -m iac_converter.cli validate .\terraform-project
```

The `auto` mode detects an available validation tool.

### 9.2 Validate with Terraform

```powershell
python -m iac_converter.cli validate .\terraform-project --tool terraform
```

### 9.3 Validate with OpenTofu

```powershell
python -m iac_converter.cli validate .\terraform-project --tool tofu
```

### 9.4 Skip Initialization

```powershell
python -m iac_converter.cli validate .\terraform-project --skip-init
```

Use this when you want to skip the initialization step.

### 9.5 Check Terraform Formatting

```powershell
python -m iac_converter.cli validate .\terraform-project --check-format
```

### 9.6 Verbose Validation

```powershell
python -m iac_converter.cli validate .\terraform-project --verbose
```

---

## 10. CLI Logging Options

The conversion commands support verbose and quiet modes.

### Default Mode

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\yaml-project -o .\terraform-output
```

Displays a successful conversion message.

### Verbose Mode

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\yaml-project -o .\terraform-output --verbose
```

Displays additional execution information, including the command name and output location.

### Quiet Mode

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\yaml-project -o .\terraform-output --quiet
```

Suppresses successful conversion messages.

Errors are still displayed in quiet mode.

The `--verbose` and `--quiet` options cannot be used together.

---

## 11. REST API

IAC Converter also provides a REST API built using FastAPI.

### 11.1 Start the API Server

Activate the Python virtual environment and execute:

```powershell
python -m uvicorn iac_converter.api.app:app --reload
```

The API server runs locally at:

```text
http://127.0.0.1:8000
```

### 11.2 API Documentation

Open the interactive API documentation in your browser:

```text
http://127.0.0.1:8000/docs
```

### 11.3 Available API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/convert/yaml-to-terraform` | YAML to Terraform |
| POST | `/convert/terraform-to-yaml` | Terraform to YAML |

The API also provides ZIP-based project conversion and single-file upload endpoints.

Use the interactive Swagger documentation at `/docs` to inspect request formats and test the available endpoints.

To stop the API server, press:

```text
Ctrl + C
```

---

## 12. Troubleshooting

### Python is not recognized

Check Python installation:

```powershell
python --version
```

If Python is not recognized, install Python and enable the PATH option in the installer.

### Virtual environment activation is blocked

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

### ModuleNotFoundError

Make sure your virtual environment is activated. Then install or upgrade IAC Converter from PyPI:

```powershell
python -m pip install --upgrade iac-converter
```

### iac-converter command is not recognized

Use the Python module invocation:

```powershell
python -m iac_converter.cli --help
```

Confirm that the virtual environment is activated.

### Terraform is not recognized

Check:

```powershell
terraform version
```

Install Terraform and make sure its executable is available through PATH.

### Conversion fails

Use verbose mode:

```powershell
python -m iac_converter.cli yaml-project-to-terraform .\yaml-project -o .\terraform-output --verbose
```

Check the input file or directory, YAML syntax, and the error message.

### Terraform validation fails

Run Terraform initialization:

```powershell
terraform -chdir=.\terraform-project init
```

Then validate:

```powershell
terraform -chdir=.\terraform-project validate
```

---

## 13. Development and Testing

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

### Run All Tests

```powershell
python -m pytest -q
```

### Run Ruff Lint

```powershell
python -m ruff check .
```

### Check Formatting

```powershell
python -m ruff format --check .
```

### Run MyPy

```powershell
python -m mypy src
```

---

## 14. Build Distribution Packages

Install the build tool:

```powershell
python -m pip install build
```

Build the source distribution and wheel:

```powershell
python -m build
```

Generated packages are stored in:

```text
dist/
├── iac_converter-0.1.0.tar.gz
└── iac_converter-0.1.0-py3-none-any.whl
```

---

## 15. License

IAC Converter is licensed under the **Apache License, Version 2.0**.

You are permitted to:

- Use IAC Converter for personal and commercial purposes.
- Modify the source code.
- Distribute original or modified versions.
- Include IAC Converter in commercial products.
- Keep your own modifications private.

When redistributing the software, you must comply with the Apache License 2.0 conditions, including retaining applicable copyright, patent, trademark and attribution notices and providing a copy of the license.

Apache License 2.0 also provides an explicit patent license subject to its terms.

**License:** [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)

The complete license text is available in the [`LICENSE`](LICENSE) file in the project root.

Copyright and licensing rights remain subject to applicable law and the ownership of the contributions.
