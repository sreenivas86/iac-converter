# Example 1: AWS S3 Bucket

This example demonstrates bidirectional YAML and Terraform conversion using `iac-converter`.

## Files

- `main.yaml` - YAML representation of the S3 bucket.
- `main.tf` - Equivalent Terraform configuration.
- `.terraform.lock.hcl` - Provider dependency lock file.

## Prerequisites

- Python 3.11 or later
- `iac-converter`
- Terraform CLI

Install the converter with:

`python -m pip install iac-converter`

## 1. YAML to Terraform

Run from the repository root:

`python -m iac_converter.cli yaml-to-terraform .\examples\guides\aws\01-s3-bucket\main.yaml -o .\examples\guides\aws\01-s3-bucket-conversion\generated.tf`

## 2. Terraform to YAML

`python -m iac_converter.cli terraform-to-yaml .\examples\guides\aws\01-s3-bucket-conversion -o .\examples\guides\aws\01-s3-bucket-output.yaml`

## 3. Format and validate Terraform

`python -m iac_converter.cli validate .\examples\guides\aws\01-s3-bucket-validation --tool terraform --check-format`

The validation checks Terraform initialization, configuration validity, and formatting.

## Important notes

- Replace `replace-with-your-unique-bucket-name` with a globally unique S3 bucket name before deploying.
- Validation does not deploy infrastructure.
- Do not include Terraform `.terraform` directories in conversion input directories. They contain downloaded provider binaries.
- Keep duplicate Terraform resource declarations out of the same validation directory.
- The conversion and validation directories above are separate test workspaces.
- AWS credentials are not needed merely to validate this configuration.