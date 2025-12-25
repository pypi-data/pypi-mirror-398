from typing import Any, TypeAlias

# --- Type Definitions ---
AnsiCode: TypeAlias = str
StyleCode: TypeAlias = AnsiCode  # e.g. BOLD, UNDERLINE
ShadeCode: TypeAlias = AnsiCode  # e.g. GREEN, BLUE
ColorCode: TypeAlias = AnsiCode  # Final combined result


class Color:
    """Raw ANSI escape codes. Internal building blocks for the library."""

    RESET: AnsiCode = "\033[0m"

    # Styles (Combinable)
    BOLD: StyleCode = "\033[1m"
    UNDERLINE: StyleCode = "\033[4m"

    # --- THE 14 PROTECTED SHADES ---
    # Standard (Deeper tones)
    S_GREEN: ShadeCode = "\033[32m"
    S_BLUE: ShadeCode = "\033[34m"
    S_PURPLE: ShadeCode = "\033[35m"
    S_CYAN: ShadeCode = "\033[36m"
    S_WHITE: ShadeCode = "\033[37m"

    # High-Intensity (Vibrant tones)
    H_GREY: ShadeCode = "\033[90m"
    H_GREEN: ShadeCode = "\033[92m"
    H_BLUE: ShadeCode = "\033[94m"
    H_PURPLE: ShadeCode = "\033[95m"
    H_CYAN: ShadeCode = "\033[96m"
    H_WHITE: ShadeCode = "\033[97m"

    # Extended Palette
    TEAL: ShadeCode = "\033[38;5;30m"
    LAVENDER: ShadeCode = "\033[38;5;147m"
    OLIVE: ShadeCode = "\033[38;5;64m"


def combine(*codes: AnsiCode) -> ColorCode:
    """Combines multiple ANSI codes (e.g., BOLD + GREEN)."""
    return "".join(codes)


class SystemColor:
    """
    RESERVED: For core library internals.
    Strictly BOLD or UNDERLINED to distinguish from scraper data.
    """

    # Verbs / Actions (BOLD)
    BATCH_PIPELINE_STATS: ColorCode = combine(Color.BOLD, Color.H_PURPLE)

    # State / Nouns (UNDERLINED)
    PROCESS_BATCH_PROGRESS: ColorCode = combine(Color.UNDERLINE, Color.S_CYAN)


class ScraperColor:
    """
    USER-FACING: Standard colors for everyday scraper logic.
    Raw shades only. It is up to the user how to apply these.
    """

    GREY: ShadeCode = Color.H_GREY
    EMERALD: ShadeCode = Color.H_GREEN
    FOREST: ShadeCode = Color.S_GREEN
    SKY: ShadeCode = Color.H_BLUE
    NAVY: ShadeCode = Color.S_BLUE
    VIOLET: ShadeCode = Color.H_PURPLE
    PLUM: ShadeCode = Color.S_PURPLE
    CYAN: ShadeCode = Color.H_CYAN
    TEAL: ShadeCode = Color.S_CYAN
    WHITE: ShadeCode = Color.H_WHITE
    SILVER: ShadeCode = Color.S_WHITE
    LAVENDER: ShadeCode = Color.LAVENDER
    OLIVE: ShadeCode = Color.OLIVE


def colorize(text: Any, color_code: ColorCode) -> str:
    """
    Wraps text in ANSI color codes.

    Args:
        text: The content to colorize (supports any type).
        color_code: A ShadeCode, StyleCode, or combined ColorCode.
    """
    return f"{color_code}{text}{Color.RESET}"
