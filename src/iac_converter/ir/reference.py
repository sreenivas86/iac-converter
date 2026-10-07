from dataclasses import dataclass

from .expression import Expression


@dataclass(frozen=True)
class Reference(Expression):
    """
    Reference to another Terraform object.

    Examples:

        aws_s3_bucket.data.id
        aws_s3_bucket.data
    """

    resource_type: str
    resource_name: str
    attribute: str | None = None

    def to_string(self) -> str:
        value = f"{self.resource_type}.{self.resource_name}"

        if self.attribute:
            value += f".{self.attribute}"

        return value