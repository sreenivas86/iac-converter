from iac_converter.compiler.terraform_to_ir import parse_terraform
from iac_converter.generator.terraform import generate_terraform
from iac_converter.ir import (
    CollectionExpression,
    ConditionalExpression,
    FunctionCall,
    Literal,
    Reference,
)


def test_nested_list_round_trip_preserves_structure():
    source = """
output "matrix" {
  value = [["alpha", "beta"], ["gamma"]]
}
"""
    project = parse_terraform(source)
    generated = generate_terraform(project)
    reparsed = parse_terraform(generated)

    expression = reparsed.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "list"
    assert len(expression.items) == 2

    first_inner = expression.items[0]
    second_inner = expression.items[1]

    assert isinstance(first_inner, CollectionExpression)
    assert isinstance(second_inner, CollectionExpression)

    assert first_inner.items == (Literal("alpha"), Literal("beta"))
    assert second_inner.items == (Literal("gamma"),)

def test_map_with_nested_list_round_trip_preserves_structure():
    source = """
output "settings" {
  value = {
    names = ["alpha", "beta"]
  }
}
"""
    project = parse_terraform(source)
    generated = generate_terraform(project)
    reparsed = parse_terraform(generated)

    expression = reparsed.outputs[0].value
    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "map"

    values = dict(expression.items)
    names = values["names"]

    assert isinstance(names, CollectionExpression)
    assert names.kind == "list"
    assert len(names.items) == 2


def test_list_with_variable_reference_round_trip():
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
    generated = generate_terraform(project)
    reparsed = parse_terraform(generated)

    expression = reparsed.outputs[0].value
    assert isinstance(expression, CollectionExpression)
    assert len(expression.items) == 2
    assert "var.bucket_name" in generated

def test_nested_map_with_mixed_expressions_round_trip():
    source = """
resource "aws_s3_bucket" "data" {
  bucket = "company-data"
}

output "settings" {
  value = {
    bucket_id = aws_s3_bucket.data.id
    normalized_name = lower("MY-BUCKET")
    enabled = var.create_bucket ? true : false
    nested = {
      regions = ["ap-south-1", "ap-southeast-1"]
    }
  }
}
"""
    project = parse_terraform(source)
    generated = generate_terraform(project)
    reparsed = parse_terraform(generated)

    expression = reparsed.outputs[0].value
    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "map"

    values = dict(expression.items)

    assert isinstance(values["bucket_id"], Reference)
    assert values["bucket_id"].resource_name == "data"
    assert values["bucket_id"].attribute == "id"

    assert isinstance(values["normalized_name"], FunctionCall)
    assert values["normalized_name"].name == "lower"

    assert isinstance(values["enabled"], ConditionalExpression)

    nested = values["nested"]
    assert isinstance(nested, CollectionExpression)

    nested_values = dict(nested.items)
    regions = nested_values["regions"]

    assert isinstance(regions, CollectionExpression)
    assert regions.kind == "list"
    assert regions.items == (
        Literal("ap-south-1"),
        Literal("ap-southeast-1"),
    )