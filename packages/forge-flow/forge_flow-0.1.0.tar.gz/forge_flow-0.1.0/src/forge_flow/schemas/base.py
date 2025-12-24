"""Strict schema base class using Pydantic v2."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class StrictSchema(BaseModel):
    """Base class for strict data schemas with immutability and validation."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        validate_assignment=True,
        frozen=True,
        use_enum_values=True,
        validate_default=True,
        arbitrary_types_allowed=False,
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrictSchema":
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> "StrictSchema":
        return cls.model_validate_json(json_str)
