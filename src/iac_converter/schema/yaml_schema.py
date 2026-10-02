from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class YAMLProvider(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class YAMLResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    count: Any | None = None
    for_each: Any | None = None
    depends_on: list[Any] = Field(default_factory=list)
    lifecycle: dict[str, Any] = Field(default_factory=dict)


class YAMLVariable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: Any | None = None
    description: str | None = None
    default: Any | None = None
    sensitive: bool = False
    nullable: bool | None = None


class YAMLDataSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class YAMLOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
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