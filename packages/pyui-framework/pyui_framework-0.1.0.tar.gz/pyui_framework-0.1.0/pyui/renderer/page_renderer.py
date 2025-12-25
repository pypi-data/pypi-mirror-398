from pyui.renderer.css import base_css


def render_page(content_html: str, title: str = "PyUI App", theme: str = "light"):
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>

    <style>
    {base_css()}
    </style>

    <script>
    function toggleTheme() {{
        const current = document.body.getAttribute("data-theme");
        document.body.setAttribute(
            "data-theme",
            current === "dark" ? "light" : "dark"
        );
    }}
    </script>
</head>

<body data-theme="{theme}">
    {content_html}
</body>
</html>
"""

    with open("dist/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("PyUI build complete → dist/index.html")
