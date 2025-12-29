"""Unit tests for base models in a2ui_pydantic.base."""

import pytest
from pydantic import ValidationError

from a2ui_pydantic.base import (
    ActionContextValue,
    IconNameLiteralOrPath,
    LiteralArrayOrPath,
    LiteralBooleanOrPath,
    LiteralNumberOrPath,
    LiteralStringOrPath,
)
from a2ui_pydantic.enums import IconName


def test_literal_string_or_path():
    """Test LiteralStringOrPath validation."""
    # Valid cases
    assert LiteralStringOrPath(literalString="foo").literal_string == "foo"
    assert LiteralStringOrPath(path="/foo").path == "/foo"

    # Invalid cases
    with pytest.raises(ValidationError):
        LiteralStringOrPath()  # Neither
    with pytest.raises(ValidationError):
        LiteralStringOrPath(literalString="foo", path="/foo")  # Both


def test_literal_number_or_path():
    """Test LiteralNumberOrPath validation."""
    # Valid cases
    assert LiteralNumberOrPath(literalNumber=123.45).literal_number == 123.45
    assert LiteralNumberOrPath(path="/foo").path == "/foo"

    # Invalid cases
    with pytest.raises(ValidationError):
        LiteralNumberOrPath()
    with pytest.raises(ValidationError):
        LiteralNumberOrPath(literalNumber=1, path="/foo")


def test_literal_boolean_or_path():
    """Test LiteralBooleanOrPath validation."""
    # Valid cases
    assert LiteralBooleanOrPath(literalBoolean=True).literal_boolean is True
    assert LiteralBooleanOrPath(path="/foo").path == "/foo"

    # Invalid cases
    with pytest.raises(ValidationError):
        LiteralBooleanOrPath()
    with pytest.raises(ValidationError):
        LiteralBooleanOrPath(literalBoolean=True, path="/foo")


def test_literal_array_or_path():
    """Test LiteralArrayOrPath validation."""
    # Valid cases
    assert LiteralArrayOrPath(literalArray=["a", "b"]).literal_array == ["a", "b"]
    assert LiteralArrayOrPath(path="/foo").path == "/foo"

    # Invalid cases
    with pytest.raises(ValidationError):
        LiteralArrayOrPath()
    with pytest.raises(ValidationError):
        LiteralArrayOrPath(literalArray=[], path="/foo")


def test_action_context_value():
    """Test ActionContextValue validation."""
    # Valid cases
    assert ActionContextValue(literalString="s").literal_string == "s"
    assert ActionContextValue(literalNumber=1.0).literal_number == 1.0
    assert ActionContextValue(literalBoolean=False).literal_boolean is False
    assert ActionContextValue(path="/p").path == "/p"

    # Invalid cases
    with pytest.raises(ValidationError):
        ActionContextValue()  # None
    with pytest.raises(ValidationError):
        ActionContextValue(literalString="s", literalNumber=1.0)  # Multiple


def test_icon_name_literal_or_path():
    """Test IconNameLiteralOrPath validation."""
    # Valid cases
    assert (
        IconNameLiteralOrPath(literalString=IconName.ADD).literal_string
        == IconName.ADD
    )
    assert IconNameLiteralOrPath(path="/icon").path == "/icon"

    # Invalid cases
    with pytest.raises(ValidationError):
        IconNameLiteralOrPath()  # Neither
    with pytest.raises(ValidationError):
        IconNameLiteralOrPath(literalString=IconName.ADD, path="/icon")  # Both
    with pytest.raises(ValidationError):
        IconNameLiteralOrPath(literalString="invalid_icon")  # Invalid enum value
