# database.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Chess Performance Calculation database using Sqlite3 via sqlite3."""

from solentware_base import sqlite3_database

from ..core.filespec import FileSpec
from ..basecore import database


class Database(database.Database, sqlite3_database.Database):
    """Methods and data structures to create, open, and close database."""

    _deferred_update_process = "chesscalc.sqlite.database_du"

    # The sqlite3 interface gives a sqlite3.programmingerror exception if
    # database actions are not done in the main thread.
    can_use_thread = False

    def __init__(
        self,
        sqlite3file,
        use_specification_items=None,
        dpt_records=None,
        **kargs,
    ):
        """Define database specification then delegate."""
        names = FileSpec(
            use_specification_items=use_specification_items,
            dpt_records=dpt_records,
        )

        super().__init__(
            names,
            sqlite3file,
            use_specification_items=use_specification_items,
            **kargs,
        )

    def delete_database(self):
        """Close and delete the open chess results database."""
        return super().delete_database(
            (
                self.database_file,
                "-".join((self.database_file, "lock")),
                "-".join((self.database_file, "journal")),
            )
        )
