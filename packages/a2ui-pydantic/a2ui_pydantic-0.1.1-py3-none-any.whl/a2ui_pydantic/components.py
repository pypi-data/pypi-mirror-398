"""Component models for A2UI schema.

This module contains all component types that can be used in A2UI surfaces.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from a2ui_pydantic.actions import Action
from a2ui_pydantic.base import (
    IconNameLiteralOrPath,
    LiteralArrayOrPath,
    LiteralBooleanOrPath,
    LiteralNumberOrPath,
    LiteralStringOrPath,
)
from a2ui_pydantic.enums import (
    Alignment,
    DividerAxis,
    Distribution,
    ImageFit,
    ImageUsageHint,
    ListDirection,
    TextFieldType,
    TextUsageHint,
)


class ChildrenTemplate(BaseModel):
    """A template for generating a dynamic list of children from a data model list.

    Attributes:
        component_id: The component to use as a template.
        data_binding: The path to the map of components in the data model.
            Values in the map will define the list of children.
    """

    component_id: str = Field(..., alias="componentId")
    data_binding: str = Field(..., alias="dataBinding")

    model_config = ConfigDict(populate_by_name=True)


class Children(BaseModel):
    """Defines the children of a container component.

    Use 'explicit_list' for a fixed set of children, or 'template' to generate
    children from a data list.

    Attributes:
        explicit_list: A fixed list of component IDs.
        template: A template for generating children from a data model list.
    """

    explicit_list: list[str] | None = Field(None, alias="explicitList")
    template: ChildrenTemplate | None = None


    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one(self):
        """Validate that exactly one of explicit_list or template is provided."""
        has_explicit = self.explicit_list is not None
        has_template = self.template is not None
        if not has_explicit ^ has_template:
            raise ValueError(
                "Exactly one of 'explicitList' or 'template' must be provided"
            )
        return self


# Text Component
class TextComponent(BaseModel):
    """A text component that displays text content.

    Attributes:
        text: The text content to display. Can be a literal string or a path
            to a value in the data model (e.g., '/doc/title').
        usage_hint: A hint for the base text style.
    """

    text: LiteralStringOrPath = Field(
        ...,
        description=(
            "The text content to display. This can be a literal string or a "
            "reference to a value in the data model ('path', e.g., '/doc/title'). "
            "While simple Markdown formatting is supported (i.e. without HTML, "
            "images, or links), utilizing dedicated UI components is generally "
            "preferred for a richer and more structured presentation."
        ),
    )
    usage_hint: TextUsageHint | None = Field(None, alias="usageHint")

    model_config = ConfigDict(populate_by_name=True)


# Image Component
class ImageComponent(BaseModel):
    """An image component that displays an image.

    Attributes:
        url: The URL of the image to display. Can be a literal string or a path
            to a value in the data model (e.g., '/thumbnail/url').
        fit: Specifies how the image should be resized to fit its container.
            Corresponds to the CSS 'object-fit' property.
        usage_hint: A hint for the image size and style.
    """

    url: LiteralStringOrPath = Field(
        ...,
        description=(
            "The URL of the image to display. This can be a literal string "
            "('literal') or a reference to a value in the data model "
            "('path', e.g. '/thumbnail/url')."
        ),
    )
    fit: ImageFit | None = None
    usage_hint: ImageUsageHint | None = Field(None, alias="usageHint")

    model_config = ConfigDict(populate_by_name=True)


# Icon Component
class IconComponent(BaseModel):
    """An icon component that displays an icon.

    Attributes:
        name: The name of the icon to display. Can be a literal icon name from
            the IconName enum or a path to a value in the data model (e.g., '/form/submit').
    """

    name: IconNameLiteralOrPath = Field(
        ...,
        description=(
            "The name of the icon to display. This can be a literal string or "
            "a reference to a value in the data model ('path', e.g. '/form/submit')."
        ),
    )


# Video Component
class VideoComponent(BaseModel):
    """A video component that displays a video.

    Attributes:
        url: The URL of the video to display. Can be a literal string or a path
            to a value in the data model (e.g., '/video/url').
    """

    url: LiteralStringOrPath = Field(
        ...,
        description=(
            "The URL of the video to display. This can be a literal string or "
            "a reference to a value in the data model ('path', e.g. '/video/url')."
        ),
    )


# AudioPlayer Component
class AudioPlayerComponent(BaseModel):
    """An audio player component that plays audio.

    Attributes:
        url: The URL of the audio to be played. Can be a literal string or a path
            to a value in the data model (e.g., '/song/url').
        description: A description of the audio, such as a title or summary.
            Can be a literal string or a path to a value in the data model
            (e.g., '/song/title').
    """

    url: LiteralStringOrPath = Field(
        ...,
        description=(
            "The URL of the audio to be played. This can be a literal string "
            "('literal') or a reference to a value in the data model "
            "('path', e.g. '/song/url')."
        ),
    )
    description: LiteralStringOrPath | None = Field(
        None,
        description=(
            "A description of the audio, such as a title or summary. This can "
            "be a literal string or a reference to a value in the data model "
            "('path', e.g. '/song/title')."
        ),
    )


# Row Component
class RowComponent(BaseModel):
    """A row component that arranges children horizontally.

    Attributes:
        children: Defines the children. Use 'explicit_list' for a fixed set of
            children, or 'template' to generate children from a data list.
        distribution: Defines the arrangement of children along the main axis
            (horizontally). Corresponds to the CSS 'justify-content' property.
        alignment: Defines the alignment of children along the cross axis
            (vertically). Corresponds to the CSS 'align-items' property.
    """

    children: Children = Field(
        ...,
        description=(
            "Defines the children. Use 'explicitList' for a fixed set of "
            "children, or 'template' to generate children from a data list."
        ),
    )
    distribution: Distribution | None = Field(
        None,
        description=(
            "Defines the arrangement of children along the main axis "
            "(horizontally). This corresponds to the CSS 'justify-content' property."
        ),
    )
    alignment: Alignment | None = Field(
        None,
        description=(
            "Defines the alignment of children along the cross axis "
            "(vertically). This corresponds to the CSS 'align-items' property."
        ),
    )


# Column Component
class ColumnComponent(BaseModel):
    """A column component that arranges children vertically.

    Attributes:
        children: Defines the children. Use 'explicit_list' for a fixed set of
            children, or 'template' to generate children from a data list.
        distribution: Defines the arrangement of children along the main axis
            (vertically). Corresponds to the CSS 'justify-content' property.
        alignment: Defines the alignment of children along the cross axis
            (horizontally). Corresponds to the CSS 'align-items' property.
    """

    children: Children = Field(
        ...,
        description=(
            "Defines the children. Use 'explicitList' for a fixed set of "
            "children, or 'template' to generate children from a data list."
        ),
    )
    distribution: Distribution | None = Field(
        None,
        description=(
            "Defines the arrangement of children along the main axis "
            "(vertically). This corresponds to the CSS 'justify-content' property."
        ),
    )
    alignment: Alignment | None = Field(
        None,
        description=(
            "Defines the alignment of children along the cross axis "
            "(horizontally). This corresponds to the CSS 'align-items' property."
        ),
    )


# List Component
class ListComponent(BaseModel):
    """A list component that displays a list of items.

    Attributes:
        children: Defines the children. Use 'explicit_list' for a fixed set of
            children, or 'template' to generate children from a data list.
        direction: The direction in which the list items are laid out.
        alignment: Defines the alignment of children along the cross axis.
    """

    children: Children = Field(
        ...,
        description=(
            "Defines the children. Use 'explicitList' for a fixed set of "
            "children, or 'template' to generate children from a data list."
        ),
    )
    direction: ListDirection | None = Field(
        None, description="The direction in which the list items are laid out."
    )
    alignment: Alignment | None = Field(
        None, description="Defines the alignment of children along the cross axis."
    )


# Card Component
class CardComponent(BaseModel):
    """A card component that wraps a child component.

    Attributes:
        child: The ID of the component to be rendered inside the card.
    """

    child: str = Field(
        ..., description="The ID of the component to be rendered inside the card."
    )


# Tabs Component
class TabItem(BaseModel):
    """A single tab item in a Tabs component.

    Attributes:
        title: The tab title. Can be a literal value or a path to a data model
            value (e.g., '/options/title').
        child: The ID of the child component to display in this tab.
    """

    title: LiteralStringOrPath = Field(
        ...,
        description=(
            "The tab title. Defines the value as either a literal value or a "
            "path to data model value (e.g. '/options/title')."
        ),
    )
    child: str = Field(..., description="The ID of the child component.")


class TabsComponent(BaseModel):
    """A tabs component that displays multiple tabs.

    Attributes:
        tab_items: An array of objects, where each object defines a tab with
            a title and a child component.
    """

    tab_items: list[TabItem] = Field(
        ...,
        alias="tabItems",
        description=(
            "An array of objects, where each object defines a tab with a "
            "title and a child component."
        ),
    )

    model_config = ConfigDict(populate_by_name=True)


# Divider Component
class DividerComponent(BaseModel):
    """A divider component that displays a visual separator.

    Attributes:
        axis: The orientation of the divider.
    """

    axis: DividerAxis | None = Field(
        None, description="The orientation of the divider."
    )


# Modal Component
class ModalComponent(BaseModel):
    """A modal component that displays content in a modal dialog.

    Attributes:
        entry_point_child: The ID of the component that opens the modal when
            interacted with (e.g., a button).
        content_child: The ID of the component to be displayed inside the modal.
    """

    entry_point_child: str = Field(
        ...,
        alias="entryPointChild",
        description=(
            "The ID of the component that opens the modal when interacted "
            "with (e.g., a button)."
        ),
    )
    content_child: str = Field(
        ...,
        alias="contentChild",
        description="The ID of the component to be displayed inside the modal.",
    )

    model_config = ConfigDict(populate_by_name=True)


# Button Component
class ButtonComponent(BaseModel):
    """A button component that triggers an action when clicked.

    Attributes:
        child: The ID of the component to display in the button, typically a
            Text component.
        primary: Indicates if this button should be styled as the primary action.
        action: The client-side action to be dispatched when the button is clicked.
    """

    child: str = Field(
        ...,
        description=(
            "The ID of the component to display in the button, typically a "
            "Text component."
        ),
    )
    primary: bool | None = Field(
        None, description="Indicates if this button should be styled as the primary action."
    )
    action: Action = Field(
        ...,
        description=(
            "The client-side action to be dispatched when the button is clicked. "
            "It includes the action's name and an optional context payload."
        ),
    )


# CheckBox Component
class CheckBoxComponent(BaseModel):
    """A checkbox component that allows boolean input.

    Attributes:
        label: The text to display next to the checkbox. Can be a literal value
            or a path to a data model value (e.g., '/option/label').
        value: The current state of the checkbox (true for checked, false for
            unchecked). Can be a literal boolean or a reference to a value in
            the data model (e.g., '/filter/open').
    """

    label: LiteralStringOrPath = Field(
        ...,
        description=(
            "The text to display next to the checkbox. Defines the value as "
            "either a literal value or a path to data model ('path', e.g. '/option/label')."
        ),
    )
    value: LiteralBooleanOrPath = Field(
        ...,
        description=(
            "The current state of the checkbox (true for checked, false for "
            "unchecked). This can be a literal boolean ('literalBoolean') or "
            "a reference to a value in the data model ('path', e.g. '/filter/open')."
        ),
    )


# TextField Component
class TextFieldComponent(BaseModel):
    """A text field component that allows text input.

    Attributes:
        label: The text label for the input field. Can be a literal string or
            a reference to a value in the data model (e.g., '/user/name').
        text: The value of the text field. Can be a literal string or a
            reference to a value in the data model (e.g., '/user/name').
        text_field_type: The type of input field to display.
        validation_regexp: A regular expression used for client-side validation
            of the input.
    """

    label: LiteralStringOrPath = Field(
        ...,
        description=(
            "The text label for the input field. This can be a literal string "
            "or a reference to a value in the data model ('path, e.g. '/user/name')."
        ),
    )
    text: LiteralStringOrPath | None = Field(
        None,
        description=(
            "The value of the text field. This can be a literal string or a "
            "reference to a value in the data model ('path', e.g. '/user/name')."
        ),
    )
    text_field_type: TextFieldType | None = Field(None, alias="textFieldType")
    validation_regexp: str | None = Field(None, alias="validationRegexp")

    model_config = ConfigDict(populate_by_name=True)


# DateTimeInput Component
class DateTimeInputComponent(BaseModel):
    """A date/time input component that allows date and/or time selection.

    Attributes:
        value: The selected date and/or time value in ISO 8601 format. Can be
            a literal string or a reference to a value in the data model
            (e.g., '/user/dob').
        enable_date: If true, allows the user to select a date.
        enable_time: If true, allows the user to select a time.
    """

    value: LiteralStringOrPath = Field(
        ...,
        description=(
            "The selected date and/or time value in ISO 8601 format. This can "
            "be a literal string ('literalString') or a reference to a value "
            "in the data model ('path', e.g. '/user/dob')."
        ),
    )
    enable_date: bool | None = Field(
        None, alias="enableDate", description="If true, allows the user to select a date."
    )
    enable_time: bool | None = Field(
        None, alias="enableTime", description="If true, allows the user to select a time."
    )

    model_config = ConfigDict(populate_by_name=True)


# MultipleChoice Component
class MultipleChoiceOption(BaseModel):
    """A single option in a MultipleChoice component.

    Attributes:
        label: The text to display for this option. Can be a literal string or
            a reference to a value in the data model (e.g., '/option/label').
        value: The value to be associated with this option when selected.
    """

    label: LiteralStringOrPath = Field(
        ...,
        description=(
            "The text to display for this option. This can be a literal string "
            "or a reference to a value in the data model (e.g. '/option/label')."
        ),
    )
    value: str = Field(
        ..., description="The value to be associated with this option when selected."
    )


class MultipleChoiceComponent(BaseModel):
    """A multiple choice component that allows selecting from multiple options.

    Attributes:
        selections: The currently selected values for the component. Can be a
            literal array of strings or a path to an array in the data model
            (e.g., '/hotel/options').
        options: An array of available options for the user to choose from.
        max_allowed_selections: The maximum number of options that the user is
            allowed to select.
    """

    selections: LiteralArrayOrPath = Field(
        ...,
        description=(
            "The currently selected values for the component. This can be a "
            "literal array of strings or a path to an array in the data model "
            "('path', e.g. '/hotel/options')."
        ),
    )
    options: list[MultipleChoiceOption] = Field(
        ..., description="An array of available options for the user to choose from."
    )
    max_allowed_selections: int | None = Field(
        None,
        alias="maxAllowedSelections",
        description="The maximum number of options that the user is allowed to select.",
    )

    model_config = ConfigDict(populate_by_name=True)


# Slider Component
class SliderComponent(BaseModel):
    """A slider component that allows selecting a numeric value.

    Attributes:
        value: The current value of the slider. Can be a literal number or a
            reference to a value in the data model (e.g., '/restaurant/cost').
        min_value: The minimum value of the slider.
        max_value: The maximum value of the slider.
    """

    value: LiteralNumberOrPath = Field(
        ...,
        description=(
            "The current value of the slider. This can be a literal number "
            "('literalNumber') or a reference to a value in the data model "
            "('path', e.g. '/restaurant/cost')."
        ),
    )
    min_value: float | None = Field(None, alias="minValue")
    max_value: float | None = Field(None, alias="maxValue")

    model_config = ConfigDict(populate_by_name=True)


# Union type for all components
Component = (
    TextComponent
    | ImageComponent
    | IconComponent
    | VideoComponent
    | AudioPlayerComponent
    | RowComponent
    | ColumnComponent
    | ListComponent
    | CardComponent
    | TabsComponent
    | DividerComponent
    | ModalComponent
    | ButtonComponent
    | CheckBoxComponent
    | TextFieldComponent
    | DateTimeInputComponent
    | MultipleChoiceComponent
    | SliderComponent
)
