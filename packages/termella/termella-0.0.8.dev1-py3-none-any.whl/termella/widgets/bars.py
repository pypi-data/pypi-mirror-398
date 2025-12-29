import sys
from ..core import Text
from ..ansi import CURSOR_HIDE, CURSOR_SHOW

def progress_bar(iteration, total, length=30, color="green", fill="█", empty="-"):
    """
    [New in v0.0.2a] Prints a progress bar to the console.
    """
    if total == 0: total = 1
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)

    filled = str(Text(fill * filled_length).style(color))
    unfilled = empty * (length - filled_length)

    # Use carriage return \r to stay on the same line
    sys.stdout.write(f'{CURSOR_HIDE}\r{filled}{unfilled} {percent}%')
    sys.stdout.flush()

    if iteration >= total:
        sys.stdout.write(f'{CURSOR_SHOW}\n')