# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance deferred update using Berkeley DB via tkinter."""

from solentware_base import db_tkinterdu_database
from solentware_base import db_tkinter_database

from ..shared import dbdu
from ..shared import alldu


class DbtkinterDatabaseduError(Exception):
    """Exception class for db_tkinter.database_du module."""


class Database(alldu.Alldu, dbdu.Dbdu, db_tkinterdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, DBfile, **kargs):
        """Delegate with DbtkinterDatabaseduError as exception class."""
        super().__init__(
            DBfile,
            DbtkinterDatabaseduError,
            ("-create", "-recover", "-txn", "-private", "-system_mem"),
            **kargs
        )


class DatabaseSU(alldu.Alldu, dbdu.Dbdu, db_tkinter_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, DBfile, **kargs):
        """Delegate with DbtkinterDatabaseduError as exception class."""
        super().__init__(
            DBfile,
            DbtkinterDatabaseduError,
            ("-create", "-recover", "-txn", "-private", "-system_mem"),
            **kargs
        )

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
