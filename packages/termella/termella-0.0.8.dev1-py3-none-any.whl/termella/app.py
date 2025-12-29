import sys
import time
from .ansi import (
    ALT_SCREEN_ENTER, ALT_SCREEN_EXIT,
    CURSOR_HIDE, CURSOR_SHOW,
    CLEAR_SCREEN, CARRIAGE_RETURN
)
from .widgets import grid

class App:
    """
    Base class for Full-Screen TUI Applications.
    Handles the Event Loop and Screen Buffer management.
    """
    def __init__(self, refresh_rate=0.1):
        self._running = False
        self.refresh_rate = refresh_rate

    def on_start(self):
        """Override this to run logic before the loop starts."""
        pass

    def on_stop(self):
        """Override this to run logic after the app exits."""
        pass

    def on_update(self):
        """Override this to define the main loop logic."""
        pass

    def render(self):
        """
        Return the UI to display.
        Should return a String, Widget, or List of Widgets.
        """
        return ""

    def exit(self):
        """Stops the application loop."""
        self._running = False

    def run(self):
        """
        Starts the application.
        1. Enters Alternate Screen Buffer.
        2. Hides Cursor.
        3. Runs the Event Loop.
        4. Restores Terminal state on exit.
        """
        try:
            # --- SETUP ---
            sys.stdout.write(ALT_SCREEN_ENTER)
            sys.stdout.write(CURSOR_HIDE)
            sys.stdout.flush()

            self._running = True
            self.on_start()

            # --- LOOP ---
            while self._running:
                self.on_update()
                view = self.render()
                if isinstance(view, (list, tuple)):
                    content = grid(view, cols=1, render=True)
                else:
                    content = str(view)

                sys.stdout.write(CLEAR_SCREEN)
                sys.stdout.write(content)
                sys.stdout.flush()

                time.sleep(self.refresh_rate)

        except KeyboardInterrupt:
            pass
        finally:
            # --- CLEANUP ---
            self.on_stop()
            sys.stdout.write(ALT_SCREEN_EXIT)
            sys.stdout.write(CURSOR_SHOW)
            sys.stdout.flush()