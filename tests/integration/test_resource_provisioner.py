from iac_converter.compiler import (
    parse_terraform_project,
    parse_yaml_project,
)
from iac_converter.generator import generate_terraform
from iac_converter.ir import Literal, RawExpression
from iac_converter.project import Project, ProjectFile


def test_resource_provisioner_round_trip() -> None:
    yaml_source = """
version: "1"

providers:
  aws:
    properties:
      region: ap-south-1

resources:
  - type: aws_s3_bucket
    name: data
    properties:
      bucket: company-data
    provisioners:
      - type: local-exec
        properties:
          command:
            expression: '\"echo ${self.id}\"'
          working_dir: /tmp
"""

    # ---------------------------------------------------------
    # YAML -> ProjectIR
    # ---------------------------------------------------------

    original_ir = parse_yaml_project(yaml_source)

    assert len(original_ir.resources) == 1

    original_resource = original_ir.resources[0]

    assert len(original_resource.provisioners) == 1

    provisioner = original_resource.provisioners[0]

    assert provisioner["type"] == "local-exec"

    assert provisioner["properties"]["command"] == RawExpression(
        '"echo ${self.id}"'
    )

    assert provisioner["properties"]["working_dir"] == Literal(
        "/tmp"
    )

    # ---------------------------------------------------------
    # ProjectIR -> Terraform
    # ---------------------------------------------------------

    terraform_source = generate_terraform(original_ir)

    assert 'provisioner "local-exec" {' in terraform_source
    assert 'command = "echo ${self.id}"' in terraform_source
    assert 'working_dir = "/tmp"' in terraform_source

    # ---------------------------------------------------------
    # Terraform -> Project
    # ---------------------------------------------------------

    terraform_project = Project(
        files=[
            ProjectFile(
                path="main.tf",
                content=terraform_source,
            )
        ]
    )

    # ---------------------------------------------------------
    # Project -> ProjectIR
    # ---------------------------------------------------------

    round_trip_ir = parse_terraform_project(terraform_project)

    assert len(round_trip_ir.resources) == 1

    round_trip_resource = round_trip_ir.resources[0]

    assert len(round_trip_resource.provisioners) == 1

    round_trip_provisioner = round_trip_resource.provisioners[0]

    assert round_trip_provisioner["type"] == "local-exec"

    assert round_trip_provisioner["properties"]["command"] == RawExpression(
        '"echo ${self.id}"'
    )

    assert round_trip_provisioner["properties"]["working_dir"] == Literal(
        "/tmp"
    )