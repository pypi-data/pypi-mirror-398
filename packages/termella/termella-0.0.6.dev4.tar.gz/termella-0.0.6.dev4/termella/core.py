import re
from .ansi import COLORS, BG_COLORS, STYLES, RESET

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def visible_len(s):
    """Returns the length of the string without ANSI codes."""
    return len(ANSI_ESCAPE.sub('', str(s)))

class Text:
    """Represents a styled string."""
    def __init__(self, content):
        self.content = str(content)
        self._codes = []

    def style(self, color=None, bg=None, styles=None):
        """Apply styles to the text object."""
        if color in COLORS: self._codes.append(COLORS[color])
        if bg in BG_COLORS: self._codes.append(BG_COLORS[bg])
        if styles:
            if isinstance(styles, str): styles = [styles]
            for s in styles:
                if s in STYLES: self._codes.append(STYLES[s])
        return self
    
    def __str__(self):
        """Render the final ANSI string."""
        if not self._codes: return self.content
        return f"\033[{';'.join(self._codes)}m{self.content}{RESET}"
    
    def __add__(self, other):
        return str(self) + str(other)