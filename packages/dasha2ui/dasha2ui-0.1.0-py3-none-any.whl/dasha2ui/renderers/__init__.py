"""
DashA2UI Renderers

This module provides renderers for converting A2UI messages to various UI frameworks.
Currently supports:
- Dash (dash_renderer)
"""

# Conditional import - only available if dash dependencies are installed
try:
    from dasha2ui.renderers.dash_renderer import A2UIRenderer
    DASH_AVAILABLE = True
except ImportError:
    A2UIRenderer = None
    DASH_AVAILABLE = False

__all__ = ["A2UIRenderer", "DASH_AVAILABLE"]
