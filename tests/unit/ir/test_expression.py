import pytest

from iac_converter.ir import (
    CollectionExpression,
    ConditionalExpression,
    FunctionCall,
    Literal,
    RawExpression,
    Reference,
    VariableReference,
)


def test_literal_preserves_value() -> None:
    expression = Literal("hello")

    assert expression.value == "hello"


def test_raw_expression_preserves_source() -> None:
    expression = RawExpression('file("userdata.sh")')

    assert expression.value == 'file("userdata.sh")'


def test_function_call_preserves_name_and_arguments() -> None:
    expression = FunctionCall(
        name="file",
        arguments=(Literal("userdata.sh"),),
    )

    assert expression.name == "file"
    assert len(expression.arguments) == 1
    assert expression.arguments[0] == Literal("userdata.sh")


def test_function_call_can_contain_typed_references() -> None:
    expression = FunctionCall(
        name="tostring",
        arguments=(VariableReference(name="instance_count"),),
    )

    assert expression.name == "tostring"
    assert expression.arguments == (VariableReference(name="instance_count"),)


def test_conditional_expression_preserves_all_parts() -> None:
    expression = ConditionalExpression(
        condition=VariableReference(name="create_bucket"),
        true_value=Literal("demo-bucket"),
        false_value=Literal("disabled"),
    )

    assert expression.condition == VariableReference(name="create_bucket")
    assert expression.true_value == Literal("demo-bucket")
    assert expression.false_value == Literal("disabled")


def test_collection_expression_preserves_list_items() -> None:
    expression = CollectionExpression(
        kind="list",
        items=(Literal("one"), Literal("two")),
    )

    assert expression.kind == "list"
    assert expression.items == (Literal("one"), Literal("two"))


def test_collection_expression_preserves_map_entries() -> None:
    expression = CollectionExpression(
        kind="map",
        items=(("environment", Literal("test")),),
    )

    assert expression.kind == "map"
    assert expression.items == (("environment", Literal("test")),)


def test_collection_expression_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        CollectionExpression(kind="set", items=())


def test_expression_objects_are_immutable() -> None:
    expression = FunctionCall(
        name="file",
        arguments=(Literal("userdata.sh"),),
    )

    with pytest.raises(AttributeError):
        expression.name = "templatefile"  # type: ignore[misc]


def test_resource_reference_remains_usable() -> None:
    expression = Reference(
        resource_type="aws_s3_bucket",
        resource_name="example",
        attribute="id",
    )

    assert expression.to_string() == "aws_s3_bucket.example.id"


def test_for_expression_preserves_list_comprehension_fields() -> None:
    from iac_converter.ir import ForExpression

    expression = ForExpression(
        value=FunctionCall(
            name="upper",
            arguments=(VariableReference(name="name"),),
        ),
        collection=VariableReference(name="names"),
        variable="name",
    )

    assert expression.variable == "name"
    assert expression.collection == VariableReference(name="names")
    assert expression.value == FunctionCall(
        name="upper",
        arguments=(VariableReference(name="name"),),
    )
    assert expression.key is None
    assert expression.condition is None
    assert expression.grouping is False
