from iac_converter.compiler.terraform_to_ir import parse_terraform
from iac_converter.ir import (
    CollectionExpression,
    Literal,
    Reference,
    VariableReference,
)


def test_nested_list_becomes_nested_collection_expressions() -> None:
    source = """
output "matrix" {
  value = [["alpha", "beta"], ["gamma"]]
}
"""
    project = parse_terraform(source)
    outer = project.outputs[0].value

    assert isinstance(outer, CollectionExpression)
    assert outer.kind == "list"
    assert len(outer.items) == 2

    first_inner = outer.items[0]
    assert isinstance(first_inner, CollectionExpression)
    assert first_inner.kind == "list"
    assert first_inner.items == (Literal("alpha"), Literal("beta"))


def test_list_preserves_variable_reference() -> None:
    source = """
variable "bucket_name" {
  type    = string
  default = "demo"
}

output "names" {
  value = [var.bucket_name, "another"]
}
"""
    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.items[0] == VariableReference(name="bucket_name")
    assert expression.items[1] == Literal("another")


def test_list_preserves_resource_reference() -> None:
    source = """
resource "aws_s3_bucket" "example" {
  bucket = "demo"
}

output "ids" {
  value = [aws_s3_bucket.example.id]
}
"""
    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    reference = expression.items[0]

    assert isinstance(reference, Reference)
    assert reference.resource_type == "aws_s3_bucket"
    assert reference.resource_name == "example"
    assert reference.attribute == "id"
