"""
DashA2UI - A2UI Protocol Implementation for Dash

A2UI (Agent-to-User Interface) is a protocol for generating declarative,
streaming UI payloads that can be rendered by A2UI-compatible clients.

This package provides:
- Complete A2UI v0.8 protocol implementation
- Component factory functions for building UIs
- Surface builders for managing UI state
- Optional Dash renderer for converting A2UI to Dash components

Usage:
    from dasha2ui import (
        A2UISurface, text, row, column, card,
        TextUsageHint, build_dashboard_ui
    )

    # Build a simple dashboard
    surface = A2UISurface("my-dashboard")
    title = surface.add(text("Hello World", usage_hint=TextUsageHint.H1))
    root = surface.add(column([title.id]))
    messages = surface.build(root_id=root.id)

For Dash rendering:
    from dasha2ui.renderers.dash_renderer import A2UIRenderer

    renderer = A2UIRenderer()
    renderer.process_messages(messages)
    dash_component = renderer.render()
"""

from dasha2ui.core import (
    # Version
    A2UI_VERSION,
    A2UI_MIME_TYPE,
    STANDARD_CATALOG_ID,
    # Bound values
    BoundString,
    BoundNumber,
    BoundBoolean,
    BoundArray,
    BoundValue,
    # Children
    ExplicitChildren,
    TemplateChildren,
    Children,
    # Actions
    Action,
    ActionContext,
    # Enums
    TextUsageHint,
    ImageUsageHint,
    ImageFit,
    Alignment,
    Distribution,
    ListDirection,
    TextFieldType,
    DividerAxis,
    IconName,
    # Components
    Component,
    text,
    image,
    icon,
    row,
    column,
    list_component,
    card,
    divider,
    button,
    text_field,
    datetime_input,
    checkbox,
    slider,
    multiple_choice,
    tabs,
    modal,
    video,
    audio_player,
    MultipleChoiceOption,
    TabItem,
    # Data model
    DataEntry,
    data_string,
    data_number,
    data_boolean,
    data_map,
    dict_to_data_entries,
    # Messages
    Styles,
    BeginRenderingMessage,
    SurfaceUpdateMessage,
    DataModelUpdateMessage,
    DeleteSurfaceMessage,
    A2UIMessage,
    # Events
    UserActionEvent,
    ClientErrorEvent,
    # Builders
    A2UISurface,
    A2UIStream,
    # Templates
    create_metric_card,
    create_data_table,
    create_chart_placeholder,
    create_filter_form,
    # Utilities
    validate_messages,
    build_dashboard_ui,
)

__version__ = "0.1.0"
__all__ = [
    # Version
    "A2UI_VERSION",
    "A2UI_MIME_TYPE",
    "STANDARD_CATALOG_ID",
    # Bound values
    "BoundString",
    "BoundNumber",
    "BoundBoolean",
    "BoundArray",
    "BoundValue",
    # Children
    "ExplicitChildren",
    "TemplateChildren",
    "Children",
    # Actions
    "Action",
    "ActionContext",
    # Enums
    "TextUsageHint",
    "ImageUsageHint",
    "ImageFit",
    "Alignment",
    "Distribution",
    "ListDirection",
    "TextFieldType",
    "DividerAxis",
    "IconName",
    # Components
    "Component",
    "text",
    "image",
    "icon",
    "row",
    "column",
    "list_component",
    "card",
    "divider",
    "button",
    "text_field",
    "datetime_input",
    "checkbox",
    "slider",
    "multiple_choice",
    "tabs",
    "modal",
    "video",
    "audio_player",
    "MultipleChoiceOption",
    "TabItem",
    # Data model
    "DataEntry",
    "data_string",
    "data_number",
    "data_boolean",
    "data_map",
    "dict_to_data_entries",
    # Messages
    "Styles",
    "BeginRenderingMessage",
    "SurfaceUpdateMessage",
    "DataModelUpdateMessage",
    "DeleteSurfaceMessage",
    "A2UIMessage",
    # Events
    "UserActionEvent",
    "ClientErrorEvent",
    # Builders
    "A2UISurface",
    "A2UIStream",
    # Templates
    "create_metric_card",
    "create_data_table",
    "create_chart_placeholder",
    "create_filter_form",
    # Utilities
    "validate_messages",
    "build_dashboard_ui",
]
