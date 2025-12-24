"""
Wrapper for overlaying heatmaps on rendering.
"""
import gymnasium as gym
import numpy as np
import cv2
from typing import Optional, Dict

class HeatmapWrapper(gym.Wrapper):
    """
    Overlays a heatmap on the environment render.
    Expects 'heatmap' or 'attention_map' key in the info dictionary.
    The map should be a 2D float array (H, W) or normalized [0, 1].
    """
    def __init__(self, env: gym.Env, colormap: int = cv2.COLORMAP_JET):
        super().__init__(env)
        self._current_heatmap = None
        self.colormap = colormap

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        # Check for heatmap in info
        if 'heatmap' in info:
            self._current_heatmap = info['heatmap']
        elif 'attention_map' in info:
            self._current_heatmap = info['attention_map']
            
        return obs, reward, terminated, truncated, info

    def render(self):
        frame = self.env.render()
        if frame is None:
            return None
            
        if self._current_heatmap is not None:
            frame = self._overlay_heatmap(frame, self._current_heatmap)
            
        return frame

    def _overlay_heatmap(self, frame: np.ndarray, heatmap: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        """
        Applies the heatmap overlay.
        """
        # Ensure frame is RGB
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            
        H, W = frame.shape[:2]
        
        # Resize heatmap to match frame
        heatmap_resized = cv2.resize(heatmap, (W, H))
        
        # Normalize to 0-255 if needed
        if heatmap_resized.max() <= 1.0:
            heatmap_resized = (heatmap_resized * 255).astype(np.uint8)
        else:
            heatmap_resized = heatmap_resized.astype(np.uint8)
            
        # Apply colormap
        heatmap_color = cv2.applyColorMap(heatmap_resized, self.colormap)
        
        # Need to ensure RGB (OpenCV uses BGR for some ops, but gym uses RGB)
        # applyColorMap returns BGR.
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
        # Blend
        overlay = cv2.addWeighted(frame, 1 - alpha, heatmap_color, alpha, 0)
        return overlay
