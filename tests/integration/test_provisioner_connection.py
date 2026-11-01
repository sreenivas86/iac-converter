from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.ir import Literal, RawExpression
from iac_converter.project import Project, ProjectFile


def test_provisioner_connection_round_trip() -> None:
    yaml_source = """
version: "1"

resources:
  - type: aws_instance
    name: server

    provisioners:
      - type: remote-exec

        properties:
          inline:
            - "echo hello"

        connection:
          type: ssh
          user: ubuntu
          private_key:
            expression: 'file("~/.ssh/id_rsa")'
          host:
            expression: self.public_ip
"""

    # YAML -> ProjectIR
    original_ir = parse_yaml_project(yaml_source)

    resource = original_ir.resources[0]
    assert len(resource.provisioners) == 1

    provisioner = resource.provisioners[0]

    assert provisioner["type"] == "remote-exec"

    assert provisioner["connection"]["type"] == Literal("ssh")
    assert provisioner["connection"]["user"] == Literal("ubuntu")
    assert provisioner["connection"]["private_key"] == RawExpression('file("~/.ssh/id_rsa")')
    assert provisioner["connection"]["host"] == RawExpression("self.public_ip")

    # ProjectIR -> Terraform
    terraform_source = generate_terraform(original_ir)

    assert 'provisioner "remote-exec" {' in terraform_source
    assert "connection {" in terraform_source
    assert 'type = "ssh"' in terraform_source
    assert 'user = "ubuntu"' in terraform_source
    assert 'private_key = file("~/.ssh/id_rsa")' in terraform_source
    assert "host = self.public_ip" in terraform_source

    # Terraform -> Project
    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content=terraform_source,
            )
        ]
    )

    # Project -> ProjectIR
    round_trip_ir = parse_terraform_project(terraform_project)

    round_trip_resource = round_trip_ir.resources[0]
    round_trip_provisioner = round_trip_resource.provisioners[0]

    assert round_trip_provisioner["type"] == "remote-exec"

    connection = round_trip_provisioner["connection"]

    assert connection["type"] == Literal("ssh")
    assert connection["user"] == Literal("ubuntu")
    assert connection["private_key"] == RawExpression('file("~/.ssh/id_rsa")')
    assert connection["host"] == RawExpression("self.public_ip")
