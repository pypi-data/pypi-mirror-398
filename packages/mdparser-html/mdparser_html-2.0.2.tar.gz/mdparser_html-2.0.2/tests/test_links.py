from mdparser import parse_markdown


def normalize(html):
    return " ".join(html.split())


def test_basic_link():
    md = "[OpenAI](https://www.openai.com)"
    html = normalize(parse_markdown(md))

    assert '<a href="https://www.openai.com">OpenAI</a>' in html

#
# def test_link_with_title():
#     md = '[OpenAI](https://www.openai.com "OpenAI Homepage")'
#     html = normalize(parse_markdown(md))
#
#     assert '<a href="https://www.openai.com" title="OpenAI Homepage">OpenAI</a>' in html

