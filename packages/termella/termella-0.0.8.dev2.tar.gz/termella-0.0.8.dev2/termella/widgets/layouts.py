from ..core import visible_len

def columns(*widgets, padding=2, align="top", render=False):
    """
    Prints strings/widgets side-by-side.
    Args:
        *widgets: Strings (output from panel(render=True), etc)
        padding (int): Spaces between columns.
    """
    cols_data = []
    for w in widgets:
        if not w: 
            cols_data.append([])
        else: 
            lines = str(w).split('\n')
            if len(lines) == 1 and lines[0] == '':
                cols_data.append([])
            else:
                cols_data.append(lines)
    
    if not any(cols_data): return "" if render else None
    max_height = max(len(c) for c in cols_data)
    if max_height == 0: return "" if render else None

    col_widths = []
    for col in cols_data:
        w = max(visible_len(line) for line in col) if col else 0
        col_widths.append(w)

    pad_str = " " * padding

    aligned_cols = []
    for col in cols_data:
        diff = max_height - len(col)
        if diff > 0:
            if align == "bottom":
                new_col = ([""] * diff) + col
            elif align == "center":
                top_pad = diff // 2
                bot_pad = diff - top_pad
                new_col = ([""] * top_pad) + col + ([""] * bot_pad)
            else:
                new_col = col + ([""] * diff)
            aligned_cols.append(new_col)
        else:
            aligned_cols.append(col)

    output_lines = []
    for i in range(max_height):
        line_parts = []
        for j, col in enumerate(aligned_cols):
            content = col[i]
            v_len = visible_len(content)
            if j < len(aligned_cols) - 1:
                fill = " " * (col_widths[j] - v_len)
                line_parts.append(content + fill)
            else:
                line_parts.append(content)

        output_lines.append(pad_str.join(line_parts))

    final_str = "\n".join(output_lines)

    if render:
        return final_str
    print(final_str)

def grid(widgets, cols=3, padding=2, render=False):
    """
    Arranges a list of widgets into a grid structure.
    """
    if not widgets: return "" if render else None
    
    grid_rows = []
    for i in range(0, len(widgets), cols):
        chunk = widgets[i : i + cols]
        row_str = columns(*chunk, padding=padding, render=True)
        if row_str:
            grid_rows.append(row_str)

    final_str = "\n\n".join(grid_rows)
    final_str = "\n".join(grid_rows)
    
    if render:
        return final_str
    print(final_str)