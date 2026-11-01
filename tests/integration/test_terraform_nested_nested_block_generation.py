from iac_converter.generator.terraform import generate_terraform
from iac_converter.ir import Block, Literal, ProjectIR, Resource


def test_generate_terraform_nested_nested_blocks():
    project = ProjectIR(
        resources=[
            Resource(
                type="example",
                name="test",
                blocks=[
                    Block(
                        type="outer",
                        attributes={
                            "name": Literal("foo"),
                        },
                        blocks=[
                            Block(
                                type="inner",
                                attributes={
                                    "enabled": Literal(True),
                                },
                            )
                        ],
                    )
                ],
            )
        ]
    )

    terraform = generate_terraform(project)

    assert 'resource "example" "test" {' in terraform
    assert "outer {" in terraform
    assert 'name = "foo"' in terraform
    assert "inner {" in terraform
    assert "enabled = true" in terraform
