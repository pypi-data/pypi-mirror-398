"""Unit tests for actions in a2ui_pydantic.actions."""

import pytest
from pydantic import ValidationError

from a2ui_pydantic.actions import Action, ActionContextItem
from a2ui_pydantic.base import ActionContextValue


def test_action():
    """Test Action validation."""
    # Valid without context
    action = Action(name="click")
    assert action.name == "click"
    assert action.context is None

    # Valid with context
    context_item = ActionContextItem(
        key="userId",
        value=ActionContextValue(literalString="123"),
    )
    action2 = Action(name="submit", context=[context_item])
    assert action2.name == "submit"
    assert len(action2.context) == 1
    assert action2.context[0].key == "userId"
    assert action2.context[0].value.literal_string == "123"

    # Valid with multiple context items
    context_item2 = ActionContextItem(
        key="count",
        value=ActionContextValue(literalNumber=5.0),
    )
    action3 = Action(name="update", context=[context_item, context_item2])
    assert len(action3.context) == 2

    # Invalid - missing name
    with pytest.raises(ValidationError):
        Action()


def test_action_context_item():
    """Test ActionContextItem validation."""
    # Valid with string value
    item = ActionContextItem(
        key="name",
        value=ActionContextValue(literalString="John"),
    )
    assert item.key == "name"
    assert item.value.literal_string == "John"  # pylint: disable=no-member

    # Valid with number value
    item2 = ActionContextItem(
        key="age",
        value=ActionContextValue(literalNumber=30.0),
    )
    assert item2.value.literal_number == 30.0  # pylint: disable=no-member

    # Valid with boolean value
    item3 = ActionContextItem(
        key="active",
        value=ActionContextValue(literalBoolean=True),
    )
    assert item3.value.literal_boolean is True  # pylint: disable=no-member

    # Valid with path value
    item4 = ActionContextItem(
        key="userId",
        value=ActionContextValue(path="/user/id"),
    )
    assert item4.value.path == "/user/id"  # pylint: disable=no-member

    # Invalid - missing key
    with pytest.raises(ValidationError):
        ActionContextItem(value=ActionContextValue(literalString="value"))

    # Invalid - missing value
    with pytest.raises(ValidationError):
        ActionContextItem(key="key")
