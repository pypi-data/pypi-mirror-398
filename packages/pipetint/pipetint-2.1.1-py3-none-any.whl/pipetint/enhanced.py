"""
Enhanced colorization API with production-safe, high-usability patterns.

This module provides multiple intuitive interfaces for text colorization:
1. Factory functions: colored(), txt()
2. Global convenience object: C
3. Enhanced ColorString class with operator overloading
4. Full backward compatibility with existing API
"""

import re
from typing import Callable, Optional, Union

from .color_codes import ColorCode, ColorManager, color_manager
from .colors import ColorType
from .core import Colorize, ColorizedString, colorize


class ColorString(str):  # noqa: PLR0904
    """
    Production-safe string subclass with fluent colorization interface.

    Supports method chaining and operator overloading for intuitive usage:
    - ColorString("hello").red().bold()
    - ColorString("world") | BLUE | UNDERLINE
    - ColorString("test") >> GREEN >> BG_YELLOW
    """

    def __new__(cls, value=""):
        return str.__new__(cls, value)

    def __init__(self, value=""):  # noqa: ARG002
        super().__init__()
        self._colorizer = Colorize()

    # === Core colorization methods ===

    def colorize(self, color_code: Union[str, ColorCode]) -> "ColorString":
        """Apply color to the string."""
        result = self._colorizer.colorize(str(self), color_code)
        return ColorString(result)

    def colorize_random(self, code: Optional[int] = None) -> "ColorString":
        """Apply random color to the string."""
        result = self._colorizer.colorize_random(str(self), code)
        return ColorString(result)

    def remove_color(self) -> "ColorString":
        """Remove ANSI color codes from the string."""
        result = self._colorizer.remove_color(str(self))
        return ColorString(result)

    # === Advanced highlighting ===

    def highlight(
        self, pattern: Union[str, re.Pattern], colors: Union[str, list[str]]
    ) -> "ColorString":
        """Highlight text matching pattern with given colors."""
        colored_str = ColorizedString(str(self))
        result = colored_str.highlight(pattern, colors)
        return ColorString(str(result))

    def highlight_at(
        self, positions: list[int], color: str = "fg_yellow"
    ) -> "ColorString":
        """Highlight characters at specific positions."""
        colored_str = ColorizedString(str(self))
        result = colored_str.highlight_at(positions, color)
        return ColorString(str(result))

    # === Operator overloading for chaining ===

    def __or__(self, color: ColorType) -> "ColorString":
        """Chain colors using | operator: text | RED | BOLD"""
        return self.colorize(color)

    def __rshift__(self, color: ColorType) -> "ColorString":
        """Chain colors using >> operator: text >> RED >> BOLD"""
        return self.colorize(color)

    # === Foreground colors ===

    def black(self) -> "ColorString":
        return self.colorize("fg_black")

    def red(self) -> "ColorString":
        return self.colorize("fg_red")

    def green(self) -> "ColorString":
        return self.colorize("fg_green")

    def yellow(self) -> "ColorString":
        return self.colorize("fg_yellow")

    def blue(self) -> "ColorString":
        return self.colorize("fg_blue")

    def magenta(self) -> "ColorString":
        return self.colorize("fg_magenta")

    def cyan(self) -> "ColorString":
        return self.colorize("fg_cyan")

    def white(self) -> "ColorString":
        return self.colorize("fg_white")

    def lightgray(self) -> "ColorString":
        return self.colorize("fg_lightgray")

    def darkgray(self) -> "ColorString":
        return self.colorize("fg_darkgray")

    def lightred(self) -> "ColorString":
        return self.colorize("fg_lightred")

    def lightgreen(self) -> "ColorString":
        return self.colorize("fg_lightgreen")

    def lightyellow(self) -> "ColorString":
        return self.colorize("fg_lightyellow")

    def lightblue(self) -> "ColorString":
        return self.colorize("fg_lightblue")

    def lightmagenta(self) -> "ColorString":
        return self.colorize("fg_lightmagenta")

    def lightcyan(self) -> "ColorString":
        return self.colorize("fg_lightcyan")

    # === Background colors ===

    def bg_black(self) -> "ColorString":
        return self.colorize("bg_black")

    def bg_red(self) -> "ColorString":
        return self.colorize("bg_red")

    def bg_green(self) -> "ColorString":
        return self.colorize("bg_green")

    def bg_yellow(self) -> "ColorString":
        return self.colorize("bg_yellow")

    def bg_blue(self) -> "ColorString":
        return self.colorize("bg_blue")

    def bg_magenta(self) -> "ColorString":
        return self.colorize("bg_magenta")

    def bg_cyan(self) -> "ColorString":
        return self.colorize("bg_cyan")

    def bg_white(self) -> "ColorString":
        return self.colorize("bg_white")

    def bg_lightgray(self) -> "ColorString":
        return self.colorize("bg_lightgray")

    def bg_darkgray(self) -> "ColorString":
        return self.colorize("bg_darkgray")

    def bg_lightred(self) -> "ColorString":
        return self.colorize("bg_lightred")

    def bg_lightgreen(self) -> "ColorString":
        return self.colorize("bg_lightgreen")

    def bg_lightyellow(self) -> "ColorString":
        return self.colorize("bg_lightyellow")

    def bg_lightblue(self) -> "ColorString":
        return self.colorize("bg_lightblue")

    def bg_lightmagenta(self) -> "ColorString":
        return self.colorize("bg_lightmagenta")

    def bg_lightcyan(self) -> "ColorString":
        return self.colorize("bg_lightcyan")

    # === Text styles ===

    def bright(self) -> "ColorString":
        return self.colorize("bright")

    def bold(self) -> "ColorString":
        return self.colorize("bright")  # Alias for bright

    def dim(self) -> "ColorString":
        return self.colorize("dim")

    def underline(self) -> "ColorString":
        return self.colorize("underline")

    def blink(self) -> "ColorString":
        return self.colorize("blink")

    def invert(self) -> "ColorString":
        return self.colorize("invert")

    def swapcolor(self) -> "ColorString":
        return self.colorize("swapcolor")

    def hidden(self) -> "ColorString":
        return self.colorize("hidden")

    def strikethrough(self) -> "ColorString":
        return self.colorize("strikethrough")


class ColorContext:
    """
    Global convenience object for colorization.

    Supports multiple usage patterns:
    - C.red("hello")              # Direct color application
    - C("hello").red()            # Factory function with chaining
    - C("hello", RED)           # Direct colorization
    """

    def __init__(self):
        self._colorizer = Colorize()

    def __call__(
        self, text: str, color: Optional[str] = None
    ) -> Union[str, ColorString]:
        """
        Dual-purpose call interface.

        Args:
            text: Text to colorize
            color: Optional color name. If provided, returns colored string.
                  If None, returns ColorString for chaining.

        Returns:
            str if color provided, ColorString if color is None
        """
        if color is None:
            return ColorString(text)
        return self._colorizer.colorize(text, color)

    def __getattr__(self, color: str) -> Callable[[str], str]:
        """
        Dynamic color methods.

        Usage: C.red("hello") -> returns colored string
        """

        def color_func(text: str) -> str:
            return self._colorizer.colorize(text, color)

        # Add docstring for better IDE support
        color_func.__doc__ = f"Colorize text with {color} color"
        color_func.__name__ = color

        return color_func


# === Factory functions ===


def colored(text: str) -> ColorString:
    """
    Create a ColorString for fluent colorization.

    Args:
        text: Text to make colorizable

    Returns:
        ColorString instance that supports chaining

    Examples:
        colored("hello").red().bold()
        colored("world") | BLUE | UNDERLINE
    """
    return ColorString(text)


def txt(text: str) -> ColorString:
    """
    Short alias for colored().

    Args:
        text: Text to make colorizable

    Returns:
        ColorString instance that supports chaining

    Examples:
        txt("hello").red().bold()
        txt("world") | BLUE | UNDERLINE
    """
    return ColorString(text)


# === Global convenience object ===

C = ColorContext()  # Global colorization object with multiple interfaces


# === Exports ===

__all__ = [
    # Enhanced API
    "C",
    # Backward compatibility
    "ColorCode",
    "ColorContext",
    "ColorManager",
    "ColorString",
    "Colorize",
    "ColorizedString",
    "color_manager",
    "colored",
    "colorize",
    "txt",
]
