# database_du.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess performance deferred update using Berkeley DB via bsddb3."""

import bsddb3.db

from solentware_base import bsddb3du_database
from solentware_base import bsddb3_database

from ..shared import dbdu
from ..shared import alldu


class Bsddb3DatabaseduError(Exception):
    """Exception class for db.database_du module."""


class Database(alldu.Alldu, dbdu.Dbdu, bsddb3du_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, DBfile, **kargs):
        """Delegate with Bsddb3DatabaseduError as exception class."""
        super().__init__(
            DBfile,
            Bsddb3DatabaseduError,
            (
                bsddb3.db.DB_CREATE
                | bsddb3.db.DB_RECOVER
                | bsddb3.db.DB_INIT_MPOOL
                | bsddb3.db.DB_INIT_LOCK
                | bsddb3.db.DB_INIT_LOG
                | bsddb3.db.DB_INIT_TXN
                | bsddb3.db.DB_PRIVATE
            ),
            **kargs
        )


class DatabaseSU(alldu.Alldu, dbdu.Dbdu, bsddb3_database.Database):
    """Provide custom deferred update for chess performance database."""

    def __init__(self, DBfile, **kargs):
        """Delegate with Bsddb3DatabaseduError as exception class."""
        super().__init__(
            DBfile,
            Bsddb3DatabaseduError,
            (
                bsddb3.db.DB_CREATE
                | bsddb3.db.DB_RECOVER
                | bsddb3.db.DB_INIT_MPOOL
                | bsddb3.db.DB_INIT_LOCK
                | bsddb3.db.DB_INIT_LOG
                | bsddb3.db.DB_INIT_TXN
                | bsddb3.db.DB_PRIVATE
            ),
            **kargs
        )

    # Class structure implies this is not an override at present.
    def deferred_update_housekeeping(self):
        """Override to do nothing."""
