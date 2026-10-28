from iac_converter.compiler.terraform_to_ir import parse_terraform
from iac_converter.generator.terraform import generate_terraform
from iac_converter.ir import CollectionExpression, Literal


def test_terraform_list_becomes_collection_expression() -> None:
    source = """
output "names" {
  value = ["alpha", "beta"]
}
"""
    project = parse_terraform(source)

    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "list"
    assert expression.items == (Literal("alpha"), Literal("beta"))


def test_terraform_map_becomes_collection_expression() -> None:
    source = """
output "settings" {
  value = {
    environment = "test"
    region      = "us-east-1"
  }
}
"""
    project = parse_terraform(source)

    expression = project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "map"
    assert dict(expression.items) == {
        "environment": Literal("test"),
        "region": Literal("us-east-1"),
    }


def test_collection_expression_round_trips_through_terraform() -> None:
    source = """
output "names" {
  value = ["alpha", "beta"]
}
"""
    first_project = parse_terraform(source)
    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)

    expression = second_project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "list"
    assert expression.items == (Literal("alpha"), Literal("beta"))

def test_terraform_tuple_values_survive_generation_and_reparsing() -> None:
    source = """
output "coordinates" {
  value = ["ap-south-1", "ap-southeast-1"]
}
"""
    first_project = parse_terraform(source)

    first_project.outputs[0].value = CollectionExpression(
        kind="tuple",
        items=(
            Literal("ap-south-1"),
            Literal("ap-southeast-1"),
        ),
    )

    generated = generate_terraform(first_project)

    # Terraform uses square-bracket syntax for collection constructors.
    assert 'value = ["ap-south-1", "ap-southeast-1"]' in generated

    second_project = parse_terraform(generated)
    expression = second_project.outputs[0].value

    assert isinstance(expression, CollectionExpression)
    assert expression.kind == "list"
    assert expression.items == (
        Literal("ap-south-1"),
        Literal("ap-southeast-1"),
    )
