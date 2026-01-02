# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database deferred update using Vedis via vedis."""

from solentware_base import vedisdu_database
from solentware_base import vedis_database

from ..shared import litedu
from ..shared import alldu


class VedisDatabaseduError(Exception):
    """Exception class for vedis.database_du module."""


class Database(alldu.Alldu, litedu.Litedu, vedisdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, vedisfile, **kargs):
        """Delegate with VedisDatabaseduError as exception class."""
        super().__init__(vedisfile, VedisDatabaseduError, **kargs)


class DatabaseSU(alldu.Alldu, litedu.Litedu, vedis_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, vedisfile, **kargs):
        """Delegate with VedisDatabaseduError as exception class."""
        super().__init__(vedisfile, VedisDatabaseduError, **kargs)

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
