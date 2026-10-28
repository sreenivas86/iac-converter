
from iac_converter.ir import (
    CollectionExpression,
    Literal,
    Reference,
)
from iac_converter.parser.yaml_parser import parse_yaml
from iac_converter.generator.yaml import generate_yaml


def test_yaml_list_becomes_collection_expression():
    source = """
outputs:
  - name: names
    value:
      - alpha
      - beta
"""
    project = parse_yaml(source)
    value = project.outputs[0].value

    assert isinstance(value, CollectionExpression)
    assert value.kind == "list"
    assert value.items == (Literal("alpha"), Literal("beta"))


def test_yaml_nested_lists_become_nested_collection_expressions():
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
    assert isinstance(second_inner, CollectionExpression)
    assert first_inner.items == (Literal("alpha"), Literal("beta"))
    assert second_inner.items == (Literal("gamma"),)


def test_yaml_map_becomes_collection_expression():
    source = """
outputs:
  - name: settings
    value:
      environment: dev
      region: ap-south-1
"""
    project = parse_yaml(source)
    value = project.outputs[0].value

    assert isinstance(value, CollectionExpression)
    assert value.kind == "map"

    values = dict(value.items)
    assert values == {
        "environment": Literal("dev"),
        "region": Literal("ap-south-1"),
    }


def test_yaml_map_preserves_resource_reference():
    source = """
resources:
  - type: aws_s3_bucket
    name: backup
    properties:
      settings:
        source:
          reference:
            resource_type: aws_s3_bucket
            resource_name: data
            attribute: id
"""
    project = parse_yaml(source)
    settings = project.resources[0].attributes["settings"]

    assert isinstance(settings, CollectionExpression)
    assert settings.kind == "map"

    values = dict(settings.items)
    reference = values["source"]

    assert isinstance(reference, Reference)
    assert reference.to_string() == "aws_s3_bucket.data.id"

def test_nested_typed_collections_survive_yaml_round_trip():
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

    original_project = parse_yaml(source)
    generated_yaml = generate_yaml(original_project)
    reparsed_project = parse_yaml(generated_yaml)

    original_value = original_project.outputs[0].value
    reparsed_value = reparsed_project.outputs[0].value

    assert isinstance(original_value, CollectionExpression)
    assert original_value.kind == "map"

    assert isinstance(reparsed_value, CollectionExpression)
    assert reparsed_value.kind == "map"

    # Confirm the complete nested structure and values are preserved.
    assert reparsed_value == original_value