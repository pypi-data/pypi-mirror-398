from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TemplateFlavor(BaseModel):
    id: str = Field(min_length=1)
    path: Optional[str] = None
    name: Optional[str] = None
    next_steps: Optional[list[str]] = Field(default=None, alias="nextSteps")

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore")

    @model_validator(mode="after")
    def ensure_relative_path(self) -> "TemplateFlavor":
        if self.path and os.path.isabs(self.path):
            raise ValueError(
                f"Flavor path must be relative for {self.id}: {self.path}"
            )
        return self


class TemplateEntry(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    flavors: list[TemplateFlavor] = Field(min_length=1)
    order: Optional[int] = None
    category: Optional[str] = None
    aliases: Optional[list[str]] = None
    hidden: Optional[bool] = None
    deprecated: Optional[bool] = None

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore")

    @field_validator("flavors", mode="before")
    @classmethod
    def coerce_flavors(cls, value: object) -> object:
        if isinstance(value, list) and value and all(
            isinstance(item, str) for item in value
        ):
            return [TemplateFlavor(id=item) for item in value]
        return value


class TemplateManifest(BaseModel):
    version: Optional[int] = None
    templates: list[TemplateEntry] = Field(min_length=1)

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="ignore")


class TemplateInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    flavors: list[str]
    flavor_details: dict[str, TemplateFlavor]
    order: Optional[int] = None
    category: Optional[str] = None
    aliases: Optional[list[str]] = None
    hidden: Optional[bool] = None
    deprecated: Optional[bool] = None

    model_config = ConfigDict(frozen=True)
