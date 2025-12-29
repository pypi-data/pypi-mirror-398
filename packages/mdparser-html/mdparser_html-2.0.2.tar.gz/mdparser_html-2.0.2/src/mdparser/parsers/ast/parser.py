from .node import Node

def parse_heading(line: str):
    stripped = line.lstrip()

    if not stripped:
        return None

    # Count leading #
    level = 0
    while level < len(stripped) and stripped[level] == "#":
        level += 1

    # Must be 1–8 #'s followed by a space
    if not (1 <= level <= 8 and len(stripped) > level and stripped[level] == " "):
        return None

    rest = stripped[level + 1 :].strip()  # text after "# "

    style = None
    if rest.startswith("["):
        end = rest.find("]")
        if end != -1:
            style = rest[1:end]
            rest = rest[end + 1 :].strip()

    attrs = {"level": level}
    if style:
        attrs["class"] = style   # use "class", not "style"

    return Node(
        type="heading",
        value=rest,
        attrs=attrs,
    )

def parse_ast(text: str) -> Node:
    """
    Entry point for AST parsing.
    """
    root = Node(type="document", children=[])

    lines = text.splitlines()

    for line in lines:
        node = parse_heading(line)
        if node:
            root.add_child(node)
            print(f"Parsed line into node: {node}")

    return root
