import os
from pyui.core.component import Component
from pyui.renderer.css import base_css
from pyui.renderer.js import base_js


class Page(Component):

    def __init__(
        self,
        body: Component,
        title: str = "PyUI App",
        theme: str = "light"
    ):
        self.body = body
        self.title = title
        self.theme = theme

    def render(self) -> str:
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{self.title}</title>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="style.css">
    <script src="script.js"></script>
</head>

<body data-theme="{self.theme}">
    {self.body.render()}
</body>
</html>
"""

    def build(self):
        os.makedirs("dist", exist_ok=True)

        with open("dist/index.html", "w", encoding="utf-8") as f:
            f.write(self.render())

        with open("dist/style.css", "w", encoding="utf-8") as f:
            f.write(base_css())

        with open("dist/script.js", "w", encoding="utf-8") as f:
            f.write(base_js())

        print("✅ PyUI build complete → dist/index.html + style.css + script.js")
