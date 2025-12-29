
from mdparser.core import parse_markdown

def test_unordered_list():
    md = "- Apple\n- Banana\n- Cherry"
    html = parse_markdown(md)
    assert "<ul>" in html
    assert "<li>Apple</li>" in html
    assert "<li>Banana</li>" in html

def test_ordered_list():
    md = "1. One\n2. Two\n3. Three"
    html = parse_markdown(md)
    assert "<ol>" in html
    assert "<li>One</li>" in html
    assert "<li>Two</li>" in html
