import re
from .core import Text
from .ansi import COLORS, BG_COLORS, STYLES, rgb_fg, rgb_bg, link_start, link_end

# Use raw string for regex pattern
TAG_RE = re.compile(r'(?<!\\)\[(.*?)(?<!\\)\]')

THEME = {
    "error": "red bold",
    "warn": "yellow",
    "info": "cyan",
    "success": "green bold"
}

def add_alias(name, style_str):
    """
    Registers a custom tag alias.
    Usage: add_alias("alert", "white bg_red bold")
    """
    THEME[name] = style_str

def unescape(s):
    r"""
    Replaces \[ with [ and \] with ].
    """
    # Use raw strings for the replacement arguments
    return s.replace(r'\[', '[').replace(r'\]', ']')

def parse(text):
    """
    Parses nested markup tags with escape support.
    """
    if "[" not in text: return Text(unescape(text))
    parts = TAG_RE.split(text)
    
    final_output = Text("")
    style_stack = [] 

    def apply_tag(chunk, tag_str):
        if not tag_str: return

        if tag_str.startswith("link="):
            url = tag_str[5:]
            chunk.add_raw_code(link_start(url))
            chunk.add_raw_suffix(link_end())
            return

        if tag_str.startswith("rgb("):
            try:
                content = tag_str[4:-1]
                r, g, b = map(int, content.split(','))
                chunk.add_raw_code(rgb_fg(r, g, b))
                return
            except: pass
        elif tag_str.startswith("bg_rgb("):
            try:
                content = tag_str[7:-1]
                r, g, b = map(int, content.split(','))
                chunk.add_raw_code(rgb_bg(r, g, b))
                return
            except: pass

        style_def = THEME.get(tag_str, tag_str)
        tokens = style_def.split()
        for token in tokens:
            if token in COLORS: chunk.style(color=token)
            elif token in BG_COLORS: chunk.style(bg=token)
            elif token in STYLES: chunk.style(styles=token)

    for i, part in enumerate(parts):
        if i % 2 == 0:
            if not part: continue
            clean_text = unescape(part)
            chunk = Text(clean_text)

            for tag in style_stack:
                apply_tag(chunk, tag)

            final_output += chunk
        else:
            tag = part.strip().replace(r'\[', '[').replace(r'\]', ']')
            if tag == "/":
                if style_stack: style_stack.pop()
            else:
                style_stack.append(tag)
                
    return final_output

def print_tag(text, end="\n"):
    t = parse(text)
    print(t, end=end)