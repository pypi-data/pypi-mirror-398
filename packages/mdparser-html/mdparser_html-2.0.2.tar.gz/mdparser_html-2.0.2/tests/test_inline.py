
from mdparser.core import parse_markdown

def test_bold():
    html = parse_markdown("**bold**")
    assert "<strong>bold</strong>" in html

def test_italic_star():
    html = parse_markdown("*italic*")
    assert "<em>italic</em>" in html

def test_italic_underscore():
    html = parse_markdown("_italic_")
    assert "<em>italic</em>" in html

def test_inline_code():
    html = parse_markdown("`code`")
    assert "<code>code</code>" in html

def test_nested_inline():
    html = parse_markdown("**bold _italic_**")
    assert "<strong>bold <em>italic</em></strong>" in html
