
from iac_converter.compiler import parse_terraform_project
from iac_converter.ir import Literal
from iac_converter.project import Project, ProjectFile


def test_terraform_nested_blocks_are_converted_to_ir() -> None:
    terraform_source = """
resource "aws_security_group" "example" {
  name = "example"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""

    project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content=terraform_source,
            )
        ]
    )

    ir = parse_terraform_project(project)

    resource = ir.resources[0]

    assert resource.type == "aws_security_group"
    assert resource.name == "example"

    assert len(resource.blocks) == 2

    first = resource.blocks[0]

    assert first.type == "ingress"
    assert first.labels == []
    assert first.attributes["from_port"] == Literal(80)
    assert first.attributes["to_port"] == Literal(80)
    assert first.attributes["protocol"] == Literal("tcp")
    assert first.attributes["cidr_blocks"] == [
        Literal("0.0.0.0/0")
    ]

    second = resource.blocks[1]

    assert second.type == "ingress"
    assert second.attributes["from_port"] == Literal(443)
    assert second.attributes["to_port"] == Literal(443)
    assert second.attributes["protocol"] == Literal("tcp")
    assert second.attributes["cidr_blocks"] == [
        Literal("0.0.0.0/0")
    ]

