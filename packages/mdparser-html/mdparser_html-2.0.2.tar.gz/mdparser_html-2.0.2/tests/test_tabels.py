
from mdparser import parse_markdown
import re

def normalize(html):
    return re.sub(r"\s+", " ", html).strip()

def test_basic_table():
    md = """
:::table
Name | Age
Tarun | 21
Alex | 22
:::
"""
    html = normalize(parse_markdown(md))

    assert "<table" in html
    assert "<th" in html
    assert ">Age</th>" in html
    assert ">Tarun</td>" in html
    assert ">21</td>" in html
    assert ">Alex</td>" in html
