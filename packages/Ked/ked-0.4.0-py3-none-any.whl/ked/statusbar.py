"""Custom footer showing key bindings and editor status"""

from textual.widgets         import Footer
from textual.widgets._footer import FooterKey
from textual.widgets         import Label
from textual.containers      import Horizontal
from textual.app             import ComposeResult
from textual.reactive        import reactive

from pathlib import Path


class Statusbar(Footer):
    """Footer showing key bindings and status of edited file"""

    file: reactive[Path | None] = reactive(None)
    """The file being edited."""

    encoding: reactive[str] = reactive('')
    """The text encoding of the file."""

    newline: reactive[str] = reactive('')
    """The line endings of the file."""

    cursor: reactive[tuple[int, int]] = reactive((1, 1))
    """The current cursor position in the editor."""

    DEFAULT_CSS = """
        $footer-key-foreground: $primary;
        #key-bindings {
            align-horizontal: left;
            FooterKey {
                border-right:  solid $surface;
                padding-left:  1;
                padding-right: 1;
            }
            FooterKey:last-child {
                border-right: none;
            }
        }
        #edit-status {
            align-horizontal: right;
            Label {
                border-right:  solid $surface;
                padding-left:  1;
                padding-right: 1;
            }
            Label:last-child {
                border-right:  none;
            }
        }
    """

    def compose(self) -> ComposeResult:
        """Composes the widget."""

        with Horizontal(id='key-bindings'):
            active_bindings = self.screen.active_bindings
            app_bindings    = {}
            other_bindings  = {}
            for (key, (node, binding, enabled, _)) in active_bindings.items():
                if not binding.show:
                    continue
                if node is self.app:
                    app_bindings[key] = (binding, enabled)
                else:
                    other_bindings[key] = (binding, enabled)
            sorted_bindings = app_bindings | other_bindings
            for (key, (binding, enabled)) in sorted_bindings.items():
                yield FooterKey(
                    key,
                    self.app.get_key_display(binding),
                    binding.description,
                    binding.action,
                    disabled=not enabled,
                    tooltip=binding.tooltip,
                )

        with Horizontal(id='edit-status'):
            yield CursorPosition(id='cursor-position').data_bind(
                Statusbar.cursor
            )
            yield LineEndings(id='line-endings').data_bind(Statusbar.newline)
            yield TextEncoding(id='text-encoding').data_bind(
                Statusbar.encoding
            )
            yield FileName(id='file-name').data_bind(Statusbar.file)


class FileName(Label):
    """Displays the file name."""

    file: reactive[None] = reactive(None, layout=True)

    def render(self) -> str:
        if self.file is None:
            self.tooltip = ''
            return ''
        self.tooltip = str(self.file)
        return self.file.name


class TextEncoding(Label):
    """Displays the detected text encoding of the file."""

    encoding: reactive[str] = reactive('', layout=True)

    def render(self) -> str:
        match self.encoding:
            case 'utf-8':
                self.tooltip = 'Text encoding is UTF-8.'
                return 'UTF-8'
            case 'utf-8-sig':
                self.tooltip = 'Text encoding is UTF-8 with a byte-order mark.'
                return 'UTF8-BOM'
            case _:
                return self.encoding


class LineEndings(Label):
    """Displays the detected line endings of the file."""

    newline: reactive[str] = reactive('', layout=True)

    def render(self) -> str:
        match self.newline:
            case '\r\n':
                self.tooltip = (
                    'Windows-like line endings:\n'
                    'carriage-return plus line-feed'
                )
                return 'CRLF'
            case '\n':
                self.tooltip = (
                    'Unix-like line endings:\n'
                    'a single line-feed character'
                )
                return 'LF'
            case _:
                self.tooltip = 'Unrecognized line endings.'
                return self.newline.replace('\r', 'CR').replace('\n', 'LF')


class CursorPosition(Label):
    """Displays the current cursor position in the file."""

    cursor: reactive[tuple[int, int]] = reactive((1, 1), layout=True)

    def render(self) -> str:
        (line, column) = self.cursor
        line += 1
        column += 1
        self.tooltip = f'The cursor is on line {line} in column {column}.'
        return f'{line},{column}'
