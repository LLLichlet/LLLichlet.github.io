from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from typing import Any

ROOT = os.path.dirname(os.path.abspath(__file__))

PERL = "C:/Users/lenovo/scoop/apps/perl/5.42.2.1"
BIN = os.path.join(PERL, "perl", "site", "bin")
PERL_BIN = os.path.join(PERL, "perl", "bin")
C_BIN = os.path.join(PERL, "c", "bin")
LATEXML = os.path.join(BIN, "latexml.bat")
LATEXMLPOST = os.path.join(BIN, "latexmlpost.bat")
ENV = os.environ.copy()
ENV["PATH"] = f"{BIN};{PERL_BIN};{C_BIN};{ENV['PATH']}"

CACHE = os.path.join(ROOT, ".cache")
HASHES = os.path.join(CACHE, "hashes.json")
os.makedirs(CACHE, exist_ok=True)

Breadcrumb = list[dict[str, str | None]] | None
Nav = dict[str, str | None] | None


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_hashes() -> dict[str, str]:
    if os.path.exists(HASHES):
        with open(HASHES, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_hashes(h: dict[str, str]) -> None:
    with open(HASHES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(h, f)


def compile_tex(src: str) -> str:
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


def body_from_tex(src: str, stored: dict[str, str]) -> str:
    h = sha256(src)
    key = os.path.relpath(src, ROOT).replace("\\", "/")
    cache_html = os.path.join(CACHE, f"{key}.html")

    if stored.get(key) == h and os.path.exists(cache_html):
        with open(cache_html, encoding="utf-8") as f:
            raw = f.read()
    else:
        tmp = compile_tex(src)
        with open(tmp, encoding="utf-8") as f:
            raw = f.read()
        os.makedirs(os.path.dirname(cache_html), exist_ok=True)
        with open(cache_html, "w", encoding="utf-8", newline="\n") as f:
            f.write(raw)
        os.remove(tmp)
        stored[key] = h

    m = re.search(r"<article[^>]*>(.*?)</article>", raw, re.DOTALL)
    return m.group(0) if m else raw


def render_breadcrumb(items: Breadcrumb) -> str:
    if not items:
        return ""
    parts: list[str] = []
    for item in items:
        if item["href"]:
            parts.append(f'<a href="{item["href"]}">{item["text"]}</a>')
        else:
            parts.append(item["text"])
    return "\n    <p>\n        " + " &gt; ".join(parts) + "\n    </p>\n"


def render_navbar(nav: Nav) -> str:
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


def css_links(depth: int) -> str:
    prefix = "../" * depth
    return (
        f'<link rel="stylesheet" href="{prefix}css/LaTeXML.css" type="text/css">\n'
        f'    <link rel="stylesheet" href="{prefix}css/ltx-article.css" type="text/css">'
    )


def wrap_page(
    title: str,
    css: str,
    body: str,
    breadcrumb: Breadcrumb,
    nav: Nav,
    back: str,
    back_text: str,
) -> str:
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


def build() -> None:
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        config: dict[str, Any] = json.load(f)

    stored = load_hashes()

    for out_path, cfg in config.items():
        src = os.path.join(ROOT, cfg["src"])
        dest = os.path.join(ROOT, out_path)

        depth: int = out_path.count("/")
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        body = body_from_tex(src, stored)

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

    save_hashes(stored)


if __name__ == "__main__":
    print("Building...")
    build()
    print("Done.")
