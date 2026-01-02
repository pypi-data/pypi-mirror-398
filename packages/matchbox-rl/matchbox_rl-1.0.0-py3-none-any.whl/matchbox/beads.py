"""Bead class for tangible reinforcement learning."""
from dataclasses import dataclass, field
from typing import Any

from . import colors


@dataclass(frozen=True)
class Bead:
    """A physical bead representing an action.

    Args:
        name: The display name (e.g., "Attack").
        action: The game action (e.g., 1, "atk", function).
        color: A standard name ("red") or Hex code ("#FF5500").
        symbol: The character used in CLI graphs (default: "●").
    """

    name: str
    action: Any
    color: str = "white"
    symbol: str = "●"

    # Internal ANSI code (derived automatically in post_init)
    _ansi: str = field(init=False, repr=False)

    def __post_init__(self):
        """Resolve the color string to an ANSI code immediately."""
        ansi_code = colors.get_ansi(self.color)
        # Bypass frozen constraint to set the derived attribute
        object.__setattr__(self, "_ansi", ansi_code)

    def render_name(self, colored: bool = True) -> str:
        """Return the bead name, optionally wrapped in ANSI color codes."""
        if colored:
            return f"{self._ansi}{self.name}{colors.RESET}"
        return self.name

    def render_bar(self, count: int, colored: bool = True) -> str:
        """Return a bar of beads (e.g., "●●●●") in the bead's color."""
        block = "●" * count
        if colored:
            return f"{self._ansi}{block}{colors.RESET}"
        return block
