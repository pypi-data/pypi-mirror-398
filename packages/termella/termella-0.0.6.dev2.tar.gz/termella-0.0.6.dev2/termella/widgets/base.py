from ..core import Text, visible_len

def panel(text, color="white", title=None, render=False):
    """
    Creates a simple ASCII box around text.
    """
    text = str(text)
    lines = text.split("\n")
    width = max(visible_len(line) for line in lines) + 2
    tl, tr, bl, br, h, v= "┌", "┐", "└", "┘", "─", "│"

    t_str = f" {title} " if title else ""
    top = h * (width - len(t_str))

    # Build the block
    output = []
    output.append(str(Text(f"{tl}{t_str}{top}{tr}").style(color)))

    for line in lines:
        # Calculate padding needed based on visible length
        padding = width - visible_len(line)
        output.append(str(Text(f"{v}{line}{' ' * padding}{v}").style(color)))

    output.append(str(Text(f"{bl}{h * width}{br}").style(color)))

    final_str = "\n".join(output)

    if render:
        return final_str
    print(final_str)