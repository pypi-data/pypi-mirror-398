"""
Visual FrozenLake environment.
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import cv2
from typing import Optional

from ..core.visual_env import VisualEnv

class VisualFrozenLake(VisualEnv):
    """
    FrozenLake with direct CV2 rendering.
    
    Map:
    S F F F
    F H F H
    F F F H
    H F F G
    """
    def __init__(self, render_mode: Optional[str] = "rgb_array", map_name="4x4", is_slippery=True):
        super().__init__(render_mode=render_mode)
        
        # Use standard frozen lake logic under the hood if possible, or reimplement simple version
        # For this demo, we'll wrap the standard logic manually to ensure full control over state
        
        self.desc = np.asarray([
            "SFFF",
            "FHFH",
            "FFFH",
            "HFFG"
        ], dtype="c")
        
        self.nrow, self.ncol = 4, 4
        self.observation_space = spaces.Discrete(self.nrow * self.ncol)
        self.action_space = spaces.Discrete(4) # 0: Left, 1: Down, 2: Right, 3: Up
        
        self.is_slippery = is_slippery
        self.s = 0 # Current state (flat index)
        self.lastaction = None
        
        self.render_fps = 4

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        # We call gym.Env.reset directly for seeding, skipping VisualEnv's wrapping reset 
        # because VisualEnv expects super() to return obs, which gym.Env does not.
        gym.Env.reset(self, seed=seed, options=options)
        
        self.s = 0
        self.lastaction = None
        
        desc_flat = self.desc.flatten()
        # Ensure we start at S
        self.s = 0 
        
        obs = self.s
        info = {"prob": 1}
        
        # Manually trigger UI update (usually VisualEnv does this, but we bypassed it)
        self._trigger_ui_update("reset", obs, info)
        
        return obs, info

    def step(self, action):
        # Bypass VisualEnv.step for same reason
        
        row = self.s // self.ncol
        col = self.s % self.ncol
        
        # Dynamics (simplified deterministic for visual demo unless slippery requested)
        # 0: Left, 1: Down, 2: Right, 3: Up
        
        if self.is_slippery:
             # Randomness placeholder
             pass
        
        # Simple move logic
        if action == 0: # Left
            col = max(col - 1, 0)
        elif action == 1: # Down
            row = min(row + 1, self.nrow - 1)
        elif action == 2: # Right
            col = min(col + 1, self.ncol - 1)
        elif action == 3: # Up
            row = max(row - 1, 0)
            
        new_s = row * self.ncol + col
        self.s = new_s
        self.lastaction = action
        
        char = self.desc.flatten()[new_s].decode('utf-8')
        
        reward = 0.0
        terminated = False
        truncated = False
        
        if char == 'G':
            reward = 1.0
            terminated = True
        elif char == 'H':
            terminated = True
            
        obs = self.s
        info = {"prob": 1}
        
        # Manually trigger UI update
        self._trigger_ui_update("step", obs, info, action, reward, terminated, truncated)
        
        return obs, reward, terminated, truncated, info

    def render(self):
        """
        Renders the grid using OpenCV.
        """
        cell_size = 64
        height = self.nrow * cell_size
        width = self.ncol * cell_size
        
        # Create canvas (BGR for OpenCV)
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Colors (BGR)
        COLOR_ICE = (255, 200, 150)   # Light blueish
        COLOR_HOLE = (50, 50, 50)     # Dark Grey
        COLOR_START = (100, 255, 100) # Green
        COLOR_GOAL = (100, 200, 255)  # Gold/Yellow-ish
        COLOR_AGENT = (50, 50, 255)   # Red
        
        # Draw grid
        for r in range(self.nrow):
            for c in range(self.ncol):
                char = self.desc[r, c].decode('utf-8')
                
                # Top left corner of cell
                x1 = c * cell_size
                y1 = r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                color = COLOR_ICE
                if char == 'H': color = COLOR_HOLE
                elif char == 'S': color = COLOR_START
                elif char == 'G': color = COLOR_GOAL
                
                # Fill cell
                cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
                
                # Draw grid lines
                cv2.rectangle(img, (x1, y1), (x2, y2), (200, 200, 200), 1)

        # Draw Agent
        row = self.s // self.ncol
        col = self.s % self.ncol
        
        center_x = int(col * cell_size + cell_size / 2)
        center_y = int(row * cell_size + cell_size / 2)
        radius = int(cell_size / 3)
        
        cv2.circle(img, (center_x, center_y), radius, COLOR_AGENT, -1)
        
        # Convert BGR to RGB for gym return
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
