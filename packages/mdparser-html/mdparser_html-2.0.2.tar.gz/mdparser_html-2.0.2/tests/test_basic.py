from mdparser.core import parse_markdown

def test_basic():
    assert "<h1>" in parse_markdown("# Hello")

