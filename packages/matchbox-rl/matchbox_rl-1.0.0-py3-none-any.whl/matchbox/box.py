"""Matchbox class for state representation and visualization."""
import random
from typing import Optional

from .beads import Bead


class Matchbox:
    """A matchbox containing beads that represent action probabilities.

    Each matchbox corresponds to a game state. The beads inside represent
    the learned probabilities for each possible action.
    """

    def __init__(self, state_id: str, initial_loadout: dict[Bead, int]) -> None:
        """Initialize a matchbox with the given state ID and bead counts.

        Args:
            state_id: Identifier for the game state this matchbox represents.
            initial_loadout: Dictionary mapping beads to their initial counts.
        """
        self.state_id = state_id
        self.beads: dict[Bead, int] = initial_loadout.copy()

    def pick(self) -> Optional[Bead]:
        """Pick a random bead weighted by count.

        Returns:
            The selected bead, or None if the matchbox is empty.
        """
        population = []
        for bead, count in self.beads.items():
            population.extend([bead] * count)

        if not population:
            return None
        return random.choice(population)

    def update(self, bead: Bead, change: int, max_beads: int = 20) -> None:
        """Update the count of a specific bead.

        Args:
            bead: The bead to update.
            change: Amount to add (positive) or remove (negative).
            max_beads: Maximum allowed beads per action.
        """
        if bead in self.beads:
            new_count = self.beads[bead] + change
            self.beads[bead] = max(0, min(new_count, max_beads))

    def total_beads(self) -> int:
        """Return the total number of beads in the matchbox."""
        return sum(self.beads.values())

    def render(self) -> str:
        """Generate a CLI histogram of the matchbox contents.

        Returns:
            A formatted string showing bead distributions with ANSI colors.
        """
        total = self.total_beads()
        if total == 0:
            return f"Matchbox [{self.state_id}] (EMPTY)"

        items = sorted(self.beads.items(), key=lambda x: x[1], reverse=True)

        lines = [f"Matchbox ID: {self.state_id}"]
        lines.append("-" * 40)

        for bead, count in items:
            percent = (count / total) * 100
            bar = bead.render_bar(count)
            name = bead.render_name()
            lines.append(f" {name:<15} | {bar} ({count}) {percent:.1f}%")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Matchbox(state_id={self.state_id!r}, beads={len(self.beads)})"
