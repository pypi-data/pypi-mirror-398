"""Command-line interface for colorize."""

import argparse
import contextlib
import html
import re
import sys

from .core import Colorize, ColorizedString


def ansi_to_html(text: str) -> str:
    """Convert ANSI color codes to HTML with inline styles.

    Properly handles reset codes and multiple colored segments.
    Escapes HTML special characters to prevent XSS vulnerabilities.

    Args:
        text: Text with ANSI color codes

    Returns:
        HTML string with <span> tags and inline styles
    """
    # Map ANSI codes to CSS
    color_map = {
        "30": "color:#000",
        "31": "color:#c00",
        "32": "color:#0c0",
        "33": "color:#cc0",
        "34": "color:#00c",
        "35": "color:#c0c",
        "36": "color:#0cc",
        "37": "color:#ccc",
        "90": "color:#888",
        "91": "color:#f00",
        "92": "color:#0f0",
        "93": "color:#ff0",
        "94": "color:#00f",
        "95": "color:#f0f",
        "96": "color:#0ff",
        "97": "color:#fff",
        "40": "background-color:#000",
        "41": "background-color:#c00",
        "42": "background-color:#0c0",
        "43": "background-color:#cc0",
        "44": "background-color:#00c",
        "45": "background-color:#c0c",
        "46": "background-color:#0cc",
        "47": "background-color:#ccc",
        "100": "background-color:#888",
        "101": "background-color:#f00",
        "102": "background-color:#0f0",
        "103": "background-color:#ff0",
        "104": "background-color:#00f",
        "105": "background-color:#f0f",
        "106": "background-color:#0ff",
        "107": "background-color:#fff",
        "1": "font-weight:bold",
        "4": "text-decoration:underline",
    }

    # Parse ANSI codes and convert to HTML spans
    result: list[str] = []
    current_styles: list[str] = []
    pos = 0

    for match in re.finditer(r"\x1b\[([0-9;]+)m", text):
        # Add any text before this escape code
        if match.start() > pos:
            plain_text = text[pos : match.start()]
            escaped_text = html.escape(plain_text).replace("\n", "<br>")
            if current_styles:
                result.append(
                    f'<span style="{";".join(current_styles)}">{escaped_text}</span>'
                )
            else:
                result.append(escaped_text)

        # Parse escape code and update styles
        codes = match.group(1).split(";")
        if "0" in codes:  # Reset
            current_styles = []
        else:
            for code in codes:
                if code in color_map:
                    current_styles.append(color_map[code])

        pos = match.end()

    # Add any remaining text after the last escape code
    if pos < len(text):
        plain_text = text[pos:]
        escaped_text = html.escape(plain_text).replace("\n", "<br>")
        if current_styles:
            result.append(
                f'<span style="{";".join(current_styles)}">{escaped_text}</span>'
            )
        else:
            result.append(escaped_text)

    return "".join(result)


def _create_help_examples() -> str:
    """Create examples for CLI help.

    Returns colored examples if stdout is a TTY, plain text otherwise.
    This ensures help is readable when piped or on systems without ANSI support.
    """
    # Check if stdout is a TTY - only show colors in interactive terminals
    if sys.stdout.isatty():
        # Colored examples for interactive terminals
        ex1_out = str(
            ColorizedString("ERROR: Connection failed").highlight(r"ERROR", ["red"])
        )
        ex2_out = str(
            ColorizedString("SUCCESS: Task completed").highlight(r"SUCCESS", ["green"])
        )
        ex3_out = str(
            ColorizedString("hello world").highlight(r"(h.(ll))", ["red", "blue"])
        )
        ex4_tmp = ColorizedString("WARN: Check logs").highlight(r"WARN", ["black"])
        ex4_out = str(ex4_tmp.highlight(r"WARN", ["bg_yellow"]))
        ex5_out = str(
            ColorizedString(
                "2024-01-15 ERROR: Connection timeout at server.py:42"
            ).highlight(
                r"(\d{4}-\d{2}-\d{2}).*?(ERROR|WARN|INFO).*?([a-z_]+\.py:\d+)",
                ["cyan", "red", "yellow"],
            )
        )
        ex6_tmp1 = ColorizedString("ERROR: Connection failed at 10:30:45").highlight(
            r"ERROR", ["red"]
        )
        ex6_tmp2 = ex6_tmp1.highlight(r"ERROR", ["bold"])
        ex6_out = str(ex6_tmp2.highlight(r"\d{2}:\d{2}:\d{2}", ["blue"]))
    else:
        # Plain text examples for non-TTY (piped output, CI, Windows cmd)
        ex1_out = "ERROR: Connection failed"
        ex2_out = "SUCCESS: Task completed"
        ex3_out = "hello world"
        ex4_out = "WARN: Check logs"
        ex5_out = "2024-01-15 ERROR: Connection timeout at server.py:42"
        ex6_out = "ERROR: Connection failed at 10:30:45"

    return f"""
Examples:
  # Highlight errors in red
  $ echo "ERROR: Connection failed" | pipetint 'ERROR' red
  {ex1_out}

  # Highlight success in green
  $ echo "SUCCESS: Task completed" | pipetint 'SUCCESS' green
  {ex2_out}

  # Nested groups - inner color wins
  $ echo "hello world" | pipetint '(h.(ll))' red blue
  {ex3_out}

  # Background + foreground
  $ echo "WARN: Check logs" | pipetint 'WARN' black,bg_yellow
  {ex4_out}

  # Multiple patterns - log parsing with 3 groups (date, level, location)
  $ echo "2024-01-15 ERROR: Connection timeout at server.py:42" | \\
      pipetint '(\\d{{4}}-\\d{{2}}-\\d{{2}}).*?(ERROR|WARN|INFO).*?([a-z_]+\\.py:\\d+)' \\
      cyan red yellow
  {ex5_out}

  # Pipeline composition - colors preserved across stages
  $ echo "ERROR: Connection failed at 10:30:45" | \\
      pipetint 'ERROR' red,bold | \\
      pipetint '\\d{{2}}:\\d{{2}}:\\d{{2}}' blue
  {ex6_out}

  # List all available colors
  $ pipetint --list-colors
        """


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Colorize text from stdin using ANSI color codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="echo 'text' | pipetint [PATTERN] [COLORS...]\n"
        "       pipetint --list-colors\n"
        "       pipetint --remove-color",
        epilog=_create_help_examples(),
    )

    parser.add_argument(
        "pattern",
        nargs="?",
        default="(.*)",
        metavar="PATTERN",
        help="Regular expression pattern to match text (default: match all)",
    )

    parser.add_argument(
        "colors",
        nargs="*",
        default=["black,bg_yellow,swapcolor"],
        metavar="COLORS",
        help="Colors for each capture group. Use commas to combine multiple colors "
        "for one group (e.g., red,bold). Default: black,bg_yellow,swapcolor",
    )

    parser.add_argument(
        "--list-colors", action="store_true", help="List all available colors and exit"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Make pattern matching case sensitive",
    )

    parser.add_argument(
        "--replace-all",
        action="store_true",
        help="Clear all previous colors before applying new ones (useful in pipelines)",
    )

    parser.add_argument(
        "-u",
        "--unbuffered",
        action="store_true",
        help="Force line-buffered output (flush after each line). "
        "Useful for real-time log streaming without external tools like stdbuf.",
    )

    parser.add_argument(
        "--remove-color",
        "--strip-color",
        action="store_true",
        help="Remove all ANSI color codes from input (strip colors to plain text)",
    )

    parser.add_argument(
        "--output-format",
        choices=["ansi", "plain", "html"],
        default="ansi",
        help="Output format: ansi (default, with color codes), plain (no colors), "
        "html (HTML with inline styles)",
    )

    return parser


def _display_foreground_colors(foreground: list[str]) -> None:
    """Display foreground colors with colored blocks."""
    section_title = ColorizedString("Foreground Colors").colorize("bold")
    print(section_title)
    print("-" * 60)
    for name in foreground:
        # Show colored block and the text "This is <color>"
        block = ColorizedString("████").colorize(name)
        demo_text = ColorizedString(f"This is {name}").colorize(name)
        print(f"  {block}  {demo_text}")
    print()


def _display_background_colors(background: list[str]) -> None:
    """Display background colors with colored blocks."""
    section_title = ColorizedString("Background Colors").colorize("bold")
    print(section_title)
    print("-" * 60)
    for name in background:
        # Show background colored block with black text
        block_tmp = ColorizedString("████").colorize(name)
        block = block_tmp.colorize("black")
        # Show text with background
        demo_tmp = ColorizedString(f"This is {name}").colorize(name)
        demo_text = demo_tmp.colorize("black")
        print(f"  {block}  {demo_text}")
    print()


def _display_text_styles(styles: list[str]) -> None:
    """Display text styles with demonstrations."""
    section_title = ColorizedString("Text Styles").colorize("bold")
    print(section_title)
    print("-" * 60)
    for name in styles:
        # Special handling for hidden - show description instead of invisible text
        if name == "hidden":
            print(f"  This is {name} (text hidden in terminal)")
        else:
            # Show the style applied to sample text
            demo = ColorizedString(f"This is {name}").colorize(name)
            print(f"  {demo}")
    print()


def list_colors():
    """List all available colors with visual demonstrations."""
    colorizer = Colorize()

    # Header
    header = ColorizedString("Available Colors").colorize("bold")
    print(header)
    print("=" * 60)
    print()

    color_map = colorizer._color_manager._color_map

    # Group colors by type (only user-facing ones)
    foreground = []
    background = []
    styles = []

    # Define text style names as a set for efficient lookup
    # Includes primary style names and all their aliases
    text_styles = {
        # Primary style names
        "bright",
        "dim",
        "underline",
        "blink",
        "invert",
        "swapcolor",
        "hidden",
        "strikethrough",
        # Style aliases
        "bold",  # alias for bright
        "inverse",  # alias for invert
        "reverse",  # alias for invert
        "swap",  # alias for swapcolor
        "strike",  # alias for strikethrough
    }

    for name in sorted(color_map.keys()):
        # Skip internal color names (fg_, bg_ prefixed duplicates)
        if name.startswith("fg_") or name.endswith("_bg"):
            continue

        if name.startswith("bg_"):
            background.append(name)
        elif name in text_styles:
            styles.append(name)
        else:
            foreground.append(name)

    # Display sections
    if foreground:
        _display_foreground_colors(foreground)

    if background:
        _display_background_colors(background)

    if styles:
        _display_text_styles(styles)

    # Footer with usage hint
    print("=" * 60)
    hint = ColorizedString("Usage: pipetint 'pattern' <color>").colorize("dim")
    print(hint)


def process_line(
    line: str,
    pattern: re.Pattern,
    color_groups: list[list[str]],
    verbose: bool = False,
    replace_all: bool = False,
) -> str:
    """Process a single line of input.

    Args:
        line: Input line to process
        pattern: Compiled regex pattern
        color_groups: List of color lists, one per capture group.
                      e.g., [['red', 'bold'], ['blue']] means group 1 gets red+bold,
                      group 2 gets blue.
        verbose: Enable verbose output
        replace_all: Clear previous colors before applying new ones
    """
    # Remove trailing newline for processing
    line = line.rstrip("\n")

    # Create ColorizedString from input
    colored_str = ColorizedString(line)

    # If replace_all is True, clear all existing colors by creating
    # a new ColorizedString from the original text only
    if replace_all:
        colored_str = ColorizedString(
            value=colored_str._original_text,
            original_text=colored_str._original_text,
            color_ranges=[],
            pipeline_stage=0,
            raw_sequences=[],
        )

    # Apply colors layer by layer across all groups
    # Each layer takes the nth color from each group
    # Inner groups have higher nesting priority within each layer
    # Empty colors are skipped in highlight() so they don't override
    max_colors = max((len(g) for g in color_groups), default=0)
    result = colored_str
    for layer in range(max_colors):
        layer_colors = []
        for group_colors in color_groups:
            if layer < len(group_colors):
                layer_colors.append(group_colors[layer])
            else:
                layer_colors.append("")
        result = result.highlight(pattern, layer_colors)

    if verbose:
        print(f"Original: {colored_str._original_text}", file=sys.stderr)
        print(f"Pattern: {pattern.pattern}", file=sys.stderr)
        print(f"Color groups: {color_groups}", file=sys.stderr)
        if replace_all:
            print("Replace all: True (cleared previous colors)", file=sys.stderr)

    return str(result)


def handle_color_removal():
    """Handle color removal mode (--remove-color or --output-format=plain)."""
    colorizer = Colorize()
    try:
        for line in sys.stdin:
            clean_line = colorizer.remove_color(line.rstrip("\n"))
            print(clean_line)
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        sys.exit(0)


def _print_result(result: str, output_format: str) -> None:
    """Print processed line respecting the desired output format."""
    if output_format == "html":
        rendered = ansi_to_html(result)
        print(f"{rendered}<br>")
    else:
        print(result)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle special commands
    if args.list_colors:
        list_colors()
        return

    # Handle remove-color mode
    if args.remove_color or args.output_format == "plain":
        handle_color_removal()
        return

    # Handle help when no stdin and using default arguments
    if (
        sys.stdin.isatty()
        and args.pattern == "(.*)"
        and args.colors == ["black,bg_yellow,swapcolor"]
    ):
        parser.print_help()
        return

    # Compile regex pattern
    flags = 0 if args.case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(args.pattern, flags)
    except re.error:
        sys.exit(1)

    # Parse colors - each argument is a group of colors for one capture group
    # e.g., ['red,bold', 'blue'] -> [['red', 'bold'], ['blue']]
    # This means group 1 gets red+bold, group 2 gets blue
    color_groups = []
    for color_arg in args.colors:
        group_colors = [c.strip() for c in color_arg.split(",") if c.strip()]
        color_groups.append(group_colors)

    # Configure line-buffered output if requested
    # Uses contextlib.suppress for cleaner handling of missing reconfigure method
    if args.unbuffered:
        with contextlib.suppress(AttributeError):
            sys.stdout.reconfigure(line_buffering=True)  # type: ignore[union-attr]

    # Process input
    try:
        for line in sys.stdin:
            result = process_line(
                line, pattern, color_groups, args.verbose, args.replace_all
            )

            _print_result(result, args.output_format)
    except KeyboardInterrupt:
        sys.exit(1)
    except BrokenPipeError:
        # Handle broken pipe gracefully
        sys.exit(0)


if __name__ == "__main__":
    main()
