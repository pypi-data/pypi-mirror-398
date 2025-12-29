"""Data model structures for A2UI schema.

This module contains models for data model updates and entries.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataModelMapEntry(BaseModel):
    """One entry in a map represented as an adjacency list.

    Attributes:
        key: The key for this map entry.
        value_string: A string value.
        value_number: A number value.
        value_boolean: A boolean value.
    """

    key: str = Field(..., description="The key for this map entry.")
    value_string: str | None = Field(None, alias="valueString")
    value_number: float | None = Field(None, alias="valueNumber")
    value_boolean: bool | None = Field(None, alias="valueBoolean")


    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one_value(self):
        """Validate that exactly one value property is provided."""
        fields = ["value_string", "value_number", "value_boolean"]
        non_none_count = sum(
            1 for field in fields if getattr(self, field) is not None
        )
        if non_none_count != 1:
            raise ValueError(
                "Exactly one of 'valueString', 'valueNumber', or 'valueBoolean' must be provided"
            )
        return self


class DataModelEntry(BaseModel):
    """A single data entry in a data model update.

    Exactly one 'value*' property should be provided alongside the key.

    Attributes:
        key: The key for this data entry.
        value_string: A string value.
        value_number: A number value.
        value_boolean: A boolean value.
        value_map: A map represented as an adjacency list.
    """

    key: str = Field(..., description="The key for this data entry.")
    value_string: str | None = Field(None, alias="valueString")
    value_number: float | None = Field(None, alias="valueNumber")
    value_boolean: bool | None = Field(None, alias="valueBoolean")
    value_map: list[DataModelMapEntry] | None = Field(None, alias="valueMap")


    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one_value(self):
        """Validate that exactly one value property is provided."""
        fields = ["value_string", "value_number", "value_boolean", "value_map"]
        non_none_count = sum(
            1 for field in fields if getattr(self, field) is not None
        )
        if non_none_count != 1:
            raise ValueError(
                "Exactly one of 'valueString', 'valueNumber', 'valueBoolean', "
                "or 'valueMap' must be provided"
            )
        return self
