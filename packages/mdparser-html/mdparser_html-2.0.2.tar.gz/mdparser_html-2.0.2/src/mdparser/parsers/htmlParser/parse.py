import re


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
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <meta charset="UTF-8">
        <style>
        h1 {{ font-size: 2.25rem; font-weight: 700; margin: 1em 0; }}
        h2 {{ font-size: 1.875rem; font-weight: 600; margin: 0.9em 0; }}
        h3 {{ font-size: 1.5rem; font-weight: 600; margin: 0.8em 0; }}
        h4 {{ font-size: 1.25rem; font-weight: 600; margin: 0.7em 0; }}
        h5 {{ font-size: 1.125rem; font-weight: 600; margin: 0.6em 0; }}
        h6 {{ font-size: 1rem; font-weight: 600; margin: 0.5em 0; }}

        p {{ margin: 0.75em 0; line-height: 1.6; }}
        ul, ol {{ margin: 1em 0 1em 1.5em; }}
        li {{ margin: 0.25em 0; }}
        code {{ background: #f6f8fa; padding: 2px 4px; border-radius: 4px; }}
        </style>
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
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
        <script>hljs.highlightAll();</script>
        <style>
        h1 {{ font-size: 2.25rem; font-weight: 700; margin: 1em 0; }}
        h2 {{ font-size: 1.875rem; font-weight: 600; margin: 0.9em 0; }}
        h3 {{ font-size: 1.5rem; font-weight: 600; margin: 0.8em 0; }}
        h4 {{ font-size: 1.25rem; font-weight: 600; margin: 0.7em 0; }}
        h5 {{ font-size: 1.125rem; font-weight: 600; margin: 0.6em 0; }}
        h6 {{ font-size: 1rem; font-weight: 600; margin: 0.5em 0; }}

        p {{ margin: 0.75em 0; line-height: 1.6; }}
        ul, ol {{ margin: 1em 0 1em 1.5em; }}
        li {{ margin: 0.25em 0; }}
        code {{ background: #f6f8fa; padding: 2px 4px; border-radius: 4px; }}
        </style>       
        </head>
        <body>
        {text}
        </body>
        </html>
        '''

# -------------------------------
# BLOCK: HEADINGS
# -------------------------------

def parse_headings(text):
    # ---------- h8 ----------
    text = re.sub(
        r'^########\s*\[([^\]]+)\]\s+(.*)$',
        r'<h8 class="\1">\2</h8>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^########\s+(.*)$',
        r'<h8>\1</h8>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h7 ----------
    text = re.sub(
        r'^#######\s*\[([^\]]+)\]\s+(.*)$',
        r'<h7 class="\1">\2</h7>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^#######\s+(.*)$',
        r'<h7>\1</h7>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h6 ----------
    text = re.sub(
        r'^######\s*\[([^\]]+)\]\s+(.*)$',
        r'<h6 class="\1">\2</h6>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^######\s+(.*)$',
        r'<h6>\1</h6>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h5 ----------
    text = re.sub(
        r'^#####\s*\[([^\]]+)\]\s+(.*)$',
        r'<h5 class="\1">\2</h5>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^#####\s+(.*)$',
        r'<h5>\1</h5>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h4 ----------
    text = re.sub(
        r'^####\s*\[([^\]]+)\]\s+(.*)$',
        r'<h4 class="\1">\2</h4>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^####\s+(.*)$',
        r'<h4>\1</h4>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h3 ----------
    text = re.sub(
        r'^###\s*\[([^\]]+)\]\s+(.*)$',
        r'<h3 class="\1">\2</h3>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^###\s+(.*)$',
        r'<h3>\1</h3>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h2 ----------
    text = re.sub(
        r'^##\s*\[([^\]]+)\]\s+(.*)$',
        r'<h2 class="\1">\2</h2>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^##\s+(.*)$',
        r'<h2>\1</h2>',
        text,
        flags=re.MULTILINE
    )

    # ---------- h1 ----------
    text = re.sub(
        r'^#\s*\[([^\]]+)\]\s+(.*)$',
        r'<h1 class="\1">\2</h1>',
        text,
        flags=re.MULTILINE
    )
    text = re.sub(
        r'^#\s+(.*)$',
        r'<h1>\1</h1>',
        text,
        flags=re.MULTILINE
    )

    return text




# -------------------------------
# INLINE: BOLD, ITALIC, CODE
# -------------------------------
def parse_inline(text):
    """Convert inline Markdown syntax to HTML.
    Args:
        text (str): Markdown source text.
    Returns:
        str: Text with inline Markdown converted to HTML.
    """
    # bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # italic: *text*
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    # italic: _text_
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)

    # inline code
    text = re.sub(r'`([^`]*)`', r'<code>\1</code>', text)

    return text


# -------------------------------
# LISTS: UL + OL
# -------------------------------
def unorderedList(match):
    """Convert Markdown unordered list to HTML unordered list.
    Args:
        match (re.Match): Regex match object for unordered list.
    Returns:
        str: HTML unordered list.
    """
    items = match.group(0).strip().split("\n")
    list_items = "".join([f"<li>{item[2:].strip()}</li>\n" for item in items])
    return f"<ul>\n{list_items}</ul>"

def orderedList(match):
    """Convert Markdown ordered list to HTML ordered list.
    Args:
        match (re.Match): Regex match object for ordered list.
    Returns:
        str: HTML ordered list.
    """
    items = match.group(0).strip().split("\n")
    list_items = ""
    for item in items:
        _, text = item.split(". ", 1)
        list_items += f"<li>{text.strip()}</li>\n"
    return f"<ol>\n{list_items}</ol>"

def parse_lists(text):
    """Convert Markdown lists to HTML lists.
    Args:
        text (str): Markdown source text.
    Returns:
        str: Text with Markdown lists converted to HTML.
    """
    text = re.sub(r'(^- .+(?:\n- .+)*)', unorderedList, text, flags=re.MULTILINE)
    text = re.sub(r'(^\d+\. .+(?:\n\d+\. .+)*)', orderedList, text, flags=re.MULTILINE)
    return text




#
# -------------------------------
# PARAGRAPHS
# -------------------------------
def wrap_paragraphs(html):
    """Wrap lines in <p> tags, except for certain HTML elements.
    Args:
        html (str): HTML source text.
    Returns:
        str: HTML text with lines wrapped in <p> tags where appropriate.
    """
    lines = html.split("\n")
    result = []
    in_pre_block = False
    for line in lines:
        stripped = line.strip()

        if not stripped:
            result.append("")
            continue
                # detect start of code block
        if stripped.startswith("<pre>") or stripped.startswith("<pre "):
            in_pre_block = True
            result.append(line)
            continue

        # detect end of code block
        if stripped.startswith("</pre>"):
            in_pre_block = False
            result.append(line)
            continue

        # if inside <pre>...</pre> → do NOT wrap
        if in_pre_block:
            result.append(line)
            continue

        if (stripped.startswith("<h") and stripped.endswith(">")) \
           or stripped.startswith("<ol>") or stripped.startswith("<ul>") \
           or stripped.startswith("</ol>") or stripped.startswith("</ul>") \
           or stripped.startswith("<li>") \
           or stripped.startswith("<pre>") or stripped.startswith("</pre>") \
           or stripped.startswith("<code>") or stripped.startswith("</code>") \
           or (stripped.startswith("<") and stripped.endswith(">")) \
          or stripped.startswith("</div>") or stripped.startswith("<div") :
            result.append(line)
            continue

        result.append(f"<p>{stripped}</p>")

    return "\n".join(result)



# -------------------------------
# CODE BLOCKS
# -------------------------------

def _normalize_language(lang):
    """Normalize programming language for syntax highlighting.
    Args:
        lang (str): Language specified in the Markdown code block.
    Returns:
        str: Normalized language for syntax highlighting.
    """
    if not lang or len(lang) <= 1:
        return "bash"
    return lang.lower()

def _code_block(match):
    """Convert Markdown code block to HTML code block with syntax highlighting.
    Args:
        match (re.Match): Regex match object for code block.
    Returns:
        str: HTML code block with syntax highlighting.
    """
    language = match.group(1)
    code_content = match.group(2)
    newLanguage = _normalize_language(language)
    code_content = ( code_content.replace("&", "&amp;") .replace("<", "&lt;") .replace(">", "&gt;") )
    return f'<pre><code class="language-{newLanguage}">\n{code_content}\n</code></pre>'

def parse_code(text):
    """Convert Markdown code blocks to HTML code blocks with syntax highlighting.
    Args:
        text (str): Markdown source text.
    Returns:
        str: Text with Markdown code blocks converted to HTML code blocks.
    """
    return re.sub(r'```(\w*)\s*\n(.*?)\n```',_code_block, text, flags=re.S)






# -------------------------------
# images
# -------------------------------

def _parse_image(match):
    """Convert Markdown image syntax to HTML <img> tag.
    Args:
        match (re.Match): Regex match object for image.
    Returns:
        str: HTML <img> tag.
    """
    alt_text = match.group(1)
    url = match.group(2)
    title = match.group(3)

    title_attr = f' title="{title}"' if title else ''
    return f'<img src="{url}" alt="{alt_text}"{title_attr} />'

def parse_images(text):
    return re.sub(
        r'!\[(.*?)\]\((.*?)(?:\s+"(.*?)")?\)',
    _parse_image,
    text
  )

#-----------------------------------------------
#Table Parsing 
#-----------------------------------------------

def parse_table_block(table_md: str) -> str:
    lines = [line.strip() for line in table_md.splitlines() if line.strip()]
    if len(lines) < 2:
        return ""

    header = [cell.strip() for cell in lines[0].split("|")]
    rows = [[cell.strip() for cell in row.split("|")] for row in lines[1:]]

    th = lambda h: f'<th style="border:1px solid #d0d7de;padding:8px 12px;background:#f6f8fa;text-align:left;">{h}</th>'
    td = lambda d: f'<td style="border:1px solid #d0d7de;padding:8px 12px;">{d}</td>'

    thead = "<thead><tr>" + "".join(th(h) for h in header) + "</tr></thead>"
    tbody = "<tbody>" + "".join(
        "<tr>" + "".join(td(cell) for cell in row) + "</tr>"
        for row in rows
    ) + "</tbody>"

    return f'''
<table style="border-collapse:collapse;width:100%;margin:1em 0;">
{thead}
{tbody}
</table>
'''







# -------------------------------
# FENCED DIVS (RECURSIVE)
# -------------------------------
#small fix to make it recursive (works with nested divs and its state machine)
def parse_fenced_divs(text: str) -> str:
    lines = text.splitlines()
    stack = []
    output = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(":::"):
            block_name = stripped[3:].strip()

            # 🔒 Closing block
            if stack and block_name == "":
                block = stack.pop()
                inner_md = "\n".join(block["content"])

                # TABLE BLOCK
                if block["type"] == "table":
                    html = parse_table_block(inner_md)

                # DIV BLOCK
                else:
                    inner_html = parse_markdown(inner_md, full_html=False)
                    html = f'<div class="{block["class"]}">\n{inner_html}\n</div>'

                if stack:
                    stack[-1]["content"].append(html)
                else:
                    output.append(html)

            # 🔓 Opening block
            else:
                if block_name == "table":
                    stack.append({
                        "type": "table",
                        "content": []
                    })
                else:
                    stack.append({
                        "type": "div",
                        "class": block_name,
                        "content": []
                    })

        else:
            if stack:
                stack[-1]["content"].append(line)
            else:
                output.append(line)

    return "\n".join(output)


#------------------------
# Hr Tag Parsing
#------------------------
def parse_hr(text: str) -> str:
    return re.sub(
        r'^\s*(?:---|\*\*\*|___)\s*$',
        '<hr />',
        text,
        flags=re.MULTILINE
    )


#------------------------
# Blockquote Parsing
#------------------------

def parse_blockquotes(text: str) -> str:
    lines = text.splitlines()
    output = []
    buffer = []

    def flush():
        if buffer:
            inner_md = "\n".join(buffer)
            inner_html = parse_markdown(inner_md, full_html=False)
            output.append(f"<blockquote>\n{inner_html}\n</blockquote>")
            buffer.clear()

    for line in lines:
        if line.lstrip().startswith(">"):
            buffer.append(line.lstrip()[1:].lstrip())
        else:
            flush()
            output.append(line)

    flush()
    return "\n".join(output)

#------------------------
# links Parsing
#------------------------
def parse_links(text: str) -> str:
    return re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2">\1</a>',
        text
    )






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
    text = parse_hr(text)
    text = parse_blockquotes(text)
    text = parse_lists(text)
    text = parse_images(text)
    text = parse_links(text)
    text = parse_inline(text)
    text = wrap_paragraphs(text)
    if full_html:
        html = _html_string(text=text,title=title,include_cdn=include_cdn)
    else:
        html = text
    return html


# # # -------------------------------
# # # RUN
# # # -------------------------------
# if __name__ == "__main__":
#     with open("/home/dragoon/coding/pythonProjects/markdownToHtml/test_internal/test.md","r") as f:
#         content = f.read()
#     html = parse_markdown(content,title="Test Markdown")
#     with open("output.html", "w") as f:
#         f.write(html)
#
#     print("Converted!")
#
