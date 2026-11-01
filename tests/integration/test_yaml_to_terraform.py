from iac_converter.generator.terraform import generate_terraform
from iac_converter.parser.yaml_parser import parse_yaml


def test_yaml_to_terraform():

    source = """
version: "1"

terraform:
  required_version: ">= 1.6.0"

providers:
  aws:
    properties:
      region: ap-south-1

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data
      tags:
        Environment: dev
        Owner: sreenu
"""

    project = parse_yaml(source)

    terraform = generate_terraform(project)

    assert "terraform {" in terraform
    assert 'required_version = ">= 1.6.0"' in terraform

    assert 'provider "aws" {' in terraform
    assert 'region = "ap-south-1"' in terraform

    assert 'resource "aws_s3_bucket" "data" {' in terraform
    assert 'bucket = "company-data"' in terraform


def test_yaml_to_terraform_reference():

    source = """
resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data

  - type: aws_s3_bucket_policy
    name: policy
    properties:
      bucket:
        reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
"""

    project = parse_yaml(source)

    terraform = generate_terraform(project)

    assert "bucket = aws_s3_bucket.data.id" in terraform


def test_yaml_to_terraform_expression():

    source = """
variables:
  - name: bucket_name
    type: string
    default: company-data

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket:
        expression: var.bucket_name
"""

    project = parse_yaml(source)

    terraform = generate_terraform(project)

    assert "type = string" in terraform
    assert 'default = "company-data"' in terraform
    assert "bucket = var.bucket_name" in terraform


def test_yaml_nested_map_preserves_reference_and_function_call():
    source = """
resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data

outputs:
  - name: settings
    value:
      bucket_id:
        reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
      normalized_name:
        expression: lower("MY-BUCKET")
"""

    project = parse_yaml(source)
    terraform = generate_terraform(project)

    assert "aws_s3_bucket.data.id" in terraform
    assert 'lower("MY-BUCKET")' in terraform

    # Expressions must not be rendered as quoted strings.
    assert '"aws_s3_bucket.data.id"' not in terraform
    assert '"lower(\\"MY-BUCKET\\")"' not in terraform


def test_yaml_module_to_terraform():
    source = """
version: "1"
modules:
  - name: vpc
    source: ./modules/vpc
    arguments:
      cidr_block: 10.0.0.0/16
      environment: production
"""

    project = parse_yaml(source)
    terraform = generate_terraform(project)

    assert 'module "vpc" {' in terraform
    assert 'source = "./modules/vpc"' in terraform
    assert 'cidr_block = "10.0.0.0/16"' in terraform
    assert 'environment = "production"' in terraform


def test_yaml_module_meta_arguments_to_terraform():
    source = """
modules:
  - name: vpc
    source: ./modules/vpc
    count:
      expression: "var.create_vpc ? 1 : 0"
    depends_on:
      - expression: "aws_s3_bucket.data"
"""

    project = parse_yaml(source)
    terraform = generate_terraform(project)

    assert 'module "vpc" {' in terraform
    assert 'source = "./modules/vpc"' in terraform
    assert "count = var.create_vpc ? 1 : 0" in terraform
    assert "depends_on = [aws_s3_bucket.data]" in terraform
