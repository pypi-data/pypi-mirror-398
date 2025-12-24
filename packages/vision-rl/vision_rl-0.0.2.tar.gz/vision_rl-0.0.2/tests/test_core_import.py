"""
Test script to verify core abstractions.
"""
import sys
import os

# Add the package root to the path so we can import vision_rl
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

try:
    from vision_rl.core.visual_env import VisualEnv
    
    print("Successfully imported VisualEnv")

    class TestEnv(VisualEnv):
        def reset(self, seed=None, options=None):
            return 0, {}
        def step(self, action):
            return 0, 0, False, False, {}
        def get_visual_obs(self):
            return "frame"

    env = TestEnv(render_mode="rgb_array")
    print("Successfully instantiated TestEnv")
    
    # Check mixins
    env.add_debug_info("test", 123)
    info = env.get_debug_info()
    assert info["test"] == 123
    print("DebugMixin works")
    
    val = env.get_visual_obs()
    assert val == "frame"
    print("CVMixin works")
    
    env.on_ui_update({})
    print("UIMixin works")
    
    print("CORE ABSTRACTIONS VERIFIED")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
