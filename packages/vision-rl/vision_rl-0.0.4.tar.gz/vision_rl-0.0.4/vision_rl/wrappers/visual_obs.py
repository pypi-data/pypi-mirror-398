"""
Wrapper for converting environment state into visual observations.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Optional, Any

class VisualObservationWrapper(gym.ObservationWrapper):
    """
    Wraps an environment to return its render output as the observation.
    Useful for environments that natively support 'rgb_array' rendering but return
    feature vectors by default.
    """
    def __init__(self, env: gym.Env, shape: Optional[tuple] = None):
        super().__init__(env)
        
        # Check if environment supports rgb_array
        if not hasattr(env, "render_mode") or env.render_mode != "rgb_array":
            # Try to force set it if possible, otherwise warn
            env.render_mode = "rgb_array"
            
        # Get a sample frame to determine observation space
        try:
            sample_frame = env.render()
            if sample_frame is None:
                raise ValueError("Env.render() returned None. Ensure render_mode is 'rgb_array'.")
            
            self.observation_space = spaces.Box(
                low=0, 
                high=255, 
                shape=sample_frame.shape, 
                dtype=np.uint8
            )
        except Exception as e:
            # If we can't render yet (maybe requires reset), use provided shape or dummy
            if shape:
                 self.observation_space = spaces.Box(
                    low=0, high=255, shape=shape, dtype=np.uint8
                )
            else:
                # Fallback, likely will be updated on first reset if not cautious
                pass

    def observation(self, observation: Any) -> np.ndarray:
        """
        Returns the current render frame as the observation.
        The original observation is ignored (or could be stored in info if needed).
        """
        frame = self.env.render()
        if frame is None:
            # Fallback if render fails, return zeros matching space
            return np.zeros(self.observation_space.shape, dtype=np.uint8)
        return frame
