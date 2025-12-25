from pyui.core.state import State
from pyui.core.component import Component


class Text(Component):
    def __init__(self, content):
        self.content = content

    def render(self) -> str:
        if isinstance(self.content, State):
            return f'<p class="pyui-text">{self.content.get()}</p>'
        return f'<p class="pyui-text">{self.content}</p>'
