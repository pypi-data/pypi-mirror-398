# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance deferred update using Berkeley DB via berkeleydb."""

import berkeleydb.db

from solentware_base import berkeleydbdu_database
from solentware_base import berkeleydb_database

from ..shared import dbdu
from ..shared import alldu


class BerkeleydbDatabaseduError(Exception):
    """Exception class for berkeleydb.database_du module."""


class Database(alldu.Alldu, dbdu.Dbdu, berkeleydbdu_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, DBfile, **kargs):
        """Delegate with BerkeleydbDatabaseduError as exception class."""
        super().__init__(
            DBfile,
            BerkeleydbDatabaseduError,
            (
                berkeleydb.db.DB_CREATE
                | berkeleydb.db.DB_RECOVER
                | berkeleydb.db.DB_INIT_MPOOL
                | berkeleydb.db.DB_INIT_LOCK
                | berkeleydb.db.DB_INIT_LOG
                | berkeleydb.db.DB_INIT_TXN
                | berkeleydb.db.DB_PRIVATE
            ),
            **kargs
        )


class DatabaseSU(alldu.Alldu, dbdu.Dbdu, berkeleydb_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, DBfile, **kargs):
        """Delegate with BerkeleydbDatabaseduError as exception class."""
        super().__init__(
            DBfile,
            BerkeleydbDatabaseduError,
            (
                berkeleydb.db.DB_CREATE
                | berkeleydb.db.DB_RECOVER
                | berkeleydb.db.DB_INIT_MPOOL
                | berkeleydb.db.DB_INIT_LOCK
                | berkeleydb.db.DB_INIT_LOG
                | berkeleydb.db.DB_INIT_TXN
                | berkeleydb.db.DB_PRIVATE
            ),
            **kargs
        )

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
