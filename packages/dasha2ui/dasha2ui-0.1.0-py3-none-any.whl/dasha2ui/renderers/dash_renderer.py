"""
A2UI to Dash Renderer

Converts A2UI JSON messages to Dash components for rendering in a Dash application.

Usage:
    from dasha2ui.renderers.dash_renderer import A2UIRenderer

    renderer = A2UIRenderer()
    renderer.process_messages(a2ui_messages)
    dash_component = renderer.render()

Requires:
    - dash
    - dash-bootstrap-components
    - dash-iconify
"""

from typing import Any, Dict, List, Optional

# Conditional imports for Dash dependencies
try:
    from dash import html
    import dash_bootstrap_components as dbc
    from dash_iconify import DashIconify
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
    html = None
    dbc = None
    DashIconify = None


class A2UIRenderer:
    """
    Renders A2UI JSON messages to Dash components.

    This renderer processes A2UI protocol messages and converts them into
    native Dash HTML and Bootstrap components for display in a Dash application.

    Supports:
    - All standard A2UI components (Text, Image, Icon, Row, Column, Card, etc.)
    - Data model binding with path resolution
    - Flexible weight-based layouts
    - Icon mapping to Material Design Icons via Iconify
    """

    def __init__(self):
        if not DASH_AVAILABLE:
            raise ImportError(
                "Dash dependencies not installed. Install with: "
                "pip install dasha2ui[dash]"
            )
        self.components: Dict[str, Dict] = {}
        self.data_model: Dict[str, Any] = {}
        self.root_id: Optional[str] = None
        self.styles: Dict[str, str] = {}

    def process_messages(self, messages: List[Dict]) -> None:
        """Process A2UI messages to build component tree and data model."""
        for msg in messages:
            if "beginRendering" in msg:
                br = msg["beginRendering"]
                self.root_id = br.get("root")
                self.styles = br.get("styles", {})

            elif "surfaceUpdate" in msg:
                su = msg["surfaceUpdate"]
                for comp in su.get("components", []):
                    self.components[comp["id"]] = comp

            elif "dataModelUpdate" in msg:
                dm = msg["dataModelUpdate"]
                path = dm.get("path", "/")
                self._update_data_model(path, dm.get("contents", []))

    def _update_data_model(self, path: str, contents: List[Dict]) -> None:
        """Update data model at specified path."""
        target = self.data_model

        # Navigate to path (simplified - just handles root for now)
        if path != "/" and path:
            parts = path.strip("/").split("/")
            for part in parts:
                if part not in target:
                    target[part] = {}
                target = target[part]

        # Process contents
        for entry in contents:
            key = entry.get("key")
            if "valueString" in entry:
                target[key] = entry["valueString"]
            elif "valueNumber" in entry:
                target[key] = entry["valueNumber"]
            elif "valueBoolean" in entry:
                target[key] = entry["valueBoolean"]
            elif "valueMap" in entry:
                target[key] = {}
                self._update_data_model(f"/{key}", entry["valueMap"])

    def _resolve_bound_value(self, bound: Dict) -> Any:
        """Resolve a bound value from literal or data model."""
        if "literalString" in bound:
            return bound["literalString"]
        if "literalNumber" in bound:
            return bound["literalNumber"]
        if "literalBoolean" in bound:
            return bound["literalBoolean"]
        if "path" in bound:
            return self._get_data_at_path(bound["path"])
        return ""

    def _get_data_at_path(self, path: str) -> Any:
        """Get data from data model at path."""
        if not path:
            return ""

        parts = path.strip("/").split("/")
        current = self.data_model

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return f"[{path}]"

        return current

    def render(self) -> Any:
        """Render the A2UI tree to Dash components."""
        if not self.root_id or self.root_id not in self.components:
            return html.Div("No UI to render", className="text-muted")

        primary_color = self.styles.get("primaryColor", "#6366f1")

        return html.Div(
            self._render_component(self.root_id),
            style={"--a2ui-primary": primary_color}
        )

    def _render_component(self, component_id: str) -> Any:
        """Recursively render a component by ID."""
        if component_id not in self.components:
            return html.Span(f"[Missing: {component_id}]", className="text-danger")

        comp_def = self.components[component_id]
        comp_wrapper = comp_def.get("component", {})
        weight = comp_def.get("weight")

        # Get the component type (first key in wrapper)
        comp_type = list(comp_wrapper.keys())[0] if comp_wrapper else None
        props = comp_wrapper.get(comp_type, {})

        # Build style with weight if specified
        style = {}
        if weight:
            style["flex"] = weight

        # Render based on type
        if comp_type == "Text":
            return self._render_text(props, style)
        elif comp_type == "Image":
            return self._render_image(props, style)
        elif comp_type == "Icon":
            return self._render_icon(props, style)
        elif comp_type == "Row":
            return self._render_row(props, style)
        elif comp_type == "Column":
            return self._render_column(props, style)
        elif comp_type == "Card":
            return self._render_card(props, style)
        elif comp_type == "Button":
            return self._render_button(props, style)
        elif comp_type == "Divider":
            return self._render_divider(props, style)
        elif comp_type == "List":
            return self._render_list(props, style)
        else:
            return html.Div(f"[Unknown: {comp_type}]", style=style)

    def _render_text(self, props: Dict, style: Dict) -> Any:
        """Render Text component."""
        text_value = self._resolve_bound_value(props.get("text", {}))
        hint = props.get("usageHint", "body")

        text_styles = {
            "h1": {"fontSize": "2rem", "fontWeight": "700", "marginBottom": "0.5rem"},
            "h2": {"fontSize": "1.5rem", "fontWeight": "600", "marginBottom": "0.4rem"},
            "h3": {"fontSize": "1.25rem", "fontWeight": "600", "marginBottom": "0.3rem"},
            "h4": {"fontSize": "1.1rem", "fontWeight": "500"},
            "h5": {"fontSize": "1rem", "fontWeight": "500"},
            "caption": {"fontSize": "0.85rem", "color": "#64748b"},
            "body": {"fontSize": "1rem"},
        }

        combined_style = {**text_styles.get(hint, {}), **style}
        return html.Div(str(text_value), style=combined_style)

    def _render_image(self, props: Dict, style: Dict) -> Any:
        """Render Image component."""
        url = self._resolve_bound_value(props.get("url", {}))
        fit = props.get("fit", "cover")
        hint = props.get("usageHint", "mediumFeature")

        size_styles = {
            "icon": {"width": "24px", "height": "24px"},
            "avatar": {"width": "48px", "height": "48px", "borderRadius": "50%"},
            "smallFeature": {"maxWidth": "150px", "maxHeight": "100px"},
            "mediumFeature": {"maxWidth": "300px", "maxHeight": "200px"},
            "largeFeature": {"maxWidth": "100%", "maxHeight": "400px"},
            "header": {"width": "100%", "maxHeight": "200px"},
        }

        img_style = {
            **size_styles.get(hint, {}),
            "objectFit": fit,
            **style
        }

        return html.Img(src=url, style=img_style)

    def _render_icon(self, props: Dict, style: Dict) -> Any:
        """Render Icon component."""
        name = self._resolve_bound_value(props.get("name", {}))

        # Map A2UI icon names to iconify icons
        icon_map = {
            "check": "mdi:check",
            "error": "mdi:alert-circle",
            "info": "mdi:information",
            "warning": "mdi:alert",
            "star": "mdi:star",
            "starOff": "mdi:star-outline",
            "starHalf": "mdi:star-half-full",
            "favorite": "mdi:heart",
            "favoriteOff": "mdi:heart-outline",
            "settings": "mdi:cog",
            "search": "mdi:magnify",
            "home": "mdi:home",
            "person": "mdi:account",
            "mail": "mdi:email",
            "phone": "mdi:phone",
            "calendar": "mdi:calendar",
            "calendarToday": "mdi:calendar-today",
            "delete": "mdi:delete",
            "edit": "mdi:pencil",
            "add": "mdi:plus",
            "close": "mdi:close",
            "menu": "mdi:menu",
            "arrowBack": "mdi:arrow-left",
            "arrowForward": "mdi:arrow-right",
            "refresh": "mdi:refresh",
            "download": "mdi:download",
            "upload": "mdi:upload",
            "share": "mdi:share",
            "shoppingCart": "mdi:cart",
            "payment": "mdi:credit-card",
            "locationOn": "mdi:map-marker",
            "notifications": "mdi:bell",
            "notificationsOff": "mdi:bell-off",
            "visibility": "mdi:eye",
            "visibilityOff": "mdi:eye-off",
            "lock": "mdi:lock",
            "lockOpen": "mdi:lock-open",
            "folder": "mdi:folder",
            "photo": "mdi:image",
            "camera": "mdi:camera",
            "print": "mdi:printer",
            "help": "mdi:help-circle",
            "accountCircle": "mdi:account-circle",
            "moreVert": "mdi:dots-vertical",
            "moreHoriz": "mdi:dots-horizontal",
            "attachFile": "mdi:attachment",
            "call": "mdi:phone",
            "event": "mdi:calendar-check",
            "send": "mdi:send",
        }

        iconify_name = icon_map.get(name, f"mdi:{name}")
        return html.Span(DashIconify(icon=iconify_name, width=24), style=style)

    def _render_row(self, props: Dict, style: Dict) -> Any:
        """Render Row component."""
        children = self._get_children(props)
        distribution = props.get("distribution", "start")
        alignment = props.get("alignment", "center")

        justify_map = {
            "start": "flex-start",
            "center": "center",
            "end": "flex-end",
            "spaceBetween": "space-between",
            "spaceAround": "space-around",
            "spaceEvenly": "space-evenly",
        }

        align_map = {
            "start": "flex-start",
            "center": "center",
            "end": "flex-end",
            "stretch": "stretch",
        }

        row_style = {
            "display": "flex",
            "flexDirection": "row",
            "justifyContent": justify_map.get(distribution, "flex-start"),
            "alignItems": align_map.get(alignment, "center"),
            "gap": "1rem",
            **style
        }

        return html.Div(
            [self._render_component(child_id) for child_id in children],
            style=row_style
        )

    def _render_column(self, props: Dict, style: Dict) -> Any:
        """Render Column component."""
        children = self._get_children(props)
        distribution = props.get("distribution", "start")
        alignment = props.get("alignment", "stretch")

        justify_map = {
            "start": "flex-start",
            "center": "center",
            "end": "flex-end",
            "spaceBetween": "space-between",
            "spaceAround": "space-around",
            "spaceEvenly": "space-evenly",
        }

        align_map = {
            "start": "flex-start",
            "center": "center",
            "end": "flex-end",
            "stretch": "stretch",
        }

        col_style = {
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": justify_map.get(distribution, "flex-start"),
            "alignItems": align_map.get(alignment, "stretch"),
            "gap": "0.5rem",
            **style
        }

        return html.Div(
            [self._render_component(child_id) for child_id in children],
            style=col_style
        )

    def _render_list(self, props: Dict, style: Dict) -> Any:
        """Render List component."""
        children = self._get_children(props)
        direction = props.get("direction", "vertical")

        list_style = {
            "display": "flex",
            "flexDirection": "column" if direction == "vertical" else "row",
            "gap": "0.5rem",
            "overflowY": "auto" if direction == "vertical" else "hidden",
            "overflowX": "auto" if direction == "horizontal" else "hidden",
            **style
        }

        return html.Div(
            [self._render_component(child_id) for child_id in children],
            style=list_style
        )

    def _render_card(self, props: Dict, style: Dict) -> Any:
        """Render Card component."""
        child_id = props.get("child")

        card_style = {
            "backgroundColor": "white",
            "borderRadius": "8px",
            "padding": "1rem",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
            "border": "1px solid #e2e8f0",
            **style
        }

        return html.Div(
            self._render_component(child_id) if child_id else None,
            style=card_style
        )

    def _render_button(self, props: Dict, style: Dict) -> Any:
        """Render Button component."""
        child_id = props.get("child")
        primary = props.get("primary", False)
        action = props.get("action", {})

        btn_style = {
            "padding": "0.5rem 1rem",
            "borderRadius": "6px",
            "cursor": "pointer",
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "border": "none",
            "backgroundColor": "#6366f1" if primary else "#f1f5f9",
            "color": "white" if primary else "#374151",
            **style
        }

        import json
        return html.Button(
            self._render_component(child_id) if child_id else "Button",
            style=btn_style,
            **{"data-action": json.dumps(action)} if action else {}
        )

    def _render_divider(self, props: Dict, style: Dict) -> Any:
        """Render Divider component."""
        axis = props.get("axis", "horizontal")

        if axis == "vertical":
            div_style = {
                "width": "1px",
                "height": "100%",
                "backgroundColor": "#e2e8f0",
                "margin": "0 0.5rem",
                **style
            }
            return html.Div(style=div_style)
        else:
            return html.Hr(style={"borderColor": "#e2e8f0", "margin": "0.5rem 0", **style})

    def _get_children(self, props: Dict) -> List[str]:
        """Get child IDs from children property."""
        children_prop = props.get("children", {})

        if "explicitList" in children_prop:
            return children_prop["explicitList"]
        elif "template" in children_prop:
            # For templates, we'd need to iterate data - simplified here
            template = children_prop["template"]
            data_path = template.get("dataBinding", "")
            component_id = template.get("componentId", "")

            # Get data at path
            data = self._get_data_at_path(data_path)
            if isinstance(data, dict):
                # For now, just return the template component for each key
                return [component_id] * len(data)
            return []

        return []

    def clear(self) -> None:
        """Clear the renderer state."""
        self.components = {}
        self.data_model = {}
        self.root_id = None
        self.styles = {}
