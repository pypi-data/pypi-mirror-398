from pyui.core.component import Component


class Alert(Component):
    def __init__(self, message: str, type: str = "info"):
        self.message = message
        self.type = type

    def render(self) -> str:
        return f"""
        <div class="pyui-alert {self.type}">
            {self.message}
        </div>
        """
