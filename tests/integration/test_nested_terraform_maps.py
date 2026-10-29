
from iac_converter.compiler.terraform_to_ir import parse_terraform
from iac_converter.ir import (
    CollectionExpression,
    ConditionalExpression,
    FunctionCall,
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


def test_map_preserves_function_call_through_terraform_round_trip():
    source = """
output "settings" {
  value = {
    normalized_name = lower("MY-BUCKET")
  }
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, CollectionExpression)
    first_values = dict(first_expression.items)
    function = first_values["normalized_name"]

    assert isinstance(function, FunctionCall)
    assert function.name == "lower"
    assert function.arguments == (Literal("MY-BUCKET"),)

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    second_expression = second_project.outputs[0].value

    assert isinstance(second_expression, CollectionExpression)
    second_values = dict(second_expression.items)
    reparsed_function = second_values["normalized_name"]

    assert isinstance(reparsed_function, FunctionCall)
    assert reparsed_function.name == "lower"
    assert reparsed_function.arguments == (Literal("MY-BUCKET"),)

def test_map_preserves_conditional_expression_through_terraform_round_trip():
    source = """
variable "create_bucket" {
  type    = bool
  default = true
}

output "settings" {
  value = {
    status = var.create_bucket ? "enabled" : "disabled"
  }
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, CollectionExpression)
    first_values = dict(first_expression.items)
    conditional = first_values["status"]

    assert isinstance(conditional, ConditionalExpression)
    assert conditional.condition == VariableReference(name="create_bucket")
    assert conditional.true_value == Literal("enabled")
    assert conditional.false_value == Literal("disabled")

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    second_expression = second_project.outputs[0].value

    assert isinstance(second_expression, CollectionExpression)
    second_values = dict(second_expression.items)
    reparsed_conditional = second_values["status"]

    assert isinstance(reparsed_conditional, ConditionalExpression)
    assert reparsed_conditional.condition == VariableReference(name="create_bucket")
    assert reparsed_conditional.true_value == Literal("enabled")
    assert reparsed_conditional.false_value == Literal("disabled")

def test_nested_function_calls_round_trip():
    source = """
output "settings" {
  value = {
    normalized_name = lower(trimspace(var.bucket_name))
  }
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, CollectionExpression)
    first_values = dict(first_expression.items)
    outer = first_values["normalized_name"]

    assert isinstance(outer, FunctionCall)
    assert outer.name == "lower"
    assert len(outer.arguments) == 1

    inner = outer.arguments[0]
    assert isinstance(inner, FunctionCall)
    assert inner.name == "trimspace"
    assert inner.arguments == (VariableReference(name="bucket_name"),)

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    second_expression = second_project.outputs[0].value

    assert isinstance(second_expression, CollectionExpression)
    second_values = dict(second_expression.items)
    reparsed_outer = second_values["normalized_name"]

    assert isinstance(reparsed_outer, FunctionCall)
    assert reparsed_outer.name == "lower"
    assert isinstance(reparsed_outer.arguments[0], FunctionCall)
    assert reparsed_outer.arguments[0].name == "trimspace"
    assert reparsed_outer.arguments[0].arguments == (
        VariableReference(name="bucket_name"),
    )


def test_nested_function_calls_round_trip():
    source = """
output "settings" {
  value = {
    normalized_name = lower(trimspace(var.bucket_name))
  }
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, CollectionExpression)
    first_values = dict(first_expression.items)
    outer = first_values["normalized_name"]

    assert isinstance(outer, FunctionCall)
    assert outer.name == "lower"
    assert len(outer.arguments) == 1

    inner = outer.arguments[0]
    assert isinstance(inner, FunctionCall)
    assert inner.name == "trimspace"
    assert inner.arguments == (VariableReference(name="bucket_name"),)

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    second_expression = second_project.outputs[0].value

    assert isinstance(second_expression, CollectionExpression)
    second_values = dict(second_expression.items)
    reparsed_outer = second_values["normalized_name"]

    assert isinstance(reparsed_outer, FunctionCall)
    assert reparsed_outer.name == "lower"
    assert isinstance(reparsed_outer.arguments[0], FunctionCall)
    assert reparsed_outer.arguments[0].name == "trimspace"
    assert reparsed_outer.arguments[0].arguments == (
        VariableReference(name="bucket_name"),
    )


def test_nested_conditional_expression_round_trip():
    source = """
variable "enabled" {
  type    = bool
  default = true
}

variable "use_custom_name" {
  type    = bool
  default = false
}

output "bucket_name" {
  value = var.enabled ? (var.use_custom_name ? "custom" : "default") : "disabled"
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, ConditionalExpression)
    assert first_expression.condition == VariableReference(name="enabled")

    nested = first_expression.true_value
    assert isinstance(nested, ConditionalExpression)
    assert nested.condition == VariableReference(name="use_custom_name")
    assert nested.true_value == Literal("custom")
    assert nested.false_value == Literal("default")
    assert first_expression.false_value == Literal("disabled")

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    reparsed = second_project.outputs[0].value

    assert isinstance(reparsed, ConditionalExpression)
    assert isinstance(reparsed.true_value, ConditionalExpression)


def test_conditional_expression_inside_function_round_trip():
    source = """
variable "enabled" {
  type    = bool
  default = true
}

output "status" {
  value = lower(var.enabled ? "ACTIVE" : "INACTIVE")
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, FunctionCall)
    assert first_expression.name == "lower"
    assert len(first_expression.arguments) == 1

    conditional = first_expression.arguments[0]
    assert isinstance(conditional, ConditionalExpression)
    assert conditional.condition == VariableReference(name="enabled")
    assert conditional.true_value == Literal("ACTIVE")
    assert conditional.false_value == Literal("INACTIVE")

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    reparsed = second_project.outputs[0].value

    assert isinstance(reparsed, FunctionCall)
    assert reparsed.name == "lower"
    assert isinstance(reparsed.arguments[0], ConditionalExpression)


def test_function_call_with_map_argument_round_trip():
    source = """
output "region" {
  value = lookup({ primary = "ap-south-1" }, "primary", "us-east-1")
}
"""
    from iac_converter.generator.terraform import generate_terraform

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, FunctionCall)
    assert first_expression.name == "lookup"
    assert len(first_expression.arguments) == 3

    mapping = first_expression.arguments[0]
    assert isinstance(mapping, CollectionExpression)
    assert mapping.kind == "map"
    assert dict(mapping.items) == {
        "primary": Literal("ap-south-1"),
    }

    generated = generate_terraform(first_project)
    second_project = parse_terraform(generated)
    reparsed = second_project.outputs[0].value

    assert isinstance(reparsed, FunctionCall)
    assert reparsed.name == "lookup"
    assert isinstance(reparsed.arguments[0], CollectionExpression)


def test_splat_expression_round_trip():
    source = """
output "instance_ids" {
  value = var.instances[*].id
}
"""
    from iac_converter.generator.terraform import generate_terraform
    from iac_converter.ir import RawExpression

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, RawExpression)
    assert first_expression.value == "var.instances[*].id"

    generated = generate_terraform(first_project)
    assert "var.instances[*].id" in generated

    second_project = parse_terraform(generated)
    reparsed = second_project.outputs[0].value

    assert isinstance(reparsed, RawExpression)
    assert reparsed.value == "var.instances[*].id"


def test_list_comprehension_round_trip():
    source = """
variable "names" {
  type    = list(string)
  default = ["alpha", "beta"]
}

output "upper_names" {
  value = [for name in var.names : upper(name)]
}
"""
    from iac_converter.generator.terraform import generate_terraform
    from iac_converter.ir import ForExpression, ForVariableReference

    first_project = parse_terraform(source)
    first_expression = first_project.outputs[0].value

    assert isinstance(first_expression, ForExpression)
    assert first_expression.variable == "name"
    assert first_expression.collection == VariableReference(name="names")
    assert first_expression.condition is None
    assert first_expression.key is None
    assert first_expression.value.arguments == (
        ForVariableReference(name="name"),
    )

    generated = generate_terraform(first_project)
    assert "[for name in var.names : upper(name)]" in generated

    second_project = parse_terraform(generated)
    second_expression = second_project.outputs[0].value

    assert isinstance(second_expression, ForExpression)
    assert second_expression == first_expression



def test_filtered_list_comprehension_round_trip():
    source = """
variable "names" {
  type    = list(string)
  default = ["alpha", "skip", "beta"]
}

output "filtered_names" {
  value = [for name in var.names : upper(name) if name != "skip"]
}
"""
    from iac_converter.generator.terraform import generate_terraform
    from iac_converter.ir import (
        ForExpression,
        ForVariableReference,
        RawExpression,
    )

    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, ForExpression)
    assert expression.variable == "name"
    assert expression.condition is not None
    assert expression.condition == RawExpression(
        value='name != "skip"'
    )
    assert expression.value.arguments == (
        ForVariableReference(name="name"),
    )

    generated = generate_terraform(project)
    assert (
        '[for name in var.names : upper(name) if name != "skip"]'
        in generated
    )

    reparsed = parse_terraform(generated)
    reparsed_expression = reparsed.outputs[0].value

    assert isinstance(reparsed_expression, ForExpression)
    assert reparsed_expression.condition == expression.condition

def test_map_comprehension_round_trip():
    source = """
variable "names" {
  type    = list(string)
  default = ["alpha", "beta"]
}

output "name_map" {
  value = {
    for name in var.names : name => upper(name)
  }
}
"""
    from iac_converter.generator.terraform import generate_terraform
    from iac_converter.ir import ForExpression, ForVariableReference

    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, ForExpression)
    assert expression.variable == "name"
    assert expression.key == ForVariableReference(name="name")
    assert expression.value.arguments == (
        ForVariableReference(name="name"),
    )

    generated = generate_terraform(project)
    assert "for name in var.names : name => upper(name)" in generated

    reparsed = parse_terraform(generated)
    assert reparsed.outputs[0].value == expression

def test_grouped_filtered_map_comprehension_generation():
    source = """
variable "names" {
  type    = list(string)
  default = ["alpha", "apple", "beta", "skip"]
}

output "grouped_names" {
  value = {
    for name in var.names : substr(name, 0, 1) => name... if name != "skip"
  }
}
"""
    from iac_converter.generator.terraform import generate_terraform
    from iac_converter.ir import ForExpression

    project = parse_terraform(source)
    expression = project.outputs[0].value

    assert isinstance(expression, ForExpression)
    assert expression.key is not None
    assert expression.grouping is True
    assert expression.condition is not None

    generated = generate_terraform(project)

    assert "name... if name !=" in generated
    assert generated.index("name... if name !=") > generated.index("=>")
    reparsed = parse_terraform(generated)
    reparsed_expression = reparsed.outputs[0].value

    assert isinstance(reparsed_expression, ForExpression)
    assert reparsed_expression.grouping is True
    assert reparsed_expression.condition == expression.condition
    assert reparsed_expression.key == expression.key
    assert reparsed_expression.value == expression.value