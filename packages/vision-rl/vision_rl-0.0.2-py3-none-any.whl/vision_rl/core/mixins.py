"""
Core mixins for VisionRL environments.
These mixins provide modular functionality for CV, UI, and debugging.
"""
from typing import Any, Dict, Optional

class CVMixin:
    """
    Mixin for Computer Vision capabilities.
    """
    def get_visual_obs(self) -> Any:
        """
        Abstract method to be implemented by the environment.
        Should return the current visual observation.
        """
        raise NotImplementedError("Environment must implement get_visual_obs()")

class UIMixin:
    """
    Mixin for UI integration capabilities.
    """
    def on_ui_update(self, data: Dict[str, Any]) -> None:
        """
        Hook called when the UI needs to be updated.
        
        Args:
            data: Dictionary containing data to send to the UI.
        """
        # Default implementation does nothing.
        # Can be overridden by subclasses or monkey-patched by UI wrappers.
        pass

class DebugMixin:
    """
    Mixin for debugging and explainability.
    """
    def __init__(self):
        self._debug_info: Dict[str, Any] = {}

    def add_debug_info(self, key: str, value: Any) -> None:
        """
        Add a key-value pair to the debug information.
        
        Args:
            key: Identifier for the debug info.
            value: The data to store.
        """
        self._debug_info[key] = value

    def get_debug_info(self) -> Dict[str, Any]:
        """
        Retrieve current debug information and clear it for the next step.
        """
        info = self._debug_info.copy()
        self._debug_info.clear()
        return info

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Basic logging hook.
        """
        # In a real implementation, this might connect to Python's logging module
        # or a custom logger.
        print(f"[{level}] {message}")
