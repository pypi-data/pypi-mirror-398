"""
VisionRL Main Package
"""
from .core.visual_env import VisualEnv
from .register import register_envs

# Auto-register environments on import
register_envs()
