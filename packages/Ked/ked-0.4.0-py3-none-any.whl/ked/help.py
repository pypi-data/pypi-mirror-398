"""Help panel showing key bindings"""

from textual.screen     import ModalScreen
from textual.containers import VerticalScroll
from textual.widgets    import Markdown
from textual.widgets    import Static
from textual.app        import ComposeResult
from rich.table         import Table
from rich.text          import Text
from rich.style         import Style


prolog = """
The following key bindings have been configured:
"""

epilog = """
If any of the key bindings don't work, it may be that they are already in use
by your terminal emulator. The terminal will only forward the combinations it
isn't reacting to itself to the application that is running inside it.

In a future version, the above key bindings will be configurable. But in the
meantime, you may consider changing the settings of your terminal to make sure
its key bindings don't clash with the editor.
"""


class Help(ModalScreen):
    """Help panel showing key bindings"""

    DEFAULT_CSS = """
        Help {
            align: right top;
        }
        #frame {
            border:           round $border;
            background:       $surface;
            margin:           2 4;
            width:            70;
            min-height:       15;
            min-width:        50;
            scrollbar-gutter: stable;
        }
        #prolog {
            margin-top: 1;
        }
        #keys {
        }
        #epilog {
            margin-top: 1;
        }
    """

    BINDINGS = (
        ('escape', 'dismiss'),
    )

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='frame') as frame:
            frame.border_title = 'Help'
            yield Markdown(prolog, id='prolog')
            yield KeyBindings(id='keys')
            yield Markdown(epilog, id='epilog')


class KeyBindings(Static):
    """Widget displaying a table with the key bindings"""

    def render(self) -> Table:
        editor = self.app.query_exactly_one('#editor')
        screen = editor.screen
        app_bindings    = {}
        editor_bindings = {}
        other_bindings  = {}
        for (key, (node, binding, _, _)) in screen.active_bindings.items():
            if node is self.app:
                app_bindings[key] = binding
            elif node is editor:
                editor_bindings[key] = binding
            else:
                other_bindings[key] = binding
        bindings_groups = {
            'Application': app_bindings,
            'Editor':      editor_bindings,
            'Other':       other_bindings,
        }
        table = Table(
            show_header = False,
            box         = None,
            padding     = (0, 1),
            pad_edge    = False,
        )
        primary     = self.app.theme_variables['primary']
        title_style = Style(color=primary, bold=True)
        key_style   = Style(color=primary)
        table.add_column('key', justify='right', style=key_style)
        table.add_column('description')
        for (title, bindings) in bindings_groups.items():
            if table.rows:
                table.add_row('', '')
            table.add_row('', Text(title, style=title_style, end=''))
            for binding in bindings.values():
                table.add_row(
                    self.app.get_key_display(binding),
                    binding.tooltip if binding.tooltip else binding.description
                )
        return table
