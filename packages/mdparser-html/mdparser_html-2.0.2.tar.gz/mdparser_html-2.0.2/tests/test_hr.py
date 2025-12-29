from mdparser import parse_markdown 


def normalize(html):
    return " ".join(html.split())


def test_horizontal_rule():
    md = """---
Content above the horizontal rule.  
---
More content below the horizontal rule.
"""
    html = normalize(parse_markdown(md))
    assert "<hr />" in html
    assert "Content above the horizontal rule." in html
    assert "More content below the horizontal rule." in html       
