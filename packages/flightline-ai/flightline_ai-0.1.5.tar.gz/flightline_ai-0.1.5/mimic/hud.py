"""HUD Module - MFD-style terminal interface components."""

from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.text import Text
from rich.theme import Theme

# ═══════════════════════════════════════════════════════════════════════════════
# MFD COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

MFD_COLORS = {
    "primary": "#00FF00",      # Phosphor Green - main text/success
    "frame": "#33FF33",        # Bright Green - borders/frames
    "dim": "#005500",          # Dark Green - secondary/muted
    "warning": "#FFB000",      # Amber - caution states
    "error": "#FF0000",        # Red - alerts/errors
    "bg": "#000000",           # Black background
}

# Rich theme with MFD styles
MFD_THEME = Theme({
    "hud": MFD_COLORS["primary"],
    "hud.frame": MFD_COLORS["frame"],
    "hud.dim": MFD_COLORS["dim"],
    "hud.warning": MFD_COLORS["warning"],
    "hud.error": MFD_COLORS["error"],
    "hud.bright": f"bold {MFD_COLORS['primary']}",
    "hud.title": f"bold {MFD_COLORS['frame']}",
})

# Create console with MFD theme
console = Console(theme=MFD_THEME)


# ═══════════════════════════════════════════════════════════════════════════════
# ASCII ART ASSETS
# ═══════════════════════════════════════════════════════════════════════════════

# Flightline company logo - targeting reticle
FLIGHTLINE_LOGO = r"""
                            ║
                            ║
                       ╔════╩════╗
                       ║         ║
            ═══════════╣         ╠═══════════
                       ║         ║
                       ╚═════════╝
"""

FLIGHTLINE_BANNER = r"""
███████╗██╗     ██╗ ██████╗ ██╗  ██╗████████╗██╗     ██╗███╗   ██╗███████╗
██╔════╝██║     ██║██╔════╝ ██║  ██║╚══██╔══╝██║     ██║████╗  ██║██╔════╝
█████╗  ██║     ██║██║  ███╗███████║   ██║   ██║     ██║██╔██╗ ██║█████╗  
██╔══╝  ██║     ██║██║   ██║██╔══██║   ██║   ██║     ██║██║╚██╗██║██╔══╝  
██║     ███████╗██║╚██████╔╝██║  ██║   ██║   ███████╗██║██║ ╚████║███████╗
╚═╝     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝
"""


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def mil_time() -> str:
    """Return current time in Zulu format (e.g., '1435Z')."""
    now = datetime.now(timezone.utc)
    return now.strftime("%H%MZ")


def waypoint(num: int) -> str:
    """Return step designator (e.g., 'WP01')."""
    return f"WP{num:02d}"


def status_indicator(status: str) -> Text:
    """
    Return a styled status indicator badge.
    
    Supported statuses: RDY, ACT, CMPLT, WARN, ERR, STANDBY
    """
    status_styles = {
        "RDY": ("hud", "◉"),
        "ACT": ("hud.bright", "◉"),
        "CMPLT": ("hud", "◉"),
        "WARN": ("hud.warning", "◉"),
        "ERR": ("hud.error", "◉"),
        "STANDBY": ("hud.dim", "○"),
    }
    
    style, indicator = status_styles.get(status.upper(), ("hud", "◉"))
    return Text(f"{indicator} [{status.upper()}]", style=style)


def hud_line(char: str = "─", width: int = 60) -> str:
    """Return a horizontal line for HUD borders."""
    return char * width


# ═══════════════════════════════════════════════════════════════════════════════
# HUD COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def print_boot_sequence(command: str = ""):
    """Display the boot sequence with Flightline branding."""
    
    # Company logo
    console.print(FLIGHTLINE_LOGO, style="hud.frame")
    
    # FLIGHTLINE banner
    console.print(FLIGHTLINE_BANNER, style="hud.bright")
    
    # Command info line
    if command:
        console.print(f"                              flightline {command.lower()}", style="hud.dim")
    console.print()
    
    # System info line
    time_str = mil_time()
    
    # Build header content with fixed-width formatting
    box_width = 64
    inner_width = box_width - 4  # Account for ║ and spaces on each side
    
    header = Text()
    header.append("╔" + "═" * (box_width - 2) + "╗\n", style="hud.frame")
    
    # Line 1: System title
    line1 = "SYNTHETIC DATA GENERATOR"
    padding1 = inner_width - len(line1)
    header.append("║  ", style="hud.frame")
    header.append(line1, style="hud.bright")
    header.append(" " * padding1 + "║\n", style="hud.frame")
    
    # Line 2: Command
    if command:
        line2 = f"COMMAND: {command.upper()}"
    else:
        line2 = "FLIGHTLINE CLI"
    padding2 = inner_width - len(line2)
    header.append("║  ", style="hud.frame")
    header.append(line2, style="hud")
    header.append(" " * padding2 + "║\n", style="hud.frame")
    
    # Line 3: Status and time
    status_str = f"[SYS RDY] {time_str}"
    padding3 = inner_width - len(status_str)
    header.append("║  ", style="hud.frame")
    header.append(" " * padding3, style="hud")
    header.append(status_str, style="hud.dim")
    header.append("║\n", style="hud.frame")
    
    header.append("╚" + "═" * (box_width - 2) + "╝", style="hud.frame")
    
    console.print(header)
    console.print()


def hud_panel(
    content: str,
    title: Optional[str] = None,
    style: str = "hud",
    border_style: str = "hud.frame"
) -> Panel:
    """Create an MFD-style panel."""
    return Panel(
        Text(content.upper(), style=style),
        title=f"┤ {title.upper()} ├" if title else None,
        title_align="left",
        border_style=border_style,
        padding=(0, 1),
    )


def print_target(label: str, value: str, wp_num: Optional[int] = None):
    """Print a data readout line."""
    prefix = f"{waypoint(wp_num)} " if wp_num else "     "
    
    text = Text()
    text.append(prefix, style="hud.dim")
    text.append("─╼ ", style="hud.frame")
    text.append(f"{label.upper()}: ", style="hud")
    text.append(value.upper(), style="hud.bright")
    
    console.print(text)


def print_status(message: str, status: str = "ACT"):
    """Print a status line with indicator."""
    text = Text()
    text.append("     STATUS: ", style="hud")
    text.append_text(status_indicator(status))
    text.append(f" {message.upper()}", style="hud")
    
    console.print(text)


def print_info(message: str):
    """Print an info message in HUD style."""
    text = Text()
    text.append("     ", style="hud")
    text.append("► ", style="hud.frame")
    text.append(message.upper(), style="hud")
    console.print(text)


def print_warning(message: str):
    """Print a warning message in amber."""
    text = Text()
    text.append("     ", style="hud")
    text.append("⚠ WARNING: ", style="hud.warning")
    text.append(message.upper(), style="hud.warning")
    console.print(text)


def print_error(message: str):
    """Print an error message in red."""
    text = Text()
    text.append("     ", style="hud")
    text.append("✖ ERROR: ", style="hud.error")
    text.append(message.upper(), style="hud.error")
    console.print(text)


def print_success(message: str):
    """Print a success message."""
    text = Text()
    text.append("     ", style="hud")
    text.append("◉── ", style="hud.bright")
    text.append(message.upper(), style="hud.bright")
    console.print(text)


def print_complete(results: dict):
    """Print the completion summary screen."""
    console.print()
    
    # Build complete box
    box_width = 52
    inner_width = box_width - 4
    
    text = Text()
    text.append("┌" + "─" * (box_width - 2) + "┐\n", style="hud.frame")
    
    # Title line
    title = "◉──◉ DONE ◉──◉"
    title_padding = inner_width - len(title)
    text.append("│  ", style="hud.frame")
    text.append(title, style="hud.bright")
    text.append(" " * title_padding + "│\n", style="hud.frame")
    
    # Separator
    text.append("│  " + "─" * inner_width + "│\n", style="hud.frame")
    
    # Print each result
    for key, value in results.items():
        line = f"{key.upper()}: {str(value).upper()}"
        padding = inner_width - len(line)
        text.append("│  ", style="hud.frame")
        text.append(line, style="hud")
        text.append(" " * max(padding, 0) + "│\n", style="hud.frame")
    
    # Status and timestamp
    status_line = f"[CMPLT] {mil_time()}"
    status_padding = inner_width - len(status_line)
    text.append("│  ", style="hud.frame")
    text.append(" " * status_padding, style="hud")
    text.append(status_line, style="hud.dim")
    text.append("│\n", style="hud.frame")
    
    text.append("└" + "─" * (box_width - 2) + "┘", style="hud.frame")
    
    console.print(text)


def create_progress(description: str = "PROCESSING") -> Progress:
    """Create a styled progress bar."""
    return Progress(
        TextColumn("[hud]     "),
        SpinnerColumn("dots", style="hud.bright"),
        TextColumn("[hud.bright]{task.description}"),
        BarColumn(
            bar_width=30,
            style="hud.dim",
            complete_style="hud.bright",
            finished_style="hud",
        ),
        TaskProgressColumn(style="hud"),
        console=console,
        transient=True,
    )


def create_status_spinner(message: str = "PROCESSING"):
    """Create a status context manager for indeterminate operations."""
    return console.status(
        f"[hud.bright]◉ {message.upper()}[/hud.bright]",
        spinner="dots",
        spinner_style="hud.bright",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK PRINTS
# ═══════════════════════════════════════════════════════════════════════════════

def hud_print(message: str, style: str = "hud"):
    """Basic HUD-style print."""
    console.print(message.upper(), style=style)


def hud_rule(title: Optional[str] = None):
    """Print a horizontal rule with optional title."""
    if title:
        console.rule(title.upper(), style="hud.frame", characters="─")
    else:
        console.print(hud_line(), style="hud.frame")
