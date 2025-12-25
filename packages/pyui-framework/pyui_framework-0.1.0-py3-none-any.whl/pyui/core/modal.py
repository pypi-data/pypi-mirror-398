from typing import List, Optional
from pyui.core.component import Component


class Modal(Component):
    def __init__(
        self,
        title: str,
        content: Component,
        actions: Optional[List[Component]] = None
    ):
        self.title = title
        self.content = content
        self.actions = actions or []

    def render(self) -> str:
        actions_html = "".join(
            action.render() for action in self.actions
        )

        return f"""
        <div class="pyui-modal-overlay">
            <div class="pyui-modal">
                <div class="pyui-modal-header">{self.title}</div>

                <div class="pyui-modal-body">
                    {self.content.render()}
                </div>

                <div class="pyui-modal-actions">
                    {actions_html}
                </div>
            </div>
        </div>
        """
