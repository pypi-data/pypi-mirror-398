from typing import List, Optional, Dict

class Node:
    def __init__(
        self,
        type: str,
        value: Optional[str] = None,
        children: Optional[List["Node"]] = None,
        attrs: Optional[Dict[str, str]] = None,
    ):
        self.type = type          # e.g. "heading", "paragraph"
        self.value = value        # raw text
        self.children = children or []
        self.attrs = attrs or {}

    def add_child(self, node: "Node"):
        self.children.append(node)

    def __repr__(self):
        return f"Node(type={self.type}, value={self.value}, children={len(self.children)})"
