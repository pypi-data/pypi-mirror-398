"""Editor widget central to the application"""

from . import config
from . import bindings

from textual.widgets           import TextArea
from textual.widgets.text_area import Edit
from textual.reactive          import reactive
from textual.message           import Message
from textual.events            import Key
from textual.events            import MouseDown

import os
import tokenize
from pathlib import Path


class Editor(TextArea, inherit_bindings=False):
    """Main widget for editing a file"""

    file: reactive[Path | None] = reactive(None)
    """file being edited"""

    encoding: str = ''
    """detected text encoding of the file"""

    newline: str = ''
    """character sequence marking line endings in the file"""

    saved_as: list[list[Edit]] = None
    """undo stack when file was last saved or first loaded"""

    class FileLoaded(Message):
        """Message posted when a file was loaded."""

    class EncodingDetected(Message):
        """Message posted when text encoding was detected."""

    class NewlineDetected(Message):
        """Message posted when line endings were detected."""

    class CursorMoved(Message):
        """Message posted when cursor was moved."""

    BINDINGS = bindings.editor

    DEFAULT_CSS = """
        Editor {
            border:  round $border;
            padding: 0;
        }
    """

    def __init__(self, id: str = 'editor'):
        super().__init__(
            id                = id,
            soft_wrap         = False,
            tab_behavior      = 'indent',
            show_line_numbers = False,
            max_checkpoints   = 1000,
            theme             = 'css',
        )

    def on_mount(self):
        """Event triggered when widget is ready to process messages."""
        self.theme = config.query(('theme', 'syntax'))

    def watch_file(self, file: Path | None):
        """Loads file whenever the reactive `file` attribute changes."""

        if file is None:
            return

        language = infer_language(file)
        if language in self.available_languages:
            self.language = language
        else:
            self.language = None

        encoding = detect_encoding(file)
        self.encoding = encoding
        self.post_message(self.EncodingDetected())

        with file.open(encoding=self.encoding) as stream:
            self.load_text(stream.read())
            newlines = stream.newlines

        if newlines is None:
            newlines = os.linesep
        elif isinstance(newlines, str):
            pass
        elif isinstance(newlines, tuple):
            self.app.exit('File contains mixed line endings.', return_code=11)
        else:
            raise TypeError(f'Unexpected type for "newlines": {newlines}')
        self.newline = newlines
        self.post_message(self.NewlineDetected())

        self.file = file
        self.post_message(self.FileLoaded())
        self.saved_as = self.history.undo_stack.copy()
        self.post_message(self.CursorMoved())

    def on_key(self, _event: Key):
        """Event triggered when the user presses a key."""
        self.post_message(self.CursorMoved())

    def on_mouse_up(self, _event: MouseDown):
        """Event triggered when the user releases a mouse button."""
        self.post_message(self.CursorMoved())

    def on_text_area_changed(self):
        """Event triggered when the user modified the text."""
        self.refresh_bindings()

    def action_save(self):
        """Saves the file to disk."""
        if not self.file:
            return
        self.file.write_text(
            self.text, encoding=self.encoding, newline=self.newline
        )
        self.saved_as = self.history.undo_stack.copy()
        self.refresh_bindings()

    def action_trim_whitespace(self):
        """Trims trailing white-space characters."""
        changed = False

        trims = 0
        for n in range(self.document.line_count):
            line = self.document.get_line(n)
            trimmed = line.rstrip(' \t')
            if trimmed != line:
                self.delete(start=(n, len(trimmed)), end=(n, len(line)))
                trims += 1
        if trims > 0:
            noun = 'line' if trims == 1 else 'lines'
            self.notify(f'Trimmed trailing white-space on {trims} {noun}.')
            changed = True

        n = self.document.line_count - 1
        last_line = self.document.get_line(n)
        if last_line != '':
            self.insert('\n', location=(n, len(last_line)))
            self.notify('Appended a blank line.')
            changed = True

        n = self.document.line_count - 2
        m = n
        while self.document.get_line(m) == '' and m >= 0:
            m -= 1
        if (m != n):
            self.delete(start=(m+1, 0), end=(n+1, 0))
            noun = 'line' if n - m == 1 else 'lines'
            self.notify(f'Deleted {n - m} trailing blank {noun}.')
            changed = True

        if not changed:
            self.notify('No trailing white-space to trim.')
        else:
            self.move_cursor(self.cursor_location)
            self.post_message(self.CursorMoved())
            self.refresh_bindings()

    def action_toggle_wrapping(self):
        """Toggles the soft-wrapping of lines."""
        self.soft_wrap = not self.soft_wrap

    def action_cursor_file_start(self):
        """Moves cursor to start of file."""
        self.move_cursor((0, 0))
        self.post_message(self.CursorMoved())

    def action_cursor_file_end(self):
        """Moves cursor to end of file."""
        y = self.document.line_count - 1
        x = len(self.document.get_line(y))
        self.move_cursor((y, x))
        self.post_message(self.CursorMoved())

    def check_action(self, action: str, _: tuple[object, ...]) -> bool | None:
        """Marks actions as currently available or not."""
        if action == 'save' and self.file and not self.modified:
            return None
        return True

    @property
    def modified(self):
        """Returns whether the file has been modified since it was saved."""
        return (self.history.undo_stack != self.saved_as)


def detect_encoding(file: Path) -> str:
    """
    Detects the text encoding of the given file.

    Uses the `tokenize` module from the Python standard library under the hood,
    and is thus limited to the same encodings.
    """
    with file.open('rb') as stream:
        (encoding, _line) = tokenize.detect_encoding(stream.readline)
    return encoding


def infer_language(file: Path) -> str:
    """Infers the syntax-highlighting language from the file extension."""
    match file.stem:
        case '.profile':
            return 'bash'
        case '.bashrc' | '.bash_logout':
            return 'bash'
        case '.zshrc':
            return 'bash'
    match file.suffix:
        case '.md':
            return 'markdown'
        case '.json':
            return 'json'
        case '.yaml' | '.yml':
            return 'yaml'
        case '.toml':
            return 'toml'
        case '.xml':
            return 'xml'
        case '.html' | '.htm':
            return 'html'
        case '.css':
            return 'css'
        case '.js':
            return 'javascript'
        case '.sh' | '.bash' | '.zsh' | '.fish':
            return 'bash'
        case '.py' | '.pyw':
            return 'python'
        case '.rs':
            return 'rust'
        case '.sql':
            return 'sql'
        case '.go':
            return 'go'
        case '.java':
            return 'java'
        case '.kt' | '.kts':
            return 'kotlin'
    return ''
