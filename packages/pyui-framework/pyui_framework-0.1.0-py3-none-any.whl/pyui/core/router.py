import os
from pyui.core.page import Page
from pyui.core.component import Component


class Router(Component):
    def __init__(self, routes: dict, title: str = "PyUI App"):
        self.routes = routes
        self.title = title

    def build(self):
        os.makedirs("dist", exist_ok=True)

        for path, component in self.routes.items():
            filename = self._path_to_filename(path)

            page = Page(
                body=component,
                title=self.title
            )

            with open(f"dist/{filename}", "w", encoding="utf-8") as f:
                f.write(page.render())

        print("✅ PyUI routing build complete")

    def _path_to_filename(self, path: str) -> str:
        if path == "/":
            return "index.html"
        return path.strip("/").replace("/", "_") + ".html"


__all__ = ["Router"]
