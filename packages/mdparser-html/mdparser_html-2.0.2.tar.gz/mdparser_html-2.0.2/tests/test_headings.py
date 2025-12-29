
from mdparser.core import parse_markdown

def test_h1():
    html = parse_markdown("# Hello")
    assert "<h1>Hello</h1>" in html

def test_h3():
    html = parse_markdown("### Title")
    assert "<h3>Title</h3>" in html

def test_h8():
    html = parse_markdown("######## Deep")
    assert "<h8>Deep</h8>" in html


def normalize(html: str) -> str:
    return " ".join(html.split())


def test_h3_without_style():
    md = "### Hello World"
    html = normalize(parse_markdown(md))

    assert "<h3>Hello World</h3>" in html


def test_h3_with_single_class():
    md = "### [text-red-500] Hello World"
    html = normalize(parse_markdown(md))

    assert '<h3 class="text-red-500">Hello World</h3>' in html



def test_h2_with_multiple_classes():
    md = "## [bg-blue-200 p-4 rounded] Styled Heading"
    html = normalize(parse_markdown(md))

    assert '<h2 class="bg-blue-200 p-4 rounded">Styled Heading</h2>' in html


def test_all_heading_levels_plain():
    md = """
# H1
## H2
### H3
#### H4
##### H5
###### H6
####### H7
######## H8
"""
    html = normalize(parse_markdown(md))

    assert "<h1>H1</h1>" in html
    assert "<h2>H2</h2>" in html
    assert "<h3>H3</h3>" in html
    assert "<h4>H4</h4>" in html
    assert "<h5>H5</h5>" in html
    assert "<h6>H6</h6>" in html
    assert "<h7>H7</h7>" in html
    assert "<h8>H8</h8>" in html



def test_all_heading_levels_styled():
    md = """
# [c1] H1
## [c2] H2
### [c3] H3
#### [c4] H4
##### [c5] H5
###### [c6] H6
####### [c7] H7
######## [c8] H8
"""
    html = normalize(parse_markdown(md))

    assert '<h1 class="c1">H1</h1>' in html
    assert '<h2 class="c2">H2</h2>' in html
    assert '<h3 class="c3">H3</h3>' in html
    assert '<h4 class="c4">H4</h4>' in html
    assert '<h5 class="c5">H5</h5>' in html
    assert '<h6 class="c6">H6</h6>' in html
    assert '<h7 class="c7">H7</h7>' in html
    assert '<h8 class="c8">H8</h8>' in html


def test_heading_style_does_not_leak():
    md = """
### [text-red-500] Title
Normal paragraph
"""
    html = normalize(parse_markdown(md))

    assert '<h3 class="text-red-500">Title</h3>' in html
    assert "<p>Normal paragraph</p>" in html


def test_heading_with_brackets_in_text():
    md = "### [text-green-500] Hello [World]"
    html = normalize(parse_markdown(md))

    assert '<h3 class="text-green-500">Hello [World]</h3>' in html














