"""
Type-safe color constants for enhanced API.

Provides constants that can be used with the enhanced colorization API:
    colored("Error") | RED | BRIGHT | BG_WHITE
    txt("Success") >> GREEN >> BOLD

This enables proper type checking and IDE autocompletion.
"""

from typing import Literal, Union

# Foreground colors
RED: Literal["fg_red"] = "fg_red"
GREEN: Literal["fg_green"] = "fg_green"
BLUE: Literal["fg_blue"] = "fg_blue"
YELLOW: Literal["fg_yellow"] = "fg_yellow"
MAGENTA: Literal["fg_magenta"] = "fg_magenta"
CYAN: Literal["fg_cyan"] = "fg_cyan"
WHITE: Literal["fg_white"] = "fg_white"
BLACK: Literal["fg_black"] = "fg_black"

# Light foreground colors
LIGHTRED: Literal["fg_lightred"] = "fg_lightred"
LIGHTGREEN: Literal["fg_lightgreen"] = "fg_lightgreen"
LIGHTBLUE: Literal["fg_lightblue"] = "fg_lightblue"
LIGHTYELLOW: Literal["fg_lightyellow"] = "fg_lightyellow"
LIGHTMAGENTA: Literal["fg_lightmagenta"] = "fg_lightmagenta"
LIGHTCYAN: Literal["fg_lightcyan"] = "fg_lightcyan"
LIGHTGRAY: Literal["fg_lightgray"] = "fg_lightgray"
DARKGRAY: Literal["fg_darkgray"] = "fg_darkgray"

# Background colors
BG_RED: Literal["bg_red"] = "bg_red"
BG_GREEN: Literal["bg_green"] = "bg_green"
BG_BLUE: Literal["bg_blue"] = "bg_blue"
BG_YELLOW: Literal["bg_yellow"] = "bg_yellow"
BG_MAGENTA: Literal["bg_magenta"] = "bg_magenta"
BG_CYAN: Literal["bg_cyan"] = "bg_cyan"
BG_WHITE: Literal["bg_white"] = "bg_white"
BG_BLACK: Literal["bg_black"] = "bg_black"

# Light background colors
BG_LIGHTRED: Literal["bg_lightred"] = "bg_lightred"
BG_LIGHTGREEN: Literal["bg_lightgreen"] = "bg_lightgreen"
BG_LIGHTBLUE: Literal["bg_lightblue"] = "bg_lightblue"
BG_LIGHTYELLOW: Literal["bg_lightyellow"] = "bg_lightyellow"
BG_LIGHTMAGENTA: Literal["bg_lightmagenta"] = "bg_lightmagenta"
BG_LIGHTCYAN: Literal["bg_lightcyan"] = "bg_lightcyan"
BG_LIGHTGRAY: Literal["bg_lightgray"] = "bg_lightgray"
BG_DARKGRAY: Literal["bg_darkgray"] = "bg_darkgray"

# Text styles
BRIGHT: Literal["bright"] = "bright"
BOLD: Literal["bright"] = "bright"  # Alias for bright
DIM: Literal["dim"] = "dim"
UNDERLINE: Literal["underline"] = "underline"
BLINK: Literal["blink"] = "blink"
INVERT: Literal["invert"] = "invert"
SWAPCOLOR: Literal["swapcolor"] = "swapcolor"
HIDDEN: Literal["hidden"] = "hidden"
STRIKETHROUGH: Literal["strikethrough"] = "strikethrough"

# Convenience collections
FOREGROUND_COLORS = [
    RED,
    GREEN,
    BLUE,
    YELLOW,
    MAGENTA,
    CYAN,
    WHITE,
    BLACK,
    LIGHTRED,
    LIGHTGREEN,
    LIGHTBLUE,
    LIGHTYELLOW,
    LIGHTMAGENTA,
    LIGHTCYAN,
    LIGHTGRAY,
    DARKGRAY,
]

BACKGROUND_COLORS = [
    BG_RED,
    BG_GREEN,
    BG_BLUE,
    BG_YELLOW,
    BG_MAGENTA,
    BG_CYAN,
    BG_WHITE,
    BG_BLACK,
    BG_LIGHTRED,
    BG_LIGHTGREEN,
    BG_LIGHTBLUE,
    BG_LIGHTYELLOW,
    BG_LIGHTMAGENTA,
    BG_LIGHTCYAN,
    BG_LIGHTGRAY,
    BG_DARKGRAY,
]

STYLES = [BRIGHT, BOLD, DIM, UNDERLINE, BLINK, INVERT, SWAPCOLOR, HIDDEN, STRIKETHROUGH]

ALL_COLORS = FOREGROUND_COLORS + BACKGROUND_COLORS + STYLES

# Type alias for all valid color strings
ColorType = Union[
    # Foreground colors
    Literal["fg_red"],
    Literal["fg_green"],
    Literal["fg_blue"],
    Literal["fg_yellow"],
    Literal["fg_magenta"],
    Literal["fg_cyan"],
    Literal["fg_white"],
    Literal["fg_black"],
    Literal["fg_lightred"],
    Literal["fg_lightgreen"],
    Literal["fg_lightblue"],
    Literal["fg_lightyellow"],
    Literal["fg_lightmagenta"],
    Literal["fg_lightcyan"],
    Literal["fg_lightgray"],
    Literal["fg_darkgray"],
    # Background colors
    Literal["bg_red"],
    Literal["bg_green"],
    Literal["bg_blue"],
    Literal["bg_yellow"],
    Literal["bg_magenta"],
    Literal["bg_cyan"],
    Literal["bg_white"],
    Literal["bg_black"],
    Literal["bg_lightred"],
    Literal["bg_lightgreen"],
    Literal["bg_lightblue"],
    Literal["bg_lightyellow"],
    Literal["bg_lightmagenta"],
    Literal["bg_lightcyan"],
    Literal["bg_lightgray"],
    Literal["bg_darkgray"],
    # Text styles
    Literal["bright"],
    Literal["dim"],
    Literal["underline"],
    Literal["blink"],
    Literal["invert"],
    Literal["swapcolor"],
    Literal["hidden"],
    Literal["strikethrough"],
    # Legacy compatibility
    str,
]

__all__ = [
    "ALL_COLORS",
    "BACKGROUND_COLORS",
    "BG_BLACK",
    "BG_BLUE",
    "BG_CYAN",
    "BG_DARKGRAY",
    "BG_GREEN",
    "BG_LIGHTBLUE",
    "BG_LIGHTCYAN",
    "BG_LIGHTGRAY",
    "BG_LIGHTGREEN",
    "BG_LIGHTMAGENTA",
    "BG_LIGHTRED",
    "BG_LIGHTYELLOW",
    "BG_MAGENTA",
    # Background colors
    "BG_RED",
    "BG_WHITE",
    "BG_YELLOW",
    "BLACK",
    "BLINK",
    "BLUE",
    "BOLD",
    # Text styles
    "BRIGHT",
    "CYAN",
    "DARKGRAY",
    "DIM",
    # Collections
    "FOREGROUND_COLORS",
    "GREEN",
    "HIDDEN",
    "INVERT",
    "LIGHTBLUE",
    "LIGHTCYAN",
    "LIGHTGRAY",
    "LIGHTGREEN",
    "LIGHTMAGENTA",
    "LIGHTRED",
    "LIGHTYELLOW",
    "MAGENTA",
    # Foreground colors
    "RED",
    "STRIKETHROUGH",
    "STYLES",
    "SWAPCOLOR",
    "UNDERLINE",
    "WHITE",
    "YELLOW",
    # Type alias
    "ColorType",
]
