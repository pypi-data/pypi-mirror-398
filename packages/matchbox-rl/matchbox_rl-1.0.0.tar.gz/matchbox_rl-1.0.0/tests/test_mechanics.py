"""Unit tests for matchbox-rl core mechanics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from matchbox import Bead, Engine, LearningConfig, Matchbox


class TestBead:
    """Tests for the Bead class."""

    def test_bead_creation_with_named_color(self):
        bead = Bead("Test", "action", "red")
        assert bead.name == "Test"
        assert bead.action == "action"
        assert bead.color == "red"
        assert bead._ansi == "\033[91m"

    def test_bead_creation_with_hex_color(self):
        bead = Bead("Hex", "action", "#FF0000")
        assert bead.color == "#FF0000"
        assert bead._ansi == "\033[38;2;255;0;0m"

    def test_bead_creation_with_shorthand_hex(self):
        bead = Bead("Short", "action", "#F00")
        assert bead._ansi == "\033[38;2;255;0;0m"

    def test_bead_default_color(self):
        bead = Bead("Default", "action")
        assert bead.color == "white"
        assert bead._ansi == "\033[97m"

    def test_bead_is_hashable(self):
        bead = Bead("Test", "action", "red")
        d = {bead: 5}
        assert d[bead] == 5

    def test_bead_render_name_colored(self):
        bead = Bead("Blue", "action", "blue")
        rendered = bead.render_name(colored=True)
        assert "Blue" in rendered
        assert "\033[94m" in rendered
        assert "\033[0m" in rendered

    def test_bead_render_name_uncolored(self):
        bead = Bead("Blue", "action", "blue")
        rendered = bead.render_name(colored=False)
        assert rendered == "Blue"
        assert "\033[" not in rendered

    def test_bead_render_bar_colored(self):
        bead = Bead("Green", "action", "green")
        bar = bead.render_bar(5, colored=True)
        assert "█████" in bar
        assert "\033[92m" in bar

    def test_bead_render_bar_uncolored(self):
        bead = Bead("Green", "action", "green")
        bar = bead.render_bar(5, colored=False)
        assert bar == "█████"
        assert "\033[" not in bar


class TestMatchbox:
    """Tests for the Matchbox class."""

    def test_matchbox_creation(self):
        beads = [Bead("A", "a", "red"), Bead("B", "b", "blue")]
        loadout = {beads[0]: 5, beads[1]: 5}
        box = Matchbox("test_state", loadout)

        assert box.state_id == "test_state"
        assert box.total_beads() == 10

    def test_matchbox_pick_returns_bead(self):
        bead = Bead("Test", "action", "red")
        box = Matchbox("state", {bead: 10})
        picked = box.pick()

        assert picked == bead

    def test_matchbox_pick_empty_returns_none(self):
        bead = Bead("Test", "action", "red")
        box = Matchbox("state", {bead: 0})
        picked = box.pick()

        assert picked is None

    def test_matchbox_update_add(self):
        bead = Bead("Test", "action", "red")
        box = Matchbox("state", {bead: 5})
        box.update(bead, 3, max_beads=20)

        assert box.beads[bead] == 8

    def test_matchbox_update_remove(self):
        bead = Bead("Test", "action", "red")
        box = Matchbox("state", {bead: 5})
        box.update(bead, -2, max_beads=20)

        assert box.beads[bead] == 3

    def test_matchbox_update_clamps_to_zero(self):
        bead = Bead("Test", "action", "red")
        box = Matchbox("state", {bead: 5})
        box.update(bead, -10, max_beads=20)

        assert box.beads[bead] == 0

    def test_matchbox_update_clamps_to_max(self):
        bead = Bead("Test", "action", "red")
        box = Matchbox("state", {bead: 18})
        box.update(bead, 5, max_beads=20)

        assert box.beads[bead] == 20

    def test_matchbox_render(self):
        beads = [Bead("A", "a", "red"), Bead("B", "b", "blue")]
        box = Matchbox("state", {beads[0]: 10, beads[1]: 5})
        rendered = box.render()

        assert "state" in rendered
        assert "A" in rendered
        assert "B" in rendered


class TestEngine:
    """Tests for the Engine class."""

    def test_engine_creation(self):
        beads = [Bead("A", "a", "red"), Bead("B", "b", "blue")]
        engine = Engine(beads)

        assert len(engine.available_beads) == 2
        assert len(engine.boxes) == 0

    def test_engine_get_move_creates_box(self):
        beads = [Bead("A", "a", "red")]
        engine = Engine(beads)
        action = engine.get_move("new_state")

        assert "new_state" in engine.boxes
        assert action == "a"

    def test_engine_get_move_records_history(self):
        beads = [Bead("A", "a", "red")]
        engine = Engine(beads)
        engine.get_move("state")

        assert len(engine.history) == 1
        assert engine.history[0][0] == "state"

    def test_engine_train_win_adds_beads(self):
        beads = [Bead("A", "a", "red")]
        config = LearningConfig(initial_beads=5, win_reward=3)
        engine = Engine(beads, config)

        engine.get_move("state")
        bead_before = engine.boxes["state"].beads[beads[0]]
        engine.train("win")

        assert engine.boxes["state"].beads[beads[0]] == bead_before + 3
        assert len(engine.history) == 0

    def test_engine_train_lose_removes_beads(self):
        beads = [Bead("A", "a", "red")]
        config = LearningConfig(initial_beads=10, lose_punishment=2)
        engine = Engine(beads, config)

        engine.get_move("state")
        bead_before = engine.boxes["state"].beads[beads[0]]
        engine.train("lose")

        assert engine.boxes["state"].beads[beads[0]] == bead_before - 2

    def test_engine_clear_history(self):
        beads = [Bead("A", "a", "red")]
        engine = Engine(beads)
        engine.get_move("state")

        assert len(engine.history) == 1
        engine.clear_history()
        assert len(engine.history) == 0

    def test_engine_get_policy(self):
        beads = [Bead("A", "a", "red"), Bead("B", "b", "blue")]
        config = LearningConfig(initial_beads=5)
        engine = Engine(beads, config)
        engine.get_move("state")
        engine.clear_history()

        policy = engine.get_policy("state")
        assert policy["a"] == 5
        assert policy["b"] == 5

    def test_engine_get_policy_unknown_state(self):
        beads = [Bead("A", "a", "red")]
        engine = Engine(beads)

        policy = engine.get_policy("unknown")
        assert policy == {}


class TestLearningConfig:
    """Tests for the LearningConfig class."""

    def test_default_values(self):
        config = LearningConfig()

        assert config.initial_beads == 4
        assert config.max_beads == 20
        assert config.win_reward == 3
        assert config.draw_reward == 0
        assert config.lose_punishment == 1

    def test_custom_values(self):
        config = LearningConfig(
            initial_beads=10,
            max_beads=50,
            win_reward=5,
            draw_reward=1,
            lose_punishment=3,
        )

        assert config.initial_beads == 10
        assert config.max_beads == 50
        assert config.win_reward == 5
        assert config.draw_reward == 1
        assert config.lose_punishment == 3


class TestColors:
    """Tests for the colors module."""

    def test_named_colors(self):
        from matchbox import colors

        assert colors.get_ansi("red") == "\033[91m"
        assert colors.get_ansi("blue") == "\033[94m"
        assert colors.get_ansi("green") == "\033[92m"
        assert colors.get_ansi("white") == "\033[97m"

    def test_hex_colors(self):
        from matchbox import colors

        assert colors.get_ansi("#FF0000") == "\033[38;2;255;0;0m"
        assert colors.get_ansi("#00FF00") == "\033[38;2;0;255;0m"
        assert colors.get_ansi("#0000FF") == "\033[38;2;0;0;255m"

    def test_shorthand_hex(self):
        from matchbox import colors

        assert colors.get_ansi("#F00") == "\033[38;2;255;0;0m"
        assert colors.get_ansi("#0F0") == "\033[38;2;0;255;0m"

    def test_case_insensitive(self):
        from matchbox import colors

        assert colors.get_ansi("RED") == "\033[91m"
        assert colors.get_ansi("Red") == "\033[91m"
        assert colors.get_ansi("#ff0000") == "\033[38;2;255;0;0m"

    def test_fallback_to_white(self):
        from matchbox import colors

        assert colors.get_ansi("invalid") == "\033[97m"
        assert colors.get_ansi("#ZZZZZZ") == "\033[97m"
