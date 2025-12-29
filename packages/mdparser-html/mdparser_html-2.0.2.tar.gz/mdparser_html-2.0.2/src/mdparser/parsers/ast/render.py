from .node import Node

def render_html(node: Node) -> str:
    if node.type == "document":
        return "\n".join(render_html(child) for child in node.children)

    if node.type == "heading":
        print(f"Rendering heading node: {node}")
        level = node.attrs["level"]
        result = ""
        if "class" in node.attrs:
            result += f'<h{level} class="{node.attrs["class"]}" >{node.value}</h{level}>'
            return result 
        return f"<h{level}>{node.value}</h{level}>"

    if node.type == "paragraph":
        return f"<p>{node.value}</p>"

    return ""
