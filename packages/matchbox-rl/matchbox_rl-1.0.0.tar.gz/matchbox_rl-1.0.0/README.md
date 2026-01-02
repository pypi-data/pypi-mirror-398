# Matchbox-RL

**A Tangible Reinforcement Learning Engine for Python.**

**Matchbox-RL** is a visualization-first AI library based on [Donald Michie's 1961 MENACE](https://en.wikipedia.org/wiki/Matchbox_Educable_Noughts_and_Crosses_Engine) (Machine Educatable Noughts And Crosses Engine).

It implements tabular Q-Learning using Michie's original physical metaphor: **Matchboxes** represent States, and **Colored Beads** represent Actions. This approach makes the probability distributions of the agent tangible, inspectable, and easy to visualize.

**Ideal for:**

* **Education:** Demonstrating Reinforcement Learning concepts with concrete examples.
* **Discrete Games:** Tic-Tac-Toe, Nim, Hexapawn, Grid Worlds.
* **Visualization:** Visualize the internal states of basic RL applications.

## Key Features

* **Physical Metaphor:** Operates on `Matchbox`, `Bead`, and `pick()` logic to simulate the probabilistic selection of actions.
* **Inspectable State:** Built-in `render()` method prints color-coded bead histograms to the terminal, visualizing the agent's confidence.
* **Smart Colors:** Supports standard names (`"red"`) and **Hex Codes** (`"#FF00AA"`) for TrueColor terminal visualization.
* **Configurable Learning:** Adjust initial bead counts, max beads, and reward/punishment values via `LearningConfig`.
* **Zero Dependencies:** Pure Python. Runs anywhere.

## Installation

```bash
pip install matchbox-rl
```

## Quick Start

### 1. Define your Actions as Beads

Each bead represents an action the agent can take. For Tic-Tac-Toe, each position (0-8) is a possible move.

```python
from matchbox import Engine, Bead, LearningConfig

# Define the 9 board positions as beads
beads = [
    Bead(name="Cell0", action=0, color="red"),
    Bead(name="Cell1", action=1, color="blue"),
    Bead(name="Cell2", action=2, color="green"),
    # ... cells 3-8
]
```

### 2. Create the Engine

```python
# Initialize with Michie's original MENACE settings
config = LearningConfig(
    initial_beads=4,      # Michie's original
    win_reward=3,         # +3 beads on win
    draw_reward=1,        # +1 bead on draw
    lose_punishment=1,    # -1 bead on loss
)

engine = Engine(beads=beads, config=config)
```

### 3. Play and Train

```python
# X plays corner (position 0), what should O play?
state_id = "X        "  # Board state as string

action = engine.get_move(state_id)
print(f"Agent chose: {action}")  # e.g., "Agent chose: 4" (center)

# After the game ends, reinforce the behavior
engine.train(result='win')   # +3 beads
engine.train(result='draw')  # +1 bead
engine.train(result='lose')  # -1 bead (confiscate)
```

## Visualizing the Agent

Matchbox-RL lets you view the learned policy as a physical collection of beads.

```python
# After 100,000 games of training:
print(engine.render_box("X        "))
```

**Example:**

![MENACE Tic-Tac-Toe](assets/menace_tictactoe.png)

## Configuration

Adjust the reinforcement schedule by passing a `LearningConfig` object.

```python
from matchbox import LearningConfig

config = LearningConfig(
    initial_beads=4,      # Starting beads per action
    max_beads=20,         # Cap on beads per action
    win_reward=3,         # Beads added on WIN
    draw_reward=0,        # Beads added on DRAW
    lose_punishment=1     # Beads removed on LOSS
)

engine = Engine(beads=beads, config=config)
```

## The History

In 1961, **Donald Michie**, a British AI researcher, did not have a computer powerful enough to test his theories on reinforcement learning. So, he built one out of **304 matchboxes** and thousands of colored beads.

He called it **MENACE** (Machine Educatable Noughts And Crosses Engine). He physically played Tic-Tac-Toe against it, removing beads when it lost and adding beads when it won. Over time, the pile of matchboxes learned to play a perfect game.

**Matchbox-RL** is a faithful software recreation of that physical mechanism.

## Examples

See the `examples/` directory:

- **`simple_walk.py`** - 2D Grid World with walls and treasure
- **`tic_tac_toe.py`** - Learning agent vs random opponent

```bash
python examples/simple_walk.py
python examples/tic_tac_toe.py
```

## License

MIT
