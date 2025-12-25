
from typing import Optional, Callable
from pyui.core.events import register_event
from typing import Optional

class Component:
    def render(self) -> str:
        raise NotImplementedError


class Text(Component):
    def __init__(self, value: str, size: str = "md"):
        self.value = value
        self.size = size

    def render(self) -> str:
        return f'<p class="pyui-text {self.size}">{self.value}</p>'



class Button(Component):
    def __init__(
        self,
        text: str,
        variant: str = "primary",
        on_click: Optional[Callable] = None
    ):
        self.text = text
        self.variant = variant
        self.on_click = on_click

        self.event_id = None
        if on_click:
            self.event_id = register_event(on_click)

    def render(self) -> str:
        onclick = (
            f'onclick="pyuiTrigger(\'{self.event_id}\')"'
            if self.event_id else ""
        )

        return f"""
        <button class="pyui-button {self.variant}" {onclick}>
            {self.text}
        </button>
        """
