# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation database using Berkeley DB via bsddb3."""

from bsddb3.db import (
    # DB_BTREE,
    # DB_HASH,
    # DB_RECNO,
    # DB_DUPSORT,
    DB_CREATE,
    DB_RECOVER,
    DB_INIT_MPOOL,
    DB_INIT_LOCK,
    DB_INIT_LOG,
    DB_INIT_TXN,
    DB_PRIVATE,
)

from solentware_base import bsddb3_database

from ..core.filespec import FileSpec
from ..basecore import database


class Database(database.Database, bsddb3_database.Database):
    """Methods and data structures to create, open, and close database."""

    _deferred_update_process = "chesscalc.db.database_du"

    def __init__(
        self,
        DBfile,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define database specification and environment then delegate."""
        dbnames = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        environment = {
            "flags": (
                DB_CREATE
                | DB_RECOVER
                | DB_INIT_MPOOL
                | DB_INIT_LOCK
                | DB_INIT_LOG
                | DB_INIT_TXN
                | DB_PRIVATE
            ),
        }

        super().__init__(
            dbnames,
            DBfile,
            environment,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def delete_database(self):
        """Close and delete the open chess results database."""
        return super().delete_database(
            (
                self.database_file,
                "-".join((self.database_file, "lock")),
                self.dbenv.get_lg_dir().decode(),
            )
        )
