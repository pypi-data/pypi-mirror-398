from ..core import Text, visible_len

def table(data, headers=None, border_color="white", align="left", render=False):
    """
    Renders a list of lists as a table.

    Args:
        data (list): list of rows (e.g. [['A', 'B'], ['C', 'D']])
        headers (list): List of column titles.
    """
    if not data and not headers: return ""

    if data: cols = len(data[0])
    else: cols = len(headers)

    if isinstance(align, str): aligns = [align.lower()] * cols
    else: aligns = [a.lower() for a in align] + ["left"] * (cols - len(align))

    widths = [0] * cols
    all_rows = ([] if not headers else [headers]) + (data if data else [])

    for row in all_rows:
        for i in range(min(len(row), cols)):
            widths[i] = max(widths[i], visible_len(row[i]))

    output = []

    def add_line(l, m, r, line):
        segments = [line * (w + 2) for w in widths]
        output.append(str(Text(l + m.join(segments) + r).style(border_color)))

    def format_cell(content, width, alignment):
        content = str(content)
        v_len = visible_len(content)
        pad = width - v_len
        if alignment == "right": return (" " * pad) + content
        elif alignment == "center":
            l_pad = pad // 2
            r_pad = pad - l_pad
            return (" " * l_pad) + content + (" " * r_pad)
        return content + (" " * pad)

    # Top Border
    add_line("┌", "┬", "┐", "─")

    # Headers
    if headers:
        row_str = "│"
        for i, cell in enumerate(headers):
            row_str += f" {format_cell(cell, widths[i], aligns[i])} │"
        output.append(str(Text(row_str).style(border_color, styles="bold")))
        add_line("├", "┼", "┤", "─")

    if not data:
        t_width = sum(widths) + (cols * 3) - 1
        output.append(str(Text("│ " + "No Data".center(t_width) + " │").style(border_color, styles="dim")))
    else:
        for row in data:
            row_str = "│"
            for i in range(cols):
                cell = row[i] if i < len(row) else ""
                row_str += f" {format_cell(cell, widths[i], aligns[i])} │"
            output.append(str(Text(row_str).style(border_color)))

    # Bottom Border
    add_line("└", "┴", "┘", "─")

    if headers:
        row_str = "│"
        for i, cell in enumerate(headers):
            row_str += f" {format_cell(cell, widths[i], aligns[i])} │"
        output.append(str(Text(row_str).style(border_color, styles="bold")))
        add_line("├", "┼", "┤", "─")

    if not data:
        t_width = sum(widths) + (cols * 3) - 1
        output.append(str(Text("│ " + "No Data".center(t_width) + " │").style(border_color, styles="dim")))
    else:
        for row in data:
            row_str = "│"
            for i in range(cols):
                cell = row[i] if i < len(row) else ""
                row_str += f" {format_cell(cell, widths[i], aligns[i])} │"
            output.append(str(Text(row_str).style(border_color)))

    add_line("└", "┴", "┘", "─")

    final_str = "\n".join(output)
    if render: return final_str
    print(final_str)