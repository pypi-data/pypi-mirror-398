"""Internal color utilities for matchbox-rl.

Handles conversion from standard names and hex codes to ANSI escape sequences.
"""


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert a hex string (e.g., '#FF00AA') to an (r, g, b) tuple."""
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def get_ansi(value: str) -> str:
    """Parse a color string (name or hex) and return the ANSI escape code.

    Supports:
    - Standard names: "red", "blue", "cyan", "white", etc.
    - Hex codes: "#FF0000", "#00FF00" (requires TrueColor terminal support).

    Args:
        value: A color name or hex code string.

    Returns:
        ANSI escape sequence for the color.
    """
    value = value.lower().strip()

    # 1. Standard Names
    #    Mapped to high-intensity ANSI colors for better visibility.
    standard_map = {
        # High-intensity ANSI colors
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "grey": "\033[90m",
        "gray": "\033[90m",
        "black": "\033[30m",
        "reset": "\033[0m",
        "orange": "\033[38;2;255;165;0m",
        "pink": "\033[38;2;255;105;180m",
        "purple": "\033[38;2;128;0;128m",
        "lime": "\033[38;2;50;205;50m",
        "teal": "\033[38;2;0;128;128m",
        "brown": "\033[38;2;139;69;19m",
        "coral": "\033[38;2;255;127;80m",
        "gold": "\033[38;2;255;215;0m",
    }

    if value in standard_map:
        return standard_map[value]

    # 2. Hex Codes (TrueColor support)
    #    Format: \033[38;2;R;G;Bm
    if value.startswith("#") and len(value) in [4, 7]:
        try:
            # Handle shorthand #F00 -> #FF0000
            if len(value) == 4:
                value = f"#{value[1]*2}{value[2]*2}{value[3]*2}"

            r, g, b = hex_to_rgb(value)
            return f"\033[38;2;{r};{g};{b}m"
        except ValueError:
            pass  # Fall through to default

    # 3. Fallback
    return standard_map["white"]


# Constant for resetting color
RESET = "\033[0m"
