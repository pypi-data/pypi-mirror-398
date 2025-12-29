"""Unit tests for data model in a2ui_pydantic.data_model."""

import pytest
from pydantic import ValidationError

from a2ui_pydantic.data_model import DataModelEntry, DataModelMapEntry


def test_data_model_map_entry():
    """Test DataModelMapEntry validation."""
    # Valid cases
    assert DataModelMapEntry(key="k", valueString="v").value_string == "v"
    assert DataModelMapEntry(key="k", valueNumber=1.0).value_number == 1.0
    assert DataModelMapEntry(key="k", valueBoolean=True).value_boolean is True

    # Invalid cases
    with pytest.raises(ValidationError):
        DataModelMapEntry(key="k")  # No value
    with pytest.raises(ValidationError):
        DataModelMapEntry(key="k", valueString="v", valueNumber=1.0)  # Multiple values


def test_data_model_entry():
    """Test DataModelEntry validation."""
    # Valid cases
    assert DataModelEntry(key="k", valueString="v").value_string == "v"
    assert DataModelEntry(key="k", valueNumber=1.0).value_number == 1.0
    assert DataModelEntry(key="k", valueBoolean=True).value_boolean is True

    map_entry = DataModelMapEntry(key="mk", valueString="mv")
    assert DataModelEntry(key="k", valueMap=[map_entry]).value_map == [map_entry]

    # Invalid cases
    with pytest.raises(ValidationError):
        DataModelEntry(key="k")  # No value
    with pytest.raises(ValidationError):
        DataModelEntry(key="k", valueString="v", valueNumber=1.0)  # Multiple values
