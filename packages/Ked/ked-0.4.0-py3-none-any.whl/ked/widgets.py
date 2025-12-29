"""Custom widgets of this application"""

from textual.widgets  import Label
from textual.reactive import reactive
from textual.binding  import Binding
from textual.message  import Message
from textual.events   import Key
from textual.events   import MouseDown
from textual.events   import Blur


class KeyInput(Label, can_focus=True):
    """Input widget for a key combination"""

    key: reactive[str] = reactive('', layout=True)
    """key (combination) represented by the widget"""

    capture: reactive[bool] = reactive(False, layout=True)
    """flag indicating if waiting for key press to capture"""

    class Changed(Message):
        """Message posted when user assigned new key"""
        def __init__(self, id: str, key: str, old: str):
            self.id  = id
            """id of (this) sender widget"""
            self.key = key
            """new key selected by the user"""
            self.old = old
            """old key stored previously"""
            super().__init__()

    DEFAULT_CSS = """
        KeyInput {
            border:        round $border;
            background:    $surface;
            content-align: center middle;
            &:focus {
                background-tint: $foreground 5%;
            }
        }
    """

    def __init__(self, key: str, **kwargs):
        super().__init__(**kwargs)
        self.key = key

    def render(self) -> str:
        """Renders the widget."""
        if self.capture:
            self.tooltip = 'Press key or key combination. Press Del to unset.'
            return 'Press key…'
        else:
            self.tooltip  = 'Click to change.'
            dummy_binding = Binding(self.key, '', '')
            key_display   = self.app.get_key_display(dummy_binding)
            return key_display

    async def on_key(self, event: Key) -> None:
        """Event triggered when user presses a key."""
        if not self.capture:
            if event.key == 'enter':
                self.capture = True
                event.stop()
            # Bubble up any other key.
        else:
            match event.key:
                case 'tab' | 'shift+tab':
                    # Bubble up.
                    return
                case 'enter' | 'escape':
                    # Stop capture.
                    pass
                case 'backspace' | 'delete':
                    # Deactivate key binding.
                    old_key  = self.key
                    self.key = ''
                    self.post_message(self.Changed(self.id, self.key, old_key))
                case _:
                    # Assign new key.
                    old_key  = self.key
                    self.key = event.key
                    self.post_message(self.Changed(self.id, self.key, old_key))
            self.capture = False
            event.stop()

    def on_blur(self, _event: Blur):
        """Event triggered when widget loses focus."""
        self.capture = False

    async def on_mouse_up(self, _event: MouseDown):
        """Event triggered when user presses a mouse button."""
        if self.has_focus:
            self.capture = True
