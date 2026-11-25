"""Build docs/REPORT.pdf from docs/REPORT.md.

Needs: pip install markdown, and Google Chrome (headless print to PDF).
Usage:  python3 scripts/build_report_pdf.py
"""
import re
import subprocess
import sys
from pathlib import Path

import markdown

DOCS = Path("docs")
md = (DOCS / "REPORT.md").read_text()
# python-markdown needs 4 spaces per nesting level for sub-lists
md = re.sub(r"(?m)^((?:  )+)(- )",
            lambda m: " " * (2 * len(m.group(1))) + m.group(2), md)
body =markdown.markdown(md, extensions=["tables", "fenced_code"])

css = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
       font-size: 9.6pt; line-height: 1.38; color: #111; }
h1 { font-size: 16pt; margin: 0 0 6px; }
h2 { font-size: 12.5pt; margin: 16px 0 6px; border-bottom: 1px solid #999;
     padding-bottom: 2px; }
h3 { font-size: 10.5pt; margin: 12px 0 4px; }
p, ul, ol { margin: 4px 0; }
li { margin: 1px 0; }
table { border-collapse: collapse; margin: 6px 0; font-size: 8.6pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 2px 5px; }
th { background: #eee; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.4pt; }
pre { background: #f5f5f5; padding: 6px; font-size: 7.8pt;
      white-space: pre-wrap; page-break-inside: avoid; }
img { display: block; margin: 6px auto; max-width: 78%;
      page-break-inside: avoid; }
hr { border: 0; border-top: 1px solid #ddd; margin: 10px 0; }
"""
html = (f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>Final Report</title><style>{css}</style></head>"
        f"<body>{body}</body></html>")
out_html = DOCS / "REPORT.html"
out_html.write_text(html)

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if not Path(chrome).exists():
    chrome = "google-chrome"
pdf = (DOCS / "REPORT.pdf").resolve()
subprocess.run([chrome, "--headless", "--disable-gpu",
                "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                out_html.resolve().as_uri()],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
out_html.unlink()
print(f"Saved {pdf}")
sys.exit(0)
