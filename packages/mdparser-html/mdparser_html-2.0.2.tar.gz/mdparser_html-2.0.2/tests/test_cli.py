
import subprocess
import tempfile
from pathlib import Path

def test_cli_runs():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "test.md"
        out = Path(tmp) / "out.html"

        md.write_text("# Hello")

        subprocess.run(
            ["md2html", str(md), "-o", str(out)],
            check=True
        )

        assert out.exists()
        assert "<h1>Hello</h1>" in out.read_text()
