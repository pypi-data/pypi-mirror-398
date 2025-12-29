"""About panel of the application"""

from .meta import version

from textual.screen     import ModalScreen
from textual.containers import VerticalScroll
from textual.containers import Center
from textual.widgets    import Markdown
from textual.widgets    import Label
from textual.color      import Color
from textual.color      import Gradient
from textual.app        import ComposeResult
from rich.text          import Text


logo = rf"""
     ___           ___          {version}
    /|  |         /\__\         _____
   |:|  |        /:/ _/_       /::\  \
   |:|  |       /:/ /\__\     /:/\:\  \
 __|:|  |      /:/ /:/ _/_   /:/  \:\__\
/\ |:|__|____ /:/_/:/ /\__\ /:/__/ \:|__|
\:\/:::::/__/ \:\/:/ /:/  / \:\  \ /:/  /
 \::/~~/~      \::/_/:/  /   \:\  /:/  /
  \:\~~\        \:\/:/  /     \:\/:/  /
   \:\__\        \::/  /       \::/  /
    \/__/         \/__/         \/__/
        Copyright © John Hennig
""".lstrip('\n')

text = """

Ked is a single-file text editor that runs in the terminal. Its interface is
intentionally simple, while its default key bindings resemble those of desktop
applications.


### Credits

Ked is built in Python on top of the excellent TUI framework [Textual]. It uses
[Cyclopts] for the command-line interface.

[Textual]:  https://textual.textualize.io
[Cyclopts]: https://cyclopts.readthedocs.io


### Why Ked?

I refuse to use [Vim] for the sake of my muscle memory, and [Nano] won't let me
rebind all the keys that I want.

As for the name, no particular reason. It was available on [PyPI], while names
I would have preferred weren't. Nonetheless, it is quick to type, and has "ed"
in it, as in "edit" or "editor".

[Vim]:  https://neovim.io
[Nano]: https://www.nano-editor.org
[PyPI]: https://pypi.org


### License

Ked is licensed [CC-BY-NC-ND-4.0], i.e. under a Creative Commons license that
allows non-commercial use and distribution, but requires attribution, forbids
commercial use and derivatives.

It is *not* an open-source license. But the source code is publicly available.
I (the author) am currently not looking for contributions. I may (or may not)
move to a more permissive license once the application is more mature. But
first and foremost, this is a personal project.

[CC-BY-NC-ND-4.0]: https://creativecommons.org/licenses/by-nc-nd/4.0
"""


class About(ModalScreen):
    """About panel of the application"""

    DEFAULT_CSS = """
        About {
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
        #logo {
            text-style: bold;
        }
        #text {
        }
    """

    BINDINGS = (
        ('escape', 'dismiss'),
    )

    def compose(self) -> ComposeResult:
        with VerticalScroll(id='frame') as frame:
            frame.border_title = 'About'
            with Center():
                label = horizonal_gradient(
                    logo,
                    start = Color.parse(self.app.theme_variables['primary']),
                    end   = Color.parse(self.app.theme_variables['accent']),
                )
                label.id = 'logo'
                yield label
            yield Markdown(text, id='text')


def vertical_gradient(text: str, start: Color, end: Color) -> Label:
    """Colors the text with a vertical gradient along the lines."""
    gradient = Gradient((0, start), (1, end))
    lines = text.splitlines(keepends=True)
    max_lines = len(lines)
    colors = (
        gradient.get_rich_color(line/(max_lines-1)).name
        for line in range(max_lines)
    )
    styled_text = Text.assemble(*zip(lines, colors, strict=True))
    return Label(styled_text)


def horizonal_gradient(text: str, start: Color, end: Color) -> Label:
    """Colors the text with a horizontal gradient along the columns."""
    gradient = Gradient((0, start), (1, end))
    lines = text.splitlines(keepends=True)
    max_columns = max(len(line) for line in lines)
    styled_text = Text()
    for line in lines:
        styled_line = Text(line)
        for column in range(len(line)):
            color = gradient.get_rich_color(column/(max_columns-1)).name
            styled_line.stylize(color,  start=column, end=column+1)
        styled_text.append_text(styled_line)
    return Label(styled_text)
