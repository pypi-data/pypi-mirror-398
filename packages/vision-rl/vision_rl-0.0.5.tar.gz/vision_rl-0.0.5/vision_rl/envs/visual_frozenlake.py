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
        
        self.q_values = None # Store Q-table for visualization
        
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
        info = {"prob": 1, "agent_state": self.s}
        
        # Manually trigger UI update (usually VisualEnv does this, but we bypassed it)
        # Send rendered frame so UI is not blank
        img = self.render()
        self._trigger_ui_update("reset", img, info)
        
        return obs, info

    def set_q_values(self, q_values):
        """
        Set the Q-values for visualization.
        Args:
            q_values: Numpy array of shape (n_states, n_actions) or similar.
        """
        self.q_values = q_values

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
        info = {"prob": 1, "agent_state": self.s}
        
        # Manually trigger UI update
        # We send the RENDERED image to the UI, not the internal state (int)
        img = self.render()
        self._trigger_ui_update("step", img, info, action, reward, terminated, truncated)
        
        return obs, reward, terminated, truncated, info

    def render(self):
        """
        Renders the grid using OpenCV.
        """
        """
        Renders the grid using OpenCV.
        """
        cell_size = 100
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

                # Draw Q-values if available
                if self.q_values is not None:
                    # q_values row for this cell
                    # state index = r * ncol + c
                    s_idx = r * self.ncol + c
                    
                    if s_idx < len(self.q_values):
                        q_row = self.q_values[s_idx]
                        
                        # 0: Left, 1: Down, 2: Right, 3: Up
                        # Position text in the corresponding quadrant of the cell
                        
                        # Font settings
                        q_font = cv2.FONT_HERSHEY_SIMPLEX
                        q_scale = 0.35
                        q_color = (0, 0, 0)
                        q_thick = 1
                        
                        # Offsets from center
                        offset = cell_size // 4
                        
                        center_x = x1 + cell_size // 2
                        center_y = y1 + cell_size // 2
                        
                        # Left (0)
                        l_text = f"{q_row[0]:.2f}"
                        cv2.putText(img, l_text, (x1 + 5, center_y), q_font, q_scale, q_color, q_thick)
                        
                        # Down (1)
                        d_text = f"{q_row[1]:.2f}"
                        # Centered at bottom
                        d_size = cv2.getTextSize(d_text, q_font, q_scale, q_thick)[0]
                        cv2.putText(img, d_text, (center_x - d_size[0]//2, y2 - 5), q_font, q_scale, q_color, q_thick)
                        
                        # Right (2)
                        r_text = f"{q_row[2]:.2f}"
                        r_size = cv2.getTextSize(r_text, q_font, q_scale, q_thick)[0]
                        cv2.putText(img, r_text, (x2 - r_size[0] - 5, center_y), q_font, q_scale, q_color, q_thick)
                        
                        # Up (3)
                        u_text = f"{q_row[3]:.2f}"
                        u_size = cv2.getTextSize(u_text, q_font, q_scale, q_thick)[0]
                        cv2.putText(img, u_text, (center_x - u_size[0]//2, y1 + 15), q_font, q_scale, q_color, q_thick)

        # Draw Agent
        row = self.s // self.ncol
        col = self.s % self.ncol
        
        center_x = int(col * cell_size + cell_size / 2)
        center_y = int(row * cell_size + cell_size / 2)
        radius = int(cell_size / 3)
        
        cv2.circle(img, (center_x, center_y), radius, COLOR_AGENT, -1)
        
        # Draw State Number
        text = str(self.s)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = center_x - text_size[0] // 2
        text_y = center_y + text_size[1] // 2
        
        cv2.putText(img, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
        
        # Convert BGR to RGB for gym return
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
