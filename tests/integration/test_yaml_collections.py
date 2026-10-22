from iac_converter.ir import (
    CollectionExpression,
    Literal,
    Reference,
)
from iac_converter.generator.yaml import generate_yaml
from iac_converter.parser.yaml_parser import parse_yaml


def test_yaml_parser_preserves_nested_list_values():
    source = """
outputs:
  - name: matrix
    value:
      - - alpha
        - beta
      - - gamma
"""

    project = parse_yaml(source)
    value = project.outputs[0].value

    assert isinstance(value, CollectionExpression)
    assert value.kind == "list"

    first_inner = value.items[0]
    second_inner = value.items[1]

    assert isinstance(first_inner, CollectionExpression)
    assert first_inner.kind == "list"
    assert first_inner.items == (Literal("alpha"), Literal("beta"))

    assert isinstance(second_inner, CollectionExpression)
    assert second_inner.kind == "list"
    assert second_inner.items == (Literal("gamma"),)


def test_yaml_parser_preserves_nested_map_values():
    source = """
outputs:
  - name: settings
    value:
      environment:
        name: dev
        regions:
          - ap-south-1
          - ap-southeast-1
"""

    project = parse_yaml(source)
    value = project.outputs[0].value

    assert isinstance(value, CollectionExpression)
    assert value.kind == "map"

    environment = dict(value.items)["environment"]

    assert isinstance(environment, CollectionExpression)
    assert environment.kind == "map"

    environment_values = dict(environment.items)
    assert environment_values["name"] == Literal("dev")

    regions = environment_values["regions"]
    assert isinstance(regions, CollectionExpression)
    assert regions.kind == "list"
    assert regions.items == (
        Literal("ap-south-1"),
        Literal("ap-southeast-1"),
    )


def test_yaml_collection_round_trip_preserves_values():
    source = """
outputs:
  - name: settings
    value:
      names:
        - alpha
        - beta
"""

    project = parse_yaml(source)
    generated = generate_yaml(project)
    reparsed = parse_yaml(generated)

    original_value = project.outputs[0].value
    round_trip_value = reparsed.outputs[0].value

    assert round_trip_value == original_value


def test_yaml_collection_preserves_resource_reference():
    source = """
resources:
  - type: aws_s3_bucket
    name: backup
    properties:
      bucket:
        reference:
          resource_type: aws_s3_bucket
          resource_name: data
          attribute: id
"""

    project = parse_yaml(source)
    generated = generate_yaml(project)
    reparsed = parse_yaml(generated)

    original_bucket = project.resources[0].attributes["bucket"]
    round_trip_bucket = reparsed.resources[0].attributes["bucket"]

    assert isinstance(original_bucket, Reference)
    assert isinstance(round_trip_bucket, Reference)
    assert round_trip_bucket.to_string() == "aws_s3_bucket.data.id"
