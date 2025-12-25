from typing import List
from typing import Callable, Optional
from pyui.core.component import Component
from pyui.core.events import register_event


class Form(Component):
    def __init__(
        self,
        *children: Component,
        on_submit: Optional[Callable] = None
    ):
        self.children = children
        self.on_submit = on_submit
        self.event_id = register_event(on_submit) if on_submit else None

    def render(self) -> str:
        submit = (
            f'onsubmit="pyuiTrigger(\'{self.event_id}\'); return false;"'
            if self.event_id else ""
        )

        children_html = "".join(child.render() for child in self.children)

        return f"""
        <form class="pyui-form" {submit}>
            {children_html}
        </form>
        """
