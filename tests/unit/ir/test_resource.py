from iac_converter.ir import Block, Literal, Resource


def test_resource_can_contain_nested_blocks() -> None:
    resource = Resource(
        type="aws_security_group",
        name="example",
        blocks=[
            Block(
                type="ingress",
                attributes={
                    "from_port": Literal(80),
                    "to_port": Literal(80),
                    "protocol": Literal("tcp"),
                },
            )
        ],
    )

    assert len(resource.blocks) == 1
    assert resource.blocks[0].type == "ingress"
    assert resource.blocks[0].attributes["from_port"] == Literal(80)
