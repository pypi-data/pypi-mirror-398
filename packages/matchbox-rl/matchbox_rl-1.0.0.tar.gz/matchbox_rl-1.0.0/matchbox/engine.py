"""Main Engine API for matchbox reinforcement learning."""
from typing import Any

from .beads import Bead
from .box import Matchbox
from .config import LearningConfig


class Engine:
    """The main coordinator for matchbox-based reinforcement learning.

    Manages a collection of matchboxes (one per state) and handles
    action selection and learning updates.
    """

    def __init__(
        self,
        beads: list[Bead],
        config: LearningConfig | None = None,
    ) -> None:
        """Initialize the engine with available beads and learning config.

        Args:
            beads: List of beads representing possible actions.
            config: Learning hyperparameters. Uses defaults if not provided.
        """
        self.available_beads = beads
        self.config = config or LearningConfig()
        self.boxes: dict[str, Matchbox] = {}
        self.history: list[tuple[str, Bead]] = []

    def get_move(self, state_id: str) -> Any:
        """Select an action for the given state.

        Creates a new matchbox if this state hasn't been seen before.
        Records the state-action pair in history for later training.

        Args:
            state_id: String identifier for the current game state.

        Returns:
            The action associated with the selected bead.

        Raises:
            RuntimeError: If the matchbox is empty (agent resigns).
        """
        if state_id not in self.boxes:
            self._init_box(state_id)

        box = self.boxes[state_id]
        bead = box.pick()

        if bead is None:
            raise RuntimeError("Matchbox is empty")

        self.history.append((state_id, bead))
        return bead.action

    def train(self, result: str) -> None:
        """Apply rewards or penalties based on the game result.

        Updates all matchboxes visited during this episode, then clears history.

        Args:
            result: One of 'win', 'draw', 'lose', or 'step'.
        """
        rewards = {
            "win": self.config.win_reward,
            "draw": self.config.draw_reward,
            "lose": -self.config.lose_punishment,
            "step": self.config.step_reward,
        }
        change = rewards.get(result, 0)

        for state_id, bead in self.history:
            self.boxes[state_id].update(bead, change, self.config.max_beads)

        self.history = []

    def clear_history(self) -> None:
        """Clear the move history without applying any training."""
        self.history = []

    def get_policy(self, state_id: str) -> dict[Any, int]:
        """Return the current bead counts for a state.

        Args:
            state_id: The state to inspect.

        Returns:
            Dictionary mapping actions to bead counts.
        """
        if state_id not in self.boxes:
            return {}
        return {bead.action: count for bead, count in self.boxes[state_id].beads.items()}

    def render_box(self, state_id: str) -> str:
        """Render the matchbox for a given state.

        Args:
            state_id: The state to render.

        Returns:
            Formatted string representation of the matchbox.
        """
        if state_id not in self.boxes:
            return f"No matchbox for state: {state_id}"
        return self.boxes[state_id].render()

    def _init_box(self, state_id: str) -> None:
        """Initialize a new matchbox for a state.

        Args:
            state_id: The state identifier.
        """
        loadout = {bead: self.config.initial_beads for bead in self.available_beads}
        self.boxes[state_id] = Matchbox(state_id, loadout)

    def __repr__(self) -> str:
        return f"Engine(beads={len(self.available_beads)}, boxes={len(self.boxes)})"
