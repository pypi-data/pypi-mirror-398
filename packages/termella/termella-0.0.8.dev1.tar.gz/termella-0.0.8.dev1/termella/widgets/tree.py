from ..core import Text

def tree(data, root_name=".", render=False):
    """
    Recursive tree renderer.
    """
    lines = []
    if root_name:
        lines.append(str(Text(root_name).style(color="blue", styles="bold")))

    def _walk(node, prefix):
        keys = list(node.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            connector = "└── " if is_last else "├── "

            val = node[key]
            if isinstance(val, dict):
                lines.append(f"{prefix}{connector}{Text(key).style(color='cyan')}")
                extension = "    " if is_last else "│   "
                _walk(val, prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{key}: {Text(str(val)).style(color='green')}")

    _walk(data, "")
    final_str = "\n".join(lines)

    if render: return final_str
    print(final_str)