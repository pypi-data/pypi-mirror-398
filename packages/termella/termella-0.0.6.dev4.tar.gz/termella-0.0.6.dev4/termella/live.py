import sys
import time
from .ansi import CURSOR_HIDE, CURSOR_SHOW, CURSOR_UP, CLEAR_EOS, CARRIAGE_RETURN
from .widgets import grid

class Live:
    """
    Context manager for live-updating terminal output.
    Prevents screen flickering by only overwriting the necessary lines.

    Usage:
        with Live() as live:
            while True:
                live.update(render_function())
                time.sleep(1)
    """
    def __init__(self, refresh=None, auto_refresh=None):
        self.last_height = 0
        self.refresh = refresh
        if auto_refresh is None:
            self.auto_refresh = (refresh is not None)
        else:
            self.auto_refresh = auto_refresh

        self.is_running = False

    def start(self):
        self.is_running = True
        try:
            sys.stdout.write(CURSOR_HIDE)
            sys.stdout.flush()
        except Exception: pass

    def stop(self):
        self.is_running = False
        try:
            sys.stdout.write(CURSOR_SHOW)
            sys.stdout.write("\n")
            sys.stdout.flush()
        except Exception: pass

    def update(self, renderable):
        """
        Replaces the previous output with the new renderable.
        Args:
            renderable (str): The multi-line string to display.
        """
        if isinstance(renderable, (list, tuple)):
            text = grid(renderable, cols=1, render=True)
        else:
            text = str(renderable)

        if text.endswith('\n'):
            text = text.rstrip('\n')
            
        lines = text.split('\n')
        new_height = len(lines)

        if self.last_height > 0:
            sys.stdout.write(CURSOR_UP * self.last_height)
            sys.stdout.write(CARRIAGE_RETURN)

        sys.stdout.write(CLEAR_EOS)
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

        self.last_height = new_height
        
        if self.auto_refresh and self.refresh:
            time.sleep(self.refresh)

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False