import sys
from .core import Text
from .ansi import CURSOR_SHOW, CURSOR_HIDE

def panel(text, color="white", title=None):
    """
    Creates a simple ASCII box around text.
    """
    text = str(text)
    lines = text.split("\n")
    width = max(len(line) for line in lines) + 2
    tl, tr, bl, br, h, v= "┌", "┐", "└", "┘", "─", "│"

    t_str = f" {title} " if title else ""
    top = h * (width - len(t_str))

    print(Text(f"{tl}{t_str}{top}{tr}").style(color))
    for line in lines:
        print(Text(f"{v}{line.ljust(width)}{v}").style(color))
    print(Text(f"{bl}{h * width}{br}").style(color))

def progress_bar(iteration, total, length=30, color="green", fill="█", empty="-"):
    """
    [New in v0.0.2a] Prints a progress bar to the console.
    """
    if total == 0:
        total = 1

    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)

    filled = str(Text(fill * filled_length).style(color))
    unfilled = empty * (length - filled_length)

    # Use carriage return \r to stay on the same line
    sys.stdout.write(f'{CURSOR_HIDE}\r{filled}{unfilled} {percent}%')
    sys.stdout.flush()

    if iteration >= total:
        sys.stdout.write(f'{CURSOR_SHOW}\n')