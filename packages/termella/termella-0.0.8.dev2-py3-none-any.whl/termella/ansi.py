"""
termella.ansi
Definitions for ANSI escape codes.
"""

RESET = "\033[0m"

# Cursor Controls (New in v0.0.2b)
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"

# Navigation (New in v0.0.4a)
CURSOR_UP = "\033[A"
CURSOR_DOWN = "\033[B"
CLEAR_LINE = "\033[2K"

def link_start(url):
    return f"\033]8;;{url}\033\\"

def link_end():
    return "\033]8;;\033\\"

def rgb_fg(r, g, b):
    return f"38;2;{r};{g};{b}"

def rgb_bg(r, g, b):
    return f"48;2;{r};{g};{b}"

COLORS = {
    "black": "30", "red": "31", "green": "32", "yellow": "33",
    "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
    "bright_red": "91", "bright_green": "92", "bright_blue": "94",
}

BG_COLORS = {
    "bg_black": "40", "bg_red": "41", "bg_green": "42",
    "bg_blue": "44", "bg_white": "47",
}

STYLES = {
    "bold": "1", "dim": "2", "italic": "3",
    "underline": "4", "blink": "5", "reverse": "7",
}

CARRIAGE_RETURN = "\r"
CLEAR_EOS = "\033[J"

# Screen Buffer Controls (New in v0.0.8)
ALT_SCREEN_ENTER = "\033[?1049h"
ALT_SCREEN_EXIT = "\033[?1049l"
CLEAR_SCREEN = "\033[2J\033[H"