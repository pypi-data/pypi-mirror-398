from typing import List, Optional
from pyui.core.component import Component


class Navbar(Component):
    def __init__(
        self,
        brand: str,
        links: Optional[List[str]] = None,
        actions: Optional[List[Component]] = None
    ):
        self.brand = brand
        self.links = links or []
        self.actions = actions or []

    def render(self) -> str:
        links_html = "".join(
            f'<div class="pyui-navbar-link">{link}</div>'
            for link in self.links
        )

        actions_html = "".join(
            action.render() for action in self.actions
        )

        return f"""
        <nav class="pyui-navbar">
            <div class="pyui-navbar-brand">{self.brand}</div>

            <div class="pyui-navbar-links">
                {links_html}
            </div>

            <div class="pyui-navbar-actions">
                {actions_html}
            </div>
        </nav>
        """
