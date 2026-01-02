"""Learning configuration for the matchbox engine."""
from dataclasses import dataclass


@dataclass
class LearningConfig:
    """Hyperparameters for matchbox learning.

    Attributes:
        initial_beads: Number of beads to start with for each action in a new matchbox.
        max_beads: Maximum beads allowed per action (prevents runaway growth).
        win_reward: Beads to add for a winning action.
        draw_reward: Beads to add/remove for a draw (can be negative).
        lose_punishment: Beads to remove for a losing action.
        step_reward: Beads to add for surviving a step (useful for grid worlds).
    """

    initial_beads: int = 4
    max_beads: int = 20
    win_reward: int = 3
    draw_reward: int = 0
    lose_punishment: int = 1
    step_reward: int = 0
