"""Persistent storage of configuration settings"""
from . import meta

import cyclopts
import platformdirs
import yaml

from functools import cache
from pathlib   import Path
from typing    import TypeAlias
from types     import NoneType
from typing    import Literal
from typing    import Union


user_dir: Path = platformdirs.user_config_path() / meta.name
"""folder with the per-user configuration"""

site_dir  = platformdirs.site_config_path() / meta.name
"""folder with the machine-wide configuration"""

file_name = 'settings.yaml'
"""name of file that stores the settings in a configuration folder"""

Setting:  TypeAlias = tuple[str, ...]
Value:    TypeAlias = str | float | int | bool
Settings: TypeAlias = dict[str, Union[Value, 'Settings']]

cli = cyclopts.App(
    name          = 'config',
    sort_key      = 3,
    help          = 'Manage the configuration.',
    help_epilogue = '',
)


@cli.command(sort_key=1)
def folders():
    """Show the configuration folders."""
    labels  = ('user config folder', 'site config folder')
    folders = (user_dir, site_dir)
    for (label, folder) in zip(labels, folders, strict=True):
        if folder.exists():
            cli.console.print(f'{label}: [bold]{folder}[/]')
        else:
            cli.console.print(f'[dim]{label}: {folder}')


@cli.command(sort_key=2)
def files():
    """Show the configuration files."""
    here    = Path(__file__).parent
    labels  = ('user config file', 'site config file', 'default config')
    files   = (user_dir/file_name, site_dir/file_name, here/file_name)
    padding = max(len(label) for label in labels) + 1
    for (label, file) in zip(labels, files, strict=True):
        if file.exists():
            cli.console.print(f'{label+":":{padding}} [bold]{file}[/]')
        else:
            cli.console.print(f'[dim]{label+":":{padding}} {file}')


def query(
    setting: Setting,
    source:  Literal['user', 'site', 'default', 'all'] = 'all',
) -> Value:
    """Queries the value of a `setting` from configuration `source` file(s)."""
    if not isinstance(setting, tuple):
        raise TypeError('Argument `setting` must be a tuple of strings.')
    if setting == ():
        raise ValueError('Argument `setting` cannot be an empty tuple.')
    match source:
        case 'user' | 'site' | 'default':
            sources = (source,)
        case 'all':
            sources = ('user', 'site', 'default')
    for source in sources:
        value = query_value(setting, load(source))
        if value is not None:
            break
    else:
        raise KeyError(f'Setting "{setting}" not found in configuration.')
    return value


def store(
    setting: Setting,
    value:   Value,
    target:  Literal['user', 'site'] = 'user',
):
    """Stores the `value` of a `setting` in `target` configuration file."""
    match target:
        case 'user':
            folder = user_dir
        case 'site':
            folder = site_dir

    file = folder/file_name
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('', encoding='UTF-8-sig')

    settings = load(target)
    store_value(setting, value, settings)
    load.cache_clear()
    save(settings, target)


@cache
def load(source: Literal['user', 'site', 'default']) -> Settings:
    """
    Loads settings from requested configuration `source`.

    This function is cached, i.e. the file corresponding to the given source
    will only be read from disk once. If the file ever changes, call
    `load_file.clear_cache()` to invalidate the cache.
    """
    match source:
        case 'user':
            file = user_dir / file_name
        case 'site':
            file = site_dir / file_name
        case 'default':
            here = Path(__file__).parent
            file = here / file_name
    if not file.exists():
        return {}
    settings = yaml.safe_load(file.read_text(encoding='UTF-8-sig'))
    if isinstance(settings, (NoneType, str)):
        return {}
    return settings


def save(settings: Settings, target: Literal['user', 'site', 'default']):
    """Saves settings in `target` configuration file."""
    match target:
        case 'user':
            file = user_dir / file_name
        case 'site':
            file = site_dir / file_name
        case 'default':
            here = Path(__file__).parent
            file = here / file_name
    file.write_text(
        yaml.dump(settings, indent=4, allow_unicode=True),
        encoding='UTF-8-sig',
    )


def query_value(setting: Setting, settings: Settings) -> Value | None:
    """Retrieves the value of the `setting` in the `settings` dictionary."""
    key = setting[0]
    if key not in settings:
        return None
    if len(setting) == 1:
        return settings[key]
    return query_value(setting[1:], settings[key])


def store_value(setting: Setting, value: Value, settings: Settings):
    """Stores the `value` of the `setting` in the `settings` dictionary."""
    key = setting[0]
    if len(setting) == 1:
        settings[key] = value
        return
    if key not in settings:
        settings[key] = {}
    store_value(setting[1:], value, settings[key])
