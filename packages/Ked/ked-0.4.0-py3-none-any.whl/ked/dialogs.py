"""Pop-up dialogs used throughout the app"""

from . import bindings

from textual.screen     import ModalScreen
from textual.widgets    import Button
from textual.widgets    import Label
from textual.containers import VerticalGroup
from textual.containers import HorizontalGroup
from textual.app        import ComposeResult


class UnsavedFile(ModalScreen[str]):
    """Dialog shown when quitting and file has not been saved."""

    BINDINGS = bindings.horizontal_buttons

    DEFAULT_CSS = """
        UnsavedFile {
            align: center middle;
        }
        #box {
            width:       auto;
            border:      round $border;
            background:  $background;
        }
        #question {
            align: center middle;
            width: 100%;
        }
        #buttons {
            width: auto;
        }
        Button {
            margin: 2 4;
        }
    """

    def compose(self) -> ComposeResult:
        """Composes the dialog."""
        with VerticalGroup(id='box'):
            with HorizontalGroup(id='question'):
                yield Label('Quit without saving?')
            with HorizontalGroup(id='buttons'):
                yield Button('Save',   variant='primary', id='save')
                yield Button('Quit',   variant='warning', id='quit')
                yield Button('Cancel', variant='default', id='cancel')

    def on_button_pressed(self, event: Button.Pressed):
        """Reports to the caller which button the user pressed."""
        self.dismiss(event.button.id)

    def action_cancel(self):
        self.dismiss('cancel')
