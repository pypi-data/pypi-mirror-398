from gymnasium.envs.registration import register

def register_envs():
    register(
        id="VisualFrozenLake-v0",
        entry_point="vision_rl.envs.visual_frozenlake:VisualFrozenLake",
    )
