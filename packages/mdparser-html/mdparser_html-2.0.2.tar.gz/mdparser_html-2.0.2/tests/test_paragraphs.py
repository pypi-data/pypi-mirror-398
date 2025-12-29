from mdparser.core import parse_markdown

def test_paragraph_wrap():
    html = parse_markdown("Hello world")
    assert "<p>Hello world</p>" in html

def test_no_paragraph_inside_heading():
    html = parse_markdown("# Title")
    assert "<p>" not in html.split("</h1>")[0]
# 975a268b-d1de-4cf8-a1df-2b29aa9933e2
