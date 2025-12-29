# mothilal-cli ✨

A fun command-line tool that displays names with style, animations, and flair!

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- 🎨 **ASCII Art Banners** - Beautiful text art with multiple fonts
- 💻 **Leetspeak Transform** - Convert names to hacker style (M0th!l@l)
- 🌈 **Rainbow Colors** - Colorful terminal output
- ⚡ **Cool Animations** - Typing effect, sparkles, matrix reveal, wave effect
- 🔗 **Website Display** - Show your website in a styled panel

## Installation

```bash
pip install mothilal-cli
```

Or install from source:

```bash
git clone https://github.com/mothilal/mothilal-cli.git
cd mothilal-cli
pip install -e .
```

## Usage

### Basic Usage

```bash
# Show the magic with default name (Mothilal)
mothilal greet

# Show with a custom name
mothilal greet YourName

# Show with custom website
mothilal greet --website https://yoursite.com
```

### Style Options

```bash
# Only leetspeak
mothilal greet --style leet

# Only ASCII art
mothilal greet --style ascii

# Only rainbow
mothilal greet --style rainbow

# Only fancy unicode
mothilal greet --style fancy

# All styles (default)
mothilal greet --style all
```

### Animation Control

```bash
# Disable animations (faster output)
mothilal greet --no-animate

# Enable animations (default)
mothilal greet --animate
```

### ASCII Art Fonts

```bash
# List available fonts
mothilal fonts

# Use a specific font
mothilal greet --font banner
mothilal greet --font big
mothilal greet --font slant
```

### Other Commands

```bash
# Show version
mothilal --version

# Show help
mothilal --help

# Show about info
mothilal about
```

## Example Output

```
    __  ___      __  __    _ __      __
   /  |/  /___  / /_/ /_  (_) /___ _/ /
  / /|_/ / __ \/ __/ __ \/ / / __ `/ / 
 / /  / / /_/ / /_/ / / / / / /_/ / /  
/_/  /_/\____/\__/_/ /_/_/_/\__,_/_/   

────────────────────────────────────────

Leetspeak style:
  → M0th!1@1

Fancy style:
  → 𝕄𝕠𝕥𝕙𝕚𝕝𝕒𝕝

Rainbow style:
  → M O T H I L A L

╭──────────── 🌐 Website ────────────╮
│       https://mothilal.xyz         │
╰────────────────────────────────────╯

         Made with ❤️ by Mothilal
```

## Development

```bash
# Clone the repo
git clone https://github.com/mothilal/mothilal-cli.git
cd mothilal-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Run the CLI
mothilal greet
```

## Publishing to PyPI

```bash
# Build the package
pip install build twine
python -m build

# Upload to TestPyPI (for testing)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Mothilal** - [https://mothilal.xyz](https://mothilal.xyz)

---

Made with ❤️ and Python
