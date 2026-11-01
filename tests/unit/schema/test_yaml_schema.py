import pytest
from pydantic import ValidationError

from iac_converter.schema.yaml_schema import (
    YAMLProject,
    YAMLResource,
    YAMLVariable,
)


def test_yaml_project_accepts_valid_data():
    project = YAMLProject.model_validate(
        {
            "version": "1",
            "resources": [
                {
                    "type": "aws_s3_bucket",
                    "name": "data",
                    "properties": {
                        "bucket": "company-data",
                    },
                }
            ],
        }
    )

    assert project.version == "1"
    assert len(project.resources) == 1


def test_yaml_project_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        YAMLProject.model_validate(
            {
                "unknown_field": "unexpected",
            }
        )


def test_yaml_resource_requires_type():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "name": "data",
            }
        )


def test_yaml_resource_requires_name():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "type": "aws_s3_bucket",
            }
        )


def test_yaml_variable_requires_name():
    with pytest.raises(ValidationError):
        YAMLVariable.model_validate(
            {
                "description": "Bucket name",
            }
        )


def test_yaml_variable_rejects_invalid_sensitive_type():
    with pytest.raises(ValidationError):
        YAMLVariable.model_validate(
            {
                "name": "bucket_name",
                "sensitive": "not-a-boolean",
            }
        )


def test_yaml_resource_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "type": "aws_s3_bucket",
                "name": "data",
                "unexpected": True,
            }
        )


def test_yaml_resource_rejects_empty_type():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "type": "",
                "name": "data",
            }
        )


def test_yaml_resource_rejects_empty_name():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "type": "aws_s3_bucket",
                "name": "",
            }
        )


def test_yaml_variable_rejects_empty_name():
    with pytest.raises(ValidationError):
        YAMLVariable.model_validate(
            {
                "name": "",
            }
        )


def test_yaml_output_rejects_empty_name():
    from iac_converter.schema.yaml_schema import YAMLOutput

    with pytest.raises(ValidationError):
        YAMLOutput.model_validate(
            {
                "name": "",
                "value": "bucket-id",
            }
        )


def test_yaml_resource_rejects_whitespace_only_name():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "type": "aws_s3_bucket",
                "name": "   ",
            }
        )


def test_yaml_resource_rejects_whitespace_only_type():
    with pytest.raises(ValidationError):
        YAMLResource.model_validate(
            {
                "type": "   ",
                "name": "data",
            }
        )


from iac_converter.schema.yaml_schema import (
    YAMLBlock,
    YAMLDataSource,
    YAMLOutput,
)


@pytest.mark.parametrize(
    "model,data",
    [
        (YAMLVariable, {"name": "   "}),
        (YAMLOutput, {"name": "   ", "value": "test"}),
        (YAMLDataSource, {"type": "   ", "name": "data"}),
        (YAMLDataSource, {"type": "aws_s3_bucket", "name": "   "}),
        (YAMLBlock, {"type": "   "}),
    ],
)
def test_schema_models_reject_whitespace_only_identifiers(model, data):
    with pytest.raises(ValidationError):
        model.model_validate(data)


from iac_converter.schema.yaml_schema import YAMLProvider


def test_yaml_provider_accepts_valid_configuration():
    provider = YAMLProvider.model_validate(
        {
            "alias": "primary",
            "properties": {
                "region": "ap-south-1",
            },
        }
    )

    assert provider.alias == "primary"
    assert provider.properties["region"] == "ap-south-1"


def test_yaml_provider_rejects_invalid_properties_type():
    with pytest.raises(ValidationError):
        YAMLProvider.model_validate(
            {
                "properties": "invalid",
            }
        )


def test_yaml_provider_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        YAMLProvider.model_validate(
            {
                "unknown": True,
            }
        )


def test_yaml_provider_rejects_invalid_alias_type():
    with pytest.raises(ValidationError):
        YAMLProvider.model_validate(
            {
                "alias": 123,
            }
        )
