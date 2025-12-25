# PipeTint

> **The only terminal colorizer with smart color nesting and pipeline composition.**

[![CI](https://github.com/jim-my/pipetint/workflows/CI/badge.svg)](https://github.com/jim-my/pipetint/actions)
[![codecov](https://codecov.io/gh/jim-my/pipetint/branch/main/graph/badge.svg)](https://codecov.io/gh/jim-my/pipetint)
[![PyPI version](https://badge.fury.io/py/pipetint.svg)](https://badge.fury.io/py/pipetint)
[![Python versions](https://img.shields.io/pypi/pyversions/pipetint.svg)](https://pypi.org/project/pipetint)
[![Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](https://github.com/jim-my/pipetint)

Python library and CLI tool for terminal text colorization with **automatic priority-based color nesting**, **pipeline composition**, and **ANSI-aware pattern matching**. Zero dependencies, pure Python.

---

## 📖 Quick Navigation

- [⚡ Quick Start](#-quick-start) - Get started in 30 seconds
- [🎨 What Makes PipeTint Unique](#-what-makes-pipetint-unique) - Smart nesting, pipelines, channel isolation
- [💡 Real-World Examples](#-real-world-examples) - Log highlighting, syntax highlighting
- [📋 Full Documentation](#-full-documentation) - Complete API reference
- [🚀 Installation](#-installation)

---

## ⚡ Quick Start

```bash
# Install
pip install pipetint

# Smart color nesting - inner groups automatically win
echo "hello world" | pipetint '(h.(ll))' red blue
# Output: "he" is red, "ll" is blue (inner has higher priority)

# Pipeline composition - colors preserved across stages
echo "hello world" | pipetint 'hello' red | pipetint 'world' blue
# Output: "hello" is red, "world" is blue

# Python API with type-safe constants
from pipetint import colored, RED, BLUE, BOLD
print(colored("Error") | RED | BOLD)
```

![Basic Colors](docs/images/basic-colors.png)

---

## 🎨 What Makes PipeTint Unique

### 1. 🧠 **Smart Color Nesting** (No other tool has this!)

Automatic priority-based rendering without manual z-index configuration:

```bash
# Nested regex groups - inner automatically wins
echo "hello world" | pipetint '(h.(ll))' red blue
# "he" is red, "ll" is blue (inner group has higher priority)
```

![Nested Groups](docs/images/nested-groups.png)

**Priority Rules:**
1. **Pipeline stage** - Later commands override earlier ones
2. **Nesting depth** - Inner regex groups override outer groups
3. **Application order** - Later applications win within same depth

### 2. 🔗 **Pipeline Composition**

Colors preserved across pipeline stages with intelligent priority:

```bash
# Both colors preserved
echo "hello world" | pipetint 'hello' red | pipetint 'world' blue

# Later stage overrides overlaps
echo "hello world" | pipetint 'hello' red | pipetint 'llo w' green
# "he" is red, "llo w" is green (overrides)
```

![Pipeline Demo](docs/images/pipeline-demo.png)

### 3. 🎯 **Channel Isolation**

Foreground, background, and attributes work independently:

```bash
# Background + foreground coexist in same text
echo "hello world" | pipetint '(h.(ll))' bg_red blue
# "he" = red background only
# "ll" = red background AND blue foreground (both channels!)
```

![Channel Isolation](docs/images/channel-isolation.png)

### 4. 🔍 **ANSI-Aware Pattern Matching**

Patterns match original text, ignoring existing ANSI codes:

```python
# Works on already-colored text!
colored_text = ColorizedString("H\x1b[31mello\x1b[0m World")
result = colored_text.highlight(r'Hello', ['green'])
# Pattern matches "Hello" despite ANSI codes in the middle
```

---

## 💡 Real-World Examples

### Log File Highlighting

```python
from pipetint import ColorizedString

log = "ERROR: Connection failed at 10:30:45"
result = (ColorizedString(log)
    .highlight(r'ERROR', ['red', 'bold'])
    .highlight(r'\d{2}:\d{2}:\d{2}', ['blue'])
)
print(result)
# "ERROR" is red+bold, timestamp is blue
```

### Multi-Stage Pipeline Processing

```bash
# Stage 1: Highlight errors
cat log.txt | pipetint 'ERROR|CRITICAL' red > /tmp/colored.txt

# Stage 2: Add timestamps (higher priority)
cat /tmp/colored.txt | pipetint '\d{2}:\d{2}:\d{2}' blue
# Both colors preserved, timestamps override errors if overlapping
```

### Syntax Highlighting

```python
code = "def hello_world():"
result = (ColorizedString(code)
    .highlight(r'\b(def)\b', ['blue'])           # Keywords
    .highlight(r'[a-z_]+\w*(?=\()', ['green'])   # Functions
)
print(result)
```

![Complex Styling](docs/images/complex-styling.png)

---

## 🚀 Installation

```bash
# From PyPI
pip install pipetint

# From source
git clone https://github.com/jim-my/pipetint.git
cd pipetint
pip install -e .
```

**Requirements:**
- Python 3.9+
- Zero dependencies (pure Python)

---

## ✨ Features

- **🧠 Smart Color Nesting**: Automatic priority-based rendering without manual z-index
- **🔍 ANSI-Aware Matching**: Patterns match original text, ignoring color codes
- **🎯 Channel Isolation**: Foreground, background, and attributes work independently
- **🔗 Pipeline Composition**: Colors preserved across pipeline stages
- **🔒 Production Safe**: No monkey patching or global state pollution
- **🎭 Multiple APIs**: Choose your style - fluent, functional, or global
- **⚡ High Performance**: Efficient implementation with minimal overhead
- **🧪 Well Tested**: 143 tests with comprehensive coverage
- **📦 Zero Dependencies**: Pure Python implementation
- **🖥️ Cross Platform**: Works on Linux, macOS, and Windows

---

## 📋 Full Documentation

### CLI Usage

#### Basic Usage

```bash
# Simple pattern matching
echo "hello world" | pipetint 'l' red

# Pattern groups
echo "hello world" | pipetint '(h.*o).*(w.*d)' red blue
```

![CLI Examples](docs/images/cli-examples.png)

#### Advanced: Nested Colors

```bash
# Nested regex groups - inner wins
echo "hello world" | pipetint '(h.(ll))' red blue
# Output: "he" is red, "ll" is blue

# Channel isolation - foreground + background
echo "hello world" | pipetint '(h.(ll))' bg_red blue
# Output: "he" = red bg, "ll" = red bg + blue fg

# Color name formats (both work)
echo "hello" | pipetint 'hello' bg_red    # Official format
echo "hello" | pipetint 'hello' red_bg    # Natural format (auto-normalized)
```

![Both Formats](docs/images/both-formats.png)

#### CLI Options

```bash
# List all available colors
pipetint --list-colors

# Case sensitive matching
echo "Hello World" | pipetint --case-sensitive 'Hello' green

# Verbose mode (debugging)
echo "test" | pipetint --verbose 'test' red

# Clear all previous colors before applying new ones
echo "hello world" | pipetint 'hello' red | pipetint --replace-all 'world' blue
# Result: Only "world" is blue, "hello" has no color
```

#### Color Removal & Output Formats

Strip ANSI color codes or convert to different formats:

```bash
# Remove all colors (strip ANSI codes)
cat colored.log | pipetint --remove-color > clean.log

# Same using --output-format
cat colored.log | pipetint --output-format=plain > clean.log

# Convert colored output to HTML (with inline styles)
echo "ERROR: Failed" | pipetint 'ERROR' red --output-format=html > output.html

# Pipeline: colorize then strip colors for data processing
cat app.log | pipetint 'ERROR' red | grep ERROR | pipetint --remove-color | wc -l
```

**Use Cases:**
- Extract plain text from colored terminal output
- Process logs without ANSI codes interfering
- Convert terminal colors to HTML for web display
- Clean up output before saving to files

### Python Library API

#### Type-Safe Constants (Recommended)

```python
from pipetint import colored, txt, RED, GREEN, BLUE, YELLOW, BOLD, BG_WHITE, UNDERLINE

# Type-safe constants with operator chaining
print(colored("Success") | GREEN | BOLD)
print(txt("Warning") | YELLOW)
print(colored("Error") | RED | BOLD | BG_WHITE)
print(txt("Info") >> BLUE >> UNDERLINE)
```

#### Global Object with Constants

```python
from pipetint import C, RED, BOLD

C.red("hello")              # Direct color method
C("hello") | RED | BOLD     # Factory with type-safe constants
C("hello", "red")           # Direct colorization (legacy)
```

#### Pattern Highlighting

```python
from pipetint import ColorizedString

# Highlight search terms
text = "The quick brown fox jumps over the lazy dog"
highlighted = ColorizedString(text).highlight(
    r"(quick)|(fox)|(lazy)",
    ["red", "blue", "green"]
)
print(highlighted)

# Syntax highlighting
code = "def hello_world():"
result = ColorizedString(code).highlight(r"\b(def)\b", ["blue"])
print(result)
```

![Pattern Highlighting](docs/images/pattern-highlighting.png)

#### Color Removal

Remove ANSI color codes from text:

```python
from pipetint import Colorize, ColorizedString

# Method 1: Using Colorize
colorizer = Colorize()
colored_text = "\033[31mERROR\033[0m: Connection failed"
clean_text = colorizer.remove_color(colored_text)
print(clean_text)  # "ERROR: Connection failed"

# Method 2: Using ColorizedString
cs = ColorizedString("\033[31mERROR\033[0m: Connection failed")
clean = cs.remove_color()
print(str(clean))  # "ERROR: Connection failed"

# Useful for processing colored output
log_line = ColorizedString("...").highlight(r'ERROR', ['red'])
# Later, extract plain text for analysis
plain_text = str(log_line.remove_color())
```

### Available Colors and Styles

#### Foreground Colors
`red`, `green`, `blue`, `yellow`, `magenta`, `cyan`, `white`, `black`, `lightred`, `lightgreen`, `lightblue`, `lightyellow`, `lightmagenta`, `lightcyan`, `lightgray`, `darkgray`

#### Background Colors
`bg_red`, `bg_green`, `bg_blue`, `bg_yellow`, `bg_magenta`, `bg_cyan`, `bg_white`, `bg_black`, `bg_lightred`, `bg_lightgreen`, `bg_lightblue`, `bg_lightyellow`, `bg_lightmagenta`, `bg_lightcyan`, `bg_lightgray`, `bg_darkgray`

#### Text Styles
`bright`/`bold`, `dim`, `underline`, `blink`, `invert`/`swapcolor`, `hidden`, `strikethrough`

### Type-Safe Color Constants

Use constants instead of error-prone string literals:

```python
from pipetint import colored, RED, GREEN, BLUE, YELLOW, BOLD, BG_WHITE

# ✅ Type-safe with IDE autocompletion and error checking
error_msg = colored("CRITICAL") | RED | BOLD | BG_WHITE
success_msg = colored("SUCCESS") | GREEN | BOLD
warning_msg = colored("WARNING") | YELLOW

# ❌ Error-prone string literals
error_msg = colored("CRITICAL") | "red" | "typo"  # Runtime error!
```

**Benefits:**
- 🔍 **IDE Autocompletion**: Get suggestions for valid colors
- 🛡️ **Type Checking**: Catch typos at development time
- 📝 **Self-Documenting**: Clear, readable code
- 🔄 **Refactoring Safe**: Rename constants across codebase
- ⚡ **No Runtime Errors**: Invalid colors caught early

---

## 🎨 Advanced: Color Nesting & Priority

### Nested Regex Groups

Inner (more specific) capture groups automatically override outer ones:

```python
from pipetint import ColorizedString

text = ColorizedString("hello world")

# Pattern: (h.(ll)) creates two groups
# - Group 1: "hell" (outer) → red
# - Group 2: "ll" (inner, higher priority) → blue
result = text.highlight(r'(h.(ll))', ['red', 'blue'])
print(result)
# Output: "he" is red, "ll" is blue (inner wins)
```

**Priority Rules:**
1. **Pipeline stage**: Later commands override earlier ones
2. **Nesting depth**: Inner regex groups override outer groups
3. **Application order**: Later applications win within same depth

### Channel Isolation

Foreground, background, and attributes are independent channels that can coexist:

```python
text = ColorizedString("hello world")

# Background and foreground don't conflict!
result = text.highlight(r'(h.(ll))', ['bg_red', 'blue'])
print(result)
# Output: "he" has red background
#         "ll" has BOTH red background AND blue foreground
```

**Available Channels:**
- **Foreground (fg)**: Text color (red, blue, green, etc.)
- **Background (bg)**: Background color (bg_red, bg_blue, etc.)
- **Attributes (attr)**: Bold, underline, dim, etc.

### ANSI-Aware Pattern Matching

Patterns always match the original text, even if it contains ANSI codes:

```python
# Text with existing ANSI codes
colored_text = ColorizedString("H\x1b[31mello\x1b[0m World")

# Pattern still matches "Hello" ignoring the ANSI codes in between
result = colored_text.highlight(r'Hello', ['green'])
print(result)
# Works! Pattern matched the original text "Hello World"
```

### Color Name Flexibility

Both `bg_red` and `red_bg` formats are supported:

```python
# These are equivalent:
text.highlight(r'hello', ['bg_red'])    # Official format
text.highlight(r'hello', ['red_bg'])    # Natural format (auto-normalized)
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pipetint

# Run specific test file
pytest tests/test_nesting.py
```

### Code Quality

```bash
# Format and lint
ruff format --preview .
ruff check --preview .

# Type checking
mypy src/

# Run pre-commit hooks
pre-commit run --all-files
```

---

## 📖 Examples

See the `examples/` directory for more comprehensive examples:

- `examples/quickstart.py` - Basic usage patterns
- `examples/enhanced_demo.py` - Full enhanced API demonstration
- `examples/nesting_demo.py` - Color nesting and priority examples

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick Start:**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests and pre-commit hooks: `pytest && pre-commit run --all-files`
5. Commit your changes: `git commit -m "feat: add amazing feature"`
6. Push and create a Pull Request

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and future direction.

**Upcoming features:**
- Configuration file support (.pipetintrc.yaml)
- Built-in color themes (log-levels, git-diff, python)
- TrueColor (24-bit RGB) support
- Pygments integration for syntax highlighting

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by the Ruby [colorize](https://github.com/fazibear/colorize) gem
- Built with modern Python best practices
- Designed for production safety and developer experience

---

## 🔄 Legacy API (Still Supported)

The original API remains fully supported for backward compatibility:

```python
from pipetint import Colorize, ColorizedString

# Original Colorize class
colorizer = Colorize()
print(colorizer.colorize("hello", "red"))

# Original ColorizedString
cs = ColorizedString("hello")
print(cs.colorize("blue"))
```

---

## 📊 Version Management

This project uses automated versioning via git tags:

- Versions are managed by `setuptools-scm` based on git tags
- `poetry-dynamic-versioning` integrates this with Poetry builds
- To release: `git tag v1.2.3 && git push --tags`
