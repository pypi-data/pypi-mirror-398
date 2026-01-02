# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database deferred update using Unqlite via unqlite."""

from solentware_base import unqlitedu_database
from solentware_base import unqlite_database

from ..shared import litedu
from ..shared import alldu


class UnqliteDatabaseduError(Exception):
    """Exception class for unqlite.database_du module."""


class Database(alldu.Alldu, litedu.Litedu, unqlitedu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, unqlitefile, **kargs):
        """Delegate with UnqliteDatabaseduError as exception class."""
        super().__init__(unqlitefile, UnqliteDatabaseduError, **kargs)


class DatabaseSU(alldu.Alldu, litedu.Litedu, unqlite_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, unqlitefile, **kargs):
        """Delegate with UnqliteDatabaseduError as exception class."""
        super().__init__(unqlitefile, UnqliteDatabaseduError, **kargs)

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
