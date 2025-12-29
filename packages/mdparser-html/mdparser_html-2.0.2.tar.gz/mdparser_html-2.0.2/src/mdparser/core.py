from mdparser.parsers.htmlParser.parse import parse_fenced_divs,parse_code,parse_headings,parse_lists,parse_images,parse_inline,wrap_paragraphs


def _html_string(text:str,include_cdn:bool=True,title:str='Markdown to HTML')->str:
    """Generate a full HTML document string.
    Args:
        text (str): HTML body content.
        include_cdn (bool): Include syntax highlighting CDN assets.
        title (str): Title for the HTML document.
    Returns:
        str: Full HTML document as a string.
    """
    if not include_cdn:
        return f'''
        <html>
        <head>
        <title>{title}</title>
        <meta charset="UTF-8">

        </head>
        <body>
        {text}
        </body>
        </html>
        '''
    else:
        return f'''
        <html>
        <head>
        <title>{title}</title>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
        <script>hljs.highlightAll();</script>

        </head>
        <body>
        {text}
        </body>
        </html>
        '''






# -------------------------------
# MAIN PIPELINE
# -------------------------------
def parse_markdown(text:str,full_html:bool=True,title:str='Markdown to HTML',include_cdn:bool=True)->str:
    """
    Convert Markdown text into HTML.

    Args:
        text (str): Markdown source text.
        full_html (bool): If True, returns a full HTML document.
                          If False, returns only the HTML body.
        title (str): Title used in the HTML <title> tag.
        include_cdn (bool): Include syntax highlighting CDN assets.

    Returns:
        str: Rendered HTML output.
    """
    text = parse_fenced_divs(text)
    text = parse_code(text)          # MUST BE FIRST!!
    text = parse_headings(text)
    text = parse_lists(text)
    text = parse_inline(text)
    text = parse_images(text)
    text = wrap_paragraphs(text)
    if full_html:
        html = _html_string(text=text,title=title,include_cdn=include_cdn)
    else:
        html = text
    return html





