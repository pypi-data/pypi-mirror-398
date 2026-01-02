# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance database deferred update using Sqlite 3 via apsw."""

from solentware_base import apswdu_database
from solentware_base import apsw_database

from ..shared import litedu
from ..shared import alldu


class ApswDatabaseduError(Exception):
    """Exception class for apsw.database_du module."""


class Database(alldu.Alldu, litedu.Litedu, apswdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with ApswDatabaseduError as exception class."""
        super().__init__(sqlite3file, ApswDatabaseduError, **kargs)


class DatabaseSU(alldu.Alldu, litedu.Litedu, apsw_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, sqlite3file, **kargs):
        """Delegate with ApswDatabaseduError as exception class."""
        super().__init__(sqlite3file, ApswDatabaseduError, **kargs)

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
