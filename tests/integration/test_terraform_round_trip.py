from iac_converter.compiler.terraform_to_ir import parse_terraform
from iac_converter.generator.terraform import generate_terraform
from iac_converter.ir import RawExpression, Reference
from iac_converter.parser.yaml_parser import parse_yaml


def test_yaml_terraform_round_trip_preserves_nested_block() -> None:
    yaml_source = """
version: "1"

providers:
  aws:
    properties:
      region: us-east-1

resources:
  - type: aws_security_group
    name: web
    properties:
      name: web-sg
    blocks:
      - type: ingress
        properties:
          from_port: 443
          to_port: 443
          protocol: tcp
          cidr_blocks:
            - "0.0.0.0/0"
"""

    original_ir = parse_yaml(yaml_source)

    terraform_source = generate_terraform(original_ir)

    round_trip_ir = parse_terraform(terraform_source)

    assert len(round_trip_ir.resources) == 1

    resource = round_trip_ir.resources[0]

    assert resource.type == "aws_security_group"
    assert resource.name == "web"

    assert len(resource.blocks) == 1

    ingress = resource.blocks[0]

    assert ingress.type == "ingress"
    assert ingress.attributes["from_port"].value == 443
    assert ingress.attributes["to_port"].value == 443
    assert ingress.attributes["protocol"].value == "tcp"
    assert ingress.attributes["cidr_blocks"][0].value == "0.0.0.0/0"


def test_terraform_round_trip_preserves_nested_blocks() -> None:
    terraform_source = """
terraform {
  required_version = ">= 1.0"
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

    description = "HTTPS access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""

    first_ir = parse_terraform(terraform_source)

    generated_terraform = generate_terraform(first_ir)

    second_ir = parse_terraform(generated_terraform)

    assert len(second_ir.resources) == 1

    resource = second_ir.resources[0]

    assert resource.type == "aws_security_group"
    assert resource.name == "web"

    assert resource.attributes["name"].value == "web-sg"

    assert len(resource.blocks) == 2

    ingress = resource.blocks[0]

    assert ingress.type == "ingress"
    assert ingress.attributes["from_port"].value == 443
    assert ingress.attributes["to_port"].value == 443
    assert ingress.attributes["protocol"].value == "tcp"
    assert ingress.attributes["cidr_blocks"][0].value == "0.0.0.0/0"
    assert ingress.attributes["description"].value == "HTTPS access"

    egress = resource.blocks[1]

    assert egress.type == "egress"
    assert egress.attributes["from_port"].value == 0
    assert egress.attributes["to_port"].value == 0
    assert egress.attributes["protocol"].value == "-1"
    assert egress.attributes["cidr_blocks"][0].value == "0.0.0.0/0"


def test_terraform_round_trip_preserves_reference() -> None:
    terraform_source = """
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
}

output "bucket_id" {
  value = aws_s3_bucket.example.id
}
"""

    first_ir = parse_terraform(terraform_source)

    generated_terraform = generate_terraform(first_ir)

    second_ir = parse_terraform(generated_terraform)

    assert len(second_ir.resources) == 1
    assert len(second_ir.outputs) == 1

    resource = second_ir.resources[0]
    output = second_ir.outputs[0]

    assert resource.type == "aws_s3_bucket"
    assert resource.name == "example"

    assert output.name == "bucket_id"
    assert isinstance(output.value, Reference)

    assert output.value.resource_type == "aws_s3_bucket"
    assert output.value.resource_name == "example"
    assert output.value.attribute == "id"


def test_terraform_round_trip_preserves_variable_reference() -> None:
    terraform_source = """
variable "bucket_name" {
  type    = string
  default = "my-bucket"
}

resource "aws_s3_bucket" "example" {
  bucket = var.bucket_name
}

output "bucket_name" {
  value = var.bucket_name
}
"""

    first_ir = parse_terraform(terraform_source)

    generated_terraform = generate_terraform(first_ir)

    second_ir = parse_terraform(generated_terraform)

    assert len(second_ir.variables) == 1
    assert len(second_ir.resources) == 1
    assert len(second_ir.outputs) == 1

    variable = second_ir.variables[0]
    resource = second_ir.resources[0]
    output = second_ir.outputs[0]

    assert variable.name == "bucket_name"

    assert isinstance(resource.attributes["bucket"], RawExpression)
    assert resource.attributes["bucket"].value == "var.bucket_name"

    assert isinstance(output.value, RawExpression)
    assert output.value.value == "var.bucket_name"