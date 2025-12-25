"""
ANSI color codes and color management functionality.
"""

import random
from enum import IntEnum
from typing import Optional


class ColorCode(IntEnum):
    """ANSI color codes enum."""

    # Control codes
    NO_COLOR = 0
    RESET = 0
    BRIGHT = 1
    DIM = 2
    UNDERLINE = 4
    BLINK = 5
    SWAPCOLOR = 7
    INVERT = 7
    HIDDEN = 8
    STRIKETHROUGH = 9

    # Foreground colors
    FG_BLACK = 30
    FG_RED = 31
    FG_GREEN = 32
    FG_YELLOW = 33
    FG_BLUE = 34
    FG_MAGENTA = 35
    FG_CYAN = 36
    FG_LIGHTGRAY = 37
    FG_DEFAULT = 39

    # Bright foreground colors
    FG_DARKGRAY = 90
    FG_LIGHTRED = 91
    FG_LIGHTGREEN = 92
    FG_LIGHTYELLOW = 93
    FG_LIGHTBLUE = 94
    FG_LIGHTMAGENTA = 95
    FG_LIGHTCYAN = 96
    FG_WHITE = 97

    # Background colors
    BG_BLACK = 40
    BG_RED = 41
    BG_GREEN = 42
    BG_YELLOW = 43
    BG_BLUE = 44
    BG_MAGENTA = 45
    BG_CYAN = 46
    BG_LIGHTGRAY = 47
    BG_DEFAULT = 49

    # Bright background colors
    BG_DARKGRAY = 100
    BG_LIGHTRED = 101
    BG_LIGHTGREEN = 102
    BG_LIGHTYELLOW = 103
    BG_LIGHTBLUE = 104
    BG_LIGHTMAGENTA = 105
    BG_LIGHTCYAN = 106
    BG_WHITE = 107


class ColorManager:
    """Manages ANSI color codes and provides color functionality."""

    def __init__(self) -> None:
        self._color_map = self._build_color_map()

    def _build_color_map(self) -> dict[str, ColorCode]:
        """Build a mapping of color names to color codes."""
        color_map = {}

        # Add all enum values by name
        for color_code in ColorCode:
            name = color_code.name.lower()
            color_map[name] = color_code

            # Add aliases without fg_ prefix (e.g., 'red' for 'fg_red')
            if name.startswith("fg_"):
                alias = name[3:]  # Remove 'fg_' prefix
                color_map[alias] = color_code

            # Add color_bg aliases for bg_color format (e.g., 'red_bg' for 'bg_red')
            if name.startswith("bg_"):
                color_part = name[3:]  # Remove 'bg_' prefix
                alias = f"{color_part}_bg"  # Create 'red_bg' format
                color_map[alias] = color_code

        # Add common attribute aliases
        color_map["bold"] = ColorCode.BRIGHT
        color_map["inverse"] = ColorCode.INVERT
        color_map["reverse"] = ColorCode.INVERT
        color_map["swap"] = ColorCode.SWAPCOLOR
        color_map["strike"] = ColorCode.STRIKETHROUGH

        return color_map

    def get_color_code(self, name: str) -> Optional[ColorCode]:
        """Get color code by name."""
        return self._color_map.get(name.lower())

    def start_color(self, color_code: ColorCode) -> str:
        """Generate ANSI escape sequence for color start."""
        return f"\033[{color_code.value}m"

    def end_color(self) -> str:
        """Generate ANSI escape sequence for color reset."""
        return f"\033[{ColorCode.RESET.value}m"

    def colorize(self, text: str, color_code: ColorCode) -> str:
        """Apply color to text."""
        return f"{self.start_color(color_code)}{text}{self.end_color()}"

    def get_foreground_colors(self) -> dict[str, ColorCode]:
        """Get all foreground color codes."""
        return {
            name: code
            for name, code in self._color_map.items()
            if name.startswith("fg_") and name not in ("fg_black", "fg_darkgray")
        }

    def get_background_colors(self) -> dict[str, ColorCode]:
        """Get all background color codes."""
        return {
            name: code
            for name, code in self._color_map.items()
            if name.startswith("bg_")
        }

    def get_all_colors(self) -> dict[str, ColorCode]:
        """Get all color codes."""
        fg_colors = self.get_foreground_colors()
        bg_colors = self.get_background_colors()
        return {**fg_colors, **bg_colors}

    def generate_random_color(self, code: Optional[int] = None) -> ColorCode:
        """Generate a random color code."""
        if code is not None:
            all_colors = list(self.get_all_colors().values())
            index = code % len(all_colors)
            return all_colors[index]
        # Use predefined set of nice colors for random selection
        nice_colors = [
            ColorCode.FG_LIGHTRED,
            ColorCode.FG_GREEN,
            ColorCode.FG_BLUE,
            ColorCode.FG_MAGENTA,
            ColorCode.FG_CYAN,
            ColorCode.FG_DARKGRAY,
            ColorCode.FG_LIGHTGREEN,
            ColorCode.FG_LIGHTYELLOW,
            ColorCode.FG_LIGHTBLUE,
            ColorCode.FG_LIGHTMAGENTA,
        ]
        return random.choice(nice_colors)

    def remove_color(self, text: str) -> str:
        """Remove ANSI color codes from text."""
        import re

        # Pattern to match ANSI escape sequences
        ansi_pattern = (
            r"\x1B\[([0-9]{1,3}(;[0-9]{1,3}(;[0-9]{1,3}(;[0-9]{1,3})?)?)?)?[m|K]"
        )
        return re.sub(ansi_pattern, "", str(text))

    def get_color_names(self) -> list[str]:
        """Get all available color names."""
        return list(self._color_map.keys())


# Global color manager instance
color_manager = ColorManager()
