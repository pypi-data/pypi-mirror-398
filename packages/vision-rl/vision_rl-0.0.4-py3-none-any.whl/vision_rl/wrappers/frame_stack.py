"""
Wrapper for stacking frames.
"""
import gymnasium as gym
import numpy as np
from gymnasium import spaces
from collections import deque
from typing import Any, Tuple, Dict

class FrameStack(gym.Wrapper):
    """
    Stacks k last frames.
    If observations are images (H, W, C), output is (H, W, C*k) or (k, H, W, C) depending on convention.
    Here we stack along the last channel for compatibility with common CNNs (H, W, C*k).
    """
    def __init__(self, env: gym.Env, num_stack: int = 4):
        super().__init__(env)
        self.num_stack = num_stack
        self.frames = deque(maxlen=num_stack)

        obs_space = env.observation_space
        if not isinstance(obs_space, spaces.Box):
             raise ValueError("FrameStack only works with Box observation spaces.")
        
        # Calculate new shape
        low = np.repeat(obs_space.low, num_stack, axis=-1)
        high = np.repeat(obs_space.high, num_stack, axis=-1)
        
        # Assume standard HWC image format
        # If shape is (H, W, C) -> (H, W, C*k)
        # If shape is (H, W) -> (H, W, k) by expanding dims first
        
        self.is_grayscale = len(obs_space.shape) == 2
        if self.is_grayscale:
            # (H, W)
            shape = obs_space.shape + (num_stack,)
            # Expand low/high if they were 2D
             # Rethink: usually grayscale means (H, W). We want (H, W, K).
             # We need to treat the incoming frame as (H, W, 1) effectively.
             # Easier to just rely on spaces logic or force channel-last.
            pass
        else:
            # (H, W, C)
            shape = list(obs_space.shape)
            shape[-1] *= num_stack
            shape = tuple(shape)

        self.observation_space = spaces.Box(
            low=low, high=high, shape=shape, dtype=obs_space.dtype
        )

    def reset(self, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        obs, info = self.env.reset(**kwargs)
        for _ in range(self.num_stack):
            self.frames.append(obs)
        return self._get_observation(), info

    def step(self, action: Any) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
        obs, reward, terminated, truncated, info = self.env.step(action)
        self.frames.append(obs)
        return self._get_observation(), reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        assert len(self.frames) == self.num_stack
        # Stack along the last axis (channel)
        # If frames are (H, W, C), stack makes (num_stack, H, W, C)
        # We want to concatenate along C.
        if self.is_grayscale:
             return np.dstack(self.frames)
        else:
             return np.concatenate(self.frames, axis=-1)
