"""
A2UI (Agent-to-User Interface) Protocol Implementation.

This module implements the A2UI v0.8 specification for generating declarative,
streaming UI payloads that can be rendered by A2UI-compatible clients.

A2UI is designed to be:
- LLM-friendly: Flat adjacency list model, easy for LLMs to generate incrementally
- Secure: Declarative data format, not executable code
- Framework-agnostic: Same payload renders on web, Flutter, etc.

Protocol Flow:
1. Server generates JSONL messages: surfaceUpdate, dataModelUpdate, beginRendering
2. Client buffers components by ID, builds tree from adjacency references
3. User interactions send userAction events back to server

See: https://github.com/google/A2UI
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Literal, Tuple
from enum import Enum


# =============================================================================
# CONSTANTS
# =============================================================================

A2UI_VERSION = "0.8"
A2UI_MIME_TYPE = "application/json+a2ui"
STANDARD_CATALOG_ID = "https://raw.githubusercontent.com/google/A2UI/refs/heads/main/specification/0.8/json/standard_catalog_definition.json"


# =============================================================================
# BOUND VALUE TYPES
# =============================================================================

@dataclass
class BoundString:
    """A string value that can be literal or bound to data model path."""
    literal_string: Optional[str] = None
    path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.literal_string is not None:
            result["literalString"] = self.literal_string
        if self.path is not None:
            result["path"] = self.path
        return result

    @classmethod
    def literal(cls, value: str) -> "BoundString":
        return cls(literal_string=value)

    @classmethod
    def bound(cls, path: str) -> "BoundString":
        return cls(path=path)

    @classmethod
    def from_value(cls, value: Union[str, "BoundString"]) -> "BoundString":
        if isinstance(value, BoundString):
            return value
        return cls.literal(value)


@dataclass
class BoundNumber:
    """A number value that can be literal or bound to data model path."""
    literal_number: Optional[float] = None
    path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.literal_number is not None:
            result["literalNumber"] = self.literal_number
        if self.path is not None:
            result["path"] = self.path
        return result

    @classmethod
    def literal(cls, value: float) -> "BoundNumber":
        return cls(literal_number=value)

    @classmethod
    def bound(cls, path: str) -> "BoundNumber":
        return cls(path=path)


@dataclass
class BoundBoolean:
    """A boolean value that can be literal or bound to data model path."""
    literal_boolean: Optional[bool] = None
    path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.literal_boolean is not None:
            result["literalBoolean"] = self.literal_boolean
        if self.path is not None:
            result["path"] = self.path
        return result

    @classmethod
    def literal(cls, value: bool) -> "BoundBoolean":
        return cls(literal_boolean=value)

    @classmethod
    def bound(cls, path: str) -> "BoundBoolean":
        return cls(path=path)


@dataclass
class BoundArray:
    """An array value that can be literal or bound to data model path."""
    literal_array: Optional[List[str]] = None
    path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.literal_array is not None:
            result["literalArray"] = self.literal_array
        if self.path is not None:
            result["path"] = self.path
        return result


BoundValue = Union[BoundString, BoundNumber, BoundBoolean, BoundArray]


# =============================================================================
# CHILDREN TYPES
# =============================================================================

@dataclass
class ExplicitChildren:
    """Fixed list of child component IDs."""
    ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"explicitList": self.ids}


@dataclass
class TemplateChildren:
    """Dynamic children generated from data model list."""
    component_id: str
    data_binding: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template": {
                "componentId": self.component_id,
                "dataBinding": self.data_binding
            }
        }


Children = Union[ExplicitChildren, TemplateChildren, List[str]]


def _normalize_children(children: Children) -> Dict[str, Any]:
    """Convert children to dict format."""
    if isinstance(children, (ExplicitChildren, TemplateChildren)):
        return children.to_dict()
    elif isinstance(children, list):
        return {"explicitList": children}
    return children


# =============================================================================
# ACTION TYPES
# =============================================================================

@dataclass
class ActionContext:
    """Key-value pair for action context."""
    key: str
    value: BoundValue

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value.to_dict() if hasattr(self.value, 'to_dict') else self.value
        }


@dataclass
class Action:
    """Client-side action dispatched on interaction."""
    name: str
    context: Optional[List[ActionContext]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.context:
            result["context"] = [c.to_dict() for c in self.context]
        return result


# =============================================================================
# COMPONENT DEFINITIONS
# =============================================================================

class TextUsageHint(str, Enum):
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    CAPTION = "caption"
    BODY = "body"


class ImageUsageHint(str, Enum):
    ICON = "icon"
    AVATAR = "avatar"
    SMALL_FEATURE = "smallFeature"
    MEDIUM_FEATURE = "mediumFeature"
    LARGE_FEATURE = "largeFeature"
    HEADER = "header"


class ImageFit(str, Enum):
    CONTAIN = "contain"
    COVER = "cover"
    FILL = "fill"
    NONE = "none"
    SCALE_DOWN = "scale-down"


class Alignment(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class Distribution(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "spaceBetween"
    SPACE_AROUND = "spaceAround"
    SPACE_EVENLY = "spaceEvenly"


class ListDirection(str, Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class TextFieldType(str, Enum):
    SHORT_TEXT = "shortText"
    LONG_TEXT = "longText"
    NUMBER = "number"
    DATE = "date"
    OBSCURED = "obscured"


class DividerAxis(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


# Icon names from standard catalog
class IconName(str, Enum):
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


@dataclass
class Component:
    """Base component with ID and optional weight."""
    id: str
    component_type: str
    properties: Dict[str, Any]
    weight: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "component": {
                self.component_type: self.properties
            }
        }
        if self.weight is not None:
            result["weight"] = self.weight
        return result


# =============================================================================
# COMPONENT FACTORY FUNCTIONS
# =============================================================================

def _gen_id(prefix: str = "comp") -> str:
    """Generate unique component ID."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def text(
    text: Union[str, BoundString],
    usage_hint: Optional[TextUsageHint] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Text component."""
    props = {
        "text": BoundString.from_value(text).to_dict()
    }
    if usage_hint:
        props["usageHint"] = usage_hint.value if isinstance(usage_hint, TextUsageHint) else usage_hint
    return Component(
        id=id or _gen_id("text"),
        component_type="Text",
        properties=props,
        weight=weight
    )


def image(
    url: Union[str, BoundString],
    fit: Optional[ImageFit] = None,
    usage_hint: Optional[ImageUsageHint] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create an Image component."""
    props = {
        "url": BoundString.from_value(url).to_dict()
    }
    if fit:
        props["fit"] = fit.value if isinstance(fit, ImageFit) else fit
    if usage_hint:
        props["usageHint"] = usage_hint.value if isinstance(usage_hint, ImageUsageHint) else usage_hint
    return Component(
        id=id or _gen_id("img"),
        component_type="Image",
        properties=props,
        weight=weight
    )


def icon(
    name: Union[str, IconName, BoundString],
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create an Icon component."""
    if isinstance(name, IconName):
        name_value = BoundString.literal(name.value)
    elif isinstance(name, str):
        name_value = BoundString.literal(name)
    else:
        name_value = name
    props = {"name": name_value.to_dict()}
    return Component(
        id=id or _gen_id("icon"),
        component_type="Icon",
        properties=props,
        weight=weight
    )


def row(
    children: Children,
    distribution: Optional[Distribution] = None,
    alignment: Optional[Alignment] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Row (horizontal layout) component."""
    props = {"children": _normalize_children(children)}
    if distribution:
        props["distribution"] = distribution.value if isinstance(distribution, Distribution) else distribution
    if alignment:
        props["alignment"] = alignment.value if isinstance(alignment, Alignment) else alignment
    return Component(
        id=id or _gen_id("row"),
        component_type="Row",
        properties=props,
        weight=weight
    )


def column(
    children: Children,
    distribution: Optional[Distribution] = None,
    alignment: Optional[Alignment] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Column (vertical layout) component."""
    props = {"children": _normalize_children(children)}
    if distribution:
        props["distribution"] = distribution.value if isinstance(distribution, Distribution) else distribution
    if alignment:
        props["alignment"] = alignment.value if isinstance(alignment, Alignment) else alignment
    return Component(
        id=id or _gen_id("col"),
        component_type="Column",
        properties=props,
        weight=weight
    )


def list_component(
    children: Children,
    direction: Optional[ListDirection] = None,
    alignment: Optional[Alignment] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a List component (scrollable)."""
    props = {"children": _normalize_children(children)}
    if direction:
        props["direction"] = direction.value if isinstance(direction, ListDirection) else direction
    if alignment:
        props["alignment"] = alignment.value if isinstance(alignment, Alignment) else alignment
    return Component(
        id=id or _gen_id("list"),
        component_type="List",
        properties=props,
        weight=weight
    )


def card(
    child: str,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Card container component."""
    return Component(
        id=id or _gen_id("card"),
        component_type="Card",
        properties={"child": child},
        weight=weight
    )


def divider(
    axis: Optional[DividerAxis] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Divider component."""
    props = {}
    if axis:
        props["axis"] = axis.value if isinstance(axis, DividerAxis) else axis
    return Component(
        id=id or _gen_id("div"),
        component_type="Divider",
        properties=props,
        weight=weight
    )


def button(
    child: str,
    action: Action,
    primary: bool = False,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Button component."""
    props = {
        "child": child,
        "action": action.to_dict()
    }
    if primary:
        props["primary"] = True
    return Component(
        id=id or _gen_id("btn"),
        component_type="Button",
        properties=props,
        weight=weight
    )


def text_field(
    label: Union[str, BoundString],
    text: Optional[Union[str, BoundString]] = None,
    field_type: Optional[TextFieldType] = None,
    validation_regexp: Optional[str] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a TextField input component."""
    props = {
        "label": BoundString.from_value(label).to_dict()
    }
    if text:
        props["text"] = BoundString.from_value(text).to_dict()
    if field_type:
        props["textFieldType"] = field_type.value if isinstance(field_type, TextFieldType) else field_type
    if validation_regexp:
        props["validationRegexp"] = validation_regexp
    return Component(
        id=id or _gen_id("field"),
        component_type="TextField",
        properties=props,
        weight=weight
    )


def datetime_input(
    value: Union[str, BoundString],
    enable_date: bool = True,
    enable_time: bool = False,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a DateTimeInput component."""
    props = {
        "value": BoundString.from_value(value).to_dict(),
        "enableDate": enable_date,
        "enableTime": enable_time
    }
    return Component(
        id=id or _gen_id("datetime"),
        component_type="DateTimeInput",
        properties=props,
        weight=weight
    )


def checkbox(
    label: Union[str, BoundString],
    value: Union[bool, BoundBoolean],
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a CheckBox component."""
    if isinstance(value, bool):
        value = BoundBoolean.literal(value)
    props = {
        "label": BoundString.from_value(label).to_dict(),
        "value": value.to_dict()
    }
    return Component(
        id=id or _gen_id("check"),
        component_type="CheckBox",
        properties=props,
        weight=weight
    )


def slider(
    value: Union[float, BoundNumber],
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Slider component."""
    if isinstance(value, (int, float)):
        value = BoundNumber.literal(float(value))
    props = {"value": value.to_dict()}
    if min_value is not None:
        props["minValue"] = min_value
    if max_value is not None:
        props["maxValue"] = max_value
    return Component(
        id=id or _gen_id("slider"),
        component_type="Slider",
        properties=props,
        weight=weight
    )


@dataclass
class MultipleChoiceOption:
    """An option for MultipleChoice component."""
    label: Union[str, BoundString]
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": BoundString.from_value(self.label).to_dict(),
            "value": self.value
        }


def multiple_choice(
    selections: Union[List[str], BoundArray],
    options: List[MultipleChoiceOption],
    max_selections: Optional[int] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a MultipleChoice component."""
    if isinstance(selections, list):
        sel_value = BoundArray(literal_array=selections)
    else:
        sel_value = selections
    props = {
        "selections": sel_value.to_dict(),
        "options": [o.to_dict() for o in options]
    }
    if max_selections is not None:
        props["maxAllowedSelections"] = max_selections
    return Component(
        id=id or _gen_id("choice"),
        component_type="MultipleChoice",
        properties=props,
        weight=weight
    )


@dataclass
class TabItem:
    """A tab item for Tabs component."""
    title: Union[str, BoundString]
    child: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": BoundString.from_value(self.title).to_dict(),
            "child": self.child
        }


def tabs(
    tab_items: List[TabItem],
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Tabs component."""
    return Component(
        id=id or _gen_id("tabs"),
        component_type="Tabs",
        properties={"tabItems": [t.to_dict() for t in tab_items]},
        weight=weight
    )


def modal(
    entry_point_child: str,
    content_child: str,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Modal component."""
    return Component(
        id=id or _gen_id("modal"),
        component_type="Modal",
        properties={
            "entryPointChild": entry_point_child,
            "contentChild": content_child
        },
        weight=weight
    )


def video(
    url: Union[str, BoundString],
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create a Video component."""
    return Component(
        id=id or _gen_id("video"),
        component_type="Video",
        properties={"url": BoundString.from_value(url).to_dict()},
        weight=weight
    )


def audio_player(
    url: Union[str, BoundString],
    description: Optional[Union[str, BoundString]] = None,
    id: Optional[str] = None,
    weight: Optional[float] = None
) -> Component:
    """Create an AudioPlayer component."""
    props = {"url": BoundString.from_value(url).to_dict()}
    if description:
        props["description"] = BoundString.from_value(description).to_dict()
    return Component(
        id=id or _gen_id("audio"),
        component_type="AudioPlayer",
        properties=props,
        weight=weight
    )


# =============================================================================
# DATA MODEL HELPERS
# =============================================================================

@dataclass
class DataEntry:
    """A single entry in the data model."""
    key: str
    value: Any
    value_type: Literal["string", "number", "boolean", "map"] = "string"

    def to_dict(self) -> Dict[str, Any]:
        result = {"key": self.key}
        if self.value_type == "string":
            result["valueString"] = str(self.value) if self.value is not None else ""
        elif self.value_type == "number":
            result["valueNumber"] = float(self.value) if self.value is not None else 0
        elif self.value_type == "boolean":
            result["valueBoolean"] = bool(self.value)
        elif self.value_type == "map":
            # value should be a list of DataEntry or dicts
            if isinstance(self.value, list):
                result["valueMap"] = [
                    e.to_dict() if isinstance(e, DataEntry) else e
                    for e in self.value
                ]
            else:
                result["valueMap"] = self.value
        return result


def data_string(key: str, value: str) -> DataEntry:
    """Create a string data entry."""
    return DataEntry(key=key, value=value, value_type="string")


def data_number(key: str, value: float) -> DataEntry:
    """Create a number data entry."""
    return DataEntry(key=key, value=value, value_type="number")


def data_boolean(key: str, value: bool) -> DataEntry:
    """Create a boolean data entry."""
    return DataEntry(key=key, value=value, value_type="boolean")


def data_map(key: str, entries: List[DataEntry]) -> DataEntry:
    """Create a nested map data entry."""
    return DataEntry(key=key, value=entries, value_type="map")


def dict_to_data_entries(data: Dict[str, Any], prefix: str = "") -> List[DataEntry]:
    """Convert a Python dict to A2UI data entries."""
    entries = []
    for key, value in data.items():
        if isinstance(value, dict):
            # Nested map
            entries.append(data_map(key, dict_to_data_entries(value)))
        elif isinstance(value, bool):
            entries.append(data_boolean(key, value))
        elif isinstance(value, (int, float)):
            entries.append(data_number(key, value))
        elif isinstance(value, list):
            # List of items - convert to indexed map
            list_entries = []
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    list_entries.append(data_map(str(i), dict_to_data_entries(item)))
                else:
                    list_entries.append(data_string(str(i), str(item)))
            entries.append(data_map(key, list_entries))
        else:
            entries.append(data_string(key, str(value) if value is not None else ""))
    return entries


# =============================================================================
# MESSAGE TYPES
# =============================================================================

@dataclass
class Styles:
    """UI styling configuration."""
    primary_color: Optional[str] = None
    font: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.primary_color:
            result["primaryColor"] = self.primary_color
        if self.font:
            result["font"] = self.font
        return result


@dataclass
class BeginRenderingMessage:
    """Signal to start rendering a surface."""
    surface_id: str
    root: str
    styles: Optional[Styles] = None
    catalog_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "beginRendering": {
                "surfaceId": self.surface_id,
                "root": self.root
            }
        }
        if self.styles:
            result["beginRendering"]["styles"] = self.styles.to_dict()
        if self.catalog_id:
            result["beginRendering"]["catalogId"] = self.catalog_id
        return result


@dataclass
class SurfaceUpdateMessage:
    """Update a surface with components."""
    surface_id: str
    components: List[Component]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "surfaceUpdate": {
                "surfaceId": self.surface_id,
                "components": [c.to_dict() for c in self.components]
            }
        }


@dataclass
class DataModelUpdateMessage:
    """Update the data model for a surface."""
    surface_id: str
    contents: List[DataEntry]
    path: str = "/"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataModelUpdate": {
                "surfaceId": self.surface_id,
                "path": self.path,
                "contents": [c.to_dict() for c in self.contents]
            }
        }


@dataclass
class DeleteSurfaceMessage:
    """Delete a surface."""
    surface_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deleteSurface": {
                "surfaceId": self.surface_id
            }
        }


A2UIMessage = Union[BeginRenderingMessage, SurfaceUpdateMessage, DataModelUpdateMessage, DeleteSurfaceMessage]


# =============================================================================
# CLIENT EVENT TYPES
# =============================================================================

@dataclass
class UserActionEvent:
    """User interaction event from client."""
    name: str
    surface_id: str
    source_component_id: str
    timestamp: str
    context: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserActionEvent":
        action = data.get("userAction", {})
        return cls(
            name=action.get("name", ""),
            surface_id=action.get("surfaceId", ""),
            source_component_id=action.get("sourceComponentId", ""),
            timestamp=action.get("timestamp", ""),
            context=action.get("context", {})
        )


@dataclass
class ClientErrorEvent:
    """Client-side error event."""
    message: str
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientErrorEvent":
        error = data.get("error", {})
        return cls(
            message=error.get("message", ""),
            details=error.get("details")
        )


# =============================================================================
# SURFACE BUILDER
# =============================================================================

class A2UISurface:
    """
    Builder for constructing an A2UI surface with components and data.

    Usage:
        surface = A2UISurface("dashboard")

        # Add components
        title = surface.add(text("Dashboard", usage_hint=TextUsageHint.H1))
        content = surface.add(column([title.id, ...]))

        # Set data
        surface.set_data({"title": "My Dashboard", "count": 42})

        # Generate messages
        messages = surface.build(root_id=content.id)
    """

    def __init__(
        self,
        surface_id: Optional[str] = None,
        primary_color: str = "#6366f1",
        font: str = "Inter"
    ):
        self.surface_id = surface_id or f"surface-{uuid.uuid4().hex[:8]}"
        self.styles = Styles(primary_color=primary_color, font=font)
        self.components: List[Component] = []
        self.data_entries: List[DataEntry] = []
        self._component_map: Dict[str, Component] = {}

    def add(self, component: Component) -> Component:
        """Add a component to the surface."""
        self.components.append(component)
        self._component_map[component.id] = component
        return component

    def add_all(self, components: List[Component]) -> List[Component]:
        """Add multiple components to the surface."""
        for c in components:
            self.add(c)
        return components

    def set_data(self, data: Dict[str, Any]) -> None:
        """Set the data model from a Python dict."""
        self.data_entries = dict_to_data_entries(data)

    def add_data_entry(self, entry: DataEntry) -> None:
        """Add a single data entry."""
        self.data_entries.append(entry)

    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by ID."""
        return self._component_map.get(component_id)

    def build(
        self,
        root_id: Optional[str] = None,
        catalog_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Build the complete list of A2UI messages.

        Returns messages in order:
        1. beginRendering
        2. surfaceUpdate with all components
        3. dataModelUpdate with data
        """
        if not root_id and self.components:
            root_id = self.components[-1].id

        if not root_id:
            raise ValueError("No root component ID specified and no components added")

        messages = []

        # Begin rendering
        messages.append(BeginRenderingMessage(
            surface_id=self.surface_id,
            root=root_id,
            styles=self.styles,
            catalog_id=catalog_id
        ).to_dict())

        # Surface update with all components
        if self.components:
            messages.append(SurfaceUpdateMessage(
                surface_id=self.surface_id,
                components=self.components
            ).to_dict())

        # Data model update
        if self.data_entries:
            messages.append(DataModelUpdateMessage(
                surface_id=self.surface_id,
                contents=self.data_entries,
                path="/"
            ).to_dict())

        return messages

    def to_jsonl(self, root_id: Optional[str] = None) -> str:
        """Generate JSONL string from messages."""
        messages = self.build(root_id)
        return "\n".join(json.dumps(m) for m in messages)

    def to_json_array(self, root_id: Optional[str] = None) -> str:
        """Generate JSON array string from messages."""
        messages = self.build(root_id)
        return json.dumps(messages, indent=2)


# =============================================================================
# DASHBOARD UI TEMPLATES
# =============================================================================

def create_metric_card(
    title: str,
    value_path: str,
    icon_name: Optional[str] = None,
    surface: Optional[A2UISurface] = None
) -> Tuple[Component, List[Component]]:
    """
    Create a metric card component.

    Returns:
        Tuple of (card_component, all_components_to_add)
    """
    s = surface or A2UISurface()

    components = []

    # Title text
    title_text = text(title, usage_hint=TextUsageHint.CAPTION, id=f"metric-title-{_gen_id()}")
    components.append(title_text)

    # Value text (bound to data model)
    value_text = text(BoundString.bound(value_path), usage_hint=TextUsageHint.H2, id=f"metric-value-{_gen_id()}")
    components.append(value_text)

    # Content column
    content_col = column([title_text.id, value_text.id], id=f"metric-content-{_gen_id()}")
    components.append(content_col)

    # Optional icon
    if icon_name:
        icon_comp = icon(icon_name, id=f"metric-icon-{_gen_id()}")
        components.append(icon_comp)
        row_comp = row([icon_comp.id, content_col.id], alignment=Alignment.CENTER, id=f"metric-row-{_gen_id()}")
        components.append(row_comp)
        card_content_id = row_comp.id
    else:
        card_content_id = content_col.id

    # Card wrapper
    card_comp = card(card_content_id, id=f"metric-card-{_gen_id()}")
    components.append(card_comp)

    return card_comp, components


def create_data_table(
    columns: List[str],
    data_path: str,
    row_template_id: str,
    surface: Optional[A2UISurface] = None
) -> Tuple[Component, List[Component]]:
    """
    Create a data table with templated rows.

    The data at data_path should be a map of rows, each row containing
    values for the specified columns.
    """
    s = surface or A2UISurface()
    components = []

    # Header row
    header_texts = []
    for col in columns:
        header_text = text(col, usage_hint=TextUsageHint.H5, id=f"header-{col}-{_gen_id()}")
        components.append(header_text)
        header_texts.append(header_text.id)

    header_row = row(header_texts, distribution=Distribution.SPACE_BETWEEN, id=f"table-header-{_gen_id()}")
    components.append(header_row)

    # List with template
    data_list = list_component(
        TemplateChildren(component_id=row_template_id, data_binding=data_path),
        direction=ListDirection.VERTICAL,
        id=f"table-list-{_gen_id()}"
    )
    components.append(data_list)

    # Container column
    table_col = column([header_row.id, data_list.id], id=f"table-{_gen_id()}")
    components.append(table_col)

    return table_col, components


def create_chart_placeholder(
    title: str,
    chart_type: str,
    data_path: str,
    surface: Optional[A2UISurface] = None
) -> Tuple[Component, List[Component]]:
    """
    Create a placeholder for a chart.

    Note: A2UI standard catalog doesn't include charts. This creates a
    card with title and a text indicating where chart would be rendered.
    For actual charts, you'd need a custom catalog with chart components.
    """
    components = []

    title_text = text(title, usage_hint=TextUsageHint.H3, id=f"chart-title-{_gen_id()}")
    components.append(title_text)

    placeholder = text(
        f"[{chart_type} chart - data bound to {data_path}]",
        usage_hint=TextUsageHint.CAPTION,
        id=f"chart-placeholder-{_gen_id()}"
    )
    components.append(placeholder)

    content_col = column([title_text.id, placeholder.id], id=f"chart-content-{_gen_id()}")
    components.append(content_col)

    chart_card = card(content_col.id, id=f"chart-card-{_gen_id()}")
    components.append(chart_card)

    return chart_card, components


def create_filter_form(
    filters: List[Dict[str, Any]],
    submit_action_name: str = "apply_filters",
    surface: Optional[A2UISurface] = None
) -> Tuple[Component, List[Component]]:
    """
    Create a filter form with various input types.

    filters: List of filter definitions, each with:
        - label: str
        - type: "text" | "number" | "date" | "select" | "checkbox"
        - path: str (data binding path)
        - options: List[dict] (for select type, with label/value)
    """
    components = []
    field_ids = []

    for f in filters:
        label = f["label"]
        path = f["path"]
        filter_type = f.get("type", "text")

        if filter_type == "text":
            field = text_field(label, BoundString.bound(path), id=f"filter-{_gen_id()}")
        elif filter_type == "number":
            field = text_field(label, BoundString.bound(path), field_type=TextFieldType.NUMBER, id=f"filter-{_gen_id()}")
        elif filter_type == "date":
            field = datetime_input(BoundString.bound(path), enable_date=True, id=f"filter-{_gen_id()}")
        elif filter_type == "checkbox":
            field = checkbox(label, BoundBoolean.bound(path), id=f"filter-{_gen_id()}")
        elif filter_type == "select":
            options = [
                MultipleChoiceOption(label=o["label"], value=o["value"])
                for o in f.get("options", [])
            ]
            field = multiple_choice(
                BoundArray(path=path),
                options,
                max_selections=1,
                id=f"filter-{_gen_id()}"
            )
        else:
            field = text_field(label, BoundString.bound(path), id=f"filter-{_gen_id()}")

        components.append(field)
        field_ids.append(field.id)

    # Submit button
    btn_text = text("Apply Filters", id=f"filter-btn-text-{_gen_id()}")
    components.append(btn_text)

    submit_btn = button(
        btn_text.id,
        Action(name=submit_action_name, context=[
            ActionContext(key="filters", value=BoundString.bound("/filters"))
        ]),
        primary=True,
        id=f"filter-submit-{_gen_id()}"
    )
    components.append(submit_btn)
    field_ids.append(submit_btn.id)

    # Form column
    form_col = column(field_ids, id=f"filter-form-{_gen_id()}")
    components.append(form_col)

    return form_col, components


# =============================================================================
# VALIDATION
# =============================================================================

def validate_messages(messages: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate A2UI messages against the schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import jsonschema
    except ImportError:
        return True, None  # Skip validation if jsonschema not available

    # Basic structural validation
    for i, msg in enumerate(messages):
        valid_keys = {"beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface"}
        msg_keys = set(msg.keys())

        if not msg_keys.intersection(valid_keys):
            return False, f"Message {i} has no valid A2UI message type"

        if len(msg_keys.intersection(valid_keys)) > 1:
            return False, f"Message {i} has multiple message types"

        # Check required fields
        if "beginRendering" in msg:
            br = msg["beginRendering"]
            if "root" not in br or "surfaceId" not in br:
                return False, f"beginRendering message {i} missing required fields"

        if "surfaceUpdate" in msg:
            su = msg["surfaceUpdate"]
            if "surfaceId" not in su or "components" not in su:
                return False, f"surfaceUpdate message {i} missing required fields"

        if "dataModelUpdate" in msg:
            dm = msg["dataModelUpdate"]
            if "surfaceId" not in dm or "contents" not in dm:
                return False, f"dataModelUpdate message {i} missing required fields"

    return True, None


# =============================================================================
# STREAMING HELPERS
# =============================================================================

class A2UIStream:
    """
    Helper for streaming A2UI messages progressively.

    Usage:
        stream = A2UIStream("dashboard")

        # Send initial structure
        yield stream.begin_rendering("root")

        # Stream components as they're generated
        yield stream.surface_update([component1, component2])

        # Update data progressively
        yield stream.data_update({"key": "value"})
    """

    def __init__(
        self,
        surface_id: str,
        primary_color: str = "#6366f1",
        font: str = "Inter"
    ):
        self.surface_id = surface_id
        self.styles = Styles(primary_color=primary_color, font=font)

    def begin_rendering(self, root_id: str, catalog_id: Optional[str] = None) -> str:
        """Generate beginRendering message as JSONL line."""
        msg = BeginRenderingMessage(
            surface_id=self.surface_id,
            root=root_id,
            styles=self.styles,
            catalog_id=catalog_id
        )
        return json.dumps(msg.to_dict())

    def surface_update(self, components: List[Component]) -> str:
        """Generate surfaceUpdate message as JSONL line."""
        msg = SurfaceUpdateMessage(
            surface_id=self.surface_id,
            components=components
        )
        return json.dumps(msg.to_dict())

    def data_update(
        self,
        data: Union[Dict[str, Any], List[DataEntry]],
        path: str = "/"
    ) -> str:
        """Generate dataModelUpdate message as JSONL line."""
        if isinstance(data, dict):
            entries = dict_to_data_entries(data)
        else:
            entries = data

        msg = DataModelUpdateMessage(
            surface_id=self.surface_id,
            contents=entries,
            path=path
        )
        return json.dumps(msg.to_dict())

    def delete(self) -> str:
        """Generate deleteSurface message as JSONL line."""
        msg = DeleteSurfaceMessage(surface_id=self.surface_id)
        return json.dumps(msg.to_dict())


# =============================================================================
# EXAMPLE: DASHBOARD BUILDER
# =============================================================================

def build_dashboard_ui(
    title: str,
    metrics: List[Dict[str, Any]],
    data: Dict[str, Any],
    surface_id: str = "dashboard"
) -> List[Dict[str, Any]]:
    """
    Build a complete dashboard UI with metrics cards.

    Args:
        title: Dashboard title
        metrics: List of metric definitions with:
            - title: str
            - value_path: str (path in data model)
            - icon: Optional[str]
        data: Data model dictionary
        surface_id: Surface identifier

    Returns:
        List of A2UI messages ready for JSONL serialization

    Example:
        messages = build_dashboard_ui(
            title="Sales Dashboard",
            metrics=[
                {"title": "Total Sales", "value_path": "/sales/total", "icon": "shoppingCart"},
                {"title": "Orders", "value_path": "/sales/orders", "icon": "payment"},
            ],
            data={"sales": {"total": "$12,345", "orders": "156"}}
        )
    """
    surface = A2UISurface(surface_id)

    # Title
    title_comp = surface.add(text(title, usage_hint=TextUsageHint.H1, id="dashboard-title"))

    # Metric cards
    metric_card_ids = []
    for m in metrics:
        card_comp, all_comps = create_metric_card(
            title=m["title"],
            value_path=m["value_path"],
            icon_name=m.get("icon"),
            surface=surface
        )
        surface.add_all(all_comps)
        metric_card_ids.append(card_comp.id)

    # Metrics row
    metrics_row = surface.add(row(
        metric_card_ids,
        distribution=Distribution.SPACE_EVENLY,
        id="metrics-row"
    ))

    # Main column
    root = surface.add(column(
        [title_comp.id, metrics_row.id],
        id="root"
    ))

    # Set data
    surface.set_data(data)

    return surface.build(root_id=root.id)
