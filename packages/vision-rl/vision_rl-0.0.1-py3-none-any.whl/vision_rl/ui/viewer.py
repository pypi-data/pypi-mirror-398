"""
Viewer class that connects an environment to the VisionDashboard.
"""
from typing import Any, Dict
from ..core.visual_env import VisualEnv
from .dashboard import VisionDashboard

class VisionViewer:
    """
    Connects a VisualEnv to a VisionDashboard.
    It patches the env's on_ui_update method to feed data to the dashboard.
    """
    def __init__(self, env: VisualEnv):
        self.env = env
        self.dashboard = VisionDashboard()
        
        # Monkey patch the env's UI hook
        # We need to find the underlying VisualEnv in case of wrappers
        target_env = env
        while hasattr(target_env, "env"):
            if hasattr(target_env, "on_ui_update"):
                # Found it (or a wrapper that exposes it)
                break
            target_env = target_env.env
            
        # If we unwrapped everything and still didn't find it, we might be at the base
        if not hasattr(target_env, "on_ui_update"):
             # It might be that the wrapper chain hid it, or the env isn't a VisualEnv
             # Try .unwrapped
             target_env = env.unwrapped

        if hasattr(target_env, "on_ui_update"):
            self._original_on_ui_update = target_env.on_ui_update
            target_env.on_ui_update = self._on_ui_update_hook
        else:
            print("Warning: Could not find 'on_ui_update' hook in environment. UI might not update.")

        
    def _on_ui_update_hook(self, data: Dict[str, Any]):
        """
        Intercepts update from env and sends to dashboard.
        """
        # Call original if it existed (though usually empty)
        self._original_on_ui_update(data)
        
        # Update dashboard
        self.dashboard.update(data)
        
    def close(self):
        self.dashboard.close()
        # Restore hook? Not strictly necessary for this scope.
