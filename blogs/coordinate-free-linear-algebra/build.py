import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

PERL = "C:/Users/lenovo/scoop/apps/perl/5.42.2.1"
BIN = os.path.join(PERL, "perl", "site", "bin")
PERL_BIN = os.path.join(PERL, "perl", "bin")
C_BIN = os.path.join(PERL, "c", "bin")
LATEXML = os.path.join(BIN, "latexml.bat")
LATEXMLPOST = os.path.join(BIN, "latexmlpost.bat")
ENV = os.environ.copy()
ENV["PATH"] = f"{BIN};{PERL_BIN};{C_BIN};{ENV['PATH']}"


def render_breadcrumb(items):
    if not items:
        return ""
    parts = []
    for item in items:
        if item["href"]:
            parts.append(f'<a href="{item["href"]}">{item["text"]}</a>')
        else:
            parts.append(item["text"])
    return "\n    <p>\n        " + " &gt; ".join(parts) + "\n    </p>\n"


def render_navbar(nav):
    if not nav:
        return ""
    prev = f'<a href="{nav["prev"]}">Prev</a>' if nav["prev"] else "Prev"
    contents = f'<a href="{nav["contents"]}">Contents</a>' if nav["contents"] else "Contents"
    nxt = f'<a href="{nav["next"]}">Next</a>' if nav["next"] else "Next"
    return (
        "\n    <hr>\n\n    <p>\n        "
        + prev
        + "\n        | "
        + contents
        + "\n        | "
        + nxt
        + "\n    </p>\n"
    )


def css_links(depth):
    """Generate CSS <link> tags with correct relative paths."""
    prefix = "../" * depth
    return (
        f'<link rel="stylesheet" href="{prefix}css/LaTeXML.css" type="text/css">\n'
        f'    <link rel="stylesheet" href="{prefix}css/ltx-article.css" type="text/css">'
    )


CACHE = os.path.join(ROOT, ".cache")

def compile_tex(src):
    """Compile a .tex file to HTML via LaTeXML. Returns path to generated HTML."""
    os.makedirs(CACHE, exist_ok=True)
    name = os.path.splitext(os.path.basename(src))[0]
    xml = os.path.join(CACHE, f"{name}.xml")
    html = os.path.join(CACHE, f"{name}.html")
    subprocess.run([LATEXML, f"--dest={xml}", src], env=ENV, check=True, cwd=ROOT)
    subprocess.run(
        [LATEXMLPOST, f"--dest={html}", "--format=html5", xml],
        env=ENV, check=True, cwd=ROOT,
    )
    os.remove(xml)
    return html


def extract_article(html_path):
    """Read LaTeXML output and extract <article> content."""
    with open(html_path, encoding="utf-8") as f:
        raw = f.read()
    m = re.search(r"<article[^>]*>(.*?)</article>", raw, re.DOTALL)
    return m.group(0) if m else raw


def wrap_page(title, css, body, breadcrumb, nav, back, back_text):
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en-US">\n'
        "\n"
        "<head>\n"
        f"    <title>{title}</title>\n"
        '    <meta charset="UTF-8">\n'
        f"    {css}\n"
        "</head>\n"
        "\n"
        "<body>\n"
        f"{render_breadcrumb(breadcrumb)}"
        f"{body}\n"
        f"{render_navbar(nav)}"
        f'    <p><a href="{back}">{back_text}</a></p>\n'
        "</body>\n"
        "\n"
        "</html>\n"
    )


def build():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    for out_path, cfg in config.items():
        src = os.path.join(ROOT, cfg["src"])
        dest = os.path.join(ROOT, out_path)

        depth = out_path.count("/")
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        tmp_html = compile_tex(src)
        body = extract_article(tmp_html)
        os.remove(tmp_html)

        html = wrap_page(
            cfg["title"],
            css_links(depth),
            body,
            cfg.get("breadcrumb"),
            cfg.get("nav"),
            cfg["back"],
            cfg["back_text"],
        )

        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print(f"  {out_path}")


if __name__ == "__main__":
    print("Building...")
    build()
    print("Done.")
