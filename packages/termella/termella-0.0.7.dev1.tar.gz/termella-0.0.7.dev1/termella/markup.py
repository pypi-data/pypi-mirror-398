import re
from .core import Text
from .ansi import COLORS, BG_COLORS, STYLES

TAG_RE = re.compile(r'\[([\w\s]+)\](.*?)\[/\]')

def parse(text):
    """
    Parses a string with inline markup tags a styled Text object.

    Example:
        parse("Hello [red]World[/]!")

    Limitations (dev0):
        - No nested tags yet (e.g. [red][bold]Hi[/][/])
    """
    final_text = Text("")
    last_pos = 0

    for match in TAG_RE.finditer(text):
        start, end = match.span()
        if start > last_pos:
            final_text += Text(text[last_pos:start])

        tag_str = match.group(1)
        content = match.group(2)

        args = tag_str.split()

        c_val = None
        bg_val = None
        s_vals = []
        
        for arg in args:
            if arg in COLORS:
                c_val = arg
            elif arg in BG_COLORS:
                bg_val = arg
            elif arg in STYLES:
                s_vals.append(arg)

        styled_chunk = Text(content).style(color=c_val, bg=bg_val, styles=s_vals)
        final_text += styled_chunk

        last_pos = end

    if last_pos < len(text):
        final_text += Text(text[last_pos:])

    return final_text

def print_tag(text, end="\n"):
    """
    Helper to parse and print immediately.
    """
    t = parse(text)
    print(t, end=end)