"""
Base VisualEnv class connecting Gymnasium with VisionRL mixins.
"""
import gymnasium as gym
from typing import Optional, Tuple, Dict, Any, Union

from .mixins import CVMixin, UIMixin, DebugMixin

class VisualEnv(gym.Env, CVMixin, UIMixin, DebugMixin):
    """
    Base class for visual environments in VisionRL.
    Extends gymnasium.Env and adds support for:
    - Visual observations (CVMixin)
    - UI updates (UIMixin)
    - Debugging (DebugMixin)
    """
    metadata = {"render_modes": ["rgb_array", "human"], "render_fps": 30}

    def __init__(self, render_mode: Optional[str] = None):
        """
        Initialize the VisualEnv.
        
        Args:
            render_mode: The render mode to use.
        """
        self.render_mode = render_mode
        # Initialize DebugMixin explicitly if needed, though simple mixins usually don't need it.
        # But our DebugMixin has an __init__ to set up _debug_info.
        DebugMixin.__init__(self)

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Reset the environment and trigger UI updates.
        """
        # Call gym's reset (handles seeding)
        obs, info = super().reset(seed=seed, options=options)
        
        # Trigger UI update
        self._trigger_ui_update("reset", obs, info)
        
        return obs, info

    def step(self, action: Any) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
        """
        Step the environment, log debug info, and trigger UI updates.
        """
        obs, reward, terminated, truncated, info = super().step(action)
        
        # Collect debug info
        debug_data = self.get_debug_info()
        if debug_data:
            info["debug"] = debug_data

        # Trigger UI update
        self._trigger_ui_update("step", obs, info, action, reward, terminated, truncated)
        
        return obs, reward, terminated, truncated, info

    def _trigger_ui_update(self, event_type: str, obs: Any, info: Dict[str, Any], 
                           action: Any = None, reward: float = 0.0, 
                           terminated: bool = False, truncated: bool = False) -> None:
        """
        Helper to construct the data packet for the UI mixin.
        """
        data = {
            "event": event_type,
            "obs": obs,
            "info": info,
            "render_mode": self.render_mode
        }
        if event_type == "step":
            data.update({
                "action": action,
                "reward": reward,
                "terminated": terminated,
                "truncated": truncated
            })
            
        self.on_ui_update(data)
