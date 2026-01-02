# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database deferred update using Sqlite 3 via sqlite3."""

from solentware_base import sqlite3du_database
from solentware_base import sqlite3_database

from ..shared import litedu
from ..shared import alldu


class Sqlite3DatabaseduError(Exception):
    """Exception class for sqlite.database_du module."""


class Database(alldu.Alldu, litedu.Litedu, sqlite3du_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with Sqlite3DatabaseduError as exception class."""
        super().__init__(sqlite3file, Sqlite3DatabaseduError, **kargs)


class DatabaseSU(alldu.Alldu, litedu.Litedu, sqlite3_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with Sqlite3DatabaseduError as exception class."""
        super().__init__(sqlite3file, Sqlite3DatabaseduError, **kargs)

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
