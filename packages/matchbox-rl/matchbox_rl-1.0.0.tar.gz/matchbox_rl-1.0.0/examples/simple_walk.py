#!/usr/bin/env python3
"""2D Grid World (Treasure Hunt) example.

The World:
    XXXXXX
    X---TX
    X-X--X
    X-S--X
    XXXXXX

Legend:
    X = Wall (death)
    T = Treasure (win)
    S = Start position
    - = Walkable

Actions: UP, DOWN, LEFT, RIGHT

This example demonstrates how matchbox learning discovers
the optimal path to treasure while avoiding obstacles.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from matchbox import Bead, Engine, LearningConfig

# Grid layout with obstacle
GRID = [
    "XXXXXX",
    "X---TX",
    "X-X--X",
    "X-S--X",
    "XXXXXX",
]

# Find key positions
START = None
TREASURE = None
for row_idx, row in enumerate(GRID):
    for col_idx, cell in enumerate(row):
        if cell == "S":
            START = (row_idx, col_idx)
        elif cell == "T":
            TREASURE = (row_idx, col_idx)

# Movement directions
MOVES = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}


def is_wall(pos: tuple[int, int]) -> bool:
    """Check if position is a wall or out of bounds."""
    row, col = pos
    if row < 0 or row >= len(GRID) or col < 0 or col >= len(GRID[0]):
        return True
    return GRID[row][col] == "X"


def play_game(engine: Engine, training: bool = True, max_steps: int = 50) -> str:
    """Play one episode of the grid world game.

    Uses step-by-step training:
    - Each surviving move gets step_reward (+1)
    - The winning move gets win_reward (+10) bonus
    - Fatal moves get lose_punishment (-3)

    This teaches the agent that shorter paths are better.
    """
    pos = START
    steps = 0

    while steps < max_steps:
        state_id = f"{pos[0]},{pos[1]}"
        try:
            action = engine.get_move(state_id)
        except RuntimeError:
            # Matchbox empty - pick randomly
            action = random.choice(list(MOVES.keys()))
            engine.clear_history()
            delta = MOVES[action]
            new_pos = (pos[0] + delta[0], pos[1] + delta[1])
            if is_wall(new_pos):
                return "lose"
            pos = new_pos
            steps += 1
            if pos == TREASURE:
                return "win"
            continue

        # Calculate new position
        delta = MOVES[action]
        new_pos = (pos[0] + delta[0], pos[1] + delta[1])

        # Check if hit wall (death) - punish only the fatal move
        if is_wall(new_pos):
            if training:
                engine.train("lose")
            else:
                engine.clear_history()
            return "lose"

        pos = new_pos
        steps += 1

        # Check if reached treasure - big bonus for winning move!
        if pos == TREASURE:
            if training:
                engine.train("win")  # Big reward for the winning move
            else:
                engine.clear_history()
            return "win"

        # Survived this step - small reward, then continue
        if training:
            engine.train("step")

    # Timeout
    engine.clear_history()
    return "lose"


def get_grid_lines():
    """Get grid lines with colors."""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    GRAY = "\033[90m"

    lines = []
    for row in GRID:
        line = ""
        for cell in row:
            if cell == "X":
                line += f"{RED}█{RESET}"
            elif cell == "S":
                line += f"{GREEN}S{RESET}"
            elif cell == "T":
                line += f"{YELLOW}★{RESET}"
            else:
                line += f"{GRAY}·{RESET}"
        lines.append(line)
    return lines


def main():
    # Create beads for our four actions
    beads = [
        Bead("Up", "UP", "cyan"),
        Bead("Down", "DOWN", "magenta"),
        Bead("Left", "LEFT", "red"),
        Bead("Right", "RIGHT", "green"),
    ]

    # Configure learning parameters
    config = LearningConfig(
        initial_beads=25,   # High randomness = sub-50% starting win rate
        max_beads=100,      # Room to grow
        win_reward=5,       # Stronger learning signal
        lose_punishment=1,
        step_reward=0,
    )

    engine = Engine(beads=beads, config=config)

    # Training phase with fixed checkpoints
    print("Training...", end="", flush=True)
    wins = 0
    checkpoints = [500, 1000, 5000, 10000]
    episodes = checkpoints[-1]
    results = []

    for i in range(episodes):
        result = play_game(engine)
        if result == "win":
            wins += 1

        if (i + 1) in checkpoints:
            results.append(f"{i + 1:>6,}: {wins / (i + 1) * 100:>2.0f}%")

    print(" done!\n")

    # Print grid and training results side by side
    grid_lines = get_grid_lines()
    right_col = ["Training:"] + results + [""]

    for i, grid_line in enumerate(grid_lines):
        right = right_col[i] if i < len(right_col) else ""
        print(f"  {grid_line}    {right}")

    # Show compact summary
    print("\nLearned Policies:")

    key_states = [
        (START, "Start"),
        ((2, 4), "Below treasure"),
    ]

    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    arrows = {
        "UP": f"{CYAN}↑{RESET}",
        "DOWN": f"{MAGENTA}↓{RESET}",
        "LEFT": f"{RED}←{RESET}",
        "RIGHT": f"{GREEN}→{RESET}",
    }

    for pos, label in key_states:
        state_id = f"{pos[0]},{pos[1]}"
        if state_id in engine.boxes:
            policy = engine.get_policy(state_id)
            total = sum(policy.values())

            parts = []
            for action in ["UP", "DOWN", "LEFT", "RIGHT"]:
                count = policy.get(action, 0)
                pct = int(count / total * 100) if total > 0 else 0
                if pct > 50:
                    parts.append(f"{BOLD}{arrows[action]}{pct}%{RESET}")
                else:
                    parts.append(f"{arrows[action]}{pct}%")

            print(f"  {label + ':':<18} {' '.join(parts)}")

    # Show full histogram for the key learned position
    print("\nBelow Treasure Matchbox:")
    print(engine.render_box("2,4"))


if __name__ == "__main__":
    main()
