"""Command-line interface of the application"""

from .    import meta
from .    import config
from .tui import TUI

from cyclopts import App, Parameter, Group

from typing  import Annotated
from pathlib import Path


prolog = f"""
{meta.name}: {meta.summary}

Usage: {meta.name} [FILE | COMMAND]
"""

epilog = """
If the file name happens to coincide with one of the commands, use the "edit"
command explicitly.
"""

cli = App(
    name             = meta.name,
    version          = meta.version,
    help             = prolog,
    usage            = '',
    help_epilogue    = epilog,
    help_flags       = '--help',
    group_arguments  = Group('Argument', sort_key=1),
    group_commands   = Group('Commands', sort_key=2),
    group_parameters = Group('Options',  sort_key=3),
)

cli['--help'].group    = 'Options'
cli['--help'].help     = 'Display this help message.'
cli['--version'].group = 'Options'

cli.command(config.cli)


@cli.default()
def default(
    file: Annotated[Path, Parameter(name=['FILE'])] = None,
    /,              # Make this a positional argument only, no "--file" option.
) -> int:
    """
    The default command that runs if no other command matched.

    :param file:
        The file to edit.
    """
    if file is None:
        cli.help_print()
        return 0
    return edit(file)


@cli.command(sort_key=1, help_epilogue='')
def edit(file: Path) -> int:
    """Edit an existing file. (default)"""
    if not file.exists():
        error(f'File "{file}" does not exist.')
        print('To create a file and then edit it, use the "create" command.')
        return 1
    if file.is_dir():
        error(f'"{file}" is a directory.')
        return 2
    return start(file)


@cli.command(sort_key=2, help_epilogue='')
def create(file: Path) -> int:
    """Create a new file and edit it."""
    if file.exists():
        error(f'File "{file}" already exist.')
        print('Use the "edit" (or no) command to open it.')
        return 3
    file.touch()
    return start(file)


def print(message: str):
    """Displays a `message` in the terminal."""
    cli.console.print(message)


def error(message: str):
    """Displays an error `message` in the terminal."""
    cli.error_console.print(f'[bold red]Error:[/bold red] {message}')


def start(file: Path) -> int:
    """Starts the text-based user interface with the given `file` loaded."""
    tui = TUI()
    tui.file = file
    error_message = tui.run()
    if error_message:
        exit_code = tui.return_code if tui.return_code else 255
        error(error_message)
    else:
        exit_code = tui.return_code if tui.return_code else 0
    return exit_code
