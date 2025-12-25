from typing import Optional
from pyui.core.component import Component


class Input(Component):
    def __init__(
        self,
        label: str,
        placeholder: str = "",
        type: str = "text",
        name: Optional[str] = None
    ):
        self.label = label
        self.placeholder = placeholder
        self.type = type
        self.name = name or label.lower().replace(" ", "_")

    def render(self) -> str:
        return f"""
        <div class="pyui-input-group">
            <label class="pyui-input-label">{self.label}</label>
            <input
                class="pyui-input"
                type="{self.type}"
                name="{self.name}"
                placeholder="{self.placeholder}"
            />
        </div>
        """
