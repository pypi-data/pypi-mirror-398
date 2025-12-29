from mdparser import parse_markdown


def normalize(html):
    return " ".join(html.split())   


def test_basic_blockquote():
    md = """> This is a blockquote.
> It has multiple lines.
> - And a list item.
> - Another list item.  
> **Bold text** inside blockquote.
"""
    html = normalize(parse_markdown(md))

    assert "<blockquote>" in html
    assert "This is a blockquote." in html
    assert "<ul>" in html
    assert "<li>And a list item.</li>" in html
    assert "<strong>Bold text</strong>" in html
    assert "</blockquote>" in html
