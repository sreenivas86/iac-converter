from iac_converter.ir import Block, Literal
from iac_converter.parser.terraform_parser import parse_terraform


def test_parse_terraform_nested_blocks():
    source = """
resource "aws_security_group" "web" {
  name = "web"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""

    project = parse_terraform(source)

    assert len(project.resources) == 1

    resource = project.resources[0]

    assert resource.type == "aws_security_group"
    assert resource.name == "web"

    assert len(resource.blocks) == 1

    ingress = resource.blocks[0]

    assert isinstance(ingress, Block)
    assert ingress.type == "ingress"

    assert ingress.attributes["from_port"] == Literal(80)
    assert ingress.attributes["to_port"] == Literal(80)
    assert ingress.attributes["protocol"] == Literal("tcp")
    assert ingress.attributes["cidr_blocks"] == [Literal("0.0.0.0/0")]
