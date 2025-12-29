"""Unit tests for components in a2ui_pydantic.components."""

import pytest
from pydantic import ValidationError

# pylint: disable=no-member

from a2ui_pydantic.actions import Action
from a2ui_pydantic.components import (
    AudioPlayerComponent,
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    Children,
    ChildrenTemplate,
    ColumnComponent,
    DateTimeInputComponent,
    DividerComponent,
    IconComponent,
    ImageComponent,
    ListComponent,
    ModalComponent,
    MultipleChoiceComponent,
    MultipleChoiceOption,
    RowComponent,
    SliderComponent,
    TabItem,
    TabsComponent,
    TextComponent,
    TextFieldComponent,
    VideoComponent,
)
from a2ui_pydantic.enums import (
    Alignment,
    DividerAxis,
    Distribution,
    IconName,
    ListDirection,
    TextFieldType,
    TextUsageHint,
)


def test_children():
    """Test Children validation."""
    # Valid cases
    assert Children(explicitList=["c1", "c2"]).explicit_list == ["c1", "c2"]
    template = ChildrenTemplate(componentId="t1", dataBinding="/items")
    assert Children(template=template).template == template

    # Invalid cases
    with pytest.raises(ValidationError):
        Children()  # Neither
    with pytest.raises(ValidationError):
        Children(explicitList=[], template=template)  # Both


def test_text_component():
    """Test TextComponent validation."""
    # Valid
    c = TextComponent(text={"literalString": "Hello"}, usageHint=TextUsageHint.H1)
    assert c.text.literal_string == "Hello"
    assert c.usage_hint == TextUsageHint.H1

    # Invalid
    with pytest.raises(ValidationError):
        TextComponent(text={})  # Missing required field content in LiteralStringOrPath


def test_image_component():
    """Test ImageComponent validation."""
    # Valid
    c = ImageComponent(url={"literalString": "http://img.com"})
    assert c.url.literal_string == "http://img.com"

    with pytest.raises(ValidationError):
        ImageComponent(url={})


def test_icon_component():
    """Test IconComponent validation."""
    # Valid
    c = IconComponent(name={"literalString": IconName.ADD})
    assert c.name.literal_string == IconName.ADD

    # Invalid
    with pytest.raises(ValidationError):
        IconComponent(name={"literalString": "INVALID_ICON"})


def test_button_component():
    """Test ButtonComponent validation."""
    # Valid
    action = Action(name="click")
    c = ButtonComponent(child="c1", action=action)
    assert c.child == "c1"
    assert c.action == action
    assert c.primary is None

    # With primary flag
    c2 = ButtonComponent(child="c1", action=action, primary=True)
    assert c2.primary is True

    # Invalid
    with pytest.raises(ValidationError):
        ButtonComponent(child="c1")  # Missing action


def test_video_component():
    """Test VideoComponent validation."""
    # Valid with literal string
    c = VideoComponent(url={"literalString": "http://video.com"})
    assert c.url.literal_string == "http://video.com"

    # Valid with path
    c2 = VideoComponent(url={"path": "/video/url"})
    assert c2.url.path == "/video/url"

    # Invalid
    with pytest.raises(ValidationError):
        VideoComponent(url={})


def test_audio_player_component():
    """Test AudioPlayerComponent validation."""
    # Valid with just URL
    c = AudioPlayerComponent(url={"literalString": "http://audio.com"})
    assert c.url.literal_string == "http://audio.com"
    assert c.description is None

    # Valid with description
    c2 = AudioPlayerComponent(
        url={"literalString": "http://audio.com"},
        description={"literalString": "Song Title"},
    )
    assert c2.description.literal_string == "Song Title"

    # Invalid
    with pytest.raises(ValidationError):
        AudioPlayerComponent(url={})


def test_row_component():
    """Test RowComponent validation."""
    # Valid with explicit list
    children = Children(explicitList=["c1", "c2"])
    c = RowComponent(children=children)
    assert c.children.explicit_list == ["c1", "c2"]
    assert c.distribution is None
    assert c.alignment is None

    # Valid with all fields
    c2 = RowComponent(
        children=children,
        distribution=Distribution.CENTER,
        alignment=Alignment.STRETCH,
    )
    assert c2.distribution == Distribution.CENTER
    assert c2.alignment == Alignment.STRETCH

    # Invalid
    with pytest.raises(ValidationError):
        RowComponent(children={})


def test_column_component():
    """Test ColumnComponent validation."""
    # Valid with template
    template = ChildrenTemplate(componentId="t1", dataBinding="/items")
    children = Children(template=template)
    c = ColumnComponent(children=children)
    assert c.children.template == template

    # Valid with distribution and alignment
    c2 = ColumnComponent(
        children=children,
        distribution=Distribution.SPACE_BETWEEN,
        alignment=Alignment.CENTER,
    )
    assert c2.distribution == Distribution.SPACE_BETWEEN
    assert c2.alignment == Alignment.CENTER


def test_list_component():
    """Test ListComponent validation."""
    children = Children(explicitList=["c1"])
    # Valid
    c = ListComponent(children=children)
    assert c.children.explicit_list == ["c1"]
    assert c.direction is None
    assert c.alignment is None

    # Valid with all fields
    c2 = ListComponent(
        children=children,
        direction=ListDirection.VERTICAL,
        alignment=Alignment.START,
    )
    assert c2.direction == ListDirection.VERTICAL
    assert c2.alignment == Alignment.START


def test_card_component():
    """Test CardComponent validation."""
    # Valid
    c = CardComponent(child="child1")
    assert c.child == "child1"

    # Invalid - missing child
    with pytest.raises(ValidationError):
        CardComponent()


def test_tabs_component():
    """Test TabsComponent and TabItem validation."""
    # Valid
    tab_item = TabItem(
        title={"literalString": "Tab 1"},
        child="child1",
    )
    c = TabsComponent(tabItems=[tab_item])
    assert len(c.tab_items) == 1
    assert c.tab_items[0].title.literal_string == "Tab 1"
    assert c.tab_items[0].child == "child1"

    # Valid with path-based title
    tab_item2 = TabItem(title={"path": "/tabs/title"}, child="child2")
    c2 = TabsComponent(tabItems=[tab_item, tab_item2])
    assert len(c2.tab_items) == 2

    # Valid - empty list is allowed
    c3 = TabsComponent(tabItems=[])
    assert len(c3.tab_items) == 0

    # Invalid TabItem - missing title
    with pytest.raises(ValidationError):
        TabItem(child="child1")


def test_divider_component():
    """Test DividerComponent validation."""
    # Valid without axis
    c = DividerComponent()
    assert c.axis is None

    # Valid with axis
    c2 = DividerComponent(axis=DividerAxis.HORIZONTAL)
    assert c2.axis == DividerAxis.HORIZONTAL

    c3 = DividerComponent(axis=DividerAxis.VERTICAL)
    assert c3.axis == DividerAxis.VERTICAL


def test_modal_component():
    """Test ModalComponent validation."""
    # Valid
    c = ModalComponent(entryPointChild="button1", contentChild="content1")
    assert c.entry_point_child == "button1"
    assert c.content_child == "content1"

    # Invalid - missing entryPointChild
    with pytest.raises(ValidationError):
        ModalComponent(contentChild="content1")

    # Invalid - missing contentChild
    with pytest.raises(ValidationError):
        ModalComponent(entryPointChild="button1")


def test_checkbox_component():
    """Test CheckBoxComponent validation."""
    # Valid
    c = CheckBoxComponent(
        label={"literalString": "Check me"},
        value={"literalBoolean": True},
    )
    assert c.label.literal_string == "Check me"
    assert c.value.literal_boolean is True

    # Valid with path-based values
    c2 = CheckBoxComponent(
        label={"path": "/form/label"},
        value={"path": "/form/checked"},
    )
    assert c2.label.path == "/form/label"
    assert c2.value.path == "/form/checked"

    # Invalid - missing label
    with pytest.raises(ValidationError):
        CheckBoxComponent(value={"literalBoolean": True})

    # Invalid - missing value
    with pytest.raises(ValidationError):
        CheckBoxComponent(label={"literalString": "Label"})


def test_text_field_component():
    """Test TextFieldComponent validation."""
    # Valid with just label
    c = TextFieldComponent(label={"literalString": "Name"})
    assert c.label.literal_string == "Name"
    assert c.text is None
    assert c.text_field_type is None
    assert c.validation_regexp is None

    # Valid with all fields
    c2 = TextFieldComponent(
        label={"literalString": "Email"},
        text={"literalString": "user@example.com"},
        textFieldType=TextFieldType.SHORT_TEXT,
        validationRegexp=r"^[^@]+@[^@]+\.[^@]+$",
    )
    assert c2.text.literal_string == "user@example.com"
    assert c2.text_field_type == TextFieldType.SHORT_TEXT
    assert c2.validation_regexp == r"^[^@]+@[^@]+\.[^@]+$"

    # Invalid - missing label
    with pytest.raises(ValidationError):
        TextFieldComponent()


def test_date_time_input_component():
    """Test DateTimeInputComponent validation."""
    # Valid with just value
    c = DateTimeInputComponent(value={"literalString": "2024-01-01T00:00:00Z"})
    assert c.value.literal_string == "2024-01-01T00:00:00Z"
    assert c.enable_date is None
    assert c.enable_time is None

    # Valid with all fields
    c2 = DateTimeInputComponent(
        value={"path": "/event/date"},
        enableDate=True,
        enableTime=False,
    )
    assert c2.value.path == "/event/date"
    assert c2.enable_date is True
    assert c2.enable_time is False

    # Invalid - missing value
    with pytest.raises(ValidationError):
        DateTimeInputComponent()


def test_multiple_choice_component():
    """Test MultipleChoiceComponent and MultipleChoiceOption validation."""
    # Valid
    option1 = MultipleChoiceOption(
        label={"literalString": "Option 1"},
        value="opt1",
    )
    option2 = MultipleChoiceOption(
        label={"path": "/options/label"},
        value="opt2",
    )
    c = MultipleChoiceComponent(
        selections={"literalArray": ["opt1"]},
        options=[option1, option2],
    )
    assert c.selections.literal_array == ["opt1"]
    assert len(c.options) == 2
    assert c.max_allowed_selections is None

    # Valid with maxAllowedSelections
    c2 = MultipleChoiceComponent(
        selections={"path": "/form/selections"},
        options=[option1],
        maxAllowedSelections=3,
    )
    assert c2.max_allowed_selections == 3

    # Invalid - missing selections
    with pytest.raises(ValidationError):
        MultipleChoiceComponent(options=[option1])

    # Invalid - missing options
    with pytest.raises(ValidationError):
        MultipleChoiceComponent(selections={"literalArray": []})

    # Invalid option - missing label
    with pytest.raises(ValidationError):
        MultipleChoiceOption(value="opt1")


def test_slider_component():
    """Test SliderComponent validation."""
    # Valid with just value
    c = SliderComponent(value={"literalNumber": 50.0})
    assert c.value.literal_number == 50.0
    assert c.min_value is None
    assert c.max_value is None

    # Valid with all fields
    c2 = SliderComponent(
        value={"path": "/slider/value"},
        minValue=0.0,
        maxValue=100.0,
    )
    assert c2.value.path == "/slider/value"
    assert c2.min_value == 0.0
    assert c2.max_value == 100.0

    # Invalid - missing value
    with pytest.raises(ValidationError):
        SliderComponent()
