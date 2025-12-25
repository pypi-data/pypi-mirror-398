from pyui.core.component import Component


class Column(Component):
    def __init__(self, *children):
        self.children = children

    def render(self) -> str:
        children_html = "".join(child.render() for child in self.children)
        return f'<div class="pyui-column">{children_html}</div>'


class Row(Component):
    def __init__(self, *children):
        self.children = children

    def render(self) -> str:
        children_html = "".join(child.render() for child in self.children)
        return f'<div class="pyui-row">{children_html}</div>'
    
    
class Card(Component):
    def __init__(self, *children, elevation: int = 1):
        self.children = children
        self.elevation = elevation

    def render(self) -> str:
        children_html = "".join(child.render() for child in self.children)
        return (
            f'<div class="pyui-card elevation-{self.elevation}">'
            f'{children_html}'
            f'</div>'
        )


