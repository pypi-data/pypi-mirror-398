"""
Matplotlib-based dashboard for VisionRL.
"""
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
from typing import Optional, Dict, Any, List

class VisionDashboard:
    """
    A real-time dashboard for visualizing RL agents.
    Displays:
    - Current Observation (Image)
    - Reward History (Plot)
    - Last Action (Text/Bar)
    - Episode Info (Text)
    """
    def __init__(self, title="VisionRL Dashboard"):
        self.title = title
        
        # turn on interactive mode
        plt.ion()
        
        self.fig = plt.figure(figsize=(12, 8), constrained_layout=True)
        self.fig.canvas.manager.set_window_title(title)
        
        gs = GridSpec(2, 2, figure=self.fig)
        
        # 1. Main View (Top Left)
        self.ax_view = self.fig.add_subplot(gs[0, 0])
        self.ax_view.set_title("Agent View")
        self.ax_view.axis('off')
        self.im_view = None
        
        # 2. Reward Plot (Top Right)
        self.ax_reward = self.fig.add_subplot(gs[0, 1])
        self.ax_reward.set_title("Rewards over Time")
        self.ax_reward.set_xlabel("Step")
        self.ax_reward.set_ylabel("Reward")
        self.reward_line, = self.ax_reward.plot([], [], 'g-', label="Instant Reward")
        self.ax_reward.legend()
        
        # 3. Action History (Bottom Left)
        self.ax_action = self.fig.add_subplot(gs[1, 0])
        self.ax_action.set_title("Last Action")
        self.ax_action.axis('off')
        self.tx_action = self.ax_action.text(0.5, 0.5, "Waiting...", 
                                           ha='center', va='center', fontsize=20)
        
        # 4. Info Panel (Bottom Right)
        self.ax_info = self.fig.add_subplot(gs[1, 1])
        self.ax_info.set_title("Episode Info")
        self.ax_info.axis('off')
        self.tx_info = self.ax_info.text(0.1, 0.5, "Initializing...", 
                                       va='center', fontsize=12, fontfamily='monospace')

        # Data store
        self.rewards: List[float] = []
        self.steps: List[int] = []
        self.total_steps = 0
        
    def update(self, data: Dict[str, Any]):
        """
        Updates the dashboard with new data.
        Expected keys in data:
            - obs: image array
            - reward: float
            - action: int/str
            - info: dict
            - terminated: bool
        """
        # Unwrap data
        obs = data.get("obs")
        reward = data.get("reward", 0.0)
        action = data.get("action")
        info = data.get("info", {})
        event = data.get("event")
        
        if event == "reset":
            # Optional: Clear plots on reset or mark it
            # self.rewards = []
            # self.steps = []
            pass
            
        # 1. Update View
        if obs is not None and isinstance(obs, np.ndarray):
            # Ensure valid image shape for matplotlib
            if len(obs.shape) == 3 or len(obs.shape) == 2:
                if self.im_view is None:
                    self.im_view = self.ax_view.imshow(obs)
                else:
                    self.im_view.set_data(obs)
        
        # 2. Update Rewards
        if event == "step":
            self.total_steps += 1
            self.steps.append(self.total_steps)
            self.rewards.append(reward)
            
            # Update plot data
            self.reward_line.set_data(self.steps, self.rewards)
            self.ax_reward.relim()
            self.ax_reward.autoscale_view()
            
        # 3. Update Action
        if action is not None:
            self.tx_action.set_text(f"Action: {action}")
            
        # 4. Update Info
        info_str = f"Step: {self.total_steps}\n"
        info_str += f"Last Reward: {reward:.2f}\n"
        if "prob" in info:
            info_str += f"Prob: {info['prob']}\n"
        if data.get("terminated"):
            info_str += "\nSTATUS: TERMINATED"
        elif data.get("truncated"):
            info_str += "\nSTATUS: TRUNCATED"
        else:
            info_str += "\nSTATUS: RUNNING"
            
        self.tx_info.set_text(info_str)
        
        # Redraw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
    def close(self):
        plt.close(self.fig)
