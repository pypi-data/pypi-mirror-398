"""
Key bindings of application and widgets

The application and editor widgets don't inherit the default key bindings, as
indicated by the `inherit_bindings=False` subclass argument. We define them
explicitly so that we can drop certain default key bindings we don't care
about. As the lists of key bindings are quite long, they are defined here in
this separate module.

The actual keys the actions are bound to are defined in the configuration
files. The default key bindings are in `settings.yaml`, but the user may remap
them as they please in the user or site configuration. For that purpose, we
define an "id" for each binding here, which will be used to identify it in the
key map. The actual key values here are set to "<ignore>", because they aren't
actually used.

Find a list of accepted `key` values in Textual's `key.py` module. Find the
default key bindings for the `TextArea` widget in its `widgets/_text_area.py`.
Find a list of accepted `action` values in the reference documentation of the
[`TextArea` widget] via the names of the `action_*` methods.

[`TextArea` widget]: https://textual.textualize.io/widgets/text_area
"""

from textual.binding import Binding


application = [
    Binding(
        key         = '<ignore>',
        action      = 'quit',
        description = 'Quit',
        tooltip     = 'Quit app and return to command prompt.',
        id          = 'quit_app',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'show_help',
        description = 'Help',
        tooltip     = 'Show Help panel.',
        id          = 'show_help',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'command_palette',
        description = 'Palette',
        tooltip     = 'Show the command palette.',
        id          = 'command_palette',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'open_settings',
        description = 'Settings',
        tooltip     = 'Open Settings dialog.',
        show        = False,
        id          = 'open_settings',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'show_about',
        description = 'About',
        tooltip     = 'Show About panel.',
        show        = False,
        id          = 'show_about',
    ),
]


editor = [

    # File operations
    Binding(
        key         = '<ignore>',
        action      = 'save',
        description = 'Save',
        tooltip     = 'Save the file to disk.',
        id          = 'save',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'trim_whitespace',
        description = 'Trim white-space',
        tooltip     = 'Trim trailing white-space characters.',
        show        = False,
        id          = 'trim_whitespace',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'toggle_wrapping',
        description = 'Toggle wrapping',
        tooltip     = 'Toggle soft-wrapping of long lines.',
        show        = False,
        id          = 'toggle_wrapping',
    ),

    # Clipboard interaction
    Binding(
        key         = '<ignore>',
        action      = 'cut',
        description = 'Cut',
        tooltip     = 'Cut selected text and copy it to the clipboard.',
        show        = False,
        id          = 'cut',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'copy',
        description = 'Copy',
        tooltip     = 'Copy selected text to the clipboard.',
        show        = False,
        id          = 'copy',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'paste',
        description = 'Paste',
        tooltip     = 'Paste text from the clipboard.',
        show        = False,
        id          = 'paste',
    ),

    # Edit history
    Binding(
        key         = '<ignore>',
        action      = 'undo',
        description = 'Undo',
        tooltip     = 'Undo the latest editing changes.',
        show        = False,
        id          = 'undo',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'redo',
        description = 'Redo',
        tooltip     = 'Redo the latest undone editing changes.',
        show        = False,
        id          = 'redo',
    ),

    # Cursor movement
    Binding(
        key         = '<ignore>',
        action      = 'cursor_up',
        description = 'Up',
        tooltip     = 'Move cursor one line up.',
        show        = False,
        id          = 'cursor_up',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_down',
        description = 'Down',
        tooltip     = 'Move cursor one line down.',
        show        = False,
        id          = 'cursor_down',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_left',
        description = 'Left',
        tooltip     = 'Move cursor one character to the left.',
        show        = False,
        id          = 'cursor_left',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_right',
        description = 'Right',
        tooltip     = 'Move cursor one character to the right.',
        show        = False,
        id          = 'cursor_right',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_word_left',
        description = 'Word left',
        tooltip     = 'Move cursor one word to the left.',
        show        = False,
        id          = 'cursor_word_left',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_word_right',
        description = 'Word right',
        tooltip     = 'Move cursor one word to the right.',
        show        = False,
        id          = 'cursor_word_right',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_line_start',
        description = 'Home',
        tooltip     = 'Move cursor to start of line.',
        show        = False,
        id          = 'cursor_line_start',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_line_end',
        description = 'End',
        tooltip     = 'Move cursor to end of line.',
        show        = False,
        id          = 'cursor_line_end',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_page_up',
        description = 'Page up',
        tooltip     = 'Move cursor one screen page up.',
        show        = False,
        id          = 'cursor_page_up',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_page_down',
        description = 'Page down',
        tooltip     = 'Move cursor one screen page down.',
        show        = False,
        id          = 'cursor_page_down',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_file_start',
        description = 'File start',
        tooltip     = 'Move cursor to start of file.',
        show        = False,
        id          = 'cursor_file_start',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_file_end',
        description = 'File end',
        tooltip     = 'Move cursor to end of file.',
        show        = False,
        id          = 'cursor_file_end',
    ),

    # Text deletion
    Binding(
        key         = '<ignore>',
        action      = 'delete_left',
        description = 'Delete left',
        tooltip     = 'Delete character to the left of cursor.',
        show        = False,
        id          = 'delete_left',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'delete_right',
        description = 'Delete right',
        tooltip     = 'Delete character to the right of cursor.',
        show        = False,
        id          = 'delete_right',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'delete_word_left',
        description = 'Delete word left',
        tooltip     = 'Delete left from cursor to start of word.',
        show        = False,
        id          = 'delete_word_left',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'delete_word_right',
        description = 'Delete word right',
        tooltip     = 'Delete right from cursor until next word.',
        show        = False,
        id          = 'delete_word_right',
    ),

    # Selections
    Binding(
        key         = '<ignore>',
        action      = 'cursor_left(True)',
        description = 'Select left',
        tooltip     = 'Select character to the left of cursor.',
        show        = False,
        id          = 'select_left',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_right(True)',
        description = 'Select right',
        tooltip     = 'Select character to the right of cursor.',
        show        = False,
        id          = 'select_right',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_word_left(True)',
        description = 'Select word left',
        tooltip     = 'Select from cursor to start of word to the left.',
        show        = False,
        id          = 'select_word_left',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_word_right(True)',
        description = 'Select word right',
        tooltip     = 'Select from cursor to end of word to the right.',
        show        = False,
        id          = 'select_word_right',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_line_start(True)',
        description = 'Select to line start',
        tooltip     = 'Select from cursor until start of line.',
        show        = False,
        id          = 'select_line_start',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_line_end(True)',
        description = 'Select to line end',
        tooltip     = 'Select from cursor until end of line.',
        show        = False,
        id          = 'select_line_end',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_up(True)',
        description = 'Select line up',
        tooltip     = 'Select one line up from cursor.',
        show        = False,
        id          = 'select_line_up',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'cursor_down(True)',
        description = 'Select line down',
        tooltip     = 'Select one line down from cursor.',
        show        = False,
        id          = 'select_line_down',
    ),
    Binding(
        key         = '<ignore>',
        action      = 'select_all',
        description = 'Select all',
        tooltip     = 'Select all text.',
        show        = False,
        id          = 'select_all',
    ),
]


horizontal_buttons = [
    Binding(
        key    = '<ignore>',
        action = 'app.focus_next',
        show   = False,
    ),
    Binding(
        key    = '<ignore>',
        action = 'app.focus_previous',
        show   = False,
    ),
    Binding(
        key    = '<ignore>',
        action = 'cancel',
        show   = False,
    ),
]


vertical_buttons = [
    Binding(
        key    = '<ignore>',
        action = 'app.focus_next',
        show   = False,
    ),
    Binding(
        key    = '<ignore>',
        action = 'app.focus_previous',
        show   = False,
    ),
    Binding(
        key    = '<ignore>',
        action = 'cancel',
        show   = False,
    ),
]


def key_display(key: str) -> str:
    """Formats a Textual key designation for (nicer) display in the app."""
    rename = {
        'escape':   'Esc',
        'delete':   'Del',
        'pageup':   'PgUp',
        'pagedown': 'PgDn',
        'backspace': '⌫',
        'tab':       '⇥',
        'enter':     '↵',
        'up':        '↑',
        'down':      '↓',
        'left':      '←',
        'right':     '→',
    }
    parts = [rename.get(part, part.title()) for part in key.split('+')]
    display = (
        '+'.join(parts)
        .replace('Ctrl+', '^')
        .replace('Shift+', '⇧')
    )
    return display
