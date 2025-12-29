
from mdparser.core import parse_markdown

def test_image_basic():
    md = "![alt](image.png)"
    html = parse_markdown(md)
    assert '<img src="image.png" alt="alt" />' in html

def test_image_with_title():
    md = '![alt](image.png "title")'
    html = parse_markdown(md)
    assert 'title="title"' in html
