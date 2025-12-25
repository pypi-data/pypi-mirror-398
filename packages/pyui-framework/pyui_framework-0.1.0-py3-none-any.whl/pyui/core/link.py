from pyui.core.component import Component


class Link(Component):
    def __init__(self, text: str, href: str):
        self.text = text
        self.href = href

    def render(self) -> str:
        return f"""
        <a class="pyui-link" href="{self.href}">
            {self.text}
        </a>
        """
