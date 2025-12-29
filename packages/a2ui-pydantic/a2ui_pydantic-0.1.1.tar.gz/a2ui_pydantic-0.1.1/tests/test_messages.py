"""Unit tests for messages in a2ui_pydantic.messages."""

import pytest
from pydantic import ValidationError

from a2ui_pydantic.actions import Action
from a2ui_pydantic.components import (
    AudioPlayerComponent,
    ButtonComponent,
    CardComponent,
    CheckBoxComponent,
    Children,
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
from a2ui_pydantic.data_model import DataModelEntry
from a2ui_pydantic.enums import IconName
from a2ui_pydantic.messages import (
    A2UIMessage,
    BeginRendering,
    ComponentWrapper,
    DataModelUpdate,
    DeleteSurface,
    Styles,
    SurfaceComponent,
    SurfaceUpdate,
)


def test_begin_rendering():
    """Test BeginRendering validation."""
    br = BeginRendering(surfaceId="s1", root="r1")
    assert br.surface_id == "s1"
    assert br.root == "r1"
    assert br.styles is None

    # With styles
    styles = Styles(font="Arial", primaryColor="#00BFFF")
    br2 = BeginRendering(surfaceId="s1", root="r1", styles=styles)
    assert br2.styles == styles
    assert br2.styles.font == "Arial"  # pylint: disable=no-member
    assert br2.styles.primary_color == "#00BFFF"  # pylint: disable=no-member


def test_surface_update():
    """Test SurfaceUpdate validation."""
    text_comp = TextComponent(text={"literalString": "Hi"})
    wrapper = ComponentWrapper(Text=text_comp)
    sc = SurfaceComponent(id="c1", component=wrapper)

    su = SurfaceUpdate(surfaceId="s1", components=[sc])
    assert su.surface_id == "s1"
    assert len(su.components) == 1

    # Invalid: empty components list
    with pytest.raises(ValidationError):
        SurfaceUpdate(surfaceId="s1", components=[])


def test_data_model_update():
    """Test DataModelUpdate validation."""
    dmu = DataModelUpdate(surfaceId="s1", contents=[])
    assert dmu.surface_id == "s1"
    assert dmu.path is None

    # With path
    entry = DataModelEntry(key="test", valueString="value")
    dmu2 = DataModelUpdate(surfaceId="s1", contents=[entry], path="/data")
    assert dmu2.path == "/data"
    assert len(dmu2.contents) == 1


def test_delete_surface():
    """Test DeleteSurface validation."""
    ds = DeleteSurface(surfaceId="s1")
    assert ds.surface_id == "s1"


def test_a2ui_message():
    """Test A2UIMessage validation."""
    br = BeginRendering(surfaceId="s1", root="r1")

    # Valid
    msg = A2UIMessage(beginRendering=br)
    assert msg.begin_rendering == br

    # Invalid
    with pytest.raises(ValidationError):
        A2UIMessage()  # None

    ds = DeleteSurface(surfaceId="s1")
    with pytest.raises(ValidationError):
        A2UIMessage(beginRendering=br, deleteSurface=ds)  # Multiple


def test_component_wrapper():
    """Test ComponentWrapper validation."""
    # Valid
    text_comp = TextComponent(text={"literalString": "Hi"})
    w = ComponentWrapper(Text=text_comp)
    assert w.Text == text_comp

    # Invalid
    with pytest.raises(ValidationError):
        ComponentWrapper()  # None

    img_comp = ImageComponent(url={"literalString": "u"})
    with pytest.raises(ValidationError):
        ComponentWrapper(Text=text_comp, Image=img_comp)  # Multiple


def test_styles():
    """Test Styles validation."""
    # Valid
    styles = Styles(font="Arial", primaryColor="#00BFFF")
    assert styles.font == "Arial"
    assert styles.primary_color == "#00BFFF"

    # Valid with just font
    styles2 = Styles(font="Helvetica")
    assert styles2.font == "Helvetica"
    assert styles2.primary_color is None

    # Valid with just primaryColor
    styles3 = Styles(primaryColor="#FF0000")
    assert styles3.primary_color == "#FF0000"
    assert styles3.font is None

    # Valid - empty
    styles4 = Styles()
    assert styles4.font is None
    assert styles4.primary_color is None

    # Invalid - wrong color format
    with pytest.raises(ValidationError):
        Styles(primaryColor="red")  # Not hex format

    with pytest.raises(ValidationError):
        Styles(primaryColor="#FF")  # Too short

    with pytest.raises(ValidationError):
        Styles(primaryColor="#GGGGGG")  # Invalid hex

    # Valid - correct hex format
    Styles(primaryColor="#ABCDEF")
    Styles(primaryColor="#123456")
    Styles(primaryColor="#000000")
    Styles(primaryColor="#FFFFFF")


def test_surface_component():
    """Test SurfaceComponent validation."""
    text_comp = TextComponent(text={"literalString": "Hi"})
    wrapper = ComponentWrapper(Text=text_comp)
    sc = SurfaceComponent(id="c1", component=wrapper)
    assert sc.id == "c1"
    assert sc.component == wrapper
    assert sc.weight is None

    # With weight
    sc2 = SurfaceComponent(id="c2", component=wrapper, weight=2.0)
    assert sc2.weight == 2.0


def test_component_wrapper_all_types():
    """Test ComponentWrapper with all component types."""
    children = Children(explicitList=["c1"])

    # Text
    assert ComponentWrapper(Text=TextComponent(text={"literalString": "Hello"})).Text

    # Image
    assert ComponentWrapper(Image=ImageComponent(url={"literalString": "http://img.com"})).Image

    # Icon
    icon_comp = IconComponent(name={"literalString": IconName.ADD})
    assert ComponentWrapper(Icon=icon_comp).Icon == icon_comp

    # Video
    assert ComponentWrapper(Video=VideoComponent(url={"literalString": "http://video.com"})).Video

    # AudioPlayer
    assert ComponentWrapper(
        AudioPlayer=AudioPlayerComponent(url={"literalString": "http://audio.com"})
    ).AudioPlayer

    # Row
    assert ComponentWrapper(Row=RowComponent(children=children)).Row

    # Column
    assert ComponentWrapper(Column=ColumnComponent(children=children)).Column

    # List
    assert ComponentWrapper(List=ListComponent(children=children)).List

    # Card
    assert ComponentWrapper(Card=CardComponent(child="c1")).Card

    # Tabs
    tabs_comp = TabsComponent(
        tabItems=[TabItem(title={"literalString": "Tab"}, child="c1")]
    )
    assert ComponentWrapper(Tabs=tabs_comp).Tabs == tabs_comp

    # Divider
    assert ComponentWrapper(Divider=DividerComponent()).Divider

    # Modal
    assert ComponentWrapper(
        Modal=ModalComponent(entryPointChild="b1", contentChild="c1")
    ).Modal

    # Button
    button_comp = ButtonComponent(child="c1", action=Action(name="click"))
    assert ComponentWrapper(Button=button_comp).Button == button_comp

    # CheckBox
    assert ComponentWrapper(
        CheckBox=CheckBoxComponent(
            label={"literalString": "Label"}, value={"literalBoolean": True}
        )
    ).CheckBox

    # TextField
    assert ComponentWrapper(
        TextField=TextFieldComponent(label={"literalString": "Label"})
    ).TextField

    # DateTimeInput
    assert ComponentWrapper(
        DateTimeInput=DateTimeInputComponent(value={"literalString": "2024-01-01"})
    ).DateTimeInput

    # MultipleChoice
    mc_comp = MultipleChoiceComponent(
        selections={"literalArray": []},
        options=[MultipleChoiceOption(label={"literalString": "Opt"}, value="opt1")],
    )
    assert ComponentWrapper(MultipleChoice=mc_comp).MultipleChoice == mc_comp

    # Slider
    assert ComponentWrapper(Slider=SliderComponent(value={"literalNumber": 50.0})).Slider
