import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")

KATEX_CSS = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">'

KATEX_JS = """\
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script>
    renderMathInElement(document.body, {
        delimiters: [
            {left: "$$", right: "$$", display: true},
            {left: "$", right: "$", display: false},
            {left: "\\\\[", right: "\\\\]", display: true},
            {left: "\\\\(", right: "\\\\)", display: false}
        ]
    });
</script>"""


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


def build():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    with open(os.path.join(ROOT, "template.html"), encoding="utf-8") as f:
        template = f.read()

    for out_path, cfg in config.items():
        src_path = os.path.join(SRC, out_path)
        with open(src_path, encoding="utf-8") as f:
            content = f.read()

        html = template
        html = html.replace("{{TITLE}}", cfg["title"])
        html = html.replace("{{KATEX_CSS}}", KATEX_CSS if cfg["katex"] else "")
        html = html.replace("{{KATEX_JS}}", KATEX_JS if cfg["katex"] else "")
        html = html.replace("{{BREADCRUMB}}", render_breadcrumb(cfg.get("breadcrumb")))
        html = html.replace("{{CONTENT}}", content)
        html = html.replace("{{NAVBAR}}", render_navbar(cfg.get("nav")))
        html = html.replace("{{BACK}}", cfg["back"])
        html = html.replace("{{BACK_TEXT}}", cfg["back_text"])

        dest = os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print(f"  {out_path}")


if __name__ == "__main__":
    print("Building...")
    build()
    print("Done.")
