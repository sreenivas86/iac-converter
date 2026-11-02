from dataclasses import dataclass

from .expression import Expression


@dataclass(frozen=True)
class Reference(Expression):
    """
    Reference to a Terraform resource.

    Examples:
        aws_s3_bucket.example
        aws_s3_bucket.example.id
    """

    resource_type: str
    resource_name: str
    attribute: str | None = None

    def to_string(self) -> str:
        value = f"{self.resource_type}.{self.resource_name}"

        if self.attribute:
            value += f".{self.attribute}"

        return value


@dataclass(frozen=True)
class DataSourceReference(Expression):
    """
    Reference to a Terraform data source.

    Example:
        data.aws_ami.example.id
    """

    data_source_type: str
    data_source_name: str
    attribute: str | None = None

    def to_string(self) -> str:
        value = f"data.{self.data_source_type}.{self.data_source_name}"

        if self.attribute:
            value += f".{self.attribute}"

        return value


@dataclass(frozen=True)
class VariableReference(Expression):
    """
    Reference to a Terraform input variable.

    Example:
        var.bucket_name
    """

    name: str

    def to_string(self) -> str:
        return f"var.{self.name}"


@dataclass(frozen=True)
class LocalReference(Expression):
    """
    Reference to a Terraform local value.

    Example:
        local.bucket_prefix
    """

    name: str

    def to_string(self) -> str:
        return f"local.{self.name}"


@dataclass(frozen=True)
class ModuleReference(Expression):
    """
    Reference to a Terraform module output.

    Example:
        module.vpc.vpc_id
    """

    module_name: str
    output_name: str

    def to_string(self) -> str:
        return f"module.{self.module_name}.{self.output_name}"


@dataclass(frozen=True)
class ForVariableReference(Expression):
    """Reference to a Terraform for-expression iteration variable."""

    name: str

    def to_string(self) -> str:
        return self.name
