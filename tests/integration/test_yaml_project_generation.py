from iac_converter.generator import generate_yaml_project
from iac_converter.ir import (
    Literal,
    Output,
    ProjectIR,
    Provider,
    RawExpression,
    Reference,
    Resource,
    Variable,
)


def test_generate_yaml_project() -> None:
    project = ProjectIR(
        terraform={
            "required_version": Literal(">= 1.6.0"),
        },
        providers=[
            Provider(
                name="aws",
                configuration={
                    "region": Literal("ap-south-1"),
                },
            )
        ],
        variables=[
            Variable(
                name="bucket_name",
                description="S3 bucket name",
                default=Literal("company-data"),
            )
        ],
        resources=[
            Resource(
                type="aws_s3_bucket",
                name="data",
                attributes={
                    "bucket": Reference(
                        resource_type="aws_s3_bucket",
                        resource_name="source",
                        attribute="id",
                    ),
                    "name": RawExpression("var.bucket_name"),
                },
            )
        ],
        outputs=[
            Output(
                name="bucket_id",
                value=Reference(
                    resource_type="aws_s3_bucket",
                    resource_name="data",
                    attribute="id",
                ),
            )
        ],
    )

    result = generate_yaml_project(project)

    assert 'version: "1"' in result
    assert "terraform:" in result
    assert "providers:" in result
    assert "variables:" in result
    assert "resources:" in result
    assert "outputs:" in result

    assert "required_version:" in result
    assert "ap-south-1" in result
    assert "company-data" in result
    assert "expression: var.bucket_name" in result
    assert "resource_type: aws_s3_bucket" in result
    assert "resource_name: data" in result


def test_generate_yaml_project_omits_empty_sections() -> None:
    project = ProjectIR(
        resources=[
            Resource(
                type="aws_s3_bucket",
                name="data",
                attributes={
                    "bucket": Literal("company-data"),
                },
            )
        ]
    )

    result = generate_yaml_project(project)

    assert "version: " in result
    assert "resources:" in result

    assert "terraform:" not in result
    assert "providers:" not in result
    assert "variables:" not in result
    assert "locals:" not in result
    assert "data_sources:" not in result
    assert "outputs:" not in result
