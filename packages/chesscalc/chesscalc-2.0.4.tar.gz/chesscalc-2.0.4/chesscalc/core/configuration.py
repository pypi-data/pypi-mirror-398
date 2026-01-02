# configuration.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Access and update items in a configuration file.

The initial values are taken from file named in self._CONFIGURATION in the
user's home directory if the file exists.

"""
from solentware_misc.core import configuration

from . import constants


class Configuration(configuration.Configuration):
    """Identify configuration and recent files and delegate to superclass."""

    _CONFIGURATION = ".chesscalc.conf"
    _DEFAULT_ITEM_VAULES = (
        (constants.RECENT_DATABASE, "~"),
        (constants.RECENT_PGN_DIRECTORY, "~"),
        (constants.RECENT_IMPORT_DIRECTORY, "~"),
    )
