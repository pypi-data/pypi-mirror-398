import sys
from ..core import Text
from ..input.listener import InputListener
from ..ansi import CURSOR_HIDE, CURSOR_SHOW, CURSOR_UP, CLEAR_LINE

def select(options, prompt="Select an option:", color="cyan", marker=">", limit=5):
    """
    Single selection menu with scrolling.
    
    Args:
        limit (int): Max number of items to show at once.
    """
    listener = InputListener()
    idx = 0
    n = len(options)
    
    # Scroll Window State
    scroll_offset = 0
    # Effective window height
    window_height = min(n, limit)
    
    sys.stdout.write(CURSOR_HIDE)
    print(Text(prompt).style(styles="bold"))

    try:
        while True:
            # 1. Adjust Scroll Offset
            # If cursor is above the window, move window up
            if idx < scroll_offset:
                scroll_offset = idx
            # If cursor is below the window, move window down
            elif idx >= scroll_offset + window_height:
                scroll_offset = idx - window_height + 1

            # 2. Render Window
            # Only iterate through the slice of options visible in the window
            visible_options = options[scroll_offset : scroll_offset + window_height]
            
            for i, opt in enumerate(visible_options):
                # Calculate the true index of this item in the main list
                real_idx = scroll_offset + i
                
                sys.stdout.write(CLEAR_LINE)
                
                # Visual Scroll Indicators (Top/Bottom)
                prefix = marker if real_idx == idx else " "
                
                # Add arrows to indicate more items above/below
                if i == 0 and scroll_offset > 0:
                    display_text = f"{prefix} ↑ {opt}" # Arrow Up
                elif i == window_height - 1 and scroll_offset + window_height < n:
                    display_text = f"{prefix} ↓ {opt}" # Arrow Down
                else:
                    display_text = f"{prefix}   {opt}"

                # Print Styles
                if real_idx == idx:
                    print(Text(display_text).style(color=color, styles="bold"))
                else:
                    print(Text(display_text).style(styles="dim"))

            # 3. Handle Input
            key = listener.read_key()
            if key == 'UP': idx = (idx - 1) % n
            elif key == 'DOWN': idx = (idx + 1) % n
            elif key == 'ENTER': return options[idx]
            elif key == 'ESC': return None
            
            # 4. Reset Cursor
            sys.stdout.write(f"\r{CURSOR_UP * window_height}")
            
    except KeyboardInterrupt:
        return None
    finally:
        sys.stdout.write(CURSOR_SHOW)
        print()

def checkbox(options, prompt="Select options (Space/Enter):", color="green", marker=">", limit=5):
    """
    Multi-selection menu with scrolling.
    """
    listener = InputListener()
    idx = 0
    n = len(options)
    selected_indices = set()
    
    # Scroll Window State
    scroll_offset = 0
    window_height = min(n, limit)
    
    sys.stdout.write(CURSOR_HIDE)
    print(Text(prompt).style(styles="bold"))

    try:
        while True:
            # Adjust Scroll
            if idx < scroll_offset: scroll_offset = idx
            elif idx >= scroll_offset + window_height: scroll_offset = idx - window_height + 1

            visible_options = options[scroll_offset : scroll_offset + window_height]
            
            for i, opt in enumerate(visible_options):
                real_idx = scroll_offset + i
                sys.stdout.write(CLEAR_LINE)
                
                is_focused = (real_idx == idx)
                is_checked = (real_idx in selected_indices)
                
                box = "[x]" if is_checked else "[ ]"
                cursor = marker if is_focused else " "
                
                # Scroll arrows
                arrow = " "
                if i == 0 and scroll_offset > 0: arrow = "↑"
                elif i == window_height - 1 and scroll_offset + window_height < n: arrow = "↓"
                
                line_str = f"{cursor} {arrow} {box} {opt}"
                
                if is_focused:
                    print(Text(line_str).style(color="cyan", styles="bold"))
                elif is_checked:
                    print(Text(line_str).style(color=color))
                else:
                    print(Text(line_str).style(styles="dim"))

            key = listener.read_key()
            if key == 'UP': idx = (idx - 1) % n
            elif key == 'DOWN': idx = (idx + 1) % n
            elif key == 'SPACE':
                if idx in selected_indices: selected_indices.remove(idx)
                else: selected_indices.add(idx)
            elif key == 'ENTER': 
                return [options[i] for i in sorted(list(selected_indices))]
            elif key == 'ESC': return []
            
            sys.stdout.write(f"\r{CURSOR_UP * window_height}")
            
    except KeyboardInterrupt:
        return []
    finally:
        sys.stdout.write(CURSOR_SHOW)
        print()