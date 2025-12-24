"""
Test script for wrappers.
"""
import sys
import os
import numpy as np
import gymnasium as gym

# Add package to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from vision_rl.core.visual_env import VisualEnv
from vision_rl.wrappers.visual_obs import VisualObservationWrapper
from vision_rl.wrappers.logger import EpisodeLoggerWrapper
from vision_rl.wrappers.frame_stack import FrameStack
from vision_rl.wrappers.heatmap import HeatmapWrapper

class DummyEnv(VisualEnv):
    def __init__(self):
        super().__init__(render_mode="rgb_array")
        self.observation_space = gym.spaces.Discrete(5)
        self.action_space = gym.spaces.Discrete(2)
        
    def reset(self, seed=None, options=None):
        return 0, {}
        
    def step(self, action):
        # Fake heatmap
        heatmap = np.random.rand(10, 10)
        return 0, 1.0, False, False, {"heatmap": heatmap}

    def render(self):
        # Return a red square
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :, 0] = 255 
        return img

def test_wrappers():
    env = DummyEnv()
    
    # 1. Test VisualObs
    env = VisualObservationWrapper(env)
    assert isinstance(env.observation_space, gym.spaces.Box)
    print("VisualObservationWrapper verified: Obs is Box")
    
    # 2. Test FrameStack
    env = FrameStack(env, num_stack=4)
    assert env.observation_space.shape[-1] == 12 # 3 channels * 4
    print("FrameStack verified: Shape correct")
    
    # 3. Test Heatmap
    env = HeatmapWrapper(env)
    
    # 4. Test Logger
    env = EpisodeLoggerWrapper(env, verbose=True)
    
    obs, info = env.reset()
    assert obs.shape == (100, 100, 12)
    
    # Step
    obs, r, term, trunc, info = env.step(0)
    
    # Render with heatmap
    frame = env.render()
    assert frame is not None
    assert frame.shape == (100, 100, 3)
    print("Heatmap render verified")
    
    print("ALL WRAPPERS PASSED")

if __name__ == "__main__":
    try:
        test_wrappers()
    except Exception as e:
        import traceback
        traceback.print_exc()
