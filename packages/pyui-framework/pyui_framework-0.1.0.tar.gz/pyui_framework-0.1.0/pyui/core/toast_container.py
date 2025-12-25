from pyui.core.component import Component


class ToastContainer(Component):
    def __init__(self, *toasts: Component):
        self.toasts = toasts

    def render(self) -> str:
        toasts_html = "".join(
            toast.render() for toast in self.toasts
        )

        return f"""
        <div class="pyui-toast-container">
            {toasts_html}
        </div>
        """
