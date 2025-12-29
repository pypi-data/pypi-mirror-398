"""Meta information about the application"""

from importlib.metadata import metadata


name    = metadata(__package__).get('name')
version = metadata(__package__).get('version')
summary = metadata(__package__).get('summary')

del metadata
