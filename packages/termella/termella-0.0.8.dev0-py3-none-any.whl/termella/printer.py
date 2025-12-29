from .core import Text

def cprint(text, color=None, bg=None, styles=None, end="\n"):
    """
    Color Print: Prints text with specified formatting.

    Args:
        text (str): The text to print.
        color (str): Foreground color name (e.g., 'red', 'blue').
        bg (str): Background color name (e.g., 'bg_white').
        styles (list/str): Styles like 'bold', 'underline'.
    """
    styled_text = Text(text).style(color, bg, styles)
    print(styled_text, end=end)

def cinput(prompt_text, color="cyan", styles="bold"):
    """
    [New in v0.0.2a] Styled Input.

    Prints a styled prompt and returns the user input.
    """
    styled_prompt = Text(prompt_text).style(color=color, styles=styles)
    try:
        return input(f"{styled_prompt} \033[0m")
    except KeyboardInterrupt:
        print()
        return None