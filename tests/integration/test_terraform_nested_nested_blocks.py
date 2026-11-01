from iac_converter.parser.terraform_parser import parse_terraform


def test_parse_terraform_nested_nested_blocks():
    source = """
resource "example" "test" {
  outer {
    name = "foo"

    inner {
      enabled = true
    }
  }
}
"""

    project = parse_terraform(source)

    assert len(project.resources) == 1

    resource = project.resources[0]

    assert resource.type == "example"
    assert resource.name == "test"

    assert len(resource.blocks) == 1

    outer = resource.blocks[0]

    assert outer.type == "outer"
    assert outer.attributes["name"].value == "foo"

    assert len(outer.blocks) == 1

    inner = outer.blocks[0]

    assert inner.type == "inner"
    assert inner.attributes["enabled"].value is True
