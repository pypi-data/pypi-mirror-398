"""Main CLI application for Mothilal CLI."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

from . import __version__, __website__
from .transforms import to_leetspeak, to_fancy, to_spaced
from .effects import (
    typing_effect,
    rainbow_text,
    print_ascii_art,
    sparkle_animation,
    print_website_panel,
    print_divider,
    matrix_reveal,
    wave_animation,
)


app = typer.Typer(
    name="mothilal",
    help="✨ A fun CLI that displays names with style and animations!",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold cyan]mothilal-cli[/bold cyan] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    ✨ Mothilal CLI - Display names with style and animations!
    
    Run 'mothilal' to see the magic, or 'mothilal --help' for options.
    """
    pass


@app.command()
def greet(
    name: str = typer.Argument(
        "Mothilal",
        help="Name to display with style",
    ),
    website: str = typer.Option(
        "https://mothilal.xyz",
        "--website", "-w",
        help="Website URL to display",
    ),
    style: str = typer.Option(
        "all",
        "--style", "-s",
        help="Style to use: leet, fancy, rainbow, ascii, all",
    ),
    animate: bool = typer.Option(
        True,
        "--animate/--no-animate", "-a/-A",
        help="Enable/disable animations",
    ),
    font: str = typer.Option(
        "slant",
        "--font", "-f",
        help="ASCII art font (slant, banner, big, standard, etc.)",
    ),
) -> None:
    """
    🎨 Display a name with stylish text and cool animations!
    
    Examples:
        mothilal greet
        mothilal greet John --style leet
        mothilal greet --no-animate --style ascii
    """
    console.print()
    
    # ASCII Art Banner
    if style in ("ascii", "all"):
        print_ascii_art(name, font=font, color="magenta")
    
    # Divider
    if animate:
        print_divider()
    
    # Leetspeak version
    if style in ("leet", "all"):
        leet_name = to_leetspeak(name)
        if animate:
            console.print()
            console.print("[dim]Leetspeak style:[/dim]")
            typing_effect(f"  → {leet_name}", delay=0.04, style="bold green")
        else:
            console.print(f"[dim]Leetspeak:[/dim] [bold green]{leet_name}[/bold green]")
    
    # Fancy unicode version
    if style in ("fancy", "all"):
        fancy_name = to_fancy(name)
        if animate:
            console.print()
            console.print("[dim]Fancy style:[/dim]")
            typing_effect(f"  → {fancy_name}", delay=0.04, style="bold blue")
        else:
            console.print(f"[dim]Fancy:[/dim] [bold blue]{fancy_name}[/bold blue]")
    
    # Rainbow version
    if style in ("rainbow", "all"):
        console.print()
        console.print("[dim]Rainbow style:[/dim]")
        spaced_name = to_spaced(name.upper())
        rainbow = rainbow_text(f"  → {spaced_name}")
        console.print(rainbow)
    
    # Sparkle animation
    if animate and style == "all":
        console.print()
        console.print("[dim]Sparkle animation:[/dim]")
        sparkle_animation(name)
    
    # Matrix reveal
    if animate and style == "all":
        console.print()
        console.print("[dim]Matrix reveal:[/dim]")
        console.print("  → ", end="")
        matrix_reveal(name.upper())
    
    # Wave animation
    if animate and style == "all":
        console.print()
        console.print("[dim]Wave effect:[/dim]")
        console.print("  → ", end="")
        wave_animation(name)
    
    # Divider before website
    console.print()
    if animate:
        print_divider()
    
    # Website panel
    print_website_panel(website)
    
    # Footer
    console.print()
    footer = Text()
    footer.append("Made with ", style="dim")
    footer.append("❤️", style="red")
    footer.append(" by ", style="dim")
    footer.append(name, style="bold cyan")
    console.print(Align.center(footer))
    console.print()


@app.command()
def about() -> None:
    """📖 Show information about Mothilal."""
    from rich.table import Table
    from rich.columns import Columns
    
    console.print()
    
    # ASCII Art Header
    print_ascii_art("Mothilal", font="slant", color="cyan")
    
    # Bio Panel
    bio_text = """[bold white]Software Engineer[/bold white] crafting innovative digital experiences at [bold cyan]10xscale.ai[/bold cyan]
Passionate about clean code, scalable architecture, and cutting-edge technology.

[dim]📍 Dharmapuri, Tamil Nadu, India[/dim]"""
    
    bio_panel = Panel(
        bio_text,
        title="👨‍💻 About Me",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(bio_panel)
    
    # Professional Journey
    journey_text = """[bold yellow]💼 Software Engineer[/bold yellow] @ [bold cyan]10XScale.ai[/bold cyan]
[dim]August 2024 - Present | Hyderabad[/dim]

Building scalable backend systems and cloud infrastructure.
Working with Python, FastAPI, Docker, and Google Cloud Platform.

[bold yellow]🎓 B.Sc Computer Science[/bold yellow]
[dim]Government Arts College, Coimbatore (2021-2024)[/dim]"""
    
    journey_panel = Panel(
        journey_text,
        title="🚀 Professional Journey",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(journey_panel)
    
    # Skills Table
    skills_table = Table(show_header=True, header_style="bold magenta", border_style="magenta")
    skills_table.add_column("Backend", style="green")
    skills_table.add_column("Frontend", style="blue")
    skills_table.add_column("Cloud/DevOps", style="yellow")
    skills_table.add_column("AI & Tools", style="cyan")
    
    skills_table.add_row(
        "Python\nFastAPI\nPHP\nMySQL\nPostgreSQL",
        "JavaScript\nTypeScript\njQuery\nHTML5/CSS3",
        "GCP\nCloud Run\nDocker\nCI/CD",
        "GitHub Copilot\nLLM Tooling\nLangGraph\nRedis"
    )
    
    skills_panel = Panel(skills_table, title="⚡ Tech Stack", border_style="magenta")
    console.print(skills_panel)
    
    # Projects
    projects_text = """[bold cyan]🎓 College Admission Seat Matrix[/bold cyan]
   PHP-based web app for seat distribution automation

[bold cyan]💼 Portfolio Website[/bold cyan]
   Modern, responsive portfolio - [link=https://mothilal.xyz]mothilal.xyz[/link]

[bold cyan]🧠 10xMindPlay[/bold cyan]
   Cognitive training platform - [link=https://10xmindplay.mothilal.xyz]10xmindplay.mothilal.xyz[/link]"""
    
    projects_panel = Panel(
        projects_text,
        title="🛠️ Featured Projects",
        border_style="green",
        padding=(1, 2),
    )
    console.print(projects_panel)
    
    # Contact Info
    contact_text = """[bold]📧 Email:[/bold]    mothilal044@gmail.com
[bold]📱 Phone:[/bold]    +91 9787962328
[bold]💼 LinkedIn:[/bold] [link=https://www.linkedin.com/in/mothilal-m-04803a227]linkedin.com/in/mothilal-m[/link]
[bold]🌐 Website:[/bold]  [link=https://mothilal.xyz]mothilal.xyz[/link]"""
    
    contact_panel = Panel(
        contact_text,
        title="📬 Get In Touch",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(contact_panel)
    
    # Beyond Code
    hobbies = Text()
    hobbies.append("🎮 Gaming  ", style="bold red")
    hobbies.append("♟️ Chess  ", style="bold yellow")
    hobbies.append("📚 Reading  ", style="bold green")
    hobbies.append("🔬 Tech Exploration", style="bold cyan")
    
    hobbies_panel = Panel(
        Align.center(hobbies),
        title="🎯 Beyond Code",
        border_style="red",
        padding=(0, 2),
    )
    console.print(hobbies_panel)
    
    # Footer
    console.print()
    footer = Text()
    footer.append("✨ Available for opportunities ✨", style="bold green")
    console.print(Align.center(footer))
    console.print()


@app.command()
def fonts() -> None:
    """🔤 List available ASCII art fonts."""
    import pyfiglet
    
    console.print("\n[bold cyan]Available ASCII Art Fonts:[/bold cyan]\n")
    
    # Show a few popular fonts with examples
    popular_fonts = ["slant", "banner", "big", "standard", "small", "mini", "digital"]
    
    for font in popular_fonts:
        try:
            console.print(f"[dim]Font: {font}[/dim]")
            art = pyfiglet.figlet_format("Hi!", font=font)
            console.print(art, style="green")
        except Exception:
            console.print(f"[dim](font '{font}' not available)[/dim]")
    
    console.print("[dim]Use --font <name> with the greet command[/dim]\n")


# Default command - run greet with defaults when no command specified
if __name__ == "__main__":
    app()
