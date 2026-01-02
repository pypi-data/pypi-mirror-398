#!/usr/bin/env python3
"""MENACE Tic-Tac-Toe - A recreation of Donald Michie's 1961 experiment.

MENACE (Machine Educable Noughts And Crosses Engine) was a mechanical
computer made of 304 matchboxes and colored beads that learned to play
tic-tac-toe through reinforcement learning.

This example trains a MENACE-style agent (O) against a random opponent (X).
Original rules: +3 beads for win, +1 for draw, -1 for loss (confiscate bead).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from matchbox import Bead, Engine, LearningConfig


# Colors for the 9 board positions
POSITION_COLORS = [
    "red",
    "blue",
    "green",
    "yellow",
    "magenta",
    "cyan",
    "orange",
    "pink",
    "gray",
]


class TicTacToe:
    """Simple Tic-Tac-Toe game implementation."""

    def __init__(self):
        self.board = [" "] * 9
        self.current_player = "X"

    def get_state(self) -> str:
        """Return the board as a string state ID."""
        return "".join(self.board)

    def empty_cells(self) -> list[int]:
        """Return list of empty cell indices."""
        return [i for i, cell in enumerate(self.board) if cell == " "]

    def make_move(self, position: int) -> bool:
        """Make a move at the given position. Returns True if valid."""
        if self.board[position] != " ":
            return False
        self.board[position] = self.current_player
        self.current_player = "O" if self.current_player == "X" else "X"
        return True

    def check_winner(self) -> str | None:
        """Return 'X', 'O', 'draw', or None if game continues."""
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6],  # Diagonals
        ]

        for line in lines:
            if self.board[line[0]] == self.board[line[1]] == self.board[line[2]] != " ":
                return self.board[line[0]]

        if " " not in self.board:
            return "draw"

        return None

    def render(self) -> str:
        """Return a string representation of the board."""
        rows = []
        for i in range(0, 9, 3):
            row = " | ".join(self.board[i : i + 3])
            rows.append(f" {row} ")
        return "\n-----------\n".join(rows)


def create_agent() -> Engine:
    """Create a matchbox agent for tic-tac-toe.

    Each bead color represents a board position (0-8).
    """
    # Create 9 beads for the 9 board positions
    beads = [
        Bead(f"Cell{i}", i, POSITION_COLORS[i])
        for i in range(9)
    ]

    config = LearningConfig(
        initial_beads=4,      # Michie's original
        max_beads=100,
        win_reward=3,         # Original: add 3 beads
        draw_reward=1,        # Original: add 1 bead
        lose_punishment=1,    # Original: confiscate played bead
    )

    return Engine(beads=beads, config=config)


def play_game(agent_o: Engine, training: bool = True) -> str:
    """Play one game: random X vs learning O.

    Args:
        agent_o: Engine controlling O (the learning agent).
        training: Whether to update agent_o after the game.

    Returns:
        The game result: 'X', 'O', or 'draw'.
    """
    game = TicTacToe()

    while True:
        current = game.current_player

        if current == "X":
            # X plays randomly
            action = random.choice(game.empty_cells())
        else:
            # O uses matchbox learning
            state = game.get_state()
            while True:
                try:
                    action = agent_o.get_move(state)
                except RuntimeError:
                    # Matchbox empty - Loss for O (MENACE resigns)
                    agent_o.clear_history()
                    return "X"
                if action in game.empty_cells():
                    break
                # Invalid move - remove beads and try again
                bead = [b for b in agent_o.available_beads if b.action == action][0]
                agent_o.boxes[state].update(bead, -1, agent_o.config.max_beads)
                agent_o.history.pop()

        game.make_move(action)
        winner = game.check_winner()

        if winner:
            break

    # Apply training to O only
    if training:
        if winner == "O":
            agent_o.train("win")
        elif winner == "X":
            agent_o.train("lose")
        else:
            agent_o.train("draw")
    else:
        agent_o.clear_history()

    return winner


def main():
    agent_o = create_agent()

    # Training phase
    print("Training...", end="", flush=True)
    checkpoints = [10, 100, 1000, 10000, 100000]
    episodes = checkpoints[-1]
    results = {"X": 0, "O": 0, "draw": 0}
    progress = []

    for i in range(episodes):
        winner = play_game(agent_o)
        results[winner] += 1

        if (i + 1) in checkpoints:
            n = i + 1
            x_pct = results["X"] / n * 100
            o_pct = results["O"] / n * 100
            d_pct = results["draw"] / n * 100
            progress.append(f"{n:>9,}: X{x_pct:.0f}% O{o_pct:.0f}% D{d_pct:.0f}%")

    print(" done!\n")

    # Print board positions and training results side by side
    print("MENACE: Random X vs Learning O\n")

    board_lines = [
        "Board positions:",
        "  0 | 1 | 2",
        "  ---------",
        "  3 | 4 | 5",
        "  ---------",
        "  6 | 7 | 8",
    ]

    right_col = ["Training:"] + progress

    for i, left in enumerate(board_lines):
        right = right_col[i] if i < len(right_col) else ""
        print(f"  {left:<16}  {right}")

    # Show learned policy for X plays position 0
    print("\nX plays 0, MENACE responds:")
    corner_state = "X        "
    if corner_state in agent_o.boxes:
        print(agent_o.render_box(corner_state))
    else:
        print("(matchbox depleted)")


if __name__ == "__main__":
    main()
