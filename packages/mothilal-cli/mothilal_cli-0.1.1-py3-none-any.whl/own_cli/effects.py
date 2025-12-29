"""Animation and visual effects for terminal output."""

import time
import random
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
import pyfiglet


console = Console()

# Rainbow colors for cycling
RAINBOW_COLORS = ["red", "orange1", "yellow", "green", "cyan", "blue", "magenta"]

# Sparkle characters for animation
SPARKLES = ["✨", "⭐", "🌟", "💫", "✦", "★", "☆"]


def typing_effect(text: str, delay: float = 0.03, style: str = "bold cyan") -> None:
    """Print text character by character with a typing animation."""
    for char in text:
        console.print(char, end="", style=style)
        time.sleep(delay)
    console.print()  # newline


def rainbow_text(text: str) -> Text:
    """Create rainbow-colored text."""
    styled = Text()
    for i, char in enumerate(text):
        color = RAINBOW_COLORS[i % len(RAINBOW_COLORS)]
        styled.append(char, style=f"bold {color}")
    return styled


def print_ascii_art(text: str, font: str = "slant", color: str = "magenta") -> None:
    """Print ASCII art banner for the given text."""
    try:
        ascii_art = pyfiglet.figlet_format(text, font=font)
        console.print(ascii_art, style=f"bold {color}")
    except Exception:
        # Fallback if font not available
        ascii_art = pyfiglet.figlet_format(text, font="standard")
        console.print(ascii_art, style=f"bold {color}")


def sparkle_animation(text: str, duration: float = 1.5) -> None:
    """Display text with sparkle animation around it."""
    frames = int(duration / 0.1)
    
    for _ in range(frames):
        left_sparkle = random.choice(SPARKLES)
        right_sparkle = random.choice(SPARKLES)
        color = random.choice(RAINBOW_COLORS)
        
        styled_text = Text()
        styled_text.append(f" {left_sparkle} ", style=f"bold {color}")
        styled_text.append(text, style="bold white")
        styled_text.append(f" {right_sparkle} ", style=f"bold {color}")
        
        console.print(styled_text, end="\r")
        time.sleep(0.1)
    
    # Final static version
    console.print(f" ✨ {text} ✨ ", style="bold yellow")


def wave_animation(text: str, waves: int = 2) -> None:
    """Display text with a wave effect."""
    for wave in range(waves):
        for i in range(len(text) + 1):
            styled = Text()
            for j, char in enumerate(text):
                if j < i:
                    styled.append(char, style="bold cyan")
                else:
                    styled.append(char, style="dim white")
            console.print(styled, end="\r")
            time.sleep(0.05)
    console.print()


def print_website_panel(url: str, title: str = "🌐 Website") -> None:
    """Display website URL in a styled panel."""
    panel = Panel(
        Align.center(f"[bold cyan link={url}]{url}[/bold cyan link]"),
        title=title,
        border_style="blue",
        padding=(0, 2),
    )
    console.print(panel)


def print_divider(char: str = "─", style: str = "dim cyan") -> None:
    """Print a horizontal divider line."""
    width = console.size.width
    console.print(char * width, style=style)


def matrix_reveal(text: str, duration: float = 1.0) -> None:
    """Reveal text with a matrix-style random character effect."""
    chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    result = list(" " * len(text))
    revealed = [False] * len(text)
    
    steps = int(duration / 0.05)
    reveals_per_step = max(1, len(text) // steps)
    
    for step in range(steps + len(text)):
        # Reveal some characters
        unrevealed = [i for i, r in enumerate(revealed) if not r]
        to_reveal = random.sample(unrevealed, min(reveals_per_step, len(unrevealed))) if unrevealed else []
        
        for i in to_reveal:
            revealed[i] = True
            result[i] = text[i]
        
        # Random characters for unrevealed positions
        for i, r in enumerate(revealed):
            if not r:
                result[i] = random.choice(chars)
        
        styled = Text()
        for i, char in enumerate(result):
            if revealed[i]:
                styled.append(char, style="bold green")
            else:
                styled.append(char, style="dim green")
        
        console.print(styled, end="\r")
        time.sleep(0.05)
        
        if all(revealed):
            break
    
    console.print()
