"""
Wrapper for logging episode statistics.
"""
import gymnasium as gym
import time
from typing import Any, Dict, Tuple

class EpisodeLoggerWrapper(gym.Wrapper):
    """
    Tracks and logs length and cumulative reward for each episode.
    """
    def __init__(self, env: gym.Env, verbose: bool = True):
        super().__init__(env)
        self.verbose = verbose
        self.episode_reward = 0.0
        self.episode_length = 0
        self.episode_start_time = 0.0
        self._episode_count = 0

    def reset(self, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        obs, info = self.env.reset(**kwargs)
        self.episode_reward = 0.0
        self.episode_length = 0
        self.episode_start_time = time.time()
        return obs, info

    def step(self, action: Any) -> Tuple[Any, float, bool, bool, Dict[str, Any]]:
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        self.episode_reward += reward
        self.episode_length += 1
        
        if terminated or truncated:
            self._episode_count += 1
            duration = time.time() - self.episode_start_time
            
            # Inject stats into info
            episode_info = {
                "r": self.episode_reward,
                "l": self.episode_length,
                "t": duration
            }
            info["episode"] = episode_info
            
            if self.verbose:
                print(f"Episode {self._episode_count}: "
                      f"Reward={self.episode_reward:.2f}, "
                      f"Length={self.episode_length}, "
                      f"Time={duration:.2f}s")
                      
        return obs, reward, terminated, truncated, info
