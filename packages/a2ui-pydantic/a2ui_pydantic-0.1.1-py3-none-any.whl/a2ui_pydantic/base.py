"""Base models for A2UI schema.

This module contains common patterns used throughout the A2UI schema,
such as literal values and data model path references.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from a2ui_pydantic.enums import IconName


class LiteralStringOrPath(BaseModel):
    """A value that can be either a literal string or a path to a data model value.

    Attributes:
        literal_string: A literal string value.
        path: A path to a value in the data model (e.g., '/doc/title').
    """

    literal_string: str | None = Field(None, alias="literalString")
    path: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one of literal_string or path is provided."""
        has_literal = self.literal_string is not None
        has_path = self.path is not None
        if not has_literal ^ has_path:
            raise ValueError(
                "Exactly one of 'literalString' or 'path' must be provided"
            )
        return self


class LiteralNumberOrPath(BaseModel):
    """A value that can be either a literal number or a path to a data model value.

    Attributes:
        literal_number: A literal number value.
        path: A path to a value in the data model (e.g., '/restaurant/cost').
    """

    literal_number: float | None = Field(None, alias="literalNumber")
    path: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one of literal_number or path is provided."""
        has_literal = self.literal_number is not None
        has_path = self.path is not None
        if not has_literal ^ has_path:
            raise ValueError(
                "Exactly one of 'literalNumber' or 'path' must be provided"
            )
        return self


class LiteralBooleanOrPath(BaseModel):
    """A value that can be either a literal boolean or a path to a data model value.

    Attributes:
        literal_boolean: A literal boolean value.
        path: A path to a value in the data model (e.g., '/filter/open').
    """

    literal_boolean: bool | None = Field(None, alias="literalBoolean")
    path: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one of literal_boolean or path is provided."""
        has_literal = self.literal_boolean is not None
        has_path = self.path is not None
        if not has_literal ^ has_path:
            raise ValueError(
                "Exactly one of 'literalBoolean' or 'path' must be provided"
            )
        return self


class LiteralArrayOrPath(BaseModel):
    """A value that can be either a literal array of strings or a path to a data model array.

    Attributes:
        literal_array: A literal array of string values.
        path: A path to an array in the data model (e.g., '/hotel/options').
    """

    literal_array: list[str] | None = Field(None, alias="literalArray")
    path: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one of literal_array or path is provided."""
        has_literal = self.literal_array is not None
        has_path = self.path is not None
        if not has_literal ^ has_path:
            raise ValueError(
                "Exactly one of 'literalArray' or 'path' must be provided"
            )
        return self



class ActionContextValue(BaseModel):
    """A value in an action context that can be a literal or a path.

    Attributes:
        path: A path to a data model value (e.g., '/user/name').
        literal_string: A literal string value.
        literal_number: A literal number value.
        literal_boolean: A literal boolean value.
    """

    path: str | None = None
    literal_string: str | None = Field(None, alias="literalString")
    literal_number: float | None = Field(None, alias="literalNumber")
    literal_boolean: bool | None = Field(None, alias="literalBoolean")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one property is provided."""
        fields = ["path", "literal_string", "literal_number", "literal_boolean"]
        non_none_count = sum(
            1 for field in fields if getattr(self, field) is not None
        )
        if non_none_count != 1:
            raise ValueError(
                "Exactly one of 'path', 'literalString', 'literalNumber', "
                "or 'literalBoolean' must be provided"
            )
        return self


class IconNameLiteralOrPath(BaseModel):
    """A value for icon name that can be either a literal icon name or a path.

    Attributes:
        literal_string: A literal icon name from the IconName enum.
        path: A path to a value in the data model (e.g., '/form/submit').
    """

    literal_string: str | None = Field(None, alias="literalString")
    path: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one of literal_string or path is provided."""
        has_literal = self.literal_string is not None
        has_path = self.path is not None
        if not has_literal ^ has_path:
            raise ValueError(
                "Exactly one of 'literalString' or 'path' must be provided"
            )
        # Validate that literal_string is a valid IconName
        if has_literal and self.literal_string not in [
            icon.value for icon in IconName
        ]:
            raise ValueError(
                f"literalString must be one of the valid IconName values, "
                f"got: {self.literal_string}"
            )
        return self
