"""Settings dialog with configuration options"""

from .        import config
from .        import bindings
from .editor  import Editor
from .widgets import KeyInput

from textual.screen     import ModalScreen
from textual.widgets    import TabbedContent
from textual.widgets    import TabPane
from textual.widgets    import Select
from textual.widgets    import Label
from textual.widgets    import Button
from textual.containers import Grid
from textual.containers import Vertical
from textual.containers import VerticalScroll
from textual.containers import Horizontal
from textual.app        import ComposeResult


class Settings(ModalScreen):
    """Settings dialog with configuration options"""

    DEFAULT_CSS = """
        Settings {
            align: right top;
        }
        #frame {
            border:     round $border;
            background: $surface;
            margin:     2 4;
            width:      80;
            height:     1fr;
            min-height: 15;
            min-width:  70;
        }
        #panels {
            height: 1fr;
            margin: 1 1;
        }
        #theme-panel {
            #theme-grid {
                grid-size:    2;
                grid-columns: auto auto;
                grid-rows:    auto;
                grid-gutter:  1 3;
                padding:      0 1;
                overflow-y:   auto;
            }
            .row {
            }
            .label {
                content-align: left middle;
                height:        1fr;
            }
            .select SelectOverlay {
                border: round $border;
            }
            .select SelectCurrent {
                border: round $border;
            }
            .select:focus SelectCurrent {
                border: round $border;
            }
        }
        #keys-panel {
            #keys-scroll {
            }
            .row {
                height: auto;
            }
            .input {
                width: 10;
            }
            .action {
                height:        100%;
                padding-left:  1;
                content-align: center middle;
            }
        }
        #buttons {
            margin-top: 1;
            height:     auto;
            Button {
                margin-top:    1;
                margin-bottom: 0;
                margin-left:   2;
                margin-right:  5;
            }
        }
    """

    BINDINGS = (
        ('escape', 'cancel'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending: dict[
            config.Setting, tuple[config.Value, config.Value]
        ] = {}
        """Settings to be stored on save or rolled back when canceled"""

    @property
    def editor(self) -> Editor:
        """Convenience property that returns the (single) editor widget."""
        return self.app.query_exactly_one('#editor', expect_type=Editor)

    def compose(self) -> ComposeResult:
        """Composes the dialog."""

        # For some reason, the app crashes when switching (back) to any theme
        # after having selected the Textual-Ansi theme. I haven't been able to
        # reproduce that with a minimal example, so it may have to do with our
        # custom components, rather than be a bug in Textual.
        exclude = ('textual-ansi',)

        # Pad theme names so the Select widget doesn't constantly resize.
        # This is a hacky solution because I haven't been able to figure out
        # how to do this elegantly. There's a `get_content_width()` method, but
        # it's not clear to me how (and if) to use it.
        themes = [
            theme for theme in sorted(self.app.available_themes.keys())
            if theme not in exclude
        ]
        padding    = max(len(theme) for theme in themes)
        themes_app = [theme.ljust(padding) for theme in themes]
        theme_app  = self.app.current_theme.name.ljust(padding)

        # Pad names of syntax-highlighting themes as well.
        themes        = sorted(self.editor.available_themes)
        padding       = max(len(theme) for theme in themes)
        themes_syntax = [theme.ljust(padding) for theme in themes]
        theme_syntax  = self.editor.theme.ljust(padding)

        # Get a map of binding ids to tooltip and key designation.
        bindings_map = {
            binding.id: (
                binding.tooltip,
                config.query(('keys', binding.id))
            )
            for binding in (bindings.application + bindings.editor)
        }

        with Vertical(id='frame') as frame:
            frame.border_title = 'Settings'

            with TabbedContent(id='panels'):

                with TabPane('Theme', id='theme-panel'):
                    with Grid(id='theme-grid'):
                        yield Label('application', classes='label')
                        yield Select.from_values(
                            values      = themes_app,
                            value       = theme_app,
                            allow_blank = False,
                            classes     = 'select',
                            id          = 'theme-app',
                        )
                        yield Label('code syntax', classes='label')
                        yield Select.from_values(
                            values      = themes_syntax,
                            value       = theme_syntax,
                            allow_blank = False,
                            classes     = 'select',
                            id          = 'theme-syntax',
                        )

                with TabPane('Keys', id='keys-panel'):
                    with VerticalScroll(id='keys-scroll', can_focus=False):
                        for (id, (tooltip, key)) in bindings_map.items():
                            with Horizontal(classes='row'):
                                yield KeyInput(key, id=id, classes='input')
                                yield Label(tooltip, classes='action')

            with Horizontal(id='buttons'):
                yield Button(
                    label   = 'Save',
                    variant = 'primary',
                    action  = 'screen.save',
                    id      = 'save',
                )
                yield Button(
                    label   = 'Cancel',
                    variant = 'default',
                    action  = 'screen.cancel',
                    id      = 'cancel',
                )

    def on_select_changed(self, event: Select.Changed):
        """Event triggered when an item was selected in a drop-down list."""
        match event.select.id:
            case 'theme-app':
                self.preview_theme_app(event.value.rstrip())
            case 'theme-syntax':
                self.preview_theme_syntax(event.value.rstrip())

    def on_key_input_changed(self, message: KeyInput.Changed):
        """Event triggered when user assigned a new key."""
        self.update_pending(('keys', message.id), message.key, message.old)

    def preview_theme_app(self, theme: str):
        """Previews the selected application theme."""
        now = self.app.current_theme.name
        if theme == now:
            return
        self.update_pending(('theme', 'app'), theme, now)
        self.app.theme = theme

    def preview_theme_syntax(self, theme: str):
        """Previews the selected syntax-highlighting theme."""
        now = self.editor.theme
        if theme == now:
            return
        self.update_pending(('theme', 'syntax'), theme, now)
        self.editor.theme = theme

    def update_pending(self,
        setting:   config.Setting,
        value_new: config.Value,
        value_now: config.Value,
    ):
        """Updates a setting pending to be changed on save."""
        if setting in self.pending:
            (_, value_old) = self.pending[setting]
            if value_new == value_old:
                del self.pending[setting]
                return
        self.pending[setting] = (value_new, value_now)

    def action_save(self):
        """Saves changed settings to disk."""
        for (setting, (value_new, _)) in self.pending.items():
            config.store(setting, value_new)
        self.app.configure_keys()
        self.dismiss()

    def action_cancel(self):
        """Rolls back settings changed for preview."""
        for (setting, (_, value_old)) in self.pending.items():
            match setting:
                case ('theme', 'app'):
                    self.app.theme = value_old
                case ('theme', 'syntax'):
                    self.editor.theme = value_old
        self.dismiss()
