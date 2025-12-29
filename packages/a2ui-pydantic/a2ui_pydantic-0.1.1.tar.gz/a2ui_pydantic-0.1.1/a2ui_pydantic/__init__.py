"""A2UI Pydantic Schema.

This package provides Pydantic models for the A2UI (Agent to UI) protocol.
The A2UI protocol enables AI agents to generate rich, interactive user interfaces
that render natively across web, mobile, and desktop.

For more information, see https://a2ui.org/
"""

# Base models
from a2ui_pydantic.base import (
    ActionContextValue,
    IconNameLiteralOrPath,
    LiteralArrayOrPath,
    LiteralBooleanOrPath,
    LiteralNumberOrPath,
    LiteralStringOrPath,
)

# Enums
from a2ui_pydantic.enums import (
    Alignment,
    DividerAxis,
    Distribution,
    IconName,
    ImageFit,
    ImageUsageHint,
    ListDirection,
    TextFieldType,
    TextUsageHint,
)

# Actions
from a2ui_pydantic.actions import Action, ActionContextItem

# Components
from a2ui_pydantic.components import (
    AudioPlayerComponent,
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    Children,
    ChildrenTemplate,
    ColumnComponent,
    Component,
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

# Data model
from a2ui_pydantic.data_model import DataModelEntry, DataModelMapEntry

# Messages
from a2ui_pydantic.messages import (
    A2UIMessage,
    BeginRendering,
    ComponentWrapper,
    DeleteSurface,
    DataModelUpdate,
    Styles,
    SurfaceComponent,
    SurfaceUpdate,
)

__all__ = [
    # Base models
    "LiteralStringOrPath",
    "LiteralNumberOrPath",
    "LiteralBooleanOrPath",
    "LiteralArrayOrPath",
    "IconNameLiteralOrPath",
    "ActionContextValue",
    # Enums
    "TextUsageHint",
    "ImageFit",
    "ImageUsageHint",
    "IconName",
    "Distribution",
    "Alignment",
    "ListDirection",
    "DividerAxis",
    "TextFieldType",
    # Actions
    "Action",
    "ActionContextItem",
    # Components
    "TextComponent",
    "ImageComponent",
    "IconComponent",
    "VideoComponent",
    "AudioPlayerComponent",
    "RowComponent",
    "ColumnComponent",
    "ListComponent",
    "CardComponent",
    "TabsComponent",
    "TabItem",
    "DividerComponent",
    "ModalComponent",
    "ButtonComponent",
    "CheckBoxComponent",
    "TextFieldComponent",
    "DateTimeInputComponent",
    "MultipleChoiceComponent",
    "MultipleChoiceOption",
    "SliderComponent",
    "Children",
    "ChildrenTemplate",
    "Component",
    # Data model
    "DataModelEntry",
    "DataModelMapEntry",
    # Messages
    "A2UIMessage",
    "BeginRendering",
    "SurfaceUpdate",
    "SurfaceComponent",
    "ComponentWrapper",
    "DataModelUpdate",
    "DeleteSurface",
    "Styles",
]

__version__ = "0.1.1"
