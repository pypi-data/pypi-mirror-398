import os
import streamlit.components.v1 as components
_RELEASE = True
if not _RELEASE:
    _component_func = components.declare_component(
    "shadcn_context_menu",
    url="http://localhost:3001",
)
else:

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/dist")
    _component_func = components.declare_component("shadcn_context_menu", path=build_dir)

def shadcn_context_menu(items, key=None):
    """
    items: list of dicts -> [{"label": "Profile", "value": "profile"}, ...]
    """
    return _component_func(items=items, key=key, default=None)