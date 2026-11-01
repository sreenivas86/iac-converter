# tests/unit/ir/test_reference.py

from iac_converter.ir import (
    DataSourceReference,
    LocalReference,
    Reference,
    VariableReference,
)


def test_resource_reference_to_string() -> None:
    reference = Reference(
        resource_type="aws_s3_bucket",
        resource_name="example",
        attribute="id",
    )

    assert reference.to_string() == "aws_s3_bucket.example.id"


def test_data_source_reference_to_string() -> None:
    reference = DataSourceReference(
        data_source_type="aws_ami",
        data_source_name="example",
        attribute="id",
    )

    assert reference.to_string() == "data.aws_ami.example.id"


def test_variable_reference_to_string() -> None:
    reference = VariableReference(name="bucket_name")

    assert reference.to_string() == "var.bucket_name"


def test_local_reference_to_string() -> None:
    reference = LocalReference(name="bucket_prefix")

    assert reference.to_string() == "local.bucket_prefix"


def test_reference():

    reference = Reference(
        resource_type="aws_s3_bucket",
        resource_name="data",
        attribute="id",
    )

    assert reference.to_string() == "aws_s3_bucket.data.id"
