from pyui.core.component import Component


class Toast(Component):
    def __init__(self, message: str, type: str = "info"):
        self.message = message
        self.type = type

    def render(self) -> str:
        return f"""
        <div class="pyui-toast {self.type}">
            {self.message}
        </div>
        """
