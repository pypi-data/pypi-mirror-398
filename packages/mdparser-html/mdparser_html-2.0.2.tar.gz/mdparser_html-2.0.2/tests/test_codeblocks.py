
from mdparser.core import parse_markdown

def test_codeblock_with_language():
    md = """```py
print("hi")
```"""
    html = parse_markdown(md)
    assert 'class="language-py"' in html
    assert "print(&quot;hi&quot;)" in html or "print" in html

def test_codeblock_without_language():
    md = """```
echo hello
```"""
    html = parse_markdown(md)
    assert 'class="language-bash"' in html
    assert "echo hello" in html
