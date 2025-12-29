import argparse


from mdparser.core import parse_markdown


def main():
    parser = argparse.ArgumentParser(
        prog="md2html", description="Convert Markdown to HTML"
    )

    parser.add_argument("input", help="Path to the input Markdown file")

    parser.add_argument(
        "-o", "--output", help="Path to the output HTML file (default: stdout)"
    )

    parser.add_argument(
        "--body-only",
        action="store_true",
        help="Output HTML body only (no <html>/<head>)",
    )

    parser.add_argument(
        "--no-cdn",
        action="store_true",
        help="Do not include syntax-highlighting CDN links",
    )

    parser.add_argument(
        "--title", default="Markdown to HTML", help="HTML document title"
    )

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        markdown = f.read()

    html = parse_markdown(
        markdown,
        full_html=not args.body_only,
        include_cdn=not args.no_cdn,
        title=args.title,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
    else:
        print(html)
