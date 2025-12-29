"""Enumeration types for A2UI schema.

This module contains all enum types used in the A2UI specification.
"""

from enum import Enum


class TextUsageHint(str, Enum):
    """Hint for the base text style."""

    H1 = "h1"  # Largest heading
    H2 = "h2"  # Second largest heading
    H3 = "h3"  # Third largest heading
    H4 = "h4"  # Fourth largest heading
    H5 = "h5"  # Fifth largest heading
    CAPTION = "caption"  # Small text for captions
    BODY = "body"  # Standard body text


class ImageFit(str, Enum):
    """Specifies how the image should be resized to fit its container.

    Corresponds to the CSS 'object-fit' property.
    """

    CONTAIN = "contain"
    COVER = "cover"
    FILL = "fill"
    NONE = "none"
    SCALE_DOWN = "scale-down"


class ImageUsageHint(str, Enum):
    """Hint for the image size and style."""

    ICON = "icon"  # Small square icon
    AVATAR = "avatar"  # Circular avatar image
    SMALL_FEATURE = "smallFeature"  # Small feature image
    MEDIUM_FEATURE = "mediumFeature"  # Medium feature image
    LARGE_FEATURE = "largeFeature"  # Large feature image
    HEADER = "header"  # Full-width, full bleed, header image


class IconName(str, Enum):
    """Available icon names."""

    ACCOUNT_CIRCLE = "accountCircle"
    ADD = "add"
    ARROW_BACK = "arrowBack"
    ARROW_FORWARD = "arrowForward"
    ATTACH_FILE = "attachFile"
    CALENDAR_TODAY = "calendarToday"
    CALL = "call"
    CAMERA = "camera"
    CHECK = "check"
    CLOSE = "close"
    DELETE = "delete"
    DOWNLOAD = "download"
    EDIT = "edit"
    EVENT = "event"
    ERROR = "error"
    FAVORITE = "favorite"
    FAVORITE_OFF = "favoriteOff"
    FOLDER = "folder"
    HELP = "help"
    HOME = "home"
    INFO = "info"
    LOCATION_ON = "locationOn"
    LOCK = "lock"
    LOCK_OPEN = "lockOpen"
    MAIL = "mail"
    MENU = "menu"
    MORE_VERT = "moreVert"
    MORE_HORIZ = "moreHoriz"
    NOTIFICATIONS_OFF = "notificationsOff"
    NOTIFICATIONS = "notifications"
    PAYMENT = "payment"
    PERSON = "person"
    PHONE = "phone"
    PHOTO = "photo"
    PRINT = "print"
    REFRESH = "refresh"
    SEARCH = "search"
    SEND = "send"
    SETTINGS = "settings"
    SHARE = "share"
    SHOPPING_CART = "shoppingCart"
    STAR = "star"
    STAR_HALF = "starHalf"
    STAR_OFF = "starOff"
    UPLOAD = "upload"
    VISIBILITY = "visibility"
    VISIBILITY_OFF = "visibilityOff"
    WARNING = "warning"


class Distribution(str, Enum):
    """Defines the arrangement of children along the main axis.

    Corresponds to the CSS 'justify-content' property.
    """

    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_AROUND = "spaceAround"
    SPACE_BETWEEN = "spaceBetween"
    SPACE_EVENLY = "spaceEvenly"


class Alignment(str, Enum):
    """Defines the alignment of children along the cross axis.

    Corresponds to the CSS 'align-items' property.
    """

    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class ListDirection(str, Enum):
    """The direction in which list items are laid out."""

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class DividerAxis(str, Enum):
    """The orientation of the divider."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class TextFieldType(str, Enum):
    """The type of input field to display."""

    DATE = "date"
    LONG_TEXT = "longText"
    NUMBER = "number"
    SHORT_TEXT = "shortText"
    OBSCURED = "obscured"
