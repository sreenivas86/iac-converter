# tests/unit/ir/test_model.py

from iac_converter.ir import ProjectIR, Provider, Resource


def test_project_ir():

    project = ProjectIR(
        providers=[
            Provider(
                name="aws",
                configuration={
                    "region": "ap-south-1",
                },
            )
        ],
        resources=[
            Resource(
                type="aws_s3_bucket",
                name="data",
                attributes={
                    "bucket": "company-data",
                },
            )
        ],
    )

    assert project.version == "1"

    assert len(project.providers) == 1
    assert project.providers[0].name == "aws"

    assert len(project.resources) == 1
    assert project.resources[0].type == "aws_s3_bucket"
    assert project.resources[0].name == "data"
