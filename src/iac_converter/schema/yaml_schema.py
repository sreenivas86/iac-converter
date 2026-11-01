from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class YAMLProvider(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class YAMLBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str

    @field_validator("type")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be empty or whitespace")
        return value

    labels: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    blocks: list["YAMLBlock"] = Field(default_factory=list)


class YAMLResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    name: str = Field(min_length=1)

    @field_validator("type", "name")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be empty or whitespace")
        return value

    properties: dict[str, Any] = Field(default_factory=dict)
    blocks: list[YAMLBlock] = Field(default_factory=list)
    count: Any | None = None
    for_each: Any | None = None
    depends_on: list[Any] = Field(default_factory=list)
    lifecycle: dict[str, Any] = Field(default_factory=dict)
    provisioners: list[dict[str, Any]] = Field(default_factory=list)


class YAMLVariable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be empty or whitespace")
        return value

    type: Any | None = None
    description: str | None = None
    default: Any | None = None
    sensitive: bool = False
    nullable: bool | None = None


class YAMLDataSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str

    @field_validator("type", "name")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be empty or whitespace")
        return value

    properties: dict[str, Any] = Field(default_factory=dict)


class YAMLOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be empty or whitespace")
        return value

    value: Any
    description: str | None = None
    sensitive: bool = False


class YAMLProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "1"
    terraform: dict[str, Any] = Field(default_factory=dict)

    providers: dict[str, YAMLProvider] = Field(default_factory=dict)

    variables: list[YAMLVariable] = Field(default_factory=list)

    resources: list[YAMLResource] = Field(default_factory=list)

    data_sources: list[YAMLDataSource] = Field(default_factory=list)

    outputs: list[YAMLOutput] = Field(default_factory=list)

    locals: dict[str, Any] = Field(default_factory=dict)
