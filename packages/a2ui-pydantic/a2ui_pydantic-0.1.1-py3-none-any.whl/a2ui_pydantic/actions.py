"""Action models for A2UI schema.

This module contains models for button actions and their context.
"""

from pydantic import BaseModel, Field

from a2ui_pydantic.base import ActionContextValue


class ActionContextItem(BaseModel):
    """A single key-value pair in an action context.

    Attributes:
        key: The key for this context item.
        value: The value, which can be a literal or a path to a data model value.
    """

    key: str = Field(..., description="The key for this context item.")
    value: ActionContextValue = Field(
        ..., description="The value to be included in the context."
    )


class Action(BaseModel):
    """The client-side action to be dispatched when a button is clicked.

    Attributes:
        name: The name of the action.
        context: Optional array of key-value pairs to include in the action context.
    """

    name: str = Field(..., description="The name of the action.")
    context: list[ActionContextItem] | None = Field(
        None, description="Optional context payload for the action."
    )
