"""Matchbox-RL: A tangible Reinforcement Learning engine.

This library implements Donald Michie's MENACE algorithm using
physical metaphors - Matchboxes and colored Beads - to make
reinforcement learning transparent and debuggable.
"""
from .beads import Bead
from .box import Matchbox
from .config import LearningConfig
from .engine import Engine

__version__ = "0.1.0"
__all__ = [
    "Bead",
    "Engine",
    "LearningConfig",
    "Matchbox",
]
