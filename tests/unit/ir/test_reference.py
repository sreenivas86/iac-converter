# tests/unit/ir/test_reference.py

from iac_converter.ir import Reference


def test_reference():

    reference = Reference(
        resource_type="aws_s3_bucket",
        resource_name="data",
        attribute="id",
    )

    assert reference.to_string() == "aws_s3_bucket.data.id"