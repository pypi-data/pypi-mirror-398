"""
Core colorization functionality with deferred rendering and proper color nesting.
"""

import re
import warnings
from dataclasses import dataclass
from typing import Any, Optional, Union

# sre_parse is deprecated in Python 3.11+ but no stable public alternative exists.
# We suppress the warning since this is the only way to properly parse regex AST.
# Future migration path: consider third-party regex parsing library if needed.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import sre_parse

from .color_codes import ColorCode, ColorManager, color_manager

# ANSI SGR code constants for extended colors
ANSI_FG_256_CODE = 38
ANSI_BG_256_CODE = 48
ANSI_256_COLOR_TYPE = 5
ANSI_TRUE_COLOR_TYPE = 2
ANSI_256_COLOR_LEN = 3  # 38;5;N
ANSI_TRUE_COLOR_LEN = 5  # 38;2;R;G;B


@dataclass
class ColorRange:
    """Represents a range of text with a specific color applied.

    Priority is a tuple (pipeline_stage, nesting_depth, application_order).
    Python's lexicographic tuple comparison ensures:
    - Later pipeline stages override earlier ones (first element)
    - More nested regex groups override less nested ones (second element)
    - Later applications override earlier ones at same depth (third element)

    Using tuples prevents overflow issues where application_order could
    spill into nesting_depth space with integer-based priority calculation.
    """

    start: int  # Position in original text (inclusive)
    end: int  # Position in original text (exclusive)
    color: str  # Color name (e.g., 'red', 'bg_blue', 'bold')
    priority: tuple[int, int, int] = (0, 0, 0)  # (stage, depth, order)
    pipeline_stage: int = 0  # Which pipeline stage this was applied in


class Colorize:
    """Main colorization class providing color functionality."""

    def __init__(self, color_manager_instance: Optional[ColorManager] = None) -> None:
        self._color_manager = color_manager_instance or color_manager

    def colorize(self, text: str, color_code: Union[str, ColorCode]) -> str:
        """Colorize text with given color code."""
        if isinstance(color_code, str):
            code = self._color_manager.get_color_code(color_code)
            if code is None:
                raise ValueError(f"Unknown color: {color_code}")
            color_code = code

        return self._color_manager.colorize(text, color_code)

    def colorize_random(self, text: str, code: Optional[int] = None) -> str:
        """Colorize text with random color."""
        color_code = self._color_manager.generate_random_color(code)
        return self._color_manager.colorize(text, color_code)

    def remove_color(self, text: str) -> str:
        """Remove ANSI color codes from text."""
        return self._color_manager.remove_color(text)

    def start_color(self, color_code: Union[str, ColorCode]) -> str:
        """Get ANSI start sequence for color."""
        if isinstance(color_code, str):
            code = self._color_manager.get_color_code(color_code)
            if code is None:
                raise ValueError(f"Unknown color: {color_code}")
            color_code = code

        return self._color_manager.start_color(color_code)

    def end_color(self) -> str:
        """Get ANSI end sequence (reset)."""
        return self._color_manager.end_color()

    def get_color_names(self) -> list[str]:
        """Get all available color names."""
        return self._color_manager.get_color_names()

    def __getattr__(self, name: str) -> str:
        """Dynamic color method support (e.g., colorize.red)."""
        color_code = self._color_manager.get_color_code(name)
        if color_code is not None:
            return self._color_manager.start_color(color_code)

        # Try with fg_ prefix
        color_code = self._color_manager.get_color_code(f"fg_{name}")
        if color_code is not None:
            return self._color_manager.start_color(color_code)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class ColorizedString(str):
    """String subclass with colorization support using deferred rendering.

    This class stores the original text and a list of color ranges separately.
    When converted to string, it renders the colors using ANSI codes with proper
    nesting support based on priority.
    """

    def __new__(
        cls,
        value: str,
        original_text: Optional[str] = None,  # noqa: ARG004
        color_ranges: Optional[list[ColorRange]] = None,  # noqa: ARG004
        pipeline_stage: int = 0,  # noqa: ARG004
        raw_sequences: Optional[list[tuple[int, str]]] = None,  # noqa: ARG004
    ) -> "ColorizedString":
        # If value has ANSI codes, we'll parse them in __init__
        # Parameters needed to match __init__ signature
        return str.__new__(cls, value)

    def __init__(
        self,
        value: str,
        original_text: Optional[str] = None,
        color_ranges: Optional[list[ColorRange]] = None,
        pipeline_stage: int = 0,
        raw_sequences: Optional[list[tuple[int, str]]] = None,
    ) -> None:
        super().__init__()
        self._colorizer = Colorize()
        self._next_priority = 0

        # If original_text provided, use it; otherwise parse from value
        if original_text is not None:
            self._original_text = original_text
            self._color_ranges = color_ranges or []
            self._pipeline_stage = pipeline_stage
            self._raw_sequences = raw_sequences or []
        else:
            # Parse ANSI codes from value to extract original text and ranges
            (
                self._original_text,
                self._color_ranges,
                self._raw_sequences,
            ) = self._parse_ansi(value)
            # If we parsed any ranges from ANSI codes, we're in a pipeline
            # Start at stage 1 so new highlights have higher priority
            if pipeline_stage == 0 and self._color_ranges:
                self._pipeline_stage = 1
            else:
                self._pipeline_stage = pipeline_stage

        # Legacy support for old _colors_at API (will be removed)
        self._colors_at: dict[int, list[str]] = {}

    @staticmethod
    @staticmethod
    def _extract_extended_color(
        codes: list[int], index: int
    ) -> tuple[Optional[tuple[str, str]], int]:
        """Extract a 256-color or truecolor code starting at index."""
        if index >= len(codes):
            return None, 1

        code = codes[index]
        if code not in {ANSI_FG_256_CODE, ANSI_BG_256_CODE}:
            return None, 1

        result: Optional[tuple[str, str]] = None
        consumed = 1
        channel = "fg" if code == ANSI_FG_256_CODE else "bg"
        prefix = f"__raw_ansi_{channel}__:"

        if index + 1 < len(codes):
            color_type = codes[index + 1]
            if color_type == ANSI_256_COLOR_TYPE and index + ANSI_256_COLOR_LEN <= len(
                codes
            ):
                value = codes[index + 2]
                raw = f"{code};{color_type};{value}"
                result = (f"{prefix}{raw}", channel)
                consumed = ANSI_256_COLOR_LEN
            elif (
                color_type == ANSI_TRUE_COLOR_TYPE
                and index + ANSI_TRUE_COLOR_LEN <= len(codes)
            ):
                r, g, b = codes[index + 2 : index + 5]
                raw = f"{code};{color_type};{r};{g};{b}"
                result = (f"{prefix}{raw}", channel)
                consumed = ANSI_TRUE_COLOR_LEN

        return result, consumed

    @staticmethod
    def _close_and_start_color(
        channel: str,
        color_name: str,
        pos: int,
        active_colors: dict[str, tuple[str, int]],
        ranges: list[ColorRange],
    ) -> None:
        """Close previous color in channel (if any) and start new color."""
        if channel in active_colors:
            prev_color, start_pos = active_colors[channel]
            if start_pos < pos:
                ranges.append(
                    ColorRange(
                        start=start_pos,
                        end=pos,
                        color=prev_color,
                        priority=(0, 0, 0),
                        pipeline_stage=0,
                    )
                )
        active_colors[channel] = (color_name, pos)

    @staticmethod
    def _add_active_colors(
        active_colors: dict[str, tuple[str, int]], pos: int, ranges: list[ColorRange]
    ) -> bool:
        """Close all active colors and emit ranges. Returns True if any were closed."""
        closed_any = False
        for color_name, start_pos in active_colors.values():
            if start_pos < pos:
                ranges.append(
                    ColorRange(
                        start=start_pos,
                        end=pos,
                        color=color_name,
                        priority=(0, 0, 0),
                        pipeline_stage=0,
                    )
                )
                closed_any = True
        active_colors.clear()
        return closed_any

    def _parse_ansi(  # noqa: PLR0914
        self, text: str
    ) -> tuple[str, list[ColorRange], list[tuple[int, str]]]:
        """Parse ANSI codes from text to extract original text and color ranges.

        Returns:
            (original_text, color_ranges, raw_sequences)
            where original_text has ANSI codes removed and raw_sequences
            contains passthrough ANSI codes we don't understand yet.
        """
        # Pattern to match ANSI escape sequences
        ansi_pattern = re.compile(r"\x1b\[([0-9;]+)m")

        # Build reverse mapping: ANSI code -> color name
        code_to_color = {}
        for color_name, code_obj in self._colorizer._color_manager._color_map.items():
            code_to_color[code_obj.value] = color_name

        original_text = []
        ranges: list[ColorRange] = []
        raw_sequences: list[tuple[int, str]] = []
        active_colors: dict[
            str, tuple[str, int]
        ] = {}  # channel -> (color_name, start_pos)
        pos = 0

        # Split text into segments (text and ANSI codes)
        last_end = 0
        for match in ansi_pattern.finditer(text):
            # Add text before this ANSI code
            segment = text[last_end : match.start()]
            if segment:
                original_text.append(segment)
                pos += len(segment)

            # Parse ANSI code
            code_str = match.group(1)
            codes = [int(c) for c in code_str.split(";") if c]

            # Handle standard and extended codes in sequence order
            index = 0
            handled_unknown = False
            while index < len(codes):
                code = codes[index]

                # Reset - close all active colors
                if code == 0:
                    closed = self._add_active_colors(active_colors, pos, ranges)
                    if not closed:
                        raw_sequences.append((pos, "\x1b[0m"))
                    index += 1
                    continue

                # Extended color sequences (256-color / truecolor)
                extended, consumed = ColorizedString._extract_extended_color(
                    codes, index
                )
                if extended:
                    color_name, channel = extended
                    ColorizedString._close_and_start_color(
                        channel, color_name, pos, active_colors, ranges
                    )
                    index += consumed
                    continue

                # Standard color codes
                if code in code_to_color:
                    color_name = code_to_color[code]
                    channel = self._get_color_channel(color_name)
                    ColorizedString._close_and_start_color(
                        channel, color_name, pos, active_colors, ranges
                    )
                else:
                    remaining = ";".join(str(c) for c in codes[index:])
                    raw_sequences.append((pos, f"\x1b[{remaining}m"))
                    handled_unknown = True
                    break

                index += 1

            if handled_unknown:
                # Skip further processing for this ANSI sequence
                last_end = match.end()
                continue

            last_end = match.end()

        # Add remaining text after last ANSI code
        if last_end < len(text):
            segment = text[last_end:]
            original_text.append(segment)
            pos += len(segment)

        # Close any remaining active colors
        if active_colors:
            self._add_active_colors(active_colors, pos, ranges)

        return "".join(original_text), ranges, raw_sequences

    def _normalize_color_name(self, color_name: str) -> str:  # noqa: PLR6301
        """Normalize color names to standard format.

        Converts red_bg -> bg_red, etc.
        """
        color_lower = color_name.lower()

        # Convert color_bg format to bg_color format
        if color_lower.endswith("_bg") and not color_lower.startswith("bg_"):
            # Extract color part (everything except _bg suffix)
            color_part = color_lower[:-3]  # Remove '_bg'
            return f"bg_{color_part}"

        return color_name

    def _get_color_channel(self, color_name: str) -> str:  # noqa: PLR6301
        """Determine which channel a color belongs to: 'fg', 'bg', or 'attr'."""
        color_lower = color_name.lower()
        # Check for raw ANSI passthrough codes
        if color_lower.startswith("__raw_ansi_fg__:"):
            return "fg"
        if color_lower.startswith("__raw_ansi_bg__:"):
            return "bg"
        # Check for background colors (support both bg_red and red_bg formats)
        if color_lower.startswith("bg_") or color_lower.endswith("_bg"):
            return "bg"
        if color_lower in {
            "bright",
            "dim",
            "underline",
            "blink",
            "strikethrough",
            "bold",
            "invert",
            "swapcolor",
            "hidden",
        }:
            return "attr"
        return "fg"

    def _render(self) -> str:  # noqa: PLR0914
        """Render the original text with color ranges applied as ANSI codes.

        This handles proper nesting by:
        1. Finding all transition points (where any range starts/ends)
        2. For each segment, determining active colors by priority within each channel
        3. Outputting appropriate ANSI codes and text
        """
        raw_sequences = getattr(self, "_raw_sequences", [])
        if not self._color_ranges and not raw_sequences:
            return self._original_text

        # Find all transition points
        transitions = {0, len(self._original_text)}
        for range_ in self._color_ranges:
            transitions.add(range_.start)
            transitions.add(range_.end)

        sorted_transitions = sorted(transitions)

        raw_sequences_by_pos: dict[int, list[str]] = {}
        for pos, seq in raw_sequences:
            raw_sequences_by_pos.setdefault(pos, []).append(seq)

        # Build output segment by segment
        result_parts = []
        current_colors: dict[str, Optional[str]] = {
            "fg": None,
            "bg": None,
            "attr": None,
        }

        for i in range(len(sorted_transitions) - 1):  # noqa: PLR1702
            start_pos = sorted_transitions[i]
            end_pos = sorted_transitions[i + 1]

            if start_pos == end_pos:
                continue

            # Find active colors at this position (highest priority in each channel)
            active_ranges = [
                r for r in self._color_ranges if r.start <= start_pos < r.end
            ]

            # Group by channel and pick highest priority
            new_colors: dict[str, Optional[str]] = {
                "fg": None,
                "bg": None,
                "attr": None,
            }
            for channel in ["fg", "bg", "attr"]:
                channel_ranges = [
                    r
                    for r in active_ranges
                    if self._get_color_channel(r.color) == channel
                ]
                if channel_ranges:
                    # Pick highest priority
                    best = max(channel_ranges, key=lambda r: r.priority)
                    new_colors[channel] = best.color

            # Output ANSI codes if colors changed
            if new_colors != current_colors:
                codes = []

                # Build combined ANSI code for all active colors
                for channel in ["fg", "bg", "attr"]:
                    color_name = new_colors[channel]
                    if color_name:
                        # Check for raw ANSI passthrough
                        if color_name.startswith(
                            "__raw_ansi_fg__:"
                        ) or color_name.startswith("__raw_ansi_bg__:"):
                            # Extract the raw ANSI code sequence
                            raw_code = color_name.split(":", 1)[1]
                            codes.append(f"\x1b[{raw_code}m")
                        else:
                            try:
                                # Normalize color name (e.g., red_bg -> bg_red)
                                normalized = self._normalize_color_name(color_name)
                                codes.append(self._colorizer.start_color(normalized))
                            except ValueError:
                                # Invalid color name, skip
                                pass

                # Always reset if we had any previous colors, then apply new ones
                # This ensures clean state
                if current_colors != {"fg": None, "bg": None, "attr": None}:
                    result_parts.append(self._colorizer.end_color())

                # Apply new color codes
                if codes:
                    result_parts.extend(codes)

                current_colors = new_colors

            result_parts.extend(raw_sequences_by_pos.get(start_pos, []))

            # Output text segment
            result_parts.append(self._original_text[start_pos:end_pos])

        # Reset at end if we have active colors
        if current_colors != {"fg": None, "bg": None, "attr": None}:
            result_parts.append(self._colorizer.end_color())

        result_parts.extend(raw_sequences_by_pos.get(len(self._original_text), []))

        return "".join(result_parts)

    def __str__(self) -> str:
        """Convert to string by rendering color ranges."""
        return self._render()

    def colorize(self, color_code: Union[str, ColorCode]) -> "ColorizedString":
        """Apply color to the entire string."""
        if isinstance(color_code, ColorCode):
            color_name = color_code.name.lower()
        else:
            color_name = str(color_code)

        # Normalize color name (e.g., red_bg -> bg_red)
        color_name = self._normalize_color_name(color_name)

        # Create new ColorRange for entire text
        # Priority tuple: (pipeline_stage, nesting_depth, application_order)
        priority = (
            self._pipeline_stage,
            1,  # depth=1 for whole-string colorization
            self._next_priority,
        )

        new_range = ColorRange(
            start=0,
            end=len(self._original_text),
            color=color_name,
            priority=priority,
            pipeline_stage=self._pipeline_stage,
        )

        # Create new ColorizedString with added range
        new_ranges = self._color_ranges.copy()
        new_ranges.append(new_range)

        result = ColorizedString(
            value=self._original_text,  # Not rendered yet
            original_text=self._original_text,
            color_ranges=new_ranges,
            pipeline_stage=self._pipeline_stage,
            raw_sequences=self._raw_sequences.copy(),
        )
        result._next_priority = self._next_priority + 1

        return result

    def colorize_random(self, code: Optional[int] = None) -> "ColorizedString":
        """Apply random color to the string."""
        random_color = self._colorizer._color_manager.generate_random_color(code)
        return self.colorize(random_color)

    def remove_color(self) -> "ColorizedString":
        """Remove all color codes and return plain text."""
        # Just return the original text without any color ranges
        return ColorizedString(
            value=self._original_text,
            original_text=self._original_text,
            color_ranges=[],
            pipeline_stage=self._pipeline_stage,
            raw_sequences=[],
        )

    def _calculate_group_nesting_depth(  # noqa: PLR6301
        self, pattern_str: str
    ) -> dict[int, int]:
        """Calculate nesting depth for each capture group in a regex pattern.

        Uses sre_parse to properly identify capturing groups (including named groups)
        vs non-capturing groups, lookaheads, lookbehinds, etc.

        Returns a dict mapping group number to nesting depth.
        Group 0 (entire match) has depth 0, first-level groups have depth 1, etc.
        """
        depth_map = {0: 0}  # Group 0 is the entire match

        try:
            parsed_pattern = sre_parse.parse(pattern_str)
            # sre_parse.parse returns a SubPattern object with a .data attribute
            items_to_traverse = (
                parsed_pattern.data
                if hasattr(parsed_pattern, "data")
                else parsed_pattern
            )
        except (re.error, ValueError, TypeError, AttributeError):
            # If parsing fails due to invalid regex or unexpected structure,
            # fall back to simple depth tracking (group 0 only)
            return depth_map

        # Constants for sre_parse structure
        OP_AV_TUPLE_LEN = 2  # Each parsed item is (op, av) tuple
        BRANCH_AV_TUPLE_LEN = 2  # BRANCH av: (None, [branches])
        ASSERT_AV_TUPLE_LEN = 2  # ASSERT av: (direction, content)
        SUBPATTERN_TUPLE_LEN_FULL = (
            4  # Full structure: (group_num, add_flags, del_flags, content)
        )
        SUBPATTERN_TUPLE_LEN_MIN = 2  # Minimum: (group_num, content)

        def extract_data(obj: Any) -> Any:
            """Extract data attribute from SubPattern object if present."""
            return obj.data if hasattr(obj, "data") else obj

        def handle_subpattern(av: Any, current_depth: int) -> None:
            """Handle SUBPATTERN node."""
            if not isinstance(av, tuple):
                return

            # Handle different tuple structures (Python version dependent)
            if len(av) >= SUBPATTERN_TUPLE_LEN_FULL:
                group_num = av[0]
                parsed_content = av[3]
            elif len(av) >= SUBPATTERN_TUPLE_LEN_MIN:
                group_num = av[0]
                parsed_content = av[1] if isinstance(av[1], list) else av[-1]
            else:
                return

            parsed_content = extract_data(parsed_content)

            if group_num is not None:
                # Capturing group (includes named groups)
                depth_map[group_num] = current_depth + 1
                if isinstance(parsed_content, list):
                    traverse(parsed_content, current_depth + 1)
            elif isinstance(parsed_content, list):
                # Non-capturing group - maintain depth for nested groups
                traverse(parsed_content, current_depth + 1)

        def handle_branch(av: Any, current_depth: int) -> None:
            """Handle BRANCH node (alternation |)."""
            if not isinstance(av, tuple) or len(av) < BRANCH_AV_TUPLE_LEN:
                return
            branches = av[1]
            if not isinstance(branches, list):
                return
            for branch_item in branches:
                branch_data = extract_data(branch_item)
                if isinstance(branch_data, list):
                    traverse(branch_data, current_depth)

        def handle_assert(av: Any, current_depth: int) -> None:
            """Handle ASSERT/ASSERT_NOT node (lookahead/behind)."""
            if not isinstance(av, tuple) or len(av) < ASSERT_AV_TUPLE_LEN:
                return
            parsed_content = extract_data(av[1])
            if isinstance(parsed_content, list):
                traverse(parsed_content, current_depth)

        def traverse(items: Any, current_depth: int) -> None:
            """Recursively traverse the regex AST to calculate nesting depths."""
            if not isinstance(items, list):
                return

            for item in items:
                if not isinstance(item, tuple) or len(item) != OP_AV_TUPLE_LEN:
                    continue

                op, av = item

                if op == sre_parse.SUBPATTERN:
                    handle_subpattern(av, current_depth)
                elif op == sre_parse.BRANCH:
                    handle_branch(av, current_depth)
                elif op in {sre_parse.ASSERT, sre_parse.ASSERT_NOT}:
                    handle_assert(av, current_depth)
                # Note: ATOMIC_GROUP (?>...) in Python 3.11+ is handled by
                # the isinstance(av, list) fallback since it doesn't capture
                elif isinstance(av, list):
                    traverse(av, current_depth)

        traverse(items_to_traverse, 0)
        return depth_map

    def highlight(
        self, pattern: Union[str, re.Pattern], colors: Union[str, list[str]]
    ) -> "ColorizedString":
        """Highlight text matching pattern with given colors.

        Matches against the original text (ignoring any existing ANSI codes).
        Inner (more nested) groups have higher priority than outer groups.
        """
        if isinstance(colors, str):
            colors = [colors]

        # Compile pattern if needed
        if isinstance(pattern, str):
            pattern_str = pattern
            pattern_obj = re.compile(pattern, re.IGNORECASE)
        else:
            pattern_obj = pattern
            pattern_str = pattern.pattern

        # Calculate nesting depth for each group
        nesting_depths = self._calculate_group_nesting_depth(pattern_str)

        # Match against original text (not rendered ANSI string!)
        matches = list(pattern_obj.finditer(self._original_text))
        if not matches:
            # No matches, return self unchanged
            return ColorizedString(
                value=self._original_text,
                original_text=self._original_text,
                color_ranges=self._color_ranges.copy(),
                pipeline_stage=self._pipeline_stage,
                raw_sequences=self._raw_sequences.copy(),
            )

        # Collect new color ranges from all matches
        new_ranges = self._color_ranges.copy()

        # Get number of groups from pattern
        num_groups = pattern_obj.groups

        for match in matches:
            if num_groups == 0:
                # No groups, highlight entire match (group 0)
                groups_to_highlight = [0]
            else:
                # Highlight all capturing groups (not group 0)
                groups_to_highlight = list(range(1, num_groups + 1))

            # Create ColorRange for each group
            for grp in groups_to_highlight:
                if match.group(grp) is None:
                    continue

                # Determine color for this group
                color_index = 0 if grp == 0 else (grp - 1) % len(colors)
                color = colors[color_index]

                # Skip empty colors (used to selectively apply colors to specific groups)
                if not color or not color.strip():
                    continue

                # Normalize color name (e.g., red_bg -> bg_red)
                color = self._normalize_color_name(color)

                # Calculate priority based on nesting depth
                # For group 0 (entire match with no groups), use depth 1
                nesting_depth = 1 if grp == 0 else nesting_depths.get(grp, 1)

                # Priority tuple: (pipeline_stage, nesting_depth, application_order)
                priority = (
                    self._pipeline_stage,
                    nesting_depth,
                    self._next_priority,
                )

                # Create range
                new_range = ColorRange(
                    start=match.start(grp),
                    end=match.end(grp),
                    color=color,
                    priority=priority,
                    pipeline_stage=self._pipeline_stage,
                )
                new_ranges.append(new_range)
                self._next_priority += 1

        # Return new ColorizedString with added ranges
        result = ColorizedString(
            value=self._original_text,
            original_text=self._original_text,
            color_ranges=new_ranges,
            pipeline_stage=self._pipeline_stage,
            raw_sequences=self._raw_sequences.copy(),
        )
        result._next_priority = self._next_priority

        return result

    def highlight_at(
        self, positions: list[int], color: str = "fg_yellow"
    ) -> "ColorizedString":
        """Highlight characters at specific positions in the original text."""
        if not positions:
            return ColorizedString(
                value=self._original_text,
                original_text=self._original_text,
                color_ranges=self._color_ranges.copy(),
                pipeline_stage=self._pipeline_stage,
                raw_sequences=self._raw_sequences.copy(),
            )

        # Normalize color name
        color = self._normalize_color_name(color)

        new_ranges = self._color_ranges.copy()

        # Create a ColorRange for each character position
        # Use high priority so they override existing colors
        for pos in sorted(set(positions)):
            if 0 <= pos < len(self._original_text):
                # Calculate priority
                # Priority tuple: (pipeline_stage, nesting_depth, application_order)
                priority = (
                    self._pipeline_stage,
                    2,  # depth=2 for individual chars
                    self._next_priority,
                )

                # Create range for single character
                new_range = ColorRange(
                    start=pos,
                    end=pos + 1,
                    color=color,
                    priority=priority,
                    pipeline_stage=self._pipeline_stage,
                )
                new_ranges.append(new_range)
                self._next_priority += 1

                # Also add swapcolor attribute
                swap_range = ColorRange(
                    start=pos,
                    end=pos + 1,
                    color="swapcolor",
                    priority=priority,
                    pipeline_stage=self._pipeline_stage,
                )
                new_ranges.append(swap_range)

        result = ColorizedString(
            value=self._original_text,
            original_text=self._original_text,
            color_ranges=new_ranges,
            pipeline_stage=self._pipeline_stage,
            raw_sequences=self._raw_sequences.copy(),
        )
        result._next_priority = self._next_priority

        return result

    def __getattr__(self, name: str) -> "ColorizedString":
        """Dynamic color methods for strings (e.g., "text".red())."""
        color_code = self._colorizer._color_manager.get_color_code(name)
        if color_code is not None:
            return self.colorize(color_code)

        # Try with fg_ prefix
        color_code = self._colorizer._color_manager.get_color_code(f"fg_{name}")
        if color_code is not None:
            return self.colorize(color_code)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


# Global colorize instance
colorize = Colorize()
