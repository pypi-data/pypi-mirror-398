import re
from mdparser import parse_markdown 


def normalize(html: str) -> str:
    """Remove extra whitespace for stable assertions"""
    return re.sub(r"\s+", " ", html).strip()


def test_basic_fenced_div():
    md = """
::: hero
Hello world
:::
"""
    html = parse_markdown(md)
    html = normalize(html)

    assert '<div class="hero">' in html
    assert '<p>Hello world</p>' in html
    assert '</div>' in html


def test_fenced_div_with_tailwind_classes():
    md = """
::: hero bg-blue-500 text-white p-6
Hero content
:::
"""
    html = normalize(parse_markdown(md))

    assert '<div class="hero bg-blue-500 text-white p-6">' in html
    assert '<p>Hero content</p>' in html


def test_fenced_div_with_heading():
    md = """
::: section p-4
# Welcome
:::
"""
    html = normalize(parse_markdown(md))

    assert '<div class="section p-4">' in html
    assert '<h1>Welcome</h1>' in html


def test_fenced_div_with_inline_markdown():
    md = """
::: card
This is **bold** and _italic_
:::
"""
    html = normalize(parse_markdown(md))

    assert '<strong>bold</strong>' in html
    assert '<em>italic</em>' in html


def test_fenced_div_with_list():
    md = """
::: list-box
- One
- Two
- Three
:::
"""
    html = normalize(parse_markdown(md))

    assert '<ul>' in html
    assert '<li>One</li>' in html
    assert '<li>Two</li>' in html
    assert '<li>Three</li>' in html


def test_nested_fenced_divs():
    md = """
::: outer
Outer start

::: inner
Inner content
:::

Outer end
:::
"""
    html = normalize(parse_markdown(md))

    assert '<div class="outer">' in html
    assert '<div class="inner">' in html
    assert '<p>Inner content</p>' in html
    assert 'Outer start' in html
    assert 'Outer end' in html


def test_fenced_div_with_code_block():
    md = """
::: code-box
```python
"""
print("hello")
