"""Message models for A2UI schema.

This module contains the main message types that can be sent in A2UI protocol.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from a2ui_pydantic.components import (
    AudioPlayerComponent,
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    ColumnComponent,
    DateTimeInputComponent,
    DividerComponent,
    IconComponent,
    ImageComponent,
    ListComponent,
    ModalComponent,
    MultipleChoiceComponent,
    RowComponent,
    SliderComponent,
    TabsComponent,
    TextComponent,
    TextFieldComponent,
    VideoComponent,
)
from a2ui_pydantic.data_model import DataModelEntry
from a2ui_pydantic.raw_schema import A2UI_SCHEMA as RAW_SCHEMA


class Styles(BaseModel):
    """Styling information for the UI.

    Attributes:
        font: The primary font for the UI.
        primary_color: The primary UI color as a hexadecimal code (e.g., '#00BFFF').
    """

    font: str | None = Field(None, description="The primary font for the UI.")
    primary_color: str | None = Field(
        None,
        alias="primaryColor",
        description="The primary UI color as a hexadecimal code (e.g., '#00BFFF').",
        pattern="^#[0-9a-fA-F]{6}$",
    )

    model_config = ConfigDict(populate_by_name=True)


class BeginRendering(BaseModel):
    """Signals the client to begin rendering a surface with a root component and specific styles.

    Attributes:
        surface_id: The unique identifier for the UI surface to be rendered.
        root: The ID of the root component to render.
        styles: Optional styling information for the UI.
    """

    surface_id: str = Field(
        ...,
        alias="surfaceId",
        description="The unique identifier for the UI surface to be rendered.",
    )
    root: str = Field(..., description="The ID of the root component to render.")
    styles: Styles | None = Field(
        None, description="Styling information for the UI."
    )

    model_config = ConfigDict(populate_by_name=True)


class ComponentWrapper(BaseModel):
    """A wrapper object that contains exactly one component type.

    This wrapper MUST contain exactly one key, which is the name of the
    component type (e.g., 'Text'). The value is an object containing the
    properties for that specific component.

    Attributes:
        Text: A Text component.
        Image: An Image component.
        Icon: An Icon component.
        Video: A Video component.
        AudioPlayer: An AudioPlayer component.
        Row: A Row component.
        Column: A Column component.
        List: A List component.
        Card: A Card component.
        Tabs: A Tabs component.
        Divider: A Divider component.
        Modal: A Modal component.
        Button: A Button component.
        CheckBox: A CheckBox component.
        TextField: A TextField component.
        DateTimeInput: A DateTimeInput component.
        MultipleChoice: A MultipleChoice component.
        Slider: A Slider component.
    """

    Text: TextComponent | None = None
    Image: ImageComponent | None = None
    Icon: IconComponent | None = None
    Video: VideoComponent | None = None
    AudioPlayer: AudioPlayerComponent | None = None
    Row: RowComponent | None = None
    Column: ColumnComponent | None = None
    List: ListComponent | None = None
    Card: CardComponent | None = None
    Tabs: TabsComponent | None = None
    Divider: DividerComponent | None = None
    Modal: ModalComponent | None = None
    Button: ButtonComponent | None = None
    CheckBox: CheckBoxComponent | None = None
    TextField: TextFieldComponent | None = None
    DateTimeInput: DateTimeInputComponent | None = None
    MultipleChoice: MultipleChoiceComponent | None = None
    Slider: SliderComponent | None = None

    @model_validator(mode="after")
    def validate_exactly_one_component(self):
        """Validate that exactly one component type is provided."""
        component_fields = [
            "Text",
            "Image",
            "Icon",
            "Video",
            "AudioPlayer",
            "Row",
            "Column",
            "List",
            "Card",
            "Tabs",
            "Divider",
            "Modal",
            "Button",
            "CheckBox",
            "TextField",
            "DateTimeInput",
            "MultipleChoice",
            "Slider",
        ]
        non_none_count = sum(
            1 for field in component_fields if getattr(self, field) is not None
        )
        if non_none_count != 1:
            raise ValueError(
                "ComponentWrapper must contain exactly one component type"
            )
        return self


class SurfaceComponent(BaseModel):
    """Represents a single component in a UI widget tree.

    Attributes:
        id: The unique identifier for this component.
        weight: The relative weight of this component within a Row or Column.
            This corresponds to the CSS 'flex-grow' property. Note: this may
            ONLY be set when the component is a direct descendant of a Row or Column.
        component: A wrapper object that MUST contain exactly one key, which is
            the name of the component type (e.g., 'Heading'). The value is an
            object containing the properties for that specific component.
    """

    id: str = Field(..., description="The unique identifier for this component.")
    weight: float | None = Field(
        None,
        description=(
            "The relative weight of this component within a Row or Column. "
            "This corresponds to the CSS 'flex-grow' property. Note: this may "
            "ONLY be set when the component is a direct descendant of a Row or Column."
        ),
    )
    component: ComponentWrapper = Field(
        ...,
        description=(
            "A wrapper object that MUST contain exactly one key, which is the "
            "name of the component type (e.g., 'Heading'). The value is an "
            "object containing the properties for that specific component."
        ),
    )


class SurfaceUpdate(BaseModel):
    """Updates a surface with a new set of components.

    Attributes:
        surface_id: The unique identifier for the UI surface to be updated.
            If you are adding a new surface this *must* be a new, unique
            identifier that has never been used for any existing surfaces shown.
        components: A list containing all UI components for the surface.
    """

    surface_id: str = Field(
        ...,
        alias="surfaceId",
        description=(
            "The unique identifier for the UI surface to be updated. If you "
            "are adding a new surface this *must* be a new, unique identified "
            "that has never been used for any existing surfaces shown."
        ),
    )
    components: list[SurfaceComponent] = Field(
        ...,
        min_length=1,
        description="A list containing all UI components for the surface.",
    )

    model_config = ConfigDict(populate_by_name=True)


class DataModelUpdate(BaseModel):
    """Updates the data model for a surface.

    Attributes:
        surface_id: The unique identifier for the UI surface this data model
            update applies to.
        path: An optional path to a location within the data model
            (e.g., '/user/name'). If omitted, or set to '/', the entire data
            model will be replaced.
        contents: An array of data entries. Each entry must contain a 'key'
            and exactly one corresponding typed 'value*' property.
    """

    surface_id: str = Field(
        ...,
        alias="surfaceId",
        description="The unique identifier for the UI surface this data model update applies to.",
    )
    path: str | None = Field(
        None,
        description=(
            "An optional path to a location within the data model "
            "(e.g., '/user/name'). If omitted, or set to '/', the entire data "
            "model will be replaced."
        ),
    )
    contents: list[DataModelEntry] = Field(
        ...,
        description=(
            "An array of data entries. Each entry must contain a 'key' and "
            "exactly one corresponding typed 'value*' property."
        ),
    )

    model_config = ConfigDict(populate_by_name=True)


class DeleteSurface(BaseModel):
    """Signals the client to delete the surface identified by 'surfaceId'.

    Attributes:
        surface_id: The unique identifier for the UI surface to be deleted.
    """

    surface_id: str = Field(
        ...,
        alias="surfaceId",
        description="The unique identifier for the UI surface to be deleted.",
    )

    model_config = ConfigDict(populate_by_name=True)


class A2UIMessage(BaseModel):
    """Describes a JSON payload for an A2UI (Agent to UI) message.

    A message MUST contain exactly ONE of the action properties:
    'beginRendering', 'surfaceUpdate', 'dataModelUpdate', or 'deleteSurface'.

    Attributes:
        begin_rendering: Signals the client to begin rendering a surface.
        surface_update: Updates a surface with a new set of components.
        data_model_update: Updates the data model for a surface.
        delete_surface: Signals the client to delete a surface.
    """

    begin_rendering: BeginRendering | None = Field(None, alias="beginRendering")
    surface_update: SurfaceUpdate | None = Field(None, alias="surfaceUpdate")
    data_model_update: DataModelUpdate | None = Field(None, alias="dataModelUpdate")
    delete_surface: DeleteSurface | None = Field(None, alias="deleteSurface")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_exactly_one_action(self):
        """Validate that exactly one action property is provided."""
        action_fields = [
            "begin_rendering",
            "surface_update",
            "data_model_update",
            "delete_surface",
        ]
        non_none_count = sum(
            1 for field in action_fields if getattr(self, field) is not None
        )
        if non_none_count != 1:
            raise ValueError(
                "A2UIMessage must contain exactly one action property: "
                "'beginRendering', 'surfaceUpdate', 'dataModelUpdate', or 'deleteSurface'"
            )
        return self

    @staticmethod
    def raw_schema() -> str:
        """Return the raw schema for the A2UI protocol."""
        return RAW_SCHEMA
