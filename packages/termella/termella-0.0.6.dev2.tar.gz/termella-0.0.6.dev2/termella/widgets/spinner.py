import sys
import time
import threading
from ..ansi import CURSOR_HIDE, CURSOR_SHOW, COLORS

class Spinner:
    """
    A context manager for a loading spinner.
    Usage:
        with Spinner("Loading..."):
            time.sleep(2)
    """
    def __init__(self, message="Loading...", delay=0.1):
        self.message = message
        self.delay = delay
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self.thread = None

    def _spin(self):
        idx = 0
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r{CURSOR_HIDE}\033[{COLORS['cyan']}m{frame}\033[0m {self.message}")
            sys.stdout.flush()
            idx += 1
            time.sleep(self.delay)

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write(f"\r{CURSOR_SHOW}")
        if exc_type:
            sys.stdout.write(f"\033[{COLORS['red']}m✖ {self.message} Failed!\033[0m\n")
        else:
            sys.stdout.write(f"\033[{COLORS['green']}m✔ {self.message} Done.\033[0m\n")
        sys.stdout.flush()
        return False