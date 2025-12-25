"""HUD Module - MFD-style terminal interface components."""

import time
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.live import Live
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
    "primary": "#00FF00",  # Phosphor Green - main text/success
    "frame": "#33FF33",  # Bright Green - borders/frames
    "dim": "#005500",  # Dark Green - secondary/muted
    "warning": "#FFB000",  # Amber - caution states
    "error": "#FF0000",  # Red - alerts/errors
    "bg": "#000000",  # Black background
}

# Rich theme with MFD styles
MFD_THEME = Theme(
    {
        "hud": MFD_COLORS["primary"],
        "hud.frame": MFD_COLORS["frame"],
        "hud.dim": MFD_COLORS["dim"],
        "hud.warning": MFD_COLORS["warning"],
        "hud.error": MFD_COLORS["error"],
        "hud.bright": f"bold {MFD_COLORS['primary']}",
        "hud.title": f"bold {MFD_COLORS['frame']}",
    }
)

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


def hud_panel(content: str, title: Optional[str] = None, style: str = "hud", border_style: str = "hud.frame") -> Panel:
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
# MFD PROGRESS PANEL (PARALLEL BATCHES)
# ═══════════════════════════════════════════════════════════════════════════════


class MFDProgress:
    """MFD-style bracketed progress panel with parallel batch tracking."""

    # Batch status constants
    PENDING = 0
    ACTIVE = 1
    COMPLETE = 2

    def __init__(self, total_records: int, batch_size: int = 10):
        self.total_records = total_records
        self.batch_size = batch_size
        self.total_batches = (total_records + batch_size - 1) // batch_size
        self.records_completed = 0
        self._live: Optional[Live] = None
        self._start_time: Optional[float] = None
        self._first_complete_time: Optional[float] = None

        # Track each batch's status: 0=pending, 1=active, 2=complete
        self._batch_status: list[int] = [self.PENDING] * self.total_batches
        self._batch_records: list[int] = [0] * self.total_batches

    def _estimate_eta(self) -> str:
        """Estimate time remaining based on completion rate."""
        if not self._first_complete_time or not self._start_time:
            return "--:--"

        completed = sum(1 for s in self._batch_status if s == self.COMPLETE)
        if completed == 0:
            return "--:--"

        # Time from start to now
        elapsed = time.time() - self._start_time

        # Estimate based on completion rate
        remaining = self.total_batches - completed
        if completed > 0:
            time_per_batch = elapsed / completed
            remaining_seconds = remaining * time_per_batch
        else:
            return "--:--"

        # Format as MM:SS
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _render_batch_icons(self) -> Text:
        """Render batch status icons: ✓=complete, ◉=active, ○=pending."""
        icons = Text()
        for i, status in enumerate(self._batch_status):
            if status == self.COMPLETE:
                icons.append("[✓]", style="hud.bright")
            elif status == self.ACTIVE:
                icons.append("[◉]", style="hud.bright")
            else:
                icons.append("[○]", style="hud.dim")
        return icons

    def _render(self) -> Text:
        """Render the MFD progress panel."""
        box_width = 62
        inner_width = box_width - 4
        bar_width = 36

        # Calculate progress
        progress_pct = (self.records_completed / self.total_records * 100) if self.total_records > 0 else 0
        filled = int(bar_width * self.records_completed / self.total_records) if self.total_records > 0 else 0
        empty = bar_width - filled

        # Build progress bar
        bar = "▓" * filled + "░" * empty

        # Format numbers
        count_str = f"{self.records_completed:03d}/{self.total_records:03d}"
        pct_str = f"{int(progress_pct):3d}%"
        eta_str = self._estimate_eta()

        # Overall status
        if all(s == self.COMPLETE for s in self._batch_status):
            status = "CMPLT"
            status_style = "hud"
        elif any(s == self.ACTIVE for s in self._batch_status):
            status = "ACTIVE"
            status_style = "hud.bright"
        else:
            status = "STANDBY"
            status_style = "hud.dim"

        text = Text()

        # Top border
        text.append("╔" + "═" * (box_width - 2) + "╗\n", style="hud.frame")

        # Line 1: Label + Progress bar + Percentage
        line1_label = "REC GEN   "
        line1_end = f"   {pct_str}"
        bar_space = inner_width - len(line1_label) - len(line1_end)
        display_bar = bar[:bar_space] if len(bar) > bar_space else bar + " " * (bar_space - len(bar))

        text.append("║  ", style="hud.frame")
        text.append(line1_label, style="hud.bright")
        text.append(display_bar[:filled], style="hud.bright")
        text.append(display_bar[filled:], style="hud.dim")
        text.append(line1_end, style="hud.bright")
        text.append("║\n", style="hud.frame")

        # Line 2: Batch icons
        text.append("║  ", style="hud.frame")
        batch_icons = self._render_batch_icons()
        # Calculate padding
        icons_len = self.total_batches * 3  # Each icon is [X] = 3 chars
        padding2 = inner_width - icons_len
        text.append_text(batch_icons)
        text.append(" " * max(padding2, 0) + "║\n", style="hud.frame")

        # Line 3: Count, ETA, Status
        line3 = f"COUNT: {count_str}    ETA: {eta_str}  "
        status_text = f"[{status}]"
        padding3 = inner_width - len(line3) - len(status_text)

        text.append("║  ", style="hud.frame")
        text.append(line3, style="hud")
        text.append(" " * max(padding3, 0), style="hud")
        text.append(status_text, style=status_style)
        text.append("║\n", style="hud.frame")

        # Bottom border
        text.append("╚" + "═" * (box_width - 2) + "╝", style="hud.frame")

        return text

    def __enter__(self):
        """Start the live display."""
        self._start_time = time.time()
        self._live = Live(self._render(), console=console, refresh_per_second=4)
        self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the live display."""
        if self._live:
            self._live.__exit__(exc_type, exc_val, exc_tb)

    def start_batch(self, batch_idx: int):
        """Mark a batch as active (0-indexed)."""
        if 0 <= batch_idx < self.total_batches:
            self._batch_status[batch_idx] = self.ACTIVE
            self._update()

    def complete_batch(self, batch_idx: int, records_in_batch: int):
        """Mark a batch as complete and add to record count."""
        if 0 <= batch_idx < self.total_batches:
            self._batch_status[batch_idx] = self.COMPLETE
            self._batch_records[batch_idx] = records_in_batch
            self.records_completed = sum(self._batch_records)

            # Track first completion for ETA
            if self._first_complete_time is None:
                self._first_complete_time = time.time()

            self._update()

    def start_all(self):
        """Mark all batches as active (for parallel execution)."""
        self._batch_status = [self.ACTIVE] * self.total_batches
        self._update()

    def _update(self):
        """Update the live display."""
        if self._live:
            self._live.update(self._render())


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
