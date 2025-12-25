from pyui.core.component import Component


class Grid(Component):
    def __init__(self, *items: Component):
        self.items = items

    def render(self) -> str:
        items_html = "".join(
            item.render() for item in self.items
        )

        return f"""
        <div class="pyui-grid">
            {items_html}
        </div>
        """

class GridItem(Component):
    def __init__(self, content: Component, span: int = 12):
        if span < 1 or span > 12:
            raise ValueError("Grid span must be between 1 and 12")

        self.content = content
        self.span = span

    def render(self) -> str:
        return f"""
        <div class="pyui-grid-item" style="--span:{self.span}">
            {self.content.render()}
        </div>
        """
