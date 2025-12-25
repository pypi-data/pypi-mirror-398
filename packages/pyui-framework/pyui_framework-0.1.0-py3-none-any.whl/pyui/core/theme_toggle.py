from pyui.core.component import Component


class ThemeToggle(Component):
    def render(self) -> str:
        return """
        <button class="pyui-button secondary" onclick="toggleTheme()">
            Toggle Theme
        </button>
        """
