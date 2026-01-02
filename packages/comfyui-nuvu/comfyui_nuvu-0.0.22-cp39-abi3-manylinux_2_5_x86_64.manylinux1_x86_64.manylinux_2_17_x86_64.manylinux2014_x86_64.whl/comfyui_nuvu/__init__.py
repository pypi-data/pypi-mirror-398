"""
comfyui_nuvu - nuvu extension package for ComfyUI

This is the generic package init for the pip-installable wheel.
It has NO import-time side effects (no route registration, no ComfyUI dependencies).

Route registration happens only when ComfyUI loads the custom node entrypoint
(custom_nodes/ComfyUI-nuvu/__init__.py), NOT when importing this package.
"""

__version__ = "0.0.22"  # Replaced by CI from git tag
__all__ = ["__version__"]


