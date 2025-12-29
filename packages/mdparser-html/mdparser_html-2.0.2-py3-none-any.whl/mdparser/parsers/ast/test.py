from mdparser.parsers.ast.parser import parse_ast
from mdparser.parsers.ast.render import render_html

md = """# H1
## [bg-blue-300 font-bold] H2
## H2
## H2
######## H8
Normal text
"""

ast = parse_ast(md)
html = render_html(ast)

print(html)

