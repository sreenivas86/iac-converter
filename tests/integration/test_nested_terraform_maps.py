
from iac_converter.compiler.terraform_to_ir import parse_terraform
from iac_converter.ir import (
    CollectionExpression,
    Literal,
    Reference,
    VariableReference,
)


def test_map_preserves_nested_list():
    source = """
output "settings" {
  value = {
    names = ["alpha", "beta"]
  }
}
"""
    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "map"

    values = dict(expression.items)
    names = values["names"]

    assert isinstance(names, CollectionExpression)
    assert names.kind == "list"
    assert names.items == (Literal("alpha"), Literal("beta"))


def test_map_preserves_variable_reference():
    source = """
variable "bucket_name" {
  type    = string
  default = "demo"
}

output "settings" {
  value = {
    bucket = var.bucket_name
  }
}
"""
    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    values = dict(expression.items)

    assert values["bucket"] == VariableReference(name="bucket_name")


def test_map_preserves_resource_reference():
    source = """
resource "aws_s3_bucket" "example" {
  bucket = "demo"
}

output "settings" {
  value = {
    bucket_id = aws_s3_bucket.example.id
  }
}
"""
    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    values = dict(expression.items)
    reference = values["bucket_id"]

    assert isinstance(reference, Reference)
    assert reference.resource_type == "aws_s3_bucket"
    assert reference.resource_name == "example"
    assert reference.attribute == "id"

