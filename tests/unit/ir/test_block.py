from iac_converter.ir import Block, Literal


def test_block_can_contain_attributes_and_nested_blocks() -> None:
    block = Block(
        type="ingress",
        attributes={
            "from_port": Literal(80),
            "to_port": Literal(80),
            "protocol": Literal("tcp"),
        },
    )

    assert block.type == "ingress"
    assert block.labels == []
    assert block.attributes["from_port"] == Literal(80)
    assert block.attributes["to_port"] == Literal(80)
    assert block.attributes["protocol"] == Literal("tcp")


def test_block_can_contain_nested_blocks() -> None:
    inner_block = Block(
        type="rule",
        attributes={
            "action": Literal("allow"),
        },
    )

    outer_block = Block(
        type="ingress",
        blocks=[inner_block],
    )

    assert len(outer_block.blocks) == 1
    assert outer_block.blocks[0].type == "rule"
    assert outer_block.blocks[0].attributes["action"] == Literal("allow")
